from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class ProgramBase(BaseModel):
    institution_name: str
    district: str
    category: str
    title: str
    target_age_group: Optional[str] = "0~36개월 공통"
    target_desc: Optional[str] = None
    apply_start_at: Optional[str] = None
    apply_end_at: Optional[str] = None
    event_date_desc: Optional[str] = None
    capacity_info: Optional[str] = None
    fee: Optional[str] = "무료"
    location: Optional[str] = None
    status: str = "접수예정"
    detail_type: str = "TABLE_TEXT"
    image_url: Optional[str] = None
    detail_content: Optional[str] = None
    origin_url: str

class ProgramCreate(ProgramBase):
    pass

class ProgramResponse(ProgramBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class SyncResult(BaseModel):
    total_added: int
    total_updated: int
    errors: list[str] = []
    message: str

class ReviewCreate(BaseModel):
    nickname: str
    password: str
    content: str

class ReviewResponse(BaseModel):
    id: int
    program_id: int
    nickname: str
    content: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ReviewDelete(BaseModel):
    password: str

