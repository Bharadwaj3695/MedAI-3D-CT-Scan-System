import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Brain, Shield, Zap, Upload, BarChart3, Bot, ArrowRight, Activity } from 'lucide-react';

const Landing = () => {
  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
      <nav className="fixed top-0 w-full z-50 glass-card border-b">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src="/med ai.png" className="w-9 h-9 object-contain" alt="Med AI Logo" />
            <span className="font-display font-bold text-xl">Med AI Scan</span>
          </div>
          <div className="hidden md:flex items-center gap-8">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Features</a>
            <a href="#how-it-works" className="text-sm text-muted-foreground hover:text-foreground transition-colors">How It Works</a>
          </div>
          <div className="flex items-center gap-3">
            <Link to="/login">
              <Button variant="ghost" size="sm">Log In</Button>
            </Link>
            <Link to="/signup">
              <Button size="sm" className="gradient-medical text-primary-foreground border-0">
                Get Started <ArrowRight className="w-4 h-4 ml-1" />
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="pt-32 pb-20 px-4 relative overflow-hidden">
        <div className="absolute inset-0 opacity-30">
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-3xl animate-float" />
          <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-accent/20 rounded-full blur-3xl animate-float" style={{ animationDelay: '1s' }} />
        </div>
        <div className="container mx-auto text-center relative z-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium mb-6">
            <Activity className="w-4 h-4" />
            AI-Powered Medical Imaging Analysis
          </div>
          <h1 className="font-display text-4xl md:text-6xl lg:text-7xl font-bold max-w-4xl mx-auto leading-tight mb-6">
            Detect Lung Diseases with{' '}
            <span className="text-gradient">AI Precision</span>
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
            Upload CT scan images and get instant AI-powered analysis with Grad-CAM heatmap
            visualization. Detect lung nodules and diseases with medical-grade accuracy.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/signup">
              <Button size="lg" className="gradient-medical text-primary-foreground border-0 h-14 px-8 text-base glow-primary">
                Start Analyzing <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <Link to="/login">
              <Button size="lg" variant="outline" className="h-14 px-8 text-base">
                View Demo
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20 px-4">
        <div className="container mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-display text-3xl md:text-4xl font-bold mb-4">
              Powerful Medical AI Features
            </h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Built for radiologists, researchers, and healthcare professionals.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: Upload, title: 'CT Scan Upload', desc: 'Upload 2D and 3D CT scan images in DICOM, PNG, JPEG formats with drag-and-drop support.' },
              { icon: Brain, title: 'AI Diagnosis', desc: 'Advanced AI models analyze scans to detect lung nodules and predict potential diseases.' },
              { icon: BarChart3, title: 'Grad-CAM Heatmap', desc: 'Visual heatmap overlay showing exactly where the AI detected anomalies in your scan.' },
              { icon: Bot, title: 'Smart AI Assistant', desc: 'Ask questions about results and get detailed explanations from our AI medical assistant.' },
              { icon: Shield, title: 'HIPAA Compliant', desc: 'End-to-end encryption and strict access controls to protect patient data.' },
              { icon: Zap, title: 'Instant Results', desc: 'Get analysis results in seconds with detailed prediction confidence scores.' },
            ].map((f, i) => (
              <div key={i} className="glass-card rounded-xl p-6 hover:shadow-xl transition-all group">
                <div className="w-12 h-12 rounded-lg gradient-medical flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  <f.icon className="w-6 h-6 text-primary-foreground" />
                </div>
                <h3 className="font-display font-semibold text-lg mb-2">{f.title}</h3>
                <p className="text-muted-foreground text-sm">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-20 px-4 bg-secondary/50">
        <div className="container mx-auto">
          <h2 className="font-display text-3xl md:text-4xl font-bold text-center mb-16">How It Works</h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            {[
              { step: '01', title: 'Upload Scan', desc: 'Upload your CT scan image in any supported format.' },
              { step: '02', title: 'AI Analysis', desc: 'Our model processes and analyzes the scan for anomalies.' },
              { step: '03', title: 'Get Results', desc: 'View predictions, heatmaps, and get AI-assisted explanations.' },
            ].map((s, i) => (
              <div key={i} className="text-center">
                <div className="w-16 h-16 rounded-full gradient-medical flex items-center justify-center mx-auto mb-4 text-primary-foreground font-display font-bold text-xl">
                  {s.step}
                </div>
                <h3 className="font-display font-semibold text-lg mb-2">{s.title}</h3>
                <p className="text-muted-foreground text-sm">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t">
        <div className="container mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <img src="/med ai.png" className="w-8 h-8 object-contain" alt="Med AI Logo" />
            <span className="font-display font-bold">Med AI Scan</span>
          </div>
          <p className="text-sm text-muted-foreground">&copy; {new Date().getFullYear()} Med AI Scan. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
