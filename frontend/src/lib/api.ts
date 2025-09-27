import { supabase } from './supabase'

// API client for backend communication
class ApiClient {
  private baseUrl: string

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  }

  private async request(endpoint: string, options: RequestInit = {}) {
    const url = `${this.baseUrl}${endpoint}`
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    }

    const response = await fetch(url, config)

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Unknown error' }))
      throw new Error(error.message || `HTTP ${response.status}`)
    }

    return response.json()
  }

  // Projects
  async createProject(data: { name: string; description?: string }) {
    return this.request('/api/v1/projects/', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getProjects() {
    return this.request('/api/v1/projects/')
  }

  async getProject(id: string) {
    return this.request(`/api/v1/projects/${id}`)
  }

  async updateProject(id: string, data: Partial<{ name: string; description?: string }>) {
    return this.request(`/api/v1/projects/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async deleteProject(id: string) {
    return this.request(`/api/v1/projects/${id}`, {
      method: 'DELETE',
    })
  }

  // Documents
  async uploadDocument(projectId: string, file: File) {
    const formData = new FormData()
    formData.append('file', file)

    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/documents/upload`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Unknown error' }))
      throw new Error(error.message || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async addUrlDocument(projectId: string, url: string) {
    return this.request(`/api/v1/projects/${projectId}/documents/url`, {
      method: 'POST',
      body: JSON.stringify({ url }),
    })
  }

  async addTextDocument(projectId: string, text: string, filename: string) {
    const formData = new FormData()
    formData.append('text', text)
    formData.append('filename', filename)

    const response = await fetch(`${this.baseUrl}/api/v1/projects/${projectId}/documents/text`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Unknown error' }))
      throw new Error(error.message || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async getProjectDocuments(projectId: string) {
    return this.request(`/api/v1/projects/${projectId}/documents`)
  }

  // Content Sources
  async addUrl(data: { project_id: string; url: string }) {
    return this.request('/api/v1/sources/url', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async uploadPdf(data: { project_id: string; file: File }) {
    const formData = new FormData()
    formData.append('project_id', data.project_id)
    formData.append('file', data.file)

    const response = await fetch(`${this.baseUrl}/api/v1/sources/pdf`, {
      method: 'POST',
      body: formData,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ message: 'Unknown error' }))
      throw new Error(error.message || `HTTP ${response.status}`)
    }

    return response.json()
  }

  async getSource(id: string) {
    return this.request(`/api/v1/sources/${id}`)
  }

  async getSourceContent(id: string) {
    return this.request(`/api/v1/sources/${id}/content`)
  }

  // Scripts
  async generateScript(data: { project_id: string; content_source_id?: string; template?: string }) {
    return this.request('/api/v1/scripts/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getScripts(projectId: string) {
    return this.request(`/api/v1/scripts/project/${projectId}`)
  }

  async getScript(id: string) {
    return this.request(`/api/v1/scripts/${id}`)
  }

  async updateScript(id: string, data: { content: string }) {
    return this.request(`/api/v1/scripts/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
  }

  async getScriptTemplates() {
    return this.request('/api/v1/scripts/templates')
  }

  // Videos
  async generateVideo(data: { project_id: string; script_id?: string; title: string }) {
    return this.request('/api/v1/videos/generate', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getVideos(projectId: string) {
    return this.request(`/api/v1/videos/project/${projectId}`)
  }

  async getVideo(id: string) {
    return this.request(`/api/v1/videos/${id}`)
  }

  async getVideoStatus(id: string) {
    return this.request(`/api/v1/videos/${id}/status`)
  }

  async estimateVideoCost(data: { duration: number; provider: string }) {
    return this.request('/api/v1/videos/estimate-cost', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }
}

export const api = new ApiClient()