from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Date,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

from plog.models.project import Project, Base

#Base = declarative_base()

class Milestone(Base):
    __tablename__ = "milestones"
    __table_args__ = (
        # The combination of milestone_id, and version must be unique.
        UniqueConstraint("milestone_id", "version", name="uq_milestone_milestone_id_version"),
        # Index for fast filtering by milestone_id
        Index("ix_milestones_milestone_id", "milestone_id"),
        # Index for fast sorting by version
        Index("ix_milestones_version", "version"),
        # Index for fast filtering by deleted
        Index("ix_milestones_deleted", "deleted"),
        # Index for fast filtering by project_id
        Index("ix_milestones_project_id", "project_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    milestone_id = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    title = Column(String(255), nullable=False)  # unique entfernt
    description = Column(Text, default="")
    initial_baseline_date = Column(Date, nullable=True)
    latest_baseline_date = Column(Date, nullable=True)
    acceptance_criteria = Column(Text, default="")
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("milestones.milestone_id"), nullable=True)
    deleted = Column(Integer, nullable=False, default=0)  # 0 = not deleted, 1 = deleted
    
    parent = relationship("Milestone", remote_side=[milestone_id], backref="children")
    project = relationship("Project", back_populates="milestones", uselist=True)

    def __repr__(self):
        return f"<Milestone(title={self.title!r}, description={self.description!r}, version={self.version!r})>"