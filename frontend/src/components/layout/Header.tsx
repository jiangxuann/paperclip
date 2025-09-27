'use client'

import Link from 'next/link'
import { useState } from 'react'
import { BookOpen, Settings, User, LogIn, LogOut } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { AuthModal } from '@/components/auth/AuthModal'
import { useSupabase } from '@/components/providers/SupabaseProvider'

export function Header() {
  const { user, signOut } = useSupabase()
  const [showAuthModal, setShowAuthModal] = useState(false)

  const handleSignOut = async () => {
    await signOut()
  }

  return (
    <>
      <header className="border-b bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
        <div className="container mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2">
            <BookOpen className="h-6 w-6 text-blue-600" />
            <span className="font-semibold text-lg">Paperclip</span>
          </Link>

          <nav className="hidden md:flex items-center space-x-6">
            <Link
              href="/papers"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Papers
            </Link>
            <Link
              href="/projects"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Projects
            </Link>
            <Link
              href="/scripts"
              className="text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Scripts
            </Link>
          </nav>

          <div className="flex items-center space-x-2">
            <Button variant="ghost" size="sm">
              <Settings className="h-4 w-4" />
            </Button>
            {user ? (
              <div className="flex items-center space-x-2">
                <span className="text-sm text-gray-600 hidden sm:block">
                  {user.email}
                </span>
                <Button variant="ghost" size="sm" onClick={handleSignOut}>
                  <LogOut className="h-4 w-4" />
                </Button>
              </div>
            ) : (
              <Button variant="ghost" size="sm" onClick={() => setShowAuthModal(true)}>
                <LogIn className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>
      </header>

      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </>
  )
}