import { ServiceResult } from '../../types/service/ServiceResult.ts';
import { GetChatsRequestDTO } from './types/GetChatsRequestDTO.ts';
import { GetChatsResponseDTO } from './types/GetChatsResponseDTO.ts';
import { CreateChatResponseDTO } from './types/CreateChatResponseDTO.ts';
import { DeleteDocumentResponseDTO } from './types/DeleteDocumentResponseDTO.ts';
import { SendMessageRequestDTO } from './types/SendMessageRequestDTO.ts';
import { ConversationResponseDTO } from './types/ConversationResponseDTO.ts';
import { ConversationPollResponseDTO } from './types/ConversationPollResponseDTO.ts';
import { GetChatDetailResponseDTO } from './types/GetChatDetailResponseDTO.ts';
import { GetSessionMessagesResponseDTO } from './types/GetSessionMessagesResponseDTO.ts';
import { ChatStatusPollResponseDTO } from './types/ChatStatusPollResponseDTO.ts';

export interface CreateChatParams {
  companyName: string;
  companyUrl: string;
  analystType: string;
  files?: File[];
}

export interface UploadDocumentsParams {
  chatId: string;
  files: File[];
}

export interface IChatListService {
  getChats(params: GetChatsRequestDTO): Promise<ServiceResult<GetChatsResponseDTO>>;
  createChat(params: CreateChatParams): Promise<ServiceResult<CreateChatResponseDTO>>;
  getChatDetail(chatId: string): Promise<ServiceResult<GetChatDetailResponseDTO>>;
  getChatStatus(chatId: string): Promise<ServiceResult<ChatStatusPollResponseDTO>>;
  deleteDocument(chatId: string, documentId: string): Promise<ServiceResult<DeleteDocumentResponseDTO>>;
  uploadDocuments(params: UploadDocumentsParams): Promise<ServiceResult<CreateChatResponseDTO>>;
  sendMessage(chatId: string, request: SendMessageRequestDTO): Promise<ServiceResult<ConversationResponseDTO>>;
  pollConversation(conversationId: string): Promise<ServiceResult<ConversationPollResponseDTO>>;
  getSessionMessages(chatId: string, sessionId: string): Promise<ServiceResult<GetSessionMessagesResponseDTO>>;
  getDocumentFile(chatId: string, documentId: string, mode: 'view' | 'download'): Promise<Blob>;
}
