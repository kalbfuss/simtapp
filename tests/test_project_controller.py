import logging
import os
import unittest

from datetime import date, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import configure_mappers, sessionmaker

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
        # Enable debug level logging
        logging.basicConfig(level=logging.DEBUG)
        # Create database and session
        self.db_path = os.path.abspath("test_projects.sqlite")
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        configure_mappers()
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        # Create instance of controller we want to test
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

        This test verifies:
        - A project can be created and stored in the database with the correct attributes.
        - The returned object contains the expected values.
        - Projects can be linked via the parent_id attribute.
        - The created and last_modified timestamps are set and equal on creation.

        Test steps:
        1. Create a Project instance and add it using add_project, then verify all attributes and timestamps.
        2. Create a child Project instance linked via parent_id and verify linkage.
        3. Fetch the child project and check the parent_id is correct.
        """
        # Create a project instance.
        project = Project(
            title="Add test project",
            description="Description",
            organization="Test organization",
            project_manager="Manager",
            project_sponsor="Sponsor",
            initiation_date=date(2025, 6, 12),
            closure_date=date(2025, 6, 20)
        )
        project = self.controller.add(project)
        self.assertIsNotNone(project.project_id)
        self.assertEqual(project.title, "Add test project")
        self.assertEqual(project.description, "Description")
        self.assertEqual(project.organization, "Test organization")
        self.assertEqual(project.project_manager, "Manager")
        self.assertEqual(project.project_sponsor, "Sponsor")
        self.assertEqual(project.initiation_date, date(2025, 6, 12))
        self.assertEqual(project.closure_date, date(2025, 6, 20))
        self.assertEqual(project.versions.count(), 1)
        self.assertIsNotNone(project.created)
        self.assertIsNotNone(project.last_modified)
        self.assertEqual(project.created, project.last_modified)
        # Test linking to parent.
        child = Project(
            title="Child Project",
            parent=project
        )
        child = self.controller.add(child)
        self.assertEqual(child.parent, project)

    def test_get_project_by_id(self):
        """
        Test the get_project method of ProjectController.

        This test verifies:
        - A project can be retrieved from the database by its ID.
        - The returned object contains the expected values.
        - A ValueError is raised if the project does not exist.

        Test steps:
        1. Add a project and retrieve it by its ID, verifying all attributes.
        2. Attempt to retrieve a non-existent project and expect a ValueError.
        """
        # Create a project.
        project = Project(
            title="Get Test Project",
            description="Description",
            organization="Test organization",
            project_manager="Manager",
            project_sponsor="Sponsor",
            initiation_date=date(2025, 6, 12),
            closure_date=date(2025, 6, 20)
        )     
        project = self.controller.add(project)
        # Ensure values in the database are as expected.        
        fetched = self.controller.get_by_id(project.project_id)
        self.assertEqual(fetched.project_id, project.project_id)
        self.assertEqual(fetched.title, "Get Test Project")
        self.assertEqual(fetched.description, "Description")
        self.assertEqual(fetched.organization, "Test organization")
        self.assertEqual(fetched.project_manager, "Manager")
        self.assertEqual(fetched.initiation_date, date(2025, 6, 12))
        self.assertEqual(fetched.closure_date, date(2025, 6, 20))
        # Attempt to get non-existent project.
        with self.assertRaises(ValueError):
            self.controller.get_by_id(99999)

    def test_update_project(self):
        """
        Test the update_project method of ProjectController.

        This test verifies:
        - All fields of a project can be updated.
        - Updating a non-existing project raises a ValueError.
        - The last_modified timestamp is updated and created remains unchanged.
        - The previous version is saved.

        Test steps:
        1. Add a project, update all fields, and verify the changes and version increment.
        2. Check that the previous version is saved.
        3. Attempt to update a non-existent project.
        """
        project = Project(
            title="Old title",
            description="Old description",
            organization="Old organization",
            project_manager="Old manager",
            project_sponsor="Old sponsor",
            initiation_date=date(2025, 1, 1),
            closure_date=date(2025, 12, 31),
            parent_id=None
        )
        project = self.controller.add(project)
        parent = Project(title="Parent for update")
        parent = self.controller.add(parent)
        old_last_modified = project.last_modified
        old_created = project.created
        # Update values of the project
        project.title="New title"
        project.description="New description"
        project.organization="New organization"
        project.project_manager="New manager"
        project.project_sponsor="New sponsor"
        project.initiation_date=date(2026, 2, 2)
        project.closure_date=date(2026, 11, 30)
        project.parent = parent
        project = self.controller.update(project)
        self.assertEqual(project.title, "New title")
        self.assertEqual(project.description, "New description")
        self.assertEqual(project.organization, "New organization")
        self.assertEqual(project.project_manager, "New manager")
        self.assertEqual(project.project_sponsor, "New sponsor")
        self.assertEqual(project.initiation_date, date(2026, 2, 2))
        self.assertEqual(project.closure_date, date(2026, 11, 30))
        self.assertEqual(project.parent_id, parent.project_id)
        self.assertEqual(project.versions.count(), 2)
        self.assertIsNotNone(project.last_modified)
        self.assertGreaterEqual(project.last_modified, old_last_modified)
        self.assertEqual(project.created, old_created)
        # Ensure the old version is stored in the project history
        old = project.versions[0]
        self.assertIsNotNone(old)
        self.assertEqual(old.title, "Old title")
        self.assertEqual(old.description, "Old description")
        self.assertEqual(old.organization, "Old organization")
        self.assertEqual(old.project_manager, "Old manager")
        self.assertEqual(old.project_sponsor, "Old sponsor")
        self.assertEqual(old.initiation_date, date(2025, 1, 1))
        self.assertEqual(old.closure_date, date(2025, 12, 31))
        self.assertEqual(old.parent_id, None)
        self.assertEqual(old.created, old_created)
        self.assertEqual(old.last_modified, old_last_modified)
        # Ensure updating a non-existing project fails
        non_existing = Project(project_id=99999)
        with self.assertRaises(ValueError):
            self.controller.update(non_existing)

    def test_delete_project(self):
        """
        Test the delete_project method of ProjectController.

        This test verifies:
        - A project and all its descendants are deleted.
        - get_project does not return a deleted project.
        - Unrelated projects are not affected.
        - Only the correct projects are returned by delete_project.

        Test steps:
        1. Add a parent project, two child projects, a grandchild, and an unrelated project.
        2. Delete the parent project, verify all descendants are deleted, and the unrelated project remains unaffected.
        3. Ensure get_project does not return deleted projects.
        4. Ensure deleted projects are removed from the database.
        """
        # Create projects.
        parent = Project(title="Parent project")
        parent = self.controller.add(parent)
        child1 = Project(title="Child 1", parent_id=parent.project_id)
        child1 = self.controller.add(child1)
        child2 = Project(title="Child 2", parent_id=parent.project_id)
        child2 = self.controller.add(child2)
        grandchild = Project(title="Grandchild", parent_id=child1.project_id)
        grandchild = self.controller.add(grandchild)
        unrelated = Project(title="Unrelated project")
        unrelated = self.controller.add(unrelated)
        # Delete parent project and verify deletion of parent and descendants.
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
        for id in [parent.project_id, child1.project_id, child2.project_id, grandchild.project_id]:
            with self.assertRaises(ValueError):
                self.controller.get_by_id(id)
        # Unrelated project should still be retrievable
        self.assertEqual(self.controller.get_by_id(unrelated.project_id).title, "Unrelated project")
        # Ensure deleted projects are removed from the projects table.
        for id in [parent.project_id, child1.project_id, child2.project_id, grandchild.project_id]:
            project = self.session.query(Project).filter(Project.project_id == id).first()
            self.assertIsNone(project)

    def test_delete_project_by_id(self):
        """
        Test the delete_by_id method of ProjectController.

        This test verifies:
        - A project and all its descendants are deleted by ID.
        - get_by_id does not return a deleted project.
        - Unrelated projects are not affected.
        - Only the correct projects are returned by delete_by_id.

        Test steps:
        1. Add a parent project, two child projects, a grandchild, and an unrelated project.
        2. Delete the parent project by ID, verify all descendants are deleted, and the unrelated project remains unaffected.
        3. Ensure get_by_id does not return deleted projects.
        4. Ensure deleted projects are removed from the database.
        """
        # Create projects.
        parent = Project(title="Parent project")
        parent = self.controller.add(parent)
        child1 = Project(title="Child 1", parent_id=parent.project_id)
        child1 = self.controller.add(child1)
        child2 = Project(title="Child 2", parent_id=parent.project_id)
        child2 = self.controller.add(child2)
        grandchild = Project(title="Grandchild", parent_id=child1.project_id)
        grandchild = self.controller.add(grandchild)
        unrelated = Project(title="Unrelated project")
        unrelated = self.controller.add(unrelated)
        # Delete parent project by ID and verify deletion of parent and descendants.
        deleted = self.controller.delete_by_id(parent.project_id)
        self.assertIn(parent, deleted)
        self.assertIn(child1, deleted)
        self.assertIn(child2, deleted)
        self.assertIn(grandchild, deleted)
        self.assertNotIn(unrelated, deleted)
        self.assertEqual(set(deleted), {parent, child1, child2, grandchild})
        # Ensure deleting a non-existing project fails.
        with self.assertRaises(ValueError):
            self.controller.delete_by_id(parent.project_id)
        # Ensure get_by_id does not return deleted project.
        for id in [parent.project_id, child1.project_id, child2.project_id, grandchild.project_id]:
            with self.assertRaises(ValueError):
                self.controller.get_by_id(id)
        # Unrelated project should still be retrievable
        self.assertEqual(self.controller.get_by_id(unrelated.project_id).title, "Unrelated project")
        # Ensure deleted projects are removed from the projects table.
        for id in [parent.project_id, child1.project_id, child2.project_id, grandchild.project_id]:
            project = self.session.query(Project).filter(Project.project_id == id).first()
            self.assertIsNone(project)

    def test_get_all_projects(self):
        """
        Test the get_projects method of ProjectController.

        This test verifies:
        - Only the latest, non-deleted version of each project is returned.

        Test steps:
        1. Add two projects and update one of them.
        2. Soft-delete one project and add a third project.
        3. Retrieve all projects and verify only the latest, non-deleted versions are returned.
        4. Ensure only one entry per project_id is returned.
        """
        project1 = Project(title="Project 1")
        project1 = self.controller.add(project1)
        project2 = Project(title="Project 2")
        project2 = self.controller.add(project2)
        # Update project1 (should increment version)
        project1.title="Project 1 updated"
        self.controller.update(project1)
        # Delete project2
        self.controller.delete(project2)
        # Add a third project
        project3 = Project(title="Project 3")
        project3 = self.controller.add(project3)
        # get_projects should only return the latest version of project1 and project3 (not deleted)
        projects = self.controller.get_all()
        project_titles = {p.title for p in projects}
        self.assertIn("Project 1 updated", project_titles)
        self.assertIn("Project 3", project_titles)
        self.assertNotIn("Project 2", project_titles)
        # Ensure only one entry per project_id
        project_ids = [p.project_id for p in projects]
        self.assertEqual(len(project_ids), len(set(project_ids)))

    def test_get_project_history(self):
        """
        Test the get_project_history method of ProjectController.

        This test verifies:
        - All versions of a project are returned in descending order by version.

        Test steps:
        1. Add a project and update it multiple times.
        2. Retrieve the project history and verify the order and content of all versions.
        """
        project = Project(title="History Test Project v1", description="v1")
        project = self.controller.add(project)
        # Update the project.
        project.title = "History Test Project v2"
        project.description = "v2"
        self.controller.update(project)
        # Update the project again.
        project.title = "History Test Project v3"
        project.description = "v3"
        self.controller.update(project)
        # Get project history.
        history = self.controller.get_history(project)
        # There should be 3 history entries
        self.assertEqual(len(history), 3)
        # Check order: latest version first
        # Titles and descriptions should match the update sequence
        self.assertEqual(history[0].title, "History Test Project v3")
        self.assertEqual(history[0].description, "v3")
        self.assertEqual(history[1].title, "History Test Project v2")
        self.assertEqual(history[1].description, "v2")
        self.assertEqual(history[2].title, "History Test Project v1")
        self.assertEqual(history[2].description, "v1")
        
    def test_possible_parent_projects(self):
        # Create some projects using controller
        p1 = self.controller.add(Project(title="Alpha"))
        p2 = self.controller.add(Project(title="Beta"))
        p3 = self.controller.add(Project(title="Gamma"))

        result = self.controller.possible_parents()
        # Check keys and values
        expected_keys = {f"Alpha (ID {p1.project_id})", f"Beta (ID {p2.project_id})", f"Gamma (ID {p3.project_id})"}
        assert set(result.keys()) == expected_keys
        assert result[f"Alpha (ID {p1.project_id})"] == p1.project_id
        assert result[f"Beta (ID {p2.project_id})"] == p2.project_id
        assert result[f"Gamma (ID {p3.project_id})"] == p3.project_id

        result = self.controller.possible_parents(p1)
        # Check keys and values
        expected_keys = {f"Beta (ID {p2.project_id})", f"Gamma (ID {p3.project_id})"}
        assert set(result.keys()) == expected_keys


if __name__ == "__main__":
    unittest.main()