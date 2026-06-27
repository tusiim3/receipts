const CATEGORY_COLORS = {
  streaming: 'bg-purple-100 text-purple-800',
  music: 'bg-pink-100 text-pink-800',
  productivity: 'bg-blue-100 text-blue-800',
  cloud_storage: 'bg-cyan-100 text-cyan-800',
  gaming: 'bg-green-100 text-green-800',
  food_delivery: 'bg-orange-100 text-orange-800',
  fitness: 'bg-red-100 text-red-800',
  news: 'bg-yellow-100 text-yellow-800',
  education: 'bg-indigo-100 text-indigo-800',
  finance: 'bg-emerald-100 text-emerald-800',
  communication: 'bg-teal-100 text-teal-800',
  utilities: 'bg-gray-100 text-gray-800',
  other: 'bg-gray-100 text-gray-600',
}

export default function SubscriptionCard({ subscription, forgotten = false }) {
  const {
    service_name,
    amount,
    currency,
    frequency,
    last_charge_date,
    category,
    is_trial,
    trial_end_date,
  } = subscription

  const categoryClass = CATEGORY_COLORS[category] || CATEGORY_COLORS.other

  return (
    <div className={`bg-white rounded-lg border p-4 ${forgotten ? 'border-amber-300 bg-amber-50' : 'border-gray-200'}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center text-indigo-600 font-bold">
            {service_name?.charAt(0)?.toUpperCase() || '?'}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{service_name}</h3>
            <p className="text-sm text-gray-500">
              {amount != null ? `${currency || ''} ${amount}` : 'Amount unknown'}
              {frequency && ` / ${frequency}`}
            </p>
          </div>
        </div>
        {category && (
          <span className={`text-xs px-2 py-1 rounded-full ${categoryClass}`}>
            {category.replace('_', ' ')}
          </span>
        )}
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs text-gray-500">
        {last_charge_date && <span>Last charge: {last_charge_date.split('T')[0]}</span>}
        {is_trial && trial_end_date && (
          <span className="text-amber-600">Trial ends: {trial_end_date.split('T')[0]}</span>
        )}
        {forgotten && <span className="text-amber-600 font-medium">Possibly forgotten</span>}
      </div>
    </div>
  )
}
