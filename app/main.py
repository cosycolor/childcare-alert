import os
import logging
from contextlib import asynccontextmanager
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import engine, Base, get_db, SessionLocal
from app.models import Program
from app.schemas import ProgramResponse, SyncResult
from app.scrapers.seed_data import sync_all_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("childcare_service")

# DB 테이블 생성
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: 초기 DB 데이터 동기화
    db = SessionLocal()
    try:
        count = db.query(Program).count()
        if count == 0:
            logger.info("Database is empty. Initializing with scraper & seed data...")
            await sync_all_data(db)
            logger.info(f"Initialized with {db.query(Program).count()} programs.")
        
        # 커뮤니티 초기 글 동기화
        from app.scrapers.seed_data import seed_community_posts
        seed_community_posts(db)
    finally:
        db.close()
    yield

app = FastAPI(
    title="육아 프로그램 통합 알림 서비스",
    description="0~36개월 영유아 부모를 위한 지자체 육아 프로그램 큐레이션 플랫폼",
    version="1.0.0",
    lifespan=lifespan
)

# 정적 파일 및 템플릿 디렉터리 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")
template_dir = os.path.join(BASE_DIR, "templates")

os.makedirs(static_dir, exist_ok=True)
os.makedirs(os.path.join(static_dir, "css"), exist_ok=True)
os.makedirs(os.path.join(static_dir, "js"), exist_ok=True)
os.makedirs(template_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")
templates = Jinja2Templates(directory=template_dir)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/programs", response_model=List[ProgramResponse])
def get_programs(
    district: Optional[str] = Query(None, description="자치구 (광진구, 성동구 등)"),
    category: Optional[str] = Query(None, description="기관 카테고리 (육아종합지원센터, 구립도서관 등)"),
    age_group: Optional[str] = Query(None, description="대상 연령 (0~12개월, 13~24개월, 25~36개월)"),
    status: Optional[str] = Query(None, description="접수 상태 (접수예정, 접수중, 마감 등)"),
    q: Optional[str] = Query(None, description="검색어 (행사명, 기관명, 내용)"),
    db: Session = Depends(get_db)
):
    query = db.query(Program)

    if district and district != "전체":
        query = query.filter(or_(Program.district == district, Program.district.contains(district)))
    
    if category and category != "전체":
        query = query.filter(Program.category == category)
        
    if age_group and age_group != "전체":
        query = query.filter(or_(
            Program.target_age_group == age_group,
            Program.target_age_group.contains("공통"),
            Program.target_desc.contains(age_group.replace("개월", ""))
        ))
        
    if status and status != "전체":
        query = query.filter(Program.status == status)
        
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Program.title.like(search),
                Program.institution_name.like(search),
                Program.target_desc.like(search),
                Program.location.like(search)
            )
        )
        
    # 상태별 우선순위 정렬: 접수중(1) -> 접수예정(2) -> 대기접수(3) -> 마감(4) -> 종료(5)
    programs = query.all()
    status_order = {"접수중": 1, "접수예정": 2, "대기접수": 3, "마감": 4, "종료": 5}
    programs.sort(key=lambda p: (status_order.get(p.status, 99), p.apply_start_at or "9999-99-99"))
    
    return programs

@app.get("/api/programs/{program_id}", response_model=ProgramResponse)
def get_program_detail(program_id: int, db: Session = Depends(get_db)):
    prog = db.query(Program).filter(Program.id == program_id).first()
    if not prog:
        raise HTTPException(status_code=404, detail="Program not found")
    return prog

@app.get("/api/stats")
def get_stats(db: Session = Depends(get_db)):
    total = db.query(Program).count()
    open_count = db.query(Program).filter(Program.status == "접수중").count()
    upcoming_count = db.query(Program).filter(Program.status == "접수예정").count()
    gwangjin_count = db.query(Program).filter(Program.district.contains("광진구")).count()
    seongdong_count = db.query(Program).filter(Program.district.contains("성동구")).count()
    
    return {
        "total": total,
        "open": open_count,
        "upcoming": upcoming_count,
        "gwangjin": gwangjin_count,
        "seongdong": seongdong_count
    }

@app.post("/api/sync", response_model=SyncResult)
async def sync_data(db: Session = Depends(get_db)):
    res = await sync_all_data(db)
    return {
        "total_added": res["total_added"],
        "total_updated": res["total_updated"],
        "errors": res["errors"],
        "message": f"동기화 완료: {res['total_programs']}개 프로그램 등록/갱신됨"
    }

# ==========================================
# 후기 / 꿀팁 댓글 API (독립 모듈)
# ==========================================
from app.models import Review
from app.schemas import ReviewCreate, ReviewResponse, ReviewDelete

@app.get("/api/programs/{program_id}/reviews", response_model=list[ReviewResponse])
def get_program_reviews(program_id: int, db: Session = Depends(get_db)):
    return db.query(Review).filter(Review.program_id == program_id).order_by(Review.created_at.desc()).all()

@app.post("/api/programs/{program_id}/reviews", response_model=ReviewResponse)
def create_program_review(program_id: int, review_in: ReviewCreate, db: Session = Depends(get_db)):
    # 프로그램 존재 여부 확인
    prog = db.query(Program).filter(Program.id == program_id).first()
    if not prog:
        raise HTTPException(status_code=404, detail="Program not found")
    
    if not review_in.nickname.strip() or not review_in.content.strip():
        raise HTTPException(status_code=400, detail="닉네임과 내용을 입력해주세요.")

    new_review = Review(
        program_id=program_id,
        nickname=review_in.nickname.strip()[:20],
        password=review_in.password.strip(),
        content=review_in.content.strip()
    )
    db.add(new_review)
    db.commit()
    db.refresh(new_review)
    return new_review

@app.post("/api/reviews/{review_id}/delete")
def delete_program_review(review_id: int, delete_in: ReviewDelete, db: Session = Depends(get_db)):
    review = db.query(Review).filter(Review.id == review_id).first()
    if not review:
        raise HTTPException(status_code=404, detail="후기를 찾을 수 없습니다.")
    
    if review.password != delete_in.password.strip():
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    
    db.delete(review)
    db.commit()
    return {"status": "success", "message": "삭제되었습니다."}


# ==========================================
# 커뮤니티 (동행 모집 & 육아 수다) API
# ==========================================
from app.models import Post, PostComment
from app.schemas import (
    PostCreate, PostResponse, PostDelete, PostStatusUpdate,
    PostCommentCreate, PostCommentResponse
)

@app.get("/api/posts", response_model=List[PostResponse])
def get_posts(
    category: Optional[str] = Query(None, description="카테고리 (같이 가요, 육아 수다, 나눔/드림)"),
    district: Optional[str] = Query(None, description="지역 (광진구, 성동구 등)"),
    age_group: Optional[str] = Query(None, description="월령 (0~12개월 등)"),
    status: Optional[str] = Query(None, description="모집 상태 (모집중, 모집완료)"),
    q: Optional[str] = Query(None, description="검색어"),
    db: Session = Depends(get_db)
):
    query = db.query(Post)

    if category and category != "전체":
        query = query.filter(Post.category == category)
    if district and district != "전체":
        query = query.filter(or_(Post.district == district, Post.district == "전체"))
    if age_group and age_group != "전체":
        query = query.filter(or_(Post.target_age_group == age_group, Post.target_age_group == "전체"))
    if status and status != "전체":
        query = query.filter(Post.status == status)
    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Post.title.like(search),
                Post.content.like(search),
                Post.program_title.like(search),
                Post.nickname.like(search)
            )
        )

    posts = query.order_by(Post.created_at.desc()).all()
    
    # 댓글 수 및 댓글 리스트 채우기
    result = []
    for p in posts:
        comments = db.query(PostComment).filter(PostComment.post_id == p.id).order_by(PostComment.created_at.asc()).all()
        post_dict = {
            "id": p.id,
            "category": p.category,
            "district": p.district,
            "target_age_group": p.target_age_group,
            "program_id": p.program_id,
            "program_title": p.program_title,
            "title": p.title,
            "content": p.content,
            "nickname": p.nickname,
            "contact": p.contact,
            "status": p.status,
            "created_at": p.created_at,
            "comments_count": len(comments),
            "comments": comments
        }
        result.append(post_dict)
    
    return result


@app.post("/api/posts", response_model=PostResponse)
def create_post(post_in: PostCreate, db: Session = Depends(get_db)):
    if not post_in.title.strip() or not post_in.content.strip() or not post_in.nickname.strip():
        raise HTTPException(status_code=400, detail="제목, 내용, 닉네임은 필수입니다.")
    if not post_in.password.strip():
        raise HTTPException(status_code=400, detail="삭제용 비밀번호를 입력해주세요.")

    new_post = Post(
        category=post_in.category or "같이 가요",
        district=post_in.district or "전체",
        target_age_group=post_in.target_age_group or "전체",
        program_id=post_in.program_id,
        program_title=post_in.program_title,
        title=post_in.title.strip()[:255],
        content=post_in.content.strip(),
        nickname=post_in.nickname.strip()[:50],
        password=post_in.password.strip(),
        contact=post_in.contact.strip() if post_in.contact else None,
        status="모집중" if post_in.category == "같이 가요" else "일반"
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    
    return {
        "id": new_post.id,
        "category": new_post.category,
        "district": new_post.district,
        "target_age_group": new_post.target_age_group,
        "program_id": new_post.program_id,
        "program_title": new_post.program_title,
        "title": new_post.title,
        "content": new_post.content,
        "nickname": new_post.nickname,
        "contact": new_post.contact,
        "status": new_post.status,
        "created_at": new_post.created_at,
        "comments_count": 0,
        "comments": []
    }


@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post_detail(post_id: int, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    
    comments = db.query(PostComment).filter(PostComment.post_id == post.id).order_by(PostComment.created_at.asc()).all()
    return {
        "id": post.id,
        "category": post.category,
        "district": post.district,
        "target_age_group": post.target_age_group,
        "program_id": post.program_id,
        "program_title": post.program_title,
        "title": post.title,
        "content": post.content,
        "nickname": post.nickname,
        "contact": post.contact,
        "status": post.status,
        "created_at": post.created_at,
        "comments_count": len(comments),
        "comments": comments
    }


@app.post("/api/posts/{post_id}/status")
def update_post_status(post_id: int, status_in: PostStatusUpdate, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.password != status_in.password.strip():
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    
    post.status = status_in.status
    db.commit()
    return {"status": "success", "new_status": post.status}


@app.post("/api/posts/{post_id}/delete")
def delete_post(post_id: int, delete_in: PostDelete, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if post.password != delete_in.password.strip():
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    
    # 댓글 함께 삭제
    db.query(PostComment).filter(PostComment.post_id == post_id).delete()
    db.delete(post)
    db.commit()
    return {"status": "success", "message": "게시글이 삭제되었습니다."}


@app.post("/api/posts/{post_id}/comments", response_model=PostCommentResponse)
def create_post_comment(post_id: int, comment_in: PostCommentCreate, db: Session = Depends(get_db)):
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="게시글을 찾을 수 없습니다.")
    if not comment_in.nickname.strip() or not comment_in.content.strip():
        raise HTTPException(status_code=400, detail="닉네임과 내용을 입력해주세요.")
    if not comment_in.password.strip():
        raise HTTPException(status_code=400, detail="비밀번호를 입력해주세요.")
    
    comment = PostComment(
        post_id=post_id,
        nickname=comment_in.nickname.strip()[:50],
        password=comment_in.password.strip(),
        content=comment_in.content.strip()
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@app.post("/api/comments/{comment_id}/delete")
def delete_post_comment(comment_id: int, delete_in: PostDelete, db: Session = Depends(get_db)):
    comment = db.query(PostComment).filter(PostComment.id == comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="댓글을 찾을 수 없습니다.")
    if comment.password != delete_in.password.strip():
        raise HTTPException(status_code=403, detail="비밀번호가 일치하지 않습니다.")
    
    db.delete(comment)
    db.commit()
    return {"status": "success", "message": "댓글이 삭제되었습니다."}


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "childcare-program-notifier"}


