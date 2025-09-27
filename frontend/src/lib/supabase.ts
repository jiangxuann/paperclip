import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || 'placeholder-key'

// Only create real client if we have valid URLs (not placeholders)
export const supabase = supabaseUrl.includes('placeholder') || supabaseAnonKey.includes('placeholder')
  ? ({
      auth: {
        getSession: () => Promise.resolve({ data: { session: null }, error: null }),
        onAuthStateChange: () => ({ data: { subscription: { unsubscribe: () => {} } } }),
        signOut: () => Promise.resolve({ error: null }),
      },
      from: () => ({
        select: () => ({
          eq: () => ({
            single: () => Promise.resolve({ data: null, error: null })
          })
        })
      }),
    } as any) // eslint-disable-line @typescript-eslint/no-explicit-any
  : createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true
      }
    })

// Types for our database schema
export interface Project {
  id: string
  name: string
  description?: string
  created_at: string
  updated_at: string
  user_id: string
  sources_count?: number
  scripts_count?: number
  videos_count?: number
}

export interface ContentSource {
  id: string
  project_id: string
  url?: string
  file_path?: string
  content_type: 'url' | 'pdf'
  status: 'pending' | 'processing' | 'completed' | 'failed'
  title?: string
  extracted_text?: string
  created_at: string
  updated_at: string
}

export interface Script {
  id: string
  project_id: string
  content_source_id?: string
  title: string
  content: string
  template_used?: string
  created_at: string
  updated_at: string
}

export interface Video {
  id: string
  project_id: string
  script_id?: string
  title: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  video_url?: string
  thumbnail_url?: string
  duration?: number
  created_at: string
  updated_at: string
}