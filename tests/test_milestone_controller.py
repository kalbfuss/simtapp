import unittest
import tempfile
import os

from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from plog.models.milestone import Milestone, Base
from plog.controllers.milestone_controller import MilestoneController

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
        self.db_path = os.path.abspath("test_milestones.db")
        self.engine = create_engine(f'sqlite:///{self.db_path}')
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        self.controller = MilestoneController(self.session)

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
        """
        milestone = self.controller.add_milestone(
            title="Test Milestone",
            description="Beschreibung",
            initial_baseline_date="2025-06-12",
            latest_baseline_date="2025-06-20",
            acceptance_criteria=["Kriterium 1", "Kriterium 2"]
        )
        self.assertIsNotNone(milestone.id)
        self.assertEqual(milestone.title, "Test Milestone")
        self.assertEqual(milestone.description, "Beschreibung")
        self.assertEqual(milestone.initial_baseline_date, "2025-06-12")
        self.assertEqual(milestone.latest_baseline_date, "2025-06-20")
        self.assertEqual(milestone.acceptance_criteria, ["Kriterium 1", "Kriterium 2"])

    def test_get_milestone(self):
        """
        Test the get_milestone method of MilestoneController.

        This test verifies that a milestone can be retrieved from the database
        by its ID and that the returned object contains the expected values.
        It also checks that a ValueError is raised if the milestone does not exist.
        """
        # Add a milestone first
        milestone = self.controller.add_milestone(
            title="GetTest Milestone",
            description="GetTest Beschreibung",
            initial_baseline_date="2025-07-01",
            latest_baseline_date="2025-07-10",
            acceptance_criteria=["GetTest Kriterium"]
        )
        # Retrieve the milestone by ID
        fetched = self.controller.get_milestone(milestone.id)
        self.assertEqual(fetched.id, milestone.id)
        self.assertEqual(fetched.title, "GetTest Milestone")
        self.assertEqual(fetched.description, "GetTest Beschreibung")
        self.assertEqual(fetched.initial_baseline_date, "2025-07-01")
        self.assertEqual(fetched.latest_baseline_date, "2025-07-10")
        self.assertEqual(fetched.acceptance_criteria, ["GetTest Kriterium"])
        # Test for non-existent milestone
        with self.assertRaises(ValueError):
            self.controller.get_milestone(99999)

if __name__ == "__main__":
    unittest.main()
