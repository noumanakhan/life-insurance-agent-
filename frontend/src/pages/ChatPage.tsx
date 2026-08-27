import { useEffect, useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Shield, Send, Plus, LogOut, Loader2, Bot, User as UserIcon, Download } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import api from '../lib/api';
import { useAuthStore, useChatStore } from '../store';
import type { ChatMessage } from '../store';
import ProfileSummaryCard from '../components/ProfileSummaryCard';
import CoverageResultCard from '../components/CoverageResultCard';
import PolicyCitation from '../components/PolicyCitation';
import ProductRecommendationList from '../components/ProductRecommendationList';
import type { ChatResponse, MessageResponse, ProfileResponse, CoverageResult, Product } from '../types';

// ── Typing indicator ──────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex items-end gap-3 fade-in">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
        <Bot size={14} className="text-white" />
      </div>
      <div className="bubble-assistant px-4 py-3">
        <div className="flex gap-1.5">
          <div className="typing-dot" />
          <div className="typing-dot" />
          <div className="typing-dot" />
        </div>
      </div>
    </div>
  );
}

// ── Single message bubble ─────────────────────────────────────────────────────
function MessageBubble({ msg }: { msg: ChatMessage }) {
  const isUser = msg.role === 'user';

  // Extract structured data from tool_calls_json
  let coverageResult: CoverageResult | null = null;
  let citations: Array<{ document: string; page: number | null; excerpt: string }> = [];
  let products: Product[] = [];

  if (msg.tool_calls_json) {
    try {
      const calls = JSON.parse(msg.tool_calls_json) as Array<{ name: string; result: unknown }>;
      for (const c of calls) {
        if (c.name === 'calculate_coverage' && c.result) {
          coverageResult = c.result as CoverageResult;
        }
        if (c.name === 'search_policy_documents' && (c.result as { citations?: unknown })?.citations) {
          citations = (c.result as { citations: Array<{ document: string; page: number | null; excerpt: string }> }).citations;
        }
        if (c.name === 'recommend_products' && (c.result as { products?: unknown })?.products) {
          products = (c.result as { products: Product[] }).products;
        }
      }
    } catch {
      /* ignore parse errors */
    }
  }

  if (isUser) {
    return (
      <div className="flex justify-end fade-in">
        <div className="bubble-user px-4 py-3 max-w-[75%]">
          <p className="text-sm text-white leading-relaxed">{msg.content}</p>
        </div>
        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-600 to-slate-700 flex items-center justify-center flex-shrink-0 ml-3 mt-auto">
          <UserIcon size={14} className="text-white" />
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-end gap-3 fade-in">
      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
        <Bot size={14} className="text-white" />
      </div>
      <div className="max-w-[80%] flex flex-col gap-2">
        <div className="bubble-assistant px-4 py-3">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
          {citations.length > 0 && <PolicyCitation citations={citations} />}
        </div>
        {coverageResult && (
          <CoverageResultCard
            result={{
              ...coverageResult,
              currency: 'USD',
              disclaimer: 'Educational guidance only. Verify with a qualified professional.',
            }}
          />
        )}
        {products.length > 0 && <ProductRecommendationList products={products} />}
      </div>
    </div>
  );
}

// ── Main ChatPage ─────────────────────────────────────────────────────────────
export default function ChatPage() {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const qc = useQueryClient();

  const { email, clearAuth } = useAuthStore();
  const { sessionId, messages, profile, isLoading, setSession, setMessages, setProfile, setLoading, addMessage } =
    useChatStore();

  // Create a new session
  const createSession = useMutation({
    mutationFn: () => api.post('/sessions', { title: 'New Conversation' }).then((r) => r.data),
    onSuccess: (session) => {
      setSession(session.id);
      setMessages([]);
    },
  });

  // Load messages for current session
  const { data: serverMessages } = useQuery({
    queryKey: ['messages', sessionId],
    queryFn: () => api.get<MessageResponse[]>(`/sessions/${sessionId}/messages`).then((r) => r.data),
    enabled: !!sessionId,
  });

  useEffect(() => {
    if (serverMessages) {
      setMessages(serverMessages as ChatMessage[]);
    }
  }, [serverMessages, setMessages]);

  // Load profile for current session
  const { data: serverProfile } = useQuery({
    queryKey: ['profile', sessionId],
    queryFn: () => api.get<ProfileResponse>(`/sessions/${sessionId}/profile`).then((r) => r.data),
    enabled: !!sessionId,
  });

  useEffect(() => {
    if (serverProfile) {
      setProfile(serverProfile);
    }
  }, [serverProfile, setProfile]);

  // Send a message
  const sendMessage = useMutation({
    mutationFn: (message: string) =>
      api.post<ChatResponse>('/chat', { session_id: sessionId, message }).then((r) => r.data),
    onMutate: (message) => {
      addMessage({
        id: crypto.randomUUID(),
        session_id: sessionId!,
        role: 'user',
        content: message,
        tool_calls_json: null,
        created_at: new Date().toISOString(),
      });
      setLoading(true);
    },
    onSuccess: (data) => {
      addMessage({
        id: crypto.randomUUID(),
        session_id: sessionId!,
        role: 'assistant',
        content: data.reply,
        tool_calls_json: data.tool_calls.length > 0 ? JSON.stringify(data.tool_calls) : null,
        created_at: new Date().toISOString(),
      });
      if (data.profile_updated) {
        qc.invalidateQueries({ queryKey: ['profile', sessionId] });
      }
    },
    onError: () => {
      addMessage({
        id: crypto.randomUUID(),
        session_id: sessionId!,
        role: 'assistant',
        content: "I'm having trouble connecting. Please try again in a moment.",
        tool_calls_json: null,
        created_at: new Date().toISOString(),
      });
    },
    onSettled: () => setLoading(false),
  });

  const handleSend = () => {
    const text = input.trim();
    if (!text || !sessionId || isLoading) return;
    setInput('');
    sendMessage.mutate(text);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleNewChat = () => {
    createSession.mutate();
  };

  const handleLogout = () => {
    clearAuth();
    localStorage.removeItem('token');
    navigate('/login');
  };

  const handleDownloadSummary = () => {
    if (messages.length === 0) return;
    const summaryText = `Life Insurance AI Advisor - Consultation Summary\nSession ID: ${sessionId}\nDate: ${new Date().toLocaleString()}\nEmail: ${email || 'N/A'}\n\nClient Profile:\n${JSON.stringify(profile, null, 2)}\n\nConversation Transcript:\n${messages
      .map((m) => `[${m.role.toUpperCase()}] ${m.content}`)
      .join('\n\n')}\n\nDisclaimer: This is educational guidance only, not licensed financial advice.`;

    const blob = new Blob([summaryText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `life_insurance_summary_${new Date().toISOString().slice(0, 10)}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  // Create session on mount if none
  useEffect(() => {
    if (!sessionId) createSession.mutate();
  }, []);

  return (
    <div className="animated-bg h-screen flex flex-col overflow-hidden">
      {/* ── Navbar ── */}
      <header
        className="glass border-b border-[var(--c-border)] px-6 py-3 flex items-center justify-between flex-shrink-0"
        style={{ borderRadius: 0 }}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
            <Shield size={16} className="text-white" />
          </div>
          <div>
            <h1 className="font-bold text-sm gradient-text">Life Insurance AI</h1>
            <p className="text-xs" style={{ color: 'var(--c-text-muted)' }}>
              Coverage Advisor
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs hidden sm:block" style={{ color: 'var(--c-text-muted)' }}>
            {email}
          </span>
          <button
            id="admin-nav-btn"
            onClick={() => navigate('/admin')}
            title="Admin policy ingestion"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer"
            style={{ background: 'var(--c-surface-2)', border: '1px solid var(--c-border)' }}
          >
            <Shield size={13} /> Admin
          </button>
          <button
            id="download-summary-btn"
            onClick={handleDownloadSummary}
            title="Download consultation summary"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors cursor-pointer"
            style={{ background: 'var(--c-surface-2)', border: '1px solid var(--c-border)' }}
          >
            <Download size={13} /> Export
          </button>
          <button
            id="new-chat-btn"
            onClick={handleNewChat}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
            style={{ background: 'var(--c-surface-2)', border: '1px solid var(--c-border)' }}
          >
            <Plus size={13} /> New Chat
          </button>
          <button
            id="logout-btn"
            onClick={handleLogout}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-red-400 transition-colors hover:bg-red-500/10"
            style={{ border: '1px solid rgba(239,68,68,0.2)' }}
          >
            <LogOut size={13} /> Logout
          </button>
        </div>
      </header>

      {/* ── Body ── */}
      <div className="flex flex-1 overflow-hidden">
        {/* ── Left sidebar — Profile ── */}
        <aside
          className="w-64 flex-shrink-0 p-4 overflow-y-auto hidden lg:block"
          style={{ borderRight: '1px solid var(--c-border)' }}
        >
          <ProfileSummaryCard profile={profile} />
        </aside>

        {/* ── Main chat area ── */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6 flex flex-col gap-5">
            {messages.length === 0 && !isLoading && (
              <div className="flex flex-col items-center justify-center flex-1 gap-4 fade-in">
                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                  <Shield size={32} className="text-white" />
                </div>
                <div className="text-center">
                  <h2 className="text-xl font-bold gradient-text mb-2">Welcome to Life Insurance AI</h2>
                  <p className="text-sm max-w-sm" style={{ color: 'var(--c-text-muted)' }}>
                    Tell me about yourself — your income, family, and financial situation — and I'll calculate your
                    recommended life insurance coverage.
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-w-lg w-full mt-2">
                  {[
                    'What life insurance coverage do I need?',
                    'I earn $80,000 a year with 2 kids',
                    "What's the difference between term and whole life?",
                    'I have a $200,000 mortgage and no existing coverage',
                  ].map((prompt) => (
                    <button
                      key={prompt}
                      onClick={() => {
                        setInput(prompt);
                      }}
                      className="text-left p-3 rounded-xl text-xs transition-all cursor-pointer"
                      style={{ background: 'var(--c-surface-2)', border: '1px solid var(--c-border)' }}
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {messages.map((msg) => (
              <MessageBubble key={msg.id} msg={msg} />
            ))}
            {isLoading && <TypingIndicator />}
            <div ref={messagesEndRef} />
          </div>

          {/* ── Input area ── */}
          <div className="px-4 pb-4 flex-shrink-0" style={{ borderTop: '1px solid var(--c-border)' }}>
            <div className="max-w-3xl mx-auto pt-4">
              <div className="flex gap-3 items-end">
                <textarea
                  id="chat-input"
                  rows={1}
                  value={input}
                  onChange={(e) => {
                    setInput(e.target.value);
                    e.target.style.height = 'auto';
                    e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px';
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder="Tell me about your financial situation…"
                  className="chat-input flex-1 px-4 py-3 text-sm"
                  disabled={isLoading || !sessionId}
                  style={{ minHeight: '48px', maxHeight: '120px' }}
                />
                <button
                  id="send-btn"
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading || !sessionId}
                  className="btn-primary w-12 h-12 flex items-center justify-center flex-shrink-0"
                >
                  {isLoading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                </button>
              </div>
              <p className="text-center text-xs mt-2" style={{ color: 'var(--c-text-muted)' }}>
                Educational guidance only — not licensed financial advice.
              </p>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
