from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
import re

class GuestBase(BaseModel):
    passport_number: str = Field(..., max_length=12, description="Passport in format NNNN-NNNNNN")
    last_name: str = Field(..., max_length=100)
    first_name: str = Field(..., max_length=100)
    middle_name: str = Field(..., max_length=100)
    birth_year: int = Field(..., ge=1900, le=2024)
    gender: str = Field(..., max_length=1)
    registration_address: str
    phone: Optional[str] = Field(None, max_length=20)
    purpose_of_visit: Optional[str] = None
    how_heard_about_us: Optional[str] = None

    @validator('passport_number')
    def validate_passport_format(cls, v):
        pattern = r'^\d{4}-\d{6}$'
        if not re.match(pattern, v):
            raise ValueError('Passport number must be in format NNNN-NNNNNN')
        return v

    @validator('gender')
    def validate_gender(cls, v):
        if v.upper() not in ['М', 'Ж', 'M', 'F']:
            raise ValueError('Gender must be М/Ж or M/F')
        return v.upper()


class GuestCreate(GuestBase):
    pass


class GuestUpdate(BaseModel):
    passport_number: Optional[str] = Field(None, max_length=12)
    last_name: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    birth_year: Optional[int] = Field(None, ge=1900, le=2024)
    gender: Optional[str] = Field(None, max_length=1)
    registration_address: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    purpose_of_visit: Optional[str] = None
    how_heard_about_us: Optional[str] = None

    @validator('passport_number')
    def validate_passport_format(cls, v):
        if v is not None:
            pattern = r'^\d{4}-\d{6}$'
            if not re.match(pattern, v):
                raise ValueError('Passport number must be in format NNNN-NNNNNN')
        return v


class Guest(GuestBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GuestWithRoom(Guest):
    room_number: Optional[str] = None
    room_type: Optional[str] = None
    check_in_date: Optional[datetime] = None
    check_out_date: Optional[datetime] = None
    booking_status: Optional[str] = None


class GuestSearchResult(BaseModel):
    id: int
    passport_number: str
    last_name: str
    first_name: str
    middle_name: str
    phone: Optional[str]
    room_number: Optional[str]
    booking_status: Optional[str]
    check_in_date: Optional[datetime]
    check_out_date: Optional[datetime]

    class Config:
        from_attributes = True