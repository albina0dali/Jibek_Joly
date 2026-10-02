import json
import sqlite3
from pathlib import Path


class HistoryStore:
    def __init__(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS snapshots (time INTEGER PRIMARY KEY, payload TEXT NOT NULL)')
        self.db.execute('CREATE TABLE IF NOT EXISTS actions (id INTEGER PRIMARY KEY, time INTEGER, description TEXT)')
        self.db.execute('CREATE TABLE IF NOT EXISTS configuration (id INTEGER PRIMARY KEY CHECK(id=1), payload TEXT NOT NULL)')

    def configuration(self):
        row=self.db.execute('SELECT payload FROM configuration WHERE id=1').fetchone()
        return json.loads(row[0]) if row else None

    def save_configuration(self, settings):
        self.db.execute('INSERT OR REPLACE INTO configuration VALUES (1,?)',(json.dumps(settings),))
        self.db.commit()

    def save(self, snapshot):
        now = snapshot['time']
        self.db.execute('INSERT OR REPLACE INTO snapshots VALUES (?,?)', (now,json.dumps(snapshot)))
        self.db.execute('DELETE FROM snapshots WHERE time < ?', (now-3600,))
        self.db.commit()

    def get(self, at):
        row = self.db.execute('SELECT payload FROM snapshots WHERE time<=? ORDER BY time DESC LIMIT 1', (at,)).fetchone()
        return json.loads(row[0]) if row else None

    def index(self):
        return [dict(time=r[0],quality=r[1]) for r in self.db.execute("SELECT time,json_extract(payload,'$.quality.value') FROM snapshots ORDER BY time")]

    def log(self, now, description):
        self.db.execute('INSERT INTO actions(time,description) VALUES (?,?)',(now,description))
        self.db.commit()

    def actions(self):
        return [dict(time=r[0],description=r[1]) for r in self.db.execute('SELECT time,description FROM actions ORDER BY id DESC LIMIT 100')]

    def clear(self):
        self.db.execute('DELETE FROM snapshots')
        self.db.execute('DELETE FROM actions')
        self.db.commit()
