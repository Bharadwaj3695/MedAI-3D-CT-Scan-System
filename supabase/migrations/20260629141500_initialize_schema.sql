-- ==============================================================================
-- MedAI 3D CT Scan System - Database Migration Script
-- Date: 2026-06-29
-- Rationale: Safe schema initialization matching the FastAPI backend exactly,
--            preserving existing tables, buckets, data, and users.
-- ==============================================================================

-- 1. Enums & Custom Types (Idempotent creation of app_role)
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'app_role') THEN
    CREATE TYPE public.app_role AS ENUM ('admin', 'user');
  END IF;
END $$;

-- 2. Profiles Table (Missing - Created safely)
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT,
  avatar_url TEXT,
  disabled BOOLEAN NOT NULL DEFAULT false,
  inactive BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. User Roles Table (Missing - Created safely)
CREATE TABLE IF NOT EXISTS public.user_roles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  role public.app_role NOT NULL DEFAULT 'user',
  UNIQUE (user_id, role)
);

-- 4. Scans Table (Existing - Altered safely)
-- Set default of scan_type to 'CT'
ALTER TABLE public.scans ALTER COLUMN scan_type SET DEFAULT 'CT';

-- Add status check constraint safely
ALTER TABLE public.scans DROP CONSTRAINT IF EXISTS scans_status_check;
ALTER TABLE public.scans ADD CONSTRAINT scans_status_check CHECK (status IN ('pending', 'processing', 'completed', 'failed'));

-- 5. Analysis Results Table (Existing - Altered safely)
-- Ensure scan_id has a UNIQUE constraint
ALTER TABLE public.analysis_results DROP CONSTRAINT IF EXISTS analysis_results_scan_id_key;
ALTER TABLE public.analysis_results ADD CONSTRAINT analysis_results_scan_id_key UNIQUE (scan_id);

-- 6. Reports Table (Missing - Created safely)
CREATE TABLE IF NOT EXISTS public.reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  scan_id UUID REFERENCES public.scans(id) ON DELETE CASCADE NOT NULL,
  user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  pdf_url TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 7. Scan Results Table (Existing - Do NOT recreate)
-- (No CREATE TABLE statement to avoid recreating or altering the existing scan_results table)

-- ==============================================================================
-- Backfill Profiles & User Roles for Existing Users
-- ==============================================================================
INSERT INTO public.profiles (id, email, full_name)
SELECT 
  id, 
  email, 
  COALESCE(raw_user_meta_data->>'full_name', split_part(email, '@', 1))
FROM auth.users
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.user_roles (user_id, role)
SELECT 
  id, 
  'user'
FROM auth.users
ON CONFLICT (user_id, role) DO NOTHING;

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

DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
  BEFORE UPDATE ON public.profiles
  FOR EACH ROW
  EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_scans_updated_at ON public.scans;
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

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- ==============================================================================
-- Row Level Security (RLS) Policies
-- ==============================================================================

-- A. Enable RLS on All Tables (Idempotent)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.scan_results ENABLE ROW LEVEL SECURITY;

-- B. Clean up legacy/conflicting policies if they exist
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can insert own profile" ON public.profiles;
DROP POLICY IF EXISTS "Users can read own role" ON public.user_roles;
DROP POLICY IF EXISTS "Admins can view all profiles" ON public.profiles;
DROP POLICY IF EXISTS "Users can view own scans" ON public.scans;
DROP POLICY IF EXISTS "Users can insert own scans" ON public.scans;
DROP POLICY IF EXISTS "Users can update own scans" ON public.scans;
DROP POLICY IF EXISTS "Admins can view all scans" ON public.scans;
DROP POLICY IF EXISTS "Users can view own results" ON public.analysis_results;
DROP POLICY IF EXISTS "Users can insert own results" ON public.analysis_results;
DROP POLICY IF EXISTS "Admins can view all results" ON public.analysis_results;

-- C. Profiles Policies
DROP POLICY IF EXISTS "Allow users to select own profile" ON public.profiles;
CREATE POLICY "Allow users to select own profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Allow users to update own profile" ON public.profiles;
CREATE POLICY "Allow users to update own profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Allow users to insert own profile" ON public.profiles;
CREATE POLICY "Allow users to insert own profile" ON public.profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

DROP POLICY IF EXISTS "Allow admins to select all profiles" ON public.profiles;
CREATE POLICY "Allow admins to select all profiles" ON public.profiles
  FOR SELECT USING (public.has_role(auth.uid(), 'admin'));

-- D. User Roles Policies
DROP POLICY IF EXISTS "Allow users to select own roles" ON public.user_roles;
CREATE POLICY "Allow users to select own roles" ON public.user_roles
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow users to insert own roles" ON public.user_roles;
CREATE POLICY "Allow users to insert own roles" ON public.user_roles
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow admins to manage all roles" ON public.user_roles;
CREATE POLICY "Allow admins to manage all roles" ON public.user_roles
  FOR ALL USING (public.has_role(auth.uid(), 'admin'));

-- E. Scans Policies
DROP POLICY IF EXISTS "Allow users to select own scans" ON public.scans;
CREATE POLICY "Allow users to select own scans" ON public.scans
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow users to insert own scans" ON public.scans;
CREATE POLICY "Allow users to insert own scans" ON public.scans
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow users to update own scans" ON public.scans;
CREATE POLICY "Allow users to update own scans" ON public.scans
  FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow users to delete own scans" ON public.scans;
CREATE POLICY "Allow users to delete own scans" ON public.scans
  FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow admins to select all scans" ON public.scans;
CREATE POLICY "Allow admins to select all scans" ON public.scans
  FOR SELECT USING (public.has_role(auth.uid(), 'admin'));

-- F. Analysis Results Policies
DROP POLICY IF EXISTS "Allow users to select own analysis results" ON public.analysis_results;
CREATE POLICY "Allow users to select own analysis results" ON public.analysis_results
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow users to insert own analysis results" ON public.analysis_results;
CREATE POLICY "Allow users to insert own analysis results" ON public.analysis_results
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow users to update own analysis results" ON public.analysis_results;
CREATE POLICY "Allow users to update own analysis results" ON public.analysis_results
  FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow users to delete own analysis results" ON public.analysis_results;
CREATE POLICY "Allow users to delete own analysis results" ON public.analysis_results
  FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow admins to select all analysis results" ON public.analysis_results;
CREATE POLICY "Allow admins to select all analysis results" ON public.analysis_results
  FOR SELECT USING (public.has_role(auth.uid(), 'admin'));

-- G. Reports Policies
DROP POLICY IF EXISTS "Allow users to select own reports" ON public.reports;
CREATE POLICY "Allow users to select own reports" ON public.reports
  FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow users to insert own reports" ON public.reports;
CREATE POLICY "Allow users to insert own reports" ON public.reports
  FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow users to update own reports" ON public.reports;
CREATE POLICY "Allow users to update own reports" ON public.reports
  FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow users to delete own reports" ON public.reports;
CREATE POLICY "Allow users to delete own reports" ON public.reports
  FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Allow admins to select all reports" ON public.reports;
CREATE POLICY "Allow admins to select all reports" ON public.reports
  FOR SELECT USING (public.has_role(auth.uid(), 'admin'));

-- H. Scan Results Policies (Legacy /predict/ Endpoint)
DROP POLICY IF EXISTS "Allow public insert on scan_results" ON public.scan_results;
CREATE POLICY "Allow public insert on scan_results" ON public.scan_results
  FOR INSERT WITH CHECK (true);

DROP POLICY IF EXISTS "Allow public select on scan_results" ON public.scan_results;
CREATE POLICY "Allow public select on scan_results" ON public.scan_results
  FOR SELECT USING (true);

-- ==============================================================================
-- Storage Buckets & Policies
-- ==============================================================================

-- A. Create the 'scans' bucket expected by the backend (Idempotent)
INSERT INTO storage.buckets (id, name, public)
VALUES ('scans', 'scans', true)
ON CONFLICT (id) DO NOTHING;

-- B. Storage Policies
DROP POLICY IF EXISTS "Allow authenticated users to upload scans" ON storage.objects;
CREATE POLICY "Allow authenticated users to upload scans" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'scans' 
    AND auth.role() = 'authenticated' 
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

DROP POLICY IF EXISTS "Allow users to view own scans" ON storage.objects;
CREATE POLICY "Allow users to view own scans" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'scans' 
    AND auth.role() = 'authenticated' 
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

DROP POLICY IF EXISTS "Allow users to delete own scans" ON storage.objects;
CREATE POLICY "Allow users to delete own scans" ON storage.objects
  FOR DELETE USING (
    bucket_id = 'scans' 
    AND auth.role() = 'authenticated' 
    AND (storage.foldername(name))[1] = auth.uid()::text
  );

DROP POLICY IF EXISTS "Allow public select on scans" ON storage.objects;
CREATE POLICY "Allow public select on scans" ON storage.objects
  FOR SELECT USING (bucket_id = 'scans');
