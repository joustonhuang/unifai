from __future__ import annotations

import http.client
import sqlite3
import sys
import tempfile
import threading
import unittest
from http.server import HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from supervisor import webui


class WebuiRuntimeTruthTests(unittest.TestCase):
    def test_runtime_truth_snapshot_reads_recent_rows_without_leaking_payloads(self):
        with tempfile.TemporaryDirectory(prefix="unifai-webui-runtime-") as tmp_dir:
            db_path = Path(tmp_dir) / "supervisor.db"
            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    spec TEXT NOT NULL,
                    result TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE oracle_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    task_id INTEGER,
                    stage TEXT NOT NULL,
                    source TEXT NOT NULL,
                    incident_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    result_json TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE events (
                    event_id TEXT PRIMARY KEY,
                    timestamp INTEGER NOT NULL,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    target TEXT,
                    task_id TEXT,
                    reason TEXT,
                    payload_json TEXT
                )
                """
            )

            conn.execute(
                """
                INSERT INTO tasks (created_at, status, spec, result)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "2026-08-15T08:00:00+00:00",
                    "done",
                    '{"type":"llm","agent":"oracle","prompt":"MOCK_SECRET_KEY_FOR_TEST"}',
                    '{"session_path":"/tmp/unifai_sessions/7.json","payload":{"summary":"safe"}}',
                ),
            )
            conn.execute(
                """
                INSERT INTO oracle_incidents (
                    created_at, task_id, stage, source, incident_type, severity, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "2026-08-15T08:01:00+00:00",
                    7,
                    "pre_execution",
                    "Supervisor",
                    "auth_refresh_failure",
                    "high",
                    '{"summary":"Authentication refresh failure detected.","wilson_message":"safe"}',
                ),
            )
            conn.execute(
                """
                INSERT INTO events (
                    event_id, timestamp, event_type, actor, target, task_id, reason, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "evt-1",
                    1755244860,
                    "gaia_plan_received",
                    "Gaia",
                    "worker-1",
                    "task-7",
                    "accepted",
                    '{"opaque":true}',
                ),
            )
            conn.commit()
            conn.close()

            original_db = webui.SUPERVISOR_DB
            try:
                webui.SUPERVISOR_DB = db_path
                snapshot = webui._runtime_truth_snapshot(limit=3)
                rendered = webui._render_runtime_truth(snapshot)
            finally:
                webui.SUPERVISOR_DB = original_db

            self.assertTrue(snapshot["ok"])
            self.assertEqual(snapshot["tasks"][0]["detail"], "llm:oracle")
            self.assertTrue(snapshot["tasks"][0]["session_persisted"])
            self.assertEqual(snapshot["tasks"][0]["summary"], "safe")
            self.assertEqual(snapshot["incidents"][0]["summary"], "Authentication refresh failure detected.")
            self.assertEqual(snapshot["events"][0]["event_type"], "gaia_plan_received")
            self.assertEqual(snapshot["brief"]["headline"], "Oracle has a high incident in pre_execution.")
            self.assertIn(
                "Latest task 1 is done: safe Session persisted.",
                snapshot["brief"]["details"],
            )
            self.assertNotIn("MOCK_SECRET_KEY_FOR_TEST", rendered)
            self.assertNotIn("/tmp/unifai_sessions/7.json", rendered)
            self.assertIn("session persisted", rendered)
            self.assertIn("safe", rendered)
            self.assertIn("Wilson Brief", rendered)
            self.assertIn("Oracle has a high incident in pre_execution.", rendered)

    def test_runtime_truth_snapshot_reports_missing_db(self):
        original_db = webui.SUPERVISOR_DB
        try:
            webui.SUPERVISOR_DB = Path("/tmp/does-not-exist-supervisor.db")
            snapshot = webui._runtime_truth_snapshot(limit=2)
            rendered = webui._render_runtime_truth(snapshot)
        finally:
            webui.SUPERVISOR_DB = original_db

        self.assertFalse(snapshot["ok"])
        self.assertIn("Runtime truth unavailable", rendered)

    def test_runtime_truth_brief_handles_empty_snapshot(self):
        snapshot = {"ok": True, "tasks": [], "incidents": [], "events": []}

        brief = webui._runtime_truth_brief(snapshot)
        rendered = webui._render_runtime_truth(snapshot)

        self.assertEqual(brief["headline"], "Runtime truth is quiet.")
        self.assertEqual(
            brief["details"],
            ["No recent Supervisor, Oracle, or Gaia rows were available."],
        )
        self.assertIn("Runtime truth is quiet.", rendered)
        self.assertIn("No recent Supervisor, Oracle, or Gaia rows were available.", rendered)

    def test_runtime_truth_render_escapes_untrusted_html(self):
        snapshot = {
            "ok": True,
            "tasks": [
                {
                    "id": "task-9",
                    "created_at": "2026-08-16T12:00:00+00:00",
                    "status": "done",
                    "detail": 'tool:<script>alert("x")</script>',
                    "summary": '<b>unsafe</b>',
                    "session_persisted": False,
                }
            ],
            "incidents": [
                {
                    "created_at": "2026-08-16T12:01:00+00:00",
                    "severity": "high",
                    "incident_type": 'prompt_<img src=x onerror=alert(1)>',
                    "stage": "pre_execution",
                    "summary": '<svg onload=alert(1)>',
                }
            ],
            "events": [
                {
                    "timestamp": '"><script>alert(2)</script>',
                    "event_type": "<planner>",
                    "actor": "<gaia>",
                    "target": "<worker-1>",
                    "task_id": "<task-9>",
                }
            ],
            "brief": {
                "headline": '<Runtime "truth">',
                "details": ['<detail>', 'plain text'],
            },
        }

        rendered = webui._render_runtime_truth(snapshot)

        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img", rendered)
        self.assertNotIn("<svg", rendered)
        self.assertIn("&lt;Runtime &quot;truth&quot;&gt;", rendered)
        self.assertIn("tool:&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;", rendered)
        self.assertIn("&lt;b&gt;unsafe&lt;/b&gt;", rendered)
        self.assertIn("prompt_&lt;img src=x onerror=alert(1)&gt;", rendered)
        self.assertIn("&lt;planner&gt;", rendered)

    def test_runtime_truth_api_exposes_read_only_json_snapshot(self):
        with tempfile.TemporaryDirectory(prefix="unifai-webui-api-") as tmp_dir:
            db_path = Path(tmp_dir) / "supervisor.db"
            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    spec TEXT NOT NULL,
                    result TEXT
                )
                """
            )
            conn.execute(
                """
                INSERT INTO tasks (created_at, status, spec, result)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "2026-08-15T10:00:00+00:00",
                    "done",
                    '{"type":"tool","cmd":"date","prompt":"MOCK_SECRET_KEY_FOR_TEST"}',
                    '{"session_path":"/tmp/unifai_sessions/9.json","payload":{"summary":"clock check complete"}}',
                ),
            )
            conn.commit()
            conn.close()

            original_db = webui.SUPERVISOR_DB
            try:
                webui.SUPERVISOR_DB = db_path
                server = HTTPServer(("127.0.0.1", 0), webui.make_handler("fake-sv-cli"))
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    conn_http = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                    conn_http.request("GET", "/api/runtime-truth")
                    response = conn_http.getresponse()
                    body = response.read().decode("utf-8")
                    conn_http.close()
                finally:
                    server.shutdown()
                    thread.join(timeout=5)
                    server.server_close()
            finally:
                webui.SUPERVISOR_DB = original_db

            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("Content-Type"), "application/json; charset=utf-8")
            self.assertEqual(response.getheader("Cache-Control"), "no-store")
            self.assertIn('"ok": true', body)
            self.assertIn('"brief": {', body)
            self.assertIn('"summary": "clock check complete"', body)
            self.assertNotIn("MOCK_SECRET_KEY_FOR_TEST", body)
            self.assertNotIn("/tmp/unifai_sessions/9.json", body)

    def test_runtime_truth_page_exposes_read_only_html_snapshot(self):
        with tempfile.TemporaryDirectory(prefix="unifai-webui-page-") as tmp_dir:
            db_path = Path(tmp_dir) / "supervisor.db"
            conn = sqlite3.connect(db_path)
            conn.execute(
                """
                CREATE TABLE tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    spec TEXT NOT NULL,
                    result TEXT
                )
                """
            )
            conn.execute(
                """
                INSERT INTO tasks (created_at, status, spec, result)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "2026-08-17T07:00:00+00:00",
                    "done",
                    '{"type":"tool","cmd":"echo","prompt":"MOCK_SECRET_KEY_FOR_TEST"}',
                    '{"session_path":"/tmp/unifai_sessions/11.json","payload":{"summary":"brief is ready"}}',
                ),
            )
            conn.commit()
            conn.close()

            original_db = webui.SUPERVISOR_DB
            try:
                webui.SUPERVISOR_DB = db_path
                server = HTTPServer(("127.0.0.1", 0), webui.make_handler("fake-sv-cli"))
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                try:
                    conn_http = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                    conn_http.request("GET", "/runtime-truth?limit=999")
                    response = conn_http.getresponse()
                    body = response.read().decode("utf-8")
                    conn_http.close()
                finally:
                    server.shutdown()
                    thread.join(timeout=5)
                    server.server_close()
            finally:
                webui.SUPERVISOR_DB = original_db

        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "text/html; charset=utf-8")
        self.assertIn("Runtime Truth Feed", body)
        self.assertIn("Rows per section (1 to 20)", body)
        self.assertIn("Wilson Brief", body)
        self.assertIn("brief is ready", body)
        self.assertNotIn("MOCK_SECRET_KEY_FOR_TEST", body)
        self.assertNotIn("/tmp/unifai_sessions/11.json", body)

    def test_runtime_truth_api_reports_missing_db_as_json_error(self):
        original_db = webui.SUPERVISOR_DB
        try:
            webui.SUPERVISOR_DB = Path("/tmp/does-not-exist-supervisor.db")
            server = HTTPServer(("127.0.0.1", 0), webui.make_handler("fake-sv-cli"))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn_http = http.client.HTTPConnection(
                    "127.0.0.1", server.server_port, timeout=5
                )
                conn_http.request("GET", "/api/runtime-truth")
                response = conn_http.getresponse()
                body = response.read().decode("utf-8")
                conn_http.close()
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
        finally:
            webui.SUPERVISOR_DB = original_db

        self.assertEqual(response.status, 200)
        self.assertEqual(
            response.getheader("Content-Type"), "application/json; charset=utf-8"
        )
        self.assertIn('"ok": false', body)
        self.assertIn("Supervisor DB not found", body)

    def test_runtime_truth_page_reports_missing_db_as_html_error(self):
        original_db = webui.SUPERVISOR_DB
        try:
            webui.SUPERVISOR_DB = Path("/tmp/does-not-exist-supervisor.db")
            server = HTTPServer(("127.0.0.1", 0), webui.make_handler("fake-sv-cli"))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn_http = http.client.HTTPConnection(
                    "127.0.0.1", server.server_port, timeout=5
                )
                conn_http.request("GET", "/runtime-truth")
                response = conn_http.getresponse()
                body = response.read().decode("utf-8")
                conn_http.close()
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
        finally:
            webui.SUPERVISOR_DB = original_db

        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Content-Type"), "text/html; charset=utf-8")
        self.assertIn("Runtime truth unavailable", body)
        self.assertIn("Supervisor DB not found", body)

    def test_runtime_truth_api_clamps_limit_query_parameter(self):
        original_db = webui.SUPERVISOR_DB
        original_snapshot = webui._runtime_truth_snapshot
        calls: list[int] = []

        def fake_snapshot(limit: int = webui.RUNTIME_TRUTH_DEFAULT_LIMIT) -> dict:
            calls.append(limit)
            return {"ok": True, "tasks": [], "incidents": [], "events": []}

        try:
            webui.SUPERVISOR_DB = Path("/tmp/does-not-matter.db")
            webui._runtime_truth_snapshot = fake_snapshot
            server = HTTPServer(("127.0.0.1", 0), webui.make_handler("fake-sv-cli"))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn_http = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn_http.request("GET", "/api/runtime-truth?limit=999")
                response = conn_http.getresponse()
                response.read()
                conn_http.close()
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
        finally:
            webui.SUPERVISOR_DB = original_db
            webui._runtime_truth_snapshot = original_snapshot

        self.assertEqual(response.status, 200)
        self.assertEqual(calls, [webui.RUNTIME_TRUTH_MAX_LIMIT])

    def test_runtime_truth_page_clamps_limit_query_parameter(self):
        original_db = webui.SUPERVISOR_DB
        original_snapshot = webui._runtime_truth_snapshot
        calls: list[int] = []

        def fake_snapshot(limit: int = webui.RUNTIME_TRUTH_DEFAULT_LIMIT) -> dict:
            calls.append(limit)
            return {"ok": True, "tasks": [], "incidents": [], "events": []}

        try:
            webui.SUPERVISOR_DB = Path("/tmp/does-not-matter.db")
            webui._runtime_truth_snapshot = fake_snapshot
            server = HTTPServer(("127.0.0.1", 0), webui.make_handler("fake-sv-cli"))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn_http = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn_http.request("GET", "/runtime-truth?limit=999")
                response = conn_http.getresponse()
                body = response.read().decode("utf-8")
                conn_http.close()
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
        finally:
            webui.SUPERVISOR_DB = original_db
            webui._runtime_truth_snapshot = original_snapshot

        self.assertEqual(response.status, 200)
        self.assertEqual(calls, [webui.RUNTIME_TRUTH_MAX_LIMIT])
        self.assertIn('value="20"', body)

    def test_runtime_truth_api_uses_default_limit_for_invalid_query_parameter(self):
        original_db = webui.SUPERVISOR_DB
        original_snapshot = webui._runtime_truth_snapshot
        calls: list[int] = []

        def fake_snapshot(limit: int = 5) -> dict:
            calls.append(limit)
            return {"ok": True, "tasks": [], "incidents": [], "events": []}

        try:
            webui.SUPERVISOR_DB = Path("/tmp/does-not-matter.db")
            webui._runtime_truth_snapshot = fake_snapshot
            server = HTTPServer(("127.0.0.1", 0), webui.make_handler("fake-sv-cli"))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn_http = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn_http.request("GET", "/api/runtime-truth?limit=banana")
                response = conn_http.getresponse()
                response.read()
                conn_http.close()
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
        finally:
            webui.SUPERVISOR_DB = original_db
            webui._runtime_truth_snapshot = original_snapshot

        self.assertEqual(response.status, 200)
        self.assertEqual(calls, [webui.RUNTIME_TRUTH_DEFAULT_LIMIT])

    def test_runtime_truth_page_uses_default_limit_for_invalid_query_parameter(self):
        original_db = webui.SUPERVISOR_DB
        original_snapshot = webui._runtime_truth_snapshot
        calls: list[int] = []

        def fake_snapshot(limit: int = webui.RUNTIME_TRUTH_DEFAULT_LIMIT) -> dict:
            calls.append(limit)
            return {"ok": True, "tasks": [], "incidents": [], "events": []}

        try:
            webui.SUPERVISOR_DB = Path("/tmp/does-not-matter.db")
            webui._runtime_truth_snapshot = fake_snapshot
            server = HTTPServer(("127.0.0.1", 0), webui.make_handler("fake-sv-cli"))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn_http = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn_http.request("GET", "/runtime-truth?limit=banana")
                response = conn_http.getresponse()
                body = response.read().decode("utf-8")
                conn_http.close()
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
        finally:
            webui.SUPERVISOR_DB = original_db
            webui._runtime_truth_snapshot = original_snapshot

        self.assertEqual(response.status, 200)
        self.assertEqual(calls, [webui.RUNTIME_TRUTH_DEFAULT_LIMIT])
        self.assertIn('value="5"', body)

    def test_runtime_truth_api_clamps_zero_limit_query_parameter(self):
        original_db = webui.SUPERVISOR_DB
        original_snapshot = webui._runtime_truth_snapshot
        calls: list[int] = []

        def fake_snapshot(limit: int = 5) -> dict:
            calls.append(limit)
            return {"ok": True, "tasks": [], "incidents": [], "events": []}

        try:
            webui.SUPERVISOR_DB = Path("/tmp/does-not-matter.db")
            webui._runtime_truth_snapshot = fake_snapshot
            server = HTTPServer(("127.0.0.1", 0), webui.make_handler("fake-sv-cli"))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn_http = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn_http.request("GET", "/api/runtime-truth?limit=0")
                response = conn_http.getresponse()
                response.read()
                conn_http.close()
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
        finally:
            webui.SUPERVISOR_DB = original_db
            webui._runtime_truth_snapshot = original_snapshot

        self.assertEqual(response.status, 200)
        self.assertEqual(calls, [webui.RUNTIME_TRUTH_MIN_LIMIT])

    def test_runtime_truth_page_clamps_zero_limit_query_parameter(self):
        original_db = webui.SUPERVISOR_DB
        original_snapshot = webui._runtime_truth_snapshot
        calls: list[int] = []

        def fake_snapshot(limit: int = webui.RUNTIME_TRUTH_DEFAULT_LIMIT) -> dict:
            calls.append(limit)
            return {"ok": True, "tasks": [], "incidents": [], "events": []}

        try:
            webui.SUPERVISOR_DB = Path("/tmp/does-not-matter.db")
            webui._runtime_truth_snapshot = fake_snapshot
            server = HTTPServer(("127.0.0.1", 0), webui.make_handler("fake-sv-cli"))
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                conn_http = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                conn_http.request("GET", "/runtime-truth?limit=0")
                response = conn_http.getresponse()
                body = response.read().decode("utf-8")
                conn_http.close()
            finally:
                server.shutdown()
                thread.join(timeout=5)
                server.server_close()
        finally:
            webui.SUPERVISOR_DB = original_db
            webui._runtime_truth_snapshot = original_snapshot

        self.assertEqual(response.status, 200)
        self.assertEqual(calls, [webui.RUNTIME_TRUTH_MIN_LIMIT])
        self.assertIn('value="1"', body)


if __name__ == "__main__":
    unittest.main()
