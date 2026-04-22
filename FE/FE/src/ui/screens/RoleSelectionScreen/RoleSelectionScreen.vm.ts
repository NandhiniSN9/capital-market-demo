import { useNavigate } from 'react-router-dom';
import secureStorage from 'react-secure-storage';
import { usePersonaStore } from '../../../store/personaStore.ts';
import { PersonaBO } from '../../../types/persona/PersonaBO.ts';
import { PERSONA_TO_ANALYST_TYPE } from '../../../helpers/config/analystTypeMap.ts';
import { SECURE_STORAGE_KEYS } from '../../../helpers/storage/secureStorageKeys.ts';

export function useRoleSelectionVM() {
  const navigate = useNavigate();
  const personas = usePersonaStore((s) => s.personas);
  const selectRole = usePersonaStore((s) => s.selectRole);

  const handleSelectRole = (personaId: string) => {
    const analystType = PERSONA_TO_ANALYST_TYPE[personaId];
    if (analystType) {
      secureStorage.setItem(SECURE_STORAGE_KEYS.ROLE, analystType);
    }

    selectRole(personaId);
    navigate('/landing');
  };

  return {
    personas: personas as PersonaBO[],
    handleSelectRole,
  };
}
