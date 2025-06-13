import uuid
from sqlalchemy import func

from plog.models.project import Project


class ProjectController:
    """
    Controller class for managing projects.

    :param session: SQLAlchemy session for database operations
    """
    def __init__(self, session):
        """
        Initialize the ProjectController.

        :param session: SQLAlchemy session
        """
        self.session = session

    def add_project(self, title, description="", organization="", project_manager="", project_sponsor="", initiation_date=None, closure_date=None, parent_id=None):
        """
        Add a new project.

        :param title: Title of the project
        :param description: Description of the project (optional)
        :param organization: Organization (optional)
        :param project_manager: Project manager (optional)
        :param project_sponsor: Project sponsor (optional)
        :param initiation_date: Initiation date (optional)
        :param closure_date: Closure date (optional)
        :param parent_id: ID of the parent project (optional)
        :return: The created Project object
        """
        # Generate a unique project_id.
        while True:
            candidate = uuid.uuid4().int >> 96
            if not self.session.query(Project).filter_by(project_id=candidate).first():
                project_id = candidate
                break
        project = Project(
            project_id=project_id,
            title=title,
            description=description,
            organization=organization,
            project_manager=project_manager,
            project_sponsor=project_sponsor,
            initiation_date=initiation_date,
            closure_date=closure_date,
            parent_id=parent_id
        )
        self.session.add(project)
        self.session.commit()
        return project

    def update_project(self, project_id, title=None, description=None, organization=None, project_manager=None, project_sponsor=None, initiation_date=None, closure_date=None, parent_id=None, new_project_id=None):
        """
        Update an existing project.

        :param project_id: ID of the project to update
        :param title: New title (optional)
        :param description: New description (optional)
        :param organization: New organization (optional)
        :param project_manager: New project manager (optional)
        :param project_sponsor: New project sponsor (optional)
        :param initiation_date: New initiation date (optional)
        :param closure_date: New closure date (optional)
        :param parent_id: New parent project ID (optional)
        :raises ValueError: If the project is not found
        :return: The updated Project object
        """
        project = (
            self.session.query(Project)
            .filter(Project.project_id == project_id, Project.deleted == 0)
            .order_by(Project.version.desc())
            .first()
        )
        if not project:
            raise ValueError("Project not found.")
        if title is not None:
            project.title = title
        if description is not None:
            project.description = description
        if organization is not None:
            project.organization = organization
        if project_manager is not None:
            project.project_manager = project_manager
        if project_sponsor is not None:
            project.project_sponsor = project_sponsor
        if initiation_date is not None:
            project.initiation_date = initiation_date
        if closure_date is not None:
            project.closure_date = closure_date
        if parent_id is not None:
            project.parent_id = parent_id
        project.version += 1
        self.session.commit()
        return project

    def delete_project(self, project_id):
        """
        Mark the specified project and all its child projects (linked via parent_id) as deleted.

        :param project_id: ID of the project to delete
        :raises ValueError: If no project is found
        :return: List of Project objects that were marked as deleted by this call
        """
        # Find the main project(s) with the given project_id and not already deleted
        projects = (
            self.session.query(Project)
            .filter(Project.project_id == project_id, Project.deleted == 0)
            .all()
        )
        if not projects:
            raise ValueError("Project not found.")
        # Track all projects marked as deleted in this call
        deleted_now = []
        # Mark the main project(s) as deleted
        for project in projects:
            project.deleted = 1
            deleted_now.append(project)
        # Recursively mark all child projects as deleted
        def mark_children_as_deleted(parent_project_id):
            children = self.session.query(Project).filter(Project.parent_id == parent_project_id, Project.deleted == 0).all()
            for child in children:
                child.deleted = 1
                deleted_now.append(child)
                mark_children_as_deleted(child.project_id)
        mark_children_as_deleted(project_id)
        self.session.commit()
        return deleted_now

    def get_projects(self):
        """
        Return all latest, non-deleted projects.

        :return: List of all latest, non-deleted Project objects
        """
        subquery = (
            self.session.query(
                Project.project_id,
                func.max(Project.version).label("max_version")
            )
            .filter(Project.deleted == 0)
            .group_by(Project.project_id)
            .subquery()
        )
        latest_projects = (
            self.session.query(Project)
            .join(subquery, (Project.project_id == subquery.c.project_id) & (Project.version == subquery.c.max_version))
            .filter(Project.deleted == 0)
            .all()
        )
        return latest_projects

    def get_project(self, project_id):
        """
        Return the latest non-deleted project with the given ID.

        :param project_id: ID of the project
        :raises ValueError: If no project is found
        :return: The Project object
        """
        project = (
            self.session.query(Project)
            .filter(Project.project_id == project_id, Project.deleted == 0)
            .order_by(Project.version.desc())
            .first()
        )
        if not project:
            raise ValueError("Project not found.")
        return project
