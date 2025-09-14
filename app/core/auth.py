from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.models.auth import UserInfo, Permissions
from app.services.auth_service import auth_service

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> UserInfo:
    user = auth_service.get_current_user_from_token(credentials.credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный токен аутентификации",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_current_user_from_token(token: str) -> Optional[UserInfo]:
    return auth_service.get_current_user_from_token(token)


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[UserInfo]:
    if not credentials:
        return None
    
    return auth_service.get_current_user_from_token(credentials.credentials)


def require_permission(permission: str):
    async def check_permission(current_user: UserInfo = Depends(get_current_user)):
        if not auth_service.check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав: требуется {permission}"
            )
        return current_user
    
    return check_permission


def require_role(role: str):
    async def check_role(current_user: UserInfo = Depends(get_current_user)):
        if not auth_service.check_role(current_user, role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав: требуется роль {role} или выше"
            )
        return current_user
    
    return check_role


async def require_manager(current_user: UserInfo = Depends(require_role("Менеджер"))):
    return current_user


async def require_admin(current_user: UserInfo = Depends(require_role("Администратор"))):
    return current_user


async def require_director(current_user: UserInfo = Depends(require_role("Директор"))):
    return current_user


async def can_manage_guests(current_user: UserInfo = Depends(require_permission(Permissions.CREATE_GUEST))):
    return current_user


async def can_manage_rooms(current_user: UserInfo = Depends(require_permission(Permissions.CREATE_ROOM))):
    return current_user


async def can_manage_users(current_user: UserInfo = Depends(require_permission(Permissions.MANAGE_USERS))):
    return current_user


async def can_generate_reports(current_user: UserInfo = Depends(require_permission(Permissions.GENERATE_REPORTS))):
    return current_user


async def can_view_logs(current_user: UserInfo = Depends(require_permission(Permissions.READ_ACTION_LOGS))):
    return current_user