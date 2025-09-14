from typing import Optional
from app.models.auth import UserInfo, ROLE_PERMISSIONS
from app.models.user import UserInDB
from app.services.user_service import user_service
from app.utils.security import verify_password, create_access_token, verify_token
from app.config import settings
from app.db.database import DBSession


class AuthService:
    
    @classmethod
    def authenticate_user(cls, username: str, password: str) -> Optional[UserInDB]:
        user = user_service.get_by_username(username)
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
            
        return user
    
    @classmethod
    def create_access_token_for_user(cls, user: UserInDB) -> dict:
        user_with_role = cls.get_user_with_role(user.id)
        if not user_with_role:
            raise ValueError("Не удалось получить данные о роли пользователя")
        
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "role": user_with_role.role_name,
            "permissions": user_with_role.permissions
        }
        
        access_token = create_access_token(token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.JWT_EXPIRE_MS // 1000,
            "user_info": user_with_role
        }
    
    @classmethod
    def get_user_with_role(cls, user_id: int) -> Optional[UserInfo]:
        with DBSession() as db:
            db.execute("""
                SELECT u.id, u.username, u.full_name, r.name as role_name
                FROM users u
                JOIN roles r ON u.role_id = r.id
                WHERE u.id = %s
            """, (user_id,))
            
            result = db.fetchone()
            if not result:
                return None
            
            role_name = result['role_name']
            permissions = ROLE_PERMISSIONS.get(role_name, [])
            
            return UserInfo(
                id=result['id'],
                username=result['username'],
                full_name=result['full_name'],
                role_name=role_name,
                permissions=permissions
            )
    
    @classmethod
    def get_current_user_from_token(cls, token: str) -> Optional[UserInfo]:
        try:
            payload = verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            return cls.get_user_with_role(int(user_id))
            
        except Exception:
            return None
    
    @classmethod
    def check_permission(cls, user: UserInfo, required_permission: str) -> bool:
        return required_permission in user.permissions
    
    @classmethod
    def check_role(cls, user: UserInfo, required_role: str) -> bool:
        role_hierarchy = ["manager", "admin", "owner"]        
        russian_roles = {"Менеджер": "manager", "Администратор": "admin", "Директор": "owner"}
        
        try:
            user_role = russian_roles.get(user.role_name, user.role_name)
            required_role_eng = russian_roles.get(required_role, required_role)
            
            user_role_level = role_hierarchy.index(user_role)
            required_role_level = role_hierarchy.index(required_role_eng)
            return user_role_level >= required_role_level
        except ValueError:
            return False
    
    @classmethod
    def change_password(cls, user_id: int, current_password: str, new_password: str) -> bool:
        user = user_service.get_by_id(user_id)
        if not user:
            raise ValueError("Пользователь не найден")
        
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Неверный текущий пароль")
        
        from app.utils.security import get_password_hash
        
        with DBSession() as db:
            hashed_new_password = get_password_hash(new_password)
            db.execute(
                "UPDATE users SET hashed_password = %s, updated_at = CURRENT_TIMESTAMP WHERE id = %s",
                (hashed_new_password, user_id)
            )
            return db.rowcount > 0


auth_service = AuthService()