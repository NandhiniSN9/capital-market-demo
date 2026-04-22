import { IChatListService } from './IChatListService.ts';
import { ChatListService } from './chatListService.ts';

export const chatListService: IChatListService = new ChatListService();
