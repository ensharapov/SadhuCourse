/**
 * Экран 3: Спецпредложение (Sales Page) — после эфира
 */

import { useTelegram } from '../hooks/useTelegram';
import { CountdownTimer } from '../components/CountdownTimer';
import type { AppMode } from '../types/telegram';

interface SalesScreenProps {
    appMode: AppMode | null;
    onBack: () => void;
}

export function SalesScreen({ appMode, onBack }: SalesScreenProps) {
    const { openLink, hapticFeedback, hapticImpact } = useTelegram();

    const handleBuy = () => {
        hapticFeedback('success');
        // Ссылка на оплату
        openLink('https://p.edpro.biz/offer-link', true);
    };

    const deadline = appMode?.deadline ? new Date(appMode.deadline) : null;
    const price = appMode?.course_price || 5990;
    const discountPrice = appMode?.course_price_discount || 4790;
    const discount = Math.round((1 - discountPrice / price) * 100);

    const isExpired = appMode?.mode === 'offer_expired';

    return (
        <div className="min-h-screen flex flex-col p-5">
            {/* Back button */}
            <button
                onClick={() => {
                    hapticImpact('light');
                    onBack();
                }}
                className="flex items-center gap-2 text-white/60 mb-4"
            >
                ← Назад
            </button>

            {/* Hero */}
            <div className="text-center mb-6 animate-fade-in">
                <div className="inline-block px-4 py-2 bg-red-500/20 text-red-400 rounded-full text-sm font-medium mb-4">
                    🔥 Специальное предложение
                </div>

                <h1 className="text-3xl font-bold mb-3">
                    Курс «ГВОЗДИ ПРОСТО»
                </h1>

                <p className="text-white/70">
                    Полный курс по практике досок Садху
                </p>
            </div>

            {/* Таймер */}
            {!isExpired && deadline && (
                <div className="card mb-6 animate-slide-up">
                    <p className="text-center text-white/60 text-sm mb-2">
                        ⏱ Скидка действует:
                    </p>
                    <CountdownTimer
                        deadline={deadline}
                        size="large"
                        onExpire={() => {
                            hapticFeedback('warning');
                        }}
                    />
                </div>
            )}

            {/* Цена */}
            <div className="card mb-6">
                <div className="flex items-center justify-center gap-4 mb-4">
                    <span className="text-2xl text-white/40 line-through">
                        {price.toLocaleString()} ₽
                    </span>
                    <span className="text-4xl font-bold bg-gradient-to-r from-orange-400 to-amber-400 bg-clip-text text-transparent">
                        {discountPrice.toLocaleString()} ₽
                    </span>
                    <span className="px-3 py-1 bg-green-500/20 text-green-400 rounded-full text-sm font-medium">
                        -{discount}%
                    </span>
                </div>
            </div>

            {/* Что внутри */}
            <div className="card mb-6 flex-1">
                <h3 className="text-lg font-semibold mb-4">Что входит в курс:</h3>
                <ul className="space-y-3">
                    <li className="flex items-start gap-3">
                        <span className="text-green-500 mt-0.5">✓</span>
                        <span className="text-white/80">6 видео-уроков теории</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-green-500 mt-0.5">✓</span>
                        <span className="text-white/80">Пошаговые практики</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-green-500 mt-0.5">✓</span>
                        <span className="text-white/80">40-дневный марафон трансформации</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-green-500 mt-0.5">✓</span>
                        <span className="text-white/80">Чек-лист безопасности</span>
                    </li>
                    <li className="flex items-start gap-3">
                        <span className="text-green-500 mt-0.5">✓</span>
                        <span className="text-white/80">Бонус: дневник практик</span>
                    </li>
                </ul>
            </div>

            {/* CTA */}
            {isExpired ? (
                <div className="text-center p-4 bg-white/5 rounded-xl border border-white/10">
                    <p className="text-white/60">
                        ❌ Скидка закончилась
                    </p>
                    <p className="text-sm text-white/40 mt-2">
                        Курс доступен по полной цене на платформе
                    </p>
                </div>
            ) : (
                <button
                    onClick={handleBuy}
                    className="btn btn-primary w-full text-lg py-4"
                >
                    Записаться на курс 🔥
                </button>
            )}

            {/* Social Proof */}
            <div className="flex items-center justify-center gap-2 mt-4 text-white/50 text-sm">
                <div className="flex -space-x-2">
                    <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-xs">👤</div>
                    <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-xs">👤</div>
                    <div className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center text-xs">👤</div>
                </div>
                <span>50+ уже купили</span>
            </div>
        </div>
    );
}
