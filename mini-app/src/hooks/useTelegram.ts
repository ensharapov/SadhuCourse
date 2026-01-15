/**
 * Хук для работы с Telegram WebApp API
 */

import { useEffect, useState, useCallback } from 'react';
import type { TelegramWebApp, TelegramUser } from '../types/telegram';

export function useTelegram() {
    const [webApp, setWebApp] = useState<TelegramWebApp | null>(null);
    const [user, setUser] = useState<TelegramUser | null>(null);
    const [startParam, setStartParam] = useState<string | null>(null);
    const [isReady, setIsReady] = useState(false);

    useEffect(() => {
        const tg = window.Telegram?.WebApp;

        if (tg) {
            tg.ready();
            tg.expand();

            setWebApp(tg);
            setUser(tg.initDataUnsafe.user || null);
            setStartParam(tg.initDataUnsafe.start_param || null);
            setIsReady(true);

            // Применяем тему Telegram
            if (tg.themeParams.bg_color) {
                document.body.style.backgroundColor = tg.themeParams.bg_color;
            }
        } else {
            // Fallback для разработки вне Telegram
            console.warn('Telegram WebApp not available, using mock data');
            setUser({
                id: 123456789,
                first_name: 'Test',
                last_name: 'User',
                username: 'testuser'
            });
            setIsReady(true);
        }
    }, []);

    const hapticFeedback = useCallback((type: 'success' | 'error' | 'warning' = 'success') => {
        webApp?.HapticFeedback?.notificationOccurred(type);
    }, [webApp]);

    const hapticImpact = useCallback((style: 'light' | 'medium' | 'heavy' = 'light') => {
        webApp?.HapticFeedback?.impactOccurred(style);
    }, [webApp]);

    const openLink = useCallback((url: string, external = false) => {
        if (webApp) {
            if (external) {
                webApp.openLink(url);
            } else {
                webApp.openTelegramLink(url);
            }
        } else {
            window.open(url, '_blank');
        }
    }, [webApp]);

    const shareLink = useCallback((url: string, text: string) => {
        // Чтобы текст был сверху, а ссылка снизу (под пальцем 👇),
        // передаем всё в параметре text, а url оставляем пустым.
        // Добавляем двойной отступ (\n\n) для красоты.
        const fullText = `${text}\n\n${url}`;
        const shareUrl = `https://t.me/share/url?url=&text=${encodeURIComponent(fullText)}`;

        openLink(shareUrl, false);
        hapticImpact('medium');
    }, [openLink, hapticImpact]);

    const showAlert = useCallback((message: string) => {
        if (webApp) {
            webApp.showAlert(message);
        } else {
            alert(message);
        }
    }, [webApp]);

    const sendData = useCallback((data: object) => {
        if (webApp) {
            webApp.sendData(JSON.stringify(data));
        }
    }, [webApp]);

    const shareToStory = useCallback((mediaUrl: string, params?: { text?: string; widget_link?: { url: string; name?: string } }) => {
        webApp?.shareToStory(mediaUrl, params);
    }, [webApp]);

    const close = useCallback(() => {
        webApp?.close();
    }, [webApp]);

    return {
        webApp,
        user,
        startParam,
        isReady,
        userId: user?.id || null,
        hapticFeedback,
        hapticImpact,
        openLink,
        shareLink,
        showAlert,
        sendData,
        shareToStory,
        close
    };
}
