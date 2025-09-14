from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from datetime import datetime, date

from app.models.action_log import (
    ActionLogWithUser, ActionLogFilter, ActionLogSummary, ActionType
)
from app.services.action_log_service import action_log_service
from app.core.auth import require_admin, get_current_user
from app.models.auth import UserInfo


class ActionLogController:
    def __init__(self):
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route(
            "/", 
            self.get_action_logs, 
            methods=["GET"], 
            response_model=List[ActionLogWithUser],
            dependencies=[Depends(require_admin)]
        )
        self.router.add_api_route(
            "/summary", 
            self.get_user_summary, 
            methods=["GET"], 
            response_model=List[ActionLogSummary],
            dependencies=[Depends(require_admin)]
        )
        self.router.add_api_route(
            "/stats", 
            self.get_system_stats, 
            methods=["GET"],
            dependencies=[Depends(require_admin)]
        )

    async def get_action_logs(
        self,
        user_id: Optional[int] = Query(None, description="ID пользователя для фильтрации"),
        username: Optional[str] = Query(None, description="Имя пользователя для поиска"),
        action_type: Optional[ActionType] = Query(None, description="Тип действия"),
        table_name: Optional[str] = Query(None, description="Название таблицы"),
        date_from: Optional[date] = Query(None, description="Начальная дата (YYYY-MM-DD)"),
        date_to: Optional[date] = Query(None, description="Конечная дата (YYYY-MM-DD)"),
        limit: int = Query(100, ge=1, le=1000, description="Количество записей"),
        offset: int = Query(0, ge=0, description="Смещение"),
        current_user: UserInfo = Depends(require_admin)
    ) -> List[ActionLogWithUser]:
        """
        Получение журнала событий с фильтрацией.
        Доступно только системным администраторам.
        
        Позволяет фильтровать события по:
        - Пользователю (ID или имени)
        - Типу действия
        - Таблице
        - Диапазону дат
        """
        try:
            date_from_dt = datetime.combine(date_from, datetime.min.time()) if date_from else None
            date_to_dt = datetime.combine(date_to, datetime.max.time()) if date_to else None
            
            filters = ActionLogFilter(
                user_id=user_id,
                username=username,
                action_type=action_type,
                table_name=table_name,
                date_from=date_from_dt,
                date_to=date_to_dt,
                limit=limit,
                offset=offset
            )
            
            logs = action_log_service.get_logs_with_filters(filters)
            return logs
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при получении журнала событий: {str(e)}"
            )

    async def get_user_summary(
        self,
        date_from: Optional[date] = Query(None, description="Начальная дата периода"),
        date_to: Optional[date] = Query(None, description="Конечная дата периода"),
        current_user: UserInfo = Depends(require_admin)
    ) -> List[ActionLogSummary]:
        """
        Получение сводки действий по пользователям.
        Показывает статистику активности сотрудников за период.
        """
        try:
            summary = action_log_service.get_user_actions_summary(
                date_from=date_from,
                date_to=date_to
            )
            return summary
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при получении сводки по пользователям: {str(e)}"
            )

    async def get_system_stats(
        self,
        date_from: Optional[date] = Query(None, description="Начальная дата периода"),
        date_to: Optional[date] = Query(None, description="Конечная дата периода"),
        current_user: UserInfo = Depends(require_admin)
    ) -> dict:
        """
        Получение общей статистики системы.
        Показывает количество действий по типам, активность по дням и т.д.
        """
        try:
            stats = action_log_service.get_system_activity_stats(
                date_from=date_from,
                date_to=date_to
            )
            return stats
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при получении статистики системы: {str(e)}"
            )


action_log_controller = ActionLogController()