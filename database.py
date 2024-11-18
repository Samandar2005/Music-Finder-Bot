import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime

# Postgres ulanish sozlamalari
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://samandar:1234@localhost:5432/telegram_bot")


def get_db_connection():
    """Bazaga ulanish."""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def initialize_database():
    """Ma'lumotlar bazasini yaratish."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL UNIQUE,
                    first_name TEXT,
                    username TEXT,
                    last_interaction TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS searches (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    query TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                );
            """)
            conn.commit()


def log_user_interaction(user):
    """Foydalanuvchi maʼlumotlarini bazaga qoʻshish yoki yangilash."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (user_id, first_name, username, last_interaction)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (user_id) DO UPDATE
                SET last_interaction = NOW();
            """, (user.id, user.first_name, user.username))
            conn.commit()


def log_search(user_id, query):
    """Foydalanuvchi soʻrovini bazaga qoʻshish."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO searches (user_id, query) VALUES (%s, %s);
            """, (user_id, query))
            conn.commit()


def get_monthly_stats():
    """Oylik statistika."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS search_count, COUNT(DISTINCT user_id) AS active_users
                FROM searches
                WHERE DATE_PART('month', created_at) = DATE_PART('month', NOW());
            """)
            return cursor.fetchone()
