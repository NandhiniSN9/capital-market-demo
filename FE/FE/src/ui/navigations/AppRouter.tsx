import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { RoleSelectionScreen } from '../screens/RoleSelectionScreen/RoleSelectionScreen.tsx';
import { LandingScreen } from '../screens/LandingScreen/LandingScreen.tsx';
import { SetupScreen } from '../screens/SetupScreen/SetupScreen.tsx';
import { ProcessingScreen } from '../screens/ProcessingScreen/ProcessingScreen.tsx';
import { ChatScreen } from '../screens/ChatScreen/ChatScreen.tsx';
import { usePersonaStore } from '../../store/personaStore.ts';

/** Keeps the URL in sync with the store phase on first load */
function PhaseSync() {
  const appPhase = usePersonaStore((s) => s.appPhase);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const phaseRoute = `/${appPhase}`;
    if (location.pathname === '/' || location.pathname !== phaseRoute) {
      navigate(phaseRoute, { replace: true });
    }
  }, []); // run once on mount

  return null;
}

export function AppRouter() {
  return (
    <BrowserRouter basename="/">
      <PhaseSync />
      <Routes>
        <Route path="/" element={<Navigate to="/role-select" replace />} />
        <Route path="/role-select" element={<RoleSelectionScreen />} />
        <Route path="/landing" element={<LandingScreen />} />
        <Route path="/setup" element={<SetupScreen />} />
        <Route path="/processing" element={<ProcessingScreen />} />
        <Route path="/ready" element={<ChatScreen />} />
        <Route path="*" element={<Navigate to="/role-select" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
