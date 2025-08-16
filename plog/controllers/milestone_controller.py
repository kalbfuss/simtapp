import logging

from datetime import datetime, timezone

from plog.models.milestone import Milestone

class MilestoneController:
    """
    Controller class for managing milestones.

    :param session: SQLAlchemy session for database operations
    """

    def __init__(self, session):
        """
        Initialize the MilestoneController.

        :param session: SQLAlchemy session
        """
        self.session = session

    def add(self, milestone):
        """
        Add a new milestone to the database.

        :param milestone: Milestone instance to add
        :return: The added Milestone instance (with assigned id)
        :raises ValueError: If parent milestone exists and project_id does not match
        """
        # Ensure milestone is linked to same project as parent if exists.
        if milestone.parent is not None:
            with self.session.no_autoflush:
                milestone.project = milestone.parent.project
        # Ensure milestone is linked to project.
        if milestone.project is None:        
            raise ValueError("Milestone must be linked to project.")
        # Set creation and last_modified timestamps.
        now = datetime.now(timezone.utc)
        milestone.created = now
        milestone.last_modified = now
        # Add milestone to database and commit.
        self.session.add(milestone)
        self.session.commit()
        return milestone

    def update(self, milestone):
        """
        Update an existing milestone in the database.
        
        :param project: Milestone instance with updated values
        :raises ValueError: If the milestone is not found
        :return: The updated milestone instance
        """
        # Ensure the milestone exists in the database.        
        db_milestone = self.session.query(Milestone).filter(Milestone.id == milestone.id).first()
        if db_milestone is None:
            raise ValueError("Milestone not found.")
        # Ensure milestone is linked to same project as parent if exists.
        if milestone.parent is not None:
            with self.session.no_autoflush:
                milestone.project = milestone.parent.project
        # Ensure milestone is linked to project.
        if milestone.project is None:        
            raise ValueError("Milestone must be linked to project.")
        # Update last_modified timestamp and commit.
        milestone.last_modified = datetime.now(timezone.utc)
        self.session.commit()
        return milestone

    def delete(self, milestone):
        """
        Remove a milestone and all its descendants from the database.

        :param milestone: Milestone instance to delete
        :raises ValueError: If milestone is not found in the database
        :return: List of milestone instance that were removed by this call
        """
        # Helper to recursively collect all child projects.
        def collect_children(milestone):
            if milestone.children is None:
                return []
            children = [ milestone for milestone in milestone.children ]
            for child in milestone.children:
                children.extend(collect_children(child))
            return children
       
        db_milestone = self.session.query(Milestone).filter(Milestone.id == milestone.id).first()
        # Ensure the project exists in the database.
        if db_milestone is None:
            raise ValueError("Milestone not found.")
        # Collect all objects that will be deleted.
        deleted = [ milestone ]    
        deleted.extend(collect_children(milestone))
        # Delete the milestone and its children.
        self.session.delete(milestone)
        self.session.commit()
        return deleted

    def get_all(self, project=None):
        """
        Return all current milestones (not deleted). Optionally filter by project_id.

        :param project: Project for which milestones shall be returned (optional)
        :return: List of all Milestone objects
        """
        query = self.session.query(Milestone)
        if project is not None:
            query = query.filter(Milestone.project_id == project.id)
        return query.all()

    def get_by_id(self, id):
        """
        Return the milestone with the given ID from the database.

        :param id: ID of the milestone
        :raises ValueError: If no milestone is found
        :return: The milestone instance
        """
        milestone = self.session.query(Milestone).filter(Milestone.id == id).first()
        if milestone is None:
            raise ValueError("Milestone not found.")
        return milestone

    def get_history(self, milestone):
        """
        Return all previous versions of a milestone in the database.

        :param project: Milestone instance for which the history shall be retrieved
        :return: List of historical milestone instances
        """
        return [ version for version in milestone.versions[::-1] ]
    
    def possible_parents(self, milestone=None):
        """
        Returns a dictionary mapping 'title (ID)' to project IDs for all existing
        projects except the given project. Useful for parent selection in forms.

        :param project: Milestone instance for which possible parents shall be
            returned. Possible parents must belong to the same project.
        :return: Dictionary mapping 'title (ID)' to project IDs
        """
        query = self.session.query(Milestone)
        if milestone is not None:
            query = query.filter(Milestone.id != milestone.id)
            query = query.filter(Milestone.project_id == milestone.project_id)
        milestones = query.all()
        return {f"{m.title} (ID {m.id})": m.id for m in milestones}