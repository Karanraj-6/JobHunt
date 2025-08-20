"""
Database models for the job automation application.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, DateTime, Boolean, Text, Integer, 
    ForeignKey, Enum, JSON, ARRAY
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

Base = declarative_base()

class JobsRaw(Base):
    """Raw job data from various sources."""
    __tablename__ = "jobs_raw"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String, nullable=False, index=True)
    fetched_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    payload = Column(JSONB if hasattr(Base.metadata.bind, 'dialect') and 
                    Base.metadata.bind.dialect.name == 'postgresql' else JSON, nullable=False)

class JobsClean(Base):
    """Cleaned and normalized job data."""
    __tablename__ = "jobs_clean"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_job_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False, index=True)
    company = Column(String, nullable=False, index=True)
    location = Column(String, nullable=False, index=True)
    employment_type = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    apply_url = Column(String, nullable=False)
    skills = Column(ARRAY(String) if hasattr(Base.metadata.bind, 'dialect') and 
                   Base.metadata.bind.dialect.name == 'postgresql' else JSON, nullable=True)
    seniority = Column(String, nullable=True, index=True)
    remote = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    posts = relationship("PostsReady", back_populates="job")
    posted_items = relationship("PostedItems", back_populates="job")

class PostsReady(Base):
    """Posts ready to be published."""
    __tablename__ = "posts_ready"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs_clean.id"), nullable=False)
    platform = Column(Enum("linkedin", "x", name="platform_enum"), nullable=False, index=True)
    caption = Column(Text, nullable=False)
    status = Column(Enum("pending", "posted", "failed", name="status_enum"), 
                   nullable=False, default="pending", index=True)
    scheduled_for = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    job = relationship("JobsClean", back_populates="posts")

class PostedItems(Base):
    """Successfully posted items."""
    __tablename__ = "posted_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs_clean.id"), nullable=False)
    platform = Column(Enum("linkedin", "x", name="platform_enum"), nullable=False, index=True)
    posted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    external_post_id = Column(String, nullable=True)  # Post URL or ID
    post_url = Column(String, nullable=True)  # Direct URL to the post
    
    # Relationships
    job = relationship("JobsClean", back_populates="posted_items")
    analytics = relationship("Analytics", back_populates="post")

class Analytics(Base):
    """Engagement analytics for posted items."""
    __tablename__ = "analytics"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID(as_uuid=True), ForeignKey("posted_items.id"), nullable=False)
    collected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    impressions = Column(Integer, nullable=True)
    likes = Column(Integer, nullable=True)
    comments = Column(Integer, nullable=True)
    shares = Column(Integer, nullable=True)
    clicks = Column(Integer, nullable=True)
    
    # Relationships
    post = relationship("PostedItems", back_populates="analytics")

