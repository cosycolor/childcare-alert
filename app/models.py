import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from app.database import Base

class Program(Base):
    __tablename__ = "programs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    institution_name = Column(String(100), nullable=False, index=True)   # 예: 광진구육아종합지원센터
    district = Column(String(50), nullable=False, index=True)           # 예: 광진구, 성동구
    category = Column(String(50), nullable=False, index=True)           # 예: 육아종합지원센터, 구립도서관, 가족센터
    title = Column(String(255), nullable=False, index=True)             # 행사/프로그램명
    
    target_age_group = Column(String(50), nullable=True, index=True)    # 0~12개월, 13~24개월, 25~36개월, 0~36개월 공통
    target_desc = Column(String(255), nullable=True)                    # 상세 대상 설명 (예: 12~24개월 영유아 및 부모)
    
    apply_start_at = Column(String(50), nullable=True, index=True)      # 신청 시작일시 (YYYY-MM-DD HH:MM 또는 YYYY-MM-DD)
    apply_end_at = Column(String(50), nullable=True)                    # 신청 종료일시
    event_date_desc = Column(String(255), nullable=True)                # 행사 진행일시/기간
    
    capacity_info = Column(String(100), nullable=True)                  # 정원/접수인원 (예: 10쌍 / 마감)
    fee = Column(String(50), default="무료")                            # 비용 (무료, 유료 등)
    location = Column(String(200), nullable=True)                       # 장소
    
    status = Column(String(50), nullable=False, default="접수예정", index=True) # 접수예정, 접수중, 대기접수, 마감, 종료
    
    detail_type = Column(String(50), default="TABLE_TEXT")              # POSTER_IMAGE, TABLE_TEXT, HYBRID
    image_url = Column(Text, nullable=True)                             # 포스터 이미지 URL
    detail_content = Column(Text, nullable=True)                        # 상세 설명 또는 JSON 구조화 데이터
    
    origin_url = Column(Text, nullable=False)                           # 원본 신청/상세 페이지 URL
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    program_id = Column(Integer, nullable=False, index=True)
    nickname = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False) # 삭제용 4자리 비밀번호
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(50), nullable=False, default="같이 가요", index=True)  # 같이 가요, 육아 수다, 나눔/드림
    district = Column(String(50), nullable=False, default="전체", index=True)        # 광진구, 성동구, 전체
    target_age_group = Column(String(50), nullable=False, default="전체", index=True)# 0~12개월, 13~24개월, 25~36개월, 전체
    program_id = Column(Integer, nullable=True, index=True)                          # 연계된 프로그램 ID (선택)
    program_title = Column(String(255), nullable=True)                              # 연계된 프로그램명 (선택)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    nickname = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False)                                   # 삭제용 4자리 비밀번호
    contact = Column(String(255), nullable=True)                                    # 오픈카톡 링크 or 연락처
    status = Column(String(50), nullable=False, default="모집중", index=True)       # 모집중, 모집완료, 일반
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class PostComment(Base):
    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    post_id = Column(Integer, nullable=False, index=True)
    nickname = Column(String(50), nullable=False)
    password = Column(String(50), nullable=False)                                   # 삭제용 4자리 비밀번호
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


