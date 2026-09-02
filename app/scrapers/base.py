import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any

# 제외 대상 키워드 (보육교사, 원장, 기관 종사자, 전문가과정, 초중고/성인 등)
EXCLUDE_KEYWORDS = [
    "전문가과정",
    "전문가 과정",
    "보육·교육기관",
    "보육교육기관",
    "보육·교육",
    "교육기관",
    "기관 종사자",
    "교직원",
    "보육교직원",
    "보육교사",
    "어린이집 교사",
    "어린이집 원장",
    "원장 및",
    "원장 대상",
    "교사 대상",
    "교직원 대상",
    "대체교사",
    "연장보육교사",
    "어린이집 대상",
    "선정 외 어린이집",
    "어린이집 운영",
    "평가제 컨설팅",
    "재무회계",
    "회계교육",
    "직무교육",
    "초등",
    "청소년",
    "어르신",
    "시니어",
    "중고등"
]

def is_for_parent_and_child(title: str, target_desc: str = "", extra_text: str = "") -> bool:
    """
    0~36개월 영유아 및 부모(양육자) 대상 공고만 엄격하게 선별.
    보육교직원, 교육기관 종사자, 전문가과정 등은 철저히 배제.
    """
    combined = f"{title} {target_desc} {extra_text}".strip()

    # 1. 제외 키워드 매칭
    for kw in EXCLUDE_KEYWORDS:
        if kw in combined:
            return False

    # 2. 부모/영유아 키워드가 전혀 없고 기관 느낌이 강한 경우 차단
    # 유효 타겟 키워드: 영유아, 영아, 유아, 아기, 아가, 부모, 양육자, 아빠, 엄마, 가정, 북스타트, 자녀, 임산부 등
    valid_target_keywords = [
        "영유아", "영아", "유아", "아기", "아가", "부모", "양육", "아빠", "엄마",
        "가정", "가족", "북스타트", "자녀", "베이비", "마사지", "놀이", "임산부", "태아", "개월", "세"
    ]
    
    has_valid_target = any(k in combined for k in valid_target_keywords)
    if not has_valid_target:
        return False

    return True


def clean_datetime_text(text: str) -> str:
    """
    날짜/일시 문자열에서 날짜와 시간 사이 공백 보정 및 불필요한 줄바꿈/대시 제거.
    예: '2026-09-1116:20~17:10' -> '2026-09-11 16:20 ~ 17:10'
    예: '2026-10-01   -' -> '2026-10-01'
    """
    if not text:
        return ""
    
    cleaned = text
    # 1. 날짜와 시작 시간 붙어있는 경우 분리 (예: 2026-09-1116:20 -> 2026-09-11 16:20)
    cleaned = re.sub(r'(\d{4}[-.]\d{2}[-.]\d{2})\s*(\d{2}:\d{2})', r'\1 \2', cleaned)
    
    # 2. 물결표(~) 앞뒤 공백 정돈
    cleaned = re.sub(r'\s*~\s*', ' ~ ', cleaned)
    
    # 3. 연속된 공백, 줄바꿈, 탭을 단일 공백으로 치환
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # 4. 끝부분의 불필요한 대시나 기호 제거 (예: '2026-10-01 -' -> '2026-10-01')
    cleaned = re.sub(r'\s*[-~]\s*$', '', cleaned).strip()
    
    return cleaned


class BaseScraper(ABC):
    def __init__(self, name: str, district: str, category: str):
        self.name = name
        self.district = district
        self.category = category

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """
        크롤링 수행 후 정규화된 Program 딕셔너리 리스트 반환
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """기관 및 스크래퍼 이름"""
        pass

    @property
    @abstractmethod
    def district(self) -> str:
        """자치구 (광진구, 성동구 등)"""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """기관 카테고리 (육아종합지원센터, 구립도서관, 가족센터 등)"""

    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """프로그램 데이터 수집 후 딕셔너리 리스트 반환"""
        pass
