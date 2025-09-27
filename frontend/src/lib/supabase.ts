import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
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