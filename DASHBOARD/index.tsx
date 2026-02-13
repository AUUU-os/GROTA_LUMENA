import React, { useState, useEffect, useRef, useMemo } from "react";
import { createRoot } from "react-dom/client";
import { GoogleGenAI, LiveServerMessage, Modality, Type } from "@google/genai";
import ReactMarkdown from "react-markdown";
import JSZip from "jszip";
import {
  MessageSquare,
  Image as ImageIcon,
  Video,
  Mic,
  Send,
  Loader2,
  AlertCircle,
  Play,
  Square,
  CheckSquare,
  Trash2,
  Plus,
  Wand2,
  CheckCircle2,
  Circle,
  Filter,
  SortAsc,
  FolderTree,
  File as FileIcon,
  ChevronRight,
  ChevronLeft,
  ChevronDown,
  Github,
  Search,
  Zap,
  X,
  Database,
  GitBranch,
  Box,
  Upload,
  Cpu,
  Globe,
  Share2,
  Download,
  Terminal,
  Command,
  Maximize2,
  MoreHorizontal,
  Sparkles,
  Layers,
  LayoutGrid,
  Settings2,
  RefreshCw,
  Copy,
  List,
  Clock,
  Film,
  Tag,
  AlertTriangle,
  Info,
  Brain,
  Volume2,
  Camera,
  Scissors,
  Flag,
  CornerDownRight,
  Hash,
  ArrowRight,
  CalendarDays,
  FileJson,
  FileUp,
  Eraser,
  Link as LinkIcon,
  Lock,
  Unlock,
  Lightbulb,
  Calendar as CalendarIcon,
  CornerDownLeft,  
  Mountain,  
  Shield,  
  Code
} from "lucide-react";

// --- Types ---

type ViewMode = "chat" | "image" | "video" | "live" | "tasks" | "repo" | "models" | "grota" | "evolution" | "docs_chat" | "memory" | "analytics" | "tools" | "social";

interface ChatMessage { 
  id: string;
  role: "user" | "model"; 
  text: string; 
  timestamp: number;
  thinking?: string;
  isAudio?: boolean;
}

type RecurringType = 'none' | 'daily' | 'weekly' | 'monthly';

interface Task {
  id: string;
  text: string;
  status: 'todo' | 'in-progress' | 'done';
  priority: 'low' | 'medium' | 'high';
  tags?: string[];
  subtasks?: Task[];
  isExpanded?: boolean;
  suggestions?: string;
  loadingSuggestions?: boolean;
  recurring?: RecurringType;
  dependencies?: string[]; // IDs of tasks that must be done
  dueDate?: string; // YYYY-MM-DD
}

interface RepoNode {
  name: string;
  type: 'file' | 'folder';
  children?: RepoNode[];
  content?: string;
}

interface LogEntry {
  id: string;
  timestamp: number;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
  
  Code?: string | number;
  source: string;
}

// --- Utils ---

const deCode = (base64: string) => {
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
  return bytes;
};

const enCode = (bytes: Uint8Array) => {
  let binary = '';
  for (let i = 0; i < bytes.byteLength; i++) binary += String.fromCharCode(bytes[i]);
  return btoa(binary);
};

const blobToBase64 = (blob: Blob): Promise<string> => {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result?.toString().split(',')[1] || "");
    reader.readAsDataURL(blob);
  });
};

const getRelativeTime = (dateStr: string) => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    const today = new Date();
    // Reset hours to compare dates only
    today.setHours(0,0,0,0);
    // Fix timezone offset issue by treating the date string as local YYYY-MM-DD
    const [y, m, d] = dateStr.split('-').map(Number);
    const targetDate = new Date(y, m - 1, d);
    
    const diffTime = targetDate.getTime() - today.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
    
    if (diffDays === 0) return "Today";
    if (diffDays === 1) return "Tomorrow";
    if (diffDays === -1) return "Yesterday";
    if (diffDays > 0 && diffDays < 7) return `In ${diffDays} days`;
    if (diffDays < 0) return `${Math.abs(diffDays)} days ago`;
    return dateStr;
};

// --- UI Components ---

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children?: React.ReactNode;
  footer?: React.ReactNode;
}

const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children, footer }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="glass w-full max-w-md rounded-[32px] overflow-hidden shadow-2xl border border-white/10 flex flex-col">
        <div className="p-6 border-b border-white/5 flex items-center justify-between bg-zinc-900/40">
          <h3 className="font-bold text-lg text-white">{title}</h3>
          <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full text-zinc-500 transition-colors"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-8 text-zinc-300 text-sm leading-relaxed">{children}</div>
        <div className="p-6 bg-zinc-900/20 flex items-center justify-end gap-3">{footer}</div>
      </div>
    </div>
  );
};

// 0. Terminal Log Component
const TerminalLog = ({ logs, isOpen, onClose, onClear }: { logs: LogEntry[], isOpen: boolean, onClose: () => void, onClear: () => void }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed bottom-0 left-0 right-0 h-64 glass border-t border-white/10 z-50 flex flex-col shadow-2xl animate-fade-in backdrop-blur-xl bg-black/90">
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/5 bg-zinc-900/50">
         <div className="flex items-center gap-2">
            <Terminal className="w-4 h-4 text-zinc-400" />
            <span className="text-xs font-bold text-zinc-300 uppercase tracking-wider">System Terminal</span>
            <span className="text-[10px] bg-zinc-800 text-zinc-500 px-1.5 py-0.5 rounded-md font-mono">{logs.length} events</span>
         </div>
         <div className="flex items-center gap-2">
            <button onClick={onClear} className="p-1 hover:bg-white/10 rounded-md text-zinc-500 hover:text-white transition-colors" title="Clear Logs">
              <Trash2 className="w-3.5 h-3.5" />
            </button>
            <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-md text-zinc-500 hover:text-white transition-colors" title="Close Terminal">
              <ChevronDown className="w-3.5 h-3.5" />
            </button>
         </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-1.5 custom-scrollbar">
         {logs.length === 0 && <div className="text-zinc-600 italic pl-2">System online. Ready for logs...</div>}
         {logs.map(log => (
            <div key={log.id} className="flex gap-3 text-zinc-300 hover:bg-white/5 p-1.5 rounded transition-colors border-l-2 border-transparent hover:border-zinc-700">
               <span className="text-zinc-600 flex-shrink-0">[{new Date(log.timestamp).toLocaleTimeString([], {hour12: false, hour:'2-digit', minute:'2-digit', second:'2-digit'})}]</span>
               <span className={`font-bold uppercase text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 self-start ${
                  log.type === 'error' ? 'bg-red-500/10 text-red-400 border border-red-500/20' :
                  log.type === 'warning' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' :
                  log.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                  'bg-blue-500/10 text-blue-400 border border-blue-500/20'
               }`}>{log.type}</span>
               <span className="flex-shrink-0 text-zinc-500 font-bold min-w-[80px]">[{log.source}]</span>
               <span className={`${log.type === 'error' ? 'text-red-300' : 'text-zinc-300'} break-all flex-1`}>
                 {log.message}
                 {log.Code && <span className="ml-2 opacity-60 bg-white/5 px-1 rounded text-[10px]">ERR_{log.Code}</span>}
               </span>
            </div>
         ))}
      </div>
    </div>
  );
};

// 1. Enhanced Chat View
const ChatView = ({ addLog }: { addLog: (log: Omit<LogEntry, 'id' | 'timestamp'>) => void }) => {
  const [input, setInput] = useState("");
  const [useThinking, setUseThinking] = useState(false);
  const [sessionId] = useState(() => {
    const key = "studio_chat_session_id";
    const existing = localStorage.getItem(key);
    if (existing) return existing;
    const fresh = `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
    localStorage.setItem(key, fresh);
    return fresh;
  });
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem("studio_chat_history");
      if (saved) return JSON.parse(saved);
    } catch (e) { console.error("Failed to load chat history", e); }
    return [{ id: '1', role: 'model', text: "Systems online. Connected to Gemini 3 Pro. How can I assist with your engineering tasks today?", timestamp: Date.now() }];
  });
  
  const [isTyping, setIsTyping] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    localStorage.setItem("studio_chat_history", JSON.stringify(messages));
  }, [messages]);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, isTyping]);

  const speakText = async (text: string) => {
    try {
      addLog({ message: "Generating speech...", type: 'info', source: 'TTS' });
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const response = await ai.models.generateContent({
        model: "gemini-2.5-flash-preview-tts",
        contents: [{ parts: [{ text: `Say clearly: ${text.slice(0, 200)}` }] }],
        config: {
          responseModalities: [Modality.AUDIO],
          speechConfig: { voiceConfig: { prebuiltVoiceConfig: { voiceName: 'Kore' } } }
        }
      });
      const base64Audio = response.candidates?.[0]?.content?.parts?.[0]?.inlineData?.data;
      if (base64Audio) {
        const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
        const data = deCode(base64Audio);
        const dataInt16 = new Int16Array(data.buffer);
        const buffer = audioCtx.createBuffer(1, dataInt16.length, 24000);
        const channelData = buffer.getChannelData(0);
        for (let i = 0; i < dataInt16.length; i++) channelData[i] = dataInt16[i] / 32768.0;
        const source = audioCtx.createBufferSource();
        source.buffer = buffer;
        source.connect(audioCtx.destination);
        source.start();
        addLog({ message: "Playing audio response.", type: 'success', source: 'TTS' });
      }
    } catch (e: any) {
      addLog({ message: `TTS failed: ${e.message}`, type: 'error', source: 'TTS' });
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsTyping(true);
    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', text: `Uploaded ${file.name}`, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);

    try {
      const base64Data = await blobToBase64(file);
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const response = await ai.models.generateContent({
        model: "gemini-3-pro-preview",
        contents: {
          parts: [
            { inlineData: { data: base64Data, mimeType: file.type } },
            { text: "Analyze this file and describe its contents in detail." }
          ]
        }
      });
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'model', text: response.text || "Analysis complete.", timestamp: Date.now() }]);
    } catch (e: any) {
      addLog({ message: `Analysis failed: ${e.message}`, type: 'error', source: 'Vision' });
    } finally {
      setIsTyping(false);
    }
  };

  const startTranscription = async () => {
    setIsTranscribing(true);
    addLog({ message: "Listening for audio transcription...", type: 'info', source: 'Audio' });
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      const chunks: Blob[] = [];
      mediaRecorder.ondataavailable = (e) => chunks.push(e.data);
      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/webm' });
        const base64 = await blobToBase64(audioBlob);
        const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
        const response = await ai.models.generateContent({
          model: "gemini-3-flash-preview",
          contents: { parts: [{ inlineData: { data: base64, mimeType: 'audio/webm' } }, { text: "Transcribe this audio exactly." }] }
        });
        if (response.text) setInput(response.text);
        setIsTranscribing(false);
        addLog({ message: "Audio transcribed successfully.", type: 'success', source: 'Audio' });
      };
      mediaRecorder.start();
      setTimeout(() => mediaRecorder.stop(), 4000);
    } catch (e: any) {
      setIsTranscribing(false);
      addLog({ message: `Transcription failed: ${e.message}`, type: 'error', source: 'Audio' });
    }
  };

  const storeConversation = async (content: string, role: "user" | "model") => {
    try {
      await fetch("http://localhost:8000/api/v1/memory/store", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          memory_type: "conversation",
          importance: 5,
          metadata: { role, source: "dashboard_chat", tags: ["chat", "dashboard"] },
          agent_id: "dashboard",
          session_id: sessionId
        }),
      });
    } catch {
      // silent fail to avoid breaking chat flow
    }
  };

  const sendMessage = async () => {
    if (!input.trim()) return;
    const userMsg: ChatMessage = { id: Date.now().toString(), role: 'user', text: input, timestamp: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);
    await storeConversation(userMsg.text, "user");

    try {
      addLog({ message: `Sending to Gemini 3 Pro (Thinking: ${useThinking})...`, type: 'info', source: 'ChatView' });
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const config: any = {};
      if (useThinking) {
        config.thinkingConfig = { thinkingBudget: 32768 };
      }

      const response = await ai.models.generateContent({
        model: "gemini-3-pro-preview",
        contents: input,
        config
      });

      const text = response.text || "No response generated.";
      setMessages(prev => [...prev, { id: Date.now().toString(), role: 'model', text, timestamp: Date.now() }]);
      await storeConversation(text, "model");
      addLog({ message: "Success.", type: 'success', source: 'ChatView' });
    } catch (e: any) {
      addLog({ message: `Failed: ${e.message}`, type: 'error', Code: e.status, source: 'ChatView' });
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-full gap-4 animate-fade-in relative">
      <div className="flex-1 overflow-y-auto custom-scrollbar pr-4 space-y-6" ref={scrollRef}>
        {messages.map((msg) => (
          <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
            <div className={`w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center border ${msg.role === 'model' ? 'bg-indigo-600/20 border-indigo-500/30 text-indigo-400' : 'bg-zinc-800 border-zinc-700 text-zinc-400'}`}>
              {msg.role === 'model' ? <Sparkles className="w-4 h-4" /> : <div className="font-bold text-xs">YOU</div>}
            </div>
            <div className={`flex flex-col max-w-[80%] ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`px-5 py-3.5 rounded-2xl text-sm leading-relaxed shadow-sm ${
                msg.role === 'user' ? 'bg-zinc-100 text-black font-medium whitespace-pre-wrap' : 'glass border border-white/5 text-zinc-300'
              }`}>
                {msg.role === 'model' ? (
                  <div className="markdown-body">
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                ) : (
                  msg.text
                )}
                {msg.role === 'model' && (
                  <button onClick={() => speakText(msg.text)} className="mt-3 inline-flex items-center text-zinc-500 hover:text-white transition-colors border border-white/5 bg-white/5 px-2 py-1 rounded-md text-[10px] uppercase font-bold tracking-wider">
                    <Volume2 className="w-3 h-3 mr-1" /> Speak Response
                  </button>
                )}
              </div>
              <span className="text-[10px] text-zinc-600 mt-1.5 px-1 font-mono opacity-50">
                {new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
              </span>
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex gap-4">
             <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
               <Sparkles className="w-4 h-4 animate-pulse" />
             </div>
             <div className="glass px-4 py-3 rounded-2xl flex items-center gap-2">
               <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
               <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
               <div className="w-1.5 h-1.5 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
             </div>
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <div className="flex items-center gap-2 px-2">
           <button 
            onClick={() => setUseThinking(!useThinking)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider transition-all border ${
              useThinking ? 'bg-indigo-500/20 border-indigo-500 text-indigo-400 shadow-[0_0_10px_rgba(99,102,241,0.2)]' : 'bg-zinc-900 border-zinc-800 text-zinc-500'
            }`}
           >
             <Brain className="w-3 h-3" />
             Deep Thinking
           </button>
        </div>
        <div className="glass p-2 rounded-[24px] flex items-end gap-2 border border-white/10 shadow-2xl shadow-black/50">
           <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept="image/*,video/*" />
           <button onClick={() => fileInputRef.current?.click()} className="p-3 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded-full transition-colors">
              <Camera className="w-5 h-5" />
           </button>
           <textarea 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => { if(e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
              placeholder="Transmit to OMEGA Core..."
              className="flex-1 bg-transparent border-0 outline-none text-sm p-3 max-h-32 min-h-[48px] resize-none text-white placeholder:text-zinc-600 custom-scrollbar"
              rows={1}
           />
           <div className="flex items-center gap-1 pb-1 pr-1">
               <button onClick={startTranscription} className={`p-2 rounded-full transition-colors ${isTranscribing ? 'text-red-400 bg-red-400/10 animate-pulse' : 'text-zinc-500 hover:text-white hover:bg-zinc-800'}`}>
                  <Mic className="w-5 h-5" />
               </button>
               <button 
                  onClick={sendMessage}
                  disabled={!input.trim() || isTyping}
                  className="w-10 h-10 bg-white text-black rounded-full flex items-center justify-center hover:bg-zinc-200 transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-white/10"
               >
                  <Send className="w-4 h-4 ml-0.5" />
               </button>
           </div>
        </div>
      </div>
    </div>
  );
}

// 2. Enhanced Visual Lab
const VisualLab = ({ addLog }: { addLog: (log: Omit<LogEntry, 'id' | 'timestamp'>) => void }) => {
  const [prompt, setPrompt] = useState("");
  const [generating, setGenerating] = useState(false);
  const [aspectRatio, setAspectRatio] = useState("1:1");
  const [mode, setMode] = useState<'image' | 'video'>('image');
  const [gallery, setGallery] = useState<{type: 'image' | 'video', url: string, prompt: string, ratio: string}[]>([
    { type: 'image', url: "https://images.unsplash.com/photo-1620641788427-b11e699ad43e?q=80&w=1000&auto=format&fit=crop", prompt: "Cyberpunk city street, neon lights, rain", ratio: "16:9" },
    { type: 'image', url: "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?q=80&w=1000&auto=format&fit=crop", prompt: "Abstract 3D glass shapes, iridescent", ratio: "1:1" },
  ]);

  const ratios = ["1:1", "2:3", "3:2", "3:4", "4:3", "9:16", "16:9", "21:9"];

  const handleGenerate = async () => {
    if (!prompt.trim()) return;

    if (typeof window !== 'undefined' && (window as any).aistudio) {
        const hasKey = await (window as any).aistudio.hasSelectedApiKey();
        if (!hasKey) {
            await (window as any).aistudio.openSelectKey();
        }
    }

    setGenerating(true);

    try {
        if (mode === 'video') {
            const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
            const ratio = (aspectRatio === '1:1' || !['16:9', '9:16'].includes(aspectRatio)) ? '16:9' : aspectRatio;
            let operation = await ai.models.generateVideos({
                model: 'veo-3.1-fast-generate-preview',
                prompt,
                config: { numberOfVideos: 1, resolution: '720p', aspectRatio: ratio as any }
            });
            while (!operation.done) {
                await new Promise(r => setTimeout(r, 10000));
                operation = await ai.operations.getVideosOperation({operation});
            }
            const videoUri = operation.response?.generatedVideos?.[0]?.video?.uri;
            if (videoUri) {
                setGallery(prev => [{ type: 'video', url: `${videoUri}&key=${process.env.API_KEY}`, prompt, ratio }, ...prev]);
            }
        } else {
            const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
            const validRatios = ["1:1", "3:4", "4:3", "9:16", "16:9"];
            const selectedRatio = validRatios.includes(aspectRatio) ? aspectRatio : "1:1";

            const response = await ai.models.generateContent({
                model: 'gemini-3-pro-image-preview',
                contents: { parts: [{ text: prompt }] },
                config: { imageConfig: { aspectRatio: selectedRatio as any, imageSize: "1K" } }
            });
            for (const part of response.candidates?.[0]?.content?.parts || []) {
                if (part.inlineData) {
                    setGallery(prev => [{ type: 'image', url: `data:${part.inlineData.mimeType};base64,${part.inlineData.data}`, prompt, ratio: selectedRatio }, ...prev]);
                    break;
                }
            }
        }
        addLog({ message: "Content generated successfully.", type: 'success', source: 'VisualLab' });
    } catch (e: any) {
        addLog({ message: `Generation failed: ${e.message}`, type: 'error', source: 'VisualLab' });
        if (e.message?.includes("Requested entity was not found")) {
            if (typeof window !== 'undefined' && (window as any).aistudio) {
                await (window as any).aistudio.openSelectKey();
            }
        }
    } finally {
        setGenerating(false);
    }
  };

  return (
    <div className="flex h-full gap-6 animate-fade-in">
       <div className="w-72 glass rounded-3xl p-5 flex flex-col gap-6 h-full">
          <div>
            <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3 block">Mode</label>
            <div className="grid grid-cols-2 gap-2 bg-zinc-900/50 p-1 rounded-xl border border-zinc-800">
                <button onClick={() => setMode('image')} className={`flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all ${mode === 'image' ? 'bg-zinc-700 text-white shadow' : 'text-zinc-500 hover:text-zinc-300'}`}>
                    <ImageIcon className="w-3.5 h-3.5" /> Image
                </button>
                <button onClick={() => setMode('video')} className={`flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-bold transition-all ${mode === 'video' ? 'bg-zinc-700 text-white shadow' : 'text-zinc-500 hover:text-zinc-300'}`}>
                    <Film className="w-3.5 h-3.5" /> Video
                </button>
            </div>
          </div>
          <div>
            <label className="text-xs font-bold text-zinc-500 uppercase tracking-wider mb-3 block">Aspect Ratio</label>
            <div className="grid grid-cols-2 gap-2">
              {ratios.map(r => (
                <button 
                  key={r} 
                  onClick={() => setAspectRatio(r)}
                  disabled={mode === 'video' && !['16:9', '9:16'].includes(r)}
                  className={`py-2 rounded-lg text-xs font-bold border transition-all ${aspectRatio === r ? 'bg-zinc-100 text-black border-zinc-100' : 'border-zinc-800 text-zinc-500 hover:border-zinc-600 disabled:opacity-30'}`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
          <div className="mt-auto p-4 bg-zinc-900/50 rounded-2xl border border-zinc-800">
             <div className="flex items-center gap-2 mb-2">
               <Zap className="w-4 h-4 text-yellow-400" />
               <span className="text-xs font-bold text-zinc-300">Fast AI Mode</span>
             </div>
             <p className="text-[10px] text-zinc-500 leading-normal">Using Gemini 3 Pro Image & Veo 3.1 Fast.</p>
          </div>
       </div>
       <div className="flex-1 flex flex-col gap-6">
          <div className="glass p-2 pl-4 rounded-[24px] flex items-center gap-4 border border-white/10">
             <Wand2 className="w-5 h-5 text-indigo-400" />
             <input className="flex-1 bg-transparent border-none outline-none text-sm text-white placeholder:text-zinc-600" placeholder="Describe the scene..." value={prompt} onChange={(e) => setPrompt(e.target.value)} />
             <button onClick={handleGenerate} disabled={generating || !prompt.trim()} className="px-6 py-3 bg-white text-black rounded-[20px] font-bold text-sm hover:bg-zinc-200 transition-all disabled:opacity-50">
               {generating ? "Working..." : "Generate"}
             </button>
          </div>
          <div className="flex-1 rounded-3xl overflow-hidden relative">
             <div className="absolute inset-0 overflow-y-auto custom-scrollbar">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pb-10">
                   {generating && <div className="aspect-square bg-zinc-900/50 rounded-2xl border border-zinc-800 flex flex-col items-center justify-center animate-pulse"><Loader2 className="w-8 h-8 text-indigo-500 animate-spin" /></div>}
                   {gallery.map((item, i) => (
                     <div key={i} className="group relative aspect-square rounded-2xl overflow-hidden border border-zinc-800 hover:border-indigo-500/50 transition-all bg-black">
                        {item.type === 'video' ? <video src={item.url} className="w-full h-full object-cover" controls loop muted /> : <img src={item.url} className="w-full h-full object-cover" />}
                        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex flex-col justify-end p-4 pointer-events-none">
                           <p className="text-xs text-white font-medium line-clamp-2">{item.prompt}</p>
                        </div>
                     </div>
                   ))}
                </div>
             </div>
          </div>
       </div>
    </div>
  );
}

// 3. ModelForge (Updated with Logging)
const ModelForge = ({ addLog }: { addLog: (log: Omit<LogEntry, 'id' | 'timestamp'>) => void }) => {
  const [activeTab, setActiveTab] = useState<'hf' | 'github' | 'custom'>('hf');
  const [search, setSearch] = useState("");
  const hfModels = [
    { id: "meta-llama/Meta-Llama-3-8B", name: "Meta Llama 3 8B", task: "Text Generation", downloads: "2.4M", color: "text-blue-400" },
    { id: "mistralai/Mistral-7B-v0.1", name: "Mistral 7B", task: "Text Generation", downloads: "1.8M", color: "text-orange-400" },
  ];
  return (
    <div className="flex h-full gap-6 animate-fade-in">
       <div className="w-64 flex flex-col gap-2">
          {['hf', 'github', 'custom'].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab as any)} className={`flex items-center gap-3 p-4 rounded-2xl text-sm font-bold transition-all ${activeTab === tab ? 'bg-zinc-100 text-black shadow-lg' : 'glass text-zinc-500 hover:bg-zinc-800/50'}`}>
              {tab === 'hf' ? 'đź¤—' : tab === 'github' ? <Github className="w-5 h-5" /> : <Cpu className="w-5 h-5" />}
              <span className="capitalize">{tab === 'hf' ? 'Hugging Face' : tab === 'github' ? 'GitHub Repos' : 'Custom Weights'}</span>
            </button>
          ))}
       </div>
       <div className="flex-1 glass rounded-3xl p-6 overflow-hidden flex flex-col border border-white/5">
          <div className="relative group mb-6">
            <Search className="w-4 h-4 absolute left-4 top-1/2 -translate-y-1/2 text-zinc-500" />
            <input className="w-full bg-zinc-900/50 border border-zinc-800 rounded-xl pl-12 pr-4 py-3 outline-none text-sm text-white" placeholder="Search models..." value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar pr-2 space-y-3">
            {hfModels.filter(m => m.name.toLowerCase().includes(search.toLowerCase())).map(model => (
              <div key={model.id} className="p-4 border border-zinc-800/50 rounded-2xl bg-zinc-900/20 flex items-center justify-between group">
                 <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-xl flex items-center justify-center bg-zinc-900 border border-zinc-800 font-bold text-lg ${model.color}`}>{model.name[0]}</div>
                    <div>
                       <h4 className="font-bold text-zinc-200 text-sm group-hover:text-white transition-colors">{model.name}</h4>
                       <p className="text-[10px] text-zinc-500 mt-1">{model.id} â€˘ {model.downloads} dl</p>
                    </div>
                 </div>
                 <button onClick={() => addLog({ message: `Deployment started for ${model.id}`, type: 'info', source: 'Forge' })} className="px-4 py-2 bg-white text-black text-xs font-bold rounded-lg">Get</button>
              </div>
            ))}
          </div>
       </div>
    </div>
  );
};

const RepoArchitect = ({ addLog }: { addLog: (log: Omit<LogEntry, 'id' | 'timestamp'>) => void }) => {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [structure, setStructure] = useState<RepoNode[]>([]);
  const [sessionId] = useState(() => {
    const key = "studio_repo_session_id";
    const existing = localStorage.getItem(key);
    if (existing) return existing;
    const fresh = `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
    localStorage.setItem(key, fresh);
    return fresh;
  });

  const storeRepoMemory = async (content: string) => {
    try {
      await fetch("http://localhost:8000/api/v1/memory/store", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          memory_type: "task",
          importance: 4,
          metadata: { source: "repo_architect", tags: ["repo", "plan"] },
          agent_id: "dashboard",
          session_id: sessionId
        }),
      });
    } catch {
      // silent fail
    }
  };
  const generateRepo = async () => {
    if (!prompt.trim() || loading) return;
    setLoading(true);
    addLog({ message: `Architecting: "${prompt}"`, type: 'info', source: 'Repo' });
    try {
      const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
      const response = await ai.models.generateContent({
        model: "gemini-3-pro-preview",
        contents: `Generate a JSON array of objects for this project: "${prompt}". Keys: name, type ("file" or "folder"), children (array), content (string).`,
        config: { responseMimeType: "application/json" }
      });
      setStructure(JSON.parse(response.text || "[]"));
      await storeRepoMemory(`Repo plan: ${prompt}`);
      addLog({ message: "Success.", type: 'success', source: 'Repo' });
    } catch (e: any) {
      addLog({ message: `Failed: ${e.message}`, type: 'error', source: 'Repo' });
    } finally { setLoading(false); }
  };
  return (
    <div className="flex h-full gap-6 animate-fade-in">
      <div className="w-1/3 flex flex-col gap-4">
        <div className="glass p-5 rounded-3xl flex flex-col gap-4 border border-white/5">
          <textarea className="w-full h-32 bg-zinc-900/50 border border-zinc-800 rounded-xl p-3 text-sm focus:bg-zinc-900 outline-none resize-none text-white" placeholder="Describe your project..." value={prompt} onChange={(e) => setPrompt(e.target.value)} />
          <button onClick={generateRepo} disabled={loading || !prompt.trim()} className="w-full py-3 bg-white text-black hover:bg-zinc-200 disabled:opacity-50 rounded-xl font-bold flex items-center justify-center gap-2">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />} Generate
          </button>
        </div>
        <div className="flex-1 glass rounded-3xl p-4 overflow-y-auto custom-scrollbar border border-white/5">
          <div className="text-[10px] font-bold text-zinc-500 uppercase mb-4 px-2">File Explorer</div>
          {structure.length === 0 ? <p className="text-center text-zinc-600 text-xs py-10">No structure yet</p> : <pre className="text-xs text-zinc-400 p-2">{JSON.stringify(structure, null, 2)}</pre>}
        </div>
      </div>
      <div className="flex-1 glass rounded-3xl flex items-center justify-center text-zinc-600 border border-white/5 shadow-2xl"><Terminal className="w-8 h-8 opacity-20" /></div>
    </div>
  );
};

const TaskView = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [newTaskText, setNewTaskText] = useState("");
  const [newTaskPriority, setNewTaskPriority] = useState<'low' | 'medium' | 'high'>('medium');
  const [newTaskRecurring, setNewTaskRecurring] = useState<RecurringType>('none');
  const [newTaskDueDate, setNewTaskDueDate] = useState("");
  const [newTaskDependencies, setNewTaskDependencies] = useState<string[]>([]);
  const [sessionId] = useState(() => {
    const key = "studio_task_session_id";
    const existing = localStorage.getItem(key);
    if (existing) return existing;
    const fresh = `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 8)}`;
    localStorage.setItem(key, fresh);
    return fresh;
  });
  const [selectedTasks, setSelectedTasks] = useState<Set<string>>(new Set());
  const [sortBy, setSortBy] = useState<'newest' | 'priority' | 'dueDate'>('newest');
  const [tagFilter, setTagFilter] = useState<string | null>(null);
  const [activeSubtaskInput, setActiveSubtaskInput] = useState<string | null>(null);
  const [deleteConfirmation, setDeleteConfirmation] = useState<{ isOpen: boolean, taskId: string | null, hasSubtasks: boolean }>({ isOpen: false, taskId: null, hasSubtasks: false });
  const [clearConfirmation, setClearConfirmation] = useState(false);
  const [showDepPicker, setShowDepPicker] = useState(false);
  const [expandedInsights, setExpandedInsights] = useState<Set<string>>(new Set());
  const [viewMode, setViewMode] = useState<'list' | 'calendar'>('list');
  const [currentCalendarDate, setCurrentCalendarDate] = useState(new Date());
  
  const subtaskInputRef = useRef<HTMLInputElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const newTaskInputRef = useRef<HTMLInputElement>(null);
    const syncWithGrotto = async () => {
      try {
        const res = await fetch("http://localhost:8000/tasks/user");
        const grottoTasks = await res.json();
        setTasks(grottoTasks.map((t: any) => ({
          ...t,
          subtasks: t.subtasks || [],
          isExpanded: true,
          dependencies: t.dependencies || [],
          recurring: t.recurring || "none",
          tags: t.tags || []
        })));
      } catch (err) { console.error("Sync failed", err); }
    };

    const brainstormTasks = async () => {
      if (!newTaskText.trim()) return;
      try {
        await fetch("http://localhost:8000/tasks/user/brainstorm", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code: newTaskText })
        });
        await syncWithGrotto();
        setNewTaskText("");
      } catch (err) { console.error("Brainstorm failed", err); }
    };


  useEffect(() => {
    const saved = localStorage.getItem("studio_tasks");
    if (saved) {
      const loaded = JSON.parse(saved);
      setTasks(loaded.map((t: any) => ({
        ...t,
        priority: t.priority || 'medium',
        subtasks: t.subtasks || [],
        isExpanded: t.isExpanded !== undefined ? t.isExpanded : true,
        tags: t.tags || [],
        recurring: t.recurring || 'none',
        dependencies: t.dependencies || [],
        dueDate: t.dueDate || ""
      })));
    }
  }, []);

  const save = (t: Task[]) => {
    setTasks(t);
    localStorage.setItem("studio_tasks", JSON.stringify(t));
  };

  const storeTaskMemory = async (content: string, meta: Record<string, any> = {}) => {
    try {
      await fetch("http://localhost:8000/api/v1/memory/store", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content,
          memory_type: "task",
          importance: 5,
          metadata: { source: "task_manager", tags: ["task", "dashboard"], ...meta },
          agent_id: "dashboard",
          session_id: sessionId
        }),
      });
    } catch {
      // silent fail
    }
  };

  const parseTags = (text: string) => {
    const regex = /#(\w+)/g;
    const tags: string[] = [];
    let match;
    while ((match = regex.exec(text)) !== null) {
      tags.push(match[1]);
    }
    const cleanText = text.replace(regex, "").trim();
    return { tags, cleanText };
  };

  const addTask = async () => {
    if (!newTaskText.trim()) return;
    const { tags, cleanText } = parseTags(newTaskText);
    const newTask: Task = { 
      id: Date.now().toString(), 
      text: cleanText || newTaskText.trim(), 
      status: 'todo', 
      priority: newTaskPriority,
      subtasks: [],
      isExpanded: true,
      tags,
      recurring: newTaskRecurring,
      dependencies: newTaskDependencies,
      dueDate: newTaskDueDate
    };
    save([newTask, ...tasks]);
    await storeTaskMemory(`Task created: ${newTask.text}`, { task_id: newTask.id, priority: newTask.priority });
    setNewTaskText("");
    setNewTaskRecurring('none');
    setNewTaskDependencies([]);
    setNewTaskDueDate("");
  };

  const traverseAndUpdate = (taskArray: Task[], id: string, updater: (t: Task) => Task): Task[] => {
    return taskArray.map(t => {
      if (t.id === id) return updater(t);
      if (t.subtasks && t.subtasks.length > 0) {
        return { ...t, subtasks: traverseAndUpdate(t.subtasks, id, updater) };
      }
      return t;
    });
  };

  const traverseAndDelete = (taskArray: Task[], id: string): Task[] => {
    return taskArray.filter(t => t.id !== id).map(t => ({
      ...t,
      subtasks: t.subtasks ? traverseAndDelete(t.subtasks, id) : [],
      dependencies: t.dependencies ? t.dependencies.filter(did => did !== id) : []
    }));
  };

  const addSubtask = async (parentId: string, text: string) => {
    if (!text.trim()) return;
    const { tags, cleanText } = parseTags(text);
    const newSubtask: Task = {
      id: Date.now().toString(),
      text: cleanText || text.trim(),
      status: 'todo',
      priority: 'medium',
      subtasks: [],
      isExpanded: true,
      tags,
      recurring: 'none',
      dependencies: [],
      dueDate: ""
    };
    save(traverseAndUpdate(tasks, parentId, (p) => ({
      ...p,
      subtasks: [...(p.subtasks || []), newSubtask],
      isExpanded: true
    })));
    await storeTaskMemory(`Subtask created: ${newSubtask.text}`, { task_id: newSubtask.id, parent_id: parentId });
    setActiveSubtaskInput(null);
  };

  const findTaskById = (ts: Task[], id: string): Task | null => {
    for (const t of ts) {
      if (t.id === id) return t;
      if (t.subtasks) {
        const found = findTaskById(t.subtasks, id);
        if (found) return found;
      }
    }
    return null;
  };

  const isBlocked = (task: Task): boolean => {
    if (!task.dependencies || task.dependencies.length === 0) return false;
    return task.dependencies.some(id => {
      const depTask = findTaskById(tasks, id);
      return !depTask || depTask.status !== 'done';
    });
  };

  const handleDeleteRequest = (id: string) => {
    const task = findTaskById(tasks, id);
    if (task && task.subtasks && task.subtasks.length > 0) {
      setDeleteConfirmation({ isOpen: true, taskId: id, hasSubtasks: true });
    } else {
      deleteTask(id);
    }
  };

  const confirmDelete = () => {
    if (deleteConfirmation.taskId) {
      deleteTask(deleteConfirmation.taskId);
      setDeleteConfirmation({ isOpen: false, taskId: null, hasSubtasks: false });
    }
  };

  const deleteTask = (id: string) => {
    save(traverseAndDelete(tasks, id));
    const nextSelected = new Set(selectedTasks);
    nextSelected.delete(id);
    setSelectedTasks(nextSelected);
  };

  const toggleTaskStatus = async (id: string) => {
    const task = findTaskById(tasks, id);
    if (task && task.status !== 'done' && isBlocked(task)) {
       return;
    }
    save(traverseAndUpdate(tasks, id, (t) => ({
      ...t,
      status: t.status === 'done' ? 'todo' : 'done'
    })));
    const updated = findTaskById(tasks, id);
    if (updated) {
      await storeTaskMemory(`Task status: ${updated.text} -> ${updated.status}`, { task_id: updated.id, status: updated.status });
    }
  };

  const toggleExpand = (id: string) => {
    save(traverseAndUpdate(tasks, id, (t) => ({
      ...t,
      isExpanded: !t.isExpanded
    })));
  };

  const toggleSelect = (id: string) => {
    setSelectedTasks(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const aiSuggest = async (taskId: string) => {
    const task = findTaskById(tasks, taskId);
    if (!task) return;

    save(traverseAndUpdate(tasks, taskId, (t) => ({ ...t, loadingSuggestions: true })));

    try {
        const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
        const response = await ai.models.generateContent({
            model: "gemini-3-flash-preview",
            contents: `The project task is: "${task.text}". Provide exactly 3 short, concrete, actionable sub-tasks or tips to complete this task successfully. Format as a brief markdown list. Keep it under 50 words total.`,
        });
        const suggestion = response.text || "No insights found.";
        save(traverseAndUpdate(tasks, taskId, (t) => ({ 
            ...t, 
            suggestions: suggestion, 
            loadingSuggestions: false 
        })));
        setExpandedInsights(prev => new Set(prev).add(taskId));
    } catch (e) {
        save(traverseAndUpdate(tasks, taskId, (t) => ({ ...t, loadingSuggestions: false })));
        console.error("AI Insight failed", e);
    }
  };

  const priorityOrder = { high: 0, medium: 1, low: 2 };

  const allAvailableTags = useMemo(() => {
    const tagsSet = new Set<string>();
    const extractTags = (ts: Task[]) => {
      ts.forEach(t => {
        t.tags?.forEach(tag => tagsSet.add(tag));
        if (t.subtasks) extractTags(t.subtasks);
      });
    };
    extractTags(tasks);
    return Array.from(tagsSet).sort();
  }, [tasks]);

  const filteredTasks = useMemo(() => {
    const matchesFilter = (t: Task): boolean => {
      if (!tagFilter) return true;
      const matchesSelf = t.tags?.includes(tagFilter);
      const matchesChild = t.subtasks?.some(matchesFilter);
      return !!(matchesSelf || matchesChild);
    };

    const filterRec = (ts: Task[]): Task[] => {
      return ts.filter(matchesFilter).map(t => ({
        ...t,
        subtasks: t.subtasks ? filterRec(t.subtasks) : []
      }));
    };

    const sortRec = (ts: Task[]): Task[] => {
      let result = [...ts];
      if (sortBy === 'priority') {
        result.sort((a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]);
      } else if (sortBy === 'dueDate') {
         result.sort((a, b) => {
             if (!a.dueDate) return 1;
             if (!b.dueDate) return -1;
             return a.dueDate.localeCompare(b.dueDate);
         });
      } else {
        result.sort((a, b) => parseInt(b.id) - parseInt(a.id));
      }
      return result.map(t => ({
        ...t,
        subtasks: t.subtasks ? sortRec(t.subtasks) : []
      }));
    };

    const filtered = filterRec(tasks);
    return sortRec(filtered);
  }, [tasks, sortBy, tagFilter]);

  const exportData = (useFiltered: boolean) => {
    const targetData = useFiltered ? filteredTasks : tasks;
    const dataStr = JSON.stringify(targetData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    const exportFileDefaultName = `studio-tasks-${useFiltered ? 'filtered' : 'all'}-${new Date().toISOString().split('T')[0]}.json`;

    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const importTasks = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const json = JSON.parse(event.target?.result as string);
        if (Array.isArray(json)) {
          if (json.length === 0 || 'text' in json[0]) {
             save([...json, ...tasks]);
          }
        }
      } catch (err) {}
    };
    reader.readAsText(file);
    e.target.value = "";
  };

  const priorityColorMap = {
    high: 'text-red-400 bg-red-400/10 border-red-500/20 shadow-[0_0_15px_rgba(248,113,113,0.1)]',
    medium: 'text-amber-400 bg-amber-400/10 border-amber-500/20 shadow-[0_0_15px_rgba(251,191,36,0.1)]',
    low: 'text-blue-400 bg-blue-400/10 border-blue-500/20 shadow-[0_0_15px_rgba(96,165,250,0.1)]',
  };

  const batchDelete = () => {
    let next = [...tasks];
    selectedTasks.forEach(id => { next = traverseAndDelete(next, id); });
    save(next);
    setSelectedTasks(new Set());
  };

  const batchMarkComplete = () => {
    let next = [...tasks];
    selectedTasks.forEach(id => { next = traverseAndUpdate(next, id, (t) => ({ ...t, status: 'done' })); });
    save(next);
    setSelectedTasks(new Set());
  };

  const TaskItem: React.FC<{ task: Task, depth: number }> = ({ task, depth = 0 }) => {
    const blocked = isBlocked(task);
    const processing = task.loadingSuggestions;
    const completedSubtasks = task.subtasks?.filter(s => s.status === 'done').length || 0;
    const totalSubtasks = task.subtasks?.length || 0;
    const progress = totalSubtasks > 0 ? (completedSubtasks / totalSubtasks) * 100 : 0;
    const hasInsight = !!task.suggestions;
    const insightExpanded = expandedInsights.has(task.id);
    const relativeTime = task.dueDate ? getRelativeTime(task.dueDate) : "";
    const isOverdue = task.dueDate && new Date(task.dueDate) < new Date() && new Date(task.dueDate).toDateString() !== new Date().toDateString() && task.status !== 'done';
    const hasSubtasks = task.subtasks && task.subtasks.length > 0;

    // Indentation and tree line logic
    const nestedStyle = depth > 0 ? {
        marginLeft: `${depth * 32}px`,
        backgroundColor: `rgba(255, 255, 255, ${Math.max(0.01, 0.05 - (depth * 0.01))})`,
        borderColor: `rgba(255, 255, 255, ${Math.max(0.03, 0.08 - (depth * 0.02))})`,
    } : {};

    return (
      <div className="flex flex-col relative group/node">
        {/* Tree connector line */}
        {depth > 0 && (
            <div 
                className="absolute w-[1px] bg-zinc-800/80 group-hover/node:bg-indigo-500/30 transition-colors"
                style={{ 
                    left: `${(depth * 32) - 16}px`, 
                    top: '-8px', 
                    height: '24px' 
                }} 
            />
        )}
        {depth > 0 && (
            <div 
                className="absolute h-[1px] bg-zinc-800/80 group-hover/node:bg-indigo-500/30 transition-colors"
                style={{ 
                    left: `${(depth * 32) - 16}px`, 
                    top: '16px', 
                    width: '16px' 
                }} 
            />
        )}

        <div 
          className={`glass group p-4 rounded-2xl flex items-center gap-3 border transition-all hover:bg-zinc-800/60 relative overflow-hidden ${
            selectedTasks.has(task.id) ? 'border-indigo-500/50 bg-indigo-500/5 shadow-[0_0_20px_rgba(99,102,241,0.1)]' : 'border-white/5'
          } ${blocked && task.status !== 'done' ? 'border-dashed border-amber-500/20 bg-amber-500/5' : ''} ${processing ? 'ring-1 ring-indigo-500 animate-pulse' : ''} animate-fade-in mb-2 shadow-sm`}
          style={nestedStyle}
        >
           {totalSubtasks > 0 && (
              <div className="absolute bottom-0 left-0 h-[2px] bg-indigo-500/40 transition-all duration-700" style={{ width: `${progress}%` }} />
           )}
           
           <div className="shrink-0 w-5 flex justify-center">
             {hasSubtasks ? (
               <button 
                 onClick={(e) => { e.stopPropagation(); toggleExpand(task.id); }} 
                 className="p-0.5 hover:bg-white/10 rounded-md text-zinc-500 hover:text-white transition-colors flex items-center justify-center"
                 title={task.isExpanded ? "Collapse" : "Expand"}
               >
                 {task.isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
               </button>
             ) : (
                <div className="w-4" /> 
             )}
           </div>

           <button onClick={() => toggleSelect(task.id)} className={`transition-colors shrink-0 ${selectedTasks.has(task.id) ? 'text-indigo-500' : 'text-zinc-600 hover:text-indigo-400'}`}>
             {selectedTasks.has(task.id) ? <CheckSquare className="w-5 h-5" /> : <Square className="w-5 h-5" />}
           </button>

           <div className="relative shrink-0">
             <button 
                onClick={() => toggleTaskStatus(task.id)} 
                disabled={(blocked && task.status !== 'done') || processing}
                className={`w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all ${
                task.status === 'done' ? 'bg-green-500 border-green-500 shadow-[0_0_12px_rgba(34,197,94,0.4)]' : 
                (blocked ? 'border-amber-500/40 cursor-not-allowed bg-amber-500/10' : 'border-zinc-700 hover:border-zinc-500')
             }`}>
                {task.status === 'done' ? <CheckCircle2 className="w-4 h-4 text-zinc-900" /> : 
                 (blocked ? <Lock className="w-3 h-3 text-amber-500" /> : processing ? <Loader2 className="w-3 h-3 text-indigo-400 animate-spin" /> : null)}
             </button>
           </div>

           <div className="flex-1 flex flex-col gap-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className={`text-sm font-bold tracking-tight truncate ${task.status === 'done' ? 'text-zinc-500 line-through' : (blocked ? 'text-zinc-400' : 'text-zinc-100')} ${depth > 0 ? 'text-zinc-300' : ''}`}>
                  {task.text}
                </span>
                {blocked && task.status !== 'done' && (
                  <span className="text-[10px] font-bold text-amber-500 uppercase flex items-center gap-1 bg-amber-500/10 px-1.5 py-0.5 rounded">
                    <AlertTriangle className="w-2.5 h-2.5" /> Blocked
                  </span>
                )}
                {processing && (
                  <span className="text-[10px] font-bold text-indigo-400 uppercase flex items-center gap-1 bg-indigo-500/10 px-1.5 py-0.5 rounded animate-pulse">
                    Thinking...
                  </span>
                )}
                {task.dueDate && (
                  <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded-md border border-white/5 flex items-center gap-1 ${
                      isOverdue ? 'bg-red-500/10 text-red-400 border-red-500/20' : 
                      relativeTime === 'Today' || relativeTime === 'Tomorrow' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : 
                      'bg-zinc-900/50 text-zinc-500'
                  }`}>
                    <Clock className="w-2.5 h-2.5" /> {relativeTime}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase border shrink-0 transition-all ${priorityColorMap[task.priority]}`}>
                  {task.priority}
                </span>
                {task.recurring && task.recurring !== 'none' && (
                  <span className="px-2 py-0.5 rounded-md text-[9px] font-bold bg-zinc-800 text-indigo-400 border border-indigo-500/20 flex items-center gap-1 shrink-0 uppercase">
                    <RefreshCw className="w-2.5 h-2.5" />
                    {task.recurring}
                  </span>
                )}
                {task.dependencies && task.dependencies.length > 0 && task.status !== 'done' && (
                  <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-md bg-amber-500/10 border border-amber-500/20 text-[9px] text-amber-500 font-bold uppercase">
                    <LinkIcon className="w-2.5 h-2.5" />
                    {blocked ? 'Locked by Prereqs' : `Links: ${task.dependencies.length}`}
                  </div>
                )}
                {task.tags?.map(t => (
                  <button 
                    key={t} 
                    onClick={(e) => { e.stopPropagation(); setTagFilter(tagFilter === t ? null : t); }}
                    className={`px-2 py-0.5 rounded-md text-[9px] font-bold border flex items-center gap-1 transition-all ${
                      tagFilter === t ? 'bg-indigo-500 text-white border-indigo-400 shadow-[0_0_12px_rgba(99,102,241,0.4)]' : 'bg-zinc-800 text-zinc-400 border-zinc-700 hover:border-zinc-500'
                    }`}
                  >
                    <Hash className="w-2.5 h-2.5" />
                    {t}
                  </button>
                ))}
                {task.subtasks && task.subtasks.length > 0 && (
                  <span className="text-[9px] text-indigo-400 font-bold flex items-center gap-1 bg-indigo-500/10 px-1.5 rounded-md border border-indigo-500/20">
                    <List className="w-2.5 h-2.5" />
                    {completedSubtasks}/{totalSubtasks}
                  </span>
                )}
              </div>
           </div>

           <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
             <button 
                onClick={() => aiSuggest(task.id)} 
                disabled={processing}
                className={`p-2 rounded-lg transition-colors ${hasInsight ? 'text-indigo-400 hover:bg-indigo-400/10' : 'text-zinc-500 hover:text-white hover:bg-zinc-800'}`} 
                title="AI Insight"
              >
                {processing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
             </button>
             <button onClick={() => setActiveSubtaskInput(task.id)} className="p-2 text-zinc-500 hover:text-white hover:bg-zinc-800 rounded-lg transition-colors" title="Add subtask"><Plus className="w-4 h-4" /></button>
             <button onClick={() => handleDeleteRequest(task.id)} className="p-2 text-zinc-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg transition-colors"><Trash2 className="w-4 h-4" /></button>
           </div>
        </div>

        {hasInsight && (
            <div className={`mx-4 mb-2 p-3 glass border border-indigo-500/10 rounded-xl transition-all duration-300 ${insightExpanded ? 'max-h-96 opacity-100 mb-4' : 'max-h-0 opacity-0 overflow-hidden mb-0'}`}>
                <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2 text-[10px] font-bold text-indigo-400 uppercase tracking-widest">
                        <Brain className="w-3 h-3" /> AI Analysis
                    </div>
                    <button onClick={() => setExpandedInsights(prev => {
                        const next = new Set(prev);
                        next.delete(task.id);
                        return next;
                    })} className="p-1 hover:bg-white/5 rounded-md text-zinc-600 hover:text-white transition-colors">
                        <X className="w-3 h-3" />
                    </button>
                </div>
                <div className="text-xs text-zinc-400 leading-relaxed prose prose-invert max-w-none prose-xs">
                    <ReactMarkdown>{task.suggestions || ""}</ReactMarkdown>
                </div>
            </div>
        )}

        {!insightExpanded && hasInsight && (
            <button 
                onClick={() => setExpandedInsights(prev => new Set(prev).add(task.id))}
                className="mx-12 mb-2 text-[9px] font-bold text-indigo-500/60 uppercase hover:text-indigo-400 transition-colors flex items-center gap-1 self-start"
            >
                <Lightbulb className="w-2.5 h-2.5" /> View AI Insight
            </button>
        )}

        {activeSubtaskInput === task.id && (
          <div className="mb-4 px-2 flex items-center gap-2 animate-fade-in relative" style={{ marginLeft: `${(depth + 1) * 32}px` }}>
             <div className="absolute left-[-16px] top-[-8px] bottom-0 w-[1px] bg-indigo-500/30" />
             <div className="absolute left-[-16px] top-[16px] w-[16px] h-[1px] bg-indigo-500/30" />
             <div className="w-1.5 h-10 bg-indigo-500/40 rounded-full mr-2 shadow-[0_0_10px_rgba(99,102,241,0.2)]" />
             <div className="flex-1 glass flex items-center px-4 py-3 rounded-2xl border-indigo-500/30 ring-1 ring-indigo-500/20 bg-indigo-500/5">
                <input 
                    ref={subtaskInputRef} 
                    autoFocus 
                    className="flex-1 bg-transparent border-none text-sm text-white outline-none placeholder:text-zinc-600" 
                    placeholder="Describe subtask + #tags..." 
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') addSubtask(task.id, e.currentTarget.value);
                        if (e.key === 'Escape') setActiveSubtaskInput(null);
                    }} 
                />
                <div className="flex items-center gap-2 ml-2">
                    <span className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest hidden sm:block">Press Enter</span>
                    <button onClick={() => subtaskInputRef.current && addSubtask(task.id, subtaskInputRef.current.value)} className="p-1.5 bg-indigo-500 text-white rounded-lg hover:bg-indigo-400 transition-colors">
                        <CornerDownLeft className="w-3.5 h-3.5" />
                    </button>
                    <button onClick={() => setActiveSubtaskInput(null)} className="p-1.5 text-zinc-500 hover:text-white transition-colors">
                        <X className="w-4 h-4" />
                    </button>
                </div>
             </div>
          </div>
        )}

        {task.isExpanded && task.subtasks && task.subtasks.length > 0 && (
          <div className="flex flex-col relative">
            <div className="absolute top-0 bottom-4 w-[1px] bg-zinc-800/80" style={{ left: `${(depth * 32) + 16}px` }} />
            {task.subtasks.map(sub => <TaskItem key={sub.id} task={sub} depth={depth + 1} />)}
          </div>
        )}
      </div>
    );
  };

  // Calendar Logic
  const CalendarView = () => {
    const monthNames = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    const daysOfWeek = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
    
    const year = currentCalendarDate.getFullYear();
    const month = currentCalendarDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    
    const prevMonthDays = new Date(year, month, 0).getDate();
    
    const grid = [];
    // Prev month days
    for (let i = firstDay - 1; i >= 0; i--) {
        grid.push({ day: prevMonthDays - i, current: false, date: new Date(year, month - 1, prevMonthDays - i) });
    }
    // Current month days
    for (let i = 1; i <= daysInMonth; i++) {
        grid.push({ day: i, current: true, date: new Date(year, month, i) });
    }
    // Next month days
    const remaining = 42 - grid.length;
    for (let i = 1; i <= remaining; i++) {
        grid.push({ day: i, current: false, date: new Date(year, month + 1, i) });
    }

    const changeMonth = (offset: number) => {
        setCurrentCalendarDate(new Date(year, month + offset, 1));
    };

    const handleDateClick = (date: Date) => {
        const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
        setNewTaskDueDate(dateStr);
        newTaskInputRef.current?.focus();
    };

    return (
        <div className="flex-1 flex flex-col gap-4 animate-fade-in pr-2">
            <div className="flex items-center justify-between glass p-4 rounded-2xl border border-white/5">
                <div className="flex flex-col">
                    <h3 className="text-xl font-bold text-white tracking-tight">{monthNames[month]} {year}</h3>
                    <p className="text-[10px] text-zinc-500 font-bold uppercase tracking-widest">Active Schedule View</p>
                </div>
                <div className="flex items-center gap-2">
                    <button onClick={() => changeMonth(-1)} className="p-2 hover:bg-white/5 rounded-xl transition-colors border border-white/5"><ChevronLeft className="w-5 h-5 text-zinc-400" /></button>
                    <button onClick={() => setCurrentCalendarDate(new Date())} className="px-4 py-2 hover:bg-white/5 rounded-xl text-xs font-bold transition-colors border border-white/5 text-zinc-400 uppercase tracking-widest">Today</button>
                    <button onClick={() => changeMonth(1)} className="p-2 hover:bg-white/5 rounded-xl transition-colors border border-white/5"><ChevronRight className="w-5 h-5 text-zinc-400" /></button>
                </div>
            </div>
            <div className="flex-1 grid grid-cols-7 grid-rows-[auto_1fr] gap-2">
                {daysOfWeek.map(d => (
                    <div key={d} className="text-center text-[10px] font-bold text-zinc-600 uppercase tracking-widest pb-1">{d}</div>
                ))}
                {grid.map((cell, idx) => {
                    const dateStr = `${cell.date.getFullYear()}-${String(cell.date.getMonth() + 1).padStart(2, '0')}-${String(cell.date.getDate()).padStart(2, '0')}`;
                    const tasksForDay = tasks.filter(t => t.dueDate === dateStr);
                    const isToday = new Date().toDateString() === cell.date.toDateString();
                    const isPast = cell.date < new Date() && !isToday;

                    return (
                        <button 
                            key={idx} 
                            onClick={() => handleDateClick(cell.date)}
                            className={`glass min-h-[100px] p-2 rounded-xl border border-white/5 flex flex-col gap-1 transition-all text-left group ${!cell.current ? 'opacity-30' : 'hover:bg-zinc-800/40 hover:border-zinc-700/50 hover:scale-[1.02]'}`}
                        >
                            <div className="flex items-center justify-between w-full">
                                <span className={`text-xs font-bold ${isToday ? 'w-6 h-6 rounded-lg bg-indigo-500 text-white flex items-center justify-center shadow-lg shadow-indigo-500/20' : 'text-zinc-500'}`}>{cell.day}</span>
                                {tasksForDay.length > 0 && <span className="w-1.5 h-1.5 rounded-full bg-indigo-400" />}
                            </div>
                            <div className="flex-1 overflow-y-auto scrollbar-hide space-y-1 mt-1 w-full">
                                {tasksForDay.map(t => {
                                    const isOverdue = isPast && t.status !== 'done';
                                    return (
                                        <div key={t.id} className={`text-[9px] px-1.5 py-1 rounded-md border truncate cursor-pointer transition-all ${
                                            t.status === 'done' ? 'bg-zinc-900/50 border-zinc-800 text-zinc-600 line-through opacity-50' : 
                                            isOverdue ? 'bg-red-500/20 border-red-500/30 text-red-300 font-bold' :
                                            priorityColorMap[t.priority]
                                        }`}>
                                            {t.text}
                                        </div>
                                    );
                                })}
                            </div>
                        </button>
                    );
                })}
            </div>
        </div>
    );
  };

  const topLevelTasks = tasks.filter(t => t.status !== 'done');

  return (
    <div className="flex flex-col h-full gap-6 animate-fade-in relative">
      <div className="glass p-6 rounded-[32px] flex flex-col gap-4 border border-white/10 shadow-2xl shadow-black/60 bg-gradient-to-br from-zinc-900/80 to-black/90">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 bg-white/5 rounded-2xl flex items-center justify-center border border-white/10 shrink-0"><CheckCircle2 className="w-6 h-6 text-indigo-400" /></div>
          <input 
            ref={newTaskInputRef}
            className="flex-1 bg-zinc-900/40 border border-zinc-800/50 rounded-2xl pl-6 pr-6 py-4 outline-none focus:ring-2 focus:ring-indigo-500/30 text-white placeholder:text-zinc-600 transition-all text-sm font-medium" 
            placeholder="Plan your next sprint (e.g. Build API #backend)..." 
            value={newTaskText} 
            onChange={e => setNewTaskText(e.target.value)} 
            onKeyDown={e => e.key === "Enter" && addTask()} 
          />
          <button onClick={addTask} className="h-14 w-14 bg-white text-black rounded-2xl flex items-center justify-center hover:bg-zinc-200 transition-all shadow-xl active:scale-95 group">
            <Plus className="w-6 h-6 group-hover:rotate-90 transition-transform duration-300" />
          </button>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 px-2">
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-3">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Priority:</span>
                <div className="flex gap-2">
                {(['low', 'medium', 'high'] as const).map(p => (
                    <button key={p} onClick={() => setNewTaskPriority(p)} className={`px-4 py-1.5 rounded-xl text-[10px] font-bold uppercase transition-all border ${newTaskPriority === p ? 'bg-white text-black border-white shadow-lg' : 'bg-zinc-900/60 text-zinc-500 border-zinc-800/50 hover:border-zinc-700'}`}>
                    {p}
                    </button>
                ))}
                </div>
            </div>
            <div className="flex items-center gap-3 relative">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Linked:</span>
                <button 
                  onClick={() => setShowDepPicker(!showDepPicker)}
                  className={`px-4 py-1.5 rounded-xl text-[10px] font-bold uppercase border transition-all flex items-center gap-2 ${newTaskDependencies.length > 0 ? 'bg-amber-500/10 text-amber-500 border-amber-500/30' : 'bg-zinc-900/60 text-zinc-500 border-zinc-800/50'}`}
                >
                  <LinkIcon className="w-3 h-3" />
                  {newTaskDependencies.length || 'None'}
                </button>
                {showDepPicker && (
                  <div className="absolute top-full left-0 mt-2 w-64 glass rounded-2xl border border-white/10 z-[60] p-4 shadow-2xl animate-fade-in max-h-60 overflow-y-auto custom-scrollbar">
                     <div className="text-[10px] font-bold text-zinc-500 uppercase mb-3 px-1">Select Prerequisites</div>
                     {topLevelTasks.length === 0 ? <p className="text-[10px] text-zinc-600 px-1">No active tasks to link.</p> : topLevelTasks.map(t => (
                        <button key={t.id} onClick={() => setNewTaskDependencies(prev => prev.includes(t.id) ? prev.filter(i => i !== t.id) : [...prev, t.id])} className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors mb-1 border ${newTaskDependencies.includes(t.id) ? 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20' : 'text-zinc-400 border-transparent hover:bg-zinc-800/50'}`}>
                           {t.text}
                        </button>
                     ))}
                  </div>
                )}
            </div>
          </div>
          <div className="flex items-center gap-4">
             <div className="flex items-center gap-2">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Due:</span>
                <input 
                    type="date" 
                    value={newTaskDueDate} 
                    onChange={e => setNewTaskDueDate(e.target.value)}
                    className="bg-zinc-900/60 border border-zinc-800/50 rounded-xl px-3 py-1.5 text-[10px] font-bold text-zinc-400 outline-none focus:border-indigo-500/50 transition-all uppercase appearance-none"
                />
             </div>
            <div className="flex items-center gap-3">
                <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Repeat:</span>
                <div className="flex gap-2">
                {(['none', 'daily', 'weekly', 'monthly'] as RecurringType[]).map(r => (
                    <button key={r} onClick={() => setNewTaskRecurring(r)} className={`px-3 py-1.5 rounded-xl text-[10px] font-bold uppercase transition-all border ${newTaskRecurring === r ? 'bg-indigo-500 text-white border-indigo-400' : 'bg-zinc-900/60 text-zinc-500 border-zinc-800/50 hover:border-zinc-700'}`}>
                    {r === 'none' ? 'None' : r.charAt(0).toUpperCase()}
                    </button>
                ))}
                </div>
            </div>
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-4 px-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-1 glass p-1 rounded-xl border border-white/5">
                <button onClick={() => setViewMode('list')} className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-bold uppercase transition-all ${viewMode === 'list' ? 'bg-white text-black shadow' : 'text-zinc-500 hover:text-white'}`}>
                    <LayoutGrid className="w-3.5 h-3.5" /> List
                </button>
                <button onClick={() => setViewMode('calendar')} className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] font-bold uppercase transition-all ${viewMode === 'calendar' ? 'bg-white text-black shadow' : 'text-zinc-500 hover:text-white'}`}>
                    <CalendarDays className="w-3.5 h-3.5" /> Schedule
                </button>
            </div>
            <div className="w-[1px] h-6 bg-zinc-800 mx-1" />
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Order:</span>
              <select value={sortBy} onChange={e => setSortBy(e.target.value as any)} className="bg-transparent text-xs font-bold text-white outline-none cursor-pointer hover:text-indigo-400 transition-colors border-b border-transparent hover:border-indigo-500">
                <option value="newest" className="bg-zinc-900">Creation Date</option>
                <option value="priority" className="bg-zinc-900">Task Priority</option>
                <option value="dueDate" className="bg-zinc-900">Due Date</option>
              </select>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1 glass p-1 rounded-xl border border-white/5">
                <input type="file" ref={fileInputRef} onChange={importTasks} className="hidden" accept=".json" />
                <button onClick={() => fileInputRef.current?.click()} className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-white/5 rounded-lg text-[10px] font-bold text-zinc-400 hover:text-white transition-all group" title="Import JSON">
                   <FileUp className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" /> IMPORT
                </button>
                <div className="w-[1px] h-4 bg-zinc-800 mx-1" />
                <button onClick={() => exportData(true)} className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-white/5 rounded-lg text-[10px] font-bold text-zinc-400 hover:text-white transition-all group" title="Export Filtered">
                   <Download className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" /> EXPORT
                </button>
                <button onClick={() => exportData(false)} className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-white/5 rounded-lg text-[10px] font-bold text-zinc-500 hover:text-white transition-all group" title="Export All Data">
                   <FileJson className="w-3.5 h-3.5 opacity-50" /> ALL
                </button>
                <div className="w-[1px] h-4 bg-zinc-800 mx-1" />
                <button onClick={() => setClearConfirmation(true)} className="flex items-center gap-1.5 px-3 py-1.5 hover:bg-red-500/10 rounded-lg text-[10px] font-bold text-zinc-600 hover:text-red-400 transition-all group" title="Clear All Tasks">
                   <Eraser className="w-3.5 h-3.5 group-hover:scale-110 transition-transform" /> CLEAR
                </button>
            </div>
            <div className="w-[1px] h-4 bg-zinc-800 ml-2" />
            <div className="flex items-center gap-2">
              <Tag className="w-3.5 h-3.5 text-indigo-400" />
              <span className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest">Explorer:</span>
            </div>
          </div>
        </div>
        {viewMode === 'list' && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1 custom-scrollbar scrollbar-hide">
            <button 
                onClick={() => setTagFilter(null)} 
                className={`px-4 py-2 rounded-2xl text-[10px] font-bold uppercase tracking-wider transition-all border whitespace-nowrap ${!tagFilter ? 'bg-white text-black border-white shadow-lg shadow-white/5' : 'bg-zinc-900/40 border-zinc-800 text-zinc-500 hover:border-zinc-700'}`}
            >
                All Workspaces
            </button>
            {allAvailableTags.map(tag => (
                <button key={tag} onClick={() => setTagFilter(tagFilter === tag ? null : tag)} className={`px-4 py-2 rounded-2xl text-[10px] font-bold uppercase tracking-wider transition-all border whitespace-nowrap flex items-center gap-1.5 ${tagFilter === tag ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-600/20' : 'bg-zinc-900/40 border-zinc-800 text-zinc-500 hover:border-zinc-700'}`}>
                <Hash className="w-2.5 h-2.5 opacity-50" />
                {tag}
                </button>
            ))}
            </div>
        )}
      </div>

      <div className="flex-1 overflow-y-auto custom-scrollbar pb-32 pr-2">
         {viewMode === 'list' ? (
             <div className="space-y-1">
                {filteredTasks.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-24 opacity-20 select-none animate-pulse">
                    <Layers className="w-20 h-20 mb-6 text-zinc-400" />
                    <p className="text-sm font-bold tracking-[0.2em] uppercase text-zinc-400">Workspace is empty</p>
                </div>
                ) : filteredTasks.map(task => (
                    <TaskItem key={task.id} task={task} depth={0} />
                ))}
            </div>
         ) : (
             <CalendarView />
         )}
      </div>

      {/* Clear All Confirmation */}
      <Modal 
        isOpen={clearConfirmation} 
        onClose={() => setClearConfirmation(false)}
        title="Wipe Entire Workspace?"
        footer={
          <>
            <button onClick={() => setClearConfirmation(false)} className="px-6 py-2.5 rounded-2xl text-xs font-bold text-zinc-400 hover:text-white transition-colors">Abort</button>
            <button onClick={() => { save([]); setClearConfirmation(false); }} className="px-6 py-2.5 rounded-2xl text-xs font-bold bg-red-500 text-white shadow-lg shadow-red-500/20 hover:bg-red-400 transition-colors text-white">Wipe Workspace</button>
          </>
        }
      >
        <p>This will permanently delete ALL tasks and subtasks. This action cannot be undone.</p>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal 
        isOpen={deleteConfirmation.isOpen} 
        onClose={() => setDeleteConfirmation({ isOpen: false, taskId: null, hasSubtasks: false })}
        title="Delete Task with Dependencies?"
        footer={
          <>
            <button onClick={() => setDeleteConfirmation({ isOpen: false, taskId: null, hasSubtasks: false })} className="px-6 py-2.5 rounded-2xl text-xs font-bold text-zinc-400 hover:text-white transition-colors">Abort</button>
            <button onClick={confirmDelete} className="px-6 py-2.5 rounded-2xl text-xs font-bold bg-red-500 text-white shadow-lg shadow-red-500/20 hover:bg-red-400 transition-colors">Destroy Everything</button>
          </>
        }
      >
        <div className="flex flex-col gap-4">
           <div className="w-12 h-12 rounded-2xl bg-red-500/10 flex items-center justify-center border border-red-500/20"><AlertTriangle className="w-6 h-6 text-red-500" /></div>
           <p>This task contains subtasks. Deleting it will also recursively remove all associated sub-items. This action is irreversible.</p>
        </div>
      </Modal>

      {/* BATCH ACTIONS BAR - PRO VERSION */}
      {selectedTasks.size > 0 && viewMode === 'list' && (
        <div className="fixed bottom-12 left-1/2 -translate-x-1/2 flex items-center gap-6 glass p-4 rounded-[28px] border border-indigo-500/40 shadow-2xl shadow-indigo-500/20 animate-fade-in z-50 ring-1 ring-white/10 bg-black/80">
           <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-indigo-500/20 flex items-center justify-center text-indigo-400 font-bold text-sm border border-indigo-500/30">{selectedTasks.size}</div>
              <div className="flex flex-col">
                <span className="text-[10px] font-bold text-white uppercase tracking-widest">Items Selected</span>
                <span className="text-[9px] text-zinc-500">Bulk operational mode active</span>
              </div>
           </div>
           <div className="h-10 w-[1px] bg-zinc-800" />
           <div className="flex items-center gap-2">
             <button onClick={batchMarkComplete} className="flex items-center gap-2 px-6 py-3 bg-zinc-900/80 hover:bg-zinc-800 rounded-2xl text-[10px] font-bold text-emerald-400 transition-all border border-zinc-800 group">
                <CheckCircle2 className="w-4 h-4 group-hover:scale-110 transition-transform" /> COMPLETE
             </button>
             <button onClick={batchDelete} className="flex items-center gap-2 px-6 py-3 bg-zinc-900/80 hover:bg-red-500/10 rounded-2xl text-[10px] font-bold text-red-400 transition-all border border-zinc-800 group">
                <Trash2 className="w-4 h-4 group-hover:scale-110 transition-transform" /> DESTROY
             </button>
           </div>
           <button onClick={() => setSelectedTasks(new Set())} className="p-3 text-zinc-600 hover:text-white transition-colors"><X className="w-5 h-5" /></button>
        </div>
      )}
    </div>
  );
};

// 4. Grota Dashboard - powered by Builder API :8800
const BUILDER_API = "http://localhost:8800/api/v1";
const BUILDER_WS = "ws://localhost:8800/ws/feed";
const agentIcons: Record<string, React.ReactNode> = { SHAD: <Zap className="w-4 h-4"/>, CLAUDE_LUSTRO: <Code className="w-4 h-4"/>, GEMINI_ARCHITECT: <Mountain className="w-4 h-4"/>, CODEX: <Box className="w-4 h-4"/> };
const statusColor: Record<string, string> = { idle: "text-emerald-400", active: "text-yellow-400", offline: "text-red-400" };
const taskStatusColor: Record<string, string> = { pending: "text-zinc-400", assigned: "text-blue-400", running: "text-yellow-400", done: "text-emerald-400", failed: "text-red-400" };

const GrotaView = ({ addLog }: { addLog: (log: Omit<LogEntry, 'id' | 'timestamp'>) => void }) => {
  const [agents, setAgents] = useState<any[]>([]);
  const [tasks, setTasks] = useState<any[]>([]);
  const [health, setHealth] = useState<any>(null);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);
  const [agentDetail, setAgentDetail] = useState<any>(null);
  const [feed, setFeed] = useState<any[]>([]);
  const [builderOnline, setBuilderOnline] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newPriority, setNewPriority] = useState("medium");
  const wsRef = useRef<WebSocket | null>(null);

  const fetchData = () => {
    fetch(`${BUILDER_API}/agents`).then(r => r.json()).then(d => setAgents(d.agents || [])).catch(() => {});
    fetch(`${BUILDER_API}/tasks`).then(r => r.json()).then(d => setTasks(d || [])).catch(() => {});
    fetch(`${BUILDER_API}/health`).then(r => r.json()).then(d => { setHealth(d); setBuilderOnline(true); }).catch(() => setBuilderOnline(false));
  };

  useEffect(() => {
    fetchData();
    const connect = () => {
      const ws = new WebSocket(BUILDER_WS);
      ws.onopen = () => { setBuilderOnline(true); };
      ws.onmessage = (e) => { try { const ev = JSON.parse(e.data); if (ev.type === "init") { setAgents(ev.data.agents || []); setTasks(ev.data.tasks || []); } else if (ev.type !== "heartbeat" && ev.type !== "pong") { setFeed(prev => [{ ...ev, id: Date.now() }, ...prev].slice(0, 50)); fetchData(); } } catch {} };
      ws.onclose = () => { setBuilderOnline(false); setTimeout(connect, 5000); };
      ws.onerror = () => ws.close();
      wsRef.current = ws;
    };
    connect();
    const interval = setInterval(fetchData, 15000);
    return () => { clearInterval(interval); wsRef.current?.close(); };
  }, []);

  useEffect(() => {
    if (!activeAgent) { setAgentDetail(null); return; }
    fetch(`${BUILDER_API}/agents/${activeAgent}`).then(r => r.json()).then(setAgentDetail).catch(() => setAgentDetail(null));
  }, [activeAgent]);

  const createTask = () => {
    if (!newTitle.trim()) return;
    fetch(`${BUILDER_API}/tasks`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title: newTitle, description: newDesc || newTitle, priority: newPriority }) })
      .then(r => r.json()).then(t => { addLog({ message: `Task created: ${t.title}`, type: "success", source: "Builder" }); setNewTitle(""); setNewDesc(""); fetchData(); })
      .catch(() => addLog({ message: "Failed to create task", type: "error", source: "Builder" }));
  };

  const dispatchTask = (taskId: string) => {
    fetch(`${BUILDER_API}/tasks/${taskId}/dispatch`, { method: "POST" })
      .then(r => r.json()).then(d => { addLog({ message: `Dispatched to ${d.routing?.agent} via ${d.routing?.bridge}`, type: "success", source: "Builder" }); fetchData(); })
      .catch(() => addLog({ message: "Dispatch failed", type: "error", source: "Builder" }));
  };

  return (
    <div className="flex h-full gap-6 animate-fade-in text-zinc-100">
      {/* Left Panel: Wataha Status */}
      <div className="w-80 flex flex-col gap-4">
        <div className="glass p-6 rounded-[32px] border border-white/10 bg-black/40 backdrop-blur-md">
          <div className="flex items-center gap-3 mb-8">
            <div className={`p-3 rounded-2xl border ${builderOnline ? 'bg-indigo-500/20 border-indigo-500/30' : 'bg-red-500/20 border-red-500/30'}`}>
              <Mountain className={`w-6 h-6 ${builderOnline ? 'text-indigo-400' : 'text-red-400'}`} />
            </div>
            <div>
              <h3 className="text-xl font-black uppercase tracking-tighter italic">Grota Lumena</h3>
              <p className="text-[10px] font-bold text-zinc-500 tracking-[0.2em] uppercase">
                {builderOnline ? `Builder v${health?.version || '?'} // ${health?.ollama || '?'}` : 'Builder Offline'}
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {agents.map(agent => (
              <button
                key={agent.name}
                onClick={() => setActiveAgent(activeAgent === agent.name ? null : agent.name)}
                className="w-full p-4 rounded-2xl border border-white/5 hover:border-indigo-500/30 transition-all duration-500 flex items-center justify-between group relative overflow-hidden"
              >
                <div className="flex items-center gap-3 z-10">
                  <div className={`w-2 h-2 rounded-full ${agent.status === 'active' ? 'bg-yellow-400 animate-pulse' : agent.status === 'idle' ? 'bg-emerald-400' : 'bg-red-400'} shadow-[0_0_8px_currentColor]`} />
                  <span className="font-bold text-sm tracking-tight">{agent.name}</span>
                </div>
                <div className="flex items-center gap-2 z-10">
                  <span className={`text-[9px] font-black uppercase tracking-widest ${statusColor[agent.status] || 'text-zinc-500'}`}>{agent.status}</span>
                  {agentIcons[agent.name] || <Cpu className="w-4 h-4"/>}
                </div>
                {activeAgent === agent.name && <div className="absolute inset-0 bg-gradient-to-r from-indigo-500/5 to-transparent animate-shimmer" />}
              </button>
            ))}
          </div>
        </div>

        {/* Live Feed */}
        <div className="flex-1 glass p-6 rounded-[32px] border border-white/10 bg-black/20 flex flex-col">
          <div className="flex items-center justify-between mb-6">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-yellow-400" />
              <span className="text-[10px] font-black uppercase tracking-[0.3em] text-zinc-400">Live Feed</span>
            </div>
            <button onClick={fetchData}><RefreshCw className="w-3 h-3 text-zinc-600 hover:text-zinc-300 transition-colors" /></button>
          </div>
          <div className="flex-1 overflow-y-auto custom-scrollbar space-y-4 pr-2">
            {feed.length === 0 && agents.map((a, i) => (
              <div key={i} className="group border-l-2 border-zinc-800 pl-4 py-1 hover:border-indigo-500/50 transition-colors">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[10px] font-black text-indigo-400 uppercase">{a.name}</span>
                </div>
                <p className="text-[11px] text-zinc-400 leading-relaxed font-medium">{a.bridge_type} | {a.capabilities?.join(", ")}</p>
              </div>
            ))}
            {feed.map((ev: any) => (
              <div key={ev.id} className="group border-l-2 border-indigo-500/30 pl-4 py-1 hover:border-indigo-500/50 transition-colors">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[9px] font-bold text-zinc-500 font-mono">[{new Date(ev.timestamp).toLocaleTimeString()}]</span>
                  <span className="text-[10px] font-black text-indigo-400 uppercase">{ev.type}</span>
                </div>
                <p className="text-[11px] text-zinc-400 leading-relaxed font-medium">{ev.data?.agent || ev.data?.task_id || JSON.stringify(ev.data).slice(0, 80)}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col gap-6">
        <div className="glass p-8 rounded-[40px] border border-white/10 flex-1 relative overflow-hidden bg-gradient-to-br from-zinc-900/40 to-black/60">
          {activeAgent && agentDetail ? (
            <div className="animate-fade-in flex flex-col h-full relative z-10">
              <div className="flex items-center justify-between mb-10">
                <div className="flex flex-col">
                  <h2 className="text-4xl font-black text-white tracking-tighter uppercase italic">{activeAgent} // DATA_STREAM</h2>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="px-2 py-0.5 bg-white/5 rounded text-[9px] font-bold text-zinc-500 uppercase tracking-widest border border-white/5">{agentDetail.bridge_type}</div>
                    <div className={`px-2 py-0.5 rounded text-[9px] font-bold uppercase tracking-widest border italic ${agentDetail.status === 'active' ? 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20' : 'bg-indigo-500/10 text-indigo-400 border-indigo-500/20'}`}>{agentDetail.status}</div>
                  </div>
                </div>
                <button onClick={() => { fetch(`${BUILDER_API}/agents/${activeAgent}/ping`, {method:'POST'}).then(r=>r.json()).then(d => addLog({message: `Ping ${activeAgent}: ${d.status}`, type: d.alive ? 'success' : 'warning', source: 'Builder'})); fetchData(); }} className="px-6 py-3 bg-white text-black rounded-2xl text-xs font-black uppercase tracking-widest hover:scale-105 transition-all shadow-xl shadow-white/5">Ping Agent</button>
              </div>

              <div className="flex-1 overflow-y-auto custom-scrollbar pr-6">
                <div className="prose prose-invert max-w-none">
                  <div className="p-6 rounded-[24px] bg-white/2 border border-white/5 mb-6">
                    <h4 className="text-xs font-bold text-indigo-400 uppercase mb-4 tracking-widest flex items-center gap-2">
                      <Brain className="w-4 h-4"/> {agentDetail.role}
                    </h4>
                    <p className="text-zinc-300 leading-relaxed text-sm whitespace-pre-wrap">{agentDetail.who_am_i?.split('\n').slice(0, 8).join('\n') || 'No WHO_AM_I data'}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-6 rounded-[24px] bg-indigo-500/5 border border-indigo-500/10">
                      <h4 className="text-[10px] font-black text-zinc-500 uppercase mb-3 tracking-widest">Capabilities</h4>
                      <div className="flex flex-wrap gap-2">
                        {agentDetail.capabilities?.map((c: string) => (
                          <span key={c} className="px-2 py-1 bg-indigo-500/10 rounded-lg text-[10px] font-bold text-indigo-300 border border-indigo-500/20">{c}</span>
                        ))}
                      </div>
                    </div>
                    <div className="p-6 rounded-[24px] bg-white/2 border border-white/5">
                      <h4 className="text-[10px] font-black text-zinc-500 uppercase mb-3 tracking-widest">Info</h4>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between"><span className="text-xs text-zinc-400">Bridge</span><span className="text-xs font-bold text-zinc-300">{agentDetail.bridge_type}</span></div>
                        <div className="flex items-center justify-between"><span className="text-xs text-zinc-400">Last seen</span><span className="text-xs font-bold text-zinc-300">{agentDetail.last_seen ? new Date(agentDetail.last_seen).toLocaleTimeString() : 'N/A'}</span></div>
                        <div className="flex items-center justify-between"><span className="text-xs text-zinc-400">Current task</span><span className="text-xs font-bold text-zinc-300">{agentDetail.current_task || 'none'}</span></div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ) : (
            <div className="animate-fade-in flex flex-col h-full relative z-10">
              <div className="flex items-center justify-between mb-8">
                <h2 className="text-3xl font-black text-white tracking-tighter uppercase italic">Task Queue</h2>
                <div className="flex items-center gap-3">
                  {health && <span className="text-[10px] font-bold text-zinc-500 uppercase">Ollama: <span className={health.ollama === 'online' ? 'text-emerald-400' : 'text-red-400'}>{health.ollama}</span> | Models: {health.ollama_models?.length || 0}</span>}
                </div>
              </div>
              <div className="mb-6 p-4 rounded-2xl bg-white/2 border border-white/5">
                <div className="flex gap-3">
                  <input value={newTitle} onChange={e => setNewTitle(e.target.value)} placeholder="Task title..." className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-indigo-500/50" onKeyDown={e => e.key === 'Enter' && createTask()} />
                  <select value={newPriority} onChange={e => setNewPriority(e.target.value)} className="bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-zinc-400 focus:outline-none">
                    <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
                  </select>
                  <button onClick={createTask} className="px-5 py-2 bg-indigo-500 hover:bg-indigo-400 text-white rounded-xl text-xs font-bold uppercase transition-all"><Plus className="w-4 h-4"/></button>
                </div>
                {newTitle && <input value={newDesc} onChange={e => setNewDesc(e.target.value)} placeholder="Description (optional)..." className="w-full mt-2 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-indigo-500/50" />}
              </div>
              <div className="flex-1 overflow-y-auto custom-scrollbar pr-4 space-y-3">
                {tasks.length === 0 && <p className="text-zinc-600 text-sm text-center mt-12">No tasks yet. Create one above.</p>}
                {tasks.map((t: any) => (
                  <div key={t.id} className="p-4 rounded-2xl bg-white/2 border border-white/5 hover:border-indigo-500/20 transition-all group">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className={`w-2 h-2 rounded-full ${t.status === 'done' ? 'bg-emerald-400' : t.status === 'running' ? 'bg-yellow-400 animate-pulse' : t.status === 'failed' ? 'bg-red-400' : 'bg-zinc-500'}`} />
                        <span className="text-sm font-bold text-zinc-200">{t.title}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`text-[9px] font-black uppercase tracking-widest ${taskStatusColor[t.status] || 'text-zinc-500'}`}>{t.status}</span>
                        <span className="text-[9px] font-bold text-zinc-600 uppercase">{t.priority}</span>
                        {t.assigned_to && <span className="text-[9px] font-bold text-indigo-400">{t.assigned_to}</span>}
                        {t.status === 'pending' && <button onClick={() => dispatchTask(t.id)} className="px-3 py-1 bg-indigo-500/20 hover:bg-indigo-500/40 rounded-lg text-[10px] font-bold text-indigo-300 transition-all uppercase">Dispatch</button>}
                      </div>
                    </div>
                    {t.result && <pre className="mt-3 p-3 rounded-xl bg-black/40 text-[11px] text-zinc-400 overflow-x-auto whitespace-pre-wrap max-h-40">{t.result.slice(0, 500)}{t.result.length > 500 ? '...' : ''}</pre>}
                    {t.error && <p className="mt-2 text-[11px] text-red-400">{t.error}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}
          <div className="absolute top-[-10%] right-[-10%] w-64 h-64 bg-indigo-500/5 rounded-full blur-[80px]" />
          <div className="absolute bottom-0 left-0 w-full h-[1px] bg-gradient-to-r from-transparent via-indigo-500/20 to-transparent" />
        </div>
        <div className="glass p-2 rounded-[24px] border border-white/10 flex items-center justify-between bg-black/40">
          <div className="flex items-center gap-2 px-4">
            <div className={`w-2 h-2 rounded-full ${builderOnline ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`} />
            <span className="text-[10px] font-black uppercase text-zinc-500 tracking-widest">
              {builderOnline ? `Builder Online // ${tasks.filter((t: any) => t.status === 'running').length} running // ${agents.length} agents` : 'Builder Offline'}
            </span>
          </div>
          <div className="flex gap-1">
            <button onClick={fetchData} className="px-4 py-2 hover:bg-white/5 rounded-xl text-[10px] font-bold text-zinc-400 transition-all uppercase">Refresh</button>
            <button onClick={() => { fetch(`${BUILDER_API}/agents/refresh`, {method:'POST'}).then(() => fetchData()); }} className="px-4 py-2 hover:bg-white/5 rounded-xl text-[10px] font-bold text-zinc-400 transition-all uppercase">Rescan Agents</button>
            <div className="w-[1px] h-4 bg-zinc-800 self-center mx-2" />
            <button onClick={() => addLog({message: "Emergency Snapshot Triggered.", type: 'warning', source: 'Core'})} className="px-4 py-2 bg-red-500/10 hover:bg-red-500/20 rounded-xl text-[10px] font-bold text-red-400 transition-all uppercase">Snapshot</button>
          </div>
        </div>
      </div>
    </div>
  );
};
// --- View Shells ---


const EvolutionView = () => {
  const [nodes, setNodes] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    fetch("http://localhost:8000/evolution")
      .then(res => res.json())
      .then(data => {
        setNodes(data.nodes || []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  return (
    <div className="flex-1 p-8 overflow-y-auto bg-[#0a0a0b]">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8 flex items-center gap-3 text-orange-500">
          <Brain className="w-8 h-8" /> DRZEWO EWOLUCJI ŚWIADOMOŚCI
        </h1>
        {loading ? (
          <div className="flex items-center gap-3 text-gray-400"><Loader2 className="animate-spin" /> Ładowanie synaps...</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {nodes.map((node: any) => (
              <div key={node.id} className="p-6 rounded-2xl bg-white/5 border border-white/10 hover:border-orange-500/50 transition-all group">
                <div className="text-orange-400 font-bold mb-2 flex items-center gap-2">
                   <Sparkles className="w-4 h-4" /> {node.label}
                </div>
                <div className="text-gray-300 text-sm leading-relaxed italic">
                  "{node.text}"
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

const MemoryView = ({ addLog }: { addLog: (log: Omit<LogEntry, 'id' | 'timestamp'>) => void }) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any[]>([]);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [typeFilter, setTypeFilter] = useState("all");
  const [page, setPage] = useState(0);
  const pageSize = 10;
  const [agentFilter, setAgentFilter] = useState("");
  const [sessionFilter, setSessionFilter] = useState("");
  const [searchPage, setSearchPage] = useState(0);
  const searchPageSize = 8;
  const [tagFilter, setTagFilter] = useState("all");
  const [metrics, setMetrics] = useState<{by_agent: Record<string, number>; by_type: Record<string, number>; by_tag: Record<string, number>} | null>(null);
  const [latestReport, setLatestReport] = useState<{file: string; content: string} | null>(null);
  const [collectiveOnly, setCollectiveOnly] = useState(false);
  const agentBadgeClass = (agent?: string) => {
    switch (agent) {
      case "dashboard": return "bg-blue-500/20 text-blue-300 border-blue-500/30";
      case "shad": return "bg-red-500/20 text-red-300 border-red-500/30";
      case "codex": return "bg-emerald-500/20 text-emerald-300 border-emerald-500/30";
      case "gemini": return "bg-indigo-500/20 text-indigo-300 border-indigo-500/30";
      case "claude": return "bg-sky-500/20 text-sky-300 border-sky-500/30";
      default: return "bg-white/5 text-zinc-400 border-white/10";
    }
  };

  const loadRecent = async (pageIndex = 0) => {
    setLoading(true);
    try {
      const offset = pageIndex * pageSize;
      const params = new URLSearchParams({
        limit: String(pageSize),
        offset: String(offset),
      });
      if (!collectiveOnly) {
        if (agentFilter.trim()) params.set("agent_id", agentFilter.trim());
        if (sessionFilter.trim()) params.set("session_id", sessionFilter.trim());
      }
      const endpoint = collectiveOnly
        ? `http://localhost:8000/api/v1/memory/collective?${params.toString()}`
        : `http://localhost:8000/api/v1/memory/recent?${params.toString()}`;
      const res = await fetch(endpoint);
      const data = await res.json();
      setResults(data.results || []);
      setPage(pageIndex);
      setSearchPage(0);
      addLog({ message: "Loaded recent memories.", type: "success", source: "Memory" });
    } catch (e: any) {
      addLog({ message: `Memory load failed: ${e.message}`, type: "error", source: "Memory" });
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/memory/stats");
      const data = await res.json();
      setStats(data.stats || null);
    } catch (e: any) {
      addLog({ message: `Memory stats failed: ${e.message}`, type: "warning", source: "Memory" });
    }
  };
  const loadMetrics = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/memory/metrics");
      const data = await res.json();
      setMetrics(data.success ? data : null);
    } catch (e: any) {
      addLog({ message: `Memory metrics failed: ${e.message}`, type: "warning", source: "Memory" });
    }
  };
  const loadLatestReport = async () => {
    try {
      const res = await fetch("http://localhost:8000/api/v1/reports/latest");
      const data = await res.json();
      if (data.success) {
        setLatestReport({ file: data.file, content: data.content });
      }
    } catch (e: any) {
      addLog({ message: `Latest report failed: ${e.message}`, type: "warning", source: "Reports" });
    }
  };

  const search = async (pageIndex = 0) => {
    setLoading(true);
    try {
      const offset = pageIndex * searchPageSize;
      const res = await fetch("http://localhost:8000/api/v1/memory/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query,
          limit: searchPageSize,
          strategy: "hybrid",
          agent_id: agentFilter.trim() || undefined,
          session_id: sessionFilter.trim() || undefined,
          offset
        }),
      });
      const data = await res.json();
      setResults(data.results || []);
      setSearchPage(pageIndex);
      addLog({ message: "Memory search complete.", type: "success", source: "Memory" });
    } catch (e: any) {
      addLog({ message: `Search failed: ${e.message}`, type: "error", source: "Memory" });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRecent();
    loadStats();
    loadMetrics();
    loadLatestReport();
  }, []);

  const filteredResults = results.filter((r) => {
    if (typeFilter === "all") return true;
    const t = r?.metadata?.memory_type || r?.memory_type;
    return t === typeFilter;
  });
  const tagFilteredResults = filteredResults.filter((r) => {
    if (tagFilter === "all") return true;
    const tags = r?.metadata?.tags || [];
    return Array.isArray(tags) && tags.includes(tagFilter);
  });
  const pagedResults = tagFilteredResults.slice(
    searchPage * searchPageSize,
    (searchPage + 1) * searchPageSize
  );

  return (
    <div className="flex-1 p-8 overflow-y-auto bg-[#0a0a0b]">
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center gap-3 text-cyan-300">
          <Brain className="w-7 h-7" />
          <h1 className="text-3xl font-bold">MEMORY VAULT</h1>
        </div>

        <div className="glass p-5 rounded-[24px] border border-white/10 flex items-center gap-3">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search memory..."
            className="flex-1 bg-transparent border-0 outline-none text-sm text-white placeholder:text-zinc-600"
          />
          <button
            onClick={async () => {
              try {
                const params = new URLSearchParams({ limit: "1000", offset: "0" });
                if (agentFilter.trim()) params.set("agent_id", agentFilter.trim());
                if (sessionFilter.trim()) params.set("session_id", sessionFilter.trim());
                if (tagFilter !== "all") params.set("tag", tagFilter);
                const res = await fetch(`http://localhost:8000/api/v1/memory/export?${params.toString()}`);
                const data = await res.json();
                const blob = new Blob([JSON.stringify(data.results || [], null, 2)], { type: "application/json" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "memory_export.json";
                a.click();
                URL.revokeObjectURL(url);
                addLog({ message: "Memory export downloaded.", type: "success", source: "Memory" });
              } catch (e: any) {
                addLog({ message: `Export failed: ${e.message}`, type: "error", source: "Memory" });
              }
            }}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-emerald-400/10 text-emerald-300 border border-emerald-400/20 hover:bg-emerald-400/20 transition"
          >
            Export JSON
          </button>
          <button
            onClick={async () => {
              try {
                const params = new URLSearchParams({ limit: "1000", offset: "0" });
                if (agentFilter.trim()) params.set("agent_id", agentFilter.trim());
                if (sessionFilter.trim()) params.set("session_id", sessionFilter.trim());
                if (tagFilter !== "all") params.set("tag", tagFilter);
                const res = await fetch(`http://localhost:8000/api/v1/memory/export.csv?${params.toString()}`);
                const text = await res.text();
                const blob = new Blob([text], { type: "text/csv" });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = "memory_export.csv";
                a.click();
                URL.revokeObjectURL(url);
                addLog({ message: "Memory export CSV downloaded.", type: "success", source: "Memory" });
              } catch (e: any) {
                addLog({ message: `Export CSV failed: ${e.message}`, type: "error", source: "Memory" });
              }
            }}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-amber-400/10 text-amber-300 border border-amber-400/20 hover:bg-amber-400/20 transition"
          >
            Export CSV
          </button>
          <button
            onClick={async () => {
              try {
                const res = await fetch("http://localhost:8000/api/v1/memory/backup/run", { method: "POST" });
                const data = await res.json();
                addLog({ message: `Backup saved: ${data.path}`, type: "success", source: "Memory" });
              } catch (e: any) {
                addLog({ message: `Backup failed: ${e.message}`, type: "error", source: "Memory" });
              }
            }}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-purple-400/10 text-purple-300 border border-purple-400/20 hover:bg-purple-400/20 transition"
          >
            Backup Now
          </button>
          <button
            onClick={async () => {
              try {
                const res = await fetch("http://localhost:8000/api/v1/memory/backup/cleanup", { method: "POST" });
                const data = await res.json();
                addLog({ message: `Backups cleaned: ${data.removed}`, type: "success", source: "Memory" });
              } catch (e: any) {
                addLog({ message: `Cleanup failed: ${e.message}`, type: "error", source: "Memory" });
              }
            }}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-zinc-400/10 text-zinc-300 border border-white/10 hover:bg-white/10 transition"
          >
            Cleanup
          </button>
          <button
            onClick={() => search(0)}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-cyan-400/10 text-cyan-300 border border-cyan-400/20 hover:bg-cyan-400/20 transition"
          >
            Search
          </button>
          <button
            onClick={() => loadRecent(0)}
            className="px-4 py-2 rounded-xl text-xs font-bold bg-white/5 text-zinc-300 border border-white/10 hover:bg-white/10 transition"
          >
            Recent
          </button>
        </div>

        <div className="glass p-4 rounded-[20px] border border-white/10 grid grid-cols-2 gap-3">
          <input
            value={agentFilter}
            onChange={(e) => setAgentFilter(e.target.value)}
            placeholder="Filter agent_id..."
            className="bg-transparent border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder:text-zinc-600"
          />
          <input
            value={sessionFilter}
            onChange={(e) => setSessionFilter(e.target.value)}
            placeholder="Filter session_id..."
            className="bg-transparent border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder:text-zinc-600"
          />
          <button
            onClick={() => loadRecent(0)}
            className="px-3 py-2 rounded-xl text-[10px] font-bold bg-cyan-400/10 text-cyan-300 border border-cyan-400/20 hover:bg-cyan-400/20 transition"
          >
            Apply Filters
          </button>
          <button
            onClick={() => { setAgentFilter(""); setSessionFilter(""); loadRecent(0); }}
            className="px-3 py-2 rounded-xl text-[10px] font-bold bg-white/5 text-zinc-400 border border-white/10 hover:bg-white/10 transition"
          >
            Clear Filters
          </button>
        </div>

        <div className="flex items-center gap-3 text-[10px] text-zinc-500 font-bold uppercase tracking-widest">
          <span>Collective Memory</span>
          <button
            onClick={() => { setCollectiveOnly(!collectiveOnly); loadRecent(0); }}
            className={`px-3 py-1.5 rounded-full border transition ${
              collectiveOnly ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/30" : "bg-white/5 text-zinc-500 border-white/10"
            }`}
          >
            {collectiveOnly ? "ON" : "OFF"}
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {["dashboard", "shad", "codex", "gemini", "claude"].map((a) => (
            <button
              key={a}
              onClick={() => { setAgentFilter(a); loadRecent(0); }}
              className="px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider border bg-white/5 text-zinc-500 border-white/10 hover:text-white"
            >
              {a}
            </button>
          ))}
        </div>

        <div className="flex flex-wrap gap-2">
          {["all", "chat", "dashboard", "task", "repo", "plan"].map((t) => (
            <button
              key={t}
              onClick={() => setTagFilter(t)}
              className={`px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider border transition ${
                tagFilter === t
                  ? "bg-emerald-400/20 text-emerald-300 border-emerald-400/30"
                  : "bg-white/5 text-zinc-500 border-white/10 hover:text-white"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2 text-[10px] text-zinc-500 font-bold uppercase tracking-widest">
          <button
            onClick={() => loadRecent(Math.max(0, page - 1))}
            className="px-3 py-1.5 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-400"
          >
            Prev
          </button>
          <span>Page {page + 1}</span>
          <button
            onClick={() => loadRecent(page + 1)}
            className="px-3 py-1.5 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-400"
          >
            Next
          </button>
        </div>

        <div className="flex flex-wrap gap-2">
          {["all", "general", "preference", "task", "conversation", "execution_feedback", "command"].map((t) => (
            <button
              key={t}
              onClick={() => setTypeFilter(t)}
              className={`px-3 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-wider border transition ${
                typeFilter === t
                  ? "bg-cyan-400/20 text-cyan-300 border-cyan-400/30"
                  : "bg-white/5 text-zinc-500 border-white/10 hover:text-white"
              }`}
            >
              {t}
            </button>
          ))}
        </div>

        {stats && (
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
              <div className="text-[10px] uppercase text-zinc-500 font-bold">Vector Count</div>
              <div className="text-lg font-bold">{stats.count}</div>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
              <div className="text-[10px] uppercase text-zinc-500 font-bold">DB Path</div>
              <div className="text-xs text-zinc-300 break-all">{stats.db_path}</div>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
              <div className="text-[10px] uppercase text-zinc-500 font-bold">Initialized</div>
              <div className="text-lg font-bold">{stats.initialized ? "YES" : "NO"}</div>
            </div>
          </div>
        )}

        {metrics && (
          <div className="grid grid-cols-3 gap-4">
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
              <div className="text-[10px] uppercase text-zinc-500 font-bold mb-2">By Agent</div>
              <div className="text-xs text-zinc-300 space-y-1">
                {Object.entries(metrics.by_agent).map(([k,v]) => (
                  <div key={k} className="flex items-center justify-between"><span>{k}</span><span>{v}</span></div>
                ))}
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
              <div className="text-[10px] uppercase text-zinc-500 font-bold mb-2">By Type</div>
              <div className="text-xs text-zinc-300 space-y-1">
                {Object.entries(metrics.by_type).map(([k,v]) => (
                  <div key={k} className="flex items-center justify-between"><span>{k}</span><span>{v}</span></div>
                ))}
              </div>
            </div>
            <div className="p-4 rounded-2xl bg-white/5 border border-white/10">
              <div className="text-[10px] uppercase text-zinc-500 font-bold mb-2">By Tag</div>
              <div className="text-xs text-zinc-300 space-y-1">
                {Object.entries(metrics.by_tag).map(([k,v]) => (
                  <div key={k} className="flex items-center justify-between"><span>{k}</span><span>{v}</span></div>
                ))}
              </div>
            </div>
          </div>
        )}

        {latestReport && (
          <div className="glass p-5 rounded-[24px] border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <div className="text-[10px] uppercase text-zinc-500 font-bold">Latest Report</div>
              <button
                onClick={loadLatestReport}
                className="px-3 py-1.5 rounded-full text-[10px] font-bold bg-white/5 text-zinc-400 border border-white/10 hover:bg-white/10 transition"
              >
                Refresh
              </button>
            </div>
            <div className="text-xs text-zinc-400 mb-2">{latestReport.file}</div>
            <pre className="text-[10px] text-zinc-300 whitespace-pre-wrap max-h-64 overflow-y-auto custom-scrollbar">
{latestReport.content}
            </pre>
          </div>
        )}

        <div className="space-y-4">
          {loading && (
            <div className="flex items-center gap-2 text-zinc-400"><Loader2 className="animate-spin" /> Loading...</div>
          )}
          {pagedResults.map((r, i) => (
            <div key={i} className="p-5 rounded-2xl bg-white/5 border border-white/10">
              <div className="text-[10px] uppercase text-cyan-300 font-bold mb-2">
                {r.metadata?.memory_type || r.memory_type || "memory"}
              </div>
              <div className="flex items-center gap-2 mb-2 text-[10px] text-zinc-500 font-mono">
                {r.metadata?.agent_id && (
                  <span className={`px-2 py-0.5 rounded-full border ${agentBadgeClass(r.metadata.agent_id)}`}>
                    agent:{r.metadata.agent_id}
                  </span>
                )}
                {r.metadata?.session_id && <span>[session:{r.metadata.session_id}]</span>}
              </div>
              <div className="text-sm text-zinc-300 leading-relaxed">{r.content}</div>
              {r.metadata && (
                <div className="text-[10px] text-zinc-500 mt-3">
                  {JSON.stringify(r.metadata)}
                </div>
              )}
              {Array.isArray(r.metadata?.tags) && r.metadata.tags.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {r.metadata.tags.map((t: string) => (
                    <span key={t} className="px-2 py-0.5 rounded-full text-[10px] uppercase tracking-wider bg-white/5 border border-white/10 text-zinc-400">
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="flex items-center gap-2 text-[10px] text-zinc-500 font-bold uppercase tracking-widest">
          <button
            onClick={() => search(Math.max(0, searchPage - 1))}
            className="px-3 py-1.5 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-400"
          >
            Prev
          </button>
          <span>Results Page {searchPage + 1}</span>
          <button
            onClick={() => search(searchPage + 1)}
            className="px-3 py-1.5 rounded-full border border-white/10 bg-white/5 hover:bg-white/10 text-zinc-400"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};


const TaskStatusBar = () => {
  const [tasks, setTasks] = React.useState<any>({});

  React.useEffect(() => {
    const fetchTasks = () => {
      fetch("http://localhost:8000/tasks/status")
        .then(res => res.json())
        .then(data => setTasks(data))
        .catch(() => {});
    };
    fetchTasks();
    const interval = setInterval(fetchTasks, 3000);
    return () => clearInterval(interval);
  }, []);

  const taskList = Object.entries(tasks);
  if (taskList.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 items-end">
      {taskList.map(([name, data]: [string, any]) => (
        <div key={name} className="glass px-4 py-2 rounded-2xl border border-white/10 shadow-2xl flex items-center gap-3 animate-fade-in">
          <div className="w-2 h-2 rounded-full bg-orange-500 animate-pulse shadow-[0_0_8px_rgba(249,115,22,0.6)]" />
          <div className="flex flex-col">
            <div className="text-[10px] font-bold text-zinc-500 uppercase tracking-widest leading-none mb-1">{name}</div>
            <div className="text-xs text-zinc-200 font-medium">{data.status}</div>
          </div>
          <div className="text-[9px] text-zinc-600 ml-2">{data.last_update}</div>
        </div>
      ))}
    </div>
  );
};


const VoiceController = ({ onTranscribe }: { onTranscribe: (text: string) => void }) => {
  const [isRecording, setIsRecording] = React.useState(false);
  const mediaRecorder = React.useRef<MediaRecorder | null>(null);
  const audioChunks = React.useRef<Blob[]>([]);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder.current = new MediaRecorder(stream);
    audioChunks.current = [];

    mediaRecorder.current.ondataavailable = (event) => {
      audioChunks.current.push(event.data);
    };

    mediaRecorder.current.onstop = async () => {
      const audioBlob = new Blob(audioChunks.current, { type: "audio/wav" });
      const formData = new FormData();
      formData.append("file", audioBlob, "audio.wav");

      try {
        const res = await fetch("http://localhost:8000/voice/transcribe", {
          method: "POST",
          body: formData,
        });
        const data = await res.json();
        if (data.text) onTranscribe(data.text);
      } catch (err) {
        console.error("Transcription failed", err);
      }
    };

    mediaRecorder.current.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorder.current?.stop();
    setIsRecording(false);
  };

  return (
    <button
      onMouseDown={startRecording}
      onMouseUp={stopRecording}
      className={`p-4 rounded-full transition-all shadow-2xl ${isRecording ? "bg-red-500 scale-110 animate-pulse" : "bg-orange-500 hover:bg-orange-600"}`}
      title="Hold to speak to Wataha"
    >
      <Mic className="w-6 h-6 text-white" />
    </button>
  );
};


const AnalyticsView = () => {
  const [stats, setStats] = React.useState<any>(null);
  React.useEffect(() => {
    fetch("http://localhost:8000/stats").then(r => r.json()).then(setStats);
  }, []);

  if (!stats) return <div className="p-8 text-zinc-500">Calculating metrics...</div>;

  return (
    <div className="flex-1 p-8 overflow-y-auto custom-scrollbar">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="glass p-6 rounded-3xl border border-white/5">
          <div className="text-zinc-500 text-xs font-bold uppercase mb-1">Total Memories</div>
          <div className="text-4xl font-bold text-white">{stats.memories}</div>
        </div>
        <div className="glass p-6 rounded-3xl border border-white/5">
          <div className="text-zinc-500 text-xs font-bold uppercase mb-1">Avg Resonance</div>
          <div className="text-4xl font-bold text-orange-500">{stats.resonance_avg}%</div>
        </div>
        <div className="glass p-6 rounded-3xl border border-white/5">
          <div className="text-zinc-500 text-xs font-bold uppercase mb-1">System Health</div>
          <div className="text-4xl font-bold text-emerald-500">Optimal</div>
        </div>
        <div className="glass p-6 rounded-3xl border border-white/5">
          <div className="text-zinc-500 text-xs font-bold uppercase mb-1">Active Agents</div>
          <div className="text-4xl font-bold text-indigo-500">5</div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="glass p-8 rounded-[32px] border border-white/5">
          <h3 className="text-xl font-bold mb-6">Memory Growth</h3>
          <div className="flex items-end gap-2 h-48">
            {stats.daily_growth.map((d: any) => (
              <div key={d.date} className="flex-1 flex flex-col items-center gap-2 group">
                <div className="w-full bg-orange-500/20 rounded-t-lg transition-all group-hover:bg-orange-500/40" style={{ height: `${(d.value / 200) * 100}%` }}></div>
                <div className="text-[10px] text-zinc-600 -rotate-45 mt-2">{d.date.split('-').slice(1).join('/')}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="glass p-8 rounded-[32px] border border-white/5">
          <h3 className="text-xl font-bold mb-6">Categories</h3>
          <div className="space-y-4">
            {Object.entries(stats.categories).map(([name, val]: [string, any]) => (
              <div key={name} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-zinc-400">{name}</span>
                  <span className="text-white font-bold">{val}%</span>
                </div>
                <div className="w-full bg-white/5 h-1.5 rounded-full overflow-hidden">
                  <div className="bg-indigo-500 h-full" style={{ width: `${val}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const ToolsView = () => {
  const [url, setUrl] = React.useState("");
  const [result, setResult] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(false);

  const handleRead = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/tools/read-link", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ code: url })
      });
      const data = await res.json();
      setResult(data);
    } catch (e) {
      alert("Error reading link");
    }
    setLoading(false);
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="max-w-2xl mx-auto space-y-8">
        <div className="glass p-8 rounded-[32px] border border-white/5 space-y-4">
          <h2 className="text-2xl font-bold flex items-center gap-3">
            <Zap className="text-orange-500" /> Nexus Link Reader
          </h2>
          <p className="text-zinc-500 text-sm">Drop a YouTube or TikTok link to extract knowledge directly into the Grotto.</p>
          <div className="flex gap-2">
            <input 
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://www.youtube.com/watch?v=..."
              className="flex-1 bg-zinc-900/50 border border-white/10 rounded-2xl px-4 py-3 text-sm focus:outline-none focus:border-orange-500/50 transition-colors"
            />
            <button 
              onClick={handleRead}
              disabled={loading}
              className="bg-orange-500 hover:bg-orange-600 text-white px-6 py-3 rounded-2xl font-bold transition-all flex items-center gap-2"
            >
              {loading ? <Loader2 className="animate-spin" /> : <Search className="w-4 h-4" />} Analyze
            </button>
          </div>
        </div>

        {result && (
          <div className="glass p-8 rounded-[32px] border border-white/10 animate-fade-in space-y-6">
            <div className="flex gap-6">
              {result.thumbnail && <img src={result.thumbnail} className="w-32 h-32 rounded-2xl object-cover shadow-2xl border border-white/10" />}
              <div className="space-y-2">
                <h3 className="text-xl font-bold text-white">{result.title}</h3>
                <div className="text-orange-500 font-bold text-sm">{result.author}</div>
                <div className="flex gap-4 text-zinc-500 text-xs">
                  <span>Duration: {Math.floor(result.duration / 60)}m {result.duration % 60}s</span>
                  <span>Views: {result.view_count?.toLocaleString()}</span>
                </div>
              </div>
            </div>
            <div className="p-4 bg-white/5 rounded-2xl text-sm text-zinc-400 italic">
              {result.description}
            </div>
            <div className="text-[10px] text-zinc-600 uppercase font-bold">Status: Knowledge Ingested to ChromaDB</div>
          </div>
        )}
      </div>
    </div>
  );
};

const DocChatView = () => {
  const [query, setQuery] = React.useState("");
  const [response, setResponse] = React.useState<any>(null);
  const [loading, setLoading] = React.useState(false);

  const handleChat = async () => {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/docs/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, n_results: 5 })
      });
      const data = await res.json();
      setResponse(data);
    } catch (e) { alert("Chronicle silent. Check API."); }
    setLoading(false);
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <div className="max-w-4xl mx-auto space-y-8">
        <div className="glass p-8 rounded-[32px] border border-white/5 space-y-4">
          <h2 className="text-2xl font-bold flex items-center gap-3 text-indigo-400">
            <FileJson className="w-8 h-8" /> CHRONICLE CHAT
          </h2>
          <p className="text-zinc-500 text-sm">Ask questions based only on your Grotto's z zindeksowanymi dokumentami.</p>
          <div className="flex gap-2">
            <input 
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Ask the ancestors..."
              className="flex-1 bg-zinc-900/50 border border-white/10 rounded-2xl px-4 py-3 text-sm focus:outline-none focus:border-indigo-500/50 transition-colors"
            />
            <button 
              onClick={handleChat}
              disabled={loading}
              className="bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-3 rounded-2xl font-bold transition-all flex items-center gap-2"
            >
              {loading ? <Loader2 className="animate-spin" /> : <Send className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {response && (
          <div className="glass p-8 rounded-[32px] border border-white/10 animate-fade-in space-y-6">
            <div className="flex justify-between items-center">
              <div className="text-[10px] font-bold text-indigo-400 uppercase tracking-widest">Wataha Response</div>
              <div className="text-[10px] font-bold text-zinc-600">RESONANCE: {response.resonance}%</div>
            </div>
            <div className="text-lg text-zinc-200 leading-relaxed italic">
              {response.answer}
            </div>
            <div className="pt-4 border-t border-white/5">
              <div className="text-[10px] font-bold text-zinc-500 mb-2">SOURCES:</div>
              <div className="flex flex-wrap gap-2">
                {response.sources.map((s: any, i: number) => (
                  <span key={i} className="px-2 py-1 bg-white/5 rounded-md text-[9px] text-zinc-400">
                    {s.title} ({s.source})
                  </span>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
const SocialHub = ({ addLog }: { addLog: any }) => {
  const [ytQuery, setYtQuery] = useState("");
  const [ytResults, setYtResults] = useState<any[]>([]);
  const [tiktokTrends, setTiktokTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const searchYT = async () => {
    setLoading(true);
    try {
      const res = await fetch(\/api/v1/social/youtube/search?q=\\);
      const data = await res.json();
      setYtResults(data.results || []);
      addLog({ message: "YouTube search completed", type: "success", source: "SocialHub" });
    } catch (e) {
      addLog({ message: "YouTube search failed", type: "error", source: "SocialHub" });
    }
    setLoading(false);
  };

  const fetchTikTok = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/social/tiktok/trends');
      const data = await res.json();
      setTiktokTrends(data.trends || []);
      addLog({ message: "TikTok trends updated", type: "success", source: "SocialHub" });
    } catch (e) {
      addLog({ message: "TikTok trends failed", type: "error", source: "SocialHub" });
    }
    setLoading(false);
  };

  useEffect(() => { fetchTikTok(); }, []);

  return (
    <div className="h-full flex flex-col gap-6 animate-fade-in">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 h-full">
        <div className="glass rounded-[32px] p-6 border border-white/5 flex flex-col">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-2xl bg-red-500/20 flex items-center justify-center text-red-500"><Film className="w-5 h-5" /></div>
            <div><h3 className="font-bold text-white">YouTube Forge</h3><p className="text-[10px] text-zinc-500 uppercase tracking-widest">Search & Analyze</p></div>
          </div>
          <div className="flex gap-2 mb-6">
            <input value={ytQuery} onChange={(e) => setYtQuery(e.target.value)} placeholder="Search videos..." className="flex-1 bg-white/5 border border-white/10 rounded-xl px-4 py-2 text-sm outline-none focus:border-red-500/50 transition-colors" />
            <button onClick={searchYT} className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-xl transition-all shadow-lg shadow-red-500/20"><Search className="w-4 h-4" /></button>
          </div>
          <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
            {ytResults.map((v, i) => (
              <div key={i} className="glass-light p-3 rounded-2xl border border-white/5 flex items-center gap-4 group hover:bg-white/5 transition-all">
                <div className="w-16 h-10 bg-zinc-800 rounded-lg flex items-center justify-center"><Play className="w-4 h-4 text-zinc-600 group-hover:text-white" /></div>
                <div className="flex-1 min-w-0">
                   <p className="text-xs font-bold text-white truncate">{v.title}</p>
                   <p className="text-[10px] text-zinc-500">{v.url}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div className="glass rounded-[32px] p-6 border border-white/5 flex flex-col">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-2xl bg-cyan-500/20 flex items-center justify-center text-cyan-500"><Hash className="w-5 h-5" /></div>
            <div><h3 className="font-bold text-white">TikTok Trends</h3><p className="text-[10px] text-zinc-500 uppercase tracking-widest">Global Pulse</p></div>
            <button onClick={fetchTikTok} className="ml-auto p-2 hover:bg-white/5 rounded-full text-zinc-500"><RefreshCw className={w-4 h-4 \} /></button>
          </div>
          <div className="flex-1 overflow-y-auto space-y-3 pr-2 custom-scrollbar">
             {tiktokTrends.map((t, i) => (
               <div key={i} className="glass-light p-4 rounded-2xl border border-white/5 flex items-center justify-between group hover:border-cyan-500/30 transition-all">
                  <div className="flex items-center gap-3">
                     <span className="text-zinc-500 font-bold text-xs">#\</span>
                     <span className="text-sm font-bold text-white group-hover:text-cyan-400 transition-colors">#{t.hashtag}</span>
                  </div>
                  <span className="text-[10px] font-bold text-zinc-500 bg-white/5 px-2 py-1 rounded-lg">{t.views} views</span>
               </div>
             ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const App = () => {
  const [view, setView] = useState<ViewMode>("chat");
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [showTerminal, setShowTerminal] = useState(false);

  const addLog = (log: Omit<LogEntry, 'id' | 'timestamp'>) => {
      const newLog = { ...log, id: Date.now().toString() + Math.random(), timestamp: Date.now() };
      setLogs(prev => [newLog, ...prev]);
      if (log.type === 'error') setShowTerminal(true);
  };

  const NavItem = ({ m, icon: Icon, label }: { m: ViewMode, icon: any, label: string }) => (
    <button onClick={() => setView(m)} className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 relative group mb-1 ${view === m ? 'bg-zinc-800 text-white shadow-lg' : 'text-zinc-500 hover:bg-zinc-800/50 hover:text-zinc-200'}`}>
      <Icon className={`w-4 h-4 ${view === m ? 'text-indigo-400' : ''}`} />
      <span className="font-medium text-sm">{label}</span>
      {view === m && <div className="absolute right-2 w-1.5 h-1.5 bg-indigo-500 rounded-full shadow-[0_0_8px_rgba(99,102,241,0.6)]" />}
    </button>
  );

  return (
    <style>
  @keyframes resonance-wave {
    0% { transform: scale(1); opacity: 0.4; }
    50% { transform: scale(1.05); opacity: 0.8; }
    100% { transform: scale(1); opacity: 0.4; }
  }
  .resonance-active {
    animation: resonance-wave 2s infinite ease-in-out;
    box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
  }
</style>
<div className="flex h-screen w-screen overflow-hidden bg-[#09090b] text-zinc-100 selection:bg-indigo-500/30">
      <div className="fixed inset-0 z-0">
          <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-indigo-500/5 rounded-full blur-[120px] animate-pulse-slow" />
          <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-blue-600/5 rounded-full blur-[120px] animate-pulse-slow" style={{ animationDelay: '2s' }} />
      </div>
      <aside className="w-64 glass flex flex-col p-4 z-10 m-4 rounded-[24px] shadow-2xl relative border border-white/5">
        <div className="flex items-center gap-3 mb-8 px-2 mt-2">
          <div className="w-8 h-8 bg-white rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(255,255,255,0.1)] resonance-active"><Zap className="w-5 h-5 text-black fill-black" /></div>
          <div><h1 className="font-bold text-lg tracking-tight leading-none text-white text-sm">STUDIO</h1><span className="text-[9px] font-bold text-zinc-500 uppercase tracking-widest">Pro Edition</span></div>
        </div>
        <nav className="space-y-1 flex-1 overflow-y-auto custom-scrollbar pr-2">
          <div className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest px-4 mb-2 mt-2">Create</div>
          <NavItem m="chat" icon={Terminal} label="OMEGA Terminal" />
          <NavItem m="image" icon={ImageIcon} label="Visual Lab" />
          <NavItem m="video" icon={Video} label="Video Forge" />
          <NavItem m="live" icon={Mic} label="Live Comm" />
          <div className="text-[10px] font-bold text-zinc-600 uppercase tracking-widest px-4 mb-2 mt-6">Develop</div>
          <NavItem m="repo" icon={FolderTree} label="Repo Architect" />
          <NavItem m="models" icon={Database} label="Model Forge" />
          <NavItem m="memory" icon={Brain} label="Memory Vault" />
          <NavItem m="tasks" icon={CheckSquare} label="Task Manager" />
          <NavItem m="social" icon={Globe} label="Social Hub" />
          <NavItem m="grota" icon={Mountain} label="Grota Dashboard" />
          <NavItem m="evolution" | "docs_chat" icon={Brain} label="Evolution Tree" />
        </nav>
      </aside>
      <main className="flex-1 flex flex-col p-6 overflow-hidden relative z-10">
        <header className="flex items-center justify-between mb-8"><VoiceController onTranscribe={(text) => speakText("Usłyszałem: " + text)} />
           <div className="animate-fade-in"><h2 className="text-3xl font-bold tracking-tight text-white capitalize">{view}</h2></div>
           <div className="flex items-center gap-3">
              <button onClick={() => setShowTerminal(!showTerminal)} className={`glass w-10 h-10 rounded-xl flex items-center justify-center transition-colors ${showTerminal ? 'bg-zinc-800 text-white' : 'text-zinc-400 hover:text-white hover:bg-zinc-800'}`}>
                 <Terminal className="w-4 h-4" />
              </button>
              <div className="glass px-3 py-2 rounded-xl text-xs font-bold border border-white/5 flex items-center gap-2 text-zinc-300"><div className="w-1.5 h-1.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" /> Gemini 3 Pro</div>
           </div>
        </header>
        <section className="flex-1 overflow-hidden relative">
          {view === "repo" && <RepoArchitect addLog={addLog} />}
          {view === "models" && <ModelForge addLog={addLog} />}
          {view === "memory" && <MemoryView addLog={addLog} />}
          {view === "tasks" && <TaskView />}
          {view === "chat" && <ChatView addLog={addLog} />}
          {view === "image" && <VisualLab addLog={addLog} />}
          {view === "video" && <div className="h-full glass rounded-[32px] p-8 flex flex-col items-center justify-center border border-white/5"><Video className="w-16 h-16 mb-4 opacity-20" /><h3 className="text-xl font-bold text-zinc-400">Wolf Vision (Veo)</h3></div>}
          {view === "live" && <div className="h-full glass rounded-[32px] p-8 flex flex-col items-center justify-center border border-white/5"><Mic className="w-16 h-16 mb-4 opacity-20" /><h3 className="text-xl font-bold text-zinc-400">Native Audio</h3></div>}
          {view === "grota" && <GrotaView addLog={addLog} />}
          {view === "social" && <SocialHub addLog={addLog} />}

          {view === "analytics" && <AnalyticsView />}
          {view === "tools" && <ToolsView />}
          {view === "evolution" | "docs_chat" && <EvolutionView />}
          <TerminalLog logs={logs} isOpen={showTerminal} onClose={() => setShowTerminal(false)} onClear={() => setLogs([])} />
        </section>
        <TaskStatusBar />
      </main>
    </div>
  );
};

const init = () => {
  const container = document.getElementById("root");
  if (container) createRoot(container).render(<App />);
};
init();





