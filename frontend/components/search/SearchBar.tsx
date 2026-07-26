'use client'

import { useState, useRef, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Search, X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { stockApi } from '@/lib/api'

export default function SearchBar({ compact = false }: { compact?: boolean }) {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const { data: results } = useQuery({
    queryKey: ['search', query],
    queryFn: () => stockApi.search(query),
    enabled: query.length >= 1,
    staleTime: 30_000,
  })

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const navigate = (ticker: string) => {
    setQuery('')
    setOpen(false)
    router.push(`/stock/${ticker.toUpperCase()}`)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && query.trim()) navigate(query.trim())
    if (e.key === 'Escape') setOpen(false)
  }

  return (
    <div ref={ref} className="relative w-full">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
        <input
          type="text"
          value={query}
          onChange={(e) => { setQuery(e.target.value); setOpen(true) }}
          onFocus={() => setOpen(true)}
          onKeyDown={handleKeyDown}
          placeholder={compact ? "Search ticker..." : "Search ticker or company..."}
          className={`w-full bg-bg-card border border-bg-border rounded-lg pl-9 pr-8 font-mono text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-brand/40 transition-colors ${compact ? 'py-1.5 text-xs' : 'py-2.5'}`}
        />
        {query && (
          <button
            onClick={() => { setQuery(''); setOpen(false) }}
            className="absolute right-2 top-1/2 -translate-y-1/2 p-0.5 text-text-muted hover:text-text-secondary"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {open && query && results?.results && results.results.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-bg-card border border-bg-border rounded-lg shadow-2xl z-50 overflow-hidden">
          {results.results.slice(0, 8).map((r) => (
            <button
              key={r.ticker}
              onClick={() => navigate(r.ticker)}
              className="w-full flex items-center justify-between px-4 py-2.5 hover:bg-bg-elevated transition-colors text-left"
            >
              <div className="flex items-center gap-3">
                <span className="font-mono font-semibold text-text-primary text-sm w-24">{r.ticker}</span>
                <span className="text-xs text-text-secondary truncate max-w-[160px]">{r.name}</span>
              </div>
              <span className="text-xs text-text-muted ml-2 flex-shrink-0">{r.exchange}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
