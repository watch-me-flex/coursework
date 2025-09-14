from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
from decimal import Decimal
import re

class RoomTypeBase(BaseModel):
    code: str = Field(..., max_length=1, description="Type code: Л-Люкс, П-Полулюкс, О-Одноместный, М-Многоместный")
    name: str = Field(..., max_length=50)
    description: Optional[str] = None

    @validator('code')
    def validate_room_type_code(cls, v):
        if v.upper() not in ['Л', 'П', 'О', 'М', 'L', 'P', 'S', 'M']:
            raise ValueError('Room type code must be Л, П, О, М')
        return v.upper()


class RoomType(RoomTypeBase):
    id: int

    class Config:
        from_attributes = True


class RoomBase(BaseModel):
    room_number: str = Field(..., max_length=4, description="Room number in format ANNN")
    type_id: int
    capacity: int = Field(..., ge=1, le=10)
    room_count: int = Field(..., ge=1, le=5)
    price_per_night: Decimal = Field(..., ge=0)
    has_bathroom: bool
    equipment: Optional[str] = None
    is_available: bool = True

    @validator('room_number')
    def validate_room_number_format(cls, v):
        pattern = r'^[ЛПОМLPSM]\d{3}$'
        if not re.match(pattern, v.upper()):
            raise ValueError('Room number must be in format ANNN where A is type code')
        return v.upper()


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    room_number: Optional[str] = Field(None, max_length=4)
    type_id: Optional[int] = None
    capacity: Optional[int] = Field(None, ge=1, le=10)
    room_count: Optional[int] = Field(None, ge=1, le=5)
    price_per_night: Optional[Decimal] = Field(None, ge=0)
    has_bathroom: Optional[bool] = None
    equipment: Optional[str] = None
    is_available: Optional[bool] = None

    @validator('room_number')
    def validate_room_number_format(cls, v):
        if v is not None:
            pattern = r'^[ЛПОМLPSM]\d{3}$'
            if not re.match(pattern, v.upper()):
                raise ValueError('Room number must be in format ANNN where A is type code')
        return v.upper() if v else v


class Room(RoomBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RoomWithType(Room):
    type_code: Optional[str] = None
    type_name: Optional[str] = None
    type_description: Optional[str] = None


class RoomAvailability(BaseModel):
    room_id: int
    room_number: str
    type_name: str
    capacity: int
    price_per_night: Decimal
    is_available: bool
    current_guest_count: int = 0

    class Config:
        from_attributes = True