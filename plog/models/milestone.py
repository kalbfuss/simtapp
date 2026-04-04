from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Date,
    DateTime,
)
from sqlalchemy.orm import relationship, backref

from plog.models.common import Base


class Milestone(Base):
    """
    Data model for the persistent storage of milestone objects.
    """
    __versioned__ = {}
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    initial_baseline_date = Column(Date, nullable=True)
    latest_baseline_date = Column(Date, nullable=True)
    acceptance_criteria = Column(Text, default="")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    created = Column(DateTime, nullable=False)
    last_modified = Column(DateTime, nullable=False)

    parent = relationship(
        "Milestone",
        remote_side=[id],
        backref=backref("children", cascade="all, delete-orphan", passive_deletes=True)
    )
    project = relationship("Project", back_populates="milestones")
    dates = relationship("MilestoneDate", back_populates="milestone", cascade="all, delete-orphan")

    def __repr__(self):
        return (
            f"<Milestone(id={self.id!r}, title={self.title!r}, description={self.description!r}, "
            f"initial_baseline_date={self.initial_baseline_date!r}, latest_baseline_date={self.latest_baseline_date!r}, "
            f"acceptance_criteria={self.acceptance_criteria!r}, project_id={self.project_id!r}, "
            f"parent_id={self.parent_id!r}, created={self.created!r}, last_modified={self.last_modified!r})>"
        )
    
    
class MilestoneDate(Base):
    """
    Data model for the persistent storage of milestone date objects.
    """
    __versioned__ = {}
    __tablename__ = "milestone_dates"

    id = Column(Integer, primary_key=True, autoincrement=True)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=False)
    date = Column(Date, nullable=False)
    entry_date = Column(Date, nullable=False)
    description = Column(Text, default="")
    created = Column(DateTime, nullable=False)
    last_modified = Column(DateTime, nullable=False)

    milestone = relationship("Milestone", back_populates="dates")

    def __repr__(self):
        return (
            f"<MilestoneDate(id={self.id!r}, milestone_id={self.milestone_id!r}, "
            f"date={self.date!r}, entry_date={self.entry_date!r}, "
            f"description={self.description!r}, created={self.created!r}, "
            f"last_modified={self.last_modified!r})>"
        )