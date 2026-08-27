import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { ProfileResponse, MessageResponse, ToolCallInfo } from '../types';

interface AuthState {
  token: string | null;
  userId: string | null;
  email: string | null;
  setAuth: (token: string, userId: string, email: string) => void;
  clearAuth: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      email: null,
      setAuth: (token, userId, email) => set({ token, userId, email }),
      clearAuth: () => set({ token: null, userId: null, email: null }),
    }),
    { name: 'auth-storage' }
  )
);

// ── Chat state ────────────────────────────────────────────────────────────────

export interface ChatMessage extends MessageResponse {
  toolCalls?: ToolCallInfo[];
  coverageResult?: unknown;
  citations?: Array<{ document: string; page: number | null; excerpt: string }>;
  products?: unknown[];
}

interface ChatState {
  sessionId: string | null;
  messages: ChatMessage[];
  profile: ProfileResponse | null;
  isLoading: boolean;
  setSession: (id: string) => void;
  addMessage: (msg: ChatMessage) => void;
  setMessages: (msgs: ChatMessage[]) => void;
  setProfile: (profile: ProfileResponse | null) => void;
  setLoading: (v: boolean) => void;
  reset: () => void;
}

export const useChatStore = create<ChatState>((set) => ({
  sessionId: null,
  messages: [],
  profile: null,
  isLoading: false,
  setSession: (id) => set({ sessionId: id }),
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setMessages: (msgs) => set({ messages: msgs }),
  setProfile: (profile) => set({ profile }),
  setLoading: (v) => set({ isLoading: v }),
  reset: () => set({ sessionId: null, messages: [], profile: null }),
}));
