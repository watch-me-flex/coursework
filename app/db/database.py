from typing import Any
from app.models.user import User
from psycopg2.pool import SimpleConnectionPool
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from app.config import settings

class DBSession:
    _pool: SimpleConnectionPool = None

    def __init__(self, autocommit=True) -> None:
        if DBSession._pool is None:
            self._init_pool()
        self.autocommit: bool = autocommit
        self.conn = None
        self.cursor = None

    @classmethod
    def _init_db(cls) -> None:
        with DBSession() as db:
            if db is None:
                raise Exception("Подключние к базе данных не было осуществлено")
                
            db.execute("SELECT 1 FROM users WHERE username = %s", ("admin",))

            if not db.fetchone():
                from app.services import user_service

                test_user: User = user_service.create(
                    username="admin",
                    password="root",
                    role_id=1,
                    full_name="admin"
                )

                print("✅ Администратор создан: ", test_user.username)

    @classmethod
    def _init_pool(cls) -> None:
        try:
            cls._pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                dbname=settings.DB_NAME,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                host=settings.DB_HOST,
                port=settings.DB_PORT
            )
            
            conn = cls._pool.getconn()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    print("✅ Подключение к базе данных успешно")
            finally:
                cls._pool.putconn(conn)
        except Exception as e:
            print(f"❌ Ошибка подключения к БД: {e}")
            raise

    def __enter__(self) -> Any | None:
        if DBSession._pool is None:
            raise Exception("Подключние к базе данных не было осуществлено")

        self.conn = DBSession._pool.getconn()
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.conn is None:
            raise Exception("Подключние к базе данных не было установлено")

        try:
            if exc_type is None and self.autocommit:
                self.conn.commit()
            elif exc_type is not None:
                self.conn.rollback()
        except Exception as e:
            print(f"❌ Ошибка транзакции: {e}")
            if self.conn:
                self.conn.rollback()
            raise
        finally:
            if self.cursor:
                self.cursor.close()
            if self.conn and DBSession._pool:
                DBSession._pool.putconn(self.conn)

import atexit

def cleanup_db_pool():
    if hasattr(DBSession, '_pool') and DBSession._pool is not None:
        DBSession._pool.closeall()

atexit.register(cleanup_db_pool)
