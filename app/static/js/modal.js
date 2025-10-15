// 간단하고 확실한 모달 시스템
function showSimpleModal(modalId, event = null) {
    // 이벤트 버블링 방지
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }

    const modal = document.querySelector(modalId);
    if (modal) {
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';

        // 모달이 열린 직후에는 백드롭 클릭을 무시하도록 플래그 설정
        modal.dataset.justOpened = 'true';
        setTimeout(() => {
            if (modal.dataset.justOpened) {
                delete modal.dataset.justOpened;
            }
        }, 200);
    }
}

function hideSimpleModal(modalId) {
    const modal = document.querySelector(modalId);
    if (modal) {
        modal.classList.remove('show');
        // 내용을 바로 지우지 말고 잠시 후에 지우기 (애니메이션 고려)
        setTimeout(() => {
            const modalContent = modal.querySelector('.simple-modal-content');
            if (modalContent) {
                modalContent.innerHTML = '';
            }
        }, 300);
        document.body.style.overflow = '';
        // 플래그 제거
        if (modal.dataset.justOpened) {
            delete modal.dataset.justOpened;
        }
    }
}

// 전역 함수로 설정
window.showModal = showSimpleModal;
window.hideModal = hideSimpleModal;

// ESC 키로 모달 닫기
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        document.querySelectorAll('.simple-modal.show').forEach(modal => {
            hideSimpleModal('#' + modal.id);
        });
    }
});

// 백드롭 클릭으로 모달 닫기
document.addEventListener('click', function(event) {
    if (event.target.classList.contains('simple-modal')) {
        // 모달이 방금 열린 경우 무시
        if (event.target.dataset.justOpened) {
            return;
        }
        hideSimpleModal('#' + event.target.id);
    }
});

// HTMX 이벤트 처리 (자동 모달 열기 제거 - 수동 onclick으로 처리)

document.body.addEventListener('htmx:afterRequest', function(event) {
    console.log('HTMX afterRequest:', {
        status: event.detail.xhr.status,
        verb: event.detail.requestConfig.verb,
        path: event.detail.requestConfig.path
    });

    if (event.detail.xhr.status >= 200 && event.detail.xhr.status < 300) {
        // 폼 제출 성공 시 모달 닫기
        if (event.detail.requestConfig.verb === 'post') {
            const path = event.detail.requestConfig.path;
            console.log('Processing POST success:', path);

            if (path.includes('/api/milestones')) {
                if (path.includes('/edit')) {
                    console.log('Milestone edit detected, closing modal');
                    // 마일스톤 편집 (200 OK)
                    const modal = document.querySelector('#edit-milestone-modal');
                    if (modal) {
                        console.log('Modal found, hiding...');
                        modal.classList.remove('show');
                        modal.classList.add('hidden');
                        document.body.style.overflow = '';
                    } else {
                        console.log('Modal not found!');
                    }
                    alert('마일스톤이 수정되었습니다!');
                    // 페이지 새로고침으로 변경사항 반영
                    window.location.reload();
                } else {
                    console.log('Milestone create detected');
                    // 마일스톤 생성 (201 Created)
                    hideSimpleModal('#new-milestone-modal');
                    alert('마일스톤이 생성되었습니다!');
                    // HTMX를 사용해서 페이지 콘텐츠만 새로고침
                    htmx.trigger(document.body, 'refreshContent');
                }
            } else if (path.includes('/api/todos')) {
                hideSimpleModal('#new-todo-modal');
                alert('TODO가 생성되었습니다!');
                // HTMX를 사용해서 페이지 콘텐츠만 새로고침
                htmx.trigger(document.body, 'refreshContent');
            } else if (path.includes('/api/daily/todos')) {
                // 마일스톤 상세 페이지의 모달인지 확인
                const milestoneModal = document.querySelector('#new-daily-todo-modal');
                if (milestoneModal) {
                    // 마일스톤 페이지의 모달은 .hidden 클래스 사용
                    milestoneModal.classList.add('hidden');
                    // 폼 초기화
                    const form = document.querySelector('#daily-todo-form');
                    if (form) form.reset();
                } else {
                    // 일반 daily todo 페이지
                    hideSimpleModal('#new-daily-todo-modal');
                }
                alert('할일이 추가되었습니다!');
                // 페이지 새로고침으로 변경사항 반영
                window.location.reload();
            }
        }
    } else if (event.detail.xhr.status === 409) {
        // 409 Conflict 에러 처리 - 서버 메시지 사용
        try {
            const errorResponse = JSON.parse(event.detail.xhr.responseText);
            alert(errorResponse.detail || '동일한 제목의 마일스톤이 이미 존재합니다. 다른 제목을 사용해주세요.');
        } catch (e) {
            alert('동일한 제목의 마일스톤이 이미 존재합니다. 다른 제목을 사용해주세요.');
        }
    } else if (event.detail.xhr.status === 400) {
        // 400 Bad Request 에러 처리
        try {
            const errorResponse = JSON.parse(event.detail.xhr.responseText);
            alert(errorResponse.detail || '입력 데이터에 오류가 있습니다. 시작일과 종료일을 확인해주세요.');
        } catch (e) {
            alert('입력 데이터에 오류가 있습니다. 시작일과 종료일을 확인해주세요.');
        }
    } else if (event.detail.xhr.status >= 400) {
        // 기타 에러 처리
        alert('오류가 발생했습니다. 다시 시도해주세요.');
    }
});