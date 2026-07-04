import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

class CLOSStorage:
    def __init__(self, db_path: str = "storage/clos.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None

    async def connect(self):
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        await self.create_tables()

    async def create_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                config TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'created'
            );

            CREATE TABLE IF NOT EXISTS cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_id TEXT NOT NULL,
                cycle_number INTEGER NOT NULL,
                brain_state TEXT,
                world_state TEXT,
                metrics TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            );

            CREATE TABLE IF NOT EXISTS genomes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                genes TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                experiment_id TEXT NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (experiment_id) REFERENCES experiments(id)
            );
        """)
        self.conn.commit()

    async def save_cycle(self, experiment_id: str, cycle_data: Dict[str, Any]):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO cycles (experiment_id, cycle_number, brain_state, world_state, metrics)
            VALUES (?, ?, ?, ?, ?)
        """, (
            experiment_id,
            cycle_data["cycle_number"],
            json.dumps(cycle_data.get("brain_state", {})),
            json.dumps(cycle_data.get("world_state", {})),
            json.dumps(cycle_data.get("metrics", {}))
        ))
        self.conn.commit()

    async def get_cycles(self, experiment_id: str) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM cycles WHERE experiment_id = ? ORDER BY cycle_number",
            (experiment_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def close(self):
        if self.conn:
            self.conn.close()
