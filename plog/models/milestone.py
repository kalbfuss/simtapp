from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    Date,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

from plog.models.project import Project

Base = declarative_base()

class Milestone(Base):
    __tablename__ = "milestones"
    __table_args__ = (
        UniqueConstraint("title", name="uq_milestone_title"),
        UniqueConstraint("id", "version", name="uq_milestone_id_version"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    version = Column(Integer, primary_key=True, nullable=False, default=1)
    title = Column(String(255), nullable=False, unique=True)
    description = Column(Text, default="")
    project_id = Column(Integer, ForeignKey("projects.id"), unique=True, nullable=True)  # 1:1 Beziehung
    parent_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    initial_baseline_date = Column(Date, nullable=True)
    latest_baseline_date = Column(Date, nullable=True)
    acceptance_criteria = Column(Text, default="")
    deleted = Column(Integer, nullable=False, default=0)  # 0 = nicht gelöscht, 1 = gelöscht
    
    parent = relationship("Milestone", remote_side=[id], backref="children")
    project = relationship("Project", back_populates="milestone", uselist=False)

    def __repr__(self):
        return f"<Milestone(title={self.title!r}, description={self.description!r}, version={self.version!r})>"