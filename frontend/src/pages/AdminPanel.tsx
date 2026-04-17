import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { supabase } from '@/lib/supabase';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Brain, ArrowLeft, Users, BarChart3, Shield } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

const AdminPanel = () => {
  const { user } = useAuth();

  const { data: allUsers = [] } = useQuery({
    queryKey: ['admin-users'],
    queryFn: async () => {
      const { data } = await supabase.from('profiles').select('*').order('created_at', { ascending: false });
      return data || [];
    },
  });

  const { data: allScans = [] } = useQuery({
    queryKey: ['admin-scans'],
    queryFn: async () => {
      const { data } = await supabase.from('scans').select('*, profiles(full_name, email)').order('created_at', { ascending: false }).limit(20);
      return data || [];
    },
  });

  const { data: stats } = useQuery({
    queryKey: ['admin-stats'],
    queryFn: async () => {
      const { count: totalUsers } = await supabase.from('profiles').select('*', { count: 'exact', head: true });
      const { count: totalScans } = await supabase.from('scans').select('*', { count: 'exact', head: true });
      const { count: completedScans } = await supabase.from('scans').select('*', { count: 'exact', head: true }).eq('status', 'completed');
      return { totalUsers: totalUsers || 0, totalScans: totalScans || 0, completedScans: completedScans || 0 };
    },
  });

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 glass-card border-b">
        <div className="container mx-auto px-4 h-16 flex items-center gap-4">
          <Link to="/dashboard"><Button variant="ghost" size="icon"><ArrowLeft className="w-5 h-5" /></Button></Link>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg gradient-medical flex items-center justify-center">
              <Shield className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="font-display font-bold">Admin Panel</span>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <h1 className="font-display text-3xl font-bold mb-8">System Overview</h1>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <Card className="glass-card">
            <CardContent className="pt-6 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Users</p>
                <p className="text-3xl font-display font-bold">{stats?.totalUsers ?? 0}</p>
              </div>
              <Users className="w-10 h-10 text-primary opacity-50" />
            </CardContent>
          </Card>
          <Card className="glass-card">
            <CardContent className="pt-6 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Total Scans</p>
                <p className="text-3xl font-display font-bold">{stats?.totalScans ?? 0}</p>
              </div>
              <BarChart3 className="w-10 h-10 text-accent opacity-50" />
            </CardContent>
          </Card>
          <Card className="glass-card">
            <CardContent className="pt-6 flex items-center justify-between">
              <div>
                <p className="text-sm text-muted-foreground">Completed</p>
                <p className="text-3xl font-display font-bold">{stats?.completedScans ?? 0}</p>
              </div>
              <Brain className="w-10 h-10 text-primary opacity-50" />
            </CardContent>
          </Card>
        </div>

        {/* Users */}
        <Card className="glass-card mb-8">
          <CardHeader><CardTitle className="font-display">Users</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {allUsers.map((u: any) => (
                <div key={u.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
                  <div>
                    <p className="font-medium text-sm">{u.full_name || 'No name'}</p>
                    <p className="text-xs text-muted-foreground">{u.email}</p>
                  </div>
                  <span className="text-xs text-muted-foreground">{new Date(u.created_at).toLocaleDateString()}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recent Scans */}
        <Card className="glass-card">
          <CardHeader><CardTitle className="font-display">Recent Scans (All Users)</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-2">
              {allScans.map((scan: any) => (
                <div key={scan.id} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
                  <div>
                    <p className="font-medium text-sm">{scan.file_name}</p>
                    <p className="text-xs text-muted-foreground">{scan.profiles?.full_name} • {scan.scan_type.toUpperCase()}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${scan.status === 'completed' ? 'bg-accent/10 text-accent' : 'bg-muted text-muted-foreground'}`}>
                      {scan.status}
                    </span>
                    <span className="text-xs text-muted-foreground">{new Date(scan.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AdminPanel;
