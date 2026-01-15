/**
 * Экран 4: Инструменты (Дневник и Таймер)
 * Синхронизация с бэкендом
 */

import { useState, useEffect, useRef } from 'react';
import { useTelegram } from '../hooks/useTelegram';
import { useApi } from '../hooks/useApi';

interface ToolsScreenProps {
    onBack: () => void;
}

export function ToolsScreen({ onBack }: ToolsScreenProps) {
    const { userId, hapticImpact, hapticFeedback } = useTelegram();
    const { getPractice, savePractice, resetPractice, loading } = useApi();

    // Таймер
    const [seconds, setSeconds] = useState(0);
    const [isRunning, setIsRunning] = useState(false);
    const intervalRef = useRef<number | null>(null);

    // Трекер 21 дня
    const [completedDays, setCompletedDays] = useState<number[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    // Загрузка прогресса при монтировании
    useEffect(() => {
        if (userId) {
            loadProgress();
        } else {
            // Fallback на localStorage для разработки
            const saved = localStorage.getItem('sadhu_completed_days');
            setCompletedDays(saved ? JSON.parse(saved) : []);
            setIsLoading(false);
        }
    }, [userId]);

    const loadProgress = async () => {
        if (!userId) return;

        setIsLoading(true);
        const data = await getPractice(userId);
        if (data) {
            setCompletedDays(data.completed_days);
        }
        setIsLoading(false);
    };

    useEffect(() => {
        if (isRunning) {
            intervalRef.current = setInterval(() => {
                setSeconds(s => s + 1);
            }, 1000);
        } else if (intervalRef.current) {
            clearInterval(intervalRef.current);
        }

        return () => {
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, [isRunning]);

    const formatTime = (totalSeconds: number) => {
        const mins = Math.floor(totalSeconds / 60);
        const secs = totalSeconds % 60;
        return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
    };

    const handleStartStop = () => {
        hapticImpact(isRunning ? 'medium' : 'light');

        if (isRunning && seconds > 0) {
            // Сохраняем практику при остановке
            savePracticeToServer();
        }

        setIsRunning(!isRunning);
    };

    const savePracticeToServer = async () => {
        if (!userId) {
            // Fallback на localStorage
            const dayIndex = completedDays.length + 1;
            if (dayIndex <= 21 && !completedDays.includes(dayIndex)) {
                const newDays = [...completedDays, dayIndex];
                setCompletedDays(newDays);
                localStorage.setItem('sadhu_completed_days', JSON.stringify(newDays));
            }
            return;
        }

        const result = await savePractice({
            telegram_id: userId,
            duration: seconds
        });

        if (result) {
            setCompletedDays(result.completed_days);
            hapticFeedback('success');
        }
    };

    const handleReset = () => {
        hapticImpact('heavy');
        setIsRunning(false);
        setSeconds(0);
    };

    const handleResetTracker = async () => {
        hapticFeedback('warning');

        if (userId) {
            await resetPractice(userId);
        } else {
            localStorage.removeItem('sadhu_completed_days');
        }

        setCompletedDays([]);
    };

    const progress = Math.round((completedDays.length / 21) * 100);

    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center">
                <div className="text-center">
                    <div className="w-12 h-12 rounded-full border-4 border-white/20 border-t-orange-500 animate-spin mx-auto mb-4" />
                    <p className="text-white/60">Загрузка прогресса...</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen p-5">
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

            <h1 className="text-2xl font-bold mb-6">⏱ Инструменты</h1>

            {/* Таймер практики */}
            <div className="card mb-6 animate-fade-in">
                <h3 className="text-lg font-semibold mb-4 text-center">
                    Таймер практики
                </h3>

                {/* Круговой дисплей */}
                <div className="flex justify-center mb-6">
                    <div className="w-40 h-40 rounded-full border-4 border-white/20 flex items-center justify-center relative">
                        {/* Прогресс-кольцо */}
                        <svg className="absolute inset-0 w-full h-full -rotate-90" viewBox="0 0 100 100">
                            <circle
                                cx="50"
                                cy="50"
                                r="46"
                                fill="none"
                                stroke="url(#gradient)"
                                strokeWidth="4"
                                strokeDasharray={`${Math.min(seconds / 300, 1) * 289} 289`}
                                strokeLinecap="round"
                            />
                            <defs>
                                <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                                    <stop offset="0%" stopColor="#ff6b35" />
                                    <stop offset="100%" stopColor="#d4a853" />
                                </linearGradient>
                            </defs>
                        </svg>

                        <span className="text-4xl font-bold tabular-nums">
                            {formatTime(seconds)}
                        </span>
                    </div>
                </div>

                {/* Кнопки управления */}
                <div className="flex gap-3">
                    <button
                        onClick={handleStartStop}
                        disabled={loading}
                        className={`btn flex-1 ${isRunning ? 'btn-secondary' : 'btn-primary'}`}
                    >
                        {isRunning ? '⏸ Пауза' : '▶️ Старт'}
                    </button>
                    <button
                        onClick={handleReset}
                        className="btn btn-secondary"
                        disabled={seconds === 0}
                    >
                        🔄
                    </button>
                </div>

                {seconds > 0 && !isRunning && (
                    <p className="text-center text-sm text-white/50 mt-3">
                        Практика будет сохранена автоматически
                    </p>
                )}
            </div>

            {/* Трекер 21 дня */}
            <div className="card animate-slide-up">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold">
                        🗓 Трекер 21 дня
                    </h3>
                    <span className="text-sm text-white/60">
                        {completedDays.length}/21 ({progress}%)
                    </span>
                </div>

                {/* Прогресс */}
                <div className="h-2 bg-white/10 rounded-full mb-4 overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-orange-500 to-amber-500 transition-all duration-300"
                        style={{ width: `${progress}%` }}
                    />
                </div>

                {/* Сетка дней */}
                <div className="grid grid-cols-7 gap-2 mb-4">
                    {Array.from({ length: 21 }, (_, i) => i + 1).map(day => (
                        <div
                            key={day}
                            className={`
                aspect-square rounded-lg text-sm font-medium flex items-center justify-center
                ${completedDays.includes(day)
                                    ? 'bg-gradient-to-br from-orange-500 to-amber-500 text-white shadow-lg shadow-orange-500/30'
                                    : 'bg-white/5 text-white/40'}
              `}
                        >
                            {completedDays.includes(day) ? '✓' : day}
                        </div>
                    ))}
                </div>

                {/* Инфо */}
                <p className="text-xs text-white/40 text-center mb-3">
                    Практики сохраняются автоматически при остановке таймера
                </p>

                {/* Сброс */}
                {completedDays.length > 0 && (
                    <button
                        onClick={handleResetTracker}
                        disabled={loading}
                        className="text-sm text-white/40 hover:text-white/60 w-full text-center"
                    >
                        Сбросить прогресс
                    </button>
                )}
            </div>
        </div>
    );
}
