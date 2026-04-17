import { useState, useCallback } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Brain, Upload, ArrowLeft, FileImage, X, Loader2 } from 'lucide-react';
import { useToast } from '@/hooks/use-toast';

const UploadScan = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [scanType, setScanType] = useState('2d');
  const [notes, setNotes] = useState('');
  const [uploading, setUploading] = useState(false);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    if (f.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onloadend = () => setPreview(reader.result as string);
      reader.readAsDataURL(f);
    } else {
      setPreview(null);
    }
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f) {
      setFile(f);
      if (f.type.startsWith('image/')) {
        const reader = new FileReader();
        reader.onloadend = () => setPreview(reader.result as string);
        reader.readAsDataURL(f);
      }
    }
  }, []);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      if (!user) {
        throw new Error("You must be logged in to upload a scan. Please sign in.");
      }

      const formData = new FormData();
      formData.append('file', file);
      formData.append('scan_type', scanType);
      formData.append('notes', notes);

      const token = localStorage.getItem('medai_token');
      const res = await fetch("/api/scans/upload", {
        method: "POST",
        headers: { "Authorization": `Bearer ${token}` },
        body: formData
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || "Error uploading to Python backend.");
      }
      
      const responseData = await res.json();

      toast({ title: 'Scan uploaded and analyzed successfully!', description: 'Redirecting to results.' });
      navigate(`/results/${responseData.scan_id}`);
    } catch (err: any) {
      toast({ title: 'Upload/Analysis failed', description: err.message, variant: 'destructive' });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 glass-card border-b">
        <div className="container mx-auto px-4 h-16 flex items-center gap-4">
          <Link to="/dashboard"><Button variant="ghost" size="icon"><ArrowLeft className="w-5 h-5" /></Button></Link>
          <div className="flex items-center gap-2">
            <img src="/med ai.png" className="w-8 h-8 object-contain" alt="Med AI Logo" />
            <span className="font-display font-bold">Upload Scan</span>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8 max-w-2xl">
        <Card className="glass-card">
          <CardHeader>
            <CardTitle className="font-display">Upload CT Scan</CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Drop zone */}
            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer
                ${file ? 'border-primary bg-primary/5' : 'border-border hover:border-primary/50'}`}
              onDragOver={e => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <input id="file-input" type="file" className="hidden" accept="image/*,.dcm,.nii,.nii.gz" onChange={handleFileChange} />
              {preview ? (
                <div className="relative inline-block">
                  <img src={preview} alt="Preview" className="max-h-64 rounded-lg mx-auto" />
                  <button onClick={e => { e.stopPropagation(); setFile(null); setPreview(null); }} className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-destructive text-destructive-foreground flex items-center justify-center">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ) : file ? (
                <div className="flex flex-col items-center gap-2">
                  <FileImage className="w-12 h-12 text-primary" />
                  <p className="font-medium">{file.name}</p>
                  <p className="text-sm text-muted-foreground">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                </div>
              ) : (
                <div className="flex flex-col items-center gap-3">
                  <Upload className="w-12 h-12 text-muted-foreground" />
                  <div>
                    <p className="font-medium">Drop your CT scan here</p>
                    <p className="text-sm text-muted-foreground">or click to browse • PNG, JPEG, DICOM, NIfTI</p>
                  </div>
                </div>
              )}
            </div>

            {/* Options */}
            <div className="grid gap-4">
              <div className="space-y-2">
                <Label>Scan Type</Label>
                <Select value={scanType} onValueChange={setScanType}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="2d">2D CT Scan</SelectItem>
                    <SelectItem value="3d">3D CT Scan</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Notes (optional)</Label>
                <Textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Patient history, symptoms, etc." rows={3} />
              </div>
            </div>

            <Button className="w-full h-12 gradient-medical text-primary-foreground border-0" onClick={handleUpload} disabled={!file || uploading}>
              {uploading ? <><Loader2 className="w-4 h-4 mr-2 animate-spin" /> Analyzing...</> : <><Upload className="w-4 h-4 mr-2" /> Upload & Analyze</>}
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default UploadScan;
