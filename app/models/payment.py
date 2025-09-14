from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from enum import Enum


class PaymentStatus(str, Enum):
    PAID = "Оплачено"
    PENDING = "Ожидает оплаты"
    CANCELLED = "Отменено"
    REFUNDED = "Возвращено"


class PaymentMethod(str, Enum):
    CASH = "Наличные"
    CARD = "Карта"
    TRANSFER = "Перевод"
    ONLINE = "Онлайн"


class RoomPaymentBase(BaseModel):
    check_in_id: int
    days_count: int = Field(..., ge=1)
    amount: Decimal = Field(..., ge=0)
    payment_method: PaymentMethod
    status: PaymentStatus = PaymentStatus.PENDING


class RoomPaymentCreate(RoomPaymentBase):
    pass


class RoomPaymentUpdate(BaseModel):
    check_in_id: Optional[int] = None
    days_count: Optional[int] = Field(None, ge=1)
    amount: Optional[Decimal] = Field(None, ge=0)
    payment_method: Optional[PaymentMethod] = None
    status: Optional[PaymentStatus] = None


class RoomPayment(RoomPaymentBase):
    id: int
    payment_date: datetime

    class Config:
        from_attributes = True


class RoomPaymentWithDetails(RoomPayment):
    guest_passport: Optional[str] = None
    guest_full_name: Optional[str] = None
    room_number: Optional[str] = None
    check_in_date: Optional[datetime] = None
    check_out_date: Optional[datetime] = None



class ServicePaymentBase(BaseModel):
    guest_id: int
    service_id: int
    amount: Decimal = Field(..., ge=0)
    quantity: int = Field(default=1, ge=1)
    payment_method: PaymentMethod
    status: PaymentStatus = PaymentStatus.PENDING
    service_type: Optional[ServiceTypeName] = None

    # @validator('service_type')
    # def validate_service_type(cls, v, values):
    #     if v is None and 'service_id' in values:
    #         pass
    #     return v


class ServicePaymentCreate(ServicePaymentBase):
    pass


class ServicePaymentUpdate(BaseModel):
    guest_id: Optional[int] = None
    service_id: Optional[int] = None
    amount: Optional[Decimal] = Field(None, ge=0)
    quantity: Optional[int] = Field(None, ge=1)
    payment_method: Optional[PaymentMethod] = None
    status: Optional[PaymentStatus] = None


class ServicePayment(ServicePaymentBase):
    id: int
    payment_date: datetime

    class Config:
        from_attributes = True


class ServicePaymentWithDetails(ServicePayment):
    guest_passport: Optional[str] = None
    guest_full_name: Optional[str] = None
    service_name: Optional[str] = None
    service_type: Optional[str] = None


class PaymentSummary(BaseModel):
    total_room_revenue: Decimal
    total_service_revenue: Decimal
    total_revenue: Decimal
    room_payments_count: int
    service_payments_count: int
    average_room_payment: Decimal
    average_service_payment: Decimal

    class Config:
        from_attributes = True