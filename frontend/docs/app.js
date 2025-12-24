const tg = window.Telegram.WebApp;

// Initialize Telegram Web App
tg.expand();
tg.ready();

// Timer Logic (Every Sunday at 18:00)
function updateTimer() {
    const now = new Date();
    // 0 = Sunday
    const dayOfWeek = now.getDay(); 
    const hours = now.getHours();
    
    // Calculate next Sunday 18:00
    let daysUntilSunday = 0 - dayOfWeek;
    if (daysUntilSunday <= 0 && hours >= 18) {
        // If it's already past 18:00 on Sunday, or it is Sunday, move to next week
        daysUntilSunday += 7;
    } else if (daysUntilSunday < 0) {
        // If it's Mon-Sat
        daysUntilSunday += 7;
    }
    
    // Target Date
    const target = new Date(now);
    target.setDate(now.getDate() + daysUntilSunday);
    target.setHours(18, 0, 0, 0);

    // If target is in the past (e.g. current Sunday before 18:00 logic handled above?)
    // Actually simpler logic: Find next occurrence of Sun 18:00
    if (target < now) {
        target.setDate(target.getDate() + 7);
    }

    const diff = target - now;

    const d = Math.floor(diff / (1000 * 60 * 60 * 24));
    const h = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
    const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

    document.getElementById('days').innerText = String(d).padStart(2, '0');
    document.getElementById('hours').innerText = String(h).padStart(2, '0');
    document.getElementById('minutes').innerText = String(m).padStart(2, '0');
}

setInterval(updateTimer, 60000); // Update every minute
updateTimer(); // Initial call

// Handlers
function handleRegistration() {
    // Show visual feedback
    const btn = document.getElementById('btn-register');
    btn.innerHTML = 'Записываем...';
    btn.disabled = true;

    // Simulate network request
    setTimeout(() => {
        // Show success modal
        document.getElementById('success-modal').classList.remove('hidden');
        
        // Haptic feedback if available
        if (tg.HapticFeedback) {
            tg.HapticFeedback.notificationOccurred('success');
        }

        // Send data to bot (User registered)
        // We send a stringified JSON object that the bot can parse
        const data = JSON.stringify({
            action: 'register_webinar',
            date: new Date().toISOString()
        });
        
        // Note: sendData closes the app. If we want to keep it open, we rely on server requests.
        // For this demo, we might just want to show the modal and let user close manually 
        // OR we use sendData when they click "Awesome" in the modal.
    }, 800);
}

function closeApp() {
    const data = JSON.stringify({
        action: 'register_webinar',
        status: 'confirmed'
    });
    tg.sendData(data);
    // fallback
    setTimeout(() => tg.close(), 100);
}

function handleBuyClick() {
    // Open payment link
    // Replace with actual link
    tg.openLink('https://yoomoney.ru/to/YOUR_WALLET'); 
}

// Theming support
document.documentElement.style.setProperty('--tg-theme-bg-color', tg.backgroundColor || '#0F0F13');
document.documentElement.style.setProperty('--tg-theme-text-color', tg.textColor || '#FFFFFF');
document.documentElement.style.setProperty('--tg-theme-button-color', tg.buttonColor || '#FF8c42');
document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.buttonTextColor || '#000000');
