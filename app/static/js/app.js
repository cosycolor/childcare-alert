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
        selectedProgram: null,

        // 커뮤니티 상태
        activeMainTab: 'programs', // 'programs' | 'community'
        communityPosts: [],
        filteredCommunityPosts: [],
        commFilters: {
            category: '전체',
            district: '전체',
            status: '전체',
            q: ''
        },
        commCurrentPage: 1,
        commPageSize: 8,
        selectedPost: null
    };

    // DOM 요소
    const elements = {
        tabBtnPrograms: document.getElementById('tab-btn-programs'),
        tabBtnCommunity: document.getElementById('tab-btn-community'),
        tabContentPrograms: document.getElementById('tab-content-programs'),
        tabContentCommunity: document.getElementById('tab-content-community'),

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

        // 프로그램 모달
        modal: document.getElementById('program-modal'),
        modalCloseBtn: document.getElementById('modal-close-btn'),
        modalBadges: document.getElementById('modal-badges'),
        modalTitle: document.getElementById('modal-title'),
        modalMetaBar: document.getElementById('modal-meta-bar'),
        modalBody: document.getElementById('modal-body'),
        btnModalApply: document.getElementById('btn-modal-apply'),
        btnCopyLink: document.getElementById('btn-copy-link'),
        btnFindCompanion: document.getElementById('btn-find-companion'),

        // 커뮤니티 요소
        commPostsGrid: document.getElementById('community-posts-grid'),
        commPaginationContainer: document.getElementById('comm-pagination-container'),
        commEmptyState: document.getElementById('comm-empty-state'),
        commTotalCount: document.getElementById('comm-total-count'),
        commSearchInput: document.getElementById('comm-search-input'),
        commSearchClear: document.getElementById('comm-search-clear'),
        btnOpenPostWrite: document.getElementById('btn-open-post-write'),
        btnEmptyWrite: document.getElementById('btn-empty-write'),

        // 글 작성 모달
        postWriteModal: document.getElementById('post-write-modal'),
        btnClosePostWrite: document.getElementById('btn-close-post-write'),
        btnCancelPostWrite: document.getElementById('btn-cancel-post-write'),
        postWriteForm: document.getElementById('post-write-form'),
        postWriteModalTitle: document.getElementById('post-write-modal-title'),
        formGroupProgram: document.getElementById('form-group-program'),
        postLinkedProgramTitle: document.getElementById('post-linked-program-title'),
        btnUnlinkProgram: document.getElementById('btn-unlink-program'),
        postProgramId: document.getElementById('post-program-id'),
        postProgramTitle: document.getElementById('post-program-title'),

        // 글 상세 모달
        postDetailModal: document.getElementById('post-detail-modal'),
        btnClosePostDetail: document.getElementById('btn-close-post-detail'),
        commDetailBadges: document.getElementById('comm-detail-badges'),
        commDetailTitle: document.getElementById('comm-detail-title'),
        commDetailMeta: document.getElementById('comm-detail-meta'),
        commLinkedProgramCard: document.getElementById('comm-linked-program-card'),
        commLinkedProgTitle: document.getElementById('comm-linked-prog-title'),
        btnViewLinkedProg: document.getElementById('btn-view-linked-prog'),
        commDetailContent: document.getElementById('comm-detail-content'),
        commContactBox: document.getElementById('comm-contact-box'),
        btnCommOpenChat: document.getElementById('btn-comm-open-chat'),
        btnTogglePostStatus: document.getElementById('btn-toggle-post-status'),
        postStatusBtnText: document.getElementById('post-status-btn-text'),
        btnDeletePost: document.getElementById('btn-delete-post'),
        commCommentsCount: document.getElementById('comm-comments-count'),
        commCommentForm: document.getElementById('comm-comment-form'),
        commCommentsList: document.getElementById('comm-comments-list'),

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

                    if (filterType === 'category' && chipBtn.getAttribute('data-value') === '백화점/마트 문센') {
                        const guideEl = document.getElementById('culture-center-guide');
                        if (guideEl) {
                            guideEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    }
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
        // 상단 메인 탭 전환
        if (elements.tabBtnPrograms) {
            elements.tabBtnPrograms.addEventListener('click', () => switchMainTab('programs'));
        }
        if (elements.tabBtnCommunity) {
            elements.tabBtnCommunity.addEventListener('click', () => switchMainTab('community'));
        }

        // 프로그램 모달 내 [🤝 동기 구하기] 버튼
        if (elements.btnFindCompanion) {
            elements.btnFindCompanion.addEventListener('click', () => {
                if (state.selectedProgram) {
                    const prog = state.selectedProgram;
                    closeModal();
                    switchMainTab('community');
                    openPostWriteModal({
                        id: prog.id,
                        title: prog.title,
                        district: prog.district,
                        ageGroup: prog.target_age_group
                    });
                }
            });
        }

        // 커뮤니티 글쓰기 버튼들
        if (elements.btnOpenPostWrite) {
            elements.btnOpenPostWrite.addEventListener('click', () => openPostWriteModal());
        }
        if (elements.btnEmptyWrite) {
            elements.btnEmptyWrite.addEventListener('click', () => openPostWriteModal());
        }
        if (elements.btnClosePostWrite) {
            elements.btnClosePostWrite.addEventListener('click', closePostWriteModal);
        }
        if (elements.btnCancelPostWrite) {
            elements.btnCancelPostWrite.addEventListener('click', closePostWriteModal);
        }
        if (elements.btnUnlinkProgram) {
            elements.btnUnlinkProgram.addEventListener('click', unlinkProgramFromForm);
        }

        // 커뮤니티 글 작성 폼 제출
        if (elements.postWriteForm) {
            elements.postWriteForm.addEventListener('submit', handlePostWriteSubmit);
        }

        // 커뮤니티 글 상세 모달 닫기
        if (elements.btnClosePostDetail) {
            elements.btnClosePostDetail.addEventListener('click', closePostDetailModal);
        }
        if (elements.postDetailModal) {
            elements.postDetailModal.addEventListener('click', (e) => {
                if (e.target === elements.postDetailModal) closePostDetailModal();
            });
        }

        // 커뮤니티 글 상태 변경 & 삭제
        if (elements.btnTogglePostStatus) {
            elements.btnTogglePostStatus.addEventListener('click', handleTogglePostStatus);
        }
        if (elements.btnDeletePost) {
            elements.btnDeletePost.addEventListener('click', handleDeleteCurrentPost);
        }

        // 연계 프로그램 보기 버튼
        if (elements.btnViewLinkedProg) {
            elements.btnViewLinkedProg.addEventListener('click', () => {
                if (state.selectedPost && state.selectedPost.program_id) {
                    closePostDetailModal();
                    switchMainTab('programs');
                    openDetailModal(state.selectedPost.program_id);
                }
            });
        }

        // 커뮤니티 댓글 작성
        if (elements.commCommentForm) {
            elements.commCommentForm.addEventListener('submit', handlePostCommentSubmit);
        }

        // 커뮤니티 카테고리 필터
        const catFilterWrap = document.getElementById('community-category-filter');
        if (catFilterWrap) {
            catFilterWrap.addEventListener('click', (e) => {
                const btn = e.target.closest('.comm-chip');
                if (btn) {
                    catFilterWrap.querySelectorAll('.comm-chip').forEach(c => c.classList.remove('active'));
                    btn.classList.add('active');
                    state.commFilters.category = btn.getAttribute('data-category');
                    applyCommunityFilters();
                }
            });
        }

        // 커뮤니티 서브 필터 (지역, 상태)
        const distFilterWrap = document.getElementById('community-district-filter');
        if (distFilterWrap) {
            distFilterWrap.addEventListener('click', (e) => {
                const btn = e.target.closest('.sub-chip');
                if (btn) {
                    distFilterWrap.querySelectorAll('.sub-chip').forEach(c => c.classList.remove('active'));
                    btn.classList.add('active');
                    state.commFilters.district = btn.getAttribute('data-district');
                    applyCommunityFilters();
                }
            });
        }

        const statusFilterWrap = document.getElementById('community-status-filter');
        if (statusFilterWrap) {
            statusFilterWrap.addEventListener('click', (e) => {
                const btn = e.target.closest('.sub-chip');
                if (btn) {
                    statusFilterWrap.querySelectorAll('.sub-chip').forEach(c => c.classList.remove('active'));
                    btn.classList.add('active');
                    state.commFilters.status = btn.getAttribute('data-status');
                    applyCommunityFilters();
                }
            });
        }

        // 커뮤니티 검색
        if (elements.commSearchInput) {
            elements.commSearchInput.addEventListener('input', (e) => {
                state.commFilters.q = e.target.value.trim();
                elements.commSearchClear.style.display = state.commFilters.q ? 'block' : 'none';
                applyCommunityFilters();
            });
        }
        if (elements.commSearchClear) {
            elements.commSearchClear.addEventListener('click', () => {
                elements.commSearchInput.value = '';
                state.commFilters.q = '';
                elements.commSearchClear.style.display = 'none';
                applyCommunityFilters();
            });
        }

        // ESC 키 닫기 이벤트 핸들링
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (lightboxModal && lightboxModal.style.display !== 'none') {
                    closeLightbox();
                } else if (elements.postDetailModal && elements.postDetailModal.style.display !== 'none') {
                    closePostDetailModal();
                } else if (elements.postWriteModal && elements.postWriteModal.style.display !== 'none') {
                    closePostWriteModal();
                } else if (deleteConfirmModal && deleteConfirmModal.style.display !== 'none') {
                    deleteConfirmModal.style.display = 'none';
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

    // ==========================================
    // 메인 상단 탭 전환 (프로그램 ↔ 커뮤니티)
    // ==========================================
    function switchMainTab(tab) {
        state.activeMainTab = tab;

        if (tab === 'programs') {
            elements.tabBtnPrograms?.classList.add('active');
            elements.tabBtnCommunity?.classList.remove('active');
            if (elements.tabContentPrograms) elements.tabContentPrograms.style.display = 'block';
            if (elements.tabContentCommunity) elements.tabContentCommunity.style.display = 'none';
        } else {
            elements.tabBtnCommunity?.classList.add('active');
            elements.tabBtnPrograms?.classList.remove('active');
            if (elements.tabContentPrograms) elements.tabContentPrograms.style.display = 'none';
            if (elements.tabContentCommunity) elements.tabContentCommunity.style.display = 'block';

            if (state.communityPosts.length === 0) {
                fetchCommunityPosts();
            } else {
                renderCommunityPosts();
            }
        }

        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    // ==========================================
    // 커뮤니티 (동기 모집 & 육아 수다) 로직
    // ==========================================
    async function fetchCommunityPosts() {
        try {
            const res = await fetch('/api/posts');
            if (res.ok) {
                state.communityPosts = await res.json();
                applyCommunityFilters();
            }
        } catch (e) {
            console.error('커뮤니티 글 로드 실패', e);
            showToast('커뮤니티 글을 불러오는 중 오류가 발생했습니다.');
        }
    }

    function applyCommunityFilters(resetPage = true) {
        if (resetPage) {
            state.commCurrentPage = 1;
        }

        let list = state.communityPosts.filter(p => {
            // 카테고리
            if (state.commFilters.category !== '전체') {
                if (p.category !== state.commFilters.category) return false;
            }
            // 지역
            if (state.commFilters.district !== '전체') {
                if (p.district !== state.commFilters.district && p.district !== '전체') return false;
            }
            // 상태 (모집중)
            if (state.commFilters.status !== '전체') {
                if (p.status !== state.commFilters.status) return false;
            }
            // 검색어
            if (state.commFilters.q) {
                const q = state.commFilters.q.toLowerCase();
                const content = `${p.title} ${p.content} ${p.nickname} ${p.program_title || ''}`.toLowerCase();
                if (!content.includes(q)) return false;
            }
            return true;
        });

        state.filteredCommunityPosts = list;
        renderCommunityPosts();
    }

    function renderCommunityPosts() {
        if (!elements.commPostsGrid) return;

        const total = state.filteredCommunityPosts.length;
        if (elements.commTotalCount) elements.commTotalCount.textContent = total;

        if (total === 0) {
            elements.commPostsGrid.innerHTML = '';
            if (elements.commEmptyState) elements.commEmptyState.style.display = 'block';
            if (elements.commPaginationContainer) {
                elements.commPaginationContainer.style.display = 'none';
                elements.commPaginationContainer.innerHTML = '';
            }
            return;
        }

        if (elements.commEmptyState) elements.commEmptyState.style.display = 'none';

        const totalPages = Math.ceil(total / state.commPageSize);
        if (state.commCurrentPage > totalPages) {
            state.commCurrentPage = Math.max(1, totalPages);
        }

        const startIndex = (state.commCurrentPage - 1) * state.commPageSize;
        const endIndex = Math.min(startIndex + state.commPageSize, total);
        const currentItems = state.filteredCommunityPosts.slice(startIndex, endIndex);

        elements.commPostsGrid.innerHTML = currentItems.map(p => {
            const dateStr = p.created_at ? p.created_at.split('T')[0] : '';
            const catBadgeClass = p.category === '같이 가요' ? 'cat-companion' : (p.category === '육아 수다' ? 'cat-chat' : 'cat-share');
            const statusBadge = p.category === '같이 가요' ? `<span class="badge-comm-status ${p.status === '모집중' ? 'status-recruiting' : 'status-done'}">${p.status}</span>` : '';

            return `
                <div class="community-card" data-post-id="${p.id}">
                    <div class="comm-card-header">
                        <div class="comm-card-badges">
                            <span class="badge-comm-cat ${catBadgeClass}">${p.category}</span>
                            ${statusBadge}
                            <span class="comm-tag-dist">${p.district}</span>
                            ${p.target_age_group && p.target_age_group !== '전체' ? `<span class="comm-tag-age">${p.target_age_group}</span>` : ''}
                        </div>
                        <span class="comm-card-date">${dateStr}</span>
                    </div>

                    ${p.program_title ? `
                        <div class="comm-card-linked-prog">
                            <i data-lucide="link" class="icon-xxs"></i>
                            <span>${escapeHtml(p.program_title)}</span>
                        </div>
                    ` : ''}

                    <h3 class="comm-card-title">${escapeHtml(p.title)}</h3>
                    <p class="comm-card-desc">${escapeHtml(p.content)}</p>

                    <div class="comm-card-footer">
                        <div class="comm-card-author">
                            <i data-lucide="user" class="icon-xs"></i> <span>${escapeHtml(p.nickname)}</span>
                        </div>
                        <div class="comm-card-meta-right">
                            ${p.contact ? `<span class="badge-kakao-ready" title="카카오톡 오픈채팅 가능"><i data-lucide="message-circle" class="icon-xxs"></i> 오픈채팅</span>` : ''}
                            <span class="comm-comment-count">
                                <i data-lucide="message-square" class="icon-xs"></i> ${p.comments_count || 0}
                            </span>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        // 카드 클릭 시 상세 모달 열기
        elements.commPostsGrid.querySelectorAll('.community-card').forEach(card => {
            card.addEventListener('click', () => {
                const postId = parseInt(card.getAttribute('data-post-id'), 10);
                openPostDetailModal(postId);
            });
        });

        // 커뮤니티 페이지네이션 렌더링
        renderCommunityPagination(totalPages, total, startIndex + 1, endIndex);

        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    function renderCommunityPagination(totalPages, total, startNum, endNum) {
        if (!elements.commPaginationContainer) return;

        if (totalPages <= 1) {
            elements.commPaginationContainer.style.display = 'none';
            elements.commPaginationContainer.innerHTML = '';
            return;
        }

        elements.commPaginationContainer.style.display = 'flex';
        const current = state.commCurrentPage;

        const pages = [];
        for (let i = 1; i <= totalPages; i++) pages.push(i);

        const pagesHtml = pages.map(p => {
            return `<button class="page-btn ${p === current ? 'active' : ''}" data-page="${p}">${p}</button>`;
        }).join('');

        elements.commPaginationContainer.innerHTML = `
            <div class="pagination-info">
                <span>전체 ${total}개 중 <strong>${startNum}-${endNum}</strong>개 표시 (${current} / ${totalPages} 페이지)</span>
            </div>
            <nav class="pagination-nav" aria-label="커뮤니티 페이지 네비게이션">
                <button class="page-nav-btn" id="btn-comm-page-prev" ${current === 1 ? 'disabled' : ''}>
                    <i data-lucide="chevron-left" class="icon-xs"></i> <span>이전</span>
                </button>
                <div class="page-numbers">
                    ${pagesHtml}
                </div>
                <button class="page-nav-btn" id="btn-comm-page-next" ${current === totalPages ? 'disabled' : ''}>
                    <span>다음</span> <i data-lucide="chevron-right" class="icon-xs"></i>
                </button>
            </nav>
        `;

        const prevBtn = elements.commPaginationContainer.querySelector('#btn-comm-page-prev');
        if (prevBtn && current > 1) {
            prevBtn.addEventListener('click', () => goToCommPage(current - 1));
        }

        const nextBtn = elements.commPaginationContainer.querySelector('#btn-comm-page-next');
        if (nextBtn && current < totalPages) {
            nextBtn.addEventListener('click', () => goToCommPage(current + 1));
        }

        elements.commPaginationContainer.querySelectorAll('.page-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const pageNum = parseInt(btn.getAttribute('data-page'), 10);
                if (pageNum && pageNum !== current) {
                    goToCommPage(pageNum);
                }
            });
        });
    }

    function goToCommPage(page) {
        state.commCurrentPage = page;
        renderCommunityPosts();
        const target = elements.tabContentCommunity;
        if (target) {
            const topOffset = target.getBoundingClientRect().top + window.scrollY - 80;
            window.scrollTo({ top: Math.max(0, topOffset), behavior: 'smooth' });
        }
    }

    // ==========================================
    // 글 작성 모달 제어
    // ==========================================
    function openPostWriteModal(linkedProgram = null) {
        if (!elements.postWriteModal) return;

        // 폼 초기화
        elements.postWriteForm.reset();

        if (linkedProgram) {
            if (elements.formGroupProgram) elements.formGroupProgram.style.display = 'block';
            if (elements.postLinkedProgramTitle) elements.postLinkedProgramTitle.textContent = linkedProgram.title;
            if (elements.postProgramId) elements.postProgramId.value = linkedProgram.id;
            if (elements.postProgramTitle) elements.postProgramTitle.value = linkedProgram.title;

            // 지역 및 카테고리 자동 설정
            const distSelect = document.getElementById('post-district');
            if (distSelect && linkedProgram.district) {
                if (linkedProgram.district.includes('광진')) distSelect.value = '광진구';
                else if (linkedProgram.district.includes('성동')) distSelect.value = '성동구';
            }

            const titleInput = document.getElementById('post-title');
            if (titleInput) {
                titleInput.value = `[${linkedProgram.title}] 함께 신청하고 같이 가실 분 구해요!`;
            }
        } else {
            unlinkProgramFromForm();
        }

        elements.postWriteModal.style.display = 'flex';
        document.body.style.overflow = 'hidden';

        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    function closePostWriteModal() {
        if (!elements.postWriteModal) return;
        elements.postWriteModal.style.display = 'none';
        if (!elements.postDetailModal || elements.postDetailModal.style.display === 'none') {
            document.body.style.overflow = '';
        }
    }

    function unlinkProgramFromForm() {
        if (elements.formGroupProgram) elements.formGroupProgram.style.display = 'none';
        if (elements.postProgramId) elements.postProgramId.value = '';
        if (elements.postProgramTitle) elements.postProgramTitle.value = '';
    }

    async function handlePostWriteSubmit(e) {
        e.preventDefault();

        const catRadio = elements.postWriteForm.querySelector('input[name="post-category"]:checked');
        const payload = {
            category: catRadio ? catRadio.value : '같이 가요',
            district: document.getElementById('post-district')?.value || '전체',
            target_age_group: document.getElementById('post-age-group')?.value || '전체',
            program_id: elements.postProgramId?.value ? parseInt(elements.postProgramId.value, 10) : null,
            program_title: elements.postProgramTitle?.value || null,
            title: document.getElementById('post-title')?.value.trim() || '',
            content: document.getElementById('post-content')?.value.trim() || '',
            contact: document.getElementById('post-contact')?.value.trim() || null,
            nickname: document.getElementById('post-nickname')?.value.trim() || '',
            password: document.getElementById('post-password')?.value.trim() || ''
        };

        if (!payload.title || !payload.content || !payload.nickname || !payload.password) {
            showToast('필수 항목을 모두 입력해주세요.');
            return;
        }

        try {
            const res = await fetch('/api/posts', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (res.ok) {
                const newPost = await res.json();
                showToast('게시글이 성공적으로 등록되었습니다! 🎉');
                closePostWriteModal();
                await fetchCommunityPosts();
                openPostDetailModal(newPost.id);
            } else {
                const err = await res.json();
                showToast(err.detail || '글 등록에 실패했습니다.');
            }
        } catch (e) {
            showToast('네트워크 오류가 발생했습니다.');
        }
    }

    // ==========================================
    // 글 상세 모달 제어
    // ==========================================
    async function openPostDetailModal(postId) {
        if (!elements.postDetailModal) return;

        try {
            const res = await fetch(`/api/posts/${postId}`);
            if (!res.ok) throw new Error('게시글을 불러오지 못했습니다.');
            const post = await res.json();
            state.selectedPost = post;

            // 뱃지 및 메타
            const catBadgeClass = post.category === '같이 가요' ? 'cat-companion' : (post.category === '육아 수다' ? 'cat-chat' : 'cat-share');
            const statusBadge = post.category === '같이 가요' ? `<span class="badge-comm-status ${post.status === '모집중' ? 'status-recruiting' : 'status-done'}">${post.status}</span>` : '';

            elements.commDetailBadges.innerHTML = `
                <span class="badge-comm-cat ${catBadgeClass}">${post.category}</span>
                ${statusBadge}
                <span class="comm-tag-dist">${post.district}</span>
                <span class="comm-tag-age">${post.target_age_group}</span>
            `;

            elements.commDetailTitle.textContent = post.title;
            const dateStr = post.created_at ? post.created_at.split('T')[0] : '';
            elements.commDetailMeta.innerHTML = `
                <span><i data-lucide="user" class="icon-xs"></i> <strong>${escapeHtml(post.nickname)}</strong></span>
                <span><i data-lucide="calendar" class="icon-xs"></i> ${dateStr}</span>
            `;

            // 연계 프로그램
            if (post.program_id && post.program_title) {
                elements.commLinkedProgTitle.textContent = post.program_title;
                elements.commLinkedProgramCard.style.display = 'flex';
            } else {
                elements.commLinkedProgramCard.style.display = 'none';
            }

            // 본문
            elements.commDetailContent.innerHTML = escapeHtml(post.content);

            // 오픈카톡 링크
            if (post.contact) {
                elements.btnCommOpenChat.href = post.contact.startsWith('http') ? post.contact : `https://${post.contact}`;
                elements.commContactBox.style.display = 'flex';
            } else {
                elements.commContactBox.style.display = 'none';
            }

            // 상태 변경 버튼 텍스트
            if (elements.btnTogglePostStatus) {
                if (post.category === '같이 가요') {
                    elements.btnTogglePostStatus.style.display = 'inline-flex';
                    elements.postStatusBtnText.textContent = post.status === '모집중' ? '모집완료로 변경' : '모집중으로 다시 변경';
                } else {
                    elements.btnTogglePostStatus.style.display = 'none';
                }
            }

            // 댓글 렌더링
            renderPostComments(post.comments || []);

            elements.postDetailModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';

            if (window.lucide) {
                window.lucide.createIcons();
            }
        } catch (e) {
            showToast('게시글을 불러오지 못했습니다.');
        }
    }

    function closePostDetailModal() {
        if (!elements.postDetailModal) return;
        elements.postDetailModal.style.display = 'none';
        document.body.style.overflow = '';
        state.selectedPost = null;
    }

    function renderPostComments(comments) {
        if (elements.commCommentsCount) elements.commCommentsCount.textContent = comments.length;

        if (!elements.commCommentsList) return;

        if (comments.length === 0) {
            elements.commCommentsList.innerHTML = `
                <div class="review-empty-box">
                    아직 등록된 댓글이 없습니다. 첫 번째 이야기를 남겨보세요! ✨
                </div>
            `;
            return;
        }

        elements.commCommentsList.innerHTML = comments.map(c => {
            const dateStr = c.created_at ? c.created_at.split('T')[0] : '';
            return `
                <div class="review-item" data-comm-comment-id="${c.id}">
                    <div class="review-item-header">
                        <span class="review-author">
                            <i data-lucide="user" class="icon-xs"></i> <strong>${escapeHtml(c.nickname)}</strong>
                        </span>
                        <div class="review-meta">
                            <span class="review-date">${dateStr}</span>
                            <button class="btn-review-delete" onclick="window.deleteCommunityComment(${c.id})">삭제</button>
                        </div>
                    </div>
                    <div class="review-item-content">${escapeHtml(c.content)}</div>
                </div>
            `;
        }).join('');

        if (window.lucide) {
            window.lucide.createIcons();
        }
    }

    async function handlePostCommentSubmit(e) {
        e.preventDefault();
        if (!state.selectedPost) return;

        const nickname = document.getElementById('comm-comment-nickname')?.value.trim();
        const password = document.getElementById('comm-comment-password')?.value.trim();
        const content = document.getElementById('comm-comment-content')?.value.trim();

        if (!nickname || !password || !content) {
            showToast('모든 항목을 입력해주세요.');
            return;
        }

        try {
            const res = await fetch(`/api/posts/${state.selectedPost.id}/comments`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ nickname, password, content })
            });

            if (res.ok) {
                showToast('댓글이 등록되었습니다! 🎉');
                document.getElementById('comm-comment-content').value = '';
                document.getElementById('comm-comment-password').value = '';
                openPostDetailModal(state.selectedPost.id);
                fetchCommunityPosts(); // 목록의 댓글 수 갱신
            } else {
                const err = await res.json();
                showToast(err.detail || '댓글 등록 실패');
            }
        } catch (e) {
            showToast('네트워크 오류가 발생했습니다.');
        }
    }

    async function handleTogglePostStatus() {
        if (!state.selectedPost) return;
        const newStatus = state.selectedPost.status === '모집중' ? '모집완료' : '모집중';
        const password = prompt('글 작성 시 입력한 비밀번호 4자리를 입력해주세요:');
        if (!password) return;

        try {
            const res = await fetch(`/api/posts/${state.selectedPost.id}/status`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ password, status: newStatus })
            });

            if (res.ok) {
                showToast(`상태가 [${newStatus}]로 변경되었습니다.`);
                openPostDetailModal(state.selectedPost.id);
                fetchCommunityPosts();
            } else {
                const err = await res.json();
                showToast(err.detail || '비밀번호가 일치하지 않습니다.');
            }
        } catch (e) {
            showToast('오류가 발생했습니다.');
        }
    }

    function handleDeleteCurrentPost() {
        if (!state.selectedPost) return;
        openUnifiedDeleteModal('post', state.selectedPost.id);
    }

    window.deleteCommunityComment = function(commentId) {
        openUnifiedDeleteModal('comm_comment', commentId);
    };

    // ==========================================
    // 통합 비밀번호 확인 및 삭제 모달 시스템
    // ==========================================
    let pendingDeleteTarget = null; // { type: 'review'|'post'|'comm_comment', id: number }
    const deleteConfirmModal = document.getElementById('delete-confirm-modal');
    const deleteConfirmForm = document.getElementById('delete-confirm-form');
    const deleteConfirmPassword = document.getElementById('delete-confirm-password');
    const btnCancelDelete = document.getElementById('btn-cancel-delete');

    function openUnifiedDeleteModal(type, id) {
        pendingDeleteTarget = { type, id };
        if (deleteConfirmPassword) deleteConfirmPassword.value = '';
        if (deleteConfirmModal) {
            deleteConfirmModal.style.display = 'flex';
            setTimeout(() => deleteConfirmPassword?.focus(), 100);
        }
    }

    window.deleteReviewItem = function(reviewId) {
        openUnifiedDeleteModal('review', reviewId);
    };

    if (btnCancelDelete) {
        btnCancelDelete.addEventListener('click', () => {
            if (deleteConfirmModal) deleteConfirmModal.style.display = 'none';
            pendingDeleteTarget = null;
        });
    }

    if (deleteConfirmForm) {
        deleteConfirmForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!pendingDeleteTarget) return;

            const password = deleteConfirmPassword ? deleteConfirmPassword.value.trim() : '';
            if (!password) {
                showToast('비밀번호를 입력해주세요.');
                return;
            }

            const { type, id } = pendingDeleteTarget;
            let endpoint = '';

            if (type === 'review') {
                endpoint = `/api/reviews/${id}/delete`;
            } else if (type === 'post') {
                endpoint = `/api/posts/${id}/delete`;
            } else if (type === 'comm_comment') {
                endpoint = `/api/comments/${id}/delete`;
            }

            try {
                const res = await fetch(endpoint, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password })
                });

                if (res.ok) {
                    showToast('삭제되었습니다.');
                    if (deleteConfirmModal) deleteConfirmModal.style.display = 'none';
                    pendingDeleteTarget = null;

                    if (type === 'review') {
                        if (state.selectedProgram) fetchReviews(state.selectedProgram.id);
                    } else if (type === 'post') {
                        closePostDetailModal();
                        fetchCommunityPosts();
                    } else if (type === 'comm_comment') {
                        if (state.selectedPost) openPostDetailModal(state.selectedPost.id);
                        fetchCommunityPosts();
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

