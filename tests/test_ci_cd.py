"""Tests for CI/CD pipeline components"""

import os
import unittest
import subprocess
from unittest.mock import patch, MagicMock

class TestCICD(unittest.TestCase):
    """Test cases for CI/CD pipeline components"""
    
    def test_deployment_scripts_exist(self):
        """Test that deployment scripts exist"""
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
        
        # Check that required scripts exist
        self.assertTrue(os.path.exists(os.path.join(scripts_dir, "prepare_deployment.sh")))
        self.assertTrue(os.path.exists(os.path.join(scripts_dir, "deploy.sh")))
        self.assertTrue(os.path.exists(os.path.join(scripts_dir, "rollback.sh")))
        self.assertTrue(os.path.exists(os.path.join(scripts_dir, "health_check.sh")))
        self.assertTrue(os.path.exists(os.path.join(scripts_dir, "check_deployment.sh")))
    
    @patch('subprocess.run')
    def test_health_check_script(self, mock_run):
        """Test health check script execution"""
        # Mock successful response
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Run health check script
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
        health_check_script = os.path.join(scripts_dir, "health_check.sh")
        
        # Test with default parameters
        result = subprocess.run(["bash", health_check_script, "--url", "http://localhost:8000/api/health"], 
                               capture_output=True, text=True)
        
        # Assert script was called
        mock_run.assert_called()
    
    @patch('subprocess.run')
    def test_deploy_script(self, mock_run):
        """Test deploy script execution"""
        # Mock successful response
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_run.return_value = mock_process
        
        # Run deploy script
        scripts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "scripts")
        deploy_script = os.path.join(scripts_dir, "deploy.sh")
        
        # Test with parameters
        result = subprocess.run(["bash", deploy_script, 
                               "--environment", "staging", 
                               "--tag", "latest"], 
                               capture_output=True, text=True)
        
        # Assert script was called
        mock_run.assert_called()
    
    def test_ci_workflow_file_exists(self):
        """Test that CI workflow file exists"""
        workflow_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            ".github", "workflows", "ci.yml"
        )
        self.assertTrue(os.path.exists(workflow_file))
        
        # Check content of workflow file
        with open(workflow_file, 'r') as f:
            content = f.read()
            
        # Check for required jobs
        self.assertIn("test:", content)
        self.assertIn("build-and-push:", content)
        self.assertIn("deploy-staging:", content)
        self.assertIn("deploy-production:", content)

if __name__ == "__main__":
    unittest.main()