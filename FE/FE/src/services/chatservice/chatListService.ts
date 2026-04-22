import { IChatListService, CreateChatParams, UploadDocumentsParams } from './IChatListService.ts';
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
import { apiClient, apiClientFast } from '../../helpers/apiClient/apiClient.ts';
import { adaptApiResponse, serviceFailureResponse } from '../../helpers/service/serviceHelpers.ts';

export class ChatListService implements IChatListService {
  async getChats(params: GetChatsRequestDTO): Promise<ServiceResult<GetChatsResponseDTO>> {
    try {
      const response = await apiClientFast.get<GetChatsResponseDTO>('/chats', { params });
      return adaptApiResponse(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to load chats';
      console.error('[ChatListService] getChats error:', message);
      return serviceFailureResponse<GetChatsResponseDTO>(null, message);
    }
  }

  async createChat(params: CreateChatParams): Promise<ServiceResult<CreateChatResponseDTO>> {
    try {
      const formData = new FormData();
      formData.append('company_name', params.companyName);
      formData.append('company_url', params.companyUrl);
      formData.append('analyst_type', params.analystType);
      if (params.files && params.files.length > 0) {
        params.files.forEach((file) => {
          formData.append('files', file);
        });
      }
      const response = await apiClient.post<CreateChatResponseDTO>('/chats', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return adaptApiResponse(response);
    } catch (error: unknown) {
      let message = 'Failed to create chat';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosErr = error as { response?: { data?: { message?: string; detail?: string } } };
        message = axiosErr.response?.data?.message || axiosErr.response?.data?.detail || message;
      } else if (error instanceof Error) {
        message = error.message;
      }
      console.error('[ChatListService] createChat error:', message);
      return serviceFailureResponse<CreateChatResponseDTO>(null, message);
    }
  }

  async getChatStatus(chatId: string): Promise<ServiceResult<ChatStatusPollResponseDTO>> {
    try {
      const response = await apiClient.get<ChatStatusPollResponseDTO>(`/chats/${chatId}/status`);
      return adaptApiResponse(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to get chat status';
      console.error('[ChatListService] getChatStatus error:', message);
      return serviceFailureResponse<ChatStatusPollResponseDTO>(null, message);
    }
  }

  async deleteDocument(chatId: string, documentId: string): Promise<ServiceResult<DeleteDocumentResponseDTO>> {
    try {
      const response = await apiClient.delete<DeleteDocumentResponseDTO>(
        `/chats/${chatId}/documents/${documentId}`
      );
      return adaptApiResponse(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to delete document';
      console.error('[ChatListService] deleteDocument error:', message);
      return serviceFailureResponse<DeleteDocumentResponseDTO>(null, message);
    }
  }

  async uploadDocuments(params: UploadDocumentsParams): Promise<ServiceResult<CreateChatResponseDTO>> {
    try {
      const formData = new FormData();
      formData.append('chat_id', params.chatId);
      params.files.forEach((file) => {
        formData.append('files', file);
      });
      const response = await apiClient.post<CreateChatResponseDTO>('/chats', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return adaptApiResponse(response);
    } catch (error: unknown) {
      let message = 'Failed to upload documents';
      if (error && typeof error === 'object' && 'response' in error) {
        const axiosErr = error as { response?: { data?: { message?: string; detail?: string } } };
        message = axiosErr.response?.data?.message || axiosErr.response?.data?.detail || message;
      } else if (error instanceof Error) {
        message = error.message;
      }
      console.error('[ChatListService] uploadDocuments error:', message);
      return serviceFailureResponse<CreateChatResponseDTO>(null, message);
    }
  }

  async sendMessage(chatId: string, request: SendMessageRequestDTO): Promise<ServiceResult<ConversationResponseDTO>> {
    try {
      const response = await apiClient.post<ConversationResponseDTO>(
        `/chats/${chatId}/messages`,
        request
      );
      return adaptApiResponse(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to send message';
      console.error('[ChatListService] sendMessage error:', message);
      return serviceFailureResponse<ConversationResponseDTO>(null, message);
    }
  }

  async pollConversation(conversationId: string): Promise<ServiceResult<ConversationPollResponseDTO>> {
    try {
      const response = await apiClient.get<ConversationPollResponseDTO>(
        `/conversations/${conversationId}`
      );
      return adaptApiResponse(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to poll conversation';
      console.error('[ChatListService] pollConversation error:', message);
      return serviceFailureResponse<ConversationPollResponseDTO>(null, message);
    }
  }

  async getChatDetail(chatId: string): Promise<ServiceResult<GetChatDetailResponseDTO>> {
    try {
      const response = await apiClient.get<GetChatDetailResponseDTO>(`/chats/${chatId}`);
      return adaptApiResponse(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to load chat details';
      console.error('[ChatListService] getChatDetail error:', message);
      return serviceFailureResponse<GetChatDetailResponseDTO>(null, message);
    }
  }

  async getSessionMessages(chatId: string, sessionId: string): Promise<ServiceResult<GetSessionMessagesResponseDTO>> {
    try {
      const response = await apiClient.get<GetSessionMessagesResponseDTO>(
        `/chats/${chatId}/sessions/${sessionId}/messages`
      );
      return adaptApiResponse(response);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to load session messages';
      console.error('[ChatListService] getSessionMessages error:', message);
      return serviceFailureResponse<GetSessionMessagesResponseDTO>(null, message);
    }
  }

  async getDocumentFile(chatId: string, documentId: string, mode: 'view' | 'download'): Promise<Blob> {
    const response = await apiClient.get(
      `/chats/${chatId}/documents/${documentId}/file`,
      { params: { mode }, responseType: 'blob' }
    );
    return response.data as Blob;
  }
}

export const chatListService = new ChatListService();
