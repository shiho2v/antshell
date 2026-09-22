// =============================================================
// File   : StockNews.tsx
// Week   : 10 | Ch.09 (2/2)
// =============================================================
'use client'

import { useEffect, useState } from 'react'

// REQ-014: 기존 대시보드·StockChart.tsx 와 동일한 규칙으로 API 주소를 읽는다.
const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

type NewsItem = {
  title: string
  date: string
  source: string
  summary: string
  url?: string
}

type NewsResponse = {
  stock_code: string
  news: NewsItem[]
}

type NewsStatus = 'idle' | 'loading' | 'ready' | 'empty' | 'error'

// @MX:NOTE: [AUTO] spec.md §4 「안전한 링크」 — url 키 존재 + 문자열 + http(s) 스킴
// (대소문자 무시) 세 조건을 모두 만족할 때만 앵커를 만든다. url 은 news-collector
// 선언 스키마에 없는 선택 필드라 값의 형태를 보장할 수 없어, 판정을 프론트엔드가
// 직접 수행한다 — 백엔드는 저장된 값을 그대로 응답에 실어 보낼 뿐이다.
function isSafeUrl(url: unknown): url is string {
  return typeof url === 'string' && /^https?:\/\//i.test(url)
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`요청 실패 (${response.status})`)
  }
  return response.json() as Promise<T>
}

export default function StockNews({ stockCode }: { stockCode: string | null | undefined }) {
  const [status, setStatus] = useState<NewsStatus>('idle')
  const [news, setNews] = useState<NewsItem[]>([])

  useEffect(() => {
    if (!stockCode) {
      setStatus('idle')
      setNews([])
      return
    }

    // REQ-011: 종목을 빠르게 바꿔도 직전 종목의 응답이 늦게 도착해 화면을
    // 덮어쓰지 않게 한다(StockChart.tsx 와 동일한 cancelled 플래그 패턴).
    let cancelled = false
    setStatus('loading')
    setNews([])

    fetchJson<NewsResponse>(`${API}/api/stocks/${stockCode}/news`)
      .then(data => {
        if (cancelled) return
        setNews(data.news)
        setStatus(data.news.length === 0 ? 'empty' : 'ready')
      })
      .catch(() => {
        if (cancelled) return
        setStatus('error')
      })

    return () => {
      cancelled = true
    }
  }, [stockCode])

  return (
    <div className="rounded-2xl bg-gray-900 p-6">
      <h2 className="mb-4 text-lg font-semibold">최신 뉴스</h2>

      {status === 'idle' && (
        <p className="text-sm text-gray-500">종목을 선택하면 해당 종목의 뉴스가 표시됩니다.</p>
      )}
      {status === 'loading' && <p className="text-sm text-gray-500">뉴스를 불러오는 중...</p>}
      {status === 'error' && (
        <p className="text-sm text-red-400">뉴스를 불러오지 못했습니다.</p>
      )}
      {status === 'empty' && <p className="text-sm text-gray-500">수집된 뉴스가 없습니다.</p>}

      {status === 'ready' && (
        <>
          <ul className="divide-y divide-gray-800">
            {news.map((item, index) => (
              <li key={index} className="py-3">
                <div className="flex items-center justify-between gap-4">
                  {isSafeUrl(item.url) ? (
                    <a
                      href={item.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-sm hover:text-indigo-400"
                    >
                      {item.title}
                    </a>
                  ) : (
                    <span className="text-sm">{item.title}</span>
                  )}
                  <span className="shrink-0 text-xs text-gray-500">{item.date}</span>
                </div>
                <div className="mt-1 text-xs text-gray-500">{item.source}</div>
                <p className="mt-1 text-sm text-gray-400">{item.summary}</p>
              </li>
            ))}
          </ul>
          {/* REQ-012: 실시간 뉴스가 아니라 사전 수집된 스냅샷임을 알린다.
              수집 시각·수집 방법은 원본 파일에 값이 없으므로 만들어 표시하지 않는다. */}
          <p className="mt-3 text-xs text-gray-500">실시간 뉴스가 아닌 사전 수집된 스냅샷입니다.</p>
        </>
      )}
    </div>
  )
}
