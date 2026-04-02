import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from wilson.source_oracle_incidents import read_oracle_incidents


class WilsonOracleIncidentSourceTests(unittest.TestCase):
    def test_reads_oracle_incident_rows(self):
        fd, path = tempfile.mkstemp(suffix='.db')
        Path(path).unlink(missing_ok=True)
        conn = sqlite3.connect(path)
        conn.execute(
            """
            CREATE TABLE oracle_incidents (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              ts TEXT,
              trace_id TEXT,
              incident_class TEXT,
              severity TEXT,
              confidence REAL,
              probable_root_cause TEXT,
              degradation TEXT,
              should_notify_wilson INTEGER,
              wilson_message TEXT,
              payload_json TEXT
            )
            """
        )
        conn.execute(
            """
            INSERT INTO oracle_incidents (
              ts, trace_id, incident_class, severity, confidence,
              probable_root_cause, degradation, should_notify_wilson,
              wilson_message, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                '2026-04-03T00:00:00Z',
                'trace-1',
                'identity_control_plane_failure',
                'high',
                0.9,
                'expired_or_invalid_oauth_token',
                'codex_lane_unavailable',
                1,
                'Codex lane unavailable',
                '{"event_type":"auth_refresh_failure"}',
            ),
        )
        conn.commit()
        conn.close()

        rows = read_oracle_incidents(path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['trace_id'], 'trace-1')
        self.assertEqual(rows[0]['payload_json']['event_type'], 'auth_refresh_failure')


if __name__ == '__main__':
    unittest.main()
