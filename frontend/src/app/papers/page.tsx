'use client'

import { useState, useEffect } from 'react'

// Force dynamic rendering to avoid Supabase client issues during build
export const dynamic = 'force-dynamic'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { BookOpen, ArrowRight, CheckCircle, Clock, AlertCircle, ExternalLink, FileText, Calendar } from 'lucide-react'
import { api } from '@/lib/api'
import { useSupabase } from '@/components/providers/SupabaseProvider'

interface ProcessedPaper {
  id: string
  url: string
  title?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  created_at: string
  project_id: string
  project_name: string
}

export default function PapersPage() {
  const { user } = useSupabase()
  const [url, setUrl] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle')
  const [result, setResult] = useState<{ project: { id: string; name: string }; source: { id: string } } | null>(null)
  const [papers, setPapers] = useState<ProcessedPaper[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (user) {
      loadPapers()
    }
  }, [user])

  const loadPapers = async () => {
    try {
      // In a real implementation, this would fetch from the API
      // For now, we'll show mock data
      setPapers([
        {
          id: '1',
          url: 'https://arxiv.org/pdf/2301.12345.pdf',
          title: 'Attention Is All You Need',
          status: 'completed',
          created_at: new Date().toISOString(),
          project_id: '1',
          project_name: 'Transformer Research'
        },
        {
          id: '2',
          url: 'https://arxiv.org/pdf/2302.67890.pdf',
          title: 'BERT: Pre-training of Deep Bidirectional Transformers',
          status: 'processing',
          created_at: new Date().toISOString(),
          project_id: '2',
          project_name: 'Language Models'
        }
      ])
    } catch (error) {
      console.error('Error loading papers:', error)
    } finally {
      setLoading(false)
    }
  }

  const validateUrl = (url: string) => {
    try {
      const parsedUrl = new URL(url)
      return parsedUrl.protocol === 'http:' || parsedUrl.protocol === 'https:'
    } catch {
      return false
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim() || !validateUrl(url.trim())) return

    setIsProcessing(true)
    setStatus('processing')
    setProgress(0)

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90))
      }, 500)

      // Create a project first
      const project = await api.createProject({
        name: `Research Paper - ${new Date().toLocaleDateString()}`,
        description: `Analysis of ${url}`
      })

      // Add the URL as a content source
      const source = await api.addUrl({
        project_id: project.id,
        url: url.trim()
      })

      clearInterval(progressInterval)
      setProgress(100)
      setStatus('completed')
      setResult({ project, source })

      // Reload papers list
      await loadPapers()

    } catch (error) {
      console.error('Error processing URL:', error)
      setStatus('error')
      setProgress(0)
    } finally {
      setIsProcessing(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'processing':
        return <Clock className="h-4 w-4 text-blue-500 animate-pulse" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <AlertCircle className="h-4 w-4 text-red-500" />
      default:
        return <BookOpen className="h-4 w-4 text-gray-400" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'processing':
        return <Badge variant="outline">Processing</Badge>
      case 'completed':
        return <Badge variant="secondary">Completed</Badge>
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>
      default:
        return <Badge variant="outline">Pending</Badge>
    }
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-4">
        <h1 className="notebook-header">Research Papers</h1>
        <p className="notebook-text text-xl max-w-2xl mx-auto">
          Add research paper URLs for AI-powered analysis and content generation
        </p>
      </div>

      {/* URL Input Card */}
      <Card className="notebook-card max-w-2xl mx-auto">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getStatusIcon(status)}
            {status === 'processing' ? 'Processing your research paper...' :
             status === 'completed' ? 'Paper processed successfully!' :
             status === 'error' ? 'Error processing paper. Please try again.' :
             'Add Research Paper URL'}
          </CardTitle>
          <CardDescription>
            Enter the URL of a research paper (PDF or web page) to begin analysis
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="flex gap-2">
              <div className="flex-1">
                <Input
                  type="url"
                  placeholder="https://arxiv.org/pdf/2301.12345.pdf"
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  disabled={isProcessing}
                  className="text-base"
                />
              </div>
              <Button
                type="submit"
                disabled={!url.trim() || !validateUrl(url.trim()) || isProcessing}
                className="notebook-button-primary"
              >
                {isProcessing ? 'Processing...' : 'Analyze Paper'}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
            {!validateUrl(url) && url && (
              <p className="text-sm text-red-600">Please enter a valid URL</p>
            )}
          </form>

          {/* Progress Bar */}
          {isProcessing && (
            <div className="space-y-2">
              <Progress value={progress} className="w-full" />
              <p className="text-sm text-gray-600 text-center">
                {progress}% complete
              </p>
            </div>
          )}

          {/* Success Message */}
          {status === 'completed' && result && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle className="h-5 w-5 text-green-500" />
                <span className="font-medium text-green-800">Success!</span>
              </div>
              <p className="text-green-700 text-sm">
                {`Your paper has been added to project "${result.project.name}".`}
                The system is now extracting content and generating embeddings.
              </p>
            </div>
          )}

          {/* Error Message */}
          {status === 'error' && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertCircle className="h-5 w-5 text-red-500" />
                <span className="font-medium text-red-800">Error</span>
              </div>
              <p className="text-red-700 text-sm">
                There was an error processing your paper. Please check the URL and try again.
              </p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Processed Papers List */}
      <Card className="notebook-card">
        <CardHeader>
          <CardTitle>Processed Papers</CardTitle>
          <CardDescription>
            Your research papers and their processing status
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600"></div>
            </div>
          ) : papers.length === 0 ? (
            <div className="text-center py-8">
              <BookOpen className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No papers processed yet</h3>
              <p className="text-gray-600">
                Add your first research paper URL above to get started
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {papers.map((paper) => (
                <div key={paper.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-3 flex-1">
                    {getStatusIcon(paper.status)}
                    <div className="flex-1">
                      <h4 className="font-medium text-gray-900">
                        {paper.title || 'Untitled Paper'}
                      </h4>
                      <div className="flex items-center gap-2 text-sm text-gray-600 mt-1">
                        <ExternalLink className="h-3 w-3" />
                        <a
                          href={paper.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="hover:text-blue-600 truncate max-w-md"
                        >
                          {paper.url}
                        </a>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-gray-500 mt-1">
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3 w-3" />
                          {new Date(paper.created_at).toLocaleDateString()}
                        </span>
                        <span>Project: {paper.project_name}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(paper.status)}
                    <Button variant="ghost" size="sm">
                      View Details
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}