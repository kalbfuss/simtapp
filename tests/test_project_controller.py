import os
import unittest

from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from plog.models.project import Project, Base
from plog.controllers.project_controller import ProjectController

class TestProjectController(unittest.TestCase):
    """
    Unit tests for the ProjectController class.

    This test suite sets up a temporary SQLite database for each test case and verifies
    the correct behavior of the ProjectController methods.
    """
    def setUp(self):
        """
        Set up a temporary SQLite database file in the local folder and initialize the ProjectController.
        This method is called before each test method.
        """
        self.db_path = os.path.abspath("test_projects.sqlite")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.controller = ProjectController(self.session)

    def tearDown(self):
        """
        Tear down the temporary database file and close all connections.
        This method is called after each test method.
        """
        self.session.close()
        self.engine.dispose()
#        if os.path.exists(self.db_path):
#            os.remove(self.db_path)

    def test_add_project(self):
        """
        Test the add_project method of ProjectController.

        This test verifies that a project can be created and stored in the database
        with the correct attributes, and that the returned object contains the expected values.
        It also verifies that projects can be linked via the parent_id attribute.
        """
        project = self.controller.add_project(
            title="Add test project",
            description="Description",
            organization="Test organization",
            project_manager="Manager",
            project_sponsor="Sponsor",
            initiation_date=date(2025, 6, 12),
            closure_date=date(2025, 6, 20)
        )
        self.assertIsNotNone(project.id)
        self.assertIsNotNone(project.project_id)
        self.assertEqual(project.title, "Add test project")
        self.assertEqual(project.description, "Description")
        self.assertEqual(project.organization, "Test organization")
        self.assertEqual(project.project_manager, "Manager")
        self.assertEqual(project.project_sponsor, "Sponsor")
        self.assertEqual(project.initiation_date, date(2025, 6, 12))
        self.assertEqual(project.closure_date, date(2025, 6, 20))
        self.assertEqual(project.version, 1)
        self.assertEqual(project.deleted, 0)

        # Test linking via parent_id
        child_project = self.controller.add_project(
            title="Child Project",
            parent_id=project.project_id
        )
        self.assertEqual(child_project.parent_id, project.project_id)
        # Fetch child and check parent_id
        fetched_child = self.controller.get_project(child_project.project_id)
        self.assertEqual(fetched_child.parent_id, project.project_id)

    def test_get_project(self):
        """
        Test the get_project method of ProjectController.

        This test verifies that a project can be retrieved from the database
        by its ID and that the returned object contains the expected values.
        It also checks that a ValueError is raised if the project does not exist.
        """
        project = self.controller.add_project(title="Get Test Project")
        fetched = self.controller.get_project(project.project_id)
        self.assertEqual(fetched.id, project.id)
        self.assertEqual(fetched.title, "Get Test Project")
        with self.assertRaises(ValueError):
            self.controller.get_project(99999)

    def test_update_project(self):
        """
        Test the update_project method of ProjectController.

        This test verifies that all fields of a project can be updated and that the version is incremented.
        It also checks that updating a non-existing project raises a ValueError.
        """
        project = self.controller.add_project(
            title="Old title",
            description="Old description",
            organization="Old organization",
            project_manager="Old manager",
            project_sponsor="Old sponsor",
            initiation_date=date(2025, 1, 1),
            closure_date=date(2025, 12, 31),
            parent_id=None
        )
        updated = self.controller.update_project(
            project_id=project.project_id,
            title="New title",
            description="New description",
            organization="New organization",
            project_manager="New manager",
            project_sponsor="New sponsor",
            initiation_date=date(2026, 2, 2),
            closure_date=date(2026, 11, 30),
            parent_id=12345
        )
        self.assertEqual(updated.title, "New title")
        self.assertEqual(updated.description, "New description")
        self.assertEqual(updated.organization, "New organization")
        self.assertEqual(updated.project_manager, "New manager")
        self.assertEqual(updated.project_sponsor, "New sponsor")
        self.assertEqual(updated.initiation_date, date(2026, 2, 2))
        self.assertEqual(updated.closure_date, date(2026, 11, 30))
        self.assertEqual(updated.parent_id, 12345)
        self.assertEqual(updated.version, 2)
        # Ensure updating a non-existing project fails
        with self.assertRaises(ValueError):
            self.controller.update_project(project_id=99999)

    def test_delete_project(self):
        """
        Test the delete_project method of ProjectController.

        This test verifies that a project is marked as deleted, that a ValueError is raised for non-existent projects, that get_project does not return a deleted project, and that child projects are also marked as deleted. It also ensures that only the correct projects are returned by delete_project.
        """
        parent = self.controller.add_project(title="Parent project")
        child1 = self.controller.add_project(title="Child 1", parent_id=parent.project_id)
        child2 = self.controller.add_project(title="Child 2", parent_id=parent.project_id)
        grandchild = self.controller.add_project(title="Grandchild", parent_id=child1.project_id)
        unrelated = self.controller.add_project(title="Unrelated project")
        deleted_projects = self.controller.delete_project(parent.project_id)
        # All returned projects must be marked as deleted
        for project in deleted_projects:
            self.assertEqual(project.deleted, 1)
        # Ensure all children and grandchildren are deleted
        deleted_ids = [proj.project_id for proj in deleted_projects]
        self.assertIn(parent.project_id, deleted_ids)
        self.assertIn(child1.project_id, deleted_ids)
        self.assertIn(child2.project_id, deleted_ids)
        self.assertIn(grandchild.project_id, deleted_ids)
        # Ensure unrelated project is not deleted and not in the returned list
        self.assertNotIn(unrelated.project_id, deleted_ids)
        # Ensure no extra projects are returned
        self.assertEqual(set(deleted_ids), {parent.project_id, child1.project_id, child2.project_id, grandchild.project_id})
        # Ensure deleting a non-existing project fails.
        with self.assertRaises(ValueError):
            self.controller.delete_project(99999)
        # Ensure get_project does not return deleted project.
        with self.assertRaises(ValueError):
            self.controller.get_project(parent.project_id)
        with self.assertRaises(ValueError):
            self.controller.get_project(child1.project_id)
        with self.assertRaises(ValueError):
            self.controller.get_project(child2.project_id)
        with self.assertRaises(ValueError):
            self.controller.get_project(grandchild.project_id)
        # Unrelated project should still be retrievable
        self.assertEqual(self.controller.get_project(unrelated.project_id).title, "Unrelated project")

    def test_get_projects(self):
        """
        Test the get_projects method of ProjectController.

        This test verifies that only the latest, non-deleted version of each project is returned.
        """
        # Add two projects
        project1 = self.controller.add_project(title="Project 1")
        project2 = self.controller.add_project(title="Project 2")
        # Update project1 (should increment version)
        updated1 = self.controller.update_project(
            project_id=project1.project_id,
            title="Project 1 updated"
        )
        # Soft-delete project2
        self.controller.delete_project(project2.project_id)
        # Add a third project
        project3 = self.controller.add_project(title="Project 3")
        # get_projects should only return the latest version of project1 and project3 (not deleted)
        projects = self.controller.get_projects()
        project_titles = {p.title for p in projects}
        self.assertIn("Project 1 updated", project_titles)
        self.assertIn("Project 3", project_titles)
        self.assertNotIn("Project 2", project_titles)
        # Ensure only one entry per project_id
        project_ids = [p.project_id for p in projects]
        self.assertEqual(len(project_ids), len(set(project_ids)))

if __name__ == "__main__":
    unittest.main()
