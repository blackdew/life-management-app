/**
 * 메인 JavaScript 파일
 * AI와 함께 놀며 사랑을 채우는 삶 - 생산성 향상을 위한 스크립트
 */

// DOM이 로드되면 실행
document.addEventListener('DOMContentLoaded', function() {
    console.log('🤖 AI와 함께 놀며 사랑을 채우는 삶 - 애플리케이션이 시작되었습니다!');

    // 초기화 함수들 실행
    initializeResponsiveFeatures();
    initializeAnimations();
    initializeFormEnhancements();
    initializeTooltips();
});

/**
 * 반응형 기능 초기화
 */
function initializeResponsiveFeatures() {
    // 모바일 메뉴 토글 (필요시 사용)
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }

    // 윈도우 리사이즈 시 반응형 조정
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            adjustResponsiveElements();
        }, 250);
    });

    // 초기 반응형 조정
    adjustResponsiveElements();
}

/**
 * 반응형 요소 조정
 */
function adjustResponsiveElements() {
    const screenWidth = window.innerWidth;

    // 작은 화면에서 카드 간격 조정
    const cards = document.querySelectorAll('.card, .bg-white.shadow');
    cards.forEach(card => {
        if (screenWidth < 640) { // sm 브레이크포인트
            card.classList.add('mx-2');
        } else {
            card.classList.remove('mx-2');
        }
    });

}

/**
 * 애니메이션 초기화
 */
function initializeAnimations() {
    // Intersection Observer로 스크롤 애니메이션
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('fade-in');
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    // 애니메이션 대상 요소들 관찰
    const animateElements = document.querySelectorAll('.card, .bg-white.shadow, .todo-item');
    animateElements.forEach(el => {
        observer.observe(el);
    });

    // 호버 효과 개선
    const hoverElements = document.querySelectorAll('.hover\\:shadow-md, .hover\\:bg-gray-50');
    hoverElements.forEach(el => {
        el.classList.add('hover-lift');
    });
}

/**
 * 폼 기능 향상
 */
function initializeFormEnhancements() {
    // 모든 입력 필드에 포커스 효과 추가
    const inputs = document.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.classList.add('focus-ring');

        // 입력값 변경시 실시간 검증
        input.addEventListener('input', function() {
            validateField(this);
        });
    });

    // 폼 제출 시 로딩 표시
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitButton = form.querySelector('[type="submit"]');
            if (submitButton) {
                showLoadingState(submitButton);
            }
        });
    });
}

/**
 * 필드 검증
 */
function validateField(field) {
    const value = field.value.trim();
    const fieldType = field.type || field.tagName.toLowerCase();

    // 기본 검증 규칙
    let isValid = true;
    let message = '';

    if (field.required && !value) {
        isValid = false;
        message = '필수 입력 항목입니다.';
    } else if (fieldType === 'email' && value && !isValidEmail(value)) {
        isValid = false;
        message = '올바른 이메일 형식이 아닙니다.';
    }

    // 시각적 피드백
    if (!isValid) {
        field.classList.add('border-red-500', 'focus:ring-red-500');
        field.classList.remove('border-gray-300', 'focus:ring-blue-500');
        showFieldError(field, message);
    } else {
        field.classList.remove('border-red-500', 'focus:ring-red-500');
        field.classList.add('border-gray-300', 'focus:ring-blue-500');
        hideFieldError(field);
    }

    return isValid;
}

/**
 * 이메일 유효성 검사
 */
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

/**
 * 필드 오류 메시지 표시
 */
function showFieldError(field, message) {
    // 기존 오류 메시지 제거
    hideFieldError(field);

    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error text-red-500 text-xs mt-1';
    errorDiv.textContent = message;

    field.parentNode.insertBefore(errorDiv, field.nextSibling);
}

/**
 * 필드 오류 메시지 숨김
 */
function hideFieldError(field) {
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

/**
 * 로딩 상태 표시
 */
function showLoadingState(button) {
    const originalText = button.textContent;
    button.textContent = '처리 중...';
    button.disabled = true;
    button.classList.add('opacity-50', 'cursor-not-allowed');

    // 3초 후 원래 상태로 복귀 (안전장치)
    setTimeout(() => {
        button.textContent = originalText;
        button.disabled = false;
        button.classList.remove('opacity-50', 'cursor-not-allowed');
    }, 3000);
}

/**
 * 툴팁 초기화
 */
function initializeTooltips() {
    const tooltipElements = document.querySelectorAll('[title]');

    tooltipElements.forEach(element => {
        let tooltip;

        element.addEventListener('mouseenter', function() {
            const title = this.getAttribute('title');
            if (!title) return;

            // title 속성 임시 제거 (기본 툴팁 방지)
            this.removeAttribute('title');
            this.setAttribute('data-original-title', title);

            // 커스텀 툴팁 생성
            tooltip = createTooltip(title);
            document.body.appendChild(tooltip);

            positionTooltip(tooltip, this);

            // 애니메이션
            setTimeout(() => {
                tooltip.classList.add('opacity-100');
                tooltip.classList.remove('opacity-0');
            }, 10);
        });

        element.addEventListener('mouseleave', function() {
            // title 속성 복원
            const originalTitle = this.getAttribute('data-original-title');
            if (originalTitle) {
                this.setAttribute('title', originalTitle);
                this.removeAttribute('data-original-title');
            }

            // 툴팁 제거
            if (tooltip) {
                tooltip.classList.add('opacity-0');
                tooltip.classList.remove('opacity-100');
                setTimeout(() => {
                    if (tooltip && tooltip.parentNode) {
                        tooltip.parentNode.removeChild(tooltip);
                    }
                }, 200);
            }
        });
    });
}

/**
 * 툴팁 생성
 */
function createTooltip(text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'fixed z-50 px-2 py-1 text-xs text-white bg-gray-900 rounded shadow-lg opacity-0 transition-opacity duration-200 pointer-events-none';
    tooltip.textContent = text;
    return tooltip;
}

/**
 * 툴팁 위치 조정
 */
function positionTooltip(tooltip, element) {
    const rect = element.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();

    let top = rect.top - tooltipRect.height - 8;
    let left = rect.left + (rect.width / 2) - (tooltipRect.width / 2);

    // 화면 경계 검사
    if (top < 0) {
        top = rect.bottom + 8;
    }

    if (left < 8) {
        left = 8;
    } else if (left + tooltipRect.width > window.innerWidth - 8) {
        left = window.innerWidth - tooltipRect.width - 8;
    }

    tooltip.style.top = top + window.pageYOffset + 'px';
    tooltip.style.left = left + 'px';
}


/**
 * 유틸리티 함수들
 */

// 디바운스 함수
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 스무스 스크롤
function smoothScrollTo(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// 로컬 스토리지 헬퍼
const Storage = {
    set: (key, value) => {
        try {
            localStorage.setItem(key, JSON.stringify(value));
            return true;
        } catch (error) {
            console.error('Storage.set error:', error);
            return false;
        }
    },

    get: (key, defaultValue = null) => {
        try {
            const item = localStorage.getItem(key);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.error('Storage.get error:', error);
            return defaultValue;
        }
    },

    remove: (key) => {
        try {
            localStorage.removeItem(key);
            return true;
        } catch (error) {
            console.error('Storage.remove error:', error);
            return false;
        }
    }
};

// 전역 객체로 유틸리티 노출
window.LifeApp = {
    debounce,
    smoothScrollTo,
    Storage,
    validateField,
    showLoadingState,
    adjustResponsiveElements
};

// HTMX 이벤트 핸들러 (HTMX가 로드된 경우)
document.addEventListener('htmx:afterRequest', function(event) {
    // 새로 로드된 콘텐츠에도 기능 적용
    setTimeout(() => {
        initializeAnimations();
        initializeFormEnhancements();
        initializeTooltips();
    }, 100);
});

// 에러 핸들링
window.addEventListener('error', function(event) {
    console.error('JavaScript 오류 발생:', event.error);

    // 사용자에게 친화적인 에러 메시지 (선택사항)
    // showNotification('일시적인 오류가 발생했습니다. 페이지를 새로고침해주세요.', 'error');
});

console.log('✅ 메인 JavaScript 초기화 완료');