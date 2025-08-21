import os
import sys
import unittest
import json
from fastapi.testclient import TestClient

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.serve.api import app


class TestCredTechAPI(unittest.TestCase):
    """Test cases for the CredTech XScore API endpoints"""

    def setUp(self):
        """Set up test client and authentication"""
        self.client = TestClient(app)
        # Get authentication token
        response = self.client.post(
            "/api/token",
            data={"username": "johndoe", "password": "secret"}
        )
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}

    def test_health_check(self):
        """Test the health check endpoint"""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "OK")
        self.assertIsNotNone(data["version"])
        self.assertIn("model_loaded", data)
        self.assertIn("timestamp", data)

    def test_authentication(self):
        """Test authentication endpoints"""
        # Test successful authentication
        response = self.client.post(
            "/api/token",
            data={"username": "johndoe", "password": "secret"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["token_type"], "bearer")

        # Test failed authentication
        response = self.client.post(
            "/api/token",
            data={"username": "johndoe", "password": "wrong_password"}
        )
        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token"""
        response = self.client.get("/api/issuers")
        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with token"""
        response = self.client.get("/api/issuers", headers=self.headers)
        self.assertEqual(response.status_code, 200)

    def test_credit_score_endpoint(self):
        """Test the credit score endpoint"""
        test_data = {
            "issuer": "Apple Inc.",
            "income": 365000000.0,
            "balance": 45000000.0,
            "transactions": 1250,
            "news_sentiment": 0.75
        }
        response = self.client.post(
            "/api/score",
            json=test_data,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["issuer"], "Apple Inc.")
        self.assertIsInstance(data["score"], float)
        self.assertIsInstance(data["rating"], str)
        self.assertIsInstance(data["risk_level"], str)
        self.assertIsInstance(data["explanation"], dict)
        self.assertIn("timestamp", data)

    def test_batch_score_endpoint(self):
        """Test the batch score endpoint"""
        test_data = {
            "items": [
                {
                    "issuer": "Apple Inc.",
                    "income": 365000000.0,
                    "balance": 45000000.0,
                    "transactions": 1250,
                    "news_sentiment": 0.75
                },
                {
                    "issuer": "Microsoft Corp.",
                    "income": 168000000.0,
                    "balance": 32000000.0,
                    "transactions": 980,
                    "news_sentiment": 0.62
                }
            ]
        }
        response = self.client.post(
            "/api/batch-score",
            json=test_data,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertEqual(len(data["results"]), 2)
        self.assertEqual(data["count"], 2)
        self.assertIn("timestamp", data)

    def test_validation_error(self):
        """Test validation error handling"""
        # Test with invalid data (negative income)
        test_data = {
            "issuer": "Apple Inc.",
            "income": -100000.0,  # Negative income should fail validation
            "balance": 45000000.0,
            "transactions": 1250,
            "news_sentiment": 0.75
        }
        response = self.client.post(
            "/api/score",
            json=test_data,
            headers=self.headers
        )
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertIn("detail", data)

    def test_model_info_endpoint(self):
        """Test the model info endpoint"""
        response = self.client.get("/api/model-info", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("name", data)
        self.assertIn("version", data)
        self.assertIn("features", data)
        self.assertIn("metrics", data)
        self.assertIn("last_trained", data)


if __name__ == "__main__":
    unittest.main()