import os
import sqlite3
import json
# pyrefly: ignore [missing-import]
import asyncpg
from typing import Optional, Dict, Any
from config import settings

async def fetch_active_resume_from_db(user_id: str) -> Optional[Dict[str, Any]]:
    """
    Connects to the shared database and retrieves the structured_data
    of the active resume version for the specified user_id.
    """
    # 1. Determine if SQLite fallback is in use
    db_engine = os.environ.get("DB_ENGINE", "sqlite")
    
    if db_engine == "sqlite" and os.environ.get("DB_HOST") != "db":
        # SQLite Query
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "django_app", "db.sqlite3")
        if not os.path.exists(db_path):
            return None
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            query = """
                SELECT rv.structured_data 
                FROM resumes_resumeversion rv
                JOIN resumes_resume r ON rv.resume_id = r.id
                WHERE r.user_id = ? AND rv.is_active = 1
                LIMIT 1
            """
            cursor.execute(query, (user_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return json.loads(row[0])
        except Exception:
            pass
        return None
        
    else:
        # Postgres Query
        try:
            conn = await asyncpg.connect(
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                host=settings.DB_HOST,
                port=settings.DB_PORT
            )
            query = """
                SELECT rv.structured_data 
                FROM resumes_resumeversion rv
                JOIN resumes_resume r ON rv.resume_id = r.id
                WHERE r.user_id = $1 AND rv.is_active = TRUE
                LIMIT 1
            """
            row = await conn.fetchrow(query, user_id)
            await conn.close()
            if row:
                # asyncpg returns jsonb fields as parsed dicts or string
                data = row["structured_data"]
                if isinstance(data, str):
                    return json.loads(data)
                return data
        except Exception:
            pass
        return None
