import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  Brain, Upload, History, LogOut, BarChart3, User, Settings, 
  Menu, X, FileText, Activity, Database, CheckCircle2, Clock, 
  ShieldCheck, Eye, Download, ExternalLink 
} from 'lucide-react';
import { useToast } from '@/hooks/use-toast';
import { useQuery } from '@tanstack/react-query';

import { StatsCard } from '@/components/ui/StatsCard';
import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';

const Dashboard = () => {
  const { user, signOut, userRole } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showReportsModal, setShowReportsModal] = useState(false);
  const [systemStatus, setSystemStatus] = useState({
    api: 'checking',
    database: 'checking',
    model: 'checking'
  });

  const { data: scans = [], isLoading: scansLoading } = useQuery({
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

  const { data: scanHistory = [] } = useQuery({
    queryKey: ['scans-history', user?.id],
    queryFn: async () => {
      const token = localStorage.getItem('medai_token');
      if (!token) return [];
      const res = await fetch('/api/scans/history?limit=50', { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) return [];
      return await res.json();
    },
    enabled: !!user,
  });

  const { data: reports = [], isLoading: reportsLoading } = useQuery({
    queryKey: ['reports', user?.id],
    queryFn: async () => {
      const token = localStorage.getItem('medai_token');
      if (!token) return [];
      const res = await fetch('/api/reports/history?limit=100', { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) return [];
      return await res.json();
    },
    enabled: !!user,
  });

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const token = localStorage.getItem('medai_token');
        if (!token) return;
        const res = await fetch('/api/scans/stats', { headers: { Authorization: `Bearer ${token}` } });
        if (res.ok) {
          setSystemStatus({
            api: 'online',
            database: 'online',
            model: 'online'
          });
        } else {
          setSystemStatus({
            api: 'degraded',
            database: 'degraded',
            model: 'online'
          });
        }
      } catch {
        setSystemStatus({
          api: 'offline',
          database: 'offline',
          model: 'offline'
        });
      }
    };
    if (user) {
      checkStatus();
    }
  }, [user, scans]);

  const handleSignOut = async () => {
    await signOut();
    navigate('/');
  };

  const totalScans = scans.length;
  const completedScans = scans.filter((s: any) => s.status === 'completed').length;
  const pendingScans = scans.filter((s: any) => s.status === 'pending' || s.status === 'processing').length;
  const totalReports = reports.length;

  const recentScans = [...scans]
    .sort(
      (a: any, b: any) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    )
    .slice(0, 5);

  return (
    <div className="min-h-screen bg-background pb-12">
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
        <div className="mb-8 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="font-display text-3xl font-bold tracking-tight">Medical Dashboard</h1>
            <p className="text-muted-foreground mt-1">Welcome back! Monitor system status, view recent scans, and manage medical reports.</p>
          </div>
          <Link to="/upload">
            <Button className="gradient-medical text-primary-foreground border-0 shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all">
              <Upload className="w-4 h-4 mr-2" /> Upload New Scan
            </Button>
          </Link>
        </div>

        {scansLoading ? (
          <LoadingSkeleton variant="dashboard" />
        ) : (
          <>
            {/* Stats Grid */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <StatsCard
                title="Total Scans"
                value={totalScans}
                icon={BarChart3}
                iconClassName="text-primary"
                iconBgClassName="bg-primary/5"
              />
              <StatsCard
                title="Completed Scans"
                value={completedScans}
                icon={CheckCircle2}
                iconClassName="text-green-600"
                iconBgClassName="bg-green-500/5"
              />
              <StatsCard
                title="Pending Scans"
                value={pendingScans}
                icon={Clock}
                iconClassName="text-yellow-600"
                iconBgClassName="bg-yellow-500/5"
              />
              <StatsCard
                title="Generated Reports"
                value={totalReports}
                icon={FileText}
                iconClassName="text-accent"
                iconBgClassName="bg-accent/5"
              />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Recent Activity (Left Column, spans 2 cols) */}
              <div className="lg:col-span-2 space-y-6">
                <Card className="glass-card">
                  <CardHeader className="flex flex-row items-center justify-between pb-4 border-b">
                    <CardTitle className="font-display text-xl flex items-center gap-2">
                      <Activity className="w-5 h-5 text-primary" /> Recent Activity
                    </CardTitle>
                    <Link to="/history">
                      <Button variant="ghost" size="sm" className="text-primary hover:text-primary/80">
                        View All <ExternalLink className="w-3.5 h-3.5 ml-1.5" />
                      </Button>
                    </Link>
                  </CardHeader>
                  <CardContent className="pt-6">
                    {recentScans.length === 0 ? (
                      <EmptyState
                        title="No scans found"
                        description="Upload a 3D CT scan to get started with AI-assisted medical analysis."
                        icon={Upload}
                        actionLabel="Upload New Scan"
                        actionHref="/upload"
                      />
                    ) : (
                      <div className="divide-y divide-border">
                        {recentScans.map((scan: any) => (
                          <div key={scan.id} className="flex flex-col sm:flex-row sm:items-center justify-between py-4 first:pt-0 last:pb-0 gap-4">
                            <div className="flex items-start gap-3">
                              <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0 mt-0.5">
                                <Brain className="w-5 h-5 text-primary" />
                              </div>
                              <div>
                                <h4 className="font-medium text-sm text-foreground line-clamp-1">{scan.file_name}</h4>
                                <p className="text-xs text-muted-foreground mt-1">
                                  {new Date(scan.created_at).toLocaleString()}
                                </p>
                                {scan.prediction && (
                                  <div className="mt-1.5 flex items-center gap-1.5">
                                    <span className="text-[11px] font-semibold text-accent bg-accent/10 px-2 py-0.5 rounded">
                                      {scan.prediction}
                                    </span>
                                    {scan.probability !== null && (
                                      <span className="text-[11px] text-muted-foreground">
                                        Confidence: {(scan.probability * 100).toFixed(1)}%
                                      </span>
                                    )}
                                  </div>
                                )}
                              </div>
                            </div>
                            <div className="flex items-center gap-3 self-end sm:self-center shrink-0">
                              <StatusBadge status={scan.status} />
                              <Link to={`/results/${scan.id}`}>
                                <Button size="sm" variant="outline" className="h-8">
                                  <Eye className="w-3.5 h-3.5 mr-1.5" /> View Results
                                </Button>
                              </Link>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Quick Actions & System Status (Right Column) */}
              <div className="space-y-6">
                {/* Quick Actions */}
                <Card className="glass-card">
                  <CardHeader>
                    <CardTitle className="font-display text-xl flex items-center gap-2">
                      <Settings className="w-5 h-5 text-primary" /> Quick Actions
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="grid grid-cols-1 gap-3">
                    <Link to="/upload" className="block">
                      <Button variant="outline" className="w-full justify-start h-12 text-left font-medium hover:bg-secondary/50 group">
                        <Upload className="w-4 h-4 mr-3 text-primary group-hover:scale-110 transition-transform" />
                        <div>
                          <div className="text-sm">Upload New Scan</div>
                          <div className="text-[10px] text-muted-foreground font-normal font-sans">Analyze a new 3D CT scan</div>
                        </div>
                      </Button>
                    </Link>
                    <Link to="/history" className="block">
                      <Button variant="outline" className="w-full justify-start h-12 text-left font-medium hover:bg-secondary/50 group">
                        <History className="w-4 h-4 mr-3 text-accent group-hover:scale-110 transition-transform" />
                        <div>
                          <div className="text-sm">Scan History</div>
                          <div className="text-[10px] text-muted-foreground font-normal font-sans">View previous scan results</div>
                        </div>
                      </Button>
                    </Link>
                    <Button 
                      variant="outline" 
                      onClick={() => setShowReportsModal(true)}
                      className="w-full justify-start h-12 text-left font-medium hover:bg-secondary/50 group"
                    >
                      <FileText className="w-4 h-4 mr-3 text-emerald-600 group-hover:scale-110 transition-transform" />
                      <div>
                        <div className="text-sm">Reports</div>
                        <div className="text-[10px] text-muted-foreground font-normal font-sans">View & download generated reports</div>
                      </div>
                    </Button>
                  </CardContent>
                </Card>

                {/* System Status */}
                <Card className="glass-card">
                  <CardHeader>
                    <CardTitle className="font-display text-xl flex items-center gap-2">
                      <ShieldCheck className="w-5 h-5 text-primary" /> System Status
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {[
                      { label: 'Backend API', status: systemStatus.api, icon: Activity },
                      { label: 'Database Service', status: systemStatus.database, icon: Database },
                      { label: 'AI Inference Model', status: systemStatus.model, icon: Brain },
                    ].map((sys, i) => (
                      <div key={i} className="flex items-center justify-between p-2.5 rounded-lg bg-secondary/30 border border-border/50">
                        <div className="flex items-center gap-2.5">
                          <sys.icon className="w-4 h-4 text-muted-foreground" />
                          <span className="text-sm font-medium">{sys.label}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`w-2 h-2 rounded-full ${
                            sys.status === 'online' ? 'bg-green-500 animate-pulse' :
                            sys.status === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                          }`} />
                          <span className="text-xs font-semibold capitalize text-muted-foreground">
                            {sys.status}
                          </span>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Reports Modal */}
      {showReportsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <Card className="w-full max-w-lg glass-card shadow-2xl border border-border animate-in zoom-in-95 duration-200">
            <CardHeader className="flex flex-row items-center justify-between pb-4 border-b">
              <CardTitle className="font-display text-xl flex items-center gap-2">
                <FileText className="w-5 h-5 text-primary" /> Medical Reports
              </CardTitle>
              <Button variant="ghost" size="icon" onClick={() => setShowReportsModal(false)} className="h-8 w-8 rounded-full">
                <X className="w-4 h-4" />
              </Button>
            </CardHeader>
            <CardContent className="pt-4 max-h-[400px] overflow-y-auto">
              {reportsLoading ? (
                <div className="text-center py-8 text-muted-foreground">Loading reports...</div>
              ) : reports.length === 0 ? (
                <EmptyState
                  title="No reports found"
                  description="No medical reports have been generated yet. Upload and analyze a scan first."
                  icon={FileText}
                />
              ) : (
                <div className="space-y-3">
                  {reports.map((report: any) => (
                    <div key={report.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/40 border border-border/40 hover:bg-secondary/60 transition-colors">
                      <div className="min-w-0 pr-4">
                        <h4 className="font-medium text-sm text-foreground line-clamp-1">{report.report_text}</h4>
                        <p className="text-xs text-muted-foreground mt-1">
                          {new Date(report.created_at).toLocaleDateString()} • ID: {report.id.substring(0, 8)}
                        </p>
                      </div>
                      <Button 
                        size="sm" 
                        variant="outline" 
                        onClick={() => window.open(`/api/reports/download/${report.id}`, "_blank")}
                        className="shrink-0"
                      >
                        <Download className="w-3.5 h-3.5 mr-1" /> Download
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
