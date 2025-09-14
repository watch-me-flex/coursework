from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., min_length=4, description="Пароль")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int 
    user_info: "UserInfo"


class UserInfo(BaseModel):
    id: int
    username: str
    full_name: str
    role_name: str
    permissions: list[str] = []

    class Config:
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Текущий пароль")
    new_password: str = Field(..., min_length=4, description="Новый пароль")


class CreateUserRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    password: str = Field(..., min_length=4, description="Пароль")
    full_name: str = Field(..., min_length=1, max_length=255, description="Полное имя")
    role_id: int = Field(..., description="ID роли пользователя")


class Permissions:
    READ_GUESTS = "read_guests"
    CREATE_GUEST = "create_guest"
    UPDATE_GUEST = "update_guest"
    DELETE_GUEST = "delete_guest"
    
    READ_ROOMS = "read_rooms"
    CREATE_ROOM = "create_room" 
    UPDATE_ROOM = "update_room"
    DELETE_ROOM = "delete_room"
    
    READ_CHECKINS = "read_checkins"
    CREATE_CHECKIN = "create_checkin"
    UPDATE_CHECKIN = "update_checkin"
    
    READ_PAYMENTS = "read_payments"
    CREATE_PAYMENT = "create_payment"
    UPDATE_PAYMENT = "update_payment"
    
    READ_SERVICES = "read_services"
    
    MANAGE_USERS = "manage_users"
    READ_ACTION_LOGS = "read_action_logs"
    FILTER_ACTION_LOGS = "filter_action_logs"
    EXPORT_ACTION_LOGS = "export_action_logs"
    
    GENERATE_REPORTS = "generate_reports"
    VIEW_STATISTICS = "view_statistics"
    MANAGE_SERVICES = "manage_services"


ROLE_PERMISSIONS = {
    "manager": [
        Permissions.READ_GUESTS, Permissions.CREATE_GUEST, Permissions.UPDATE_GUEST, Permissions.DELETE_GUEST,
        Permissions.READ_ROOMS, Permissions.CREATE_ROOM, Permissions.UPDATE_ROOM, Permissions.DELETE_ROOM,
        Permissions.READ_CHECKINS, Permissions.CREATE_CHECKIN, Permissions.UPDATE_CHECKIN,
        Permissions.READ_PAYMENTS, Permissions.CREATE_PAYMENT, Permissions.UPDATE_PAYMENT,
        Permissions.READ_SERVICES,
    ],
    "admin": [
        Permissions.READ_GUESTS, Permissions.CREATE_GUEST, Permissions.UPDATE_GUEST, Permissions.DELETE_GUEST,
        Permissions.READ_ROOMS, Permissions.CREATE_ROOM, Permissions.UPDATE_ROOM, Permissions.DELETE_ROOM,
        Permissions.READ_CHECKINS, Permissions.CREATE_CHECKIN, Permissions.UPDATE_CHECKIN,
        Permissions.READ_PAYMENTS, Permissions.CREATE_PAYMENT, Permissions.UPDATE_PAYMENT,
        Permissions.READ_SERVICES,
        Permissions.MANAGE_USERS,
        Permissions.READ_ACTION_LOGS, Permissions.FILTER_ACTION_LOGS, Permissions.EXPORT_ACTION_LOGS,
    ],
    "owner": [
        Permissions.READ_GUESTS, Permissions.CREATE_GUEST, Permissions.UPDATE_GUEST, Permissions.DELETE_GUEST,
        Permissions.READ_ROOMS, Permissions.CREATE_ROOM, Permissions.UPDATE_ROOM, Permissions.DELETE_ROOM,
        Permissions.READ_CHECKINS, Permissions.CREATE_CHECKIN, Permissions.UPDATE_CHECKIN,
        Permissions.READ_PAYMENTS, Permissions.CREATE_PAYMENT, Permissions.UPDATE_PAYMENT,
        Permissions.READ_SERVICES,
        Permissions.MANAGE_USERS,
        Permissions.READ_ACTION_LOGS, Permissions.FILTER_ACTION_LOGS, Permissions.EXPORT_ACTION_LOGS,
        Permissions.GENERATE_REPORTS, Permissions.VIEW_STATISTICS, Permissions.MANAGE_SERVICES,
    ],
    "Менеджер": [
        Permissions.READ_GUESTS, Permissions.CREATE_GUEST, Permissions.UPDATE_GUEST, Permissions.DELETE_GUEST,
        Permissions.READ_ROOMS, Permissions.CREATE_ROOM, Permissions.UPDATE_ROOM, Permissions.DELETE_ROOM,
        Permissions.READ_CHECKINS, Permissions.CREATE_CHECKIN, Permissions.UPDATE_CHECKIN,
        Permissions.READ_PAYMENTS, Permissions.CREATE_PAYMENT, Permissions.UPDATE_PAYMENT,
        Permissions.READ_SERVICES,
    ],
    "Администратор": [
        Permissions.READ_GUESTS, Permissions.CREATE_GUEST, Permissions.UPDATE_GUEST, Permissions.DELETE_GUEST,
        Permissions.READ_ROOMS, Permissions.CREATE_ROOM, Permissions.UPDATE_ROOM, Permissions.DELETE_ROOM,
        Permissions.READ_CHECKINS, Permissions.CREATE_CHECKIN, Permissions.UPDATE_CHECKIN,
        Permissions.READ_PAYMENTS, Permissions.CREATE_PAYMENT, Permissions.UPDATE_PAYMENT,
        Permissions.READ_SERVICES,
        Permissions.MANAGE_USERS,
        Permissions.READ_ACTION_LOGS, Permissions.FILTER_ACTION_LOGS, Permissions.EXPORT_ACTION_LOGS,
    ],
    "Директор": [
        Permissions.READ_GUESTS, Permissions.CREATE_GUEST, Permissions.UPDATE_GUEST, Permissions.DELETE_GUEST,
        Permissions.READ_ROOMS, Permissions.CREATE_ROOM, Permissions.UPDATE_ROOM, Permissions.DELETE_ROOM,
        Permissions.READ_CHECKINS, Permissions.CREATE_CHECKIN, Permissions.UPDATE_CHECKIN,
        Permissions.READ_PAYMENTS, Permissions.CREATE_PAYMENT, Permissions.UPDATE_PAYMENT,
        Permissions.READ_SERVICES,
        Permissions.MANAGE_USERS,
        Permissions.READ_ACTION_LOGS, Permissions.FILTER_ACTION_LOGS, Permissions.EXPORT_ACTION_LOGS,
        Permissions.GENERATE_REPORTS, Permissions.VIEW_STATISTICS, Permissions.MANAGE_SERVICES,
    ]
}