from datetime import datetime
from newAgent.src.api.APIs import RestAPI
import sqlite3
import os
import pickle
import traceback
import threading
import json


class DataBase:
    DEFAULT_RATE_COUNT_VALUE: int = 48
    MAXIMUM_RATE_COUNT_VALUE: int = 50

    def __init__(self, platform: str):
        # Thread lock for database operations
        self._db_lock = threading.Lock()
        try:
            path = os.path.join(os.path.expanduser('~'), 'Documents/flatlay_database.db')
            if platform == 'WINDOWS':
                # path = 'flatlay_database.db'
                pass
            elif platform == 'MAC':
                path = os.path.join(os.path.expanduser('~'), 'flatly_database.db')
            if not os.path.exists(path):
                try:
                    file = open(path, 'w')
                    file.close()
                except Exception as os_ex:
                    print(os_ex)
            self.req = RestAPI('None')
            # Enable thread-safe mode for SQLite
            self._sql = sqlite3.connect(path, check_same_thread=False)
            self.cursor = self._sql.cursor()
            self._create_tables()
            self._delete_expired_sessions()
            self._drop_prev_tables()
            self._update_twitter_name_to_x()
            self._insert_default_values()
        except Exception as ex:
            print(ex)

    def _create_tables(self):
        """Creating info table and maybe some other tables"""
        # feedback table
        table_feedback_table = f'CREATE TABLE IF NOT EXISTS feedback (rate_count INTEGER DEFAULT {self.DEFAULT_RATE_COUNT_VALUE} NOT NULL);'
        self.cursor.execute(table_feedback_table)

        # crawlerSession table
        table_crawler_session = 'CREATE TABLE IF NOT EXISTS crawlerSession (username VARCHAR(20), social VARCHAR(20), cookies BLOB, expiry TIMESTAMP NOT NULL, when_added TIMESTAMP, profile_photo BLOB, cookies_json TEXT)'
        self.cursor.execute(table_crawler_session)

        # settings table
        table_settings = 'CREATE TABLE IF NOT EXISTS settings (key VARCHAR(50) PRIMARY KEY, value TEXT)'
        self.cursor.execute(table_settings)

        # configs table for storing xpath configs from API
        table_configs = 'CREATE TABLE IF NOT EXISTS configs (config_name VARCHAR(255) PRIMARY KEY, config_data TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)'
        self.cursor.execute(table_configs)

        pragma_check_sessions = 'PRAGMA TABLE_INFO(crawlerSession);'
        self.cursor.execute(pragma_check_sessions)
        if len(self.cursor.fetchall()) != 7:
            self._recreate_session_table()

        self._sql.commit()

    def _drop_prev_tables(self):
        """
        DROP useless tables
        """
        try:
            TABLES: list = ["info", "instagramInfo", "images"]
            for TABLE in TABLES:
                query = "DROP TABLE IF EXISTS %s;"
                self.cursor.execute(query % TABLE)
            self._sql.commit()

        except Exception as ex:
            print("Exception _drop_prev_tables", ex)
            traceback.print_exc()

    def _update_twitter_name_to_x(self):
        """
        This method must be delete after two updates
        """
        try:
            query = """UPDATE crawlerSession SET social='x' WHERE social='x'"""
            self.cursor.execute(query)
            self._sql.commit()
        except Exception as ex:
            print("Exception _update_twitter_name_to_x", ex)
            traceback.print_exc()

    def _recreate_session_table(self):
        try:
            query_drop_table = """DROP TABLE crawlerSession;"""
            query_create_table = """CREATE TABLE IF NOT EXISTS crawlerSession (username VARCHAR(20), social VARCHAR(20), cookies BLOB, expiry TIMESTAMP NOT NULL, when_added TIMESTAMP, profile_photo BLOB, cookies_json TEXT)"""
            self.cursor.execute(query_drop_table)
            self.cursor.execute(query_create_table)
            self._sql.commit()

        except Exception as ex:
            traceback.print_exc()
            print('_recreate_session_table', ex)

    def _insert_default_values(self):
        """
        INSERT TABLES DEFAULT VALUES
        """
        try:
            # feedback table
            query = f"INSERT INTO feedback SELECT {self.DEFAULT_RATE_COUNT_VALUE} WHERE NOT EXISTS (SELECT 1 FROM feedback);"
            self.cursor.execute(query)

            self._sql.commit()

        except Exception as ex:
            print("Exception insert_default_values", ex)
            traceback.print_exc()

    def _delete_expired_sessions(self):
        """Delete sessions that have expired"""
        try:
            query = "DELETE FROM crawlerSession WHERE expiry < ?"
            self.cursor.execute(query, (datetime.now(),))
            self._sql.commit()
        except Exception as ex:
            print("Exception _delete_expired_sessions", ex)

    def fetch_crawler_session(self, username: str, social: str):
        """Getting info which matched with username and social"""
        with self._db_lock:
            try:
                query = """SELECT cookies, cookies_json FROM crawlerSession WHERE username='%s' AND social='%s' ORDER BY when_added DESC LIMIT 1""" % (
                    username, social)
                self.cursor.execute(query)
                fetch = self.cursor.fetchone()
                if not fetch:
                    return None
                
                # Prefer JSON cookies if available
                if fetch[1]:
                    try:
                        return json.loads(fetch[1])
                    except Exception:
                        pass
                        
                if isinstance(fetch[0], bytes):
                    return pickle.loads(fetch[0])
            except Exception as ex:
                print('Exception on fetch_crawler_session', ex)
                traceback.print_exc()

    def fetch_username_crawler_session(self, social: str):
        """Fetch username from crawler session"""
        with self._db_lock:
            try:
                query = """SELECT username FROM crawlerSession WHERE social='%s' ORDER BY when_added DESC LIMIT 1""" % social
                self.cursor.execute(query)
                fetch = self.cursor.fetchall()
                if not fetch:
                    return None
                return fetch[-1][0]
            except Exception as ex:
                print('Exception on fetch_crawler_session', ex)
                traceback.print_exc()

    def fetch_all_usernames_crawler_session(self, social: str):
        """Fetch all usernames from crawler session"""
        try:
            query = """SELECT DISTINCT username FROM crawlerSession WHERE social='%s'""" % social
            self.cursor.execute(query)
            fetch = self.cursor.fetchall()
            if not fetch:
                return []
            return list(map(lambda x: x[0], fetch))
        except Exception as ex:
            print('Exception on fetch_crawler_session', ex)
            traceback.print_exc()

    def fetch_latest_crawler_session(self, social: str):
        """Fetch the most recent session for a social platform without requiring username"""
        with self._db_lock:
            try:
                query = """SELECT cookies, username, profile_photo, cookies_json FROM crawlerSession WHERE social='%s' ORDER BY when_added DESC LIMIT 1""" % social
                self.cursor.execute(query)
                fetch = self.cursor.fetchone()
                if not fetch:
                    return None
                
                cookies_blob = fetch[0]
                username = fetch[1]
                profile_photo = fetch[2]
                cookies_json = fetch[3]
                
                cookies = None
                if cookies_json:
                    try:
                        cookies = json.loads(cookies_json)
                    except Exception:
                        pass
                
                if cookies is None and isinstance(cookies_blob, bytes):
                    cookies = pickle.loads(cookies_blob)
                
                return (cookies, username, profile_photo)
            except Exception as ex:
                print('Exception on fetch_latest_crawler_session', ex)
                traceback.print_exc()
                return None

    def delete_latest_crawler_session(self, social: str):
        """Delete the most recent session for a social platform"""
        with self._db_lock:
            try:
                print(f"[DELETE_SESSION] Starting deletion process for {social}")
                
                # First check how many sessions exist before deletion
                query_count_before = """SELECT COUNT(*) FROM crawlerSession WHERE social=?"""
                self.cursor.execute(query_count_before, (social,))
                sessions_before = self.cursor.fetchone()[0]
                print(f"[DELETE_SESSION] Sessions before deletion for {social}: {sessions_before}")
                
                if sessions_before == 0:
                    print(f"[DELETE_SESSION] No sessions exist for {social}")
                    return False
                
                # Get the most recent session to delete (get the actual record details)
                query_get = """SELECT username, when_added FROM crawlerSession WHERE social=? ORDER BY when_added DESC LIMIT 1"""
                self.cursor.execute(query_get, (social,))
                fetch = self.cursor.fetchone()
                
                if fetch:
                    username, when_added = fetch
                    print(f"[DELETE_SESSION] Found latest session for {social}")
                    
                    # Delete the specific session by username, social, and when_added to ensure we get the exact record
                    query_delete = """DELETE FROM crawlerSession WHERE username=? AND social=? AND when_added=?"""
                    self.cursor.execute(query_delete, (username, social, when_added))
                    self._sql.commit()
                    
                    # Verify deletion
                    self.cursor.execute(query_count_before, (social,))
                    sessions_after = self.cursor.fetchone()[0]
                    print(f"[DELETE_SESSION] Sessions after deletion for {social}: {sessions_after}")
                    
                    return sessions_before > sessions_after
                
                return False
                
            except Exception as ex:
                print('Exception on delete_latest_crawler_session', ex)
                traceback.print_exc()
                return False

    def fetch_setting(self, key: str, default=None):
        """Fetch a setting value by key"""
        with self._db_lock:
            try:
                query = "SELECT value FROM settings WHERE key=?"
                self.cursor.execute(query, (key,))
                result = self.cursor.fetchone()
                if result:
                    return result[0]
                return default
            except Exception as ex:
                print(f"Exception on fetch_setting({key})", ex)
                traceback.print_exc()
                return default

    def save_setting(self, key: str, value: str):
        """Save or update a setting"""
        with self._db_lock:
            try:
                query = "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)"
                self.cursor.execute(query, (key, str(value)))
                self._sql.commit()
                return True
            except Exception as ex:
                print(f"Exception on save_setting({key}, {value})", ex)
                traceback.print_exc()
                return False

    def latest_cookies(self, social: str):
        """Alias for fetch_latest_crawler_session to match usage in main.py"""
        return self.fetch_latest_crawler_session(social)

    def delete_latest(self, social: str):
        """Alias for delete_latest_crawler_session to match usage in main.py"""
        return self.delete_latest_crawler_session(social)

    def delete_all(self, social: str):
        """Delete all sessions for a social platform"""
        with self._db_lock:
            try:
                print(f"[DELETE_ALL] Starting deletion of ALL sessions for {social}")
                
                query_count_before = """SELECT COUNT(*) FROM crawlerSession WHERE social=?"""
                self.cursor.execute(query_count_before, (social,))
                sessions_before = self.cursor.fetchone()[0]
                
                if sessions_before == 0:
                    print(f"[DELETE_ALL] No sessions exist for {social}")
                    return True
                
                query_delete = """DELETE FROM crawlerSession WHERE social=?"""
                self.cursor.execute(query_delete, (social,))
                self._sql.commit()
                
                self.cursor.execute(query_count_before, (social,))
                sessions_after = self.cursor.fetchone()[0]
                
                print(f"[DELETE_ALL] Deleted {sessions_before} sessions. Remaining: {sessions_after}")
                return sessions_after == 0
                
            except Exception as ex:
                print('Exception on delete_all', ex)
                traceback.print_exc()
                return False

    def feedback_increase_rate_count(self) -> bool:
        """
        Increment the rate_count in the feedback table.
        Returns True if rate_count >= MAXIMUM_RATE_COUNT_VALUE, else False.
        """
        with self._db_lock:
            try:
                # Increment the rate_count
                query_update = "UPDATE feedback SET rate_count = rate_count + 1"
                self.cursor.execute(query_update)
                self._sql.commit()

                # Fetch the current rate_count
                query_select = "SELECT rate_count FROM feedback"
                self.cursor.execute(query_select)
                result = self.cursor.fetchone()
                
                if result:
                    rate_count = result[0]
                    if rate_count >= self.MAXIMUM_RATE_COUNT_VALUE:
                        return True
                return False

            except Exception as ex:
                print('Exception on feedback_increase_rate_count', ex)
                traceback.print_exc()
                return False

    def insert_auto(self, social: str, cookies: object, expiry: datetime, username: str = 'Unknown', profile_photo: bytes = None):
        """
        Insert a new session automatically
        """
        with self._db_lock:
            try:
                print(f"[INSERT_AUTO] Inserting session for {social}")
                
                query = """INSERT INTO crawlerSession (username, social, cookies, expiry, when_added, profile_photo, cookies_json) VALUES (?, ?, ?, ?, ?, ?, ?)"""
                
                # Handle both types of cookies
                cookies_blob = None
                cookies_json = None
                
                if isinstance(cookies, bytes):
                    cookies_blob = cookies
                else:
                    # It's an object (list of dicts)
                    try:
                        cookies_blob = pickle.dumps(cookies)
                        cookies_json = json.dumps(cookies)
                    except Exception:
                        pass
                
                self.cursor.execute(query, (username, social, cookies_blob, expiry, datetime.now(), profile_photo, cookies_json))
                self._sql.commit()
                return True
                
            except Exception as ex:
                print('Exception on insert_auto', ex)
                traceback.print_exc()
                return False

    def insert_into_crawler_session(self, username: str, social: str, cookies: object, expiry: datetime, profile_photo: bytes = None):
        """Insert a session into the database (legacy/direct method)"""
        with self._db_lock:
            try:
                query = """INSERT INTO crawlerSession (username, social, cookies, expiry, when_added, profile_photo, cookies_json) VALUES (?, ?, ?, ?, ?, ?, ?)"""
                
                cookies_blob = None
                cookies_json = None
                
                if isinstance(cookies, bytes):
                    cookies_blob = cookies
                else:
                    try:
                        cookies_blob = pickle.dumps(cookies)
                        cookies_json = json.dumps(cookies)
                    except Exception:
                        pass
                    
                self.cursor.execute(query, (username, social, cookies_blob, expiry, datetime.now(), profile_photo, cookies_json))
                self._sql.commit()
                return True
            except Exception as ex:
                print('Exception on insert_into_crawler_session', ex)
                traceback.print_exc()
                return False

    def delete_from_crawler_session(self, username: str, social: str):
        """Delete a specific session by username and social"""
        with self._db_lock:
            try:
                query = """DELETE FROM crawlerSession WHERE username=? AND social=?"""
                self.cursor.execute(query, (username, social))
                self._sql.commit()
                return True
            except Exception as ex:
                print('Exception on delete_from_crawler_session', ex)
                traceback.print_exc()
                return False

    def debug_show_all_sessions(self, social: str):
        """Debug method to show all sessions for a social platform"""
        with self._db_lock:
            try:
                query = """SELECT username, when_added FROM crawlerSession WHERE social=?"""
                self.cursor.execute(query, (social,))
                rows = self.cursor.fetchall()
                print(f"[DEBUG_DB] Sessions for {social}:")
                for row in rows:
                    print(f"  - User: {row[0]}, Added: {row[1]}")
                if not rows:
                    print("  - No sessions found.")
            except Exception as ex:
                print('Exception on debug_show_all_sessions', ex)

    def save_config(self, config_name: str, config_data: dict):
        """Save or update a config in the database"""
        with self._db_lock:
            try:
                config_json = json.dumps(config_data)
                query = """INSERT OR REPLACE INTO configs (config_name, config_data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)"""
                self.cursor.execute(query, (config_name, config_json))
                self._sql.commit()
                return True
            except Exception as ex:
                print(f"Exception on save_config({config_name})", ex)
                traceback.print_exc()
                return False

    def fetch_config(self, config_name: str):
        """Fetch a config from the database"""
        with self._db_lock:
            try:
                query = "SELECT config_data FROM configs WHERE config_name=?"
                self.cursor.execute(query, (config_name,))
                result = self.cursor.fetchone()
                if result:
                    return json.loads(result[0])
                return None
            except Exception as ex:
                print(f"Exception on fetch_config({config_name})", ex)
                traceback.print_exc()
                return None

    def delete_config(self, config_name: str):
        """Delete a config from the database"""
        with self._db_lock:
            try:
                query = "DELETE FROM configs WHERE config_name=?"
                self.cursor.execute(query, (config_name,))
                self._sql.commit()
                return True
            except Exception as ex:
                print(f"Exception on delete_config({config_name})", ex)
                traceback.print_exc()
                return False

    def list_configs(self):
        """List all config names in the database"""
        with self._db_lock:
            try:
                query = "SELECT config_name FROM configs ORDER BY updated_at DESC"
                self.cursor.execute(query)
                results = self.cursor.fetchall()
                return [row[0] for row in results]
            except Exception as ex:
                print("Exception on list_configs", ex)
                traceback.print_exc()
                return []
