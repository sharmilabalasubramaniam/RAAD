import React, { useState } from 'react';
import { Sparkles, Send, RefreshCw, AlertCircle, Bot, User, CheckCircle2 } from 'lucide-react';
import { apiService } from '../../services/api';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: string;
  isError?: boolean;
}

export const DashboardCopilotChat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome-1',
      sender: 'assistant',
      text: '👋 Hello! I am connected to the **ResourcePulse AI Agent** (`http://localhost:8001`). Ask me anything about workforce availability, overloaded engineers, or priority tasks.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [agentError, setAgentError] = useState<string | null>(null);

  const testPrompts = [
    'How many employees are available?',
    'Show overloaded engineers.',
    'Who should handle the highest priority task?',
    'Which tasks are at risk?'
  ];

  const handleSendMessage = async (promptText?: string) => {
    const textToSend = promptText || inputQuery;
    if (!textToSend.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `usr-${Date.now()}`,
      sender: 'user',
      text: textToSend,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!promptText) setInputQuery('');
    setIsLoading(true);
    setAgentError(null);

    try {
      const response = await apiService.askCopilot(textToSend);
      setMessages((prev) => [
        ...prev,
        {
          id: response.id,
          sender: 'assistant',
          text: response.text,
          timestamp: response.timestamp
        }
      ]);
    } catch (err: any) {
      console.error('Copilot Chat Error:', err);
      const errorMsg = err?.message || 'Failed to communicate with AI Agent at http://localhost:8001';
      setAgentError(errorMsg);
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: 'assistant',
          text: `⚠️ **Agent Communication Error**: ${errorMsg}`,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          isError: true
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200/90 rounded-2xl shadow-xs overflow-hidden flex flex-col h-[480px]">
      
      {/* Card Header */}
      <div className="bg-slate-900 text-white p-4 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="p-1.5 bg-amber-500/20 text-amber-400 rounded-lg border border-amber-500/30">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold font-serif tracking-tight flex items-center gap-2">
              RAAD AI Copilot
              <span className="text-[9px] font-mono font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30 px-1.5 py-0.2 rounded">
                LIVE AGENT
              </span>
            </h2>
            <p className="text-[10px] text-slate-400 font-mono">
              Connected to agent:8001 → backend:8000
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {agentError ? (
            <span className="text-[10px] font-mono font-bold bg-rose-500/20 text-rose-300 border border-rose-500/30 px-2 py-0.5 rounded flex items-center gap-1">
              <AlertCircle className="w-3 h-3" /> Agent Offline
            </span>
          ) : (
            <span className="text-[10px] font-mono font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 px-2 py-0.5 rounded flex items-center gap-1">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" /> Active
            </span>
          )}
        </div>
      </div>

      {/* Suggested Quick Prompts */}
      <div className="bg-slate-50 border-b border-slate-200/80 px-3 py-2 flex items-center gap-1.5 overflow-x-auto text-[11px]">
        <span className="text-[10px] font-mono uppercase font-bold text-slate-400 shrink-0 mr-1">TEST PROMPTS:</span>
        {testPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSendMessage(prompt)}
            disabled={isLoading}
            className="bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 px-2.5 py-1 rounded-md shrink-0 font-medium transition cursor-pointer disabled:opacity-50 text-[11px]"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Message List Window */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50/40">
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`flex items-start gap-2.5 max-w-[88%] ${
              msg.sender === 'user' ? 'ml-auto flex-row-reverse' : 'mr-auto'
            }`}
          >
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5 ${
                msg.sender === 'user'
                  ? 'bg-slate-800 text-white'
                  : msg.isError
                  ? 'bg-rose-100 text-rose-700 border border-rose-300'
                  : 'bg-amber-100 text-amber-900 border border-amber-300'
              }`}
            >
              {msg.sender === 'user' ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
            </div>

            <div
              className={`p-3 rounded-xl text-xs leading-relaxed ${
                msg.sender === 'user'
                  ? 'bg-slate-900 text-white rounded-tr-xs shadow-2xs font-medium'
                  : msg.isError
                  ? 'bg-rose-50 border border-rose-200 text-rose-900 rounded-tl-xs'
                  : 'bg-white border border-slate-200/90 text-slate-800 rounded-tl-xs shadow-2xs whitespace-pre-wrap'
              }`}
            >
              <div>{msg.text}</div>
              <span className={`block text-[9px] font-mono mt-1 ${msg.sender === 'user' ? 'text-slate-400 text-right' : 'text-slate-400'}`}>
                {msg.timestamp}
              </span>
            </div>
          </div>
        ))}

        {isLoading && (
          <div className="flex items-center gap-2 text-xs text-slate-500 font-mono bg-white border border-slate-200 p-2.5 rounded-xl max-w-xs shadow-2xs">
            <RefreshCw className="w-3.5 h-3.5 animate-spin text-amber-600" />
            <span>AI Agent reasoning across backend telemetry...</span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="p-3 bg-white border-t border-slate-200">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          <input
            type="text"
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            disabled={isLoading}
            placeholder="Ask RAAD AI... (e.g. 'Show overloaded engineers.')"
            className="flex-1 bg-slate-100 border border-slate-200 rounded-lg px-3 py-2 text-xs text-slate-900 placeholder-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-slate-900 transition disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !inputQuery.trim()}
            className="bg-slate-900 hover:bg-slate-800 text-white p-2 rounded-lg transition shadow-2xs disabled:opacity-50 cursor-pointer shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

    </div>
  );
};
