from fastapi import APIRouter, HTTPException,  Query, status
from typing import Any, List, Optional
from datetime import date

from app.models.payment import (
    RoomPayment, RoomPaymentCreate, RoomPaymentWithDetails,
    ServicePayment, ServicePaymentCreate, ServicePaymentWithDetails,
    PaymentStatus, PaymentSummary
)
from app.services.payment_service import payment_service



class PaymentController:
    def __init__(self):
        self.router = APIRouter()
        self.setup_routes()

    def setup_routes(self):
        self.router.add_api_route("/room", self.create_room_payment, methods=["POST"], response_model=RoomPayment)
        self.router.add_api_route("/room", self.get_room_payments, methods=["GET"], response_model=List[RoomPaymentWithDetails])
        self.router.add_api_route("/room/{payment_id}", self.get_room_payment, methods=["GET"], response_model=RoomPaymentWithDetails)
        self.router.add_api_route("/room/{payment_id}/status", self.update_room_payment_status, methods=["PATCH"], response_model=RoomPayment)
        
        self.router.add_api_route("/service", self.create_service_payment, methods=["POST"], response_model=ServicePayment)
        self.router.add_api_route("/service", self.get_service_payments, methods=["GET"], response_model=List[ServicePaymentWithDetails])
        self.router.add_api_route("/service/{payment_id}", self.get_service_payment, methods=["GET"], response_model=ServicePaymentWithDetails)
        self.router.add_api_route("/service/{payment_id}/status", self.update_service_payment_status, methods=["PATCH"], response_model=ServicePayment)
        
        self.router.add_api_route("/check-in/{check_in_id}/room-payments", self.get_room_payments_by_check_in, methods=["GET"], response_model=List[RoomPayment])
        self.router.add_api_route("/guest/{guest_id}/service-payments", self.get_service_payments_by_guest, methods=["GET"], response_model=List[ServicePayment])
        
        self.router.add_api_route("/summary", self.get_payment_summary, methods=["GET"], response_model=PaymentSummary)
        self.router.add_api_route("/revenue/rooms", self.get_revenue_by_room, methods=["GET"])

    async def create_room_payment(self, payment_data: RoomPaymentCreate) -> RoomPayment:
        try:
            payment = payment_service.create_room_payment(payment_data)
            return payment
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при создании платежа за номер")

    async def create_service_payment(self, payment_data: ServicePaymentCreate) -> ServicePayment:
        """
        Создание платежа за услугу.
        При оплате прочих услуг необходимо указывать: 
        дату оплаты, код клиента, вид услуги, размер оплаты.
        
        - **guest_id**: ID клиента
        - **service_id**: ID услуги
        - **amount**: Сумма платежа (если 0, то рассчитывается автоматически)
        - **quantity**: Количество услуг (по умолчанию 1)
        - **payment_method**: Способ оплаты
        - **status**: Статус платежа
        """
        try:
            payment = payment_service.create_service_payment(payment_data)
            # TODO: Добавить логирование действия
            return payment
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при создании платежа за услугу")

    async def get_room_payments(
        self,
        status_filter: Optional[PaymentStatus] = Query(None, alias="status", description="Фильтр по статусу платежа"),
        date_from: Optional[date] = Query(None, description="Фильтр от даты"),
        date_to: Optional[date] = Query(None, description="Фильтр до даты"),
        skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
        limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей")
    ) -> List[RoomPaymentWithDetails]:
        """
        Получение всех платежей за номера с фильтрацией.
        
        - **status**: Фильтр по статусу платежа
        - **date_from**: Фильтр от даты платежа
        - **date_to**: Фильтр до даты платежа
        - **skip**: Количество записей для пропуска (пагинация)
        - **limit**: Максимальное количество записей
        """
        try:
            payments = payment_service.get_all_room_payments(
                status=status_filter,
                date_from=date_from,
                date_to=date_to,
                skip=skip,
                limit=limit
            )
            return payments
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении платежей за номера")

    async def get_service_payments(
        self,
        status_filter: Optional[PaymentStatus] = Query(None, alias="status", description="Фильтр по статусу платежа"),
        date_from: Optional[date] = Query(None, description="Фильтр от даты"),
        date_to: Optional[date] = Query(None, description="Фильтр до даты"),
        skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
        limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей")
    ) -> List[ServicePaymentWithDetails]:
        """
        Получение всех платежей за услуги с фильтрацией.
        
        - **status**: Фильтр по статусу платежа
        - **date_from**: Фильтр от даты платежа
        - **date_to**: Фильтр до даты платежа
        - **skip**: Количество записей для пропуска (пагинация)
        - **limit**: Максимальное количество записей
        """
        try:
            payments = payment_service.get_all_service_payments(
                status=status_filter,
                date_from=date_from,
                date_to=date_to,
                skip=skip,
                limit=limit
            )
            return payments
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении платежей за услуги")

    async def get_room_payment(self, payment_id: int) -> RoomPaymentWithDetails:
        """
        Получение информации о платеже за номер.
        
        - **payment_id**: ID платежа
        """
        try:
            payment = payment_service.get_room_payment_with_details(payment_id)
            if not payment:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платеж не найден")
            return payment
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении данных платежа")

    async def get_service_payment(self, payment_id: int) -> ServicePaymentWithDetails:
        """
        Получение информации о платеже за услугу.
        
        - **payment_id**: ID платежа
        """
        try:
            payment = payment_service.get_service_payment_with_details(payment_id)
            if not payment:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платеж не найден")
            return payment
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении данных платежа")

    async def update_room_payment_status(self, payment_id: int, new_status: PaymentStatus) -> RoomPayment:
        """
        Обновление статуса платежа за номер.
        
        - **payment_id**: ID платежа
        - **new_status**: Новый статус платежа
        """
        try:
            payment = payment_service.update_room_payment_status(payment_id, new_status)
            if not payment:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платеж не найден")
            # TODO: Добавить логирование действия
            return payment
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при обновлении статуса платежа")

    async def update_service_payment_status(self, payment_id: int, new_status: PaymentStatus) -> ServicePayment:
        """
        Обновление статуса платежа за услугу.
        
        - **payment_id**: ID платежа
        - **new_status**: Новый статус платежа
        """
        try:
            payment = payment_service.update_service_payment_status(payment_id, new_status)
            if not payment:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Платеж не найден")
            # TODO: Добавить логирование действия
            return payment
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при обновлении статуса платежа")

    async def get_room_payments_by_check_in(self, check_in_id: int) -> List[RoomPayment]:
        """
        Получение всех платежей за номер для конкретного заселения.
        
        - **check_in_id**: ID заселения
        """
        try:
            payments = payment_service.get_room_payments_by_check_in(check_in_id)
            return payments
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении платежей за заселение")

    async def get_service_payments_by_guest(self, guest_id: int) -> List[ServicePayment]:
        """
        Получение всех платежей за услуги для конкретного гостя.
        
        - **guest_id**: ID гостя
        """
        try:
            payments = payment_service.get_service_payments_by_guest(guest_id)
            return payments
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении платежей гостя")

    async def get_payment_summary(
        self,
        date_from: Optional[date] = Query(None, description="Период от даты"),
        date_to: Optional[date] = Query(None, description="Период до даты")
    ) -> PaymentSummary:
        """
        Получение сводной статистики по платежам.
        
        - **date_from**: Период статистики от даты
        - **date_to**: Период статистики до даты
        
        Возвращает:
        - Общий доход от номеров и услуг
        - Количество платежей
        - Средние суммы платежей
        """
        try:
            summary = payment_service.get_payment_summary(date_from, date_to)
            return summary
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении сводки платежей")

    async def get_revenue_by_room(
        self,
        date_from: Optional[date] = Query(default=None, description="Период от даты"),
        date_to: Optional[date] = Query(default=None, description="Период до даты")
    ) -> List[dict[Any, Any]]:
        """
        Отчет по среднему доходу за номер.
        Показывает доход, который принесла отелю каждая комната за указанный временной интервал.
        
        - **date_from**: Период отчета от даты
        - **date_to**: Период отчета до даты
        
        Возвращает доходы по каждому номеру с количеством платежей и проданными днями.
        """
        try:
            revenue_data: List[dict[Any, Any]] = payment_service.get_revenue_by_room(date_from, date_to)
            return revenue_data
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Ошибка при получении отчета по доходам")


router = PaymentController().router