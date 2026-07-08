import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Brain, ArrowLeft, Eye } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

import { StatusBadge } from '@/components/ui/StatusBadge';
import { EmptyState } from '@/components/ui/EmptyState';
import { LoadingSkeleton } from '@/components/ui/LoadingSkeleton';

const ScanHistory = () => {
  const { user } = useAuth();

  const { data: scans = [], isLoading } = useQuery({
    queryKey: ['all-scans', user?.id],
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

  return (
    <div className="min-h-screen bg-background pb-12">
      <header className="sticky top-0 z-50 glass-card border-b">
        <div className="container mx-auto px-4 h-16 flex items-center gap-4">
          <Link to="/dashboard"><Button variant="ghost" size="icon"><ArrowLeft className="w-5 h-5" /></Button></Link>
          <div className="flex items-center gap-2">
            <img src="/med ai.png" className="w-8 h-8 object-contain" alt="Med AI Logo" />
            <span className="font-display font-bold">Scan History</span>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-3xl">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="font-display">All Scans</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <LoadingSkeleton variant="table" rows={5} />
            ) : scans.length === 0 ? (
              <EmptyState
                title="No scans uploaded yet"
                description="Upload a 3D CT scan to begin. Your scan history will appear here."
                icon={Brain}
                actionLabel="Upload New Scan"
                actionHref="/upload"
              />
            ) : (
              <div className="space-y-3">
                {scans.map((scan: any) => (
                  <div key={scan.id} className="flex items-center justify-between p-4 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                        <Brain className="w-5 h-5 text-primary" />
                      </div>
                      <div>
                        <p className="font-medium text-sm">{scan.file_name}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          {scan.scan_type.toUpperCase()} • {new Date(scan.created_at).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={scan.status} />
                      <Link to={`/results/${scan.id}`}>
                        <Button size="sm" variant="outline"><Eye className="w-3 h-3 mr-1" /> View</Button>
                      </Link>
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

export default ScanHistory;
