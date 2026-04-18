"""
Database Connection Manager - Connects      Python to Phase 1 MySQL DB
Provides unified interface for all database operations
"""

import mysql.connector
from mysql.connector import Error
from typing import Optional, List, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Manages all connections to sousse_smart_city_projet_module database"""
    
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
    
    def connect(self) -> bool:
        """Établir connexion à la BD"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                use_pure=True
            )
            self.cursor = self.connection.cursor(dictionary=True, buffered=True)
            logger.info(f"✅ Connected to {self.database} at {self.host}:{self.port}")
            return True
        except Error as err:
            logger.error(f"❌ Connection error: {err}")
            return False
    
    def close(self):
        """Fermer connexion"""
        if self.connection and self.connection.is_connected():
            if self.cursor:
                self.cursor.close()
            self.connection.close()
            logger.info("Connection closed")
    
    def execute_query(self, query: str, params: tuple = None) -> bool:
        """Exécuter query (INSERT/UPDATE/DELETE)"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            self.connection.commit()
            logger.debug(f"✅ Query executed: {query[:60]}...")
            return True
        except Error as err:
            self.connection.rollback()
            logger.error(f"❌ Query error: {err}")
            return False
    
    def fetch_all(self, query: str, params: tuple = None) -> List[Dict]:
        """Récupérer tous les résultats"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchall()
        except Error as err:
            logger.error(f"❌ Fetch error: {err}")
            return []
    
    def fetch_one(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Récupérer un seul résultat"""
        try:
            if params:
                self.cursor.execute(query, params)
            else:
                self.cursor.execute(query)
            return self.cursor.fetchone()
        except Error as err:
            logger.error(f"❌ Fetch error: {err}")
            return None
    
    def get_count(self, query: str, params: tuple = None) -> int:
        """Récupérer count d'une requête"""
        rows = self.fetch_all(query, params)
        return len(rows) if rows else 0
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Global instance
_db = None

def get_db() -> DatabaseConnection:
    """Récupérer instance BD globale (singleton)"""
    global _db
    if _db is None:
        _db = DatabaseConnection()
        _db.connect()
    return _db

def reset_db():
    """Reset la connexion globale"""
    global _db
    if _db:
        _db.close()
    _db = None
