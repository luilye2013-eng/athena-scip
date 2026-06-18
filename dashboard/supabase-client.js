/**
 * Athena SCIP - Supabase Client Singleton
 * SINGLE SOURCE OF TRUTH - Do not redeclare anywhere else
 */

// Only initialize if not already defined
if (typeof window.supabaseClient === 'undefined') {
    window.supabaseClient = supabase.createClient(
        window.CONFIG.SUPABASE_URL,
        window.CONFIG.SUPABASE_KEY
    );
    console.log('✅ Supabase client initialized');
}