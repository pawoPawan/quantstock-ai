import { NextRequest, NextResponse } from 'next/server'

const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function proxy(request: NextRequest, path: string[]): Promise<NextResponse> {
  const url = new URL(request.url)
  const target = `${BACKEND}/${path.join('/')}${url.search}`

  try {
    const res = await fetch(target, {
      method: request.method,
      headers: { 'Content-Type': 'application/json' },
      body: request.method !== 'GET' && request.method !== 'HEAD' ? await request.text() : undefined,
      signal: AbortSignal.timeout(55_000),
    })
    const data = await res.text()
    return new NextResponse(data, {
      status: res.status,
      headers: { 'Content-Type': 'application/json' },
    })
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err)
    return NextResponse.json({ detail: `Proxy error: ${msg}` }, { status: 502 })
  }
}

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path)
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxy(request, params.path)
}
