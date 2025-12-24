'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { demoApiClient } from '@/lib/demo-api-client'
import { demoTokenStorage } from '@/lib/demo-token-storage'

export default function Home() {
  const router = useRouter()

  useEffect(() => {
    const initializeDemo = async () => {
      // STEP 1: Check if demo token already exists
      const existingToken = demoTokenStorage.getToken();
      const existingPatientId = demoTokenStorage.getPatientId();

      if (existingToken && existingPatientId) {
        // Token exists and is valid - redirect to dashboard
        console.log('✅ Demo token exists, redirecting to dashboard');
        console.log('   Patient ID:', existingPatientId);
        router.push('/dashboard');
        return;
      }

      // STEP 3: Check if initialization is already in progress
      const initStatus = demoTokenStorage.getInitStatus();

      if (initStatus === 'pending') {
        console.log('⏳ Demo initialization already in progress, waiting...');
        // Wait for initialization to complete (polling)
        const checkInterval = setInterval(() => {
          if (demoTokenStorage.isInitialized()) {
            console.log('✅ Initialization complete, redirecting...');
            clearInterval(checkInterval);
            router.push('/dashboard');
          }
        }, 500);

        // Timeout after 10 seconds
        setTimeout(() => {
          clearInterval(checkInterval);
          console.error('❌ Initialization timeout - restarting');
          demoTokenStorage.clear();
          window.location.reload();
        }, 10000);

        return;
      }

      // STEP 4: No token exists - create new demo user
      console.log('🚀 Initializing new demo user...');
      demoTokenStorage.markInitPending();

      try {
        const result = await demoApiClient.initialize();

        if (result) {
          // Token is automatically stored in localStorage by demoApiClient
          console.log('✅ Demo initialized:', result);
          console.log('   Patient ID:', result.patient_id);
          console.log('   Session count:', result.session_ids.length);

          // Verify storage worked
          const storedPatientId = demoTokenStorage.getPatientId();
          if (!storedPatientId) {
            throw new Error('Failed to store patient ID in localStorage');
          }

          // Redirect to dashboard
          router.push('/dashboard');
        } else {
          throw new Error('Demo initialization returned null');
        }
      } catch (err) {
        console.error('❌ Demo initialization error:', err);
        demoTokenStorage.clear();

        // Show error to user
        alert('Failed to initialize demo. Please refresh the page.');
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
