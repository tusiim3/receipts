export default function SpendSummary({ totalMonthly, currency, subscriptionCount }) {
  return (
    <div className="bg-indigo-600 rounded-lg p-6 text-white">
      <p className="text-indigo-200 text-sm">Estimated Monthly Spend</p>
      <p className="text-3xl font-bold mt-1">
        {currency} {totalMonthly?.toFixed(2) ?? '0.00'}
      </p>
      <p className="text-indigo-200 text-sm mt-2">
        {subscriptionCount} active subscription{subscriptionCount !== 1 ? 's' : ''}
      </p>
    </div>
  )
}
