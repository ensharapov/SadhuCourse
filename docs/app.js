/**
 * Гвозди Просто — Mini App
 * Дата эфира: 3 января 2025, 19:00 МСК
 */

// ═══════════════════════════════════════════════════════════════
// КОНФИГУРАЦИЯ
// ═══════════════════════════════════════════════════════════════

const CONFIG = {
    // Дата эфира (МСК = UTC+3)
    webinarDate: new Date('2026-01-03T19:00:00+03:00'),

    // Начальное количество покупателей
    initialBuyers: 50,

    // Telegram WebApp
    tg: window.Telegram?.WebApp
};

// ═══════════════════════════════════════════════════════════════
// ИНИЦИАЛИЗАЦИЯ
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    initTelegramWebApp();
    initCountdown();
    initBuyersCounter();
    initButtons();
});

function initTelegramWebApp() {
    if (CONFIG.tg) {
        CONFIG.tg.ready();
        CONFIG.tg.expand();

        // Применяем тему Telegram
        applyTelegramTheme();

        // Настраиваем MainButton если нужно
        CONFIG.tg.MainButton.hide();
    }
}

function applyTelegramTheme() {
    const tg = CONFIG.tg;
    if (!tg) return;

    // Можно адаптировать цвета под тему Telegram
    // Пока используем свою тёмную тему
    document.body.style.backgroundColor = tg.themeParams.bg_color || '#0a0a0f';
}

// ═══════════════════════════════════════════════════════════════
// ТАЙМЕР ОБРАТНОГО ОТСЧЁТА
// ═══════════════════════════════════════════════════════════════

function initCountdown() {
    updateCountdown();
    setInterval(updateCountdown, 1000);
}

function updateCountdown() {
    const now = new Date();
    const diff = CONFIG.webinarDate - now;

    const daysEl = document.getElementById('days');
    const hoursEl = document.getElementById('hours');
    const minutesEl = document.getElementById('minutes');

    if (!daysEl || !hoursEl || !minutesEl) return;

    if (diff <= 0) {
        // Эфир уже начался или прошёл
        daysEl.textContent = '00';
        hoursEl.textContent = '00';
        minutesEl.textContent = '00';

        // Меняем текст
        const timerLabel = document.querySelector('.timer-label');
        if (timerLabel) {
            timerLabel.textContent = 'Эфир идёт!';
        }

        const eventDate = document.querySelector('.event-date');
        if (eventDate) {
            eventDate.textContent = '🔴 Подключайся сейчас!';
        }
        return;
    }

    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    daysEl.textContent = String(days).padStart(2, '0');
    hoursEl.textContent = String(hours).padStart(2, '0');
    minutesEl.textContent = String(minutes).padStart(2, '0');
}

// ═══════════════════════════════════════════════════════════════
// СЧЁТЧИК ПОКУПАТЕЛЕЙ (social proof)
// ═══════════════════════════════════════════════════════════════

function initBuyersCounter() {
    const buyersEl = document.getElementById('buyers-count');
    if (!buyersEl) return;

    let count = CONFIG.initialBuyers;

    // Имитация роста (каждые 30-90 секунд +1)
    setInterval(() => {
        if (Math.random() > 0.7) {
            count++;
            buyersEl.textContent = count;

            // Небольшая анимация
            buyersEl.style.transform = 'scale(1.2)';
            setTimeout(() => {
                buyersEl.style.transform = 'scale(1)';
            }, 200);
        }
    }, 30000 + Math.random() * 60000);
}

// ═══════════════════════════════════════════════════════════════
// КНОПКИ
// ═══════════════════════════════════════════════════════════════

function initButtons() {
    const buyBtn = document.getElementById('btn-buy');
    const closeModalBtn = document.getElementById('btn-close-modal');
    const modal = document.getElementById('success-modal');
    const modalOverlay = document.querySelector('.modal-overlay');

    // Покупка курса
    if (buyBtn) {
        buyBtn.addEventListener('click', handleBuyClick);
    }

    // Закрытие модалки
    if (closeModalBtn) {
        closeModalBtn.addEventListener('click', closeModal);
    }

    if (modalOverlay) {
        modalOverlay.addEventListener('click', closeModal);
    }
}

function handleBuyClick() {
    // Открываем ссылку на оплату
    // В реальности здесь будет URL от ЮKassa

    if (CONFIG.tg) {
        // Отправляем запрос на создание платежа
        CONFIG.tg.sendData(JSON.stringify({
            action: 'buy_course',
            price: 4790,
            timestamp: Date.now()
        }));

        // Можно показать сообщение
        CONFIG.tg.showAlert('Переходим к оплате...');
    } else {
        alert('Для покупки откройте приложение в Telegram');
    }
}

// ═══════════════════════════════════════════════════════════════
// МОДАЛЬНОЕ ОКНО
// ═══════════════════════════════════════════════════════════════

function showModal() {
    const modal = document.getElementById('success-modal');
    if (modal) {
        modal.classList.add('active');

        // Haptic feedback
        if (CONFIG.tg?.HapticFeedback) {
            CONFIG.tg.HapticFeedback.notificationOccurred('success');
        }
    }
}

function closeModal() {
    const modal = document.getElementById('success-modal');
    if (modal) {
        modal.classList.remove('active');
    }

    // Закрываем Mini App если в Telegram
    if (CONFIG.tg) {
        setTimeout(() => {
            CONFIG.tg.close();
        }, 300);
    }
}

// ═══════════════════════════════════════════════════════════════
// УТИЛИТЫ
// ═══════════════════════════════════════════════════════════════

function formatDate(date) {
    return date.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        hour: '2-digit',
        minute: '2-digit'
    });
}
