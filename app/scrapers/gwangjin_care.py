import re
import ssl
import json
import logging
import urllib.request
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from app.scrapers.base import BaseScraper, clean_datetime_text, is_for_parent_and_child

logger = logging.getLogger(__name__)


class GwangjinCareScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "광진구육아종합지원센터"

    @property
    def district(self) -> str:
        return "광진구"

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
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
            "Referer": "https://www.gjcare.go.kr/"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=self._get_ssl_context(), timeout=10) as response:
            raw_bytes = response.read()
            try:
                return raw_bytes.decode("euc-kr")
            except UnicodeDecodeError:
                return raw_bytes.decode("utf-8", errors="ignore")

    def _determine_age_group(self, title: str, desc: str = "") -> str:
        combined = f"{title} {desc}"
        if any(w in combined for w in ["0~12", "영아", "모유", "베이비", "기어다니는", "아가", "신생아"]):
            return "0~12개월"
        elif any(w in combined for w in ["12~24", "13~24", "돌", "아장아장", "걸음마", "오감"]):
            return "13~24개월"
        elif any(w in combined for w in ["24~36", "25~36", "두돌", "3세", "신체놀이"]):
            return "25~36개월"
        return "0~36개월 공통"

    def _fetch_detail_info(self, detail_url: str) -> Dict[str, str]:
        """개별 상세페이지의 테이블 정보 파싱"""
        details = {}
        try:
            html = self._fetch_html(detail_url)
            soup = BeautifulSoup(html, "html.parser")
            for tr in soup.find_all("tr"):
                th = tr.find("th")
                td = tr.find("td")
                if th and td:
                    k = th.get_text(strip=True)
                    v = td.get_text(strip=True)
                    if k and v:
                        details[k] = v
        except Exception as e:
            logger.debug(f"Detail fetch failed for {detail_url}: {e}")
        return details

    async def scrape(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        target_menus = [
            ("060801", "행사"),
            ("060201", "부모교육/영유아프로그램")
        ]

        for pno, menu_name in target_menus:
            list_url = f"https://www.gjcare.go.kr/html/sub/index.php?pno={pno}"
            try:
                html = self._fetch_html(list_url)
                soup = BeautifulSoup(html, "html.parser")
                
                # 갤러리/리스트 형태의 항목들 추출
                items = soup.select("ul.gallery_list li, .program_list li, .sub_con_box ul li, ul li")
                for li in items:
                    a_view = li.find("a", href=lambda h: h and "mode=view" in h and "idx=" in h)
                    if not a_view:
                        continue
                    
                    href = a_view.get("href", "")
                    clean_href = href.replace("../../", "").lstrip("/")
                    detail_url = f"https://www.gjcare.go.kr/{clean_href}"
                    
                    # 제목 추출
                    title = a_view.get_text(strip=True)
                    if not title or len(title) < 2:
                        span = li.find("span")
                        title = span.get_text(strip=True) if span else "광진구육아종합지원센터 프로그램"

                    # 이미지 URL
                    img = li.find("img")
                    img_url = None
                    if img and img.get("src"):
                        src = img["src"]
                        if src.startswith("/"):
                            img_url = f"https://www.gjcare.go.kr{src}"
                        elif src.startswith(".."):
                            clean_src = src.replace("../", "").lstrip("/")
                            img_url = f"https://www.gjcare.go.kr/{clean_src}"
                        else:
                            img_url = f"https://www.gjcare.go.kr/{src}"

                    # 일자 및 상태 파싱
                    p_texts = [p.get_text(strip=True) for p in li.find_all("p")]
                    period = ""
                    status = "접수예정"
                    
                    for pt in p_texts:
                        if re.search(r"\d{4}-\d{2}-\d{2}", pt):
                            period = pt
                        if "신청" in pt and "기간" not in pt and "신청자" not in pt:
                            status = "접수중"
                        elif "마감" in pt:
                            status = "마감"

                    # 상세페이지의 정밀 데이터 매핑
                    detail_data = self._fetch_detail_info(detail_url)
                    
                    # 1. 신청기간 (상세페이지의 '신청기간' 우선)
                    exact_apply_period = clean_datetime_text(detail_data.get("신청기간", period))
                    apply_start = exact_apply_period.split("~")[0].strip() if "~" in exact_apply_period else exact_apply_period
                    apply_end = exact_apply_period.split("~")[1].strip() if "~" in exact_apply_period else ""

                    # 2. 진행일시 (상세페이지의 '일시' 우선)
                    event_date = clean_datetime_text(detail_data.get("일시", period or "상세 페이지 참조"))
                    
                    # 3. 정원 및 대상
                    raw_cap = detail_data.get("신청인원 / 정원", detail_data.get("신청인원/정원", detail_data.get("정원", "")))
                    if raw_cap:
                        capacity = f"{raw_cap} (마감)" if status == "마감" else raw_cap
                    else:
                        capacity = "선착순 모집"

                    target_desc = detail_data.get("대상", "광진구 관내 영유아 및 양육자")

                    # 보육교사/어린이집 전용 공고 필터링 (부모/영유아 대상만 허용)
                    from app.scrapers.base import is_for_parent_and_child
                    if not is_for_parent_and_child(title, target_desc, str(detail_data)):
                        logger.info(f"Filtered out non-parent program: {title}")
                        continue

                    # 이미 중복된 공고인지 확인
                    if any(r["origin_url"] == detail_url for r in results):
                        continue

                    # 상세 데이터 내 일시/신청기간도 정제
                    cleaned_detail_data = {}
                    for k, v in detail_data.items():
                        if k in ["일시", "신청기간", "기간"]:
                            cleaned_detail_data[k] = clean_datetime_text(v)
                        else:
                            cleaned_detail_data[k] = v

                    results.append({
                        "institution_name": self.name,
                        "district": self.district,
                        "category": self.category,
                        "title": title,
                        "target_age_group": self._determine_age_group(title, target_desc),
                        "target_desc": target_desc,
                        "apply_start_at": apply_start,
                        "apply_end_at": apply_end,
                        "event_date_desc": event_date,
                        "capacity_info": capacity,
                        "fee": "무료",
                        "location": "광진구육아종합지원센터 (군자동)",
                        "status": status,
                        "detail_type": "TABLE_TEXT",
                        "image_url": None,
                        "detail_content": json.dumps(cleaned_detail_data, ensure_ascii=False) if cleaned_detail_data else None,
                        "origin_url": detail_url
                    })


            except Exception as e:
                logger.error(f"Gwangjin care live scrape error for pno={pno}: {e}")

        logger.info(f"Gwangjin care live scraped {len(results)} actual programs.")
        return results
