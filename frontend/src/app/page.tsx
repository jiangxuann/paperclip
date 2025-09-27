'use client'

import { useState } from 'react'

// Force dynamic rendering to avoid Supabase client issues during build
export const dynamic = 'force-dynamic'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { BookOpen, Link as LinkIcon, ArrowRight, CheckCircle, Clock, AlertCircle, LogIn } from 'lucide-react'
import { api } from '@/lib/api'
import { useSupabase } from '@/components/providers/SupabaseProvider'
import { AuthModal } from '@/components/auth/AuthModal'

export default function HomePage() {
  const { user, loading } = useSupabase()
  const [url, setUrl] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [status, setStatus] = useState<'idle' | 'processing' | 'completed' | 'error'>('idle')
  const [result, setResult] = useState<{ project: { id: string; name: string }; source: { id: string } } | null>(null)
  const [showAuthModal, setShowAuthModal] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!url.trim()) return

    setIsProcessing(true)
    setStatus('processing')
    setProgress(0)

    try {
      // Simulate progress updates
      const progressInterval = setInterval(() => {
        setProgress(prev => Math.min(prev + 10, 90))
      }, 500)

      // Create a project first (in a real app, this would be handled differently)
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

    } catch (error) {
      console.error('Error processing URL:', error)
      setStatus('error')
      setProgress(0)
    } finally {
      setIsProcessing(false)
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-500 animate-pulse" />
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      default:
        return <BookOpen className="h-5 w-5 text-gray-400" />
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'processing':
        return 'Processing your research paper...'
      case 'completed':
        return 'Paper processed successfully!'
      case 'error':
        return 'Error processing paper. Please try again.'
      default:
        return 'Ready to process your research paper'
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return (
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Hero Section */}
        <div className="text-center space-y-4">
          <h1 className="notebook-header">
            Transform Research Papers into Insights
          </h1>
          <p className="notebook-text text-xl max-w-2xl mx-auto">
            Paste a research paper URL and let AI extract key insights, generate summaries,
            and create engaging video content from academic research.
          </p>
        </div>

        {/* Sign In Prompt */}
        <Card className="notebook-card max-w-md mx-auto text-center">
          <CardHeader>
            <CardTitle>Get Started</CardTitle>
            <CardDescription>
              Sign in to start processing research papers with AI
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={() => setShowAuthModal(true)}
              className="notebook-button-primary w-full"
            >
              <LogIn className="mr-2 h-4 w-4" />
              Sign In
            </Button>
          </CardContent>
        </Card>

        <AuthModal
          isOpen={showAuthModal}
          onClose={() => setShowAuthModal(false)}
        />
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Hero Section */}
      <div className="text-center space-y-4">
        <h1 className="notebook-header">
          Transform Research Papers into Insights
        </h1>
        <p className="notebook-text text-xl max-w-2xl mx-auto">
          Paste a research paper URL and let AI extract key insights, generate summaries,
          and create engaging video content from academic research.
        </p>
      </div>

      {/* Main Input Card */}
      <Card className="notebook-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getStatusIcon()}
            {getStatusText()}
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
                disabled={!url.trim() || isProcessing}
                className="notebook-button-primary"
              >
                {isProcessing ? 'Processing...' : 'Analyze Paper'}
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
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

          {/* Status Messages */}
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
              <div className="mt-3 flex gap-2">
                <Button variant="outline" size="sm">
                  View Project
                </Button>
                <Button variant="outline" size="sm">
                  Generate Summary
                </Button>
              </div>
            </div>
          )}

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

      {/* Feature Overview */}
      <div className="grid md:grid-cols-3 gap-6">
        <Card className="notebook-card">
          <CardHeader>
            <CardTitle className="text-lg">Content Extraction</CardTitle>
            <CardDescription>
              Automatically extract text, figures, and metadata from research papers
            </CardDescription>
          </CardHeader>
        </Card>

        <Card className="notebook-card">
          <CardHeader>
            <CardTitle className="text-lg">AI-Powered Analysis</CardTitle>
            <CardDescription>
              Generate summaries, key insights, and structured analysis using advanced AI
            </CardDescription>
          </CardHeader>
        </Card>

        <Card className="notebook-card">
          <CardHeader>
            <CardTitle className="text-lg">Video Generation</CardTitle>
            <CardDescription>
              Create engaging video content from your research with AI narration
            </CardDescription>
          </CardHeader>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card className="notebook-card">
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>
            Your latest research paper processing jobs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <div>
                  <p className="font-medium text-sm">Attention Is All You Need</p>
                  <p className="text-xs text-gray-500">Processed 2 minutes ago</p>
                </div>
              </div>
              <Badge variant="secondary">Completed</Badge>
            </div>

            <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                <div>
                  <p className="font-medium text-sm">BERT: Pre-training of Deep Bidirectional Transformers</p>
                  <p className="text-xs text-gray-500">Processing...</p>
                </div>
              </div>
              <Badge variant="outline">Processing</Badge>
            </div>
          </div>
        </CardContent>
      </Card>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </div>
  )
}
