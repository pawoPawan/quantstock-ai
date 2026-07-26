import type { Metadata } from 'next'
import './globals.css'
import QueryProvider from '@/components/providers/QueryProvider'
import { Toaster } from 'react-hot-toast'

export const metadata: Metadata = {
  title: 'QuantStock AI — Institutional Stock Research Platform',
  description: 'Bloomberg-grade stock analysis: options, technicals, fundamentals, quant metrics, and AI-driven insights.',
  keywords: ['stock analysis', 'options analytics', 'technical analysis', 'Black-Scholes', 'quantitative finance'],
  openGraph: {
    title: 'QuantStock AI',
    description: 'Institutional-grade stock research powered by AI and quantitative finance',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="min-h-screen bg-bg-primary">
        <QueryProvider>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              style: {
                background: '#1a1a1a',
                color: '#e5e5e5',
                border: '1px solid #242424',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '13px',
              },
            }}
          />
        </QueryProvider>
      </body>
    </html>
  )
}
