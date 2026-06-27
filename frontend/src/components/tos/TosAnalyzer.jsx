import { useState } from 'react'
import api from '../../api'
import Layout from '../Layout'
import TosResultCard from './TosResultCard'

export default function TosAnalyzer() {
  const [url, setUrl] = useState('')
  const [pdfFile, setPdfFile] = useState(null)
  const [imageFile, setImageFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [results, setResults] = useState(null)

  const handleAnalyze = async () => {
    setError('')
    setResults(null)
    setLoading(true)

    try {
      let data

      if (url.trim()) {
        const response = await api.post('/tos/analyze-url', { url: url.trim() })
        data = response.data
      } else if (pdfFile || imageFile) {
        const formData = new FormData()
        formData.append('file', pdfFile || imageFile)
        const response = await api.post('/tos/analyze-file', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        })
        data = response.data
      } else {
        setError('Please provide a URL, PDF, or screenshot to analyze.')
        setLoading(false)
        return
      }

      setResults(data)
    } catch (err) {
      setError(err.response?.data?.message || 'Analysis failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Layout>
      <h1 className="text-2xl font-bold text-gray-900 mb-2">Terms of Service Analyzer</h1>
      <p className="text-gray-500 mb-6">
        Paste a URL, upload a PDF, or share a screenshot to find financial traps before you sign.
      </p>

      <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6 space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">URL</label>
          <input
            type="url"
            value={url}
            onChange={(e) => { setUrl(e.target.value); setPdfFile(null); setImageFile(null) }}
            placeholder="https://example.com/terms"
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">PDF Upload</label>
            <input
              type="file"
              accept=".pdf"
              onChange={(e) => { setPdfFile(e.target.files[0]); setUrl(''); setImageFile(null) }}
              className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-indigo-50 file:text-indigo-700"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Screenshot Upload</label>
            <input
              type="file"
              accept=".png,.jpg,.jpeg,.webp"
              onChange={(e) => { setImageFile(e.target.files[0]); setUrl(''); setPdfFile(null) }}
              className="w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:bg-indigo-50 file:text-indigo-700"
            />
          </div>
        </div>

        <button
          onClick={handleAnalyze}
          disabled={loading}
          className="px-6 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Reading the fine print...' : 'Analyze'}
        </button>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 text-red-700 rounded text-sm">{error}</div>
      )}

      {results && (
        <div>
          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
            <p className="font-medium text-amber-900">Risk Summary</p>
            <p className="text-amber-800 text-sm mt-1">{results.risk_summary}</p>
          </div>

          {results.flags?.length === 0 ? (
            <p className="text-gray-500">No financial risk flags found.</p>
          ) : (
            <div className="space-y-4">
              {results.flags.map((flag, i) => (
                <TosResultCard key={i} flag={flag} />
              ))}
            </div>
          )}
        </div>
      )}
    </Layout>
  )
}
