// Persona-specific user profiles — in a real app this would come from auth context
export const PERSONA_PROFILES: Record<string, { name: string; photo: string }> = {
  'buy-side-equity': {
    name: 'Marcus Chen',
    photo: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face&auto=format&q=80',
  },
  'sell-side-equity': {
    name: 'Sarah Mitchell',
    photo: 'https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=100&h=100&fit=crop&crop=face&auto=format&q=80',
  },
  'credit': {
    name: 'David Okafor',
    photo: 'https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=100&h=100&fit=crop&crop=face&auto=format&q=80',
  },
  'dcm': {
    name: 'Elena Vasquez',
    photo: 'https://images.unsplash.com/photo-1573496359142-b8d87734a5a2?w=100&h=100&fit=crop&crop=face&auto=format&q=80',
  },
  'private-markets': {
    name: 'James Harrington',
    photo: 'https://images.unsplash.com/photo-1560250097-0b93528c311a?w=100&h=100&fit=crop&crop=face&auto=format&q=80',
  },
};

const DEFAULT_PROFILE = {
  name: 'John Doe',
  photo: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=100&h=100&fit=crop&crop=face&auto=format&q=80',
};

export function getPersonaProfile(personaId: string) {
  return PERSONA_PROFILES[personaId] || DEFAULT_PROFILE;
}

export function getPersonaPhoto(personaId: string) {
  return (PERSONA_PROFILES[personaId] || DEFAULT_PROFILE).photo;
}
