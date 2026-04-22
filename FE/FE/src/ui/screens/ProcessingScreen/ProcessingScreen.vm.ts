import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import secureStorage from 'react-secure-storage';
import { usePersonaStore } from '../../../store/personaStore.ts';
import { getPersonaConfig } from '../../../helpers/data/personaConfig.ts';
import { PERSONA_TO_ANALYST_TYPE } from '../../../helpers/config/analystTypeMap.ts';
import { SECURE_STORAGE_KEYS } from '../../../helpers/storage/secureStorageKeys.ts';

type StepStatus = 'pending' | 'active' | 'done';

const STEP_DURATION = 2000;
const STEP_GAP = 200;

export function useProcessingVM() {
  const navigate = useNavigate();
  const activePersona = usePersonaStore((s) => s.activePersona);
  const companySetup = usePersonaStore((s) => s.companySetup);
  const setAppPhase = usePersonaStore((s) => s.setAppPhase);

  const config = getPersonaConfig(activePersona.id);
  const companyName = companySetup?.name ?? 'Company';

  const steps = config.documents.map((doc, i) => ({
    label: doc,
    delay: i * (STEP_DURATION + STEP_GAP),
    duration: STEP_DURATION,
  }));

  const totalDuration = steps.length * (STEP_DURATION + STEP_GAP) - STEP_GAP + 400;

  const [statuses, setStatuses] = useState<StepStatus[]>(steps.map(() => 'pending'));

  const doneCount = statuses.filter((s) => s === 'done').length;
  const progress = steps.length > 0 ? (doneCount / steps.length) * 100 : 0;

  useEffect(() => {
    const timers: ReturnType<typeof setTimeout>[] = [];

    steps.forEach((step, i) => {
      timers.push(setTimeout(() => {
        setStatuses((prev) => { const next = [...prev]; next[i] = 'active'; return next; });
      }, step.delay));
      timers.push(setTimeout(() => {
        setStatuses((prev) => { const next = [...prev]; next[i] = 'done'; return next; });
      }, step.delay + step.duration));
    });

    // After animation completes, navigate to /landing (not /ready)
    timers.push(setTimeout(() => {
      const analystType = PERSONA_TO_ANALYST_TYPE[activePersona.id];
      if (analystType) {
        secureStorage.setItem(SECURE_STORAGE_KEYS.ROLE, analystType);
      }
      setAppPhase('landing');
      navigate('/landing');
    }, totalDuration));

    return () => timers.forEach(clearTimeout);
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return { companyName, steps, statuses, progress, doneCount };
}
 