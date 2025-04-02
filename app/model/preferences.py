from sqlalchemy import Column, Integer, String, ForeignKey
from pydantic import BaseModel
from sqlalchemy.ext.declarative import declarative_base
from typing import List


Base = declarative_base()
class Tenant(Base):
    __tablename__ = "tenants"
    tenant_id = Column(Integer, primary_key=True, index=True)
    tenant_name = Column(String, index=True)

class Category(Base):
    __tablename__ = "categories"
    category_id = Column(Integer, primary_key=True, index=True)
    category_name = Column(String, index=True)

class Event(Base):
    __tablename__ = "events"
    event_id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    event_name = Column(String, index=True)

class Channel(Base):
    __tablename__ = "channels"
    channel_id = Column(Integer, primary_key=True, index=True)
    channel_name = Column(String, index=True)

class TenantPreference(Base):
    __tablename__ = "tenant_preferences"
    tenant_pref_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id"))
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    event_id = Column(Integer, ForeignKey("events.event_id"))
    channel_id = Column(Integer, ForeignKey("channels.channel_id"))

class UserPreference(Base):
    __tablename__ = "user_preferences"
    user_pref_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.tenant_id"))
    category_id = Column(Integer, ForeignKey("categories.category_id"))
    event_id = Column(Integer, ForeignKey("events.event_id"))
    channel_id = Column(Integer, ForeignKey("channels.channel_id"))

class ChannelData(BaseModel):
    channel_id: int
    channel_name: str  
class EventData(BaseModel):
    event_id: int
    event_name: str  
    channels: List[ChannelData]

class CategoryData(BaseModel):
    category_id: int
    category_name: str  
    events: List[EventData]

class TenantPreferencesRequest(BaseModel):
    tenant_id: int
    preferences: List[CategoryData]

class UserPreferencesRequest(BaseModel):
    user_id: int
    tenant_id: int
    preferences: List[CategoryData]

class ChannelID(BaseModel):
    channel_id: int

class EventID(BaseModel):
    event_id: int
    channels: List[ChannelID]

class CategoryID(BaseModel):
    category_id: int
    events: List[EventID]

class TenantPreferencesPostRequest(BaseModel):
    preferences: List[CategoryID]

class UserPreferencesPostRequest(BaseModel):
    # user_id: int
    tenant_id: int
    preferences: List[CategoryID]

class ChannelResponse(BaseModel):
    channel_id: int
    channel_name: str

class CategoryResponse(BaseModel):
    category_id: int
    category_name: str

class EventResponse(BaseModel):
    event_id: int
    category_id: int
    event_name: str
