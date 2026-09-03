import os
import json
import asyncio
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models import Program, Post, PostComment
from app.scrapers.gwangjin_lib import GwangjinLibScraper
from app.scrapers.gwangjin_care import GwangjinCareScraper
from app.scrapers.gwangjin_sports import GwangjinSportsScraper
from app.scrapers.seongdong_care import SeongdongCareScraper
from app.scrapers.familynet import FamilyNetScraper

logger = logging.getLogger(__name__)

def load_fallback_scraped_data() -> List[Dict[str, Any]]:
    json_path = os.path.join(os.path.dirname(__file__), "scraped_seed_data.json")
    if os.path.exists(json_path):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Fallback seed data load error: {e}")
    return []

# 100% 실제 지자체 공공기관 스크래핑 데이터만 사용 (임의 하드코딩 큐레이션 데이터 제거)
CURATED_OFFICIAL_DATA = []


async def sync_all_data(db: Session) -> dict:
    from app.database import create_tables
    create_tables()

    scrapers_config: List[Tuple[Any, str, str, str]] = [
        (GwangjinCareScraper(), "광진구육아종합지원센터", "광진구", "육아종합지원센터"),
        (GwangjinSportsScraper(), "광진구시설관리공단", "광진구", "구민체육센터"),
        (SeongdongCareScraper(), "성동구육아종합지원센터", "성동구", "육아종합지원센터"),
        (GwangjinLibScraper(), "광진정보도서관", "광진구", "구립도서관"),
        (FamilyNetScraper(), "가족센터", "광진구", "가족센터"),
    ]

    fallback_data = load_fallback_scraped_data()
    errors = []

    # 1. 스크래퍼 병렬 수집 (각 스크래퍼 최대 10초 대기)
    async def run_scraper(scraper, name, district, category):
        try:
            items = await asyncio.wait_for(scraper.scrape(), timeout=12.0)
            if items and len(items) > 0:
                return (scraper, name, district, category, items, None)
            else:
                return (scraper, name, district, category, None, f"{name}: 수집된 데이터 없음 (빈 결과)")
        except Exception as e:
            msg = f"{name} 수집 중 오류: {str(e)}"
            logger.warning(msg)
            return (scraper, name, district, category, None, msg)

    tasks = [run_scraper(s, n, d, c) for s, n, d, c in scrapers_config]
    scrape_results = await asyncio.gather(*tasks)

    # 2. 공식 큐레이션 데이터 항상 안전하게 동기화 (Upsert)
    curated_titles = {item["title"] for item in CURATED_OFFICIAL_DATA}
    db.query(Program).filter(Program.title.in_(curated_titles)).delete(synchronize_session=False)
    for item in CURATED_OFFICIAL_DATA:
        try:
            db.add(Program(**item))
        except Exception as e:
            errors.append(f"큐레이션 저장 오류 ({item.get('title')}): {str(e)}")

    added_titles = set(curated_titles)
    for p in db.query(Program).all():
        added_titles.add(p.title)

    # 3. 기관별 데이터 처리: 수집 성공 시 갱신, 수집 실패(해외 IP 차단/타임아웃) 시 기존 데이터 보존
    for scraper, name, district, category, items, err in scrape_results:
        if err:
            errors.append(err)

        # 기존 DB에 저장되어 있는 해당 기관/카테고리 데이터 조회
        existing_items = db.query(Program).filter(
            Program.category == category,
            Program.district.contains(district),
            ~Program.title.in_(curated_titles)
        ).all()

        if items and len(items) > 0:
            # 실시간 수집 성공: 기존 데이터 교체 및 최신화
            logger.info(f"[{name}] 실시간 수집 성공 ({len(items)}건) -> DB 갱신")
            for ex in existing_items:
                db.delete(ex)
                if ex.title in added_titles:
                    added_titles.discard(ex.title)
            for item in items:
                if item.get("title") not in added_titles:
                    try:
                        db.add(Program(**item))
                        added_titles.add(item.get("title"))
                    except Exception as e:
                        errors.append(f"DB 저장 오류 ({item.get('title')}): {str(e)}")
        else:
            # 실시간 수집 실패 (해외 IP 차단 또는 네트워크 오류)
            if existing_items and len(existing_items) > 0:
                # 기존 데이터가 이미 존재하므로 삭제하지 않고 안전하게 보존!
                logger.info(f"[{name}] 실시간 수집 불가/실패 -> 기존 DB 데이터({len(existing_items)}건) 보존 유지")
            else:
                # DB가 비어있는 최초 실행 상태인 경우 Fallback 시드 데이터 로드
                fb_items = [
                    fb for fb in fallback_data
                    if (fb.get("category") == category or district in fb.get("district", "")) and fb.get("title") not in added_titles
                ]
                logger.info(f"[{name}] DB 비어있음 -> Fallback 시드 데이터({len(fb_items)}건) 로드")
                for fb in fb_items:
                    if fb.get("title") not in added_titles:
                        try:
                            db.add(Program(**fb))
                            added_titles.add(fb.get("title"))
                        except Exception as e:
                            errors.append(f"시드 저장 오류 ({fb.get('title')}): {str(e)}")

    # 4. 최종 안전망: DB 프로그램 중 fallback_data에서 누락된 것이 있으면 보충
    for fb in fallback_data:
        if fb.get("title") not in added_titles:
            try:
                db.add(Program(**fb))
                added_titles.add(fb.get("title"))
            except Exception as e:
                logger.debug(f"Safety net seed load error: {e}")

    db.commit()
    seed_community_posts(db)

    total_programs = db.query(Program).count()
    open_programs = db.query(Program).filter(Program.status == "접수중").count()
    logger.info(f"동기화 완료: 총 {total_programs}건 (접수중 {open_programs}건)")

    return {
        "total_added": total_programs,
        "total_updated": 0,
        "total_programs": total_programs,
        "errors": errors
    }


def seed_community_posts(db: Session):
    if db.query(Post).count() > 0:
        return

    sample_posts = [
        {
            "category": "같이 가요",
            "district": "광진구",
            "target_age_group": "13~24개월",
            "title": "이번 주 목요일 꾸미팡팡 공동육아방(중곡점) 2회차 같이 가실 분 계신가요?",
            "content": "안녕하세요! 14개월 남아 키우는 중곡동 맘입니다 :)\n목요일 오후 1시 타임(2회차) 예약 성공했는데, 혼자 가기 심심해서 또래 아가랑 같이 놀고 육아 수다 나눌 분 구해요! 댓글 남겨주시거나 편하게 연락주세요~",
            "nickname": "중곡동하람맘",
            "password": "1234",
            "contact": "https://open.kakao.com/o/sample1",
            "status": "모집중",
            "comments": [
                {
                    "nickname": "군자동라온맘",
                    "password": "1234",
                    "content": "저도 15개월 여아 키워요! 2회차 예약해뒀는데 목요일에 봬요 ㅎㅎ"
                }
            ]
        },
        {
            "category": "같이 가요",
            "district": "성동구",
            "target_age_group": "0~12개월",
            "title": "성동구 보건소 모유수유 클리닉 다음 주 월요일 같이 가실 분 구해요",
            "content": "생후 4개월 완모 중인데 자세 교정받으러 보건소 가려고 합니다. 첫 방문이라 긴장되는데 혹시 같이 가실 성동구 초보맘 계실까요?",
            "nickname": "왕십리새댁",
            "password": "1234",
            "contact": None,
            "status": "모집중",
            "comments": []
        },
        {
            "category": "육아 수다",
            "district": "광진구",
            "target_age_group": "25~36개월",
            "title": "어린이대공원 아차산 숲체험 주차 및 유모차 코스 꿀팁 공유해요 🌳",
            "content": "지난 주말에 28개월 아이 데리고 숲체험 다녀왔는데, 정문 주차장보다 구의문 주차장이 잔디밭이랑 놀이터 접근성이 훨씬 좋더라구요! 유모차 끌고 가시는 분들은 구의문 쪽으로 진입하시면 계단 없이 평지로만 다닐 수 있습니다. 주말엔 10시 전 도착 추천드려요!",
            "nickname": "구의동아빠",
            "password": "1234",
            "contact": None,
            "status": "일반",
            "comments": [
                {
                    "nickname": "자양동도윤맘",
                    "password": "1234",
                    "content": "좋은 정보 감사합니다! 이번 주말에 꼭 가봐야겠네요."
                }
            ]
        },
        {
            "category": "나눔/드림",
            "district": "광진구",
            "target_age_group": "0~12개월",
            "title": "[드림] 아기 범보의자 + 식판 세트 깨끗한 것 나눔합니다 (자양동 직거래)",
            "content": "아이가 이제 커서 하이체어로 넘어가서 깨끗하게 세척/소독한 범보의자 무료 드림합니다. 자양역 근처 직거래 가능하신 분 댓글 남겨주세요!",
            "nickname": "자양맘",
            "password": "1234",
            "contact": "https://open.kakao.com/o/sample2",
            "status": "모집완료",
            "comments": [
                {
                    "nickname": "광진맘",
                    "password": "1234",
                    "content": "줄 서봅니다! 오늘 저녁에 바로 가지러 갈 수 있어요."
                }
            ]
        }
    ]

    for p_data in sample_posts:
        comments_data = p_data.pop("comments", [])
        post = Post(**p_data)
        db.add(post)
        db.commit()
        db.refresh(post)

        for c_data in comments_data:
            comment = PostComment(post_id=post.id, **c_data)
            db.add(comment)
        db.commit()

