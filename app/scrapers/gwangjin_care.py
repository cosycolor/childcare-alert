import re
import ssl
import json
import html
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
                text = raw_bytes.decode("euc-kr")
            except UnicodeDecodeError:
                text = raw_bytes.decode("utf-8", errors="ignore")
            text = text.replace("&40&59;", "(").replace("&41&59;", ")")
            return html.unescape(text)

    def _determine_age_group(self, title: str, desc: str = "") -> str:
        combined = f"{title} {desc}"
        
        # 1. 개월 수 명시 매칭 (예: 15~24개월, 0~12개월 등)
        m = re.search(r'(\d+)\s*~\s*(\d+)\s*개월', combined)
        if m:
            start_m, end_m = int(m.group(1)), int(m.group(2))
            if end_m <= 12:
                return "0~12개월"
            elif start_m >= 24 or (start_m >= 20 and end_m >= 36):
                return "25~36개월"
            elif start_m >= 12 or end_m <= 27:
                return "13~24개월"
            return "0~36개월 공통"

        # 2. 유아 나이 매칭 (예: 3~5세, 3세)
        m_age = re.search(r'(\d+)\s*세', combined)
        if m_age:
            age = int(m_age.group(1))
            if age <= 1:
                return "0~12개월"
            elif age == 2:
                return "13~24개월"
            elif age >= 3:
                return "25~36개월"

        # 3. 특정 키워드
        if any(w in combined for w in ["모유", "베이비", "기어다니는", "신생아", "이유식", "마사지", "0~12", "0~6"]):
            return "0~12개월"
        elif any(w in combined for w in ["돌 ", "아장아장", "걸음마", "오감", "13~24"]):
            return "13~24개월"
        elif any(w in combined for w in ["두돌", "신체놀이", "3D펜", "과학놀이", "25~36"]):
            return "25~36개월"

        return "0~36개월 공통"

    def _clean_capacity_text(self, raw_cap: str, status: str) -> str:
        if not raw_cap:
            return "선착순 모집"
        cleaned = re.sub(r'(온라인\s*신청하기|대기접수가능|신청하기|마감).*', '', raw_cap).strip()
        if not cleaned:
            cleaned = raw_cap.strip()
        if status == "마감" and "마감" not in cleaned:
            cleaned = f"{cleaned} (마감)"
        return cleaned

    def _clean_fee_text(self, raw_fee: str) -> str:
        if not raw_fee or raw_fee.strip() in ["원", "0원", "무료", ""]:
            return "무료"
        return raw_fee.strip()

    def _fetch_detail_info(self, detail_url: str) -> Dict[str, str]:
        """개별 상세페이지의 테이블 정보 파싱"""
        details = {}
        try:
            page_html = self._fetch_html(detail_url)
            soup = BeautifulSoup(page_html, "html.parser")
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

    def _scrape_play_programs(self) -> List[Dict[str, Any]]:
        """꾸미팡팡 공동육아방 놀이프로그램 게시판(pno=041603)에서 최신 월별 1,2,3호점 이미지 파싱"""
        items = []
        try:
            board_url = "https://www.gjcare.go.kr/html/sub/index.php?pno=041603"
            page_html = self._fetch_html(board_url)
            soup = BeautifulSoup(page_html, "html.parser")

            # 게시판 글 목록 탐색 (onclick="_viewLink('1121', 'O')")
            for tr in soup.find_all("tr"):
                a_tag = tr.find("a", onclick=lambda o: o and "_viewLink" in o)
                if not a_tag:
                    continue

                onclick_val = a_tag.get("onclick", "")
                m = re.search(r"_viewLink\s*\(\s*['\"](\d+)['\"]", onclick_val)
                if not m:
                    continue

                board_idx = m.group(1)
                article_title = a_tag.get_text(strip=True)
                
                # 최신 월 놀이프로그램인지 확인 (예: 2026년 꾸미팡팡 공동육아방 9월 놀이프로그램 안내)
                m_month = re.search(r'(\d+)월\s*놀이프로그램', article_title)
                month_label = f"{m_month.group(1)}월" if m_month else "월별"

                detail_url = f"https://www.gjcare.go.kr/html/sub/index.php?pno=041603&mode=view&board_idx={board_idx}&page=1"
                article_html = self._fetch_html(detail_url)
                art_soup = BeautifulSoup(article_html, "html.parser")

                # 본문 내 첨부 이미지 추출
                raw_imgs = art_soup.find_all("img")
                content_imgs = []
                for img in raw_imgs:
                    src = img.get("src", "")
                    if "cheditor" in src or "attach" in src or "upload" in src:
                        if src.startswith("/"):
                            content_imgs.append(f"https://www.gjcare.go.kr{src}")
                        elif src.startswith("http"):
                            content_imgs.append(src)
                        else:
                            content_imgs.append(f"https://www.gjcare.go.kr/{src}")

                # 1호점(능동), 2호점(중곡동), 3호점(군자동) 순서 매핑
                branches = [
                    ("1호점(능동)", "광진구 천호대로 122길 30 1층 (능동)", "https://www.gjcare.go.kr/html/sub/index.php?pno=041604"),
                    ("2호점(중곡동)", "광진구 능동로 400 보건복지행정타운 별관 3층", "https://www.gjcare.go.kr/html/sub/index.php?pno=041605"),
                    ("3호점(군자동)", "광진구 동일로 56가길 31 3층 (군자동)", "https://www.gjcare.go.kr/html/sub/index.php?pno=041800")
                ]

                for idx, (b_name, b_loc, b_url) in enumerate(branches):
                    img_url = content_imgs[idx] if idx < len(content_imgs) else None
                    items.append({
                        "institution_name": f"광진구육아종합지원센터 ({b_name})",
                        "district": "광진구",
                        "category": "공공놀이터/키즈카페",
                        "title": f"[공동육아방] 꾸미팡팡 {b_name} {month_label} 놀이프로그램 일정 안내",
                        "target_age_group": "0~36개월 공통",
                        "target_desc": "광진구 관내 0~36개월 영아 및 동반 보호자",
                        "apply_start_at": "매주 월요일 09:00",
                        "apply_end_at": "이용일 전날 24:00까지",
                        "event_date_desc": f"{month_label} 평일 상시 (1회차 09:30, 2회차 13:00, 3회차 15:30)",
                        "capacity_info": "회차당 3가족 (최대 6명, 선착순)",
                        "fee": "무료",
                        "location": b_loc,
                        "status": "접수중",
                        "detail_type": "POSTER_IMAGE" if img_url else "TABLE_TEXT",
                        "image_url": img_url,
                        "detail_content": json.dumps({
                            "시설명": f"꾸미팡팡 공동육아방 {b_name}",
                            "위치": b_loc,
                            "프로그램": f"{month_label} 신체/오감/미술/음악 테마 놀이프로그램 (포스터 이미지 참조)",
                            "정기예약오픈": "매주 월요일 오전 09:00에 차주 이용분 오픈",
                            "예약/취소규칙": "이용 전날 24시까지 온라인 취소 (당일 10시까지 유선 취소 시 벌점 없음)",
                            "신청방법": "광진구육아종합지원센터 홈페이지 온라인 신청 (미달 시 당일 전화 예약)"
                        }, ensure_ascii=False),
                        "origin_url": b_url
                    })

                # 최신 글 1개(당월)만 처리하고 종료
                break
        except Exception as e:
            logger.error(f"Error scraping play programs: {e}")

        return items

    async def scrape(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        target_menus = [
            ("060801", "행사"),
            ("060201", "부모교육")
        ]

        # 1. 행사 및 부모교육 크롤링
        for pno, menu_name in target_menus:
            list_url = f"https://www.gjcare.go.kr/html/sub/index.php?pno={pno}"
            try:
                page_html = self._fetch_html(list_url)
                soup = BeautifulSoup(page_html, "html.parser")
                
                # 1) 행사 탭(갤러리 카드형 리스트) 처리
                gallery_items = soup.select("ul.gallery_list li, .program_list li, .sub_con_box ul li")
                for li in gallery_items:
                    a_view = li.find("a", href=lambda h: h and "mode=view" in h and "idx=" in h)
                    if not a_view:
                        continue
                    
                    href = a_view.get("href", "")
                    clean_href = href.replace("../../", "").lstrip("/")
                    detail_url = f"https://www.gjcare.go.kr/{clean_href}"
                    
                    if any(r["origin_url"] == detail_url for r in results):
                        continue

                    title = a_view.get_text(strip=True)
                    if not title or len(title) < 2:
                        span = li.find("span")
                        title = span.get_text(strip=True) if span else "광진구육아종합지원센터 프로그램"

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

                    detail_data = self._fetch_detail_info(detail_url)
                    target_desc = detail_data.get("대상", "광진구 관내 영유아 및 양육자")

                    if not is_for_parent_and_child(title, target_desc, str(detail_data)):
                        logger.info(f"Filtered out non-parent program: {title}")
                        continue

                    exact_apply_period = clean_datetime_text(detail_data.get("신청기간", period))
                    apply_start = exact_apply_period.split("~")[0].strip() if "~" in exact_apply_period else exact_apply_period
                    apply_end = exact_apply_period.split("~")[1].strip() if "~" in exact_apply_period else ""
                    event_date = clean_datetime_text(detail_data.get("일시", period or "상세 페이지 참조"))

                    raw_cap = detail_data.get("신청인원 / 정원", detail_data.get("신청인원/정원", detail_data.get("정원", "")))
                    capacity = self._clean_capacity_text(raw_cap, status)
                    fee = self._clean_fee_text(detail_data.get("교육비", detail_data.get("참가비", detail_data.get("수강료", "무료"))))

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
                        "fee": fee,
                        "location": "광진구육아종합지원센터 (군자동)",
                        "status": status,
                        "detail_type": "TABLE_TEXT",
                        "image_url": None,
                        "detail_content": json.dumps(cleaned_detail_data, ensure_ascii=False) if cleaned_detail_data else None,
                        "origin_url": detail_url
                    })

                # 2) 부모교육 탭(테이블 게시판 형태) 처리
                table_rows = soup.select("table tbody tr, table tr")
                for tr in table_rows:
                    tds = tr.find_all("td")
                    if not tds or len(tds) < 3:
                        continue
                    
                    a_view = tr.find("a", href=lambda h: h and "mode=view" in h and "idx=" in h)
                    if not a_view:
                        continue

                    title = a_view.get_text(strip=True)
                    if title in ["신청", "마감", "대기", "취소", "접수"] or len(title) < 2:
                        continue

                    href = a_view.get("href", "")
                    clean_href = href.replace("../../", "").lstrip("/")
                    detail_url = f"https://www.gjcare.go.kr/{clean_href}"

                    if any(r["origin_url"] == detail_url for r in results):
                        continue

                    row_text = tr.get_text()
                    status = "접수중" if "신청" in row_text else ("마감" if "마감" in row_text else "접수예정")

                    detail_data = self._fetch_detail_info(detail_url)
                    target_desc = detail_data.get("대상", "광진구 관내 영유아 및 양육자")

                    if not is_for_parent_and_child(title, target_desc, str(detail_data)):
                        logger.info(f"Filtered out non-parent program: {title}")
                        continue

                    exact_apply_period = clean_datetime_text(detail_data.get("신청기간", ""))
                    apply_start = exact_apply_period.split("~")[0].strip() if "~" in exact_apply_period else exact_apply_period
                    apply_end = exact_apply_period.split("~")[1].strip() if "~" in exact_apply_period else ""
                    event_date = clean_datetime_text(detail_data.get("일시", "상세 페이지 참조"))

                    raw_cap = detail_data.get("교육정원", detail_data.get("신청인원 / 정원", detail_data.get("정원", "")))
                    capacity = self._clean_capacity_text(raw_cap, status)
                    fee = self._clean_fee_text(detail_data.get("교육비", detail_data.get("참가비", detail_data.get("수강료", "무료"))))

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
                        "fee": fee,
                        "location": "광진구육아종합지원센터 (군자동)",
                        "status": status,
                        "detail_type": "TABLE_TEXT",
                        "image_url": None,
                        "detail_content": json.dumps(cleaned_detail_data, ensure_ascii=False) if cleaned_detail_data else None,
                        "origin_url": detail_url
                    })

            except Exception as e:
                logger.error(f"Gwangjin care live scrape error for pno={pno}: {e}")

        # 2. 꾸미팡팡 공동육아방 1, 2, 3호점 월별 놀이프로그램(이미지 포함) 추가
        play_items = self._scrape_play_programs()
        results.extend(play_items)

        logger.info(f"Gwangjin care live scraped {len(results)} actual programs.")
        return results
