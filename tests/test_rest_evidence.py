"""Temporary submission evidence test that exercises the REST API with real cURL commands."""
import json
import os
import shutil
import subprocess
import time
from unittest import TestCase

from service import app, talisman
from service.models import Account, db


class TestRestEvidence(TestCase):
    """Generate real cURL evidence for CREATE, LIST, READ, UPDATE, and DELETE."""

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        talisman.force_https = False
        with app.app_context():
            db.session.query(Account).delete()
            db.session.commit()

        if shutil.which("curl") is None:
            subprocess.run(["apt-get", "update"], check=True, stdout=subprocess.DEVNULL)
            subprocess.run(
                ["apt-get", "install", "-y", "curl"],
                check=True,
                stdout=subprocess.DEVNULL,
            )

        env = os.environ.copy()
        cls.server = subprocess.Popen(
            [
                "python",
                "-c",
                "from service import app,talisman; talisman.force_https=False; app.run(host='127.0.0.1',port=5000,use_reloader=False)",
            ],
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for _ in range(30):
            result = subprocess.run(
                ["curl", "-sS", "http://127.0.0.1:5000/health"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                return
            time.sleep(1)
        raise RuntimeError("REST service did not start")

    @classmethod
    def tearDownClass(cls):
        cls.server.terminate()
        try:
            cls.server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            cls.server.kill()

    @staticmethod
    def _run(label, command):
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"\n===== {label} =====")
        print("$ " + " ".join(command))
        print(result.stdout.strip())
        return result.stdout.strip()

    def test_rest_submission_evidence(self):
        payload = {
            "name": "John Doe",
            "email": "john@example.com",
            "address": "123 Main Street",
            "phone_number": "555-0100",
            "date_joined": "2026-09-08",
        }
        create_out = self._run(
            "REST_CREATE_DONE",
            [
                "curl", "-sS", "-X", "POST", "http://127.0.0.1:5000/accounts",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payload),
            ],
        )
        account_id = json.loads(create_out)["id"]

        self._run(
            "REST_LIST_DONE",
            ["curl", "-sS", "http://127.0.0.1:5000/accounts"],
        )

        self._run(
            "REST_READ_DONE",
            ["curl", "-sS", f"http://127.0.0.1:5000/accounts/{account_id}"],
        )

        payload["name"] = "John Smith"
        payload["address"] = "456 Main Street"
        self._run(
            "REST_UPDATE_DONE",
            [
                "curl", "-sS", "-X", "PUT",
                f"http://127.0.0.1:5000/accounts/{account_id}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(payload),
            ],
        )

        self._run(
            "REST_DELETE_DONE",
            [
                "curl", "-sS", "-i", "-X", "DELETE",
                f"http://127.0.0.1:5000/accounts/{account_id}",
            ],
        )
