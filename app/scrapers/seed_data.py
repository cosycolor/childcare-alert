import json
import logging
from sqlalchemy.orm import Session
from app.models import Program
from app.scrapers.gwangjin_lib import GwangjinLibScraper
from app.scrapers.gwangjin_care import GwangjinCareScraper
from app.scrapers.seongdong_care import SeongdongCareScraper
from app.scrapers.familynet import FamilyNetScraper

logger = logging.getLogger(__name__)

# 실제 지자체 연계 공공/민간 프로그램 및 예약 데이터 (키즈카페, 놀이터, 보건소, 숲체험, 백화점/마트 문센, 북스타트, 시간제보육)
CURATED_OFFICIAL_DATA = [
    # 1. 공공놀이터 / 서울형 키즈카페
    {
        "institution_name": "광진구육아종합지원센터 (꾸미팡팡)",
        "district": "광진구",
        "category": "공공놀이터/키즈카페",
        "title": "[공공놀이터] 광진구 꾸미팡팡놀이터(군자/자양) 영유아 실내놀이실 정기 예약",
        "target_age_group": "0~36개월 공통",
        "target_desc": "광진구 거주 0~36개월 영유아 및 보호자 (만 5세 이하)",
        "apply_start_at": "매주 화요일 09:00",
        "apply_end_at": "이용 당일 1시간 전까지",
        "event_date_desc": "화~토 (1회차 10:00, 2회차 13:00, 3회차 15:30)",
        "capacity_info": "회차당 15가정 (선착순 정기 예약)",
        "fee": "영유아 2,000원 (보호자 무료)",
        "location": "꾸미팡팡놀이터 군자점 (군자동) / 자양점",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": "https://images.unsplash.com/photo-1596464716127-f2a829822301?auto=format&fit=crop&w=800&q=80",
        "detail_content": json.dumps({
            "시설명": "광진구 꾸미팡팡놀이터 (공공 영유아 실내놀이터)",
            "이용대상": "0~36개월 영유아 및 미취학 아동과 보호자",
            "정기예약오픈": "매주 화요일 오전 09:00 (차주 이용분 오픈)",
            "이용시간": "1회차 10:00~12:00, 2회차 13:00~15:00, 3회차 15:30~17:30",
            "이용요금": "아동 2,000원 / 보호자 무료 (다둥이/기초생활수급 100% 감면)",
            "예약방법": "광진구 공식 예약포털 온라인 선착순 예약"
        }, ensure_ascii=False),
        "origin_url": "https://www.gjcare.go.kr/html/sub/index.php?pno=030401"
    },
    {
        "institution_name": "서울형 키즈카페 (광진구)",
        "district": "광진구",
        "category": "공공놀이터/키즈카페",
        "title": "[서울형 키즈카페] 광진구점(중곡3동점/자양4동점) 영유아 회차 정기 예약",
        "target_age_group": "0~36개월 공통",
        "target_desc": "서울시 거주 영유아(0~36개월 전용 회차 포함) 및 보호자",
        "apply_start_at": "매주 화요일 09:00",
        "apply_end_at": "이용 당일까지 선착순",
        "event_date_desc": "화~일 1일 3회차 운영 (회차별 2시간)",
        "capacity_info": "회차당 20~25명 (공식 마스터 정원)",
        "fee": "아동 2,000원 / 보호자 1,000원 (돌 이전 영아 무료)",
        "location": "서울형 키즈카페 광진구 중곡3동점 / 자양4동점",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": "https://images.unsplash.com/photo-1544717305-2782549b5136?auto=format&fit=crop&w=800&q=80",
        "detail_content": json.dumps({
            "시설명": "서울형 키즈카페 (광진구 지점)",
            "예약오픈일": "매주 화요일 오전 09:00 (다음 주 이용분 전체 오픈)",
            "이용요금": "아동 2,000원 ~ 3,000원, 보호자 1,000원 (다둥이카드 소지자 무료)",
            "특징": "0~36개월 아기를 위한 '영아 전용 안전 놀이존' 및 수유실 구비",
            "공식예약": "서울시 우리동네키움포털(몽땅정보통) 키즈카페 직통 예약 시스템"
        }, ensure_ascii=False),
        "origin_url": "https://umppa.seoul.go.kr/icare/user/kidsCafe/BD_selectKidsCafeList.do"
    },
    {
        "institution_name": "서울형 키즈카페 (성동구)",
        "district": "성동구",
        "category": "공공놀이터/키즈카페",
        "title": "[서울형 키즈카페] 성동구점(금호점/성수점/마장점) 영유아 정기 예약",
        "target_age_group": "0~36개월 공통",
        "target_desc": "성동구 및 서울시 거주 영유아 및 보호자",
        "apply_start_at": "매주 화요일 09:00",
        "apply_end_at": "이용 당일까지 선착순",
        "event_date_desc": "화~일 (10:00 / 13:00 / 15:30 각 2시간)",
        "capacity_info": "회차당 20명 내외",
        "fee": "아동 2,000원 / 보호자 1,000원 (다둥이 무료)",
        "location": "성동구 금호1가동점, 성수1가점, 마장동점 등",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": None,
        "detail_content": json.dumps({
            "시설명": "서울형 키즈카페 성동구 관내 지점",
            "예약오픈일": "매주 화요일 오전 09:00 정기 예약 오픈",
            "감면혜택": "다둥이카드 소지자, 장애인, 한부모가정 100% 무료 감면 (온라인 자동 연동)",
            "공식예약": "서울시 우리동네키움포털(몽땅정보통) 키즈카페 직통 예약 시스템"
        }, ensure_ascii=False),
        "origin_url": "https://umppa.seoul.go.kr/icare/user/kidsCafe/BD_selectKidsCafeList.do"
    },

    # 2. 보건소 (모자보건실 영유아 건강/양육 프로그램)
    {
        "institution_name": "광진구보건소 (모자보건실)",
        "district": "광진구",
        "category": "보건소",
        "title": "[광진구보건소] 0~12개월 영아 맞춤 1:1 모유수유 클리닉 & 베이비 이유식 코칭",
        "target_age_group": "0~12개월 (영아)",
        "target_desc": "광진구 거주 출산 수유부 및 0~12개월 영아 양육 부모",
        "apply_start_at": "2026-09-01",
        "apply_end_at": "2026-09-25",
        "event_date_desc": "매주 목요일 14:00~16:00 (1:1 전문가 개별 맞춤 상담)",
        "capacity_info": "회차당 6가정 (선착순 사전 예약)",
        "fee": "무료",
        "location": "광진구보건소 2층 모자보건실",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": None,
        "detail_content": json.dumps({
            "프로그램명": "광진구보건소 영아 모유수유 및 초기/중기 이유식 클리닉",
            "내용": "국제모유수유전문가 1:1 수유 자세 교정 및 아기 월령별 알레르기 예방 이유식 가이드",
            "신청방법": "광진구보건소 모자보건실 온라인 예약 또는 전화 접수",
            "준비물": "아기 수첩, 수유 쿠션(선택)"
        }, ensure_ascii=False),
        "origin_url": "https://www.gwangjin.go.kr/health/main.do"
    },
    {
        "institution_name": "성동구보건소 (모자보건실)",
        "district": "성동구",
        "category": "보건소",
        "title": "[성동구보건소] 6~24개월 영유아 영양플러스 & 건강 오감발달 교실",
        "target_age_group": "6~24개월",
        "target_desc": "성동구 관내 6~24개월 영유아 및 보호자",
        "apply_start_at": "2026-09-05",
        "apply_end_at": "2026-09-20",
        "event_date_desc": "2026-09-24 (목) 10:30~11:30",
        "capacity_info": "15가정 (선착순 접수)",
        "fee": "무료",
        "location": "성동구보건소 본관 3층 보건교육실",
        "status": "접수예정",
        "detail_type": "TABLE_TEXT",
        "image_url": None,
        "detail_content": json.dumps({
            "프로그램명": "성동구보건소 영유아 발달 및 영양플러스 교실",
            "내용": "영유아 성장 단계별 필수 영양소 섭취법 및 부모와 함께하는 신체 놀이",
            "신청방법": "성동구보건소 홈페이지 온라인 예약"
        }, ensure_ascii=False),
        "origin_url": "https://bogunso.sd.go.kr"
    },

    # 3. 숲체험 / 생태공원 (서울숲 & 어린이대공원)
    {
        "institution_name": "서울숲공원 (서울시공공서비스예약)",
        "district": "성동구",
        "category": "숲체험/공원",
        "title": "[서울숲] 2026 가을학기 아장아장 영아 숲놀이 (12~36개월 부모동반)",
        "target_age_group": "13~24개월 (걸음마)",
        "target_desc": "12~36개월 영아 및 보호자 (가정당 아동 1명, 보호자 1명)",
        "apply_start_at": "2026-09-08 10:00",
        "apply_end_at": "2026-09-18",
        "event_date_desc": "매주 화/목 10:30~11:30 (총 4회차 운영)",
        "capacity_info": "회차당 10가정 (서울시공공서비스예약)",
        "fee": "무료",
        "location": "서울숲공원 숲속놀이터 및 거울연못 일대",
        "status": "접수예정",
        "detail_type": "TABLE_TEXT",
        "image_url": "https://images.unsplash.com/photo-1448375240586-882707db888b?auto=format&fit=crop&w=800&q=80",
        "detail_content": json.dumps({
            "프로그램명": "서울숲 아장아장 영아 생태 숲체험",
            "내용": "전문 숲해설가와 함께 낙엽 밟기, 흙 만지기, 자연물 오감 자극 야외 숲놀이",
            "신청방법": "서울시 공공서비스예약 온라인 선착순 신청",
            "유의사항": "유모차 동반 가능, 편안한 복장 착용"
        }, ensure_ascii=False),
        "origin_url": "https://yeyak.seoul.go.kr/web/reservation/selectReservList.do"
    },
    {
        "institution_name": "서울어린이대공원 (서울시공공서비스예약)",
        "district": "광진구",
        "category": "숲체험/공원",
        "title": "[어린이대공원] 엄마·아빠와 함께하는 숲속 힐링 유모차 산책 (0~24개월)",
        "target_age_group": "0~24개월",
        "target_desc": "0~24개월 영아 및 유모차 동반 보호자",
        "apply_start_at": "2026-09-01",
        "apply_end_at": "2026-09-15",
        "event_date_desc": "매주 수요일 11:00~12:00",
        "capacity_info": "회차당 12가정",
        "fee": "무료",
        "location": "어린이대공원 숲속의 무대 뒤편 산책로",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": None,
        "detail_content": json.dumps({
            "프로그램명": "어린이대공원 유모차 숲길 힐링 산책",
            "내용": "유모차 전용 무장애 숲길을 따라 거닐며 피톤치드 힐링 및 아기 오감 소리 탐색",
            "신청방법": "서울시 공공서비스예약 포털 접수"
        }, ensure_ascii=False),
        "origin_url": "https://yeyak.seoul.go.kr/web/reservation/selectReservList.do"
    },

    # 4. 백화점 / 대형마트 문화센터 (0~36개월 영유아 인기 강좌)
    {
        "institution_name": "롯데백화점 문화센터 (건대스타시티점)",
        "district": "광진구",
        "category": "백화점/마트 문센",
        "title": "[롯데 건대점 문센] 2026 가을학기 '베이비 오감놀이 팡팡 & 베이비 마사지' (4~12개월)",
        "target_age_group": "0~12개월 (영아)",
        "target_desc": "4~12개월 영아 및 보호자 (1:1 동반)",
        "apply_start_at": "2026-08-20",
        "apply_end_at": "2026-09-10",
        "event_date_desc": "2026-09-05 ~ 2026-11-28 (매주 금 11:10~11:50, 총 12회)",
        "capacity_info": "강좌당 12가정 (선착순 접수)",
        "fee": "120,000원 (재료비 별도 30,000원)",
        "location": "롯데백화점 건대스타시티점 9층 문화센터",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": "https://images.unsplash.com/photo-1502086223501-7ea6ecd79368?auto=format&fit=crop&w=800&q=80",
        "detail_content": json.dumps({
            "강좌명": "베이비 오감놀이 팡팡 & 베이비 마사지",
            "지점": "롯데백화점 건대스타시티점 (광진구 자양동)",
            "대상": "생후 4개월 ~ 12개월 영아",
            "강좌내용": "부모와의 애착 형성을 돕는 베이비 림프 마사지 및 계절 곡물 오감 놀이",
            "신청방법": "롯데백화점 문화센터 공식 홈페이지 온라인 수강신청"
        }, ensure_ascii=False),
        "origin_url": "https://culture.lotteshopping.com"
    },
    {
        "institution_name": "이마트 문화센터 (왕십리점)",
        "district": "성동구",
        "category": "백화점/마트 문센",
        "title": "[이마트 왕십리점] 2026 가을학기 '트니트니 키즈챔프' 신체 발달 놀이 (15~24개월)",
        "target_age_group": "13~24개월 (걸음마)",
        "target_desc": "15~24개월 걸음마기 영유아 및 보호자",
        "apply_start_at": "2026-08-15",
        "apply_end_at": "2026-09-10",
        "event_date_desc": "2026-09-06 ~ 2026-11-29 (매주 토 10:20~11:00)",
        "capacity_info": "정원 14명 (선착순 수강신청)",
        "fee": "130,000원 (교구비 포함)",
        "location": "이마트 왕십리점 3층 문화센터 (성동구 행당동)",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": "https://images.unsplash.com/photo-1566004100631-35d015d6a491?auto=format&fit=crop&w=800&q=80",
        "detail_content": json.dumps({
            "강좌명": "트니트니 키즈챔프 (가을학기)",
            "지점": "이마트 문화센터 왕십리점 (왕십리역 민자역사)",
            "대상": "15~24개월 활발하게 걷는 아기",
            "강좌내용": "대근육 발달과 균형 감각을 키워주는 대한민국 No.1 영유아 신체 놀이 강좌",
            "신청방법": "이마트 문화센터 웹사이트 수강신청 직통 연결"
        }, ensure_ascii=False),
        "origin_url": "https://www.cultureclub.emart.com"
    },
    {
        "institution_name": "이마트 문화센터 (자양점)",
        "district": "광진구",
        "category": "백화점/마트 문센",
        "title": "[이마트 자양점] 2026 가을학기 '텀블키즈(Tumble Kids)' 뮤직 오감놀이 (8~18개월)",
        "target_age_group": "0~18개월",
        "target_desc": "8~18개월 영아 및 보호자",
        "apply_start_at": "2026-08-15",
        "apply_end_at": "2026-09-10",
        "event_date_desc": "2026-09-04 ~ 2026-11-27 (매주 목 11:30~12:10)",
        "capacity_info": "12가정",
        "fee": "110,000원",
        "location": "이마트 자양점 문화센터 (더샵스타시티 지하)",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": None,
        "detail_content": json.dumps({
            "강좌명": "텀블키즈 뮤직 오감놀이",
            "지점": "이마트 자양점 (광진구 자양동)",
            "대상": "8개월 ~ 18개월 영아",
            "강좌내용": "클래식 음악과 함께하는 리듬 타악기 탐색 및 촉각 자극 테마 놀이",
            "신청방법": "이마트 문화센터 온라인 수강신청"
        }, ensure_ascii=False),
        "origin_url": "https://www.cultureclub.emart.com"
    },

    # 5. 구립도서관 북스타트
    {
        "institution_name": "성동구립도서관",
        "district": "성동구",
        "category": "구립도서관",
        "title": "2026 성동구 북스타트(Bookstart) 책꾸러미 택배 및 방문 수령 신청",
        "target_age_group": "0~36개월 공통",
        "target_desc": "성동구 거주 0~35개월 영유아 (출생~3세)",
        "apply_start_at": "상시 접수중",
        "apply_end_at": "꾸러미 소진 시까지",
        "event_date_desc": "신청 승인 후 도서관 방문 수령 또는 택배 배송",
        "capacity_info": "성동구 거주 영유아 전원",
        "fee": "무료 (그림책 2권, 가방, 가이드북 증정)",
        "location": "성동구립도서관 / 성수도서관 / 금호도서관 등 관내 구립도서관",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": None,
        "detail_content": json.dumps({
            "사업명": "성동구 북스타트(Bookstart) 책꾸러미 배부",
            "지원대상": "성동구에 주민등록을 둔 0~35개월 영유아",
            "신청기간": "상시 온라인 신청 가능",
            "단계구분": "1단계: 북스타트(0~18개월), 2단계: 북스타트 플러스(19~35개월)",
            "수령방법": "성동구립도서관 홈페이지 온라인 신청 후 지정 도서관 방문 수령",
            "문의처": "성동구립도서관 (02-2204-6424)"
        }, ensure_ascii=False),
        "origin_url": "https://www.sdlib.or.kr/main/sub.html?section=1&menu=188"
    },

    # 6. 정부지원 시간제보육
    {
        "institution_name": "아이사랑(임신육아종합포털)",
        "district": "광진구/성동구",
        "category": "시간제보육",
        "title": "[정부지원] 6~36개월 맞춤형 시간제보육 서비스 온라인 상시 예약",
        "target_age_group": "0~36개월 공통",
        "target_desc": "만 6개월 ~ 36개월 미만 영아 (가정양육 아동)",
        "apply_start_at": "상시 온라인 예약",
        "apply_end_at": "이용 당일 1일 전까지",
        "event_date_desc": "평일 09:00 ~ 18:00 (월 최대 80시간 지원)",
        "capacity_info": "1:3 전문 보육교사 매칭",
        "fee": "정부지원 시간당 2,000원 (본인부담금 기준)",
        "location": "광진구·성동구 관내 지정 어린이집 및 육아종합지원센터 시간제보육실",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": None,
        "detail_content": json.dumps({
            "서비스명": "시간제보육 서비스 (독립반/통합반)",
            "지원대상": "만 6개월 이상 ~ 36개월 미만 영아",
            "지원시간": "월 최대 80시간 정부지원 (시간당 2,000원 본인부담)",
            "이용방법": "임신육아종합포털 아이사랑 회원가입 > 아동등록 > 시간제보육 예약",
            "광진구 제공기관": "광진구육아종합지원센터, 구립어린이집 등",
            "성동구 제공기관": "성동구육아종합지원센터, 구립성수어린이집 등"
        }, ensure_ascii=False),
        "origin_url": "https://www.childcare.go.kr/cpin/contents/010401000000.jsp"
    }
]

async def sync_all_data(db: Session) -> dict:
    from app.database import create_tables
    create_tables()

    scrapers = [
        GwangjinCareScraper(),
        SeongdongCareScraper(),
        GwangjinLibScraper(),
        FamilyNetScraper()
    ]
    
    total_added = 0
    total_updated = 0
    errors = []
    
    # 1. 스크래퍼 실행
    all_scraped_items = []
    for scraper in scrapers:
        try:
            items = await scraper.scrape()
            all_scraped_items.extend(items)
        except Exception as e:
            msg = f"{scraper.name} 수집 중 오류: {str(e)}"
            logger.error(msg)
            errors.append(msg)
            
    # 2. 공식 큐레이션 데이터 결합
    all_scraped_items.extend(CURATED_OFFICIAL_DATA)
    
    # 3. DB 초기화 후 정규화 저장
    db.query(Program).delete()
    
    for item in all_scraped_items:
        try:
            new_prog = Program(**item)
            db.add(new_prog)
            total_added += 1
        except Exception as e:
            errors.append(f"DB 저장 오류 ({item.get('title')}): {str(e)}")
            
    db.commit()
    return {
        "total_added": total_added,
        "total_updated": total_updated,
        "total_programs": db.query(Program).count(),
        "errors": errors
    }
