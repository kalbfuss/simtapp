from datetime import datetime, timezone
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

    def add_project(self, project):
        """
        Add a new project to the database.

        :param project: Project instance to add
        :return: The created Project instance (with assigned project_id)
        """
        
        # Set creation and last_modified timestamps.
        now = datetime.now(timezone.utc)
        project.created = now
        project.last_modified = now
        # Add project to database and commit.
        self.session.add(project)
        self.session.commit()
        return project

    def update_project(self, project):
        """
        Update an existing project in the database.

        :param project: Project instance with updated values
        :raises ValueError: If the project is not found
        :return: The updated Project object
        """
        db_project = self.session.query(Project).filter(Project.project_id == project.project_id).first()
        # Ensure the project exists in the database.
        if db_project is None:
            raise ValueError("Project not found.")
        # Update last_modified timestamp and commit.
        project.last_modified = datetime.now(timezone.utc)
        self.session.commit()
        return project

    def delete_project(self, project):
        """
        Remove a project and all its descendants from the database.

        :param project: Project instance to delete
        :raises ValueError: If project is not found in the datbase.
        :return: List of Project objects that were removed by this call
        """
        
        # Helper to recursively collect all child projects.
        def collect_children(project):
            if project.children is None:
                return []
            children = [ project for project in project.children ]
            for child in project.children:
                children.extend(collect_children(child))
            return children
       
        db_project = self.session.query(Project).filter(Project.project_id == project.project_id).first()
        # Ensure the project exists in the database.
        if db_project is None:
            raise ValueError("Project not found.")
        # Collect all objects that will be deleted.
        deleted_projects = [ project ]    
        deleted_projects.extend(collect_children(project))
        # Delete the project and its children.
        self.session.delete(project)
        self.session.commit()
        return deleted_projects

    def get_projects(self):
        """
        Return all projects in the database.

        :return: List of all current Project objects
        """
        return self.session.query(Project).all()

    def get_project(self, project_id):
        """
        Return the project with the given ID from the database.

        :param project_id: ID of the project
        :raises ValueError: If no project is found
        :return: The Project object
        """
        project = self.session.query(Project).filter(Project.project_id == project_id).first()
        if project is None:
            raise ValueError("Project not found.")
        return project

    def get_project_history(self, project):
        """
        Return all previous versions of a project in the database.

        :param project: Project instance for which the history shall be retrieved
        :return: List of ProjectVersion objects, starting with the latest version
        """
        return [ version for version in project.versions[::-1] ]