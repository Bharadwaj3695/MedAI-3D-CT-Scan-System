import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Brain, ArrowLeft, Bot, Send, Loader2 } from 'lucide-react';

const AIAssistant = () => {
  const [messages, setMessages] = useState<{ role: string; content: string }[]>([
    { role: 'assistant', content: "Hello! I'm your medical AI assistant. I can help you understand CT scan results, explain medical terminology, and answer questions about lung diseases. How can I help you today?" },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!input.trim()) return;
    const msg = input;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg }]);
    setLoading(true);
    try {
      const res = await fetch('/api/ai-chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: msg,
          context: 'General medical AI assistant for lung disease queries.'
        })
      });
      if (!res.ok) throw new Error('Backend error');
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, something went wrong. Please try again.' }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <header className="sticky top-0 z-50 glass-card border-b">
        <div className="container mx-auto px-4 h-16 flex items-center gap-4">
          <Link to="/dashboard"><Button variant="ghost" size="icon"><ArrowLeft className="w-5 h-5" /></Button></Link>
          <div className="flex items-center gap-2">
            <img src="/med ai.png" className="w-8 h-8 object-contain" alt="Med AI Logo" />
            <span className="font-display font-bold">AI Medical Assistant</span>
          </div>
        </div>
      </header>

      <div className="flex-1 container mx-auto px-4 py-6 max-w-2xl flex flex-col">
        <Card className="glass-card flex-1 flex flex-col">
          <CardContent className="flex-1 flex flex-col pt-6">
            <div className="flex-1 overflow-y-auto space-y-3 mb-4 p-3 bg-secondary/30 rounded-lg min-h-[400px]">
              {messages.map((m, i) => (
                <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[85%] rounded-xl px-4 py-3 text-sm leading-relaxed ${m.role === 'user' ? 'gradient-medical text-primary-foreground' : 'bg-card border'}`}>
                    {m.role === 'assistant' && <Bot className="w-4 h-4 mb-1 text-primary inline mr-1" />}
                    {m.content}
                  </div>
                </div>
              ))}
              {loading && (
                <div className="flex justify-start">
                  <div className="bg-card border rounded-xl px-4 py-3">
                    <Loader2 className="w-4 h-4 animate-spin text-primary" />
                  </div>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <Input value={input} onChange={e => setInput(e.target.value)} placeholder="Ask about lung diseases, scan results..." onKeyDown={e => e.key === 'Enter' && handleSend()} className="h-11" />
              <Button onClick={handleSend} disabled={loading} className="h-11 gradient-medical text-primary-foreground border-0">
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AIAssistant;
