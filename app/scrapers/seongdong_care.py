import re
import ssl
import json
import logging
import urllib.request
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)

class SeongdongCareScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "성동구육아종합지원센터"

    @property
    def district(self) -> str:
        return "성동구"

    @property
    def category(self) -> str:
        return "육아종합지원센터"

    def _get_ssl_context(self):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def _fetch_html(self, url: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://ccic.sd.go.kr/main/index.php"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=self._get_ssl_context(), timeout=10) as response:
            return response.read().decode("utf-8", errors="ignore")

    def _determine_age_group(self, title: str, target: str) -> str:
        combined = f"{title} {target}"
        if any(w in combined for w in ["0~12", "2~11", "영아", "베이비", "마사지", "신생아", "아가"]):
            return "0~12개월"
        elif any(w in combined for w in ["12~24", "13~24", "돌", "아장아장", "오감놀이", "걸음마"]):
            return "13~24개월"
        elif any(w in combined for w in ["20~22", "23~24", "25~36", "3세", "신체놀이"]):
            return "25~36개월"
        return "0~36개월 공통"

    async def scrape(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        
        # 성동구육아종합지원센터 실제 온라인 신청 페이지들
        target_menus = [
            ("06", "04", "02", "가정양육 영유아 프로그램"),
            ("06", "02", "02", "부모교육 프로그램")
        ]

        for cat, menu, group, menu_label in target_menus:
            list_url = f"https://ccic.sd.go.kr/main/main.php?categoryid={cat}&menuid={menu}&groupid={group}"
            try:
                html = self._fetch_html(list_url)
                soup = BeautifulSoup(html, "html.parser")
                
                # 테이블 행 파싱
                for tr in soup.find_all("tr"):
                    tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                    if len(tds) < 6:
                        continue
                    
                    # 제목 및 링크 추출
                    a_tag = tr.find("a", href=lambda h: h and "boardView" in h)
                    if not a_tag:
                        continue
                    
                    title = tds[1]
                    target_desc = tds[2] if len(tds) > 2 else "성동구 관내 영유아 및 보호자"
                    event_time = tds[3] if len(tds) > 3 else "상세 페이지 참조"
                    apply_period = tds[4] if len(tds) > 4 else ""
                    capacity = tds[5] if len(tds) > 5 else "정원 마감"
                    raw_status = tds[6] if len(tds) > 6 else ""

                    # boardView('10825') 에서 no 추출
                    match = re.search(r"boardView\('?(\d+)'?\)", a_tag.get("href", ""))
                    if match:
                        no = match.group(1)
                        detail_url = f"https://ccic.sd.go.kr/main/main.php?categoryid={cat}&menuid={menu}&groupid={group}&board=view&no={no}"
                    else:
                        detail_url = list_url

                    # 보육교사/어린이집 전용 공고 필터링 (부모 및 영유아 대상만 허용)
                    from app.scrapers.base import is_for_parent_and_child
                    if not is_for_parent_and_child(title, target_desc):
                        logger.info(f"Filtered out non-parent program: {title} ({target_desc})")
                        continue

                    # 상태 정규화
                    status = "접수예정"

                    if "신청" in raw_status or "접수" in raw_status:
                        status = "접수중"
                    elif "마감" in raw_status or "종료" in raw_status:
                        status = "마감"

                    apply_start = apply_period.split("~")[0].strip() if "~" in apply_period else apply_period
                    apply_end = apply_period.split("~")[1].strip() if "~" in apply_period else ""

                    results.append({
                        "institution_name": self.name,
                        "district": self.district,
                        "category": self.category,
                        "title": title,
                        "target_age_group": self._determine_age_group(title, target_desc),
                        "target_desc": target_desc,
                        "apply_start_at": apply_start,
                        "apply_end_at": apply_end,
                        "event_date_desc": event_time,
                        "capacity_info": capacity,
                        "fee": "무료",
                        "location": "성동구육아종합지원센터 (왕십리로 241)",
                        "status": status,
                        "detail_type": "TABLE_TEXT",
                        "image_url": None,
                        "detail_content": json.dumps({
                            "프로그램명": title,
                            "대상": target_desc,
                            "일시": event_time,
                            "신청기간": apply_period,
                            "정원/접수인원": capacity,
                            "신청상태": raw_status,
                            "신청기관": "성동구육아종합지원센터"
                        }, ensure_ascii=False),
                        "origin_url": detail_url
                    })
            except Exception as e:
                logger.error(f"Seongdong care live scrape error: {e}")

        logger.info(f"Seongdong care live scraped {len(results)} actual programs.")
        return results
