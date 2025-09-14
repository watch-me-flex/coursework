from typing import Optional, List
from pydantic import BaseModel, Field


class PermissionBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None


class Permission(PermissionBase):
    id: int

    class Config:
        from_attributes = True


class RolePermissionBase(BaseModel):
    role_id: int
    permission_id: int


class RolePermissionCreate(RolePermissionBase):
    pass


class RolePermission(RolePermissionBase):
    class Config:
        from_attributes = True


class RoleWithPermissions(BaseModel):
    id: int
    name: str
    description: Optional[str]
    permissions: List[Permission] = []

    class Config:
        from_attributes = True


class UserWithRole(BaseModel):
    id: int
    username: str
    full_name: str
    role: RoleWithPermissions
    permissions: List[str] = [] 

    class Config:
        from_attributes = True