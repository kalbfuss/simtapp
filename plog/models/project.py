import logging
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Date,
    DateTime,
    UniqueConstraint,
    Index,
    event,
    inspect
)
from sqlalchemy.orm import relationship, backref

from plog.models.common import Base

class Project(Base):
    """
    Data model for the persistent storage of project objects.
    """
    __versioned__ = {}
    __tablename__ = "projects"

    project_id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    organization = Column(String(255), default="")
    project_manager = Column(String(255), default="")
    project_sponsor = Column(String(255), default="")
    initiation_date = Column(Date, nullable=True)
    closure_date = Column(Date, nullable=True)
    parent_id = Column(Integer, ForeignKey("projects.project_id"), nullable=True)
    created = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))
    last_modified = Column(DateTime, nullable=False, default=datetime.now(timezone.utc))

    parent = relationship(
        "Project",
        remote_side=[project_id],
        backref=backref("children", cascade="all, delete-orphan", passive_deletes=True)
    )
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")
        
    def __repr__(self):
        return f"<Project(title={self.title!r}, organization={self.organization!r})>"