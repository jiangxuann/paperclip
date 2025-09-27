import { redirect } from 'next/navigation'

export default function AuthCallback() {
  // This page should redirect immediately, no client-side logic needed
  redirect('/')
}