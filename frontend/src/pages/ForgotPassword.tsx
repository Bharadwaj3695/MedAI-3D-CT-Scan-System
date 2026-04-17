import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Brain, Mail, ArrowLeft } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const { resetPassword } = useAuth();
  const { toast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await resetPassword(email);
      setSent(true);
    } catch (err: any) {
      toast({ title: 'Error', description: err.message, variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4 bg-background">
      <Card className="w-full max-w-md glass-card">
        <CardHeader className="text-center space-y-4">
          <Link to="/" className="inline-flex items-center gap-2 justify-center">
            <img src="/med ai.png" className="w-10 h-10 object-contain" alt="Med AI Logo" />
          </Link>
          <h1 className="font-display text-2xl font-bold">Reset Password</h1>
        </CardHeader>
        <CardContent>
          {sent ? (
            <div className="text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto">
                <Mail className="w-8 h-8 text-primary" />
              </div>
              <p className="text-muted-foreground">We've sent a password reset link to <strong>{email}</strong></p>
              <Link to="/login"><Button variant="outline" className="w-full"><ArrowLeft className="w-4 h-4 mr-2" /> Back to Login</Button></Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <p className="text-sm text-muted-foreground">Enter your email and we'll send you a reset link.</p>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" value={email} onChange={e => setEmail(e.target.value)} className="h-11" required />
              </div>
              <Button type="submit" className="w-full h-11 gradient-medical text-primary-foreground border-0" disabled={loading}>
                {loading ? 'Sending...' : 'Send Reset Link'}
              </Button>
              <Link to="/login" className="block text-center text-sm text-muted-foreground hover:text-foreground">
                <ArrowLeft className="w-3 h-3 inline mr-1" /> Back to login
              </Link>
            </form>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default ForgotPassword;
