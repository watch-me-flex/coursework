from fastapi import APIRouter, HTTPException, Depends, Query, status
from typing import List, Optional
from datetime import date

from app.models.service import (
    Service, ServiceCreate, ServiceUpdate, ServiceWithType,
    ServiceType, ServiceTypeCreate, ServiceTypeUpdate,
    ServiceUsageStats, ServiceRevenueReport
)
from app.services.service_service import service_service
from app.models.action_log import ActionType


class ServiceController:
    def __init__(self):
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route("/types", self.get_service_types, methods=["GET"], response_model=List[ServiceType])
        self.router.add_api_route("/types", self.create_service_type, methods=["POST"], response_model=ServiceType)
        self.router.add_api_route("/types/{type_id}", self.update_service_type, methods=["PUT"], response_model=ServiceType)
        self.router.add_api_route("/types/{type_id}", self.delete_service_type, methods=["DELETE"])
        self.router.add_api_route("/", self.create_service, methods=["POST"], response_model=Service)
        self.router.add_api_route("/", self.get_services, methods=["GET"], response_model=List[ServiceWithType])
        self.router.add_api_route("/{service_id}", self.get_service, methods=["GET"], response_model=ServiceWithType)
        self.router.add_api_route("/{service_id}", self.update_service, methods=["PUT"], response_model=Service)
        self.router.add_api_route("/{service_id}", self.delete_service, methods=["DELETE"])
        self.router.add_api_route("/type/{type_name}", self.get_services_by_type, methods=["GET"], response_model=List[ServiceWithType])
        self.router.add_api_route("/{service_id}/availability", self.set_service_availability, methods=["PATCH"], response_model=Service)
        self.router.add_api_route("/statistics/usage", self.get_service_usage_stats, methods=["GET"], response_model=List[ServiceUsageStats])
        self.router.add_api_route("/statistics/revenue", self.get_service_revenue_report, methods=["GET"], response_model=List[ServiceRevenueReport])
        self.router.add_api_route("/statistics/popular", self.get_popular_services, methods=["GET"])

    async def create_service_type(self, service_type_data: ServiceTypeCreate) -> ServiceType:
        try:
            service_type = service_service.create_service_type(service_type_data)
            return service_type
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при создании типа услуги")

    async def get_service_types(self) -> List[ServiceType]:
        try:
            service_types = service_service.get_service_types()
            return service_types
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении типов услуг")

    async def update_service_type(self, type_id: int, service_type_data: ServiceTypeUpdate) -> ServiceType:
        try:
            service_type = service_service.update_service_type(type_id, service_type_data)
            if not service_type:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип услуги не найден")
            return service_type
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при обновлении типа услуги")

    async def delete_service_type(self, type_id: int):
        try:
            success = service_service.delete_service_type(type_id)
            if not success:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Тип услуги не найден")
            return {"message": "Тип услуги успешно удален"}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при удалении типа услуги")

    async def create_service(self, service_data: ServiceCreate) -> Service:
        try:
            service = service_service.create_service(service_data)
            return service
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при создании услуги")

    async def get_services(
        self,
        type_id: Optional[int] = Query(None, description="Фильтр по типу услуги"),
        is_available: Optional[bool] = Query(None, description="Фильтр по доступности"),
        skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
        limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей")
    ) -> List[ServiceWithType]:
        try:
            services = service_service.get_all_services(
                type_id=type_id,
                is_available=is_available,
                skip=skip,
                limit=limit
            )
            return services
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении списка услуг")

    async def get_service(self, service_id: int) -> ServiceWithType:
        try:
            service = service_service.get_service_with_type(service_id)
            if not service:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Услуга не найдена")
            return service
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении данных услуги")

    async def update_service(self, service_id: int, service_data: ServiceUpdate) -> Service:
        try:
            service = service_service.update(service_id, service_data)
            if not service:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Услуга не найдена")
            return service
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при обновлении услуги")

    async def delete_service(self, service_id: int):
        try:
            success = service_service.delete(service_id)
            if not success:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Услуга не найдена")
            return {"message": "Услуга успешно удалена"}
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при удалении услуги")

    async def get_services_by_type(self, type_name: str) -> List[ServiceWithType]:
        try:
            services = service_service.get_services_by_type(type_name)
            return services
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении услуг по типу")

    async def set_service_availability(self, service_id: int, is_available: bool) -> Service:
        try:
            service = service_service.set_availability(service_id, is_available)
            if not service:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Услуга не найдена")
            
            status_text = "доступной" if is_available else "недоступной"
            return service
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при изменении доступности услуги")

    async def get_service_usage_stats(
        self,
        date_from: Optional[date] = Query(None, description="Статистика от даты"),
        date_to: Optional[date] = Query(None, description="Статистика до даты")
    ) -> List[ServiceUsageStats]:
        try:
            stats = service_service.get_service_usage_stats(date_from, date_to)
            return stats
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении статистики использования")

    async def get_service_revenue_report(
        self,
        date_from: Optional[date] = Query(None, description="Период отчета от даты"),
        date_to: Optional[date] = Query(None, description="Период отчета до даты")
    ) -> List[ServiceRevenueReport]:
        try:
            report = service_service.get_service_revenue_report(date_from, date_to)
            return report
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при формировании отчета по услугам")

    async def get_popular_services(
        self,
        limit: int = Query(10, ge=1, le=50, description="Количество услуг в топе")
    ):
        try:
            popular_services = service_service.get_popular_services(limit)
            return popular_services
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении популярных услуг")


router = ServiceController().router