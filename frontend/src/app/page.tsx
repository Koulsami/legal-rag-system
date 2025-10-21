import Link from 'next/link'

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
      <div className="max-w-4xl mx-auto px-6 text-center">
        <h1 className="text-5xl font-bold text-gray-900 mb-4">
          Myk Raws Legal AI
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          Singapore Statutory Interpretation Assistant
        </p>
        <Link 
          href="/ask"
          className="inline-flex items-center gap-2 bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition-colors"
        >
          Start Asking Questions
        </Link>
      </div>
    </div>
  )
}
