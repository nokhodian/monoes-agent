import sys
import os
import threading
import logging
import time
from pathlib import Path

# Add project root to sys.path
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from PyQt5.QtCore import QObject, pyqtSignal, pyqtProperty, QUrl, pyqtSlot
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtQml import QQmlApplicationEngine

from newAgent.core.bot import get_bot_class
from newAgent.core.auth import AuthManager
from newAgent.core.runner import ActionRunner
from newAgent.src.data.data_parser import Actions
from newAgent.src.api.APIs import RestAPI
from newAgent.src.database.database import DataBase

# Custom Log Handler to send logs to QML
class SignalHandler(logging.Handler):
    def __init__(self, signal):
        super().__init__()
        self.signal = signal

    def emit(self, record):
        msg = self.format(record)
        self.signal.emit(msg + "\n")

class Backend(QObject):
    logEmitted = pyqtSignal(str, arguments=['msg'])
    isRunningChanged = pyqtSignal(bool, arguments=['running'])
    actionsChanged = pyqtSignal()
    loginSuccess = pyqtSignal()
    loginError = pyqtSignal(str, arguments=['message'])
    socialStatusesChanged = pyqtSignal()

    savedTokenChanged = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.db = DataBase('MAC')
        self._logs = ""
        self._isRunning = False
        self._headless = False
        self._actions = []
        self._runningId = ""
        self._savedToken = self.db.fetch_setting("api_token", "")
        self._socialStatuses = {
            "Instagram": False,
            "LinkedIn": False,
            "X": False,
            "TikTok": False,
            "Telegram": False,
            "Email": False
        }
        self.bot_instance = None
        
        # Setup logging
        self.logger = logging.getLogger("gui")
        self.logger.setLevel(logging.INFO)
        # Remove existing handlers to avoid duplicates
        for h in self.logger.handlers[:]:
            self.logger.removeHandler(h)
                
        handler = SignalHandler(self.logEmitted)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        self.logger.addHandler(handler)
        
        self.logEmitted.connect(self.append_log)
        
        # Initial check
        self.checkSocialStatus()

    @pyqtProperty(str, notify=logEmitted)
    def logs(self):
        return self._logs

    @pyqtProperty(bool, notify=isRunningChanged)
    def isRunning(self):
        return self._isRunning

    @pyqtProperty(bool, notify=isRunningChanged) # Using same notifier for simplicity or add one
    def headless(self):
        return self._headless

    @headless.setter
    def headless(self, value):
        if self._headless != value:
            self._headless = value
            self.logger.info("Headless mode: {}".format(value))

    @pyqtProperty('QVariantMap', notify=socialStatusesChanged)
    def socialStatuses(self):
        return self._socialStatuses

    @pyqtProperty('QVariantList', notify=actionsChanged)
    def actions(self):
        # Sort: INPROGRESS first, then PENDING, then DONE
        def sort_key(action):
            state = action.get('state', 'PENDING')
            if state == 'INPROGRESS': return 0
            if state == 'PENDING': return 1
            if state == 'DONE': return 2
            return 3
        return sorted(self._actions, key=sort_key)

    @pyqtProperty(str, notify=savedTokenChanged)
    def savedToken(self):
        return self._savedToken

    def append_log(self, msg):
        self._logs += msg

    @pyqtSlot(str)
    def login(self, token):
        if not token:
            self.loginError.emit("Token cannot be empty")
            return
            
        self.logger.info("Logging in...")
        def _login_thread():
            try:
                RestAPI.set_authorization(token)
                # Fetch actions to verify login
                res = RestAPI.get_actions()
                if res and 'actions' in res:
                    self._actions = [Actions(a).action for a in res['actions']]
                    self.actionsChanged.emit()
                    
                    # Save token if login successful
                    self.db.save_setting("api_token", token)
                    self._savedToken = token
                    self.savedTokenChanged.emit()
                    
                    self.loginSuccess.emit()
                    self.logger.info("Login successful")
                else:
                    self.logger.warning("No actions found or invalid token")
                    self.loginError.emit("Invalid token or API issue")
            except Exception as e:
                self.logger.error("Login failed: {}".format(e))
                self.loginError.emit(str(e))
        
        threading.Thread(target=_login_thread, daemon=True).start()

    @pyqtSlot(str)
    def login_manual(self, platform):
        if self._isRunning:
            self.logger.warning("An action is already running")
            return
            
        self.logger.info("Opening manual login for {}...".format(platform))
        self._isRunning = True
        self.isRunningChanged.emit(True)
        
        def _manual_login_thread():
            try:
                bot_class, login_url = get_bot_class(platform.lower())
                bot = bot_class(login_url, 'MAC')
                self.bot_instance = bot
                bot.headless = False # Must be visible for manual login
                bot.web_driver(login_required=False)
                
                auth = AuthManager(platform)
                auth.check_and_save_login(bot)
                
                self.logger.info("Manual login check complete for {}".format(platform))
                self.checkSocialStatus()
            except Exception as e:
                self.logger.error("Error during manual login: {}".format(e))
            finally:
                self._isRunning = False
                self.isRunningChanged.emit(False)
                self.bot_instance = None
                if 'bot' in locals() and bot:
                    try:
                        bot.quit()
                    except Exception:
                        pass

        threading.Thread(target=_manual_login_thread, daemon=True).start()

    @pyqtSlot()
    def checkSocialStatus(self):
        from newAgent.src.database.database import DataBase
        db = DataBase('MAC')
        platforms = ["INSTAGRAM", "LINKEDIN", "X", "TIKTOK", "TELEGRAM"]
        changed = False
        for p in platforms:
            status = db.latest_cookies(p) is not None
            key = p.capitalize() if p != "X" else "X"
            if self._socialStatuses.get(key) != status:
                self._socialStatuses[key] = status
                changed = True
        
        if changed:
            self.socialStatusesChanged.emit()

    @pyqtSlot()
    def refreshActions(self):
        def _fetch():
            try:
                res = RestAPI.get_actions()
                if res and 'actions' in res:
                    new_actions = []
                    for a in res['actions']:
                        parsed = Actions(a).action
                        # Preserve local INPROGRESS state
                        if self._runningId and parsed.get('id') == self._runningId:
                            parsed['state'] = 'INPROGRESS'
                        new_actions.append(parsed)
                    
                    self._actions = new_actions
                    self.actionsChanged.emit()
                    self.logger.info("Refreshed: {} actions".format(len(self._actions)))
                else:
                    self.logger.warning("No actions found")
            except Exception as e:
                self.logger.error("Refresh failed: {}".format(e))

        threading.Thread(target=_fetch, daemon=True).start()

    @pyqtSlot(str, str, str, int, str)
    def run_action(self, platform, action_type, keyword, max_results, action_id=""):
        if self._isRunning:
            self.logger.warning("An action is already running")
            return
        
        self._isRunning = True
        self._runningId = action_id
        self.isRunningChanged.emit(True)
        
        # Update local actions list to show 'INPROGRESS' immediately
        if action_id:
            for action in self._actions:
                if action.get('id') == action_id:
                    action['state'] = 'INPROGRESS'
                    self.actionsChanged.emit()
                    break

        self.logger.info("Run: {} {} '{}' (max {})".format(platform, action_type, keyword, max_results))

        thread = threading.Thread(target=self._run_action_thread, args=(platform, action_type, keyword, max_results, action_id))
        thread.daemon = True
        thread.start()

    @pyqtSlot()
    def stop_action(self):
        if self.bot_instance:
            self.logger.info("Stopping action...")
            # This is a bit forceful but fits current architecture
            try:
                self.bot_instance.quit()
            except Exception:
                pass
            self._isRunning = False
            self.isRunningChanged.emit(False)
            
            if self._runningId:
                for action in self._actions:
                    if action.get('id') == self._runningId:
                        action['state'] = 'PENDING'
                        self.actionsChanged.emit()
                        break
                self._runningId = ""

    def _run_action_thread(self, platform, action_type, keyword, max_results, action_id=""):
        try:
            self.logger.info("Initializing...")
            
            bot_class, login_url = get_bot_class(platform)
            bot = bot_class(login_url, 'MAC')
            self.bot_instance = bot
            
            bot._has_challenge = lambda: False
            bot.headless = self._headless
            
            auth = AuthManager(platform)
            auth.load_cookies(bot)
            
            bot.web_driver(login_required=False)
            auth.check_and_save_login(bot)
            
            action_data = {
                "type": action_type,
                "platform": platform,
                "keyword": keyword,
                "maxResultsCount": max_results,
                "createdAt": int(time.time() * 1000),
                "state": "PENDING",
                "createdBy": "GUI"
            }
            
            action = Actions(action_data)
            
            self.logger.info("Executing...")
            runner = ActionRunner(bot, action)
            runner.run()
            
            self.logger.info("Done!")
            self.refreshActions() # Refresh list to show updated state
            self.checkSocialStatus() # In case they logged in during run

        except Exception as e:
            self.logger.error("Error: {}".format(str(e)))
        finally:
            self._isRunning = False
            self._runningId = ""
            self.isRunningChanged.emit(False)
            self.bot_instance = None
            if 'bot' in locals() and bot:
                try:
                    bot.quit()
                except Exception:
                    pass

if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    app.setOrganizationName("Monoes")
    app.setApplicationName("Mono Agent")

    engine = QQmlApplicationEngine()
    
    backend = Backend()
    engine.rootContext().setContextProperty("backend", backend)

    # Add the current directory to import paths for QML to find SidebarButton.qml etc.
    engine.addImportPath(str(Path(__file__).parent / "gui" / "qml"))

    qml_file = Path(__file__).parent / "gui" / "qml" / "main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))

    if not engine.rootObjects():
        sys.exit(-1)

    sys.exit(app.exec_())
