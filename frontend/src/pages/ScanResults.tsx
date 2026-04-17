import { useState, useEffect, useRef } from 'react';
import { useParams, Link, useLocation } from 'react-router-dom';

import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Brain, ArrowLeft, AlertTriangle, CheckCircle, Activity, Bot, Send, Loader2 } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';

interface AnalysisResult {
  prediction: string;
  confidence: number;
  gradcam_base64?: string;
  base_image_base64?: string;
  findings: string[];
  recommendations: string[];
  risk_level: 'low' | 'moderate' | 'high';
}

const ScanResults = () => {
  const { id } = useParams<{ id: string }>();
  const { user } = useAuth();
  const { toast } = useToast();
  const [scan, setScan] = useState<any>(null);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [chatMessages, setChatMessages] = useState<{ role: string; content: string }[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const location = useLocation();

  useEffect(() => {
    fetchScan();
  }, [id, location.state]);

  const fetchScan = async () => {
    if (!id) return;
    try {
      const token = localStorage.getItem('medai_token');
      const res = await fetch(`/api/scans/${id}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error('Scan not found');
      
      const { scan: scanData, result: resultData } = await res.json();
      setScan(scanData);

      if (scanData?.status === 'completed') {
        if (resultData) {
          setResult(resultData.result_data as AnalysisResult);
        }
        setAnalyzing(false);
      } else if (scanData?.status === 'pending') {
        setAnalyzing(true);
        setTimeout(fetchScan, 3000);
      }
    } catch {
      // ignore
    }
    setLoading(false);
  };

  // Draw heatmap overlay on canvas
  useEffect(() => {
    if (!canvasRef.current || !result) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Fixed canvas size for layout consistency
    canvas.width = 800;
    canvas.height = 400;
    
    // Draw background
    ctx.fillStyle = '#0f172a'; // slate-900 
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // Choose which encoded image to draw based on toggle
    const b64 = showHeatmap ? result.gradcam_base64 : result.base_image_base64;

    if (b64) {
      const displayImg = new Image();
      displayImg.src = `data:image/png;base64,${b64}`;
      displayImg.onload = () => {
         const aspect = displayImg.width / displayImg.height;
         let drawWidth = canvas.width * 0.9;
         let drawHeight = drawWidth / aspect;
         
         // Ensure it doesn't overflow height
         if (drawHeight > canvas.height * 0.9) {
            drawHeight = canvas.height * 0.9;
            drawWidth = drawHeight * aspect;
         }
         
         ctx.drawImage(displayImg, (canvas.width - drawWidth)/2, (canvas.height - drawHeight)/2, drawWidth, drawHeight);
      };
    } else {
      // Fallback
      ctx.fillStyle = '#94a3b8';
      ctx.font = '16px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('Processing image visualization...', canvas.width/2, canvas.height/2);
    }

  }, [scan, showHeatmap, result]);

  const handleChatSend = async () => {
    if (!chatInput.trim()) return;
    const msg = chatInput;
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: msg }]);
    setChatLoading(true);

    try {
      const res = await fetch('/api/ai-chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: msg,
          context: result ? `Analysis results: ${JSON.stringify(result)}` : 'No analysis results available yet.',
        }),
      });
      if (!res.ok) throw new Error('Backend error');
      const data = await res.json();
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.reply }]);
    } catch {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error. Please try again.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  const riskColor = result?.risk_level === 'high' ? 'destructive' : result?.risk_level === 'moderate' ? 'secondary' : 'default';

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 glass-card border-b">
        <div className="container mx-auto px-4 h-16 flex items-center gap-4">
          <Link to="/dashboard"><Button variant="ghost" size="icon"><ArrowLeft className="w-5 h-5" /></Button></Link>
          <div className="flex items-center gap-2">
            <img src="/med ai.png" className="w-8 h-8 object-contain" alt="Med AI Logo" />
            <span className="font-display font-bold">Analysis Results</span>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {analyzing ? (
          <div className="text-center py-20">
            <div className="w-20 h-20 rounded-full gradient-medical flex items-center justify-center mx-auto mb-6 animate-pulse-glow">
              <Brain className="w-10 h-10 text-primary-foreground animate-pulse" />
            </div>
            <h2 className="font-display text-2xl font-bold mb-2">Analyzing Your Scan</h2>
            <p className="text-muted-foreground">Our AI model is processing your CT scan...</p>
          </div>
        ) : result ? (
          <Tabs defaultValue="results" className="space-y-6">
            <TabsList className="grid w-full grid-cols-3 max-w-md">
              <TabsTrigger value="results">Results</TabsTrigger>
              <TabsTrigger value="heatmap">Grad-CAM</TabsTrigger>
              <TabsTrigger value="assistant">AI Chat</TabsTrigger>
            </TabsList>

            <TabsContent value="results" className="space-y-6">
              {/* Prediction Card */}
              <Card className="glass-card">
                <CardContent className="pt-6">
                  <div className="flex items-start justify-between mb-6">
                    <div>
                      <h2 className="font-display text-xl font-bold">{result.prediction}</h2>
                      <p className="text-muted-foreground text-sm mt-1">Confidence: {(result.confidence * 100).toFixed(1)}%</p>
                    </div>
                    <Badge variant={riskColor as any} className="text-sm">
                      {result.risk_level === 'high' ? <AlertTriangle className="w-3 h-3 mr-1" /> : <CheckCircle className="w-3 h-3 mr-1" />}
                      {result.risk_level} risk
                    </Badge>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-3 mb-2">
                    <div className="h-3 rounded-full gradient-medical transition-all" style={{ width: `${result.confidence * 100}%` }} />
                  </div>
                </CardContent>
              </Card>

              {/* Findings */}
              <div className="grid md:grid-cols-2 gap-6">
                <Card className="glass-card">
                  <CardHeader><CardTitle className="font-display text-lg flex items-center gap-2"><Activity className="w-5 h-5 text-primary" /> Findings</CardTitle></CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {result.findings.map((f, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <div className="w-1.5 h-1.5 rounded-full bg-primary mt-2 shrink-0" />
                          {f}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
                <Card className="glass-card">
                  <CardHeader><CardTitle className="font-display text-lg flex items-center gap-2"><Brain className="w-5 h-5 text-accent" /> Recommendations</CardTitle></CardHeader>
                  <CardContent>
                    <ul className="space-y-2">
                      {result.recommendations.map((r, i) => (
                        <li key={i} className="flex items-start gap-2 text-sm">
                          <div className="w-1.5 h-1.5 rounded-full bg-accent mt-2 shrink-0" />
                          {r}
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              </div>
            </TabsContent>

            <TabsContent value="heatmap">
              <Card className="glass-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="font-display">Grad-CAM Heatmap Visualization</CardTitle>
                    <Button variant="outline" size="sm" onClick={() => setShowHeatmap(!showHeatmap)}>
                      {showHeatmap ? 'Hide' : 'Show'} Heatmap
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="relative bg-secondary/50 rounded-xl p-4 flex justify-center">
                    <canvas ref={canvasRef} className="max-w-full max-h-[500px] rounded-lg" />
                  </div>
                  <div className="flex items-center gap-4 mt-4 justify-center">
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded" style={{ background: 'rgba(255,0,0,0.6)' }} />
                      <span className="text-xs text-muted-foreground">High attention</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded" style={{ background: 'rgba(255,165,0,0.4)' }} />
                      <span className="text-xs text-muted-foreground">Medium</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-4 h-4 rounded" style={{ background: 'rgba(255,255,0,0.2)' }} />
                      <span className="text-xs text-muted-foreground">Low</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="assistant">
              <Card className="glass-card">
                <CardHeader><CardTitle className="font-display flex items-center gap-2"><Bot className="w-5 h-5 text-primary" /> AI Medical Assistant</CardTitle></CardHeader>
                <CardContent>
                  <div className="h-80 overflow-y-auto space-y-3 mb-4 p-3 bg-secondary/30 rounded-lg">
                    {chatMessages.length === 0 && (
                      <div className="text-center py-8 text-muted-foreground text-sm">
                        <Bot className="w-10 h-10 mx-auto mb-2 opacity-50" />
                        Ask me anything about the analysis results.
                      </div>
                    )}
                    {chatMessages.map((m, i) => (
                      <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[80%] rounded-xl px-4 py-2 text-sm ${m.role === 'user' ? 'gradient-medical text-primary-foreground' : 'bg-card border'}`}>
                          {m.content}
                        </div>
                      </div>
                    ))}
                    {chatLoading && (
                      <div className="flex justify-start">
                        <div className="bg-card border rounded-xl px-4 py-2"><Loader2 className="w-4 h-4 animate-spin" /></div>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2">
                    <Input value={chatInput} onChange={e => setChatInput(e.target.value)} placeholder="Ask about the results..." onKeyDown={e => e.key === 'Enter' && handleChatSend()} />
                    <Button onClick={handleChatSend} disabled={chatLoading} className="gradient-medical text-primary-foreground border-0">
                      <Send className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        ) : (
          <div className="text-center py-20">
            <p className="text-muted-foreground">No analysis results found for this scan.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ScanResults;
