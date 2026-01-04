/**
 * Экран 1: Welcome-онбординг и Регистрация
 */

import { useState } from 'react';
import { useTelegram } from '../hooks/useTelegram';
import { useApi } from '../hooks/useApi';

interface WelcomeScreenProps {
    onComplete: () => void;
}

type Goal = 'stress' | 'energy' | 'health';

export function WelcomeScreen({ onComplete: _onComplete }: WelcomeScreenProps) {
    const { user, userId, hapticFeedback, sendData } = useTelegram();
    const { registerUser, loading } = useApi();

    const [name, setName] = useState(user?.first_name || '');
    const [phone, setPhone] = useState('');
    const [goal, setGoal] = useState<Goal | ''>('');
    const [errorMsg, setErrorMsg] = useState<string | null>(null);

    // Проверяем URL параметр для прямого перехода на форму
    const urlParams = new URLSearchParams(window.location.search);
    const skipIntro = urlParams.get('form') === '1';
    const [step, setStep] = useState<'intro' | 'form'>(skipIntro ? 'form' : 'intro');

    const handleRegister = async () => {
        if (!userId || !goal) return;
        setErrorMsg(null);

        hapticFeedback('success');

        try {
            const result = await registerUser({
                telegram_id: userId,
                name,
                phone,
                goal
            });

            if (result) {
                // Отправляем данные боту и закрываем приложение
                sendData({
                    action: 'register_webinar',
                    name,
                    phone,
                    goal
                });
            } else {
                throw new Error('API returned null');
            }
        } catch (e) {
            hapticFeedback('error');
            const msg = e instanceof Error ? e.message : String(e);
            setErrorMsg(msg);

            // Пытаемся показать сообщение об ошибке
            if (window.Telegram?.WebApp) {
                window.Telegram.WebApp.showAlert(`Ошибка: ${msg}\nAPI: ${import.meta.env.VITE_API_URL || 'HARDCODED'}`);
            } else {
                alert(`Ошибка: ${msg}`);
            }
        }
    };

    if (step === 'intro') {
        return (
            <div className="min-h-screen flex flex-col p-5">
                {/* Hero */}
                <div className="flex-1 flex flex-col items-center justify-center text-center animate-fade-in">
                    {/* Иконка */}
                    <div className="w-24 h-24 rounded-full bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center mb-6 shadow-lg shadow-orange-500/30">
                        <span className="text-5xl">🔥</span>
                    </div>

                    <h1 className="text-3xl font-bold mb-3">
                        Гвозди Просто
                    </h1>

                    <p className="text-white/70 text-lg mb-8 max-w-xs">
                        Безопасный вход в практику досок Садху
                    </p>

                    {/* Цитата */}
                    <div className="card mb-8 max-w-sm">
                        <p className="text-lg italic text-white/90">
                            «Твой путь к внутренней силе начинается здесь»
                        </p>
                    </div>

                    {/* Что получишь */}
                    <div className="w-full max-w-sm space-y-3 mb-8">
                        <div className="flex items-center gap-3 text-left">
                            <span className="text-2xl">🎯</span>
                            <span className="text-white/80">Теория и практика</span>
                        </div>
                        <div className="flex items-center gap-3 text-left">
                            <span className="text-2xl">💬</span>
                            <span className="text-white/80">Ответы на вопросы</span>
                        </div>
                        <div className="flex items-center gap-3 text-left">
                            <span className="text-2xl">🎁</span>
                            <span className="text-white/80">Розыгрыш доски Садху</span>
                        </div>
                    </div>
                </div>

                {/* CTA */}
                <button
                    onClick={() => {
                        hapticFeedback('success');
                        setStep('form');
                    }}
                    className="btn btn-primary w-full text-lg py-4"
                >
                    Забронировать место на эфир ✨
                </button>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex flex-col p-5 animate-slide-up">
            {/* Header */}
            <div className="text-center mb-8">
                <h2 className="text-2xl font-bold mb-2">Регистрация на эфир</h2>
                <p className="text-white/60">Заполни форму для участия</p>
            </div>

            {/* Form */}
            <div className="flex-1 space-y-5">
                <div>
                    <label className="block text-sm text-white/60 mb-2">Имя</label>
                    <input
                        type="text"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        placeholder="Как тебя зовут?"
                        className="input"
                    />
                </div>

                <div>
                    <label className="block text-sm text-white/60 mb-2">Телефон (опционально)</label>
                    <input
                        type="tel"
                        value={phone}
                        onChange={(e) => setPhone(e.target.value)}
                        placeholder="+7 (___) ___-__-__"
                        className="input"
                    />
                </div>

                <div>
                    <label className="block text-sm text-white/60 mb-2">Какую цель хочешь достичь?</label>
                    <select
                        value={goal}
                        onChange={(e) => setGoal(e.target.value as Goal)}
                        className="select"
                    >
                        <option value="" disabled>Выбери цель...</option>
                        <option value="stress">🧘 Снизить стресс</option>
                        <option value="energy">⚡ Повысить энергию</option>
                        <option value="health">💪 Улучшить здоровье</option>
                    </select>
                </div>
            </div>

            {/* Submit */}
            <div className="space-y-3 mt-8">
                {errorMsg && (
                    <div className="text-red-500 text-sm text-center p-2 bg-red-900/20 rounded border border-red-500/30">
                        {errorMsg}
                        <div className="text-xs text-white/50 mt-1">
                            API: {import.meta.env.VITE_API_URL || 'HARDCODED'}
                        </div>
                    </div>
                )}
                <button
                    onClick={handleRegister}
                    disabled={!goal || loading}
                    className="btn btn-primary w-full text-lg py-4"
                >
                    {loading ? 'Регистрируем...' : 'Записаться на эфир 🔥'}
                </button>

                <button
                    onClick={() => setStep('intro')}
                    className="btn btn-secondary w-full"
                >
                    ← Назад
                </button>
            </div>
        </div>
    );
}
