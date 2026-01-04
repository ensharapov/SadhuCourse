/**
 * Хук для работы с API бэкенда
 */

import { useState, useCallback } from 'react';
import type { UserData, AppMode, ReferralInfo } from '../types/telegram';

// Hardcode API URL to prevent ENV issues
const API_BASE = 'https://web-production-fbbc.up.railway.app';
// const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8080';

interface ApiResponse<T> {
    success: boolean;
    data?: T;
    error?: string;
}

export function useApi() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchApi = useCallback(async <T>(
        endpoint: string,
        options?: RequestInit
    ): Promise<T | null> => {
        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE}${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                },
                ...options,
            });

            const result: ApiResponse<T> = await response.json();

            if (result.success && result.data) {
                return result.data;
            } else {
                setError(result.error || 'Unknown error');
                return null;
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Network error');
            return null;
        } finally {
            setLoading(false);
        }
    }, []);

    const getUserData = useCallback(async (telegramId: number): Promise<UserData | null> => {
        return fetchApi<UserData>(`/api/user/${telegramId}`);
    }, [fetchApi]);

    const getAppMode = useCallback(async (): Promise<AppMode | null> => {
        return fetchApi<AppMode>('/api/mode');
    }, [fetchApi]);

    const getReferralLink = useCallback(async (telegramId: number): Promise<ReferralInfo | null> => {
        return fetchApi<ReferralInfo>(`/api/referral/${telegramId}`);
    }, [fetchApi]);

    const registerUser = useCallback(async (data: {
        telegram_id: number;
        name?: string;
        phone?: string;
        goal?: string;
    }): Promise<UserData | null> => {
        return fetchApi<UserData>('/api/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }, [fetchApi]);

    // Трекер практики
    interface PracticeData {
        completed_days: number[];
        total_days: number;
        target_days: number;
        logs?: Array<{
            practice_date: string;
            duration_seconds: number;
        }>;
    }

    const getPractice = useCallback(async (telegramId: number): Promise<PracticeData | null> => {
        return fetchApi<PracticeData>(`/api/practice/${telegramId}`);
    }, [fetchApi]);

    const savePractice = useCallback(async (data: {
        telegram_id: number;
        date?: string;
        duration?: number;
    }): Promise<PracticeData | null> => {
        return fetchApi<PracticeData>('/api/practice', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }, [fetchApi]);

    const resetPractice = useCallback(async (telegramId: number): Promise<boolean> => {
        const result = await fetch(`${API_BASE}/api/practice/${telegramId}`, {
            method: 'DELETE',
        });
        const json = await result.json();
        return json.success;
    }, []);

    return {
        loading,
        error,
        getUserData,
        getAppMode,
        getReferralLink,
        registerUser,
        getPractice,
        savePractice,
        resetPractice,
    };
}

