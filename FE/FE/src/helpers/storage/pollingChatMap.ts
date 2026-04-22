import secureStorage from 'react-secure-storage';
import { SECURE_STORAGE_KEYS } from './secureStorageKeys.ts';

type PollingChatMap = Record<string, string>; // role -> chatId

function readMap(): PollingChatMap {
  try {
    const raw = secureStorage.getItem(SECURE_STORAGE_KEYS.POLLING_CHAT_MAP) as string | null;
    return raw ? (JSON.parse(raw) as PollingChatMap) : {};
  } catch {
    return {};
  }
}

function writeMap(map: PollingChatMap): void {
  secureStorage.setItem(SECURE_STORAGE_KEYS.POLLING_CHAT_MAP, JSON.stringify(map));
}

export function setPollingChat(role: string, chatId: string): void {
  const map = readMap();
  map[role] = chatId;
  writeMap(map);
}

export function getPollingChat(role: string): string | null {
  return readMap()[role] ?? null;
}

export function clearPollingChat(role: string): void {
  const map = readMap();
  delete map[role];
  writeMap(map);
}
