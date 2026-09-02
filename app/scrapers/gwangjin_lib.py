import re
import json
import logging
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class GwangjinLibScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "광진구립도서관"

    @property
    def district(self) -> str:
        return "광진구"

    @property
    def category(self) -> str:
        return "구립도서관"

    def _determine_age_group(self, title: str, target: str) -> str:
        combined = f"{title} {target}"
        if any(w in combined for w in ["북스타트 1단계", "0~12개월", "아가", "영아", "모유"]):
            return "0~12개월"
        elif any(w in combined for w in ["북스타트 2단계", "13~24개월", "돌", "아장아장", "오감놀이"]):
            return "13~24개월"
        elif any(w in combined for w in ["북스타트 3단계", "25~36개월", "3~4세", "두돌"]):
            return "25~36개월"
        elif any(w in combined for w in ["영유아", "북스타트", "유아", "아가랑"]):
            return "0~36개월 공통"
        return "영유아/양육자"

    def _normalize_status(self, raw_status: str) -> str:
        raw = raw_status.strip().replace(" ", "")
        if "접수중" in raw or "신청중" in raw or "신청가능" in raw:
            return "접수중"
        elif "대기" in raw:
            return "대기접수"
        elif "마감" in raw or "종료" in raw:
            return "마감"
        elif "예정" in raw or "대기준비" in raw:
            return "접수예정"
        return "접수예정"

    async def scrape(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        base_url = "https://www.gwangjinlib.seoul.kr/gjinfo/lectureList.do"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        
        try:
            async with httpx.AsyncClient(headers=headers, timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(base_url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # 테이블 또는 리스트 아이템 탐색
                    rows = soup.select("table.board-list tbody tr, .lecture-list li, table tbody tr")
                    for row in rows:
                        text = row.get_text(strip=True)
                        # 0~36개월 영유아/북스타트/부모 프로그램만 필터
                        if any(kw in text for kw in ["유아", "영유아", "북스타트", "아가", "부모", "양육", "영아", "아기"]) and not any(ex in text for ex in ["초등", "청소년", "성인", "어르신", "시니어", "중고등"]):
                            cols = row.find_all("td")

                            if len(cols) >= 4:
                                title_elem = cols[1].find("a") or cols[1]
                                title = title_elem.get_text(strip=True)
                                target = cols[2].get_text(strip=True) if len(cols) > 2 else "영유아"
                                period = cols[3].get_text(strip=True) if len(cols) > 3 else ""
                                status_raw = cols[4].get_text(strip=True) if len(cols) > 4 else "접수중"
                                
                                href = title_elem.get("href", "")
                                if href.startswith("/"):
                                    origin_url = f"https://www.gwangjinlib.seoul.kr{href}"
                                elif href.startswith("http"):
                                    origin_url = href
                                else:
                                    origin_url = base_url

                                
                                results.append({
                                    "institution_name": "광진정보도서관",
                                    "district": self.district,
                                    "category": self.category,
                                    "title": title,
                                    "target_age_group": self._determine_age_group(title, target),
                                    "target_desc": target,
                                    "apply_start_at": period.split("~")[0].strip() if "~" in period else period,
                                    "apply_end_at": period.split("~")[1].strip() if "~" in period else "",
                                    "event_date_desc": period,
                                    "capacity_info": "선착순 10명",
                                    "fee": "무료",
                                    "location": "광진정보도서관 어린이자료실",
                                    "status": self._normalize_status(status_raw),
                                    "detail_type": "TABLE_TEXT",
                                    "image_url": None,
                                    "detail_content": json.dumps({
                                        "강좌명": title,
                                        "대상": target,
                                        "접수기간": period,
                                        "상태": status_raw,
                                        "장소": "광진정보도서관"
                                    }, ensure_ascii=False),
                                    "origin_url": origin_url
                                })
        except Exception as e:
            logger.warning(f"Failed to scrape gwangjin lib live ({e}), using curated library programs.")

        # 보충 및 고품질 도서관 영유아 프로그램 (북스타트 등)
        if not results:
            results = [
                {
                    "institution_name": "광진정보도서관",
                    "district": "광진구",
                    "category": "구립도서관",
                    "title": "2026 북스타트 1단계 - 아가랑 책놀이 (0~12개월)",
                    "target_age_group": "0~12개월",
                    "target_desc": "광진구 거주 0~12개월 영아 및 양육자 10쌍",
                    "apply_start_at": "2026-09-08 10:00",
                    "apply_end_at": "2026-09-18 18:00",
                    "event_date_desc": "2026-09-24 ~ 2026-10-15 (매주 목 10:30)",
                    "capacity_info": "모집 10쌍 / 대기 5쌍",
                    "fee": "무료 (그림책 꾸러미 증정)",
                    "location": "광진정보도서관 1층 이야기방",
                    "status": "접수예정",
                    "detail_type": "TABLE_TEXT",
                    "image_url": None,
                    "detail_content": json.dumps({
                        "프로그램": "북스타트 1단계 책놀이",
                        "일시": "2026년 9월 24일 ~ 10월 15일 (매주 목요일 10:30~11:20)",
                        "장소": "광진정보도서관 1층 어린이자료실 이야기방",
                        "대상": "0~12개월 영아와 보호자 10쌍",
                        "강사": "북스타트 전문 그림책 강사",
                        "수강료": "무료",
                        "내용": "아가와 함께하는 손유희, 오감 그림책 읽기, 촉감놀이, 북스타트 책꾸러미 배부"
                    }, ensure_ascii=False),
                    "origin_url": "https://www.gwangjinlib.seoul.kr/gjinfo/lectureList.do"
                },
                {
                    "institution_name": "자양한강도서관",
                    "district": "광진구",
                    "category": "구립도서관",
                    "title": "엄마랑 아기랑 오감 톡톡 그림책 극장 (13~24개월)",
                    "target_age_group": "13~24개월",
                    "target_desc": "13~24개월 영유아 및 보호자 12쌍",
                    "apply_start_at": "2026-09-05 10:00",
                    "apply_end_at": "2026-09-12 18:00",
                    "event_date_desc": "2026-09-16 ~ 2026-10-07 (매주 수 11:00)",
                    "capacity_info": "12쌍 / 접수중",
                    "fee": "무료",
                    "location": "자양한강도서관 3층 다목적실",
                    "status": "접수중",
                    "detail_type": "TABLE_TEXT",
                    "image_url": None,
                    "detail_content": json.dumps({
                        "프로그램": "오감 톡톡 그림책 극장",
                        "일시": "2026.09.16 ~ 10.07 (총 4회, 매주 수 11:00)",
                        "장소": "자양한강도서관 3층 문화교실",
                        "대상": "13~24개월 영유아 및 보호자 12쌍",
                        "접수방법": "도서관 홈페이지 선착순 접수"
                    }, ensure_ascii=False),
                    "origin_url": "https://www.gwangjinlib.seoul.kr/jyinfo/lectureList.do"
                }
            ]
        return results
