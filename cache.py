import os
import sqlite3
import pickle
from time import time
from typing_extensions import Optional
import logging
logger = logging.getLogger(__name__)
class SqliteCache:
    """ SQLite-based cache with expiration support """

    _create_sql = (
        "CREATE TABLE IF NOT EXISTS entries "
        "(key TEXT PRIMARY KEY, val BLOB, exp FLOAT)"
    )
    _create_index = "CREATE INDEX IF NOT EXISTS keyname_index ON entries (key)"
    _get_sql = "SELECT val, exp FROM entries WHERE key = ?"
    _del_sql = "DELETE FROM entries WHERE key = ?"
    _set_sql = "REPLACE INTO entries (key, val, exp) VALUES (?, ?, ?)"
    _add_sql = "INSERT INTO entries (key, val, exp) VALUES (?, ?, ?)"
    _clear_sql = "DELETE FROM entries"

    def __init__(self, path: str):
            """ Initialize cache and ensure database file exists """
            self.path = os.path.abspath(path)
            self._ensure_db_file()
            self.connection = self._get_conn()

    def _ensure_db_file(self):
        """ Ensure the SQLite database file and directory exist """
        db_dir = os.path.dirname(self.path)
        os.makedirs(db_dir, exist_ok=True)  # Create directory if needed

        if not os.path.exists(self.path):
            open(self.path, 'a').close()  # Create empty file if it doesn't exist
            logger.info(f"Created new SQLite database file: {self.path}")

    def _get_conn(self):
        """ Returns a persistent SQLite connection """
        conn = sqlite3.connect(self.path, timeout=60, check_same_thread=False)
        with conn:
            conn.execute(self._create_sql)
            conn.execute(self._create_index)
        return conn

    def get(self, key: str):
        """ Retrieve a value from the cache """
        row = self.connection.execute(self._get_sql, (key,)).fetchone()
        if row:
            expire = row[1]
            if expire == 0 or expire > time():
                return pickle.loads(row[0])
        return None

    def set(self, key: str, value, timeout: Optional[int] = None):
        """ Add a key-value pair to the cache with an optional timeout """
        expire = 0 if timeout is None else time() + timeout
        data = pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)
        self.connection.execute(self._set_sql, (key, data, expire))
        self.connection.commit()

    def delete(self, key: str):
        """ Delete a cache entry """
        self.connection.execute(self._del_sql, (key,))
        self.connection.commit()

    def clear(self):
        """ Clear the entire cache """
        self.connection.execute(self._clear_sql)
        self.connection.commit()

    def __del__(self):
        """ Cleanup SQLite connection """
        if self.connection:
            self.connection.close()
