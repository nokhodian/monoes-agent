import smtplib
from email.message import EmailMessage
import logging
import traceback
import inspect

recipients: list = [
                    'nokhodian@gmail.com']


class FlatLay:
    """
    Updated FlatLay class for Bearer token authentication (Monoes API)
    """
    username: str = ''
    password: str = ''  # No longer used but kept for compatibility
    name: str = ''
    profile_pic_url: str = ''
    isLoggedIn: bool = False
    id_token: str = None  # Now stores the Bearer token
    bearer_token: str = None  # Explicit Bearer token storage
    
    # Authentication error tracking
    _auth_error_occurred: bool = False
    _last_auth_error: dict = None
    
    # Hardcoded Bearer token for testing - replace with your token
    HARDCODED_BEARER_TOKEN: str = ""
    
    @classmethod
    def auth_with_bearer_token(cls, bearer_token: str):
        """
        Authenticate using a Bearer token instead of email/password
        
        Args:
            bearer_token: The Bearer token for API authentication
            
        Returns:
            dict: Authentication result
        """
        try:
            if not bearer_token or not bearer_token.strip():
                return {
                    'title': 'Error',
                    'message': 'Bearer token cannot be empty'
                }
            
            # Store the token
            cls.bearer_token = bearer_token.strip()
            cls.id_token = f"Bearer {cls.bearer_token}"
            cls.isLoggedIn = True
            cls.username = "monoes_user"  # Default username for compatibility
            cls.name = "Monoes User"  # Default name
            
            return {
                'title': 'Success',
                'message': 'Successfully authenticated with Bearer token'
            }
            
        except Exception as ex:
            cls.isLoggedIn = False
            cls.id_token = None
            cls.bearer_token = None
            return {
                'title': 'Error',
                'message': f'Authentication failed: {str(ex)}'
            }
    
    @classmethod
    def auto_auth_with_hardcoded_token(cls):
        """
        Automatically authenticate using the hardcoded Bearer token
        
        Returns:
            dict: Authentication result
        """
        return cls.auth_with_bearer_token(cls.HARDCODED_BEARER_TOKEN)
    
    @classmethod  
    def auth(cls, email_or_token: str, password: str = None):
        """
        Backward compatibility method - now handles Bearer token
        
        Args:
            email_or_token: Bearer token (password parameter ignored)
            password: Ignored for Bearer token auth
            
        Returns:
            dict: Authentication result
        """
        return cls.auth_with_bearer_token(email_or_token)
    
    @classmethod
    def clear_authentication(cls):
        """
        Clear all authentication data and reset login state
        """
        cls.isLoggedIn = False
        cls.id_token = None
        cls.bearer_token = None
        cls.username = ''
        cls.name = ''
        cls.profile_pic_url = ''
    
    @classmethod
    def handle_auth_error(cls, error_details: dict):
        """
        Handle authentication errors by clearing auth state and triggering re-authentication
        
        Args:
            error_details: Dictionary containing error information
        """
        try:
            # Clear authentication state
            cls.clear_authentication()
            
            # Log the authentication error
            error_message = error_details.get('message', 'Authentication failed')
            logging.warning(f'Authentication error handled: {error_message}')
            
            # Set a flag or trigger re-authentication prompt
            # This could be used by the UI to show a re-authentication dialog
            cls._auth_error_occurred = True
            cls._last_auth_error = error_details
            
            return {
                'success': True,
                'message': 'Authentication error handled, please re-authenticate',
                'requires_reauth': True
            }
            
        except Exception as ex:
            logging.error(f'Error in handle_auth_error: {ex}')
            return {
                'success': False,
                'message': f'Failed to handle authentication error: {str(ex)}'
            }


def traceback_email_flatlay(body: str = '',
                            subject: str = '',
                            use_traceback: bool = True,
                            image_content: bytes = b'',
                            request_body = None):
    """Send an email using SMTP with proper error handling.
        Subject -> FLATLAY Username
        body -> traceback.format_exc()
    """
    import os
    if os.environ.get('MONOES_DEBUG') == '1':
        logging.info("DEBUG MODE: Skipping email traceback.")
        logging.error(f"Subject: {subject}\nBody: {body}\nTraceback: {traceback.format_exc() if use_traceback else 'N/A'}")
        try:
            caller = inspect.stack()[1]
            logging.info(f"Email trigger caller: {caller.filename}:{caller.lineno} in {caller.function}")
        except Exception:
            pass
        return

    global recipients
    if FlatLay.username:
        subject = FlatLay.username
    if use_traceback:
        body += traceback.format_exc()
    sender_email = 'n.e.a.r.n.o10@gmail.com'
    password = 'eedb znbx bgqc sknf '
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    try:
        # Connect to the SMTP server
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, password)
            for receiver_email in recipients:
                # Create a MIME message
                msg = EmailMessage()
                msg['Subject'] = subject
                msg['From'] = "Monoes Support"
                msg['To'] = receiver_email
                msg.set_content(body)
                if image_content and isinstance(image_content, bytes):
                    msg.add_attachment(image_content, maintype='image', subtype='png',
                                       filename='View of the Error moment')
                if request_body and isinstance(request_body, str | bytes):
                    content = request_body.encode("utf-8") if isinstance(request_body, str) else request_body
                    msg.add_attachment(content, maintype="text", subtype="txt",
                                       filename="RequestBody.txt")
                server.sendmail(sender_email, receiver_email, msg.as_string())

                logging.info(f"Email sent successfully to {receiver_email}")

    except smtplib.SMTPAuthenticationError:
        logging.error("Authentication error: Unable to login to the SMTP server.")
    except smtplib.SMTPConnectError:
        logging.error("Connection error: Unable to connect to the SMTP server.")
    except smtplib.SMTPRecipientsRefused:
        logging.error(f"Recipient {receiver_email} refused.")
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        traceback.print_exc()


def regenerate_token():
    """
    Token regeneration for Bearer tokens (returns existing token)
    Bearer tokens don't typically need regeneration like JWT refresh tokens
    """
    if FlatLay.isLoggedIn and FlatLay.bearer_token:
        return FlatLay.id_token
    return None


if __name__ == '__main__':
    import json

    file = [{"platform": "INSTAGRAM",
             "platform_username": "ParsaPournabi",
             "Followers": 1000,
             "is_verified": True}, {"platform": "INSTAGRAM",
                                    "platform_username": "https://flatlay.io",
                                    "Followers": None, "is_verified": True}] * 1000
    js = json.dumps(file)
    traceback_email_flatlay(body="error on requests", request_body=js)
