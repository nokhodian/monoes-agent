def map_action_to_legacy(a: dict) -> dict:
    return {
        "id": a.get("id"),
        "createdAt": a.get("createdAt"),
        "type": a.get("type"),
        "state": {
            "ASSIGNED": "PENDING",
            "IN_PROGRESS": "INPROGRESS",
            "PAUSED": "PAUSE",
            "PENDING": "PENDING",
            "DONE": "DONE"
        }.get(a.get("state"), a.get("state")),
        "title": a.get("title"),
        "createdBy": a.get("createdBy"),
        "execProps": {
            "source": a.get("targetPlatform"),
            "sourceType": a.get("type"),
            "jobs": [],
            "maxResultsCount": 0,
            "resultsCount": 0,
            "failedInvites": [],
            "inviteesCount": 0,
            "reachedIndex": a.get("position", 0),
            "failedProfileSearches": [],
            "profilesCount": 0,
            "failedMessages": [],
            "recipientsCount": 0,
            "failedItems": [],
            "itemsCount": 0,
            "requiredQuotas": 0,
            "currentStage": "",
            "reachedSubIndex": -1
        },
        "props": {
            "messageSubject": a.get("contentSubject"),
            "text": a.get("contentMessage"),
            "media": [{"url": u, "type": "IMAGE", "effect": "normal", "customRatio": ""} for u in (a.get("contentBlobURL") or [])],
            "scheduledDate": a.get("scheduledDate"),
            "target": a.get("targetPlatform")
        }
    }

def map_person_to_saved_item(p: dict, platform: str) -> dict:
    return {
        "id": p.get("id"),
        "socialUserId": p.get("id"),
        "platform_username": p.get("platform_username"),
        "full_name": p.get("full_name"),
        "image_url": p.get("image_url"),
        "follower_count": p.get("follower_count"),
        "contact_details": p.get("contact_details"),
        "website": p.get("website"),
        "url": "",
        "platform": platform.lower(),
        "updated_at": "",
        "created_at": "",
        "category": p.get("category"),
        "introduction": p.get("introduction"),
        "is_verified": p.get("is_verified"),
        "location": "",
        "company_name": "",
        "job_title": p.get("job_title"),
        "opportunity_title": "",
        "opportunity_value": 0
    }
