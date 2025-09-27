'use client'

import { useEffect, useState } from 'react'

// Force dynamic rendering to avoid Supabase client issues during build
export const dynamic = 'force-dynamic'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Plus, FolderOpen, Calendar, FileText, Upload, Link as LinkIcon, File, X } from 'lucide-react'
import { useSupabase } from '@/components/providers/SupabaseProvider'
import { api } from '@/lib/api'

interface Project {
  id: string
  name: string
  description?: string
  status: string
  created_at: string
  updated_at: string
  user_id: string
  document_count?: number
}

export default function ProjectsPage() {
  const { user } = useSupabase()
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [selectedProject, setSelectedProject] = useState<Project | null>(null)
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    url: '',
    text: '',
    filename: '',
  })
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [uploadType, setUploadType] = useState<'file' | 'url' | 'text'>('file')

  useEffect(() => {
    if (user) {
      loadProjects()
    }
  }, [user])

  const loadProjects = async () => {
    try {
      const data = await api.getProjects()
      setProjects(data)
    } catch (error) {
      console.error('Error loading projects:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateProject = async () => {
    try {
      await api.createProject({
        name: formData.name,
        description: formData.description,
      })
      setShowCreateModal(false)
      setFormData({ name: '', description: '', url: '', text: '', filename: '' })
      loadProjects()
    } catch (error) {
      console.error('Error creating project:', error)
    }
  }

  const handleUploadDocument = async () => {
    if (!selectedProject) return

    try {
      if (uploadType === 'file' && selectedFile) {
        await api.uploadDocument(selectedProject.id, selectedFile)
      } else if (uploadType === 'url') {
        await api.addUrlDocument(selectedProject.id, formData.url)
      } else if (uploadType === 'text') {
        await api.addTextDocument(selectedProject.id, formData.text, formData.filename || 'document.txt')
      }

      setShowUploadModal(false)
      setSelectedProject(null)
      setFormData({ name: '', description: '', url: '', text: '', filename: '' })
      setSelectedFile(null)
      loadProjects()
    } catch (error) {
      console.error('Error uploading document:', error)
    }
  }

  const openUploadModal = (project: Project) => {
    setSelectedProject(project)
    setShowUploadModal(true)
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="notebook-header">Projects</h1>
          <p className="notebook-text">Manage your research paper analysis projects</p>
        </div>
        <Button className="notebook-button-primary" onClick={() => setShowCreateModal(true)}>
          <Plus className="mr-2 h-4 w-4" />
          New Project
        </Button>
      </div>

      {/* Projects Grid */}
      {projects.length === 0 ? (
        <Card className="notebook-card text-center py-12">
          <CardContent>
            <FolderOpen className="mx-auto h-12 w-12 text-gray-400 mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No projects yet</h3>
            <p className="text-gray-600 mb-4">
              Create your first project to start analyzing research papers
            </p>
            <Button className="notebook-button-primary" onClick={() => setShowCreateModal(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create Project
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <Card key={project.id} className="notebook-card hover:shadow-lg transition-shadow">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FolderOpen className="h-5 w-5 text-blue-600" />
                  {project.name}
                </CardTitle>
                <CardDescription>
                  {project.description || 'No description'}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <div className="flex items-center gap-1">
                      <FileText className="h-4 w-4" />
                      <span>{project.document_count || 0} documents</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Calendar className="h-3 w-3" />
                    <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
                  </div>

                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" className="flex-1" onClick={() => openUploadModal(project)}>
                      <Upload className="mr-1 h-3 w-3" />
                      Upload
                    </Button>
                    <Button variant="outline" size="sm">
                      View
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Recent Activity */}
      <Card className="notebook-card">
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest updates across all projects</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center gap-3 py-2">
              <div className="w-2 h-2 bg-green-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">Paper processing completed</p>
                <p className="text-xs text-gray-500">Attention Is All You Need • 2 minutes ago</p>
              </div>
              <Badge variant="secondary">Completed</Badge>
            </div>

            <div className="flex items-center gap-3 py-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">Script generation started</p>
                <p className="text-xs text-gray-500">BERT Analysis • 5 minutes ago</p>
              </div>
              <Badge variant="outline">Processing</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Create Project Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Create New Project</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowCreateModal(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">Project Name</label>
                <Input
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="Enter project name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Description (Optional)</label>
                <Textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="Enter project description"
                  rows={3}
                />
              </div>
              <div className="flex gap-2 pt-4">
                <Button onClick={handleCreateProject} className="flex-1">
                  Create Project
                </Button>
                <Button variant="outline" onClick={() => setShowCreateModal(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Upload Document Modal */}
      {showUploadModal && selectedProject && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold">Upload Document to {selectedProject.name}</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowUploadModal(false)}>
                <X className="h-4 w-4" />
              </Button>
            </div>
            <div className="space-y-4">
              <div className="flex gap-2">
                <Button
                  variant={uploadType === 'file' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setUploadType('file')}
                >
                  <File className="mr-1 h-3 w-3" />
                  File
                </Button>
                <Button
                  variant={uploadType === 'url' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setUploadType('url')}
                >
                  <LinkIcon className="mr-1 h-3 w-3" />
                  URL
                </Button>
                <Button
                  variant={uploadType === 'text' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setUploadType('text')}
                >
                  <FileText className="mr-1 h-3 w-3" />
                  Text
                </Button>
              </div>

              {uploadType === 'file' && (
                <div>
                  <label className="block text-sm font-medium mb-1">Select File</label>
                  <Input
                    type="file"
                    accept=".pdf,.txt,.docx,.md"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  />
                </div>
              )}

              {uploadType === 'url' && (
                <div>
                  <label className="block text-sm font-medium mb-1">URL</label>
                  <Input
                    value={formData.url}
                    onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                    placeholder="https://example.com/paper.pdf"
                  />
                </div>
              )}

              {uploadType === 'text' && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium mb-1">Filename</label>
                    <Input
                      value={formData.filename}
                      onChange={(e) => setFormData({ ...formData, filename: e.target.value })}
                      placeholder="document.txt"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Text Content</label>
                    <Textarea
                      value={formData.text}
                      onChange={(e) => setFormData({ ...formData, text: e.target.value })}
                      placeholder="Paste your research paper text here..."
                      rows={6}
                    />
                  </div>
                </div>
              )}

              <div className="flex gap-2 pt-4">
                <Button onClick={handleUploadDocument} className="flex-1">
                  Upload Document
                </Button>
                <Button variant="outline" onClick={() => setShowUploadModal(false)}>
                  Cancel
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}