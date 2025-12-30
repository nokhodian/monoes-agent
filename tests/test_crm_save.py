import sys
import os
import argparse

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

def test_save(token=None):
    if not token:
        print("🔍 No token provided, fetching from database...")
        db = DataBase('MAC')
        token = db.fetch_setting("api_token", "")
        if not token:
            print("❌ No api_token found in database.")
            return
        print(f"✅ Loaded token from database: {token[:10]}...")
    else:
        print(f"ℹ️ Using provided token: {token[:10]}...")

    # Initialize RestAPI and FlatLay
    RestAPI.set_authorization(token)
    FlatLay.auth_with_bearer_token(token)

    # Mock profile data
    mock_profiles = [
        {
            "platform": "INSTAGRAM",
            "full_name": "Test User Antigravity",
            "platform_username": "antigravity_test_bot",
            "url": "https://www.instagram.com/antigravity_test_bot/",
            "bio": "I am a test bot for verifying CRM saving.",
            "followers": 1234,
            "following": 567,
            "posts": 42,
            "website": "https://example.com",
            "verified": False,
            "image_url": "https://static.cdninstagram.com/rsrc.php/v4/yI/r/VsNE-OHk_8a.png"
        }
    ]

    print("\n🚀 Attempting to save mock profile to CRM...")
    print(f"Payload Preview: {mock_profiles[0]['full_name']} (@{mock_profiles[0]['platform_username']})")
    
    try:
        # We call create_people which handles mapping internally
        response = RestAPI.create_people(mock_profiles)
        
        print("\n" + "="*60)
        print("RESULT:")
        print(f"Response Type: {type(response)}")
        print(f"Response Content: {response}")
        print("="*60)
        
        if isinstance(response, dict) and (response.get('success') or response.get('message') == 'done'):
            print("\n✅ SAVE SUCCESSFUL!")
        elif isinstance(response, list):
            print("\n✅ SAVE SUCCESSFUL (Batch response)!")
        else:
            print("\n❌ SAVE FAILED (Check response above)")

    except Exception as e:
        print(f"\n💥 CRITICAL ERROR during save: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test CRM saving functionality.")
    parser.add_argument("--token", help="Manually provide a Bearer token (ignores database)")
    args = parser.parse_args()

    test_save(args.token)
