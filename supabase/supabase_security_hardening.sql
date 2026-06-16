-- Supabase Database Security Hardening Script
-- Project ID: ndkjiycehjdkcqupphuu
-- Run this script in the Supabase SQL Editor to resolve all security advisories.

-- 1. Organize Extensions (Fixes Advisor 0014: Extension in public schema)
-- Move common extensions to a dedicated 'extensions' schema
CREATE SCHEMA IF NOT EXISTS extensions;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp" SCHEMA extensions;
CREATE EXTENSION IF NOT EXISTS "pgcrypto" SCHEMA extensions;

-- 2. Enable Row Level Security (Fixes Advisor 0013 & 0007: RLS disabled)
ALTER TABLE IF EXISTS public.recruiters ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.scoring_weights ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.stripe_webhook_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.organization_invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.candidate_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS public.interviews ENABLE ROW LEVEL SECURITY;

-- 3. Create Security Policies (Fixes Advisor 0008: RLS enabled but no policy exists)

-- Recruiters access policy
DROP POLICY IF EXISTS recruiter_self_policy ON public.recruiters;
CREATE POLICY recruiter_self_policy ON public.recruiters 
    FOR ALL 
    TO authenticated 
    USING (auth.uid() = id);

DROP POLICY IF EXISTS recruiter_insert_policy ON public.recruiters;
CREATE POLICY recruiter_insert_policy ON public.recruiters 
    FOR INSERT 
    TO anon, authenticated 
    WITH CHECK (true);

-- Scoring weights access policy
DROP POLICY IF EXISTS scoring_weights_policy ON public.scoring_weights;
CREATE POLICY scoring_weights_policy ON public.scoring_weights 
    FOR ALL 
    TO authenticated 
    USING (recruiter_id = auth.uid());

-- Candidates access policy
DROP POLICY IF EXISTS candidates_policy ON public.candidates;
CREATE POLICY candidates_policy ON public.candidates 
    FOR ALL 
    TO authenticated 
    USING (recruiter_id = auth.uid());

-- Jobs access policy
DROP POLICY IF EXISTS jobs_policy ON public.jobs;
CREATE POLICY jobs_policy ON public.jobs 
    FOR ALL 
    TO authenticated 
    USING (recruiter_id = auth.uid());

-- Candidate notes access policy
DROP POLICY IF EXISTS candidate_notes_policy ON public.candidate_notes;
CREATE POLICY candidate_notes_policy ON public.candidate_notes 
    FOR ALL 
    TO authenticated 
    USING (EXISTS (
        SELECT 1 FROM public.candidates 
        WHERE public.candidates.id = candidate_id 
        AND public.candidates.recruiter_id = auth.uid()
    ));

-- Interviews access policy
DROP POLICY IF EXISTS interviews_policy ON public.interviews;
CREATE POLICY interviews_policy ON public.interviews 
    FOR ALL 
    TO authenticated 
    USING (EXISTS (
        SELECT 1 FROM public.candidates 
        WHERE public.candidates.id = candidate_id 
        AND public.candidates.recruiter_id = auth.uid()
    ));

-- Stripe webhook events access policy
DROP POLICY IF EXISTS stripe_webhook_events_policy ON public.stripe_webhook_events;
CREATE POLICY stripe_webhook_events_policy ON public.stripe_webhook_events 
    FOR ALL 
    TO authenticated, anon 
    USING (true);

-- Organization invitations access policy
DROP POLICY IF EXISTS organization_invitations_policy ON public.organization_invitations;
CREATE POLICY organization_invitations_policy ON public.organization_invitations 
    FOR ALL 
    TO authenticated 
    USING (true);

-- 4. Harden Public Schema Functions (Fixes Advisor 0010 & 0011: Function search path mutable / definer)
-- Dynamic PL/pgSQL script to loop over all functions in the public schema and set INVOKER + search_path.
DO $$
DECLARE
    func_record RECORD;
BEGIN
    FOR func_record IN 
        SELECT 
            p.proname,
            pg_get_function_identity_arguments(p.oid) AS args
        FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
    LOOP
        EXECUTE format('ALTER FUNCTION public.%I(%s) SECURITY INVOKER;', func_record.proname, func_record.args);
        EXECUTE format('ALTER FUNCTION public.%I(%s) SET search_path = public, pg_temp;', func_record.proname, func_record.args);
    END LOOP;
END;
$$;
