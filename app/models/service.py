from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from decimal import Decimal
from enum import Enum

class ServiceTypeName(str, Enum):
    RESTAURANT = "Ресторан"
    GYM = "Спортивные тренажеры" 
    ENTERTAINMENT = "Досуг"
    SPA = "Спа"
    LAUNDRY = "Прачечная"
    PARKING = "Парковка"
    TRANSFER = "Трансфер"
    OTHER = "Прочее"


class ServiceTypeBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class ServiceTypeCreate(ServiceTypeBase):
    pass

class ServiceTypeUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class ServiceType(ServiceTypeBase):
    id: int

    class Config:
        from_attributes = True


class ServiceBase(BaseModel):
    type_id: int
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    is_available: bool = True


class ServiceCreate(ServiceBase):
    pass


class ServiceUpdate(BaseModel):
    type_id: Optional[int] = None
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    is_available: Optional[bool] = None


class Service(ServiceBase):
    id: int

    class Config:
        from_attributes = True


class ServiceWithType(Service):
    type_name: Optional[str] = None
    type_description: Optional[str] = None


class ServiceUsageStats(BaseModel):
    service_id: int
    service_name: str
    service_type: str
    total_revenue: Decimal
    usage_count: int
    average_order_value: Decimal

    class Config:
        from_attributes = True


class ServiceRevenueReport(BaseModel):
    service_type: str
    total_revenue: Decimal
    orders_count: int
    percentage_of_total: float

    class Config:
        from_attributes = True