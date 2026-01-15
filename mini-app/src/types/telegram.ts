/**
 * Типы для Telegram WebApp API
 */

export interface TelegramUser {
    id: number;
    first_name: string;
    last_name?: string;
    username?: string;
    language_code?: string;
    is_premium?: boolean;
}

export interface TelegramWebApp {
    initData: string;
    initDataUnsafe: {
        user?: TelegramUser;
        start_param?: string;
    };
    version: string;
    platform: string;
    colorScheme: 'light' | 'dark';
    themeParams: {
        bg_color?: string;
        text_color?: string;
        hint_color?: string;
        link_color?: string;
        button_color?: string;
        button_text_color?: string;
        secondary_bg_color?: string;
    };
    isExpanded: boolean;
    viewportHeight: number;
    viewportStableHeight: number;

    ready(): void;
    expand(): void;
    close(): void;

    MainButton: {
        text: string;
        color: string;
        textColor: string;
        isVisible: boolean;
        isActive: boolean;
        isProgressVisible: boolean;
        setText(text: string): void;
        onClick(callback: () => void): void;
        offClick(callback: () => void): void;
        show(): void;
        hide(): void;
        enable(): void;
        disable(): void;
        showProgress(leaveActive?: boolean): void;
        hideProgress(): void;
    };

    BackButton: {
        isVisible: boolean;
        onClick(callback: () => void): void;
        offClick(callback: () => void): void;
        show(): void;
        hide(): void;
    };

    HapticFeedback: {
        impactOccurred(style: 'light' | 'medium' | 'heavy' | 'rigid' | 'soft'): void;
        notificationOccurred(type: 'error' | 'success' | 'warning'): void;
        selectionChanged(): void;
    };

    openLink(url: string): void;
    openTelegramLink(url: string): void;
    showAlert(message: string, callback?: () => void): void;
    showConfirm(message: string, callback?: (confirmed: boolean) => void): void;
    sendData(data: string): void;
    requestContact(callback: (shared: boolean) => void): void;
    shareToStory(media_url: string, params?: { text?: string; widget_link?: { url: string; name?: string } }): void;
}

declare global {
    interface Window {
        Telegram?: {
            WebApp: TelegramWebApp;
        };
    }
}

export interface UserData {
    user_id: number;
    username: string | null;
    full_name: string | null;
    is_registered: boolean;
    referrals: number;
    target_referrals: number;
    in_raffle: boolean;
}

export interface AppMode {
    mode: 'before_webinar' | 'live' | 'after_webinar' | 'offer_expired';
    webinar_date: string;
    seconds_until: number;
    deadline: string | null;
    course_price: number;
    course_price_discount: number;
}

export interface ReferralInfo {
    referral_link: string;
    share_text: string;
    share_url: string;
}

export type Screen = 'welcome' | 'dashboard' | 'sales' | 'tools';
