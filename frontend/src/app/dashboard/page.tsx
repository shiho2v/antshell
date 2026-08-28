// =============================================================
// File   : page.tsx
// Author : @JaeHoYang
// Week   : 07 | Ch.07 (2/2)
// Created: 2026-08-22
// =============================================================
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import type { User } from '@supabase/supabase-js'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

const MOCK_STOCKS = [
  { code: '005930', name: '삼성전자', price: '74,500', change: '+1.2%', up: true },
  { code: '000660', name: 'SK하이닉스', price: '198,000', change: '-0.5%', up: false },
  { code: '009150', name: '삼성전기', price: '142,000', change: '+2.1%', up: true },
  { code: '008490', name: '서흥', price: '28,350', change: '-1.3%', up: false },
]

const MOCK_NEWS = [
  { title: '삼성전자, 3분기 영업이익 10조 돌파 전망', time: '10분 전' },
  { title: 'SK하이닉스 HBM4 양산 일정 앞당겨', time: '32분 전' },
  { title: '코스피, 외국인 순매수에 2,650선 회복', time: '1시간 전' },
]

type GithubIssue = {
  number: number
  title: string
  user: string
  url: string
  created_at: string
  labels: string[]
}

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [savingCode, setSavingCode] = useState<string | null>(null)
  const [saveMsg, setSaveMsg] = useState<string | null>(null)
  const [issues, setIssues] = useState<GithubIssue[]>([])
  const [issuesLoading, setIssuesLoading] = useState(true)

  useEffect(() => {
    const supabase = createClient()
    supabase.auth.getUser().then(({ data }) => {
      if (!data.user) router.replace('/login')
      else setUser(data.user)
    })
  }, [router])

  useEffect(() => {
    fetch(`${API}/api/github/issues`)
      .then(r => r.json())
      .then(d => setIssues(d.issues ?? []))
      .catch(() => setIssues([]))
      .finally(() => setIssuesLoading(false))
  }, [])

  async function handleLogout() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.replace('/login')
  }

  async function saveToNotion(stock: typeof MOCK_STOCKS[0]) {
    setSavingCode(stock.code)
    setSaveMsg(null)
    try {
      const res = await fetch(`${API}/api/report/notion`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(stock),
      })
      const data = await res.json()
      setSaveMsg(res.ok ? data.message : `오류: ${data.detail}`)
    } catch {
      setSaveMsg('서버 연결 실패')
    } finally {
      setSavingCode(null)
      setTimeout(() => setSaveMsg(null), 4000)
    }
  }

  if (!user) return null

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      {/* 헤더 */}
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold">불타는 개미지옥</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-400">{user.email}</span>
          <button
            onClick={handleLogout}
            className="rounded-lg bg-gray-800 px-4 py-1.5 text-sm hover:bg-gray-700"
          >
            로그아웃
          </button>
        </div>
      </div>

      {/* Notion 저장 결과 토스트 */}
      {saveMsg && (
        <div className="mb-4 rounded-lg bg-indigo-900 px-4 py-2 text-sm text-indigo-200">
          {saveMsg}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* 포트폴리오 요약 */}
        <div className="col-span-1 rounded-2xl bg-gray-900 p-6">
          <h2 className="mb-4 text-lg font-semibold">내 포트폴리오</h2>
          <p className="text-3xl font-bold text-green-400">+3.24%</p>
          <p className="mt-1 text-sm text-gray-400">평가손익: +1,240,000원</p>
          <div className="mt-4 border-t border-gray-800 pt-4">
            <div className="flex justify-between text-sm">
              <span className="text-gray-400">총 평가금액</span>
              <span>39,240,000원</span>
            </div>
            <div className="mt-2 flex justify-between text-sm">
              <span className="text-gray-400">총 매입금액</span>
              <span>38,000,000원</span>
            </div>
          </div>
        </div>

        {/* 보유 종목 */}
        <div className="col-span-2 rounded-2xl bg-gray-900 p-6">
          <h2 className="mb-4 text-lg font-semibold">보유 종목</h2>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-400">
                <th className="pb-3">종목</th>
                <th className="pb-3 text-right">현재가</th>
                <th className="pb-3 text-right">등락률</th>
                <th className="pb-3 text-right">Notion</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800">
              {MOCK_STOCKS.map(s => (
                <tr key={s.code}>
                  <td className="py-3">
                    <p className="font-medium">{s.name}</p>
                    <p className="text-xs text-gray-500">{s.code}</p>
                  </td>
                  <td className="py-3 text-right">{s.price}원</td>
                  <td className={`py-3 text-right font-semibold ${s.up ? 'text-red-400' : 'text-blue-400'}`}>
                    {s.change}
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={() => saveToNotion(s)}
                      disabled={savingCode === s.code}
                      className="rounded-md bg-indigo-700 px-2 py-1 text-xs hover:bg-indigo-600 disabled:opacity-40"
                    >
                      {savingCode === s.code ? '저장 중...' : 'Notion 저장'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* 최신 뉴스 */}
        <div className="col-span-3 rounded-2xl bg-gray-900 p-6">
          <h2 className="mb-4 text-lg font-semibold">최신 뉴스</h2>
          <ul className="divide-y divide-gray-800">
            {MOCK_NEWS.map((n, i) => (
              <li key={i} className="flex items-center justify-between py-3">
                <span className="text-sm">{n.title}</span>
                <span className="ml-4 shrink-0 text-xs text-gray-500">{n.time}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* GitHub 이슈 */}
        <div className="col-span-3 rounded-2xl bg-gray-900 p-6">
          <h2 className="mb-4 text-lg font-semibold">
            GitHub 이슈
            <span className="ml-2 text-sm font-normal text-gray-400">shiho2v/antshell</span>
          </h2>
          {issuesLoading ? (
            <p className="text-sm text-gray-500">불러오는 중...</p>
          ) : issues.length === 0 ? (
            <p className="text-sm text-gray-500">열린 이슈가 없습니다.</p>
          ) : (
            <ul className="divide-y divide-gray-800">
              {issues.map(issue => (
                <li key={issue.number} className="flex items-start justify-between py-3">
                  <div>
                    <a
                      href={issue.url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-sm hover:text-indigo-400"
                    >
                      #{issue.number} {issue.title}
                    </a>
                    <div className="mt-1 flex gap-1">
                      {issue.labels.map(lb => (
                        <span key={lb} className="rounded bg-gray-700 px-1.5 py-0.5 text-xs text-gray-300">
                          {lb}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="ml-4 shrink-0 text-right text-xs text-gray-500">
                    <p>@{issue.user}</p>
                    <p>{issue.created_at}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
