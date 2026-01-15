/**
 * Экран 2: Дашборд участника (Центр управления)
 */

import { useEffect, useState } from 'react';
import { useTelegram } from '../hooks/useTelegram';
import { useApi } from '../hooks/useApi';
import { ProgressBar } from '../components/ProgressBar';
import { CountdownTimer } from '../components/CountdownTimer';
import type { UserData, ReferralInfo, AppMode } from '../types/telegram';

interface DashboardScreenProps {
    appMode: AppMode | null;
    onNavigate: (screen: 'sales' | 'tools') => void;
}

export function DashboardScreen({ appMode, onNavigate }: DashboardScreenProps) {
    const { userId, shareLink, hapticImpact, shareToStory } = useTelegram();
    const { getUserData, getReferralLink, loading } = useApi();

    const [userData, setUserData] = useState<UserData | null>(null);
    const [referralInfo, setReferralInfo] = useState<ReferralInfo | null>(null);

    useEffect(() => {
        if (userId) {
            loadData();
        }
    }, [userId]);

    const loadData = async () => {
        if (!userId) return;

        const [user, referral] = await Promise.all([
            getUserData(userId),
            getReferralLink(userId)
        ]);

        setUserData(user);
        setReferralInfo(referral);
    };

    const handleInvite = () => {
        if (referralInfo) {
            hapticImpact('medium');
            shareLink(referralInfo.referral_link, referralInfo.share_text);
        }
    };

    const webinarDate = appMode?.webinar_date ? new Date(appMode.webinar_date) : null;
    const formattedDate = webinarDate?.toLocaleDateString('ru-RU', {
        day: 'numeric',
        month: 'long',
        hour: '2-digit',
        minute: '2-digit'
    });

    return (
        <div className="min-h-screen p-5 space-y-8">
            {/* Header */}
            <header className="flex items-center justify-between">
                <div>
                    <h1 className="text-xl font-bold">🔥 Гвозди Просто</h1>
                    <p className="text-sm text-white/60">Привет, {userData?.full_name?.split(' ')[0] || 'Участник'}!</p>
                </div>
                <div className="live-badge">
                    Бесплатный Эфир
                </div>
            </header>

            {/* Таймер до эфира */}
            {appMode?.mode === 'before_webinar' && webinarDate && (
                <div className="card animate-fade-in py-6">
                    <p className="text-center text-white/60 text-sm mb-4">До эфира осталось:</p>
                    <CountdownTimer deadline={webinarDate} size="medium" />
                    <p className="text-center text-white/50 text-sm mt-4">
                        📅 {formattedDate} МСК
                    </p>
                </div>
            )}

            {/* Блок розыгрыша */}
            <div className="card animate-slide-up">
                <div className="flex items-start justify-between mb-4">
                    <div>
                        <h3 className="text-lg font-semibold mb-1">🎁 Розыгрыш доски Садху</h3>
                        <p className="text-sm text-white/60">
                            {userData?.in_raffle
                                ? 'Ты участвуешь в розыгрыше!'
                                : 'Пригласи 2 друзей для участия'}
                        </p>
                    </div>
                </div>

                {/* Условия (новое) */}
                {!userData?.in_raffle && (
                    <div className="bg-white/5 rounded-lg p-3 mb-4 text-xs text-white/60 space-y-1">
                        <p>1. Нажми кнопку "Пригласить друга" 👇</p>
                        <p>2. Друг должен зарегистрироваться на эфир.</p>
                        <p>3. Когда наберется 2 друга, ты автоматически попадешь в список участников розыгрыша!</p>
                    </div>
                )}

                <ProgressBar
                    current={userData?.referrals || 0}
                    target={userData?.target_referrals || 2}
                    className="mb-4"
                />

                <div className="grid grid-cols-1 gap-2">
                    <button
                        onClick={handleInvite}
                        className="btn btn-primary w-full"
                        disabled={loading}
                    >
                        📲 Пригласить друга
                    </button>

                    <button
                        onClick={() => {
                            if (referralInfo) {
                                hapticImpact('heavy');
                                /* 
                                   Формируем URL картинки (она в public/story-bg.png).
                                   Используем текущий origin.
                                */
                                const bgUrl = window.location.origin + '/story-bg.png';

                                shareToStory(bgUrl, {
                                    text: `Иду на эфир по гвоздестоянию! 🧘\nЗаряжаться энергией и снимать стресс.\n\nКто со мной? 👇\n\n${referralInfo.referral_link}`,
                                    widget_link: {
                                        url: referralInfo.referral_link,
                                        name: 'Записаться'
                                    }
                                });
                            }
                        }}
                        className="btn btn-primary bg-gradient-to-r from-purple-500 to-pink-500 border-none w-full"
                        disabled={loading}
                    >
                        📸 В сторис
                    </button>
                </div>
            </div>

            {/* Блок подготовки */}
            <div className="card">
                <h3 className="text-lg font-semibold mb-4">📝 Подготовка к эфиру</h3>
                <ul className="space-y-3">
                    <li className="flex items-center gap-3 text-white/80">
                        <span className="text-green-500 text-lg">✓</span>
                        Приготовь воду 💧
                    </li>
                    <li className="flex items-center gap-3 text-white/80">
                        <span className="text-green-500 text-lg">✓</span>
                        Блокнот для заметок 📓
                    </li>
                    <li className="flex items-center gap-3 text-white/80">
                        <span className="text-green-500 text-lg">✓</span>
                        Тихое место 🧘
                    </li>
                    <li className="flex items-center gap-3 text-white/80">
                        <span className="text-green-500 text-lg">✓</span>
                        Позитивный настрой 🌟
                    </li>
                </ul>
            </div>

            {/* Блок подписки на канал */}
            <div className="card bg-gradient-to-r from-blue-900/50 to-purple-900/50 border border-blue-500/30">
                <div className="flex items-center gap-3 mb-3">
                    <span className="text-2xl">📢</span>
                    <h3 className="text-lg font-semibold">Подпишись на канал</h3>
                </div>
                <p className="text-white/70 text-sm mb-4">
                    Там анонсы эфиров, напоминания и полезные материалы по практике.
                </p>
                <button
                    onClick={() => {
                        hapticImpact('light');
                        window.open('https://t.me/telminov_life8', '_blank');
                    }}
                    className="btn btn-primary w-full"
                >
                    Перейти в канал →
                </button>
            </div>

            {/* Навигация */}
            <div className="grid grid-cols-2 gap-3 pt-2">
                {appMode?.mode === 'after_webinar' && (
                    <button
                        onClick={() => {
                            hapticImpact('light');
                            onNavigate('sales');
                        }}
                        className="btn btn-secondary"
                    >
                        💳 Курс со скидкой
                    </button>
                )}
                <button
                    onClick={() => {
                        hapticImpact('light');
                        onNavigate('tools');
                    }}
                    className="btn btn-secondary col-span-2 py-3"
                >
                    ⏱ Инструменты практики
                </button>
            </div>
        </div>
    );
}
