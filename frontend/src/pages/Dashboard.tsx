import { useState, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Brain, Upload, History, Bot, LogOut, BarChart3, User, Settings, Menu, X } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useQuery } from '@tanstack/react-query';

const Dashboard = () => {
  const { user, signOut, userRole } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const { data: scans = [] } = useQuery({
    queryKey: ['scans', user?.id],
    queryFn: async () => {
      const token = localStorage.getItem('medai_token');
      if (!token) return [];
      const res = await fetch('/api/scans/', { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error('Failed to fetch scans');
      const json = await res.json();
      return json.scans || [];
    },
    enabled: !!user,
  });

  const { data: stats } = useQuery({
    queryKey: ['stats', user?.id],
    queryFn: async () => {
      const token = localStorage.getItem('medai_token');
      if (!token) return { totalScans: 0, analyzed: 0 };
      const res = await fetch('/api/scans/stats', { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) return { totalScans: 0, analyzed: 0 };
      const json = await res.json();
      return { totalScans: json.total_scans || 0, analyzed: json.analyzed_scans || 0 };
    },
    enabled: !!user,
  });

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Top Bar */}
      <header className="sticky top-0 z-50 glass-card border-b">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button className="md:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
            <Link to="/dashboard" className="flex items-center gap-2">
              <img src="/med ai.png" className="w-10 h-10 object-contain" alt="Med AI Logo" />
              <span className="font-display font-bold hidden sm:block">Med AI Scan</span>
            </Link>
          </div>
          <div className="flex items-center gap-3">
            {userRole === 'admin' && (
              <Link to="/admin">
                <Button variant="outline" size="sm"><Settings className="w-4 h-4 mr-1" /> Admin</Button>
              </Link>
            )}
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="w-4 h-4 text-primary" />
              </div>
              <span className="text-sm hidden sm:block">{user?.email}</span>
            </div>
            <Button variant="ghost" size="icon" onClick={handleSignOut}><LogOut className="w-4 h-4" /></Button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="font-display text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">Welcome back! Manage your CT scan analyses.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          {[
            { label: 'Total Scans', value: stats?.totalScans ?? 0, icon: BarChart3, color: 'text-primary' },
            { label: 'Analyzed', value: stats?.analyzed ?? 0, icon: Brain, color: 'text-accent' },
            { label: 'Pending', value: (stats?.totalScans ?? 0) - (stats?.analyzed ?? 0), icon: History, color: 'text-muted-foreground' },
            { label: 'AI Sessions', value: 0, icon: Bot, color: 'text-primary' },
          ].map((s, i) => (
            <Card key={i} className="glass-card">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-muted-foreground">{s.label}</p>
                    <p className="text-2xl font-display font-bold mt-1">{s.value}</p>
                  </div>
                  <s.icon className={`w-8 h-8 ${s.color} opacity-60`} />
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-4 mb-8">
          <Link to="/upload" className="block">
            <Card className="glass-card hover:shadow-xl transition-all cursor-pointer group h-full">
              <CardContent className="pt-6 flex flex-col items-center text-center">
                <div className="w-14 h-14 rounded-xl gradient-medical flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Upload className="w-7 h-7 text-primary-foreground" />
                </div>
                <h3 className="font-display font-semibold text-lg">Upload Scan</h3>
                <p className="text-sm text-muted-foreground mt-1">Upload a new CT scan for AI analysis</p>
              </CardContent>
            </Card>
          </Link>
          <Link to="/history" className="block">
            <Card className="glass-card hover:shadow-xl transition-all cursor-pointer group h-full">
              <CardContent className="pt-6 flex flex-col items-center text-center">
                <div className="w-14 h-14 rounded-xl bg-accent/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <History className="w-7 h-7 text-accent" />
                </div>
                <h3 className="font-display font-semibold text-lg">Scan History</h3>
                <p className="text-sm text-muted-foreground mt-1">View past analyses and results</p>
              </CardContent>
            </Card>
          </Link>
          <Link to="/ai-assistant" className="block">
            <Card className="glass-card hover:shadow-xl transition-all cursor-pointer group h-full">
              <CardContent className="pt-6 flex flex-col items-center text-center">
                <div className="w-14 h-14 rounded-xl bg-primary/10 flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <Bot className="w-7 h-7 text-primary" />
                </div>
                <h3 className="font-display font-semibold text-lg">AI Assistant</h3>
                <p className="text-sm text-muted-foreground mt-1">Chat with our medical AI assistant</p>
              </CardContent>
            </Card>
          </Link>
        </div>

        {/* Recent Scans */}
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="font-display">Recent Scans</CardTitle>
          </CardHeader>
          <CardContent>
            {scans.length === 0 ? (
              <div className="text-center py-12">
                <Upload className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">No scans yet. Upload your first CT scan to get started.</p>
                <Link to="/upload"><Button className="mt-4 gradient-medical text-primary-foreground border-0">Upload Scan</Button></Link>
              </div>
            ) : (
              <div className="space-y-3">
                {scans.map((scan: any) => (
                  <div key={scan.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Brain className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{scan.file_name}</p>
                        <p className="text-xs text-muted-foreground">{new Date(scan.created_at).toLocaleDateString()}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`text-xs px-2 py-1 rounded-full ${scan.status === 'completed' ? 'bg-accent/10 text-accent' : 'bg-muted text-muted-foreground'}`}>
                        {scan.status}
                      </span>
                      {scan.status === 'completed' && (
                        <Link to={`/results/${scan.id}`}>
                          <Button size="sm" variant="outline">View</Button>
                        </Link>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;
