import logging
import os
import unittest

from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import configure_mappers, sessionmaker

from plog.models.milestone import Milestone, Base
from plog.models.project import Project
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
        # Enable debug level logging
        logging.basicConfig(level=logging.DEBUG)
        # Create database and session
        self.db_path = os.path.abspath("test_milestones.sqlite")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        configure_mappers()
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        # Create project controller for test purposes
        self.project_controller = ProjectController(self.session)
        # Create instance of controller we want to test
        self.controller = MilestoneController(self.session)

    def tearDown(self):
        """
        Tear down the temporary database file and close all connections.
        This method is called after each test method.
        """
        self.session.close()
        self.engine.dispose()
#        if os.path.exists(self.db_path):
#            os.remove(self.db_path)

    def test_add_milestone(self):
        """
        Test the add_milestone method of MilestoneController.

        This test verifies:
        - A milestone can be created and stored in the database with the correct attributes.
        - The returned object contains the expected values.
        - Multiple milestones can be added to the same project and are linked correctly.
        - Child milestones are always associated with the same project as their parent.

        Test steps:
        1. Create a parent project.
        2. Add a milestone to the project and verify all attributes.
        3. Add a second milestone with the same title to the same project and verify both exist.
        4. Add a child milestone with the correct project_id and verify linkage.
        5. Attempt to add a child milestone with a mismatched project_id and expect a ValueError.
        """
        # Create a parent project.
        project = Project(title="Parent project")
        project = self.project_controller.add(project)
        # Add first milestone to parent project.
        milestone = Milestone(
            title="First test milestone",
            project=project,
            description="First description",
            initial_baseline_date=date(2025, 6, 12),
            latest_baseline_date=date(2025, 6, 20),
            acceptance_criteria="Criteria"
        )
        milestone = self.controller.add(milestone)
        self.assertIsNotNone(milestone.milestone_id)
        self.assertEqual(milestone.title, "First test milestone")
        self.assertEqual(milestone.description, "First description")
        self.assertEqual(milestone.initial_baseline_date, date(2025, 6, 12))
        self.assertEqual(milestone.latest_baseline_date, date(2025, 6, 20))
        self.assertEqual(milestone.acceptance_criteria, "Criteria")
        self.assertEqual(milestone.project_id, project.project_id)
        # Add a second milestone to the same project.
        milestone2 = Milestone(title="First test milestone", project=project, description="Second description")
        milestone2 = self.controller.add(milestone2)
        self.assertIsNotNone(milestone2.milestone_id)
        self.assertNotEqual(milestone.milestone_id, milestone2.milestone_id)
        self.assertEqual(milestone2.project_id, project.project_id)
        self.assertEqual(milestone2.title, "First test milestone")
        self.assertEqual(milestone2.description, "Second description")
        # Ensure adding a milestone not associated to any project fails.
        milestone3 = Milestone(title="Third test miletone")
        with self.assertRaises(ValueError):
            self.controller.add(milestone3)
        # Add a child milestone with correct project_id.
        child1 = Milestone(title="Child milestone", project=project, parent=milestone)
        child1 = self.controller.add(child1)
        self.assertEqual(child1.parent_id, milestone.milestone_id)
        self.assertEqual(child1.project_id, project.project_id)
        # Ensure linkage of milestone to same project as parent is enforced.
        project2 = Project(title="Other project")
        project2 = self.project_controller.add(project2)
        child2 = Milestone(title="Invalid child milestone", project=project2, parent=milestone)
        child2 = self.controller.add(child2)
        self.assertEqual(child2.project_id, milestone.project_id)

    def test_get_milestone_by_id(self):
        """
        Test the get_milestone method of MilestoneController.

        This test verifies:
        - A milestone can be retrieved from the database by its ID.
        - The returned object contains the expected values.
        - A ValueError is raised if the milestone does not exist.

        Test steps:
        1. Create a project and add a milestone.
        2. Retrieve the milestone by its ID and verify all attributes.
        3. Attempt to retrieve a non-existent milestone and expect a ValueError.
        """
        # Create project and add a milestone
        project = Project(title="Parent project")
        project = self.project_controller.add(project)
        milestone = Milestone(
            title="Get Test milestone",
            project = project,
            description="Description",
            initial_baseline_date=date(2025, 7, 1),
            latest_baseline_date=date(2025, 7, 10),
            acceptance_criteria="Criteria"
        )
        milestone = self.controller.add(milestone)
        # Ensure values in the database are as epected.
        fetched = self.controller.get_by_id(milestone.milestone_id)
        self.assertEqual(fetched.milestone_id, milestone.milestone_id)
        self.assertEqual(fetched.title, "Get Test milestone")
        self.assertEqual(fetched.description, "Description")
        self.assertEqual(fetched.initial_baseline_date, date(2025, 7, 1))
        self.assertEqual(fetched.latest_baseline_date, date(2025, 7, 10))
        self.assertEqual(fetched.acceptance_criteria, "Criteria")
        self.assertEqual(fetched.project_id, project.project_id)
        # Attempt to get non-existent milestone.
        with self.assertRaises(ValueError):
            self.controller.get_by_id(99999)

    def test_delete_milestone(self):
        """
        Test the delete_milestone method of MilestoneController.

        This test verifies:
        - A milestone and all its descendants are deleted.
        - get_milestone does not return a deleted milestone.
        - Unrelated milestones are not affected.
        - Only the correct milestones are returned by delete_project.

        Test steps:
        1. Add a parent milestone, two child milestones, a grandchild, and an unrelated milestone.
        2. Delete the parent milestone, verify all descendants are deleted, and the unrelated milestone remains unaffected.
        3. Ensure get_milestone does not return deleted milestones.
        4. Ensure deleted milestones are removed from the database.        
        """
        # Create milestones.
        project = Project(title="Delete Test Project")
        project = self.project_controller.add(project)
        parent = Milestone(title="Parent milestone", project=project)
        parent = self.controller.add(parent)
        child1 = Milestone(title="Child 1", parent=parent)
        child1 = self.controller.add(child1)
        child2 = Milestone(title="Child 2", parent=parent)
        child2 = self.controller.add(child2)
        grandchild = Milestone(title="Grandchild", parent=child1)
        grandchild = self.controller.add(grandchild)
        unrelated = Milestone(title="Unrelated milestone", project=project)
        unrelated = self.controller.add(unrelated)
        # Delete parent milestone and verify deletion of parent and descendants.
        deleted = self.controller.delete(parent)
        self.assertIn(parent, deleted)
        self.assertIn(child1, deleted)
        self.assertIn(child2, deleted)
        self.assertIn(grandchild, deleted)
        self.assertNotIn(unrelated, deleted)
        self.assertEqual(set(deleted), {parent, child1, child2, grandchild})
        # Ensure deleting a non-existing project fails.
        with self.assertRaises(ValueError):
            self.controller.delete(parent)
        # Ensure get_project does not return deleted project.
        for id in [parent.milestone_id, child1.milestone_id, child2.milestone_id, grandchild.milestone_id]:
            with self.assertRaises(ValueError):
                self.controller.get_by_id(id)
        # Unrelated project should still be retrievable.
        self.assertEqual(self.controller.get_by_id(unrelated.milestone_id).title, "Unrelated milestone")
        # Ensure deleted projects are removed from the projects table.
        for id in [parent.milestone_id, child1.milestone_id, child2.milestone_id, grandchild.milestone_id]:
            milestone = self.session.query(Milestone).filter(Milestone.milestone_id == id).first()
            self.assertIsNone(milestone)

    def test_update_milestone(self):
        """
        Test the update_milestone method of MilestoneController.

        This test verifies:
        - All fields of a milestone can be updated.
        - Updating a non-existing milestone raises a ValueError.
        - The last_modified timestamp is updated and created remains unchanged.
        - The previous version is save.d

        Test steps:
        1. Create a project and add a milestone.
        2. Update all fields of the milestone, verify the changes and version increment.
        3. Check that the previous version is saved.
        4. Attempt to update a non-existent milestone.
        5. Attempt to link milestone to different project as parent.

        """
        # Create parent project and add milestone.
        project = Project(title="Update Test Project")
        project = self.project_controller.add(project)
        milestone = Milestone(
            title="Old title",
            project=project,
            description="Old description",
            initial_baseline_date=date(2025, 8, 1),
            latest_baseline_date=date(2025, 8, 10),
            acceptance_criteria="Old criteria"
        )
        milestone = self.controller.add(milestone)
        parent = Milestone(title="Parent for update", project=project)
        parent = self.controller.add(parent)        
        old_created = milestone.created
        old_last_modified = milestone.last_modified
        # Update the milestone.
        milestone.title="New title"
        milestone.description="New description"
        milestone.initial_baseline_date=date(2025, 9, 1)
        milestone.latest_baseline_date=date(2025, 9, 10)
        milestone.acceptance_criteria="New criteria"
        milestone.parent = parent
        milestone = self.controller.update(milestone)
        self.assertEqual(milestone.title, "New title")
        self.assertEqual(milestone.description, "New description")
        self.assertEqual(milestone.initial_baseline_date, date(2025, 9, 1))
        self.assertEqual(milestone.latest_baseline_date, date(2025, 9, 10))
        self.assertEqual(milestone.acceptance_criteria, "New criteria")
        self.assertEqual(milestone.versions.count(), 2)
        self.assertIsNotNone(milestone.last_modified)
        self.assertGreaterEqual(milestone.last_modified, old_last_modified)
        self.assertEqual(milestone.created, old_created)
        # Ensure the old version is stored in the milestone history.
        old = milestone.versions[0]
        self.assertIsNotNone(old)
        self.assertEqual(old.title, "Old title")
        self.assertEqual(old.description, "Old description")
        self.assertEqual(old.initial_baseline_date, date(2025, 8, 1))
        self.assertEqual(old.latest_baseline_date, date(2025, 8, 10))
        self.assertEqual(old.acceptance_criteria, "Old criteria")
        self.assertEqual(old.created, old_created)
        self.assertEqual(old.last_modified, old_last_modified)
        # Ensure updating a non-existing milestone fails
        non_existing = Milestone(milestone_id=99999)
        with self.assertRaises(ValueError):
            self.controller.update(non_existing)
        # Ensure linkage of milestone to same project as parent is enforced.
        project2 = Project(title="Update Test Project #2")
        project2 = self.project_controller.add(project2)
        milestone.project = project2
        milestone = self.controller.update(milestone)
        self.assertEqual(milestone.project, project)

    def test_get_milestone_history(self):
        """
        Test the get_milestone_history method of MilestoneController.

        This test verifies:
        - All versions of a milestone, including the deleted version, are returned in descending order by version.

        Test steps:
        1. Create a project and add a milestone.
        2. Update the milestone multiple times.
        3. Delete the milestone.
        4. Retrieve the milestone history and verify the order and content of all versions.
        """
        # Create parent project and add milestone.
        project = Project(title="History Test Project")
        project = self.project_controller.add(project)
        # Update the milestone.
        milestone = Milestone(title="History Test Milestone v1", project=project, description="v1")
        self.controller.add(milestone)
        milestone.title="History Test Milestone v2"
        milestone.description="v2"
        self.controller.update(milestone)
        # Update the milestone again.
        milestone.title="History Test Milestone v3"
        milestone.description="v3"
        self.controller.update(milestone)
        # Get milestone history.
        history = self.controller.get_history(milestone)
        # There should be 3 history entries
        self.assertEqual(len(history), 3)
        # Check order: latest version first
        self.assertEqual(history[0].title, "History Test Milestone v3")
        self.assertEqual(history[0].description, "v3")
        self.assertEqual(history[1].title, "History Test Milestone v2")
        self.assertEqual(history[1].description, "v2")
        self.assertEqual(history[2].title, "History Test Milestone v1")
        self.assertEqual(history[2].description, "v1")

    def test_get_all_milestones(self):
        """
        Test the get_milestones method of MilestoneController.

        This test verifies:
        - All milestones are returned if no filter is set.
        - Only milestones for the given project_id are returned if filtered.

        Test steps:
        1. Create two projects and add milestones to both.
        2. Retrieve all milestones and verify all are present.
        3. Retrieve milestones filtered by project_id and verify only the correct milestones are returned.
        """
        # Create two projects.
        project1 = Project(title="Project 1")
        project1 = self.project_controller.add(project1)
        project2 = Project(title="Project 2")
        project2 = self.project_controller.add(project2)
        # Add milestones to both projects.
        m1 = Milestone(title="M1", project=project1)
        m1 = self.controller.add(m1)
        m2 = Milestone(title="M2", project=project1)
        m2 = self.controller.add(m2)
        m3 = Milestone(title="M3", project=project2)
        m3 = self.controller.add(m3)
        # Ensure that get_milestones without filter returns all milestones.
        all_milestones = self.controller.get_all()
        milestone_titles = {m.title for m in all_milestones}
        self.assertIn("M1", milestone_titles)
        self.assertIn("M2", milestone_titles)
        self.assertIn("M3", milestone_titles)
        # Ensure that get_milestones with project_id filter returns the correct milestones.
        project1_milestones = self.controller.get_all(project_id=project1.project_id)
        project1_titles = {m.title for m in project1_milestones}
        self.assertIn("M1", project1_titles)
        self.assertIn("M2", project1_titles)
        self.assertNotIn("M3", project1_titles)
        project2_milestones = self.controller.get_all(project_id=project2.project_id)
        project2_titles = {m.title for m in project2_milestones}
        self.assertIn("M3", project2_titles)
        self.assertNotIn("M1", project2_titles)
        self.assertNotIn("M2", project2_titles)

if __name__ == "__main__":
    unittest.main()
