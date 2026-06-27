const SEVERITY_STYLES = {
  high: 'bg-red-100 text-red-800 border-red-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  low: 'bg-green-100 text-green-800 border-green-200',
}

export default function TosResultCard({ flag }) {
  const { flag_title, severity, explanation, exact_quote } = flag
  const style = SEVERITY_STYLES[severity] || SEVERITY_STYLES.low

  return (
    <div className="bg-white rounded-lg border border-gray-200 p-5">
      <div className="flex items-start justify-between mb-3">
        <h3 className="font-semibold text-gray-900">{flag_title}</h3>
        <span className={`text-xs px-2 py-1 rounded-full border ${style}`}>
          {severity}
        </span>
      </div>
      <p className="text-gray-600 text-sm mb-3">{explanation}</p>
      {exact_quote && (
        <blockquote className="text-xs text-gray-500 border-l-2 border-gray-300 pl-3 italic">
          "{exact_quote}"
        </blockquote>
      )}
    </div>
  )
}
