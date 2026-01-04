import { create } from "zustand";
import { Conversation, Message } from "@/types";
import { apiClient } from "@/api";

interface ConversationStore {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: Message[];
  loading: boolean;
  error: string | null;

  fetchConversations: () => Promise<void>;
  fetchMessages: (conversationId: string) => Promise<void>;
  createConversation: (
    agentId: string,
    title?: string
  ) => Promise<Conversation>;
  deleteConversation: (conversationId: string) => Promise<void>;
  setCurrentConversation: (conversation: Conversation | null) => void;
  addMessage: (message: Message) => void;
  clearMessages: () => void;
}

export const useConversationStore = create<ConversationStore>((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  loading: false,
  error: null,

  fetchConversations: async () => {
    set({ loading: true, error: null });
    try {
      const conversations = await apiClient.listConversations();
      set({ conversations, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  fetchMessages: async (conversationId: string) => {
    set({ loading: true, error: null });
    try {
      const messages = await apiClient.getConversationMessages(conversationId);
      set({ messages, loading: false });
    } catch (error: any) {
      set({ error: error.message, loading: false });
    }
  },

  createConversation: async (agentId: string, title?: string) => {
    set({ loading: true, error: null });
    try {
      const conversation = await apiClient.createConversation({
        agent_id: agentId,
        title,
      });
      set((state) => ({
        conversations: [conversation, ...state.conversations],
        currentConversation: conversation,
        loading: false,
      }));
      return conversation;
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  deleteConversation: async (conversationId: string) => {
    set({ loading: true, error: null });
    try {
      await apiClient.deleteConversation(conversationId);
      set((state) => ({
        conversations: state.conversations.filter(
          (c) => c.id !== conversationId
        ),
        currentConversation:
          state.currentConversation?.id === conversationId
            ? null
            : state.currentConversation,
        loading: false,
      }));
    } catch (error: any) {
      set({ error: error.message, loading: false });
      throw error;
    }
  },

  setCurrentConversation: (conversation: Conversation | null) => {
    set({ currentConversation: conversation });
    if (conversation) {
      get().fetchMessages(conversation.id);
    } else {
      set({ messages: [] });
    }
  },

  addMessage: (message: Message) => {
    set((state) => ({
      messages: [...state.messages, message],
    }));
  },

  clearMessages: () => {
    set({ messages: [] });
  },
}));
