/**
 * Компонент прогресс-бара для отображения прогресса рефералов
 */

interface ProgressBarProps {
    current: number;
    target: number;
    showLabel?: boolean;
    className?: string;
}

export function ProgressBar({ current, target, showLabel = true, className = '' }: ProgressBarProps) {
    const percentage = Math.min((current / target) * 100, 100);

    return (
        <div className={className}>
            {showLabel && (
                <div className="flex justify-between items-center mb-2">
                    <span className="text-sm text-white/70">
                        {current >= target
                            ? `🚀 Приглашено: ${current} (Цель: ${target})`
                            : `${current} из ${target} друзей`}
                    </span>
                    <span className="text-sm font-semibold text-white">
                        {Math.round(percentage)}%
                    </span>
                </div>
            )}
            <div className="progress-bar">
                <div
                    className="progress-bar-fill"
                    style={{ width: `${percentage}%` }}
                />
            </div>
        </div>
    );
}
