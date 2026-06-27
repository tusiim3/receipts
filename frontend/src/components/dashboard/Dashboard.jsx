import { useEffect, useState } from 'react'
import api from '../../api'
import Layout from '../Layout'
import SpendSummary from './SpendSummary'
import SubscriptionCard from './SubscriptionCard'

export default function Dashboard() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const { data } = await api.get('/intelligence/summary')
        setSummary(data)
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to load dashboard')
      } finally {
        setLoading(false)
      }
    }
    fetchSummary()
  }, [])

  if (loading) {
    return (
      <Layout>
        <div className="text-center text-gray-500 py-12">Loading dashboard...</div>
      </Layout>
    )
  }

  if (error) {
    return (
      <Layout>
        <div className="text-center text-red-600 py-12">{error}</div>
      </Layout>
    )
  }

  const subscriptions = summary?.subscriptions || []
  const forgottenServices = new Set(
    (summary?.wasteful_flags || [])
      .filter((f) => f.type === 'possibly_forgotten')
      .flatMap((f) => f.services)
  )

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <SpendSummary
          totalMonthly={summary?.total_monthly_spend}
          currency={summary?.currency || 'USD'}
          subscriptionCount={subscriptions.length}
        />
      </div>

      {subscriptions.length === 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 p-8 text-center">
          <p className="text-gray-500 mb-4">No subscriptions found yet.</p>
          <p className="text-sm text-gray-400">
            Connect your Gmail to scan for subscriptions, or analyze terms of service.
          </p>
        </div>
      ) : (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Your Subscriptions</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {subscriptions.map((sub, i) => (
              <SubscriptionCard
                key={i}
                subscription={sub}
                forgotten={forgottenServices.has(sub.service_name)}
              />
            ))}
          </div>
        </div>
      )}
    </Layout>
  )
}
