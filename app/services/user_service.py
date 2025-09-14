from typing import List, Optional
from app.models.user import User, UserInDB
from app.db.database import DBSession

class UserService:
    @classmethod
    def create(
        cls,
        username: str,
        password: str,
        role_id: int,
        full_name: Optional[str] = None
    ) -> UserInDB:
        from app.utils.security import get_password_hash

        with DBSession() as db:
            existing_user = cls.get_by_username(username)
            if existing_user:
                raise ValueError(f"Пользователь с именем {username} уже существует")

            hashed_password = get_password_hash(password)
            
            db.execute(
                """
                INSERT INTO users (username, hashed_password, role_id, full_name)
                VALUES (%s, %s, %s, %s)
                RETURNING *
                """,
                (username, hashed_password, role_id, full_name)
            )
            result = db.fetchone()
            return UserInDB(**result)

    @classmethod
    def get_by_id(cls, user_id: int) -> Optional[UserInDB]:
        with DBSession() as db:
            db.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            result = db.fetchone()
            return UserInDB(**result) if result else None

    @classmethod
    def get_by_username(cls, username: str) -> Optional[UserInDB]:
        with DBSession() as db:
            db.execute("SELECT * FROM users WHERE username = %s", (username,))
            result = db.fetchone()
            return UserInDB(**result) if result else None

    @classmethod
    def get_all(
        cls,
        skip: int = 0,
        limit: int = 100
    ) -> List[UserInDB]:
        with DBSession() as db:
            db.execute("SELECT * FROM users ORDER BY id LIMIT %s OFFSET %s", (limit, skip))
            results = db.fetchall()
            return [UserInDB(**row) for row in results]

    @classmethod
    def update(
        cls,
        user_id: int,
        **kwargs
    ) -> Optional[UserInDB]:
        if not kwargs:
            return None
            
        with DBSession() as db:
            db.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            if not db.fetchone():
                return None
                
            set_parts = []
            values = [] 

            for key, value in kwargs.items():
                if value is not None:
                    set_parts.append(f"{key} = %s")
                    values.append(value)
            
            if not set_parts:
                return None
                
            query = f"""
                UPDATE users 
                SET {', '.join(set_parts)}
                WHERE id = %s
                RETURNING *
            """
            values.append(user_id)
            
            db.execute(query, tuple(values))
            result = db.fetchone()
            return UserInDB(**result) if result else None

    @classmethod
    def delete(cls, user_id: int) -> bool:
        with DBSession() as db:
            db.execute("DELETE FROM users WHERE id = %s", (user_id,))
            return db.rowcount > 0

user_service = UserService()