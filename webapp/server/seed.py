from sqlalchemy.orm import Session
from .db import SessionLocal, engine, Base
from .models.action import Action
from .models.person import Person
from .models.action_target import ActionTarget
from .models.social_list import SocialList
from .models.social_list_item import SocialListItem
from .models.template import Template
from .models.thread import Thread
from .models.config import ConfigEntry
import uuid

def run():
    db: Session = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)
        # Seed actions
        a1 = Action(
            id=str(uuid.uuid4()),
            createdAt=0,
            createdBy="AI",
            ownerId="owner-1",
            title="Keyword Search - Instagram",
            type="KEYWORD_SEARCH",
            state="PENDING",
            disabled=False,
            targetPlatform="INSTAGRAM",
            position=0
        )
        db.add(a1)
        # Seed people
        p1 = Person(
            id=str(uuid.uuid4()),
            platform_username="skimohaaa",
            full_name="Ski Moha",
            image_url="",
            contact_details=[],
            website="",
            content_count=0,
            follower_count="10.5k",
            following_count=500,
            introduction="Digital Creator",
            is_verified=False,
            category="Artist",
            job_title="Creator"
        )
        db.add(p1)
        # Seed target
        t1 = ActionTarget(
            id=str(uuid.uuid4()),
            actionId=a1.id,
            personId=p1.id,
            platform="INSTAGRAM",
            link="https://www.instagram.com/skimohaaa/",
            sourceType="PROFILE",
            status="PENDING"
        )
        db.add(t1)
        # Seed social list
        sl = SocialList(
            id=str(uuid.uuid4()),
            listType="INSTAGRAM",
            name="in-new-list-2",
            itemCount=0,
            email="nokhodian@gmail.com"
        )
        db.add(sl)
        sli = SocialListItem(
            id=str(uuid.uuid4()),
            listId=sl.id,
            platform="INSTAGRAM",
            platform_username="malohg",
            image_url="",
            url="gholam/.com",
            full_name="GholamRest",
            contact_details=[{"type":"email","value":""}],
            follower_count=1
        )
        db.add(sli)
        sl.itemCount = 1
        # Seed template
        tmpl = Template(id=1, name="welcome", subject="Welcome", body="Hello there!", meta={})
        db.merge(tmpl)
        # Seed thread
        th = Thread(id=str(uuid.uuid4()), socialUserId=p1.id, meta={"key":"any type"}, messages=[{"type":"OUTBOUND","body":"Hi"}])
        db.add(th)
        # Seed config
        cfg = ConfigEntry(name="crawler_xpath", data={"xpath": {}, "settings": {}})
        db.merge(cfg)
        db.commit()
        print("Seed completed")
    finally:
        db.close()

if __name__ == "__main__":
    run()
