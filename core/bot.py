from src.robot.instagram import Instagram
from src.robot.linkedin import Linkedin
from src.robot.x import X
from src.robot.tiktok import Tiktok

def get_bot_class(platform):
    platform = platform.lower()
    if platform == 'instagram':
        return Instagram, 'https://www.instagram.com/accounts/login/'
    elif platform == 'linkedin':
        return Linkedin, 'https://www.linkedin.com/login'
    elif platform == 'x':
        return X, 'https://x.com/i/flow/login'
    elif platform == 'tiktok':
        return Tiktok, 'https://www.tiktok.com/login'
    else:
        raise ValueError(f"Unknown platform: {platform}")
