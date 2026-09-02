import re
import json
import logging
import urllib.request
import ssl
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from app.scrapers.base import BaseScraper, clean_datetime_text, is_for_parent_and_child

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

    def _fetch_html(self, url: str) -> str:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8"
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=self._get_ssl_context(), timeout=10) as response:
            raw_bytes = response.read()
            return raw_bytes.decode("utf-8", errors="ignore")

    def _determine_age_group(self, title: str, desc: str = "") -> str:
        combined = f"{title} {desc}"
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

        if any(w in combined for w in ["0~12", "영아", "모유", "베이비", "아가", "신생아"]):
            return "0~12개월"
        elif any(w in combined for w in ["12~24", "13~24", "돌", "아장아장", "걸음마", "오감"]):
            return "13~24개월"
        elif any(w in combined for w in ["24~36", "25~36", "두돌", "3세", "신체놀이"]):
            return "25~36개월"
        return "0~36개월 공통"

    async def scrape(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        # 1. 광진구가족센터 공동육아나눔터 (자양동, 구의동) 실시간 크롤링
        try:
            list_url = "https://gwangjin.familynet.or.kr/center/lay1/bbs/S295T315C319/A/12/list.do"
            list_html = self._fetch_html(list_url)
            soup = BeautifulSoup(list_html, "html.parser")

            seen_branches = set()

            for a in soup.find_all("a"):
                txt = a.get_text(strip=True)
                href = a.get("href", "")
                
                # 공지 제외, [자양동...] / [구의동...] 프로그램 안내 글 매칭
                if "공동육아나눔터" in txt and "프로그램 안내" in txt and "view.do" in href:
                    # 지점명 파악 (자양동, 구의동)
                    branch_name = "자양동" if "자양동" in txt else ("구의동" if "구의동" in txt else "광진구")
                    
                    # 이미 최신 월 공고를 수집한 지점은 건너뜀
                    if branch_name in seen_branches:
                        continue
                    seen_branches.add(branch_name)

                    # 상세 URL 구성
                    if href.startswith("/"):
                        detail_url = f"https://gwangjin.familynet.or.kr{href}"
                    elif href.startswith("http"):
                        detail_url = href
                    else:
                        detail_url = f"https://gwangjin.familynet.or.kr/center/lay1/bbs/S295T315C319/A/12/{href}"

                    detail_html = self._fetch_html(detail_url)
                    dsoup = BeautifulSoup(detail_html, "html.parser")

                    # 1) 본문 포스터 이미지 추출 (upload/editor 우선)
                    img_url = None
                    for img in dsoup.find_all("img"):
                        src = img.get("src", "")
                        if "editor" in src:
                            img_url = src if src.startswith("http") else f"https://gwangjin.familynet.or.kr{src}"
                            break
                    if not img_url:
                        for img in dsoup.find_all("img"):
                            src = img.get("src", "")
                            if any(ext in src.lower() for ext in [".jpg", ".png", ".jpeg"]) and "board/2022" not in src and "header" not in src and "sub" not in src:
                                img_url = src if src.startswith("http") else f"https://gwangjin.familynet.or.kr{src}"
                                break

                    # 2) 네이버 예약 / 네이버 폼 신청 링크 추출
                    naver_apply_url = None
                    for da in dsoup.find_all("a"):
                        dhref = da.get("href", "")
                        if any(k in dhref for k in ["booking.naver.com", "naver.me", "form.naver.com", "forms.gle"]):
                            naver_apply_url = dhref
                            break

                    # 본문 내 텍스트에서 링크 정규식 검색 (a 태그 없이 텍스트로만 링크가 적혀 있는 경우 대응)
                    if not naver_apply_url:
                        m_url = re.search(r'https?://(booking\.naver\.com[^\s<>"\']+|naver\.me/[^\s<>"\']+|form\.naver\.com[^\s<>"\']+)', detail_html)
                        if m_url:
                            naver_apply_url = m_url.group(0)

                    # 3) 지점별 메타 정보 및 위치
                    if branch_name == "자양동":
                        loc = "광진구가족센터 자양동 공동육아나눔터 (자양번영로 44-1 2층)"
                        default_apply = "https://booking.naver.com/booking/12/bizes/1014170"
                    else:
                        loc = "광진구가족센터 구의동 공동육아나눔터 (아차산로 58길 18 2층)"
                        default_apply = "https://gwangjin.familynet.or.kr/center/lay1/bbs/S295T315C319/A/12/list.do"

                    apply_url = naver_apply_url or default_apply

                    # 4) 본문 요약
                    table = dsoup.find("table")
                    body_text = table.get_text("\n", strip=True) if table else txt
                    
                    # 월 추출
                    m_m = re.search(r'(\d+)월', txt)
                    month_str = f"{m_m.group(1)}월" if m_m else "월별"

                    results.append({
                        "institution_name": f"광진구가족센터 ({branch_name} 공동육아나눔터)",
                        "district": "광진구",
                        "category": "가족센터",
                        "title": f"[공동육아나눔터] {branch_name} 공동육아나눔터 {month_str} 프로그램 및 오감놀이 (네이버 신청)",
                        "target_age_group": "0~36개월 공통",
                        "target_desc": "광진구 거주 0~36개월 영유아 및 양육 보호자",
                        "apply_start_at": "상시 접수 (네이버 예약/폼)",
                        "apply_end_at": "회차별 선착순 마감시까지",
                        "event_date_desc": f"{month_str} 평일 및 토요일 (회차별 일정 안내문 참조)",
                        "capacity_info": "회차/프로그램별 선착순 (네이버 예약)",
                        "fee": "무료",
                        "location": loc,
                        "status": "접수중",
                        "detail_type": "POSTER_IMAGE" if img_url else "TABLE_TEXT",
                        "image_url": img_url,
                        "detail_content": json.dumps({
                            "시설명": f"광진구가족센터 {branch_name} 공동육아나눔터",
                            "위치": loc,
                            "신청방식": "홈페이지 신청 대신 네이버 예약/네이버 폼으로 다이렉트 신청",
                            "주요내용": f"{month_str} 부모-자녀 애착증진 오감놀이, 유리드믹스 음악놀이, 상시 열린 놀이공간 이용",
                            "네이버신청링크": apply_url,
                            "이용요금": "무료"
                        }, ensure_ascii=False),
                        "origin_url": apply_url
                    })

        except Exception as e:
            logger.error(f"Gwangjin familynet live scrape error: {e}")

        # 2. 성동구가족센터 공동육아나눔터
        results.append({
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
        })

        logger.info(f"FamilyNet live scraped {len(results)} programs.")
        return results
