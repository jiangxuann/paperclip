'use client'

import { ReactNode } from 'react'
import { Header } from './Header'

interface NotebookLayoutProps {
  children: ReactNode
}

export function NotebookLayout({ children }: NotebookLayoutProps) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  )
}