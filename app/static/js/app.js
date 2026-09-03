/**
 * 아이랑 모아 - 프론트엔드 애플리케이션 스크립트
 */

document.addEventListener('DOMContentLoaded', () => {
    // 상태 관리
    const state = {
        programs: [],
        filteredPrograms: [],
        currentView: 'list', // 'list' | 'calendar'
        filters: {
            district: '전체',
            age_group: '전체',
            category: '전체',
            status: '전체',
            fee: '전체', // '전체' | '무료' | '유료'
            babyBirthdate: null,
            babyMonths: null,
            q: ''
        },
        sortBy: 'status', // 'status' | 'free_first' | 'paid_first' | 'title'
        currentPage: 1,
        pageSize: 12,
        currentMonth: new Date(2026, 8, 1), // 2026년 9월 기본
        selectedProgram: null
    };

    // DOM 요소
    const elements = {
        programsGrid: document.getElementById('programs-grid'),
        paginationContainer: document.getElementById('pagination-container'),
        emptyState: document.getElementById('empty-state'),
        resultTotalCount: document.getElementById('result-total-count'),
        searchInput: document.getElementById('search-input'),
        searchClear: document.getElementById('search-clear'),
        btnResetFilters: document.getElementById('btn-reset-filters'),
        btnSync: document.getElementById('btn-sync'),
        btnListView: document.getElementById('view-list-btn'),
        btnCalView: document.getElementById('view-calendar-btn'),
        listViewContainer: document.getElementById('list-view-container'),
        calViewContainer: document.getElementById('calendar-view-container'),
        calMonthTitle: document.getElementById('cal-month-title'),
        calDaysGrid: document.getElementById('calendar-days'),
        calPrevBtn: document.getElementById('cal-prev'),
        calNextBtn: document.getElementById('cal-next'),
        calSelectedInfo: document.getElementById('calendar-selected-info'),
        
        // 아이 생년월일 맞춤 필터
        babyBirthdate: document.getElementById('baby-birthdate'),
        babyCalcResult: document.getElementById('baby-calc-result'),
        babyMonthsText: document.getElementById('baby-months-text'),
        btnClearBabyDate: document.getElementById('btn-clear-baby-date'),
        sortSelect: document.getElementById('sort-select'),

        // 통계 배너
        statOpen: document.getElementById('stat-open'),
        statUpcoming: document.getElementById('stat-upcoming'),
        statGwangjin: document.getElementById('stat-gwangjin'),
        statSeongdong: document.getElementById('stat-seongdong'),

        // 모달
        modal: document.getElementById('program-modal'),
        modalCloseBtn: document.getElementById('modal-close-btn'),
        modalBadges: document.getElementById('modal-badges'),
        modalTitle: document.getElementById('modal-title'),
        modalMetaBar: document.getElementById('modal-meta-bar'),
        modalBody: document.getElementById('modal-body'),
        btnModalApply: document.getElementById('btn-modal-apply'),
        btnCopyLink: document.getElementById('btn-copy-link'),
        toast: document.getElementById('toast-message')
    };

    // 초기화
    init();

    async function init() {
        bindEvents();
        await fetchStats();
        await fetchPrograms();
    }

    // 이벤트 바인딩
    function bindEvents() {
        // 검색 입력
        elements.searchInput.addEventListener('input', (e) => {
            state.filters.q = e.target.value.trim();
            elements.searchClear.style.display = state.filters.q ? 'block' : 'none';
            applyFilters();
        });

        elements.searchClear.addEventListener('click', () => {
            elements.searchInput.value = '';
            state.filters.q = '';
            elements.searchClear.style.display = 'none';
            applyFilters();
        });

        // 칩스 필터 클릭 이벤트
        ['district', 'age', 'fee', 'category', 'status'].forEach(filterType => {
            const containerId = `filter-${filterType}`;
            const container = document.getElementById(containerId);
            if (!container) return;

            container.addEventListener('click', (e) => {
                const chipBtn = e.target.closest('.chip');
                if (chipBtn) {
                    container.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
                    chipBtn.classList.add('active');

                    const stateKey = filterType === 'age' ? 'age_group' : filterType;
                    state.filters[stateKey] = chipBtn.getAttribute('data-value');
                    applyFilters();
                }
            });
        });

        // 아이 생년월일 입력 이벤트
        if (elements.babyBirthdate) {
            elements.babyBirthdate.addEventListener('change', (e) => {
                const bdate = e.target.value;
                if (bdate) {
                    const months = calculateBabyMonths(bdate);
                    state.filters.babyBirthdate = bdate;
                    state.filters.babyMonths = months;

                    const years = Math.floor(months / 12);
                    const remMonths = months % 12;
                    const ageDesc = years > 0 ? `만 ${years}세 (${months}개월)` : `생후 ${months}개월`;
                    
                    elements.babyMonthsText.textContent = `👶 ${ageDesc} 맞춤 보기`;
                    elements.babyCalcResult.style.display = 'flex';
                } else {
                    clearBabyFilter();
                }
                applyFilters();
            });
        }

        // 아이 생년월일 필터 해제 버튼
        if (elements.btnClearBabyDate) {
            elements.btnClearBabyDate.addEventListener('click', () => {
                clearBabyFilter();
                applyFilters();
            });
        }

        // 정렬 선택 변경 이벤트
        if (elements.sortSelect) {
            elements.sortSelect.addEventListener('change', (e) => {
                state.sortBy = e.target.value;
                applyFilters();
            });
        }

        // 필터 초기화 버튼
        if (elements.btnResetFilters) {
            elements.btnResetFilters.addEventListener('click', resetFilters);
        }

        // 뷰 전환 버튼
        elements.btnListView.addEventListener('click', () => switchView('list'));
        elements.btnCalView.addEventListener('click', () => switchView('calendar'));

        // 캘린더 월 이동
        elements.calPrevBtn.addEventListener('click', () => {
            state.currentMonth.setMonth(state.currentMonth.getMonth() - 1);
            renderCalendar();
        });

        elements.calNextBtn.addEventListener('click', () => {
            state.currentMonth.setMonth(state.currentMonth.getMonth() + 1);
            renderCalendar();
        });

        // 동기화 버튼
        elements.btnSync.addEventListener('click', handleSync);

        // 모달 닫기
        elements.modalCloseBtn.addEventListener('click', closeModal);
        elements.modal.addEventListener('click', (e) => {
            if (e.target === elements.modal) closeModal();
        });
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (lightboxModal && lightboxModal.style.display !== 'none') {
                    closeLightbox();
                } else if (elements.modal.style.display !== 'none') {
                    closeModal();
                }
            }
        });

        // 링크 복사
        elements.btnCopyLink.addEventListener('click', () => {
            if (state.selectedProgram) {
                navigator.clipboard.writeText(state.selectedProgram.origin_url).then(() => {
                    showToast('신청 페이지 링크가 클립보드에 복사되었습니다.');
                });
            }
        });
    }

    // 아이 생후 개월 수 계산 (현재 날짜 기준)
    function calculateBabyMonths(birthdateStr) {
        const birthDate = new Date(birthdateStr);
        const today = new Date(); // 현재 날짜

        let months = (today.getFullYear() - birthDate.getFullYear()) * 12;
        months += today.getMonth() - birthDate.getMonth();
        if (today.getDate() < birthDate.getDate()) {
            months -= 1;
        }
        return Math.max(0, months);
    }

    // 아이 생년월일 필터 해제
    function clearBabyFilter() {
        if (elements.babyBirthdate) {
            elements.babyBirthdate.value = '';
            elements.babyBirthdate.type = 'text';
        }
        if (elements.babyCalcResult) elements.babyCalcResult.style.display = 'none';
        state.filters.babyBirthdate = null;
        state.filters.babyMonths = null;
    }

    // 아이 월령에 맞는 프로그램인지 정밀 판별
    function isProgramEligibleForBabyMonths(item, babyMonths) {
        if (babyMonths === null || isNaN(babyMonths)) return true;

        const combined = `${item.title} ${item.target_desc || ''} ${item.target_age_group || ''}`;

        // 1. 구체적 개월 수 범위 매칭 (예: 12~20개월, 20-48개월, 6-12개월, 17-32개월)
        const matchRange = combined.match(/(\d+)\s*[-~]\s*(\d+)\s*개월/);
        if (matchRange) {
            const startM = parseInt(matchRange[1], 10);
            const endM = parseInt(matchRange[2], 10);
            return babyMonths >= startM && babyMonths <= endM;
        }

        // 2. 단일 기준 매칭
        if (combined.includes('0~12개월') || combined.includes('영아')) {
            return babyMonths <= 12;
        }
        if (combined.includes('13~24개월') || combined.includes('걸음마')) {
            return babyMonths >= 12 && babyMonths <= 24;
        }
        if (combined.includes('25~36개월') || combined.includes('두돌')) {
            return babyMonths >= 24 && babyMonths <= 36;
        }
        if (combined.includes('공통') || combined.includes('0~36개월')) {
            return babyMonths <= 36;
        }

        // 기본적으로 36개월 이하 아기 모두 수용
        return babyMonths <= 36;
    }

    // 비용(무료/유료) 판별
    function isFeeMatch(itemFee, filterValue) {
        if (filterValue === '전체') return true;
        const isFree = !itemFee || itemFee.includes('무료') || itemFee.trim() === '0원' || itemFee.trim() === '원' || itemFee.trim() === '';
        return filterValue === '무료' ? isFree : !isFree;
    }

    // 뷰 전환
    function switchView(viewName) {
        state.currentView = viewName;
        if (viewName === 'list') {
            elements.btnListView.classList.add('active');
            elements.btnCalView.classList.remove('active');
            elements.listViewContainer.style.display = 'block';
            elements.calViewContainer.style.display = 'none';
        } else {
            elements.btnCalView.classList.add('active');
            elements.btnListView.classList.remove('active');
            elements.listViewContainer.style.display = 'none';
            elements.calViewContainer.style.display = 'block';
            renderCalendar();
        }
    }

    // 필터 초기화
    function resetFilters() {
        state.filters = {
            district: '전체',
            age_group: '전체',
            category: '전체',
            status: '전체',
            fee: '전체',
            babyBirthdate: null,
            babyMonths: null,
            q: ''
        };
        elements.searchInput.value = '';
        elements.searchClear.style.display = 'none';
        clearBabyFilter();

        state.sortBy = 'status';
        if (elements.sortSelect) elements.sortSelect.value = 'status';

        ['district', 'age', 'fee', 'category', 'status'].forEach(filterType => {
            const container = document.getElementById(`filter-${filterType}`);
            if (container) {
                container.querySelectorAll('.chip').forEach(c => {
                    c.classList.toggle('active', c.getAttribute('data-value') === '전체');
                });
            }
        });

        applyFilters();
    }

    // 데이터 가져오기
    async function fetchPrograms() {
        try {
            const res = await fetch('/api/programs');
            if (!res.ok) throw new Error('데이터를 불러오지 못했습니다.');
            state.programs = await res.json();
            applyFilters();
        } catch (error) {
            console.error(error);
            showToast('프로그램 데이터를 가져오는 중 오류가 발생했습니다.');
        }
    }

    async function fetchStats() {
        try {
            const res = await fetch('/api/stats');
            if (res.ok) {
                const stats = await res.json();
                elements.statOpen.textContent = `${stats.open}건`;
                elements.statUpcoming.textContent = `${stats.upcoming}건`;
                elements.statGwangjin.textContent = `${stats.gwangjin}건`;
                elements.statSeongdong.textContent = `${stats.seongdong}건`;
            }
        } catch (e) {
            console.warn('통계 데이터 로드 실패', e);
        }
    }

    // 동기화 트리거
    async function handleSync() {
        elements.btnSync.disabled = true;
        elements.btnSync.innerHTML = '<span class="icon">⏳</span> 갱신 중...';
        showToast('최신 프로그램 정보를 수집하고 있습니다...');

        try {
            const res = await fetch('/api/sync', { method: 'POST' });
            const data = await res.json();
            showToast(data.message || '데이터 갱신이 완료되었습니다.');
            await fetchStats();
            await fetchPrograms();
        } catch (e) {
            showToast('동기화 중 오류가 발생했습니다.');
        } finally {
            elements.btnSync.disabled = false;
            elements.btnSync.innerHTML = '<span class="icon">🔄</span> 최신 정보 갱신';
        }
    }

    // 클라이언트 사이드 필터 및 정렬 적용
    function applyFilters(resetPage = true) {
        if (resetPage) {
            state.currentPage = 1;
        }

        let list = state.programs.filter(item => {
            // 1. 자치구
            if (state.filters.district !== '전체') {
                if (!item.district.includes(state.filters.district)) return false;
            }
            // 2. 기관 카테고리
            if (state.filters.category !== '전체') {
                if (item.category !== state.filters.category) return false;
            }
            // 3. 연령 칩스 필터
            if (state.filters.age_group !== '전체') {
                const isMatch = item.target_age_group === state.filters.age_group ||
                                item.target_age_group.includes('공통') ||
                                (item.target_desc && item.target_desc.includes(state.filters.age_group.replace('개월', '')));
                if (!isMatch) return false;
            }
            // 4. 아이 생년월일 기반 월령 맞춤 필터
            if (state.filters.babyMonths !== null) {
                if (!isProgramEligibleForBabyMonths(item, state.filters.babyMonths)) {
                    return false;
                }
            }
            // 5. 비용 필터 (무료 / 유료)
            if (!isFeeMatch(item.fee, state.filters.fee)) {
                return false;
            }
            // 6. 상태 필터
            if (state.filters.status !== '전체') {
                if (item.status !== state.filters.status) return false;
            }
            // 7. 검색어
            if (state.filters.q) {
                const q = state.filters.q.toLowerCase();
                const content = `${item.title} ${item.institution_name} ${item.target_desc || ''} ${item.location || ''}`.toLowerCase();
                if (!content.includes(q)) return false;
            }
            return true;
        });

        // 정렬 적용
        const statusOrder = { "접수중": 1, "접수예정": 2, "대기접수": 3, "마감": 4, "종료": 5 };
        
        list.sort((a, b) => {
            if (state.sortBy === 'free_first') {
                const aFree = !a.fee || a.fee.includes('무료') ? 0 : 1;
                const bFree = !b.fee || b.fee.includes('무료') ? 0 : 1;
                if (aFree !== bFree) return aFree - bFree;
                return (statusOrder[a.status] || 99) - (statusOrder[b.status] || 99);
            } else if (state.sortBy === 'paid_first') {
                const aFree = !a.fee || a.fee.includes('무료') ? 1 : 0;
                const bFree = !b.fee || b.fee.includes('무료') ? 1 : 0;
                if (aFree !== bFree) return aFree - bFree;
                return (statusOrder[a.status] || 99) - (statusOrder[b.status] || 99);
            } else if (state.sortBy === 'title') {
                return a.title.localeCompare(b.title, 'ko');
            } else {
                // 기본: status
                const orderA = statusOrder[a.status] || 99;
                const orderB = statusOrder[b.status] || 99;
                if (orderA !== orderB) return orderA - orderB;
                return (a.apply_start_at || '9999').localeCompare(b.apply_start_at || '9999');
            }
        });

        state.filteredPrograms = list;

        renderList();
        if (state.currentView === 'calendar') {
            renderCalendar();
        }
    }

    // D-Day 계산 함수 (접수예정 또는 접수중일 때만 계산, 마감/종료는 제외)
    function calculateDDay(applyStartStr, status) {
        if (!applyStartStr || applyStartStr.includes('상시')) return null;
        if (status === '마감' || status === '종료') return null;

        try {
            const dateOnly = applyStartStr.split(' ')[0];
            const targetDate = new Date(dateOnly);
            if (isNaN(targetDate.getTime())) return null;

            const today = new Date();
            today.setHours(0, 0, 0, 0);
            targetDate.setHours(0, 0, 0, 0);

            const diffDays = Math.ceil((targetDate - today) / (1000 * 60 * 60 * 24));
            if (diffDays === 0) return 'D-Day';
            if (diffDays > 0 && diffDays <= 30) return `D-${diffDays}`;
            return null;
        } catch (e) {
            return null;
        }
    }

    // 카드 목록 렌더링 (페이지네이션 적용)
    function renderList() {
        const total = state.filteredPrograms.length;
        elements.resultTotalCount.textContent = total;

        if (total === 0) {
            elements.programsGrid.innerHTML = '';
            elements.emptyState.style.display = 'block';
            if (elements.paginationContainer) {
                elements.paginationContainer.style.display = 'none';
                elements.paginationContainer.innerHTML = '';
            }
            return;
        }

        elements.emptyState.style.display = 'none';

        const totalPages = Math.ceil(total / state.pageSize);
        if (state.currentPage > totalPages) {
            state.currentPage = Math.max(1, totalPages);
        }

        const startIndex = (state.currentPage - 1) * state.pageSize;
        const endIndex = Math.min(startIndex + state.pageSize, total);
        const currentItems = state.filteredPrograms.slice(startIndex, endIndex);

        elements.programsGrid.innerHTML = currentItems.map(prog => {
            const dday = calculateDDay(prog.apply_start_at, prog.status);
            const statusClass = prog.status === '접수중' ? 'open' : (prog.status === '접수예정' ? 'upcoming' : 'closed');

            return `
                <div class="program-card" data-id="${prog.id}">
                    <div class="card-top-bar">
                        <div class="card-tags">
                            <span class="tag-district">${prog.district}</span>
                            <span class="tag-category">${prog.category}</span>
                            <span class="tag-age">${prog.target_age_group || '0~36개월'}</span>
                        </div>
                        <div class="card-status-wrap">
                            <span class="badge-status ${statusClass}">${prog.status}</span>
                            ${dday && prog.status !== '마감' ? `<span class="badge-dday">${dday}</span>` : ''}
                        </div>
                    </div>
                    
                    <div class="card-body">
                        <div class="card-inst-name">${prog.institution_name}</div>
                        <h3 class="card-title">${prog.title}</h3>
                        
                        <div class="card-info-list">
                            <div class="info-item">
                                <span class="lbl">신청기간</span>
                                <span class="val">${prog.apply_start_at || '별도 안내'} ${prog.apply_end_at ? '~ ' + prog.apply_end_at : ''}</span>
                            </div>
                            <div class="info-item">
                                <span class="lbl">진행일시</span>
                                <span class="val">${prog.event_date_desc || '상세정보 참조'}</span>
                            </div>
                            <div class="info-item">
                                <span class="lbl">정원/대상</span>
                                <span class="val">${prog.capacity_info || ''} (${prog.target_desc || '영유아'})</span>
                            </div>
                        </div>
                    </div>

                    <div class="card-footer">
                        <button class="btn btn-outline btn-detail-trigger" data-id="${prog.id}">
                            <i data-lucide="info" class="icon-xs"></i> 자세히 보기
                        </button>
                        <a href="${prog.origin_url}" target="_blank" rel="noopener noreferrer" class="btn btn-primary" onclick="event.stopPropagation();">
                            신청하기 <i data-lucide="external-link" class="icon-xs"></i>
                        </a>
                    </div>
                </div>
            `;
        }).join('');

        // 카드 클릭 시 모달 열기 이벤트
        elements.programsGrid.querySelectorAll('.program-card').forEach(card => {
            card.addEventListener('click', () => {
                const id = parseInt(card.getAttribute('data-id'), 10);
                openDetailModal(id);
            });
        });

        // 페이지네이션 컨트롤 렌더링
        renderPagination(totalPages, total, startIndex + 1, endIndex);

        // Lucide SVG 아이콘 활성화
        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    // 페이지네이션 UI 렌더링
    function renderPagination(totalPages, total, startItemNum, endItemNum) {
        if (!elements.paginationContainer) return;

        if (totalPages <= 1) {
            elements.paginationContainer.style.display = 'none';
            elements.paginationContainer.innerHTML = '';
            return;
        }

        elements.paginationContainer.style.display = 'flex';

        const current = state.currentPage;

        // 페이지 번호 생성 (7개 이하 전체 표시, 초과 시 스마트 윈도우 & ...)
        const pages = [];
        if (totalPages <= 7) {
            for (let i = 1; i <= totalPages; i++) pages.push(i);
        } else {
            pages.push(1);
            if (current > 3) {
                pages.push('...');
            }
            const start = Math.max(2, current - 1);
            const end = Math.min(totalPages - 1, current + 1);
            for (let i = start; i <= end; i++) {
                pages.push(i);
            }
            if (current < totalPages - 2) {
                pages.push('...');
            }
            pages.push(totalPages);
        }

        const pagesHtml = pages.map(p => {
            if (p === '...') {
                return `<span class="page-ellipsis">···</span>`;
            }
            return `<button class="page-btn ${p === current ? 'active' : ''}" data-page="${p}" aria-label="${p}페이지">${p}</button>`;
        }).join('');

        elements.paginationContainer.innerHTML = `
            <div class="pagination-info">
                <span>전체 ${total}개 중 <strong>${startItemNum}-${endItemNum}</strong>개 표시 (${current} / ${totalPages} 페이지)</span>
            </div>
            <nav class="pagination-nav" aria-label="프로그램 페이지 네비게이션">
                <button class="page-nav-btn" id="btn-page-prev" ${current === 1 ? 'disabled' : ''} title="이전 페이지">
                    <i data-lucide="chevron-left" class="icon-xs"></i> <span>이전</span>
                </button>
                <div class="page-numbers">
                    ${pagesHtml}
                </div>
                <button class="page-nav-btn" id="btn-page-next" ${current === totalPages ? 'disabled' : ''} title="다음 페이지">
                    <span>다음</span> <i data-lucide="chevron-right" class="icon-xs"></i>
                </button>
            </nav>
        `;

        // 이전/다음/번호 클릭 이벤트
        const prevBtn = elements.paginationContainer.querySelector('#btn-page-prev');
        if (prevBtn && current > 1) {
            prevBtn.addEventListener('click', () => goToPage(current - 1));
        }

        const nextBtn = elements.paginationContainer.querySelector('#btn-page-next');
        if (nextBtn && current < totalPages) {
            nextBtn.addEventListener('click', () => goToPage(current + 1));
        }

        elements.paginationContainer.querySelectorAll('.page-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const pageNum = parseInt(btn.getAttribute('data-page'), 10);
                if (pageNum && pageNum !== current) {
                    goToPage(pageNum);
                }
            });
        });
    }

    // 지정 페이지로 이동 및 상단 스크롤
    function goToPage(page) {
        state.currentPage = page;
        renderList();
        
        // 목록 상단으로 부드럽게 스크롤
        const target = elements.listViewContainer;
        if (target) {
            const headerHeight = document.querySelector('.app-header')?.offsetHeight || 70;
            const topOffset = target.getBoundingClientRect().top + window.scrollY - headerHeight - 16;
            window.scrollTo({ top: Math.max(0, topOffset), behavior: 'smooth' });
        }
    }


    // 캘린더 렌더링
    function renderCalendar() {
        const year = state.currentMonth.getFullYear();
        const month = state.currentMonth.getMonth(); // 0-indexed

        elements.calMonthTitle.textContent = `${year}년 ${month + 1}월`;

        const firstDayOfMonth = new Date(year, month, 1);
        const lastDayOfMonth = new Date(year, month + 1, 0);

        const startDayIndex = firstDayOfMonth.getDay(); // 0: 일요일
        const totalDays = lastDayOfMonth.getDate();

        const prevMonthLastDay = new Date(year, month, 0).getDate();

        let gridHtml = '';

        // 이전 달 날짜들
        for (let i = startDayIndex - 1; i >= 0; i--) {
            gridHtml += `<div class="cal-day-cell other-month"><span class="cal-day-number">${prevMonthLastDay - i}</span></div>`;
        }

        const today = new Date();

        // 이번 달 날짜들
        for (let day = 1; day <= totalDays; day++) {
            const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
            const isToday = (today.getFullYear() === year && today.getMonth() === month && today.getDate() === day);

            // 해당 일자에 신청 시작하는 프로그램 찾기
            const dayEvents = state.filteredPrograms.filter(p => {
                return p.apply_start_at && p.apply_start_at.startsWith(dateStr);
            });

            // 캘린더 배지용 제목 간소화 함수 ([기관명] 제거 및 글자 수 슬라이스)
            const formatBadgeTitle = (rawTitle) => {
                let clean = rawTitle.replace(/\[.*?\]/g, '').trim();
                return clean || rawTitle;
            };

            gridHtml += `
                <div class="cal-day-cell ${isToday ? 'today' : ''}" data-date="${dateStr}">
                    <span class="cal-day-number">${day}</span>
                    <div class="cal-events-list">
                        ${dayEvents.slice(0, 2).map(ev => `
                            <div class="cal-event-badge ${ev.status === '접수중' ? 'open' : 'upcoming'}" title="${ev.institution_name}: ${ev.title}">
                                ${formatBadgeTitle(ev.title)}
                            </div>
                        `).join('')}
                        ${dayEvents.length > 2 ? `<span class="cal-more-badge">+${dayEvents.length - 2}건</span>` : ''}
                    </div>
                </div>
            `;

        }

        elements.calDaysGrid.innerHTML = gridHtml;

        // 캘린더 날짜 클릭 시 해당 일자 프로그램 표시
        elements.calDaysGrid.querySelectorAll('.cal-day-cell:not(.other-month)').forEach(cell => {
            cell.addEventListener('click', () => {
                const clickedDate = cell.getAttribute('data-date');
                const matched = state.filteredPrograms.filter(p => p.apply_start_at && p.apply_start_at.startsWith(clickedDate));
                if (matched.length > 0) {
                    elements.calSelectedInfo.innerHTML = `
                        <div class="filter-card">
                            <h3 style="margin-bottom:12px;">📅 ${clickedDate} 신청 오픈 프로그램 (${matched.length}건)</h3>
                            <div class="programs-grid">
                                ${matched.map(p => `
                                    <div class="program-card" onclick="window.openModalById(${p.id})">
                                        <div class="card-body">
                                            <span class="tag-category">${p.institution_name}</span>
                                            <h4 class="card-title" style="margin-top:6px;">${p.title}</h4>
                                            <p style="font-size:13px; color:var(--text-muted);">${p.capacity_info || ''} / ${p.target_desc || ''}</p>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    `;
                } else {
                    elements.calSelectedInfo.innerHTML = `
                        <div class="filter-card" style="text-align:center; color:var(--text-muted);">
                            📅 ${clickedDate}에는 예정된 신청 오픈 일정이 없습니다.
                        </div>
                    `;
                }
            });
        });

        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    // 모달 열기 함수
    window.openModalById = function(id) {
        openDetailModal(id);
    };


    function openDetailModal(id) {
        const prog = state.programs.find(p => p.id === id);
        if (!prog) return;

        state.selectedProgram = prog;

        // 배지 설정
        const statusClass = prog.status === '접수중' ? 'open' : (prog.status === '접수예정' ? 'upcoming' : 'closed');
        elements.modalBadges.innerHTML = `
            <span class="tag-district">${prog.district}</span>
            <span class="tag-category">${prog.category}</span>
            <span class="tag-age">${prog.target_age_group || '0~36개월'}</span>
            <span class="badge-status ${statusClass}">${prog.status}</span>
        `;

        elements.modalTitle.textContent = prog.title;
        elements.modalMetaBar.innerHTML = `
            <span>🏢 <strong>${prog.institution_name}</strong></span>
            <span>📍 ${prog.location || '상세 정보 참조'}</span>
            <span>💰 ${prog.fee || '무료'}</span>
        `;

        // 모달 바디 렌더링 (이미지 또는 구조화 테이블)
        let bodyHtml = '';
        if (prog.image_url) {
            bodyHtml += `
                <div class="poster-container" id="modal-poster-wrap" title="클릭하여 고화질 확대 보기">
                    <img src="${prog.image_url}" alt="${prog.title} 홍보 포스터" class="poster-viewer" />
                    <div class="poster-overlay">
                        <span class="poster-zoom-badge">
                            <i data-lucide="zoom-in" class="icon-xs"></i> 🔍 클릭하여 고화질 확대 보기
                        </span>
                    </div>
                </div>
            `;
        }

        let detailObj = {};
        try {
            if (prog.detail_content) {
                detailObj = JSON.parse(prog.detail_content);
            }
        } catch (e) {
            detailObj = { "안내사항": prog.detail_content };
        }

        bodyHtml += `
            <table class="detail-table">
                <tbody>
                    <tr>
                        <th>신청 기간</th>
                        <td><strong>${prog.apply_start_at || '별도 공지'} ~ ${prog.apply_end_at || ''}</strong></td>
                    </tr>
                    <tr>
                        <th>진행 일시</th>
                        <td>${prog.event_date_desc || '상세 일정 참조'}</td>
                    </tr>
                    <tr>
                        <th>모집 대상</th>
                        <td>${prog.target_desc || '0~36개월 영유아 및 보호자'}</td>
                    </tr>
                    <tr>
                        <th>모집 정원</th>
                        <td>${prog.capacity_info || '선착순 마감'}</td>
                    </tr>
                    ${Object.entries(detailObj).map(([k, v]) => `
                        <tr>
                            <th>${k}</th>
                            <td>${v}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;

        elements.modalBody.innerHTML = bodyHtml;
        elements.btnModalApply.href = prog.origin_url;

        // 포스터 이미지 클릭 시 라이트박스 열기
        const posterWrap = elements.modalBody.querySelector('#modal-poster-wrap');
        if (posterWrap) {
            posterWrap.addEventListener('click', () => {
                openLightbox(prog.image_url, prog.title);
            });
        }

        // 해당 프로그램 후기 불러오기
        fetchReviews(prog.id);

        elements.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    function closeModal() {
        elements.modal.style.display = 'none';
        document.body.style.overflow = '';
        state.selectedProgram = null;
    }

    // ==========================================
    // 후기 & 꿀팁 댓글 시스템 (독립 모듈)
    // ==========================================
    const reviewForm = document.getElementById('review-form');
    const reviewsListContainer = document.getElementById('reviews-list-container');
    const modalReviewCount = document.getElementById('modal-review-count');

    if (reviewForm) {
        reviewForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!state.selectedProgram) return;

            const nicknameInput = document.getElementById('review-nickname');
            const passwordInput = document.getElementById('review-password');
            const contentInput = document.getElementById('review-content');

            const payload = {
                nickname: nicknameInput.value.trim(),
                password: passwordInput.value.trim(),
                content: contentInput.value.trim()
            };

            if (!payload.nickname || !payload.password || !payload.content) {
                showToast('모든 항목을 입력해주세요.');
                return;
            }

            try {
                const res = await fetch(`/api/programs/${state.selectedProgram.id}/reviews`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (res.ok) {
                    showToast('소중한 후기/꿀팁이 등록되었습니다! 🎉');
                    contentInput.value = '';
                    passwordInput.value = '';
                    fetchReviews(state.selectedProgram.id);
                } else {
                    const err = await res.json();
                    showToast(err.detail || '후기 등록에 실패했습니다.');
                }
            } catch (err) {
                showToast('네트워크 오류가 발생했습니다.');
            }
        });
    }

    async function fetchReviews(programId) {
        if (!reviewsListContainer) return;
        reviewsListContainer.innerHTML = '<div style="font-size:12.5px; color:var(--text-muted); padding:10px 0;">후기를 불러오는 중...</div>';

        try {
            const res = await fetch(`/api/programs/${programId}/reviews`);
            if (res.ok) {
                const reviews = await res.json();
                if (modalReviewCount) {
                    modalReviewCount.textContent = reviews.length;
                }

                if (reviews.length === 0) {
                    reviewsListContainer.innerHTML = `
                        <div class="review-empty-box">
                            아직 등록된 후기나 꿀팁이 없습니다. 첫 번째 꿀팁을 남겨보세요! ✨
                        </div>
                    `;
                    return;
                }

                reviewsListContainer.innerHTML = reviews.map(r => {
                    const dateStr = r.created_at ? r.created_at.split('T')[0] : '';
                    return `
                        <div class="review-item" data-review-id="${r.id}">
                            <div class="review-item-header">
                                <span class="review-author">
                                    <i data-lucide="user" class="icon-xs"></i> <strong>${r.nickname}</strong>
                                </span>
                                <div class="review-meta">
                                    <span class="review-date">${dateStr}</span>
                                    <button class="btn-review-delete" onclick="window.deleteReviewItem(${r.id})">삭제</button>
                                </div>
                            </div>
                            <div class="review-item-content">${escapeHtml(r.content)}</div>
                        </div>
                    `;
                }).join('');

                if (window.lucide) {
                    window.lucide.createIcons();
                }
            }
        } catch (e) {
            reviewsListContainer.innerHTML = '<div style="font-size:12px; color:var(--text-muted);">후기를 불러오지 못했습니다.</div>';
        }
    }

    // 삭제 모달 상태 관리
    let pendingDeleteReviewId = null;
    const deleteConfirmModal = document.getElementById('delete-confirm-modal');
    const deleteConfirmForm = document.getElementById('delete-confirm-form');
    const deleteConfirmPassword = document.getElementById('delete-confirm-password');
    const btnCancelDelete = document.getElementById('btn-cancel-delete');

    window.deleteReviewItem = function(reviewId) {
        pendingDeleteReviewId = reviewId;
        if (deleteConfirmPassword) deleteConfirmPassword.value = '';
        if (deleteConfirmModal) {
            deleteConfirmModal.style.display = 'flex';
            setTimeout(() => deleteConfirmPassword?.focus(), 100);
        }
    };

    if (btnCancelDelete) {
        btnCancelDelete.addEventListener('click', () => {
            if (deleteConfirmModal) deleteConfirmModal.style.display = 'none';
            pendingDeleteReviewId = null;
        });
    }

    if (deleteConfirmForm) {
        deleteConfirmForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!pendingDeleteReviewId) return;

            const password = deleteConfirmPassword ? deleteConfirmPassword.value.trim() : '';
            if (!password) {
                showToast('비밀번호를 입력해주세요.');
                return;
            }

            try {
                const res = await fetch(`/api/reviews/${pendingDeleteReviewId}/delete`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password })
                });

                if (res.ok) {
                    showToast('댓글이 삭제되었습니다.');
                    if (deleteConfirmModal) deleteConfirmModal.style.display = 'none';
                    pendingDeleteReviewId = null;
                    if (state.selectedProgram) {
                        fetchReviews(state.selectedProgram.id);
                    }
                } else {
                    const err = await res.json();
                    showToast(err.detail || '비밀번호가 일치하지 않습니다.');
                }
            } catch (e) {
                showToast('삭제 중 오류가 발생했습니다.');
            }
        });
    }


    function escapeHtml(str) {
        if (!str) return '';
        return str
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;')
            .replace(/\n/g, '<br/>');
    }

    // ==========================================
    // 이미지 고화질 확대 라이트박스 뷰어 매니저
    // ==========================================
    const lightboxModal = document.getElementById('image-lightbox-modal');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxTitle = document.getElementById('lightbox-title');
    const btnZoomIn = document.getElementById('btn-zoom-in');
    const btnZoomOut = document.getElementById('btn-zoom-out');
    const btnZoomReset = document.getElementById('btn-zoom-reset');
    const btnLightboxExternal = document.getElementById('btn-lightbox-external');
    const btnLightboxClose = document.getElementById('btn-lightbox-close');

    let zoomScale = 1.0;
    let panX = 0;
    let panY = 0;
    let isDragging = false;
    let startDragX = 0;
    let startDragY = 0;

    function openLightbox(imageUrl, title) {
        if (!lightboxModal || !lightboxImg) return;

        lightboxImg.src = imageUrl;
        if (lightboxTitle) lightboxTitle.textContent = title ? `${title}` : '포스터 확대 보기';
        if (btnLightboxExternal) btnLightboxExternal.href = imageUrl;

        // 초기화
        resetLightboxTransform();

        lightboxModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    function closeLightbox() {
        if (!lightboxModal) return;
        lightboxModal.style.display = 'none';
        resetLightboxTransform();
        if (!elements.modal || elements.modal.style.display === 'none') {
            document.body.style.overflow = '';
        }
    }

    function resetLightboxTransform() {
        zoomScale = 1.0;
        panX = 0;
        panY = 0;
        updateLightboxTransform();
    }

    function updateLightboxTransform() {
        if (!lightboxImg) return;
        lightboxImg.style.transform = `translate(${panX}px, ${panY}px) scale(${zoomScale})`;
        if (zoomScale > 1.0) {
            lightboxImg.classList.add('is-zoomed');
        } else {
            lightboxImg.classList.remove('is-zoomed');
        }
    }

    function setZoom(newScale) {
        zoomScale = Math.max(0.5, Math.min(newScale, 4.0));
        if (zoomScale <= 1.0) {
            panX = 0;
            panY = 0;
        }
        updateLightboxTransform();
    }

    if (lightboxModal) {
        if (btnZoomIn) {
            btnZoomIn.addEventListener('click', (e) => {
                e.stopPropagation();
                setZoom(zoomScale + 0.3);
            });
        }
        if (btnZoomOut) {
            btnZoomOut.addEventListener('click', (e) => {
                e.stopPropagation();
                setZoom(zoomScale - 0.3);
            });
        }
        if (btnZoomReset) {
            btnZoomReset.addEventListener('click', (e) => {
                e.stopPropagation();
                resetLightboxTransform();
            });
        }
        if (btnLightboxClose) {
            btnLightboxClose.addEventListener('click', (e) => {
                e.stopPropagation();
                closeLightbox();
            });
        }

        // 배경 클릭 시 닫기
        lightboxModal.addEventListener('click', (e) => {
            if (e.target === lightboxModal || e.target.id === 'lightbox-content-area' || e.target.id === 'lightbox-img-wrapper') {
                closeLightbox();
            }
        });

        // 마우스 휠 줌
        const contentArea = document.getElementById('lightbox-content-area');
        if (contentArea) {
            contentArea.addEventListener('wheel', (e) => {
                e.preventDefault();
                const delta = e.deltaY > 0 ? -0.2 : 0.2;
                setZoom(zoomScale + delta);
            }, { passive: false });
        }

        // 마우스 드래그 이동
        lightboxImg.addEventListener('mousedown', (e) => {
            isDragging = true;
            startDragX = e.clientX - panX;
            startDragY = e.clientY - panY;
            lightboxImg.classList.add('grabbing');
        });

        window.addEventListener('mousemove', (e) => {
            if (!isDragging) return;
            panX = e.clientX - startDragX;
            panY = e.clientY - startDragY;
            updateLightboxTransform();
        });

        window.addEventListener('mouseup', () => {
            if (isDragging) {
                isDragging = false;
                lightboxImg.classList.remove('grabbing');
            }
        });

        // 터치 제스처 (모바일 드래그 & 더블탭 확대 & 핀치 줌)
        let lastTouchTime = 0;
        let initialTouchDistance = 0;
        let initialScale = 1.0;

        lightboxImg.addEventListener('touchstart', (e) => {
            if (e.touches.length === 1) {
                const now = Date.now();
                if (now - lastTouchTime < 300) {
                    // 더블탭 줌 토글
                    setZoom(zoomScale > 1.2 ? 1.0 : 2.2);
                    lastTouchTime = 0;
                    return;
                }
                lastTouchTime = now;
                isDragging = true;
                startDragX = e.touches[0].clientX - panX;
                startDragY = e.touches[0].clientY - panY;
            } else if (e.touches.length === 2) {
                isDragging = false;
                initialTouchDistance = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
                initialScale = zoomScale;
            }
        }, { passive: true });

        lightboxImg.addEventListener('touchmove', (e) => {
            if (e.touches.length === 1 && isDragging) {
                panX = e.touches[0].clientX - startDragX;
                panY = e.touches[0].clientY - startDragY;
                updateLightboxTransform();
            } else if (e.touches.length === 2 && initialTouchDistance > 0) {
                const currentDistance = Math.hypot(
                    e.touches[0].clientX - e.touches[1].clientX,
                    e.touches[0].clientY - e.touches[1].clientY
                );
                const scaleFactor = currentDistance / initialTouchDistance;
                setZoom(initialScale * scaleFactor);
            }
        }, { passive: true });

        lightboxImg.addEventListener('touchend', () => {
            isDragging = false;
            initialTouchDistance = 0;
        }, { passive: true });
    }

    // 토스트 메시지
    function showToast(msg) {
        elements.toast.textContent = msg;
        elements.toast.classList.add('show');
        setTimeout(() => {
            elements.toast.classList.remove('show');
        }, 2500);
    }
});

