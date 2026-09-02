import re
import ssl
import json
import logging
import urllib.request
from typing import List, Dict, Any, Tuple
from app.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class GwangjinSportsScraper(BaseScraper):
    @property
    def name(self) -> str:
        return "광진구시설관리공단"

    @property
    def district(self) -> str:
        return "광진구"

    @property
    def category(self) -> str:
        return "구민체육센터"

    def _get_ssl_context(self):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def _is_valid_infant_program(self, class_nm: str, target_age: str) -> Tuple[bool, str]:
        """
        0~36개월 영유아 및 부모 동반 강좌만 엄격하게 선별.
        20~21년생(만 5~6세), 5~7세, 초등학생 등 36개월 초과 대상은 철저히 배제.
        """
        combined = f"{class_nm} {target_age}".strip()

        # 1. 36개월 초과 명시된 나이/출생년도 필터링
        exclude_patterns = [
            r'20[-~]21년생', r'20[-~]22년생', r'18[-~]21년생', r'19[-~]21년생', r'18[-~]20년생', r'16[-~]19년생',
            r'5[-~]7세', r'6[-~]7세', r'5[-~]6세', r'6[-~]8세', r'7[-~]9세', r'8[-~]11세',
            r'만5세', r'만6세', r'만5[-~]6세', r'43개월[-~]5세', r'48개월[-~]',
            r'초1', r'초2', r'초3', r'초등', r'중학', r'중고', r'성인', r'주부', r'실버', r'헬스', r'요가', r'필라테스'
        ]

        # 영아/부모동반 명시 여부
        is_parent_infant = any(k in combined for k in ['12-20개월', '12~20', '15-24', '13-24', '0~12', '엄마랑', '노리야', '아이쿵', '키리키', '베이비'])
        is_toddler_parent = ('보호자+' in target_age or '아이랑 함께' in class_nm or '엄마랑' in class_nm) and any(m in target_age for m in ['20-48', '24-48', '20~48', '24~48'])

        for pat in exclude_patterns:
            if re.search(pat, target_age) or re.search(pat, class_nm):
                if not (is_parent_infant or is_toddler_parent):
                    return False, ""

        # 2. 유효한 0~36개월 강좌 매칭 및 연령대 반환
        if any(w in combined for w in ['12-20', '15-24', '13~24']):
            return True, "13~24개월"
        if any(w in combined for w in ['0~12', '0~6', '베이비', '영아']):
            return True, "0~12개월"
        if is_toddler_parent or any(w in target_age for w in ['22-23년생', '23년생', '24년생']):
            return True, "25~36개월"
        if is_parent_infant or any(k in class_nm for k in ['오감친구', '꼬물꼬물아이쿵', '키리키영어놀이터', '노리야']):
            return True, "0~36개월 공통"

        return False, ""

    async def scrape(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        centers = [
            ("GWANGJIN01", "광진구민체육센터", "광진구 구천면로 14 (광장동)", "https://booking.gwangjin.or.kr/fmcs/2?company_code=GWANGJIN01"),
            ("GWANGJIN02", "중곡문화체육센터", "광진구 능동로 400 (중곡동)", "https://booking.gwangjin.or.kr/fmcs/2?company_code=GWANGJIN02"),
            ("GWANGJIN03", "광진문화예술회관", "광진구 능동로 76 (자양동)", "https://booking.gwangjin.or.kr/fmcs/2?company_code=GWANGJIN03")
        ]

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Referer": "https://booking.gwangjin.or.kr/fmcs/2",
            "Accept": "application/json, text/javascript, */*; q=0.01"
        }

        for code, center_name, loc, direct_booking_url in centers:
            list_url = f"https://booking.gwangjin.or.kr/rest/lecture/list?company_code={code}&page=1&page_size=500"
            try:
                req = urllib.request.Request(list_url, headers=headers)
                with urllib.request.urlopen(req, context=self._get_ssl_context(), timeout=10) as res:
                    data = json.loads(res.read().decode("utf-8"))

                for it in data:
                    class_nm = (it.get("class_nm") or "").strip()
                    target_age = (it.get("target_age_name") or "").strip()
                    cat1 = (it.get("category1") or "").strip()
                    cat2 = (it.get("category2") or "").strip()

                    is_valid, age_group = self._is_valid_infant_program(class_nm, target_age)
                    if not is_valid:
                        continue

                    fee_raw = it.get("course_fee") or "0"
                    fee_str = f"{fee_raw}원" if fee_raw and fee_raw != "0" else "무료"

                    day_nm = it.get("train_day_nm") or ""
                    stime = it.get("train_stime") or ""
                    etime = it.get("train_etime") or ""
                    time_desc = f"매주 {day_nm}요일 {stime} ~ {etime}" if day_nm and stime else "정규 강좌 시간표 참조"

                    capa = it.get("capa") or ""
                    reg = it.get("reg_person") or ""
                    cap_desc = f"{reg}/{capa}명" if capa else "선착순 모집"

                    target_desc = target_age if target_age else "0~36개월 영유아 및 보호자"

                    results.append({
                        "institution_name": f"광진구시설관리공단 ({center_name})",
                        "district": "광진구",
                        "category": "구민체육센터",
                        "title": f"[{center_name}] {class_nm}",
                        "target_age_group": age_group,
                        "target_desc": target_desc,
                        "apply_start_at": "매월 20일경 정기 접수 오픈",
                        "apply_end_at": "마감시까지",
                        "event_date_desc": time_desc,
                        "capacity_info": f"정원: {cap_desc}",
                        "fee": fee_str,
                        "location": loc,
                        "status": "접수중",
                        "detail_type": "TABLE_TEXT",
                        "image_url": None,
                        "detail_content": json.dumps({
                            "강좌명": class_nm,
                            "운영센터": center_name,
                            "카테고리": f"{cat1} > {cat2}" if cat2 else cat1,
                            "수강대상": target_desc,
                            "수업시간": time_desc,
                            "수강료": fee_str,
                            "강사명": it.get("teacher_name") or "전문 강사진",
                            "신청안내": "광진구통합예약시스템(booking.gwangjin.or.kr) 수강신청 다이렉트 페이지에서 온라인 결제 접수"
                        }, ensure_ascii=False),
                        "origin_url": direct_booking_url
                    })

            except Exception as e:
                logger.error(f"Failed to scrape sports center {center_name} ({code}): {e}")

        logger.info(f"GwangjinSportsScraper scraped {len(results)} infant programs.")
        return results
