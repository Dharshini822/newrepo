import os
import sys
import unittest
import json
import base64
import numpy as np
import cv2

# Add root to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from app import create_app
import config

class SignAITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.client = cls.app.test_client()

    def test_01_status_endpoint(self):
        res = self.client.get("/api/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "online")
        self.assertTrue(data["hand_detector_ready"])
        self.assertTrue(data["model_configured"])

    def test_02_model_status_endpoint(self):
        res = self.client.get("/api/model/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["configured"])
        self.assertIn("HELLO", data["classes"])
        self.assertIn("A", data["classes"])
        self.assertGreater(data["num_classes"], 0)

    def test_03_translate_endpoint(self):
        # Test ISL glossary translation to Tamil
        res = self.client.post("/api/translate", json={"text": "HELLO", "target_lang": "ta"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertEqual(data["result"]["translated"], "வணக்கம்")

        # Test another common sign
        res2 = self.client.post("/api/translate", json={"text": "THANK YOU", "target_lang": "ta"})
        self.assertEqual(res2.status_code, 200)
        data2 = res2.get_json()
        self.assertTrue(data2["success"])
        self.assertEqual(data2["result"]["translated"], "நன்றி")

    def test_04_glossary_endpoint(self):
        res = self.client.get("/api/translate/glossary")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertGreater(len(data["glossary"]), 10)

    def test_05_dataset_stats_endpoint(self):
        res = self.client.get("/api/dataset/stats")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("total_images", data["stats"])
        self.assertIn("distribution", data["stats"])

    def test_06_dataset_manifest_endpoint(self):
        res = self.client.get("/api/dataset/manifest")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("project", data)
        self.assertIn("summary", data)

    def test_07_history_workflow(self):
        # 1. Add manual entry
        add_res = self.client.post("/api/history/add", json={
            "sign_detected": "HELLO",
            "confidence": 0.95,
            "target_lang": "ta",
            "translation": "வணக்கம்",
            "source": "manual"
        })
        self.assertEqual(add_res.status_code, 200)
        add_data = add_res.get_json()
        entry_id = add_data["entry"]["id"]

        # 2. Query history
        list_res = self.client.get("/api/history?limit=10")
        self.assertEqual(list_res.status_code, 200)
        list_data = list_res.get_json()
        self.assertTrue(list_data["success"])
        found = any(e["id"] == entry_id for e in list_data["history"])
        self.assertTrue(found)

        # 3. Delete entry
        del_res = self.client.delete(f"/api/history/{entry_id}")
        self.assertEqual(del_res.status_code, 200)

    def test_08_predict_frame_no_hand(self):
        # Send empty black frame
        blank = np.zeros((240, 320, 3), dtype=np.uint8)
        _, buf = cv2.imencode(".jpg", blank)
        b64 = "data:image/jpeg;base64," + base64.b64encode(buf).decode("utf-8")

        res = self.client.post("/api/predict/frame", json={"frame": b64, "target_lang": "ta"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertFalse(data["has_hand"])

    def test_09_health_endpoint(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "online")

    def test_10_dataset_endpoint(self):
        res = self.client.get("/api/dataset")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])
        self.assertIn("stats", data)
        self.assertIn("samples", data)

    def test_11_train_status(self):
        res = self.client.get("/api/train/status")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn("is_training", data)
        self.assertIn("progress", data)
        self.assertIn("logs", data)

    def test_12_history_clear(self):
        res = self.client.delete("/api/history")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data["success"])

if __name__ == "__main__":
    unittest.main()
