from newAgent.src.robot.flatlay import FlatLay, traceback_email_flatlay, regenerate_token
from newAgent.src.exceptions.errors import NotAuthorizedError, WebSocketCommonError, WebSocketInvalidResponseError
from newAgent.src.data.data_parser import Event
from datetime import datetime
import websocket
import ssl
import logging
import json
import os


# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()
# Main Execution
start_time = datetime.now()


# logger.info(f"Script started at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

def exception_handler(func):
    def wrapper(*args, **kwargs):
        retries = 0
        max_retries = 3
        while retries < max_retries:
            try:
                result = func(*args, **kwargs)
                return result if result else True

            except NotAuthorizedError:
                logger.error(msg := f"NotAuthorized Error via websocket-{func.__name__}\nYou must login first!\n")
                traceback_email_flatlay(
                    body=msg)

            except ConnectionRefusedError as conn_err:
                logger.error(msg := f"ConnectionRefusedError via websocket-{func.__name__}\n{conn_err}")
                traceback_email_flatlay(body=msg)
                retries += 1
                continue

            except WebSocketInvalidResponseError as ws_ir_ex:
                logger.error(msg := f"WebSocketInvalidResponseError via websocket-{func.__name__}\n{ws_ir_ex}\n")
                traceback_email_flatlay(
                    body=msg)

            except websocket.WebSocketBadStatusException as w_bad_status_ex:
                msg_err = str(w_bad_status_ex)
                if "Unauthorized" in msg_err and "401" in msg_err:
                    logger.warning(f"Unauthorized or Token is expired")
                    id_token = regenerate_token()
                    if id_token:
                        Client.set_authorization(id_token)
                        retries += 1
                        continue
                    else:
                        logger.error("An error occurred via regenerating id_token")
                else:
                    logger.error(msg := f"Server Error via websocket-{func.__name__}")
                    traceback_email_flatlay(body=msg)

            except websocket.WebSocketTimeoutException as w_tex:
                logger.error(msg := f"WebSocketTimeoutException via websocket-{func.__name__}\n{w_tex}")
                traceback_email_flatlay(body=msg)

            except websocket.WebSocketConnectionClosedException as w_c_ex:
                logger.error(msg := f"WebSocketConnectionClosedException via websocket-{func.__name__}\n{w_c_ex}")
                if retries < max_retries:
                    slf = args[0]
                    slf.login()
                    retries += 1
                    continue
                traceback_email_flatlay(
                    body=msg)

            except websocket.WebSocketException as w_ex:
                logger.error(msg := f"WebSocketException via websocket-{func.__name__}\n{w_ex}")
                traceback_email_flatlay(body=msg)

            except ssl.SSLEOFError as eof_ex:
                logger.error(msg := f"SSLEOFError Error via websocket-{func.__name__}\n{eof_ex}")
                if retries < max_retries:
                    slf = args[0]
                    slf.login()
                    retries += 1
                    continue
                traceback_email_flatlay(body=msg)

            except ssl.SSLError as ssl_ex:
                logger.error(msg := f"SSLError via websocket-{func.__name__}\n{ssl_ex}")
                if retries < max_retries:
                    slf = args[0]
                    slf.login()
                    retries += 1
                    continue
                traceback_email_flatlay(body=msg)

            except TimeoutError as t_ex:
                logger.error(msg := f"TimeoutError via websocket-{func.__name__}\nCheck Internet connection\n{t_ex}\n")
                traceback_email_flatlay(body=msg)

            except Exception as ex:
                logger.error(msg := f"Unknown error occurred via websocket-{func.__name__}\n{ex}")
                traceback_email_flatlay(body=msg)

            break
        # return False
        raise WebSocketCommonError("An error occurred at websocket Client class")

    return wrapper


class Client(websocket.WebSocket):
    """
    WebSocket-Client class for communicating online data with back-end
    """
    isLoggedIn: bool = False
    header: dict = {"Authorization": ""}  # Connecting requests_header
    _timeout: int = 30

    def __init__(self,
                 id_token: str,
                 uri: str = "wss://0280bb4g93.execute-api.us-west-2.amazonaws.com/dev/",
                 timeout: int = 30
                 ):
        super(Client, self).__init__(sslopt={"check_hostname": False, "cert_reqs": ssl.CERT_NONE})
        self.uri = uri
        self._timeout = timeout
        self._set_timeout(self._timeout)
        self.set_authorization(id_token)

    @staticmethod
    def set_authorization(id_token: str):
        Client.header['Authorization'] = f"{id_token}"

    def _set_timeout(self, timeout):
        """
        Private method for set the timeout value
        Args:
            timeout: int | float //required
        """
        self.settimeout(timeout)
        logger.info(f"WebSocket Timeout set to: {self.timeout}")

    @exception_handler
    def login(self):
        """
        Connecting to server method

        Returns:
            True if the connection was successful
        Raises:
            WebSocketCommonError: if any method has any exception
        """
        self.connect(self.uri,
                     header=Client.header,
                     timeout=self._timeout)
        self.isLoggedIn = True

    def _read(self, timeout=None, as_class: bool = True):
        """
        Read data from server.

        Args:
            timeout: int | float | None # if the timeout argument is None, process will use the DefaultTimeout value (self._timeout)
            as_class: bool: Returns dict if False, Returns Event class if True

        Returns:
            JSON if data can parse
        """
        if not self.isLoggedIn:
            raise NotAuthorizedError("")

        try:
            if timeout:
                self._timeout = timeout
                self._set_timeout(timeout)
            ret = json.loads(self.recv())
            if isinstance(ret, dict):
                event_type = ret.get("eventType")
                logger.info(f"Response received: dict eventType={event_type}")
            else:
                logger.info(f"Response received: {type(ret).__name__}")
            if as_class:
                ret = Event(ret)
            return ret
        finally:
            self._set_timeout(self._timeout)

    @exception_handler
    def read(self, timeout=None, as_class: bool = True):
        """
        Public Read data from server, but via exception_handler decorator

        Args:
            timeout: int | float | None # if the timeout argument is None, process will use the DefaultTimeout value (self._timeout)
            as_class: bool: Returns dict if False, Returns Event class if True

        Returns:
           Dict if client recieve data from server successfully
        Raises:
            WebSocketCommonError: if any method has any exception
        """
        return self._read(timeout, as_class)

    @exception_handler
    def send_data(self, data):
        """
        Sending data to server

        Args:
            data: Any

        Returns:
            True if the data sent successfully
        Raises:
            WebSocketCommonError: if any method has any exception
        """
        if not self.isLoggedIn:
            raise NotAuthorizedError("")
        req = json.dumps(data)
        if isinstance(data, dict):
            event_type = data.get("eventType")
            logger.info(f"Request sent: dict eventType={event_type}")
        else:
            logger.info(f"Request sent: {type(data).__name__}")
        self.send(req)
        result = self._read()
        if isinstance(result, dict):
            if result["eventType"] == Event.ERROR:
                raise WebSocketInvalidResponseError("The Request content and Response Content doesn't match!\n"
                                                    f"Error: {result}")
        elif isinstance(result, Event):
            if result.eventType == Event.ERROR:
                raise WebSocketInvalidResponseError("The Request content and Response Content doesn't match!\n"
                                                    f"Error: {result}")

    @exception_handler
    def logout(self):
        """
        Disconnecting to server

        Raises:
            WebSocketCommonError: if any method has any exception
        """
        if self.isLoggedIn:
            self.close()
            self.isLoggedIn = False


if __name__ == '__main__':
    FlatLay.username = os.getenv("FLATLAY_USERNAME", "")
    FlatLay.password = os.getenv("FLATLAY_PASSWORD", "")
    _token = os.getenv("FLATLAY_TOKEN", "")
    if not FlatLay.username or not FlatLay.password or not _token:
        logger.error("Missing FLATLAY_USERNAME/FLATLAY_PASSWORD/FLATLAY_TOKEN; skipping websocket test run")
    else:
        client = Client(id_token=_token, timeout=30)
        client.login()
