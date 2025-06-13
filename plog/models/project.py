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
from sqlalchemy.orm import relationship, declarative_base

#from plog.models.milestone import Milestone

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        # The combination of project_id and version must be unique.
        UniqueConstraint("project_id", "version", name="uq_project_project_id_version"),
        # Index for fast filtering by project_id
        Index("ix_projects_project_id", "project_id"),
        # Index for fast sorting by version
        Index("ix_projects_version", "version"),
        # Index for fast filtering by deleted
        Index("ix_projects_deleted", "deleted"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    title = Column(String(255), nullable=False)  # unique entfernt
    description = Column(Text, default="")
    organization = Column(String(255), default="")
    project_manager = Column(String(255), default="")
    project_sponsor = Column(String(255), default="")
    initiation_date = Column(Date, nullable=True)
    closure_date = Column(Date, nullable=True)
    parent_id = Column(Integer, ForeignKey("projects.project_id"), nullable=True)
    deleted = Column(Integer, nullable=False, default=0)  # 0 = not deleted, 1 = deleted

    parent = relationship("Project", remote_side=[project_id], backref="children")
    milestones = relationship("Milestone", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(title={self.title!r}, organization={self.organization!r})>"