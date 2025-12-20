class ParsingError(Exception):
    """Exception raised for Value Parsing Error.
    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str, error_code: int = 0):
        self.error_code = error_code
        super(ParsingError, self).__init__(message)


class UnExpectedError(Exception):
    """Exception raised for UnExpected error scenarios.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str, error_code: int = 0):
        self.error_code = error_code
        super(UnExpectedError, self).__init__(message)


class WebDriverCustomError(Exception):
    """Exception raised for WebDriverCustomError error scenarios.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str, error_code: int = 0):
        self.error_code = error_code
        super(WebDriverCustomError, self).__init__(message)


class ResponseIsNoneError(Exception):
    """Exception raised when the requests response from RestAPI class is None.

    Attributes:
        message -- explanation of the error
    """

    def __init__(self, message: str, error_code: int = 0):
        self.error_code = error_code
        super(ResponseIsNoneError, self).__init__(message)


class NotAllowedToRunTheAction(Exception):
    """Exception raised when the user can't run the action for costs or functionality reasons.
        For example: Quotas is less than the ActionNeedQuotas or on the MESSAGING the list length is None.

    Attributes:
        message -- explanation of the error

    error_code_notification_message: attribute will used for showing the error to the user by the error_code.
    Here is the how to use this attribute example:
    try:
      raise NotAllowedToRunTheAction("example technical error message", error_code=0)
    except NotAllowedToRunTheAction as not_allowed_err:
      logger.error(not_allowed_err)
      showMessagePopUp(NotAllowedToRunTheAction.error_code_notification_message[not_allowed_err.error_code])
    """
    error_code_notification_message: list = ["Sorry but you don't have enough Quotas for this action.",
                                             "Current action list length is empty!"]

    def __init__(self, message: str, error_code: int = 0):
        self.error_code = error_code
        super(NotAllowedToRunTheAction, self).__init__(message)


class AuthenticationFailedError(Exception):
    """Exception raised when the the automatic social_media authentication will be failed.
    Attributes:
        message -- explanation of the error

    error_code_notification_message: attribute will used for showing the error to the user by the error_code.
    Here is the how to use this attribute example:
    try:
      raise AuthenticationFailedError("example technical error message", error_code=0)
    except AuthenticationFailedError as not_allowed_err:
      logger.error(not_allowed_err)
      showMessagePopUp(AuthenticationFailedError.error_code_notification_message[not_allowed_err.error_code])
    """
    error_code_notification_message: list = ["Authentication failed while running the action!"]

    def __init__(self, message: str, error_code: int = 0):
        self.error_code = error_code
        super(AuthenticationFailedError, self).__init__(message)


class NotAuthorizedError(Exception):
    """
    Exception raised when the client isn't authorized to aws
    Uses: RestAPI & WebSocket-Client
    try:
        if self.isLoggedIn == False:
            raise NotAuthorizedError("Not Authorized")
    except NotAuthorizedError as no_auth_err:
        print(str(no_auth_err)
    """

    def __init__(self, message: str, error_code: int = 0):
        self.error_code = error_code
        super(NotAuthorizedError, self).__init__(message)


class WebSocketInvalidResponseError(Exception):
    """
    Exception raised when an incorrect response came from server
    Uses: Client.send_data()
    """

    def __init__(self, message: str, error_code: int = 0):
        self.error_code = error_code
        super(WebSocketInvalidResponseError, self).__init__(message)


class WebSocketCommonError(Exception):
    """
    Exception raised when any error raise on WebSocket-Client class
    Uses: HANDLER.ACTION_ERRORS
    """

    def __init__(self, message: str, error_code: int = 0):
        self.error_code = error_code
        super(WebSocketCommonError, self).__init__(message)


if __name__ == '__main__':
    import traceback

    try:
        if 10 > 5:
            raise UnExpectedError('This is the unexpected error')

    except UnExpectedError as err:
        print('Unexpected error is: ', err, 'Error Code:', err.error_code)
        traceback.print_exc()
    except Exception as error:
        print('Exceptions is:', error)
        traceback.print_exc()
