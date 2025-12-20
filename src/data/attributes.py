from __future__ import annotations
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from newAgent.src.data.data_parser import Actions
    from typing import List


class GUI_Attrs:
    """
    This class includes Gui attributes for example social Icons dictionary and...
    """
    queue_nodes_widgets: list = []  # The list of the All QWidget & DraggableQWidget which are contains in ui.sawcQueue.
    queue_nodes_widgets_cache: List[
        int] = []  # The copy from the queue_nodes_widgets_cache, Also this attribute must be set before the refresh data & RestAPI Requests.
    socials_icon: dict = {'instagram': ':/icons/icons/Instagram-Connected.png',
                          'linkedin': ':/icons/icons/Linkedin-Connected.png',
                          'tiktok': ':/icons/icons/Tiktok-Connected.png',
                          'email': ':/icons/icons/Email-Connected.png',
                          'flatlay': ':/icons/icons/Email-Connected.png',
                          'telegram': ':/icons/icons/Telegram-Connected.png',
                          'x': ':/icons/icons/Twitter-Connected.png'}  # A Dictionary for each social media Connected-Disconnected Icon
    action_social_icon: dict = {'instagram': (':/icons/icons/Instagram-Logo-PNG.png', None),
                                'linkedin': (':/icons/icons/Linkedin-Logo.png', (70, 70)),
                                'tiktok': (':/icons/icons/tiktok-Logo.png', (55, 55)),
                                'email': (':/icons/icons/Email-Logo.ico', (56, 56)),
                                'flatlay': (':/icons/icons/Email-Logo.ico', (56, 56)),
                                'telegram': (':/icons/icons/Telegram-Logo.png', (56, 56)),
                                'x': (':/icons/icons/Twitter-logo-png.png', (56, 56))}  # A Dictionary for each social media action Icon
    socials_scheduled: dict = {'tiktok': 30,
                               'telegram': 1825}  # The social medias which can be scheduled inside of them.
    # The value must be the number of the days that could be scheduled.


class Attrs:
    """
    This class uses for static attributes. for example:
    target action attribute or current_widget attributes or current_thread attribute.
    """
    current_action_running: Actions = None
    current_monitor_running: Any = None
    current_bot_action_id_running: int = 0  # If the bot runs an action automatically by self, this attribute must be set the current action running "createdAt".
    scheduled_actions: List[
        Actions] = []  # The all of the scheduled actions will be added to this attribute after each data refresh & RestAPI Requests.
    not_done_actions: List[
        Actions] = []  # The all actions which are not in Done states will be appended to this attribute.
    queue_actions: List[
        Actions] = []  # The all actions which are must be in queue after each data refresh & RestAPI Requests.
    user_selected_queue = set()  # If user add any action to the queue the createdAt of the action will add to this set().
    queue_pause: bool = True  # The Queue Launch button signal will connect to this attribute.
    not_allowed_run_action: bool = False  # Uses for when the bot wants to run an action automatically from the queue, (This attribute helps to check if we can run next action or not).
    
    # Sleep Configurations
    sleep_config = {
        'typing_min': 0.05,
        'typing_max': 0.25,
        'action_min': 1.0,
        'action_max': 3.0,
        'page_load': 5.0,
        'scroll_min': 2.0,
        'scroll_max': 5.0,
        'long_wait': 30.0,
        'retry_wait': 1.0,
        'warning_wait': 85.0,
        'concurrency_wait': 480.0
    }
