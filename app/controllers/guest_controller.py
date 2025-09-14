from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from datetime import date

from app.models.guest import (
    Guest, GuestCreate, GuestUpdate, GuestSearchResult, GuestWithRoom
)
from app.services.guest_service import guest_service
from app.models.action_log import ActionType


class GuestController:
    def __init__(self):
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route("/", self.create_guest, methods=["POST"], response_model=Guest)
        self.router.add_api_route("/", self.get_guests, methods=["GET"], response_model=List[Guest])
        self.router.add_api_route("/{guest_id}", self.get_guest, methods=["GET"], response_model=Guest)
        self.router.add_api_route("/{guest_id}", self.update_guest, methods=["PUT"], response_model=Guest)
        self.router.add_api_route("/{guest_id}", self.delete_guest, methods=["DELETE"])
        
        self.router.add_api_route("/search/passport/{passport_number}", self.search_by_passport, methods=["GET"], response_model=GuestWithRoom)
        self.router.add_api_route("/search/name", self.search_by_name, methods=["GET"], response_model=List[GuestSearchResult])
        self.router.add_api_route("/filter", self.filter_guests, methods=["GET"], response_model=List[GuestSearchResult])
        
        self.router.add_api_route("/current", self.get_current_guests, methods=["GET"], response_model=List[GuestWithRoom])
        self.router.add_api_route("/statistics", self.get_guest_statistics, methods=["GET"])

    async def create_guest(self, guest_data: GuestCreate) -> Guest:
        """
        Регистрация нового постояльца.
        
        - **passport_number**: Номер паспорта в формате NNNN-NNNNNN
        - **last_name**: Фамилия
        - **first_name**: Имя
        - **middle_name**: Отчество
        - **birth_year**: Год рождения
        - **gender**: Пол (М/Ж или M/F)
        - **registration_address**: Адрес по прописке
        - **phone**: Номер телефона (опционально)
        - **purpose_of_visit**: Цель прибытия (опционально)
        - **how_heard_about_us**: Откуда узнал о гостинице (опционально)
        """
        try:
            guest = guest_service.create(guest_data)
            return guest
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при создании постояльца")

    async def get_guests(
        self, 
        skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
        limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей")
    ) -> List[Guest]:
        """
        Просмотр всех зарегистрированных постояльцев.
        
        - **skip**: Количество записей для пропуска (пагинация)
        - **limit**: Максимальное количество записей
        """
        try:
            guests = guest_service.get_all(skip=skip, limit=limit)
            return guests
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении списка постояльцев")

    async def get_guest(self, guest_id: int) -> Guest:
        """
        Получение информации о конкретном постояльце.
        
        - **guest_id**: ID постояльца
        """
        try:
            guest = guest_service.get_by_id(guest_id)
            if not guest:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Постоялец не найден")
            return guest
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении данных постояльца")

    async def update_guest(self, guest_id: int, guest_data: GuestUpdate) -> Guest:
        """
        Обновление данных постояльца.
        
        - **guest_id**: ID постояльца
        - **guest_data**: Данные для обновления
        """
        try:
            guest = guest_service.update(guest_id, guest_data)
            if not guest:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Постоялец не найден")
            # TODO: Добавить логирование действия
            return guest
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при обновлении данных постояльца")

    async def delete_guest(self, guest_id: int):
        """
        Удаление данных о постояльце.
        
        - **guest_id**: ID постояльца
        """
        try:
            success = guest_service.delete(guest_id)
            if not success:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Постоялец не найден")
            # TODO: Добавить логирование действия
            return {"message": "Постоялец успешно удален"}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при удалении постояльца")

    async def search_by_passport(self, passport_number: str) -> GuestWithRoom:
        """
        Поиск постояльца по номеру паспорта.
        Результат: все сведения о найденном постояльце и № гостиничного номера, в котором он проживает.
        
        - **passport_number**: Номер паспорта в формате NNNN-NNNNNN
        """
        try:
            guest = guest_service.get_by_passport(passport_number)
            if not guest:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Постоялец с указанным паспортом не найден")
            return guest
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при поиске постояльца")

    async def search_by_name(
        self,
        last_name: Optional[str] = Query(None, description="Фамилия"),
        first_name: Optional[str] = Query(None, description="Имя"), 
        middle_name: Optional[str] = Query(None, description="Отчество")
    ) -> List[GuestSearchResult]:
        """
        Поиск постояльца по ФИО.
        Результаты поиска: ФИО, Серия и номер паспорта.
        
        - **last_name**: Фамилия (частичное совпадение)
        - **first_name**: Имя (частичное совпадение)
        - **middle_name**: Отчество (частичное совпадение)
        """
        if not any([last_name, first_name, middle_name]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Необходимо указать хотя бы одно поле для поиска")
        
        try:
            guests = guest_service.search_by_name(last_name, first_name, middle_name)
            return guests
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при поиске постояльцев")

    async def filter_guests(
        self,
        room_number: Optional[str] = Query(None, description="Номер гостиничного номера"),
        check_in_date: Optional[date] = Query(None, description="Дата поселения"),
        passport_number: Optional[str] = Query(None, description="Номер паспорта (частичное совпадение)"),
        skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
        limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей")
    ) -> List[GuestSearchResult]:
        """
        Фильтрация данных о постояльцах по:
        - № гостиничного номера
        - Дате поселения
        - Паспортным данным
        
        - **room_number**: Номер комнаты
        - **check_in_date**: Дата заселения
        - **passport_number**: Номер паспорта или его часть
        - **skip**: Пагинация - количество записей для пропуска
        - **limit**: Пагинация - максимальное количество записей
        """
        try:
            guests = guest_service.filter_guests(
                room_number=room_number,
                check_in_date=check_in_date,
                passport_number=passport_number,
                skip=skip,
                limit=limit
            )
            return guests
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при фильтрации постояльцев")

    async def get_current_guests(self) -> List[GuestWithRoom]:
        """
        Получение списка текущих постояльцев в отеле.
        
        Возвращает постояльцев, которые в данный момент заселены в номера.
        """
        try:
            guests = guest_service.get_current_guests()
            return guests
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении списка текущих постояльцев")

    async def get_guest_statistics(self):
        """
        Получение статистики по постояльцам.
        
        Возвращает:
        - Общее количество постояльцев
        - Количество текущих постояльцев
        - Статистику по источникам информации о гостинице
        """
        try:
            stats = guest_service.get_guest_statistics()
            return stats
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении статистики")


router = GuestController().router