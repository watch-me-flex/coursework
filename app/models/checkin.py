from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, validator
from enum import Enum


class CheckInStatus(str, Enum):
    ACTIVE = "Активно"
    COMPLETED = "Завершено"
    CANCELLED = "Отменено"


class CheckInBase(BaseModel):
    guest_id: int
    room_id: int
    check_in_date: date
    check_out_date: Optional[date] = None
    status: CheckInStatus = CheckInStatus.ACTIVE

    @validator('check_out_date')
    def validate_checkout_after_checkin(cls, v, values):
        if v and 'check_in_date' in values and v <= values['check_in_date']:
            raise ValueError('Check-out date must be after check-in date')
        return v


class CheckInCreate(CheckInBase):
    pass


class CheckInUpdate(BaseModel):
    guest_id: Optional[int] = None
    room_id: Optional[int] = None
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    status: Optional[CheckInStatus] = None

    @validator('check_out_date')
    def validate_checkout_after_checkin(cls, v, values):
        if v and 'check_in_date' in values and values['check_in_date'] and v <= values['check_in_date']:
            raise ValueError('Check-out date must be after check-in date')
        return v


class CheckIn(CheckInBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CheckInWithDetails(CheckIn):
    guest_passport: Optional[str] = None
    guest_full_name: Optional[str] = None
    room_number: Optional[str] = None
    room_type: Optional[str] = None
    price_per_night: Optional[float] = None


class CheckOutRequest(BaseModel):
    check_in_id: int
    check_out_date: date = Field(default_factory=date.today)

    @validator('check_out_date')
    def validate_checkout_date_not_future(cls, v):
        if v > date.today():
            raise ValueError('Check-out date cannot be in the future')
        return v


class CurrentGuestView(BaseModel):
    id: int
    passport_number: str
    full_name: str
    room_number: str
    room_type: str
    price_per_night: float
    check_in_date: date
    check_out_date: Optional[date]
    previous_stays: int

    class Config:
        from_attributes = True