import sys
import os
import random
import string

# Add the parent directory of 'newAgent' to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from newAgent.src.api.APIs import RestAPI
from newAgent.src.database.database import DataBase
from newAgent.src.robot.flatlay import FlatLay

def save_random_profile():
    print("🔍 Fetching token from database...")
    db = DataBase('MAC')
    token = db.fetch_setting("api_token", "")
    
    if not token:
        print("❌ No token found.")
        return

    RestAPI.set_authorization(token)
    FlatLay.auth_with_bearer_token(token)

    # Generate random name/username
    rand = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    name = f"Test User {rand}"
    username = f"user_{rand}"

    profile = [{
        "platform": "INSTAGRAM",
        "full_name": name,
        "platform_username": username,
        "url": f"https://instagram.com/{username}",
        "bio": "Random test profile for CRM saving.",
        "followers": random.randint(100, 10000),
        "createdBy": {"name": "monoes-agent"}
    }]

    print(f"🚀 Saving: {name} (@{username})...")
    res = RestAPI.create_people(profile)
    
    # RestAPI.create_people returns the response object if it hits an error or a dict if successful (due to @retry)
    if isinstance(res, dict) and 'data' in res:
        print(f"✅ SUCCESS! CRM ID: {res['data']['createPeople'][0]['id']}")
    else:
        print(f"❌ FAILED. Response: {res}")

if __name__ == "__main__":
    save_random_profile()
