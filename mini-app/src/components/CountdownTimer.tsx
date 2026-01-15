/**
 * Компонент обратного отсчёта
 */

import { useEffect, useState, useMemo } from 'react';

interface CountdownTimerProps {
    deadline: string | Date;
    onExpire?: () => void;
    className?: string;
    size?: 'small' | 'medium' | 'large';
}

interface TimeLeft {
    days: number;
    hours: number;
    minutes: number;
    seconds: number;
    total: number;
}

function calculateTimeLeft(deadline: Date): TimeLeft {
    const now = new Date();
    const diff = deadline.getTime() - now.getTime();

    if (diff <= 0) {
        return { days: 0, hours: 0, minutes: 0, seconds: 0, total: 0 };
    }

    return {
        days: Math.floor(diff / (1000 * 60 * 60 * 24)),
        hours: Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60)),
        minutes: Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60)),
        seconds: Math.floor((diff % (1000 * 60)) / 1000),
        total: diff
    };
}

export function CountdownTimer({
    deadline,
    onExpire,
    className = '',
    size = 'medium'
}: CountdownTimerProps) {
    const deadlineDate = useMemo(() =>
        deadline instanceof Date ? deadline : new Date(deadline),
        [deadline]
    );

    const [timeLeft, setTimeLeft] = useState<TimeLeft>(() => calculateTimeLeft(deadlineDate));

    useEffect(() => {
        const timer = setInterval(() => {
            const newTimeLeft = calculateTimeLeft(deadlineDate);
            setTimeLeft(newTimeLeft);

            if (newTimeLeft.total <= 0) {
                clearInterval(timer);
                onExpire?.();
            }
        }, 1000);

        return () => clearInterval(timer);
    }, [deadlineDate, onExpire]);

    const sizeClasses = {
        small: 'text-xl',
        medium: 'text-3xl',
        large: 'text-5xl'
    };

    const labelClasses = {
        small: 'text-[10px]',
        medium: 'text-xs',
        large: 'text-sm'
    };

    const pad = (n: number) => String(n).padStart(2, '0');

    if (timeLeft.total <= 0) {
        return (
            <div className={`text-center ${className}`}>
                <span className="text-2xl font-bold text-red-500">Время вышло!</span>
            </div>
        );
    }

    return (
        <div className={`flex justify-center gap-3 ${className}`}>
            {timeLeft.days > 0 && (
                <>
                    <div className="timer-block">
                        <span className={`timer-value ${sizeClasses[size]}`}>{pad(timeLeft.days)}</span>
                        <span className={`timer-label ${labelClasses[size]}`}>дней</span>
                    </div>
                    <span className={`${sizeClasses[size]} text-white/30 self-start mt-1`}>:</span>
                </>
            )}

            <div className="timer-block">
                <span className={`timer-value ${sizeClasses[size]}`}>{pad(timeLeft.hours)}</span>
                <span className={`timer-label ${labelClasses[size]}`}>часов</span>
            </div>

            <span className={`${sizeClasses[size]} text-white/30 self-start mt-1`}>:</span>

            <div className="timer-block">
                <span className={`timer-value ${sizeClasses[size]}`}>{pad(timeLeft.minutes)}</span>
                <span className={`timer-label ${labelClasses[size]}`}>минут</span>
            </div>

            {size !== 'small' && (
                <>
                    <span className={`${sizeClasses[size]} text-white/30 self-start mt-1`}>:</span>
                    <div className="timer-block">
                        <span className={`timer-value ${sizeClasses[size]}`}>{pad(timeLeft.seconds)}</span>
                        <span className={`timer-label ${labelClasses[size]}`}>секунд</span>
                    </div>
                </>
            )}
        </div>
    );
}
