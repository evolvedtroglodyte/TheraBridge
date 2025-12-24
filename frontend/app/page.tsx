'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { demoApiClient } from '@/lib/demo-api-client'
import { demoTokenStorage } from '@/lib/demo-token-storage'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    const initializeDemo = async () => {
      // Check if demo token already exists
      const existingToken = demoTokenStorage.getToken()

      if (existingToken) {
        // Token exists, redirect to dashboard immediately
        console.log('✅ Demo token exists, redirecting to dashboard')
        router.push('/dashboard')
        return
      }

      // No token exists, create new demo user
      console.log('🚀 Initializing demo user...')

      try {
        const result = await demoApiClient.initialize()

        if (result) {
          // Token is automatically stored in localStorage by demoApiClient
          console.log('✅ Demo initialized:', result)

          // Redirect to dashboard
          router.push('/dashboard')
        } else {
          console.error('❌ Demo initialization failed: result is null')
          // Still redirect to dashboard (it will handle the error)
          router.push('/dashboard')
        }
      } catch (err) {
        console.error('❌ Demo initialization error:', err)
        // Still redirect to dashboard (it will handle the error)
        router.push('/dashboard')
      }
    }

    initializeDemo()
  }, [router])

  // Loading screen while initializing - matches dashboard aesthetic
  return (
    <div className="min-h-screen bg-[#ECEAE5] dark:bg-[#1a1625] transition-colors duration-300 flex items-center justify-center">
      <div className="text-center">
        <div className="mb-4">
          <svg className="animate-spin h-12 w-12 text-gray-700 dark:text-gray-300 mx-auto" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        </div>
        <h2 className="text-xl font-light text-gray-900 dark:text-gray-100 mb-2" style={{ fontFamily: 'system-ui' }}>
          Loading TherapyBridge
        </h2>
        <p className="text-sm font-light text-gray-600 dark:text-gray-400" style={{ fontFamily: 'system-ui' }}>
          Preparing your experience...
        </p>
      </div>
    </div>
  )
}
