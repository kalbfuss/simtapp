import unittest
import tempfile
import os

from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from plog.models.milestone import Milestone, Base
#from plog.models.project import Project
from plog.controllers.milestone_controller import MilestoneController
from plog.controllers.project_controller import ProjectController

class TestMilestoneController(unittest.TestCase):
    """
    Unit tests for the MilestoneController class.

    This test suite sets up a temporary SQLite database for each test case and verifies
    the correct behavior of the MilestoneController methods.
    """
    def setUp(self):
        """
        Set up a temporary SQLite database file in the local folder and initialize the MilestoneController.
        This method is called before each test method.
        """
        self.db_path = os.path.abspath("test_milestones.sqlite")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.controller = MilestoneController(self.session)
        self.project_controller = ProjectController(self.session)

    def tearDown(self):
        """
        Tear down the temporary database file and close all connections.
        This method is called after each test method.
        """
        self.session.close()
        self.engine.dispose()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_add_milestone(self):
        """
        Test the add_milestone method of MilestoneController.

        This test verifies that a milestone can be created and stored in the database
        with the correct attributes, and that the returned object contains the expected values.
        It also verifies that multiple milestones can be added to the same project and are linked correctly.
        """
        # Create a parent project
        project = self.project_controller.add_project(title="Parent project")

        # Add first milestone
        milestone = self.controller.add_milestone(
            title="First test milestone",
            project_id=project.project_id,
            description="First description",
            initial_baseline_date=date(2025, 6, 12),
            latest_baseline_date=date(2025, 6, 20),
            acceptance_criteria="Criteria"
        )
        self.assertIsNotNone(milestone.id)
        self.assertEqual(milestone.title, "First test milestone")
        self.assertEqual(milestone.description, "First description")
        self.assertEqual(milestone.initial_baseline_date, date(2025, 6, 12))
        self.assertEqual(milestone.latest_baseline_date, date(2025, 6, 20))
        self.assertEqual(milestone.acceptance_criteria, "Criteria")
        self.assertEqual(milestone.project_id, project.project_id)

        # Add a second milestone to the same project
        milestone2 = self.controller.add_milestone(
            title="First test milestone",  # identischer Titel erlaubt
            project_id=project.project_id,
            description="Second description"
        )
        self.assertIsNotNone(milestone2.id)
        self.assertNotEqual(milestone.milestone_id, milestone2.milestone_id)
        self.assertEqual(milestone2.project_id, project.project_id)
        self.assertEqual(milestone2.title, "First test milestone")
        self.assertEqual(milestone2.description, "Second description")

    def test_get_milestone(self):
        """
        Test the get_milestone method of MilestoneController.

        This test verifies that a milestone can be retrieved from the database
        by its ID and that the returned object contains the expected values.
        It also checks that a ValueError is raised if the milestone does not exist.
        """
        # Create a parent project
        project = self.project_controller.add_project(title="Parent project")

        # Add a milestone first
        milestone = self.controller.add_milestone(
            title="Get test milestone",
            project_id=project.project_id,
            description="Description",
            initial_baseline_date=date(2025, 7, 1),
            latest_baseline_date=date(2025, 7, 10),
            acceptance_criteria="Criteria"
        )
        # Retrieve the milestone by ID
        fetched = self.controller.get_milestone(milestone.milestone_id)
        self.assertEqual(fetched.id, milestone.id)
        self.assertEqual(fetched.title, "Get test milestone")
        self.assertEqual(fetched.description, "Description")
        self.assertEqual(fetched.initial_baseline_date, date(2025, 7, 1))
        self.assertEqual(fetched.latest_baseline_date, date(2025, 7, 10))
        self.assertEqual(fetched.acceptance_criteria, "Criteria")
        self.assertEqual(fetched.project_id, project.project_id)
        # Test for non-existent milestone
        with self.assertRaises(ValueError):
            self.controller.get_milestone(99999)

    def test_delete_milestone(self):
        """
        Test the delete_milestone method of MilestoneController.

        This test verifies that a milestone and its child milestones are marked as deleted,
        that a ValueError is raised for non-existent milestones, and that only the correct milestones
        are returned by delete_milestone.
        """
        # Create a parent project
        project = self.project_controller.add_project(title="Delete Test Project")

        # Add parent milestone
        parent = self.controller.add_milestone(
            title="Parent milestone",
            project_id=project.project_id,
            description="Parent milestone"
        )
        # Add child milestone
        child = self.controller.add_milestone(
            title="Child milestone",
            project_id=project.project_id,
            parent_id=parent.milestone_id,
            description="Child milestone"
        )
        # Add another child milestone
        child2 = self.controller.add_milestone(
            title="Child milestone 2",
            project_id=project.project_id,
            parent_id=parent.milestone_id,
            description="Child milestone 2"
        )
        # Delete parent milestone (should recursively delete children)
        deleted = self.controller.delete_milestone(parent.milestone_id)
        deleted_ids = {m.id for m in deleted}
        self.assertIn(parent.id, deleted_ids)
        self.assertIn(child.id, deleted_ids)
        self.assertIn(child2.id, deleted_ids)
        # All should be marked as deleted
        for m in [parent, child, child2]:
            self.assertEqual(m.deleted, 1)
        # Trying to delete a non-existent milestone should raise ValueError
        with self.assertRaises(ValueError):
            self.controller.delete_milestone(999999)

    def test_update_milestone(self):
        """
        Test the update_milestone method of MilestoneController.

        This test verifies that all fields of a milestone can be updated and that the version is incremented.
        It also checks that updating a non-existing milestone raises a ValueError and that the title uniqueness is enforced.
        """
        # Create a parent project
        project = self.project_controller.add_project(title="Update Test Project")

        # Add a milestone
        milestone = self.controller.add_milestone(
            title="Old title",
            project_id=project.project_id,
            description="Old description",
            initial_baseline_date=date(2025, 8, 1),
            latest_baseline_date=date(2025, 8, 10),
            acceptance_criteria="Old criteria"
        )
        # Update the milestone
        updated = self.controller.update_milestone(
            milestone_id=milestone.milestone_id,
            title="New title",
            description="New description",
            initial_baseline_date=date(2025, 9, 1),
            latest_baseline_date=date(2025, 9, 10),
            acceptance_criteria="New criteria"
        )
        self.assertEqual(updated.title, "New title")
        self.assertEqual(updated.description, "New description")
        self.assertEqual(updated.initial_baseline_date, date(2025, 9, 1))
        self.assertEqual(updated.latest_baseline_date, date(2025, 9, 10))
        self.assertEqual(updated.acceptance_criteria, "New criteria")
        self.assertEqual(updated.version, 2)
        # Ensure updating a non-existing milestone fails
        with self.assertRaises(ValueError):
            self.controller.update_milestone(99999)
        # Ensure title uniqueness is NOT enforced anymore
        milestone2 = self.controller.add_milestone(
            title="New title",
            project_id=project.project_id
        )
        # Es darf kein Fehler mehr auftreten, beide Milestones existieren mit gleichem Titel
        self.assertNotEqual(milestone.milestone_id, milestone2.milestone_id)
        self.assertEqual(milestone2.title, "New title")
        # Ensure title uniqueness is NOT enforced anymore in update
        milestone3 = self.controller.update_milestone(
            milestone_id=milestone.milestone_id,
            title="Another milestone title"
        )
        self.assertEqual(milestone3.title, "Another milestone title")
        # Es darf kein Fehler auftreten, wenn ein anderer Milestone denselben Titel hat
        milestone4 = self.controller.update_milestone(
            milestone_id=milestone2.milestone_id,
            title="Another milestone title"
        )
        self.assertEqual(milestone4.title, "Another milestone title")

if __name__ == "__main__":
    unittest.main()
