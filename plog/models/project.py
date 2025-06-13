from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Date,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base

#from plog.models.milestone import Milestone

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    __table_args__ = (
        UniqueConstraint("title", name="uq_project_title"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    title = Column(String(255), nullable=False, unique=True)
    description = Column(Text, default="")
    organization = Column(String(255), default="")
    project_manager = Column(String(255), default="")
    project_sponsor = Column(String(255), default="")
    initiation_date = Column(Date, nullable=True)
    closure_date = Column(Date, nullable=True)
    parent_id = Column(Integer, ForeignKey("projects.project_id"), nullable=True)
    deleted = Column(Integer, nullable=False, default=0)  # 0 = not deleted, 1 = deleted

    parent = relationship("Project", remote_side=[project_id], backref="children")

    def __repr__(self):
        return f"<Project(title={self.title!r}, organization={self.organization!r})>"