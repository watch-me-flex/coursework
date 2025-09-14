from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.action_log_service import action_log_service
from app.services.auth_service import auth_service
import logging

logger = logging.getLogger(__name__)


class UserContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        skip_paths = ["/docs", "/redoc", "/openapi.json", "/health", "/auth/login"]
        
        if any(request.url.path.startswith(path) for path in skip_paths):
            return await call_next(request)
        
        auth_header = request.headers.get("Authorization")
        user_id = None
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                user_info = auth_service.get_current_user_from_token(token)
                if user_info:
                    user_id = user_info.id
            except Exception as e:
                logger.warning(f"Не удалось получить информацию о пользователе из токена: {e}")
        
        if user_id:
            try:
                action_log_service.set_current_user_context(user_id)
            except Exception as e:
                logger.error(f"Ошибка при установке контекста пользователя: {e}")
        
        response = await call_next(request)
        
        try:
            action_log_service.clear_user_context()
        except Exception as e:
            logger.error(f"Ошибка при очистке контекста пользователя: {e}")
        
        return response