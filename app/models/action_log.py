from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ActionType(str, Enum):
    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    CHECK_IN = "CHECK_IN"
    CHECK_OUT = "CHECK_OUT"
    PAYMENT = "PAYMENT"
    REPORT_GENERATE = "REPORT_GENERATE"


class ActionLogBase(BaseModel):
    user_id: Optional[int] = None
    action_type: ActionType
    table_name: Optional[str] = Field(None, max_length=50)
    record_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None


class ActionLogCreate(ActionLogBase):
    pass


class ActionLog(ActionLogBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ActionLogWithUser(ActionLog):
    username: Optional[str] = None
    user_full_name: Optional[str] = None
    user_role: Optional[str] = None


class ActionLogFilter(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    action_type: Optional[ActionType] = None
    table_name: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ActionLogSummary(BaseModel):
    user_id: int
    username: str
    user_full_name: str
    total_actions: int
    actions_by_type: Dict[str, int]
    last_action_date: datetime

    class Config:
        from_attributes = True