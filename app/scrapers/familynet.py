import json
import logging
import urllib.request
import ssl
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from app.scrapers.base import BaseScraper, is_for_parent_and_child

logger = logging.getLogger(__name__)

class FamilyNetScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "가족센터"

    @property
    def district(self) -> str:
        return "광진구/성동구"

    @property
    def category(self) -> str:
        return "가족센터"

    def _get_ssl_context(self):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def _determine_age_group(self, title: str, desc: str = "") -> str:
        combined = f"{title} {desc}"
        if any(w in combined for w in ["0~12", "영아", "모유", "베이비", "아가", "신생아"]):
            return "0~12개월"
        elif any(w in combined for w in ["12~24", "13~24", "돌", "아장아장", "걸음마", "오감"]):
            return "13~24개월"
        elif any(w in combined for w in ["24~36", "25~36", "두돌", "3세", "신체놀이"]):
            return "25~36개월"
        return "0~36개월 공통"

    async def scrape(self) -> List[Dict[str, Any]]:
        # 패밀리넷 공식 [프로그램 안내 > 프로그램 신청] 직통 URL 제공 (오류 alert 없이 바로 이동)
        return [
            {
                "institution_name": "광진구가족센터",
                "district": "광진구",
                "category": "가족센터",
                "title": "[공동육아나눔터] 광진구 영유아 부모-자녀 상시 오감놀이 및 나눔터 이용",
                "target_age_group": "0~36개월 공통",
                "target_desc": "광진구 거주 0~36개월 영유아 및 양육 부모",
                "apply_start_at": "상시 온라인 예약",
                "apply_end_at": "이용 전일까지",
                "event_date_desc": "평일 및 토요일 10:00 ~ 17:00",
                "capacity_info": "타임별 5가정 (자유놀이/품앗이)",
                "fee": "무료",
                "location": "광진구가족센터 공동육아나눔터 (아차산로 24길)",
                "status": "접수중",
                "detail_type": "TABLE_TEXT",
                "image_url": None,
                "detail_content": json.dumps({
                    "기관명": "광진구가족센터",
                    "위치": "광진구가족센터 공동육아나눔터 (아차산로 24길)",
                    "대상": "광진구 관내 0~36개월 영유아 및 양육 부모",
                    "주요내용": "자유놀이 공간 이용, 장난감·도서 열람, 부모 품앗이 소그룹 모임",
                    "신청페이지": "광진구가족센터 프로그램 신청 직통 페이지로 이동"
                }, ensure_ascii=False),
                "origin_url": "https://gwangjin.familynet.or.kr/center/lay1/program/S295T322C451/recruitReceipt/list.do"
            },
            {
                "institution_name": "성동구가족센터",
                "district": "성동구",
                "category": "가족센터",
                "title": "[공동육아나눔터] 성동구 영유아 가정 놀이나눔터 상시 이용 및 부모 소통",
                "target_age_group": "0~36개월 공통",
                "target_desc": "성동구 거주 영유아 및 주양육자",
                "apply_start_at": "상시 온라인 예약",
                "apply_end_at": "이용 전일까지",
                "event_date_desc": "월~금 09:30 ~ 17:30",
                "capacity_info": "타임별 6가정",
                "fee": "무료",
                "location": "성동구가족센터 공동육아나눔터 (무학로 6길)",
                "status": "접수중",
                "detail_type": "TABLE_TEXT",
                "image_url": None,
                "detail_content": json.dumps({
                    "기관명": "성동구가족센터",
                    "위치": "성동구가족센터 공동육아나눔터 (무학로 6길)",
                    "대상": "성동구 거주 영유아 및 부모",
                    "주요내용": "영유아 친화 놀이공간 이용, 부모 양육 정보 교류 및 품앗이",
                    "신청페이지": "성동구가족센터 프로그램 신청 직통 페이지로 이동"
                }, ensure_ascii=False),
                "origin_url": "https://seongdong.familynet.or.kr/web/lay1/program/S1T304C450/recruitReceipt/list.do"
            }
        ]
