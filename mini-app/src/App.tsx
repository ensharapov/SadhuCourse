/**
 * Главный компонент приложения
 * Управляет навигацией между экранами и состоянием
 */

import { useState, useEffect } from 'react';
import { useTelegram } from './hooks/useTelegram';
import { useApi } from './hooks/useApi';
import { WelcomeScreen } from './screens/WelcomeScreen';
import { DashboardScreen } from './screens/DashboardScreen';
import { SalesScreen } from './screens/SalesScreen';
import { ToolsScreen } from './screens/ToolsScreen';
import type { Screen, AppMode, UserData } from './types/telegram';

function App() {
  const { isReady, userId } = useTelegram();
  const { getUserData, getAppMode } = useApi();

  const [screen, setScreen] = useState<Screen>('welcome');
  const [appMode, setAppMode] = useState<AppMode | null>(null);
  const [, setUserData] = useState<UserData | null>(null);
  const [loading, setLoading] = useState(true);

  // Загрузка начальных данных
  useEffect(() => {
    if (isReady) {
      loadInitialData();
    }
  }, [isReady, userId]);

  const loadInitialData = async () => {
    setLoading(true);

    try {
      // Загружаем режим приложения
      const mode = await getAppMode();
      setAppMode(mode);

      // Если есть userId, проверяем регистрацию
      if (userId) {
        const user = await getUserData(userId);
        setUserData(user);

        // Если уже зарегистрирован — показываем дашборд
        if (user?.is_registered) {
          setScreen('dashboard');
        }
      }
    } catch (error) {
      console.error('Failed to load initial data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRegistrationComplete = () => {
    setScreen('dashboard');
    // Обновляем данные пользователя
    if (userId) {
      getUserData(userId).then(setUserData);
    }
  };

  const handleNavigate = (newScreen: 'sales' | 'tools') => {
    setScreen(newScreen);
  };

  const handleBack = () => {
    setScreen('dashboard');
  };

  // Экран загрузки
  if (loading || !isReady) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-orange-500 to-amber-500 flex items-center justify-center mb-4 mx-auto animate-pulse">
            <span className="text-3xl">🔥</span>
          </div>
          <p className="text-white/60">Загрузка...</p>
        </div>
      </div>
    );
  }

  // Рендер текущего экрана
  switch (screen) {
    case 'welcome':
      return <WelcomeScreen onComplete={handleRegistrationComplete} />;

    case 'dashboard':
      return (
        <DashboardScreen
          appMode={appMode}
          onNavigate={handleNavigate}
        />
      );

    case 'sales':
      return (
        <SalesScreen
          appMode={appMode}
          onBack={handleBack}
        />
      );

    case 'tools':
      return <ToolsScreen onBack={handleBack} />;

    default:
      return <WelcomeScreen onComplete={handleRegistrationComplete} />;
  }
}

export default App;
