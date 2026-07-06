"""Metadata Index – SQLite jako lekki indeks laboratorium."""

import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional


class MetadataIndex:
    def __init__(self, db_path: str = "storage/metadata_index.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self):
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS experiments (
                experiment_id TEXT PRIMARY KEY,
                workflow_version TEXT NOT NULL,
                parent_experiment TEXT,
                manifest_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                genome TEXT NOT NULL,
                scenario TEXT NOT NULL,
                seed INTEGER NOT NULL,
                ticks INTEGER NOT NULL,
                workflow_version TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                summary_metrics TEXT,
                artifact_pointers TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES experiments(experiment_id)
            );

            CREATE INDEX IF NOT EXISTS idx_runs_experiment ON runs(experiment_id);
            CREATE INDEX IF NOT EXISTS idx_runs_genome ON runs(genome);
            CREATE INDEX IF NOT EXISTS idx_runs_scenario ON runs(scenario);
        """)
        self.conn.commit()

    def register_experiment(self, experiment_id: str, manifest_dict: Dict[str, Any],
                           workflow_version: str = "0.4", parent_experiment: Optional[str] = None):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO experiments (experiment_id, workflow_version, parent_experiment, manifest_json) VALUES (?, ?, ?, ?)",
            (experiment_id, workflow_version, parent_experiment, json.dumps(manifest_dict))
        )
        self.conn.commit()

    def register_run(self, run_id: str, experiment_id: str, genome: str,
                    scenario: str, seed: int, ticks: int, workflow_version: str,
                    status: str = "pending", summary_metrics: Dict = None,
                    artifact_pointers: Dict = None):
        cursor = self.conn.cursor()
        cursor.execute(
            """INSERT OR REPLACE INTO runs
               (run_id, experiment_id, genome, scenario, seed, ticks,
                workflow_version, status, summary_metrics, artifact_pointers)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (run_id, experiment_id, genome, scenario, seed, ticks,
             workflow_version, status,
             json.dumps(summary_metrics or {}),
             json.dumps(artifact_pointers or {}))
        )
        self.conn.commit()

    def get_experiment_runs(self, experiment_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM runs WHERE experiment_id = ? ORDER BY run_id",
            (experiment_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_run_count_by_status(self, experiment_id: str) -> Dict[str, int]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT status, COUNT(*) as cnt FROM runs WHERE experiment_id = ? GROUP BY status",
            (experiment_id,)
        )
        return {row["status"]: row["cnt"] for row in cursor.fetchall()}

    def list_experiments(self) -> List[Dict[str, Any]]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM experiments ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        if self.conn:
            self.conn.close()
