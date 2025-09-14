from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from datetime import date

from app.models.checkin import (
    CheckIn, CheckInCreate, CheckInUpdate, CheckInWithDetails,
    CheckOutRequest, CurrentGuestView, CheckInStatus
)
from app.services.checkin_service import checkin_service
from app.models.action_log import ActionType


class CheckInController:
    def __init__(self):
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route("/check-in", self.check_in_guest, methods=["POST"], response_model=CheckIn)
        self.router.add_api_route("/check-out", self.check_out_guest, methods=["POST"], response_model=CheckIn)
        
        self.router.add_api_route("/", self.get_all_check_ins, methods=["GET"], response_model=List[CheckInWithDetails])
        self.router.add_api_route("/{check_in_id}", self.get_check_in, methods=["GET"], response_model=CheckInWithDetails)
        self.router.add_api_route("/{check_in_id}", self.update_check_in, methods=["PUT"], response_model=CheckIn)
        self.router.add_api_route("/{check_in_id}/cancel", self.cancel_check_in, methods=["PATCH"], response_model=CheckIn)
        
        self.router.add_api_route("/current", self.get_current_guests, methods=["GET"], response_model=List[CurrentGuestView])
        self.router.add_api_route("/guest/{guest_id}/history", self.get_guest_check_ins, methods=["GET"], response_model=List[CheckInWithDetails])
        self.router.add_api_route("/room/{room_id}/history", self.get_room_check_ins, methods=["GET"], response_model=List[CheckInWithDetails])
        self.router.add_api_route("/statistics", self.get_occupancy_statistics, methods=["GET"])

    async def check_in_guest(
        self, 
        guest_id: int, 
        room_id: int, 
        check_in_date: Optional[date] = None
    ) -> CheckIn:
        """
        Поселение постояльца в номер.
        
        - **guest_id**: ID постояльца
        - **room_id**: ID номера
        - **check_in_date**: Дата заселения (по умолчанию - сегодня)
        """
        try:
            check_in = checkin_service.check_in_guest(guest_id, room_id, check_in_date)
            return check_in 
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при заселении постояльца")

    async def check_out_guest(self, check_out_request: CheckOutRequest) -> CheckIn:
        """
        Выселение постояльца.
        
        - **check_in_id**: ID заселения
        - **check_out_date**: Дата выселения (по умолчанию - сегодня)
        """
        try:
            check_in = checkin_service.check_out_guest(check_out_request)
            # TODO: Добавить логирование действия
            return check_in
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при выселении постояльца")

    async def get_all_check_ins(
        self,
        status_filter: Optional[CheckInStatus] = Query(None, alias="status", description="Фильтр по статусу заселения"),
        date_from: Optional[date] = Query(None, description="Фильтр от даты"),
        date_to: Optional[date] = Query(None, description="Фильтр до даты"),
        skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
        limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей")
    ) -> List[CheckInWithDetails]:
        """
        Получение списка всех заселений с фильтрацией.
        
        - **status**: Фильтр по статусу (Активно, Завершено, Отменено)
        - **date_from**: Фильтр от даты заселения
        - **date_to**: Фильтр до даты заселения
        - **skip**: Количество записей для пропуска (пагинация)
        - **limit**: Максимальное количество записей
        """
        try:
            check_ins = checkin_service.get_all_check_ins(
                status=status_filter,
                date_from=date_from,
                date_to=date_to,
                skip=skip,
                limit=limit
            )
            return check_ins
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении списка заселений")

    async def get_check_in(self, check_in_id: int) -> CheckInWithDetails:
        """
        Получение информации о конкретном заселении.
        
        - **check_in_id**: ID заселения
        """
        try:
            check_in = checkin_service.get_with_details(check_in_id)
            if not check_in:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заселение не найдено")
            return check_in
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении данных заселения")

    async def update_check_in(self, check_in_id: int, check_in_data: CheckInUpdate) -> CheckIn:
        """
        Обновление данных заселения.
        
        - **check_in_id**: ID заселения
        - **check_in_data**: Данные для обновления
        """
        try:
            check_in = checkin_service.update(check_in_id, check_in_data)
            if not check_in:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заселение не найдено")
            return check_in
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при обновлении данных заселения")

    async def cancel_check_in(self, check_in_id: int) -> CheckIn:
        """
        Отмена заселения.
        
        - **check_in_id**: ID заселения
        """
        try:
            check_in = checkin_service.cancel_check_in(check_in_id)
            if not check_in:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Заселение не найдено")
            return check_in
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при отмене заселения")

    async def get_current_guests(self) -> List[CurrentGuestView]:
        """
        Получение списка текущих гостей отеля.
        
        Возвращает постояльцев, которые в данный момент заселены в номера
        с подробной информацией о номерах и предыдущих заселениях.
        """
        try:
            guests = checkin_service.get_current_guests()
            return guests
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении списка текущих гостей")

    async def get_guest_check_ins(self, guest_id: int) -> List[CheckInWithDetails]:
        """
        Получение истории заселений постояльца.
        
        - **guest_id**: ID постояльца
        """
        try:
            check_ins = checkin_service.get_guest_check_ins(guest_id)
            return check_ins
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении истории заселений постояльца")

    async def get_room_check_ins(self, room_id: int) -> List[CheckInWithDetails]:
        """
        Получение истории заселений в номер.
        
        - **room_id**: ID номера
        """
        try:
            check_ins = checkin_service.get_room_check_ins(room_id)
            return check_ins
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении истории заселений номера")

    async def get_occupancy_statistics(
        self,
        date_from: Optional[date] = Query(None, description="Статистика от даты"),
        date_to: Optional[date] = Query(None, description="Статистика до даты")
    ):
        """
        Получение статистики по заселенности.
        
        - **date_from**: Период статистики от даты
        - **date_to**: Период статистики до даты
        
        Возвращает:
        - Общее количество заселений
        - Активные заселения
        - Завершенные заселения
        - Среднюю продолжительность проживания
        """
        try:
            stats = checkin_service.get_occupancy_statistics(date_from, date_to)
            return stats
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении статистики")


router = CheckInController().router