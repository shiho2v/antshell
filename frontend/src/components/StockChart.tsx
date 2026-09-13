// =============================================================
// File   : StockChart.tsx
// Author : @injeinnam
// Week   : 09 | Ch.09 (1/2)
// Created: 2026-09-13
// =============================================================
'use client'

import { useEffect, useRef, useState } from 'react'

// REQ-013: 기존 대시보드(page.tsx:14)와 동일한 규칙으로 API 주소를 읽는다.
const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

// 국내 시장 관례에 맞춘 색상. 상승 빨강 / 하락 파랑 (page.tsx 의 등락률 색과 동일).
const COLOR_UP = '#f87171'
const COLOR_DOWN = '#60a5fa'
const COLOR_SMA_5 = '#fbbf24'
const COLOR_SMA_20 = '#a78bfa'
const COLOR_SMA_60 = '#34d399'

type OhlcvRecord = {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
}

type OhlcvResponse = {
  stock_code: string
  source: string
  fetched_date: string | null
  records: OhlcvRecord[]
}

type IndicatorsResponse = {
  stock_code: string
  source: string
  dates: string[]
  sma_5: (number | null)[]
  sma_20: (number | null)[]
  sma_60: (number | null)[]
}

type ChartMeta = {
  source: string
  firstDate: string
  lastDate: string
  recordCount: number
}

type LoadStatus = 'loading' | 'ready' | 'error'

/** 지표 배열에서 null 구간을 걷어내고 차트가 받는 {time, value} 형태로 바꾼다. */
function toLinePoints(dates: string[], series: (number | null)[]) {
  const points: { time: string; value: number }[] = []
  for (let index = 0; index < dates.length; index += 1) {
    const value = series[index]
    if (value !== null && value !== undefined) {
      points.push({ time: dates[index], value })
    }
  }
  return points
}

async function fetchJson<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error(`요청 실패 (${response.status})`)
  }
  return response.json() as Promise<T>
}

export default function StockChart({
  stockCode,
  stockName,
}: {
  stockCode: string
  stockName: string
}) {
  const containerRef = useRef<HTMLDivElement | null>(null)
  const [status, setStatus] = useState<LoadStatus>('loading')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [meta, setMeta] = useState<ChartMeta | null>(null)

  useEffect(() => {
    // 종목이 바뀌면 이전 요청 결과가 늦게 도착해 새 차트를 덮어쓰는 것을 막는다.
    let cancelled = false
    let disposeChart: (() => void) | null = null

    setStatus('loading')
    setErrorMessage(null)
    setMeta(null)

    async function drawChart() {
      try {
        // 차트 라이브러리는 브라우저 전용이라 서버 렌더링 경로에서 로드하지 않는다.
        const [{ createChart, CandlestickSeries, LineSeries, HistogramSeries }, ohlcv, indicators] =
          await Promise.all([
            import('lightweight-charts'),
            fetchJson<OhlcvResponse>(`${API}/api/stocks/${stockCode}/ohlcv`),
            fetchJson<IndicatorsResponse>(`${API}/api/stocks/${stockCode}/indicators`),
          ])

        const container = containerRef.current
        if (cancelled || !container) {
          return
        }
        if (ohlcv.records.length === 0) {
          throw new Error('표시할 시세 데이터가 없습니다')
        }

        const chart = createChart(container, {
          width: container.clientWidth,
          height: 420,
          layout: {
            background: { color: 'transparent' },
            textColor: '#9ca3af',
            attributionLogo: false,
          },
          grid: {
            vertLines: { color: '#1f2937' },
            horzLines: { color: '#1f2937' },
          },
          rightPriceScale: { borderColor: '#374151' },
          timeScale: { borderColor: '#374151', timeVisible: false },
          crosshair: { mode: 0 },
        })

        // REQ-011: 캔들스틱 본체
        const candleSeries = chart.addSeries(CandlestickSeries, {
          upColor: COLOR_UP,
          downColor: COLOR_DOWN,
          borderUpColor: COLOR_UP,
          borderDownColor: COLOR_DOWN,
          wickUpColor: COLOR_UP,
          wickDownColor: COLOR_DOWN,
        })
        candleSeries.setData(
          ohlcv.records.map(record => ({
            time: record.date,
            open: record.open,
            high: record.high,
            low: record.low,
            close: record.close,
          }))
        )

        // REQ-012: SMA 3선 오버레이
        const movingAverages: [string, (number | null)[], string][] = [
          ['SMA 5', indicators.sma_5, COLOR_SMA_5],
          ['SMA 20', indicators.sma_20, COLOR_SMA_20],
          ['SMA 60', indicators.sma_60, COLOR_SMA_60],
        ]
        movingAverages.forEach(([title, series, color]) => {
          const lineSeries = chart.addSeries(LineSeries, {
            title,
            color,
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: false,
          })
          lineSeries.setData(toLinePoints(indicators.dates, series))
        })

        // REQ-012: 거래량 서브차트 (별도 pane)
        const volumeSeries = chart.addSeries(
          HistogramSeries,
          { priceFormat: { type: 'volume' }, priceScaleId: '' },
          1
        )
        volumeSeries.setData(
          ohlcv.records.map(record => ({
            time: record.date,
            value: record.volume,
            color: record.close >= record.open ? COLOR_UP : COLOR_DOWN,
          }))
        )
        const panes = chart.panes()
        if (panes.length > 1) {
          panes[0].setHeight(300)
          panes[1].setHeight(120)
        }

        chart.timeScale().fitContent()

        const resizeObserver = new ResizeObserver(entries => {
          const width = entries[0]?.contentRect.width
          if (width) {
            chart.applyOptions({ width })
            // 폭이 바뀌면 보이는 구간도 다시 맞춰야 한다. 그러지 않으면 생성 시점의
            // 좁은 폭 기준으로 잡힌 범위가 그대로 남아 데이터가 한쪽에 몰려 보인다.
            chart.timeScale().fitContent()
          }
        })
        resizeObserver.observe(container)

        disposeChart = () => {
          resizeObserver.disconnect()
          chart.remove()
        }

        setMeta({
          source: ohlcv.source,
          firstDate: ohlcv.records[0].date,
          lastDate: ohlcv.records[ohlcv.records.length - 1].date,
          recordCount: ohlcv.records.length,
        })
        setStatus('ready')
      } catch (error) {
        if (cancelled) {
          return
        }
        // REQ-014: 차트 영역에만 오류를 표시하고 페이지 전체를 중단시키지 않는다.
        setErrorMessage(error instanceof Error ? error.message : '차트를 불러오지 못했습니다')
        setStatus('error')
      }
    }

    drawChart()

    return () => {
      cancelled = true
      if (disposeChart) {
        disposeChart()
      }
    }
  }, [stockCode])

  return (
    <div className="rounded-2xl bg-gray-900 p-6">
      <div className="mb-4 flex items-baseline justify-between">
        <h2 className="text-lg font-semibold">
          {stockName}
          <span className="ml-2 text-sm font-normal text-gray-500">{stockCode}</span>
        </h2>
        {/* REQ-015: 실시간이 아니라 사전 수집된 스냅샷임을 알린다. */}
        {meta && (
          <span className="text-xs text-gray-500">
            {meta.firstDate} ~ {meta.lastDate} · {meta.recordCount}거래일
            {meta.source === 'sample' && (
              <span className="ml-2 rounded bg-amber-900 px-1.5 py-0.5 text-amber-200">
                샘플 데이터
              </span>
            )}
          </span>
        )}
      </div>

      {status === 'loading' && <p className="text-sm text-gray-500">차트를 불러오는 중...</p>}
      {status === 'error' && (
        <p className="text-sm text-red-400">차트를 불러오지 못했습니다 — {errorMessage}</p>
      )}

      {/* 컨테이너는 항상 렌더링한다. display:none 상태에서 차트를 만들면
          clientWidth 가 0 이라 폭 0 기준으로 범위가 잡힌다. */}
      <div ref={containerRef} className="w-full" />

      {status === 'ready' && (
        <div className="mt-3 flex gap-4 text-xs text-gray-500">
          <span style={{ color: COLOR_SMA_5 }}>— SMA 5</span>
          <span style={{ color: COLOR_SMA_20 }}>— SMA 20</span>
          <span style={{ color: COLOR_SMA_60 }}>— SMA 60</span>
          <span className="ml-auto">실시간 시세가 아닌 사전 수집 데이터입니다</span>
        </div>
      )}
    </div>
  )
}
