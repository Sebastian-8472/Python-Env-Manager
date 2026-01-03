import unittest
from unittest.mock import patch, MagicMock, subprocess
import json
from py_updater import PyUpdater

class TestPyUpdater(unittest.TestCase):
    """
    Unit tests for the PyUpdater class.
    
    These tests use mocking to simulate terminal commands and file system 
    operations, ensuring the logic is tested in isolation.
    """

    def setUp(self):
        """Initialize the updater instance before each test."""
        self.updater = PyUpdater()

    @patch('subprocess.run')
    def test_get_outdated_packages_success(self, mock_run):
        """Test successful retrieval of outdated packages."""
        # Simulate pip output
        mock_output = [
            {"name": "requests", "version": "2.20.0", "latest_version": "2.28.0"}
        ]
        mock_run.return_value = MagicMock(
            stdout=json.dumps(mock_output),
            returncode=0
        )

        packages = self.updater.get_outdated_packages()
        
        self.assertEqual(len(packages), 1)
        self.assertEqual(packages[0]['name'], 'requests')
        mock_run.assert_called_once()

    @patch('subprocess.run')
    def test_update_package_success(self, mock_run):
        """Test a successful single package update."""
        mock_run.return_value = MagicMock(returncode=0)
        
        result = self.updater.update_package("requests", "2.20.0", "2.28.0")
        
        self.assertTrue(result)
        # Verify pip was called with the correct upgrade arguments
        args, _ = mock_run.call_args
        self.assertIn("--upgrade", args[0])
        self.assertIn("requests", args[0])

    @patch('subprocess.run')
    def test_create_backup_io_error(self, mock_run):
        """Test error handling when backup creation fails."""
        # Simulate a subprocess error
        mock_run.side_effect = subprocess.CalledProcessError(1, 'cmd')
        
        filename = self.updater.create_backup("fail_test.txt")
        
        self.assertIsNone(filename)

    @patch('os.path.exists')
    def test_install_from_requirements_missing_file(self, mock_exists):
        """Test that installation fails gracefully if the file is missing."""
        mock_exists.return_value = False
        
        result = self.updater.install_from_requirements("non_existent.txt")
        
        self.assertFalse(result)

    def test_init_sets_executable(self):
        """Test that the class correctly identifies the Python executable."""
        import sys
        self.assertEqual(self.updater.python_exe, sys.executable)

if __name__ == "__main__":
    unittest.main()
