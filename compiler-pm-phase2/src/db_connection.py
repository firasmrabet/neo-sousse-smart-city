"""
Database Connection Module - Access to Phase 1 MySQL database from      Python
"""

import mysql.connector
from mysql.connector import Error
from typing import Optional, List, Dict, Any
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Singleton database connection manager"""
    
    _instance = None
    
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 3306,
        user: str = "root",
        password: str = "",
        database: str = "sousse_smart_city_projet_module"
    ):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
    
    @classmethod
    def get_instance(cls):
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance.connect()
        return cls._instance
    
    def reconnect(self) -> bool:
        """Reconnect to ensure fresh connection with no cached data"""
        try:
            if self.connection and self.connection.is_connected():
                self.close()
            return self.connect()
        except Error as err:
            logger.error(f"Reconnection error: {err}")
            return False
    
    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                use_pure=True,
                autocommit=True,
                connection_timeout=3
            )
            self.cursor = self.connection.cursor(dictionary=True, buffered=True)
            logger.info(f"✅ DB Connected: {self.database}")
            return True
        except Error as err:
            logger.error(f"❌ Connection error: {err}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            if self.cursor:
                self.cursor.close()
            self.connection.close()
            logger.info("DB Connection closed")
    
    def _db_available(self) -> bool:
        """Check if connection and cursor are ready; try reconnect once."""
        if self.cursor and self.connection and self.connection.is_connected():
            return True
        # Attempt a single reconnect
        return self.connect()

    def execute_query(self, query: str, params: tuple = None) -> bool:
        """Execute write query (INSERT/UPDATE/DELETE)"""
        if not self._db_available():
            logger.warning("execute_query skipped: no DB connection")
            return False
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            return True
        except Error as err:
            logger.error(f"Query error: {err}")
            try:
                self.connection.rollback()
            except Exception:
                pass
            return False
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """Fetch all query results"""
        if not self._db_available():
            logger.warning("fetch_all skipped: no DB connection")
            return []
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as err:
            logger.error(f"Fetch error: {err}")
            return []
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Fetch single result"""
        if not self._db_available():
            logger.warning("fetch_one skipped: no DB connection")
            return None
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except Error as err:
            logger.error(f"Fetch error: {err}")
            return None
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Convenience function
def get_db() -> DatabaseConnection:
    """Get database connection instance"""
    return DatabaseConnection.get_instance()
