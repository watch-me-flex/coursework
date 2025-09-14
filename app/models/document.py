from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from enum import Enum


class DocumentType(str, Enum):
    PASSPORT_SCAN = "passport_scan"
    ID_CARD = "id_card"
    VISA = "visa"
    DRIVER_LICENSE = "driver_license"
    OTHER = "other"


class GuestDocumentBase(BaseModel):
    guest_id: int
    document_type: DocumentType
    file_url: str
    file_name: str = Field(..., max_length=255)
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)


class GuestDocumentCreate(GuestDocumentBase):
    pass


class GuestDocumentUpdate(BaseModel):
    guest_id: Optional[int] = None
    document_type: Optional[DocumentType] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = Field(None, max_length=255)
    file_size: Optional[int] = None
    mime_type: Optional[str] = Field(None, max_length=100)


class GuestDocument(GuestDocumentBase):
    id: int
    upload_date: datetime

    class Config:
        from_attributes = True


class GuestDocumentWithDetails(GuestDocument):
    guest_passport: Optional[str] = None
    guest_name: Optional[str] = None


class DocumentUploadRequest(BaseModel):
    guest_id: int
    document_type: DocumentType = DocumentType.PASSPORT_SCAN


class DocumentUploadResponse(BaseModel):
    document_id: int
    file_url: str
    upload_date: datetime
    message: str = "Document uploaded successfully"

    class Config:
        from_attributes = True