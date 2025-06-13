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

    def add_milestone(self, title, parent_id=None, description="", initial_baseline_date=None, latest_baseline_date=None, acceptance_criteria=None):
        """
        Add a new milestone.

        :param title: Title of the milestone (must be unique)
        :param parent_id: ID of the parent milestone (optional)
        :param description: Description of the milestone (optional)
        :param initial_baseline_date: Initial baseline date (optional)
        :param latest_baseline_date: Latest baseline date (optional)
        :param acceptance_criteria: List of acceptance criteria (optional)
        :raises ValueError: If the title is not unique
        :return: The created Milestone object
        """
        if self.session.query(Milestone).filter_by(title=title).first():
            raise ValueError("Milestone title must be unique.")
        milestone = Milestone(
            title=title,
            parent_id=parent_id,
            description=description,
            initial_baseline_date=initial_baseline_date,
            latest_baseline_date=latest_baseline_date,
            acceptance_criteria=acceptance_criteria or []
        )
        self.session.add(milestone)
        self.session.commit()
        return milestone

    def update_milestone(self, milestone_id, new_title=None, description=None, initial_baseline_date=None, latest_baseline_date=None, acceptance_criteria=None):
        """
        Update an existing milestone.

        :param milestone_id: ID of the milestone to update
        :param new_title: New title (optional)
        :param description: New description (optional)
        :param initial_baseline_date: New initial baseline date (optional)
        :param latest_baseline_date: New latest baseline date (optional)
        :param acceptance_criteria: New acceptance criteria (optional)
        :raises ValueError: If the milestone is not found or the new title is not unique
        :return: The updated Milestone object
        """
        milestone = (
            self.session.query(Milestone)
            .filter(Milestone.id == milestone_id)
            .order_by(Milestone.version.desc())
            .first()
        )
        if not milestone:
            raise ValueError("Milestone not found.")
        if new_title and new_title != milestone.title:
            if self.session.query(Milestone).filter_by(title=new_title).first():
                raise ValueError("Milestone title must be unique.")
            milestone.title = new_title
        if description is not None:
            milestone.description = description
        if initial_baseline_date is not None:
            milestone.initial_baseline_date = initial_baseline_date
        if latest_baseline_date is not None:
            milestone.latest_baseline_date = latest_baseline_date
        if acceptance_criteria is not None:
            milestone.acceptance_criteria = acceptance_criteria
        milestone.version += 1
        self.session.commit()
        return milestone

    def delete_milestone(self, milestone_id):
        """
        Mark one or more milestones as deleted.

        :param milestone_id: ID of the milestone to delete
        :raises ValueError: If no milestone is found
        :return: List of deleted Milestone objects
        """
        milestones = (
            self.session.query(Milestone)
            .filter(Milestone.id == milestone_id)
            .all()
        )
        if not milestones:
            raise ValueError("Milestone not found.")
        for milestone in milestones:
            milestone.deleted = 1
        self.session.commit()
        return milestones

    def get_milestones(self):
        """
        Return all milestones.

        :return: List of all Milestone objects
        """
        return self.session.query(Milestone).all()

    def get_milestone(self, milestone_id):
        """
        Return the latest non-deleted milestone with the given ID.

        :param milestone_id: ID of the milestone
        :raises ValueError: If no milestone is found
        :return: The Milestone object
        """
        milestone = (
            self.session.query(Milestone)
            .filter(Milestone.id == milestone_id, Milestone.deleted == 0)
            .order_by(Milestone.version.desc())
            .first()
        )
        if not milestone:
            raise ValueError("Milestone not found.")
        return milestone