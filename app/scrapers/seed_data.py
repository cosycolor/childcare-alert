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

# 실제 지자체 연계 공공/민간 프로그램 및 예약 데이터 (키즈카페, 놀이터, 보건소, 숲체험, 백화점/마트 문센, 북스타트, 시간제보육)
CURATED_OFFICIAL_DATA = [
    # 1. 공공놀이터 / 서울형 키즈카페 / 공동육아방
    {
        "institution_name": "광진구육아종합지원센터 (꾸미팡팡 공동육아방)",
        "district": "광진구",
        "category": "공공놀이터/키즈카페",
        "title": "[공동육아방] 광진구 꾸미팡팡 공동육아방(1호점 능동/2호점 중곡동/3호점 군자동) 예약",
        "target_age_group": "0~36개월 공통",
        "target_desc": "광진구 관내 0~36개월 영아 및 동반 보호자 (부모/양육자)",
        "apply_start_at": "매주 월요일 09:00",
        "apply_end_at": "이용 전날 24:00까지",
        "event_date_desc": "평일 월~금 (1회차 09:30~11:30 / 2회차 13:00~15:00 / 3회차 15:30~17:30)",
        "capacity_info": "회차당 3가족 (최대 6명, 선착순)",
        "fee": "무료",
        "location": "1호점(능동), 2호점(중곡동), 3호점(군자동)",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": "https://images.unsplash.com/photo-1596464716127-f2a829822301?auto=format&fit=crop&w=800&q=80",
        "detail_content": json.dumps({
            "시설명": "광진구 꾸미팡팡 공동육아방 (1호점 능동, 2호점 중곡동, 3호점 군자동)",
            "이용대상": "광진구 관내 36개월 이하 영아 및 동반 부모(보호자)",
            "정기예약오픈": "매주 월요일 오전 09:00에 다음 주 예약 오픈",
            "예약/취소규칙": "홈페이지 예약 및 취소는 이용일 전날 24시까지 가능 (당일 10시까지 전화 취소 시 벌점 미발생)",
            "이용시간": "1회차 09:30~11:30, 2회차 13:00~15:00, 3회차 15:30~17:30 (점심/환경정비시간 제외)",
            "이용인원": "회차당 3가족(6명) / 형제자매 동반 시 총 7명 이내",
            "이용요금": "무료",
            "예약방법": "광진구육아종합지원센터 홈페이지 회원가입 후 온라인 신청 (미달 시 당일 전화 신청)"
        }, ensure_ascii=False),
        "origin_url": "https://www.gjcare.go.kr/html/sub/index.php?pno=041604"
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
    },

    # 7. 영유아 복합문화/체험관 (신규)
    {
        "institution_name": "서울상상나라",
        "district": "광진구",
        "category": "복합체험관",
        "title": "[서울상상나라] 36개월 미만 전용 '아기놀이터' & 영아 오감 발달놀이",
        "target_age_group": "0~36개월 공통",
        "target_desc": "36개월 미만 영유아 및 양육자 (단독 전용 공간)",
        "apply_start_at": "상시 관람 예약",
        "apply_end_at": "회차별 마감 시까지",
        "event_date_desc": "화~일 10:00 ~ 18:00 (1일 4회차 운영)",
        "capacity_info": "회차당 25가정 (쾌적한 인원 제한)",
        "fee": "36개월 미만 무료 (보호자 4,000원)",
        "location": "광진구 능동 18 서울상상나라 2층 아기놀이터 (어린이대공원 정문)",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": "https://images.unsplash.com/photo-1596464716127-f2a829822301?auto=format&fit=crop&w=800&q=80",
        "detail_content": json.dumps({
            "시설명": "서울상상나라 2층 아기놀이터",
            "대상": "36개월 미만 영유아 전용 (큰 아이들과 분리되어 안전함)",
            "공간특징": "오감 자극 놀이 구조물, 부드러운 안전 쿠션 매트, 영아 수유실 완비",
            "신청방법": "서울상상나라 공식 홈페이지 > 개인예약 > 관람일/회차 선택 (사전 예약 권장)",
            "문의처": "02-6450-9500"
        }, ensure_ascii=False),
        "origin_url": "https://www.seoulchildrensmuseum.org"
    },
    {
        "institution_name": "성동 아이사랑 복합문화센터",
        "district": "성동구",
        "category": "복합체험관",
        "title": "[성동 아이사랑] 0~36개월 '뮤직 키즈 스튜디오' & 영유아 창의예술놀터",
        "target_age_group": "0~36개월 공통",
        "target_desc": "성동구 관내 0~36개월 영유아 및 가족",
        "apply_start_at": "매월 20일 10:00",
        "apply_end_at": "선착순 마감 시까지",
        "event_date_desc": "화~토 (1회차 10:00, 2회차 13:30, 3회차 15:30)",
        "capacity_info": "회차당 15가정",
        "fee": "무료 ~ 2,000원",
        "location": "성동구 금호로 22 (금호동3가) 성동 아이사랑복합문화센터",
        "status": "접수중",
        "detail_type": "TABLE_TEXT",
        "image_url": None,
        "detail_content": json.dumps({
            "시설구성": "1층 뮤직키즈스튜디오(음악체험), 2층 공동육아나눔터, 3~4층 창의예술놀터(디지털아트)",
            "주요프로그램": "영아 악기 소리 탐색, 인터랙티브 미디어아트 놀이, 아기 감각 드로잉",
            "신청방법": "성동 아이사랑 복합문화센터 웹사이트 온라인 사전예약",
            "문의처": "02-2204-7640"
        }, ensure_ascii=False),
        "origin_url": "https://artplay.sd.go.kr"
    },

    # 8. 구민체육센터 영아 수영 / 베이비 아쿠아 (신규)
    {
        "institution_name": "광진구민체육센터",
        "district": "광진구",
        "category": "구민체육센터",
        "title": "[광진구민체육센터] 12~36개월 '엄마랑 아가랑' 베이비 아쿠아 수영 교실",
        "target_age_group": "13~36개월",
        "target_desc": "12~36개월 영유아 및 보호자 (1:1 동반 입수)",
        "apply_start_at": "2026-09-22 09:00",
        "apply_end_at": "2026-09-28 18:00",
        "event_date_desc": "2026-10-01 ~ 2026-10-31 (매주 화/목 11:00 ~ 11:50)",
        "capacity_info": "반별 10쌍 선착순",
        "fee": "월 45,000원",
        "location": "광진구민체육센터 지하 2층 수영장 유아전용풀 (광장동)",
        "status": "접수예정",
        "detail_type": "TABLE_TEXT",
        "image_url": None,
        "detail_content": json.dumps({
            "강좌명": "엄마랑 아가랑 영아 수영 교실",
            "특징": "따뜻한 수온의 유아 전용풀에서 진행되는 심폐지구력 및 관절 이완 물놀이",
            "준비물": "방수 기저귀, 수영복, 수영모, 보호자 수영복",
            "신청방법": "광진구시설관리공단 공공체육시설 수강신청 시스템 접수"
        }, ensure_ascii=False),
        "origin_url": "https://booking.gwangjin.or.kr/fmcs/2?company_code=GWANGJIN01"
    },
    {
        "institution_name": "성동구민종합체육센터",
        "district": "성동구",
        "category": "구민체육센터",
        "title": "[성동구민체육센터] 18~36개월 '유아랑 엄마랑' 따뜻한 물놀이 & 체육 교실",
        "target_age_group": "18~36개월",
        "target_desc": "18~36개월 영유아 및 양육자",
        "apply_start_at": "2026-09-25 09:00",
        "apply_end_at": "2026-09-30 18:00",
        "event_date_desc": "2026-10-01 ~ 2026-10-31 (매주 월/수/금 10:00 ~ 10:50)",
        "capacity_info": "12쌍 선착순",
        "fee": "월 40,000원",
        "location": "성동구민종합체육센터 1층 유아풀 (뚝섬역 8번 출구)",
        "status": "접수예정",
        "detail_type": "TABLE_TEXT",
        "image_url": None,
        "detail_content": json.dumps({
            "강좌명": "유아랑 엄마랑 물놀이 체육",
            "특징": "물 공포심을 없애고 보호자와 교감하는 리듬 수중 체조",
            "신청방법": "성동구도시관리공단 체육시설 수강신청 포털 온라인 접수"
        }, ensure_ascii=False),
        "origin_url": "https://sports.happysd.or.kr"
    }
]


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

