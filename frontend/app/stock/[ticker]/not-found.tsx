import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-text-primary mb-2">Ticker Not Found</h1>
        <p className="text-text-secondary mb-6">This ticker may not exist or is unavailable.</p>
        <Link href="/" className="px-6 py-2.5 bg-brand text-white rounded-lg text-sm font-medium">
          Back to Search
        </Link>
      </div>
    </div>
  )
}
