// =============================================================
// File   : page.tsx
// SPEC   : SPEC-PORTFOLIO-001 M3
// =============================================================
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase'
import type { User } from '@supabase/supabase-js'

// REQ-014: 기존 대시보드(dashboard/page.tsx:16)와 동일한 규칙으로 API 주소를 읽는다.
const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

type ValuationResult = {
  stock_code: string
  name: string
  revenue_growth_pct: number | null
  op_income_growth_pct: number | null
  verdict: string
  score: number
  basis: string
}

type RiskResult = {
  stock_code: string
  name: string
  market_value: number
  concentration: string
  drawdown_from_52w: string
  supply_flow: string
  volume_state: string
  risk_score: number
  overall: string
}

type AllocationResult = {
  stock_code: string
  name: string
  current_price: number
  market_value: number
  actual_weight_pct: number
  target_weight_pct: number
  drift_pct: number
  action: string
  rebalance_amount: number
}

type PortfolioResponse = {
  meta: {
    schema_version: string
    source: string
    portfolio_name: string
    as_of: string
    generated_date: string
  }
  valuation: { results: ValuationResult[] }
  risk: { total_market_value: number; results: RiskResult[] }
  allocation: { total_asset: number; cash: number; results: AllocationResult[] }
}

// REQ-015: verdict·overall·action 은 unknown 일 수 있고, 이는 오류가 아니라 정상 경로다.
function isUnknown(value: string | undefined | null) {
  return !value || value === 'unknown'
}

const VERDICT_STYLE: Record<string, string> = {
  저평가: 'bg-green-900 text-green-300',
  적정: 'bg-gray-700 text-gray-200',
  주의: 'bg-yellow-900 text-yellow-300',
  고평가: 'bg-red-900 text-red-300',
}

const OVERALL_STYLE: Record<string, string> = {
  low: 'bg-green-900 text-green-300',
  medium: 'bg-yellow-900 text-yellow-300',
  high: 'bg-red-900 text-red-300',
}

const ACTION_STYLE: Record<string, string> = {
  매수: 'bg-red-900 text-red-300',
  매도: 'bg-blue-900 text-blue-300',
  유지: 'bg-gray-700 text-gray-200',
}

// REQ-015: 판정 불가(unknown) 상태는 목록에서 숨기지 않고, 정상 판정과 시각적으로 구분되는
// 점선 테두리 배지로 표시한다 (정상 판정은 채워진 색 배지).
function StatusBadge({ value, styleMap }: { value: string | undefined; styleMap: Record<string, string> }) {
  if (isUnknown(value)) {
    return (
      <span className="rounded border border-dashed border-gray-600 px-2 py-0.5 text-xs text-gray-500">
        판정 불가
      </span>
    )
  }
  return (
    <span className={`rounded px-2 py-0.5 text-xs font-semibold ${styleMap[value as string] ?? 'bg-gray-700 text-gray-200'}`}>
      {value}
    </span>
  )
}

export default function PortfolioPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [data, setData] = useState<PortfolioResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // REQ-012: 인증되지 않은 사용자는 대시보드와 동일하게 /login 으로 이동시킨다.
  useEffect(() => {
    const supabase = createClient()
    supabase.auth.getUser().then(({ data }) => {
      if (!data.user) router.replace('/login')
      else setUser(data.user)
    })
  }, [router])

  // REQ-011: 요청 실패(네트워크 오류·4xx·5xx)는 분석 결과 영역에만 오류를 표시하고
  // 나머지 화면(헤더)은 정상 렌더링한다.
  useEffect(() => {
    fetch(`${API}/api/portfolio`)
      .then(async res => {
        if (!res.ok) {
          if (res.status === 404) {
            throw new Error('분석 결과가 아직 생성되지 않았습니다.')
          }
          throw new Error('분석 결과를 불러오지 못했습니다.')
        }
        return (await res.json()) as PortfolioResponse
      })
      .then(setData)
      .catch(() => setError('서버 연결 실패'))
      .finally(() => setLoading(false))
  }, [])

  if (!user) return null

  // 종목 코드 기준으로 세 블록(valuation/risk/allocation)을 하나의 행으로 합친다.
  // spec.md §4에 따라 세 results 리스트의 길이는 같다.
  const rows = data
    ? data.allocation.results.map(alloc => ({
        alloc,
        valuation: data.valuation.results.find(v => v.stock_code === alloc.stock_code),
        risk: data.risk.results.find(r => r.stock_code === alloc.stock_code),
      }))
    : []

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      {/* 헤더 */}
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold">포트폴리오 분석</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">{user.email}</span>
          <Link
            href="/dashboard"
            className="rounded-lg bg-gray-800 px-4 py-1.5 text-sm hover:bg-gray-700"
          >
            대시보드
          </Link>
        </div>
      </div>

      {loading ? (
        <p className="text-sm text-gray-500">불러오는 중...</p>
      ) : error ? (
        <div className="rounded-2xl bg-gray-900 p-6">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      ) : data ? (
        <div className="space-y-6">
          {/* REQ-010: as_of / generated_date 를 구분 레이블과 함께 표시하고, 스냅샷·샘플 여부를 알린다. */}
          <div className="rounded-2xl bg-gray-900 p-6">
            <div className="flex flex-wrap items-center gap-3 text-sm text-gray-400">
              <span>{data.meta.portfolio_name}</span>
              <span>보유 종목 기준일: {data.meta.as_of}</span>
              <span>분석 생성일: {data.meta.generated_date}</span>
              {data.meta.source === 'sample' && (
                <span className="rounded bg-yellow-900 px-2 py-0.5 text-xs font-semibold text-yellow-300">
                  샘플 데이터 (실제 에이전트 분석 아님)
                </span>
              )}
            </div>
            <p className="mt-2 text-xs text-gray-500">
              실시간 시세가 아닌 스냅샷입니다. 분석 결과는 위 기준일 시점에 생성된 값입니다.
            </p>
          </div>

          {/* REQ-009: 종목별 밸류에이션·리스크·리밸런싱을 표시한다. */}
          <div className="rounded-2xl bg-gray-900 p-6">
            <h2 className="mb-4 text-lg font-semibold">종목별 분석</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400">
                  <th className="pb-3">종목</th>
                  <th className="pb-3">밸류에이션</th>
                  <th className="pb-3">리스크</th>
                  <th className="pb-3">리밸런싱</th>
                  <th className="pb-3 text-right">드리프트</th>
                  <th className="pb-3 text-right">리밸런싱 금액</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-800">
                {rows.map(({ alloc, valuation, risk }) => (
                  <tr key={alloc.stock_code}>
                    <td className="py-3">
                      <p className="font-medium">{alloc.name}</p>
                      <p className="text-xs text-gray-500">{alloc.stock_code}</p>
                    </td>
                    <td className="py-3">
                      <StatusBadge value={valuation?.verdict} styleMap={VERDICT_STYLE} />
                      {valuation && !isUnknown(valuation.verdict) && (
                        <span className="ml-2 text-xs text-gray-500">{valuation.score}점</span>
                      )}
                    </td>
                    <td className="py-3">
                      <StatusBadge value={risk?.overall} styleMap={OVERALL_STYLE} />
                    </td>
                    <td className="py-3">
                      <StatusBadge value={alloc.action} styleMap={ACTION_STYLE} />
                    </td>
                    <td className="py-3 text-right">{alloc.drift_pct.toFixed(1)}%</td>
                    <td className="py-3 text-right">{alloc.rebalance_amount.toLocaleString()}원</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : null}
    </div>
  )
}
