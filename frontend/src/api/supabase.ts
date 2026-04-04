import { createClient, type SupabaseClient } from "@supabase/supabase-js";

const supabaseUrl = (import.meta.env.VITE_SUPABASE_URL ?? "").trim();
const supabaseKey = (import.meta.env.VITE_SUPABASE_ANON_KEY ?? "").trim();

export const supabaseConfigured = Boolean(supabaseUrl && supabaseKey);

/**
 * Real credentials come from `.env` (VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY).
 * When unset, auth and DB calls are inert until configured (see `supabaseConfigured`).
 */
function buildClient(): SupabaseClient {
  if (supabaseConfigured) {
    return createClient(supabaseUrl, supabaseKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
      },
    });
  }

  return createClient("https://invalid.invalid", "invalid", {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}

export const supabase = buildClient();
