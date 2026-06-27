import { useEffect, useState, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { auth } from '../../firebase'
import api from '../../api'
import Layout from '../Layout'
import SubscriptionCard from '../dashboard/SubscriptionCard'

export default function GmailConnect() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const [scanning, setScanning] = useState(false)
  const [scanResult, setScanResult] = useState(null)
  const [error, setError] = useState('')
  const scanTriggered = useRef(false)

  const connected = searchParams.get('connected') === 'true'
  const oauthError = searchParams.get('error')

  useEffect(() => {
    if (oauthError) {
      setError(`Gmail connection failed: ${oauthError}`)
    }
  }, [oauthError])

  useEffect(() => {
    if (connected && !scanTriggered.current) {
      scanTriggered.current = true
      runScan()
    }
  }, [connected])

  const runScan = async () => {
    setScanning(true)
    setError('')
    try {
      const { data } = await api.post('/gmail/scan')
      setScanResult(data)
      setTimeout(() => navigate('/dashboard'), 3000)
    } catch (err) {
      setError(err.response?.data?.message || 'Scan failed')
    } finally {
      setScanning(false)
    }
  }

  const handleConnect = async () => {
    setError('')
    try {
      const token = await auth.currentUser.getIdToken()
      const apiBase = import.meta.env.VITE_API_BASE_URL
      window.location.href = `${apiBase}/auth/gmail?token=${token}`
    } catch (err) {
      setError('Failed to start Gmail connection')
    }
  }

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Gmail Scanner</h1>
      <p className="text-gray-500 mb-6">
        Connect your Gmail to automatically find subscriptions, receipts, and trial notices.
      </p>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>
      )}

      {scanning && (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <div className="animate-pulse text-indigo-600 font-medium mb-2">
            Scanning your inbox...
          </div>
          <p className="text-sm text-gray-500">This may take a minute.</p>
        </div>
      )}

      {scanResult && !scanning && (
        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
          <p className="text-lg font-semibold text-green-700 mb-2">
            Found {scanResult.total_count} subscriptions across {scanResult.unique_services} services
          </p>
          <p className="text-sm text-gray-500 mb-4">Redirecting to dashboard...</p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {scanResult.subscriptions?.map((sub, i) => (
              <SubscriptionCard key={i} subscription={sub} />
            ))}
          </div>
        </div>
      )}

      {!scanning && !scanResult && (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <button
            onClick={handleConnect}
            className="px-6 py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 font-medium"
          >
            Connect Gmail
          </button>
          <p className="text-xs text-gray-400 mt-4">
            We only request read-only access to scan for billing emails.
          </p>
        </div>
      )}
    </Layout>
  )
}
