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


# ==========================================
# 커뮤니티 (Post / Comment) Schemas
# ==========================================
class PostCreate(BaseModel):
    category: str = "같이 가요"
    district: str = "전체"
    target_age_group: str = "전체"
    program_id: Optional[int] = None
    program_title: Optional[str] = None
    title: str
    content: str
    nickname: str
    password: str
    contact: Optional[str] = None

class PostCommentResponse(BaseModel):
    id: int
    post_id: int
    nickname: str
    content: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PostResponse(BaseModel):
    id: int
    category: str
    district: str
    target_age_group: str
    program_id: Optional[int] = None
    program_title: Optional[str] = None
    title: str
    content: str
    nickname: str
    contact: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None
    comments_count: int = 0
    comments: list[PostCommentResponse] = []

    class Config:
        from_attributes = True

class PostCommentCreate(BaseModel):
    nickname: str
    password: str
    content: str

class PostDelete(BaseModel):
    password: str

class PostStatusUpdate(BaseModel):
    password: str
    status: str


