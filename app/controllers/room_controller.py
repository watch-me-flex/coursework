from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from datetime import date

from app.models.room import (
    Room, RoomCreate, RoomUpdate, RoomType, RoomWithType, RoomAvailability
)
from app.services.room_service import room_service
from app.models.action_log import ActionType


class RoomController:
    def __init__(self):
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route("/types", self.get_room_types, methods=["GET"], response_model=List[RoomType])
        self.router.add_api_route("/types", self.create_room_type, methods=["POST"], response_model=RoomType)
        
        self.router.add_api_route("/", self.create_room, methods=["POST"], response_model=Room)
        self.router.add_api_route("/", self.get_rooms, methods=["GET"], response_model=List[RoomWithType])
        self.router.add_api_route("/{room_id}", self.get_room, methods=["GET"], response_model=Room)
        self.router.add_api_route("/{room_id}", self.update_room, methods=["PUT"], response_model=Room)
        self.router.add_api_route("/{room_id}", self.delete_room, methods=["DELETE"])
        
        self.router.add_api_route("/available", self.get_available_rooms, methods=["GET"], response_model=List[RoomAvailability])
        self.router.add_api_route("/number/{room_number}", self.get_room_by_number, methods=["GET"], response_model=Room)
        self.router.add_api_route("/{room_id}/availability", self.set_room_availability, methods=["PATCH"], response_model=Room)
        self.router.add_api_route("/statistics", self.get_room_statistics, methods=["GET"])

    async def create_room_type(self, code: str, name: str, description: Optional[str] = None) -> RoomType:
        try:
            room_type = room_service.create_room_type(code, name, description)
            return room_type
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при создании типа номера")

    async def get_room_types(self) -> List[RoomType]:
        try:
            room_types = room_service.get_room_types()
            return room_types
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении типов номеров")

    async def create_room(self, room_data: RoomCreate) -> Room:
        try:
            room = room_service.create_room(room_data)
            return room
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при создании номера")

    async def get_rooms(
        self, 
        skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
        limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей")
    ) -> List[RoomWithType]:
        try:
            rooms = room_service.get_all(skip=skip, limit=limit)
            return rooms
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении списка номеров")

    async def get_room(self, room_id: int) -> Room:
        try:
            room = room_service.get_by_id(room_id)
            if not room:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Номер не найден")
            return room
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении данных номера")

    async def get_room_by_number(self, room_number: str) -> Room:
        try:
            room = room_service.get_by_number(room_number)
            if not room:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Номер не найден")
            return room
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении данных номера")

    async def update_room(self, room_id: int, room_data: RoomUpdate) -> Room:
        try:
            room = room_service.update(room_id, room_data)
            if not room:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Номер не найден")
            return room
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при обновлении данных номера")

    async def delete_room(self, room_id: int):
        try:
            success = room_service.delete(room_id)
            if not success:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Номер не найден")
            return {"message": "Номер успешно удален"}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при удалении номера")

    async def get_available_rooms(
        self,
        check_in_date: Optional[date] = Query(None, description="Дата заселения"),
        check_out_date: Optional[date] = Query(None, description="Дата выселения")
    ) -> List[RoomAvailability]:
        try:
            if check_in_date and check_out_date and check_in_date >= check_out_date:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Дата заселения должна быть раньше даты выселения")
            
            rooms = room_service.get_available_rooms(check_in_date, check_out_date)
            return rooms
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении доступных номеров")

    async def set_room_availability(self, room_id: int, is_available: bool) -> Room:
        try:
            room = room_service.set_availability(room_id, is_available)
            if not room:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Номер не найден")
            
            status_text = "доступным" if is_available else "недоступным"
            return room
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при изменении доступности номера")

    async def get_room_statistics(self):
        try:
            stats = room_service.get_room_statistics()
            return stats
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении статистики")


router = RoomController().router