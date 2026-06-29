-- ==============================================================================
-- MedAI 3D CT Scan System - Database Migration Script
-- Date: 2026-06-29
-- Rationale: Complete schema initialization matching the FastAPI backend exactly.
-- ==============================================================================

-- 1. Enums & Custom Types
CREATE TYPE public.app_role AS ENUM ('admin', 'user');

-- 2. Profiles Table
-- Primary key 'id' directly references 'auth.users(id)' (id == auth.users.id)
CREATE TABLE public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT,
  avatar_url TEXT,
  disabled BOOLEAN NOT NULL DEFAULT false,
  inactive BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. User Roles Table
CREATE TABLE public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  role public.app_role NOT NULL DEFAULT 'user',
  UNIQUE (user_id, role)
);

-- 4. Scans Table
CREATE TABLE public.scans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  file_name TEXT NOT NULL,
  file_path TEXT NOT NULL,
  file_url TEXT,
  scan_type TEXT NOT NULL DEFAULT 'CT',
  notes TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT scans_status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed'))
);

-- 5. Analysis Results Table
CREATE TABLE public.analysis_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scan_id UUID REFERENCES public.scans(id) ON DELETE CASCADE NOT NULL UNIQUE,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  result_data JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 6. Reports Table
CREATE TABLE public.reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scan_id UUID REFERENCES public.scans(id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  pdf_url TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 7. Scan Results Table (For Legacy /predict/ Endpoint Compatibility)
CREATE TABLE public.scan_results (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_name TEXT NOT NULL,
  prediction TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ==============================================================================
-- Performance Optimization (Indexes)
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_user_roles_user_id ON public.user_roles(user_id);
CREATE INDEX IF NOT EXISTS idx_scans_user_id ON public.scans(user_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_scan_id ON public.analysis_results(scan_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_user_id ON public.analysis_results(user_id);
CREATE INDEX IF NOT EXISTS idx_reports_scan_id ON public.reports(scan_id);
CREATE INDEX IF NOT EXISTS idx_reports_user_id ON public.reports(user_id);

-- ==============================================================================
-- Functions & Triggers
-- ==============================================================================

-- A. Role Verification Helper Function
CREATE OR REPLACE FUNCTION public.has_role(_user_id UUID, _role public.app_role)
RETURNS BOOLEAN
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
AS $$
  SELECT EXISTS (SELECT 1 FROM public.user_roles WHERE user_id = _user_id AND role = _role)
$$;

-- B. Updated At Auto-timestamp Trigger Function
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

CREATE TRIGGER update_scans_updated_at
  BEFORE UPDATE ON public.scans
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

-- C. User Registration Webhook Trigger Function (Auto-profile Creation)
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.profiles (id, email, full_name)
  VALUES (
    NEW.id,
    NEW.email,
    COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
  )
  ON CONFLICT (id) DO NOTHING;

  INSERT INTO public.user_roles (user_id, role)
  VALUES (NEW.id, 'user')
  ON CONFLICT (user_id, role) DO NOTHING;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- ==============================================================================
-- Row Level Security (RLS) Policies
-- ==============================================================================

-- A. Enable RLS on All Tables
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_results ENABLE ROW LEVEL SECURITY;

-- B. Profiles Policies
CREATE POLICY "Allow users to select own profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Allow users to update own profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

CREATE POLICY "Allow users to insert own profile" ON public.profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Allow admins to select all profiles" ON public.profiles
  FOR SELECT USING (public.has_role(auth.uid(), 'admin'));

-- C. User Roles Policies
CREATE POLICY "Allow users to select own roles" ON public.user_roles
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Allow users to insert own roles" ON public.user_roles
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Allow admins to manage all roles" ON public.user_roles
  FOR ALL USING (public.has_role(auth.uid(), 'admin'));

-- D. Scans Policies
CREATE POLICY "Allow users to select own scans" ON public.scans
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Allow users to insert own scans" ON public.scans
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Allow users to update own scans" ON public.scans
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Allow users to delete own scans" ON public.scans
  FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Allow admins to select all scans" ON public.scans
  FOR SELECT USING (public.has_role(auth.uid(), 'admin'));

-- E. Analysis Results Policies
CREATE POLICY "Allow users to select own analysis results" ON public.analysis_results
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Allow users to insert own analysis results" ON public.analysis_results
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Allow users to update own analysis results" ON public.analysis_results
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Allow users to delete own analysis results" ON public.analysis_results
  FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Allow admins to select all analysis results" ON public.analysis_results
  FOR SELECT USING (public.has_role(auth.uid(), 'admin'));

-- F. Reports Policies
CREATE POLICY "Allow users to select own reports" ON public.reports
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Allow users to insert own reports" ON public.reports
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Allow users to update own reports" ON public.reports
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Allow users to delete own reports" ON public.reports
  FOR DELETE USING (auth.uid() = user_id);

CREATE POLICY "Allow admins to select all reports" ON public.reports
  FOR SELECT USING (public.has_role(auth.uid(), 'admin'));

-- G. Scan Results Policies (Legacy /predict/ Endpoint)
CREATE POLICY "Allow public insert on scan_results" ON public.scan_results
  FOR INSERT WITH CHECK (true);

CREATE POLICY "Allow public select on scan_results" ON public.scan_results
  FOR SELECT USING (true);

-- ==============================================================================
-- Storage Buckets & Policies
-- ==============================================================================

-- A. Create the 'scans' bucket expected by the backend
INSERT INTO storage.buckets (id, name, public)
VALUES ('scans', 'scans', true)
ON CONFLICT (id) DO NOTHING;

-- B. Storage Policies
CREATE POLICY "Allow authenticated users to upload scans" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'scans' 
    AND auth.role() = 'authenticated' 
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

CREATE POLICY "Allow users to view own scans" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'scans' 
    AND auth.role() = 'authenticated' 
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

CREATE POLICY "Allow users to delete own scans" ON storage.objects
  FOR DELETE USING (
    bucket_id = 'scans' 
    AND auth.role() = 'authenticated' 
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

CREATE POLICY "Allow public select on scans" ON storage.objects
  FOR SELECT USING (bucket_id = 'scans');
