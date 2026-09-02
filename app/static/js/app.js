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
            q: ''
        },
        currentMonth: new Date(2026, 8, 1), // 2026년 9월 기본
        selectedProgram: null
    };

    // DOM 요소
    const elements = {
        programsGrid: document.getElementById('programs-grid'),
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

        // 칩스 필터 클릭 이벤트 (아이콘 클릭 시에도 부모 chip을 찾도록 개선)
        ['district', 'age', 'category', 'status'].forEach(filterType => {
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


        // 필터 초기화 버튼
        elements.btnResetFilters.addEventListener('click', resetFilters);

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
            if (e.key === 'Escape' && elements.modal.style.display !== 'none') {
                closeModal();
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
            q: ''
        };
        elements.searchInput.value = '';
        elements.searchClear.style.display = 'none';

        ['district', 'age', 'category', 'status'].forEach(filterType => {
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

    // 클라이언트 사이드 필터 적용
    function applyFilters() {
        state.filteredPrograms = state.programs.filter(item => {
            // 자치구
            if (state.filters.district !== '전체') {
                if (!item.district.includes(state.filters.district)) return false;
            }
            // 기관 카테고리
            if (state.filters.category !== '전체') {
                if (item.category !== state.filters.category) return false;
            }
            // 연령
            if (state.filters.age_group !== '전체') {
                const isMatch = item.target_age_group === state.filters.age_group ||
                                item.target_age_group.includes('공통') ||
                                (item.target_desc && item.target_desc.includes(state.filters.age_group.replace('개월', '')));
                if (!isMatch) return false;
            }
            // 상태
            if (state.filters.status !== '전체') {
                if (item.status !== state.filters.status) return false;
            }
            // 검색어
            if (state.filters.q) {
                const q = state.filters.q.toLowerCase();
                const content = `${item.title} ${item.institution_name} ${item.target_desc || ''} ${item.location || ''}`.toLowerCase();
                if (!content.includes(q)) return false;
            }
            return true;
        });

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

    // 카드 목록 렌더링
    function renderList() {
        elements.resultTotalCount.textContent = state.filteredPrograms.length;

        if (state.filteredPrograms.length === 0) {
            elements.programsGrid.innerHTML = '';
            elements.emptyState.style.display = 'block';
            return;
        }

        elements.emptyState.style.display = 'none';
        elements.programsGrid.innerHTML = state.filteredPrograms.map(prog => {
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

        // Lucide SVG 아이콘 활성화
        if (window.lucide) {
            window.lucide.createIcons();
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
            bodyHtml += `<img src="${prog.image_url}" alt="${prog.title} 홍보 포스터" class="poster-viewer" />`;
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

        elements.modal.style.display = 'flex';
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        elements.modal.style.display = 'none';
        document.body.style.overflow = '';
        state.selectedProgram = null;
    }

    // 토스트 메시지
    function showToast(msg) {
        elements.toast.textContent = msg;
        elements.toast.classList.add('show');
        setTimeout(() => {
            elements.toast.classList.remove('show');
        }, 3000);
    }
});
