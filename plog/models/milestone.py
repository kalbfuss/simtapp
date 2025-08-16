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
    Data model for the persistent storage of current milestone objects.
    """
    __versioned__ = {}
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, default="")
    initial_baseline_date = Column(Date, nullable=True)
    latest_baseline_date = Column(Date, nullable=True)
    acceptance_criteria = Column(Text, default="")
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    created = Column(DateTime, nullable=False)
    last_modified = Column(DateTime, nullable=False)

    parent = relationship(
        "Milestone",
        remote_side=[id],
        backref=backref("children", cascade="all, delete-orphan", passive_deletes=True)
    )
    project = relationship("Project", back_populates="milestones")

    def __repr__(self):
        return f"<Milestone(title={self.title!r})>"