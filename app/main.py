from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from app.db.database import engine
from sqlalchemy.exc import IntegrityError
from app.model.preferences import (TenantPreferencesRequest,ChannelResponse, Tenant, TenantPreference, 
                                   Category, Event, Channel, UserPreference, UserPreferencesRequest,
                                   UserPreferencesPostRequest, 
                                   TenantPreferencesPostRequest, CategoryResponse, EventResponse)
from app.db.database import get_db
Base = declarative_base()

app = FastAPI()

Base.metadata.create_all(bind=engine)

@app.post("/tenants/{tenant_id}/preferences/")
def create_tenant_preferences(tenant_id: int, request: TenantPreferencesPostRequest, db: Session = Depends(get_db)):
    try:
        # Instead of getting tenant_id from the body, we use the path param tenant_id
        tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail=f"Tenant with ID {tenant_id} not found")

        new_preferences = []

        for category in request.preferences:
            db_category = db.query(Category).filter(Category.category_id == category.category_id).first()
            if not db_category:
                raise HTTPException(status_code=400, detail=f"Category {category.category_id} not found")

            for event in category.events:
                db_event = db.query(Event).filter(
                    Event.event_id == event.event_id, Event.category_id == category.category_id
                ).first()
                if not db_event:
                    raise HTTPException(
                        status_code=400, 
                        detail=f"Event {event.event_id} not found or does not belong to category {category.category_id}"
                    )

                for channel in event.channels:
                    db_channel = db.query(Channel).filter(Channel.channel_id == channel.channel_id).first()
                    if not db_channel:
                        raise HTTPException(status_code=400, detail=f"Channel {channel.channel_id} not found")

                    new_preferences.append(
                        TenantPreference(
                            tenant_id=tenant_id,  # Using tenant_id from the path parameter
                            category_id=category.category_id,
                            event_id=event.event_id,
                            channel_id=channel.channel_id,
                        )
                    )

        db.bulk_save_objects(new_preferences)
        db.commit()

        return {"message": "Preferences added successfully", "total_rows_inserted": len(new_preferences)}

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database Integrity Error: {repr(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {repr(e)}")



@app.get("/tenants/{tenant_id}/preferences", response_model=TenantPreferencesRequest)
def get_tenant_preferences(tenant_id: int, db: Session = Depends(get_db)):
    tenant = db.query(Tenant).filter(Tenant.tenant_id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    preferences = db.query(TenantPreference).filter(TenantPreference.tenant_id == tenant_id).all()

    response = {
        "tenant_id": tenant.tenant_id,
        "tenant_name": tenant.tenant_name,
        "preferences": []
    }

    for pref in preferences:
        category = db.query(Category).filter(Category.category_id == pref.category_id).first()
        event = db.query(Event).filter(Event.event_id == pref.event_id).first()
        channel = db.query(Channel).filter(Channel.channel_id == pref.channel_id).first()

        category_obj = next((cat for cat in response["preferences"] if cat["category_id"] == category.category_id), None)
        if not category_obj:
            category_obj = {
                "category_id": category.category_id,
                "category_name": category.category_name, 
                "events": []
            }
            response["preferences"].append(category_obj)

        event_obj = next((event_obj for event_obj in category_obj["events"] if event_obj["event_id"] == event.event_id), None)
        if not event_obj:
            event_obj = {
                "event_id": event.event_id,
                "event_name": event.event_name,  
                "channels": []
            }
            category_obj["events"].append(event_obj)

        event_obj["channels"].append({
            "channel_id": channel.channel_id,
            "channel_name": channel.channel_name  
        })

    return response


@app.post("/users/{user_id}/preferences")
def create_user_preferences(user_id: int, request: UserPreferencesPostRequest, db: Session = Depends(get_db)):
    try:
        tenant = db.query(Tenant).filter(Tenant.tenant_id == request.tenant_id).first()
        if not tenant:
            raise HTTPException(status_code=404, detail=f"Tenant with ID {request.tenant_id} not found")

        new_preferences = []

        for category in request.preferences:
            db_category = db.query(Category).filter(Category.category_id == category.category_id).first()
            if not db_category:
                raise HTTPException(status_code=400, detail=f"Category {category.category_id} not found")

            for event in category.events:
                db_event = db.query(Event).filter(
                    Event.event_id == event.event_id, Event.category_id == category.category_id
                ).first()
                if not db_event:
                    raise HTTPException(status_code=400, detail=f"Event {event.event_id} not found")

                for channel in event.channels:
                    db_channel = db.query(Channel).filter(Channel.channel_id == channel.channel_id).first()
                    if not db_channel:
                        raise HTTPException(status_code=400, detail=f"Channel {channel.channel_id} not found")

                    new_preferences.append(
                        UserPreference(
                            user_id=user_id,  # Now using path parameter instead of request body
                            tenant_id=request.tenant_id,
                            category_id=category.category_id,
                            event_id=event.event_id,
                            channel_id=channel.channel_id,
                        )
                    )

        db.bulk_save_objects(new_preferences)
        db.commit()

        return {"message": "User Preferences added successfully", "total_rows_inserted": len(new_preferences)}

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database Integrity Error: {repr(e)}")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {repr(e)}")


@app.get("/users/{user_id}/preferences", response_model=UserPreferencesRequest)
def get_user_preferences(user_id: int, db: Session = Depends(get_db)):
    preferences = db.query(UserPreference).filter(UserPreference.user_id == user_id).all()

    if not preferences:
        raise HTTPException(status_code=404, detail=f"User with ID {user_id} has no preferences")

    response = {
        "user_id": user_id,
        "tenant_id": preferences[0].tenant_id,
        "preferences": []
    }

    categories_map = {}
    for pref in preferences:
        category = db.query(Category).filter(Category.category_id == pref.category_id).first()
        event = db.query(Event).filter(Event.event_id == pref.event_id).first()
        channel = db.query(Channel).filter(Channel.channel_id == pref.channel_id).first()

        if category.category_id not in categories_map:
            categories_map[category.category_id] = {
                "category_id": category.category_id,
                "category_name": category.category_name,
                "events": []
            }

        category_obj = categories_map[category.category_id]
        
        event_obj = next((e for e in category_obj["events"] if e["event_id"] == event.event_id), None)
        if not event_obj:
            event_obj = {
                "event_id": event.event_id,
                "event_name": event.event_name,
                "channels": []
            }
            category_obj["events"].append(event_obj)

        event_obj["channels"].append({
            "channel_id": channel.channel_id,
            "channel_name": channel.channel_name
        })

    response["preferences"] = list(categories_map.values())
    
    return response

@app.get("/preferences/channels",  response_model=list[ChannelResponse])
def get_channels(db: Session = Depends(get_db)):
    channel = db.query(Channel).all()
    return channel


@app.get("/preferences/categories",  response_model=list[CategoryResponse])
def get_categories(db: Session = Depends(get_db)):
    category = db.query(Category).all()
    return category
@app.get("/preferences/events",  response_model=list[EventResponse])
def get_events(db: Session = Depends(get_db)):
    event = db.query(Event).all()
    return event
