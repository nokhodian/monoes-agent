from newAgent.src.exceptions.errors import AuthenticationFailedError, WebSocketCommonError, ParsingError
from newAgent.src.robot.flatlay import traceback_email_flatlay
import functools
import logging

logger = logging.getLogger(__name__)


class HANDLER:
    """
    This class will handle all the exceptions of the src/main_dir/main.py -> Main class methods via specific decorator.

    How to use:
    -Put the decorator on the specific method. example -> @HANDLER.ACTION_ERRORS
                                                          def instagram_campaign_invitation(self):
                                                                ...
    """

    @classmethod
    def ACTION_ERRORS(cls, method):
        """
        This decorator must be used on the each action running methods.
        """

        @functools.wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                func = method(self, *args, **kwargs)
                return func
            except AttributeError as attr_err:
                # Don't return early for AttributeErrors - let them propagate or handle in WORKFLOW
                # Only catch AttributeErrors that are actual action errors, not UI initialization issues
                logger.error("AttributeError in %s", method.__name__)
                return {"title": "Error", "message": str(attr_err)}
            except ParsingError as parsing_err:
                traceback_email_flatlay(body=f"ParsingError at {method.__name__}\n{parsing_err}\n")

                if parsing_err.error_code == 0:  # Quotas parse
                    pass
                elif parsing_err.error_code == 1:  # Event.prepare_send parse
                    pass
                elif parsing_err.error_code == 2:  # Event.prepare_send Invalid Values
                    return {"title": "Error", "message": "Invalid state value"}
                elif parsing_err.error_code == 3:  # Event.prepare_send Invalid Values
                    return {"title": "Error", "message": "Invalid eventType value"}
                elif parsing_err.error_code == 4:
                    pass

                return {"title": "Error", "message": str(parsing_err)}
            except AuthenticationFailedError as auth_err:
                return {"title": "Error", "message": str(auth_err)}
            except WebSocketCommonError as ws_err:
                return {"title": "Error", "message": "Communication with server failed"}
            except Exception as err:
                logger.error("Unhandled exception in %s: %s", method.__name__, type(err).__name__)
                return {"title": "Error", "message": f"Something went wrong {str(err)}"}

        return wrapper
