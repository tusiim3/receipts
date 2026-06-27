import { useEffect, useState } from 'react'
import api from '../../api'
import Layout from '../Layout'
import SpendSummary from '../dashboard/SpendSummary'
import SubscriptionCard from '../dashboard/SubscriptionCard'

export default function CostIntelligencePage() {
  const [summary, setSummary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [alternatives, setAlternatives] = useState({})
  const [sentiments, setSentiments] = useState({})
  const [loadingAlt, setLoadingAlt] = useState({})
  const [loadingSent, setLoadingSent] = useState({})

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const { data } = await api.get('/intelligence/summary')
        setSummary(data)
      } catch (err) {
        setError(err.response?.data?.message || 'Failed to load intelligence data')
      } finally {
        setLoading(false)
      }
    }
    fetchSummary()
  }, [])

  const loadAlternatives = async (sub) => {
    const key = sub.service_name
    if (alternatives[key] || loadingAlt[key]) return

    setLoadingAlt((prev) => ({ ...prev, [key]: true }))
    try {
      const { data } = await api.post('/intelligence/alternatives', {
        service_name: sub.service_name,
        current_amount: sub.amount || 0,
        currency: sub.currency || 'USD',
        frequency: sub.frequency || 'monthly',
      })
      setAlternatives((prev) => ({ ...prev, [key]: data.alternatives }))
    } catch {
      setAlternatives((prev) => ({ ...prev, [key]: [] }))
    } finally {
      setLoadingAlt((prev) => ({ ...prev, [key]: false }))
    }
  }

  const loadSentiment = async (serviceName) => {
    if (sentiments[serviceName] || loadingSent[serviceName]) return

    setLoadingSent((prev) => ({ ...prev, [serviceName]: true }))
    try {
      const { data } = await api.post('/intelligence/sentiment', {
        service_name: serviceName,
      })
      setSentiments((prev) => ({ ...prev, [serviceName]: data }))
    } catch {
      setSentiments((prev) => ({ ...prev, [serviceName]: null }))
    } finally {
      setLoadingSent((prev) => ({ ...prev, [serviceName]: false }))
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="text-center text-gray-500 py-12">Loading intelligence...</div>
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
  const wastefulFlags = summary?.wasteful_flags || []
  const forgottenServices = new Set(
    wastefulFlags.filter((f) => f.type === 'possibly_forgotten').flatMap((f) => f.services)
  )

  const flaggedSubs = subscriptions.filter(
    (sub) =>
      forgottenServices.has(sub.service_name) ||
      wastefulFlags.some((f) => f.services?.includes(sub.service_name))
  )

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Cost Intelligence</h1>

      {/* Section 1: Subscription Map */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Subscription Map</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <SpendSummary
            totalMonthly={summary?.total_monthly_spend}
            currency={summary?.currency || 'USD'}
            subscriptionCount={subscriptions.length}
          />
        </div>

        {Object.entries(summary?.grouped_by_category || {}).map(([category, subs]) => (
          <div key={category} className="mb-6">
            <h3 className="text-sm font-medium text-gray-500 uppercase mb-3">
              {category.replace('_', ' ')}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {subs.map((sub, i) => (
                <SubscriptionCard
                  key={i}
                  subscription={sub}
                  forgotten={forgottenServices.has(sub.service_name)}
                />
              ))}
            </div>
          </div>
        ))}
      </section>

      {/* Section 2: Wasteful Spend Flags */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Wasteful Spend Flags</h2>
        {wastefulFlags.length === 0 ? (
          <p className="text-gray-500 text-sm">No wasteful spend detected.</p>
        ) : (
          <div className="space-y-3">
            {wastefulFlags.map((flag, i) => (
              <div key={i} className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="text-amber-900 text-sm font-medium">{flag.message}</p>
                {flag.services?.length > 0 && (
                  <p className="text-amber-700 text-xs mt-1">{flag.services.join(', ')}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Section 3: Alternatives & Savings */}
      <section className="mb-10">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Alternatives & Savings</h2>
        {(flaggedSubs.length > 0 ? flaggedSubs : subscriptions).slice(0, 5).map((sub) => (
          <div key={sub.service_name} className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-medium text-gray-900">{sub.service_name}</h3>
              <button
                onClick={() => loadAlternatives(sub)}
                disabled={loadingAlt[sub.service_name]}
                className="text-sm text-indigo-600 hover:underline disabled:opacity-50"
              >
                {loadingAlt[sub.service_name] ? 'Searching...' : 'Find alternatives'}
              </button>
            </div>
            {alternatives[sub.service_name]?.map((alt, i) => (
              <div key={i} className="border-t border-gray-100 pt-3 mt-3 first:border-0 first:pt-0 first:mt-0">
                <p className="font-medium text-sm">{alt.name}</p>
                <p className="text-sm text-green-600">{alt.estimated_monthly_cost}</p>
                <p className="text-xs text-gray-500 mt-1">{alt.key_difference}</p>
                {alt.source_url && (
                  <a
                    href={alt.source_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-indigo-600 hover:underline mt-1 inline-block"
                  >
                    Source
                  </a>
                )}
              </div>
            ))}
          </div>
        ))}
      </section>

      {/* Section 4: Platform Sentiment */}
      <section>
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Platform Sentiment</h2>
        {subscriptions.slice(0, 5).map((sub) => (
          <div key={sub.service_name} className="bg-white rounded-lg border border-gray-200 p-4 mb-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-medium text-gray-900">{sub.service_name}</h3>
              <button
                onClick={() => loadSentiment(sub.service_name)}
                disabled={loadingSent[sub.service_name]}
                className="text-sm text-indigo-600 hover:underline disabled:opacity-50"
              >
                {loadingSent[sub.service_name] ? 'Loading...' : 'Get sentiment'}
              </button>
            </div>
            {sentiments[sub.service_name] && (
              <div>
                <span className={`text-xs px-2 py-1 rounded-full ${
                  sentiments[sub.service_name].sentiment === 'positive'
                    ? 'bg-green-100 text-green-800'
                    : sentiments[sub.service_name].sentiment === 'negative'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-yellow-100 text-yellow-800'
                }`}>
                  {sentiments[sub.service_name].sentiment}
                </span>
                <p className="text-sm text-gray-600 mt-2">{sentiments[sub.service_name].summary}</p>
                {sentiments[sub.service_name].sources?.length > 0 && (
                  <p className="text-xs text-gray-400 mt-1">
                    Sources: {sentiments[sub.service_name].sources.join(', ')}
                  </p>
                )}
              </div>
            )}
          </div>
        ))}
      </section>
    </Layout>
  )
}
