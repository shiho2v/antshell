// =============================================================
// File   : page.tsx (settings)
// Author : @injeinnam
// Week   : 09 | Ch.09 (1/2)
// Created: 2026-09-13
// =============================================================
'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase'
import type { User } from '@supabase/supabase-js'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

type NotionSettings = {
  connected: boolean
  page_id: string | null
}

type Status = 'loading' | 'ready' | 'saving' | 'error'

export default function SettingsPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [settings, setSettings] = useState<NotionSettings | null>(null)
  const [status, setStatus] = useState<Status>('loading')
  const [message, setMessage] = useState<string | null>(null)
  const [accessToken, setAccessToken] = useState('')
  const [pageInput, setPageInput] = useState('')

  /** 현재 세션의 액세스 토큰. 백엔드가 사용자를 식별하는 데 쓴다. */
  const getSessionToken = useCallback(async () => {
    const supabase = createClient()
    const { data } = await supabase.auth.getSession()
    return data.session?.access_token ?? null
  }, [])

  useEffect(() => {
    const supabase = createClient()
    supabase.auth.getUser().then(({ data }) => {
      if (!data.user) router.replace('/login')
      else setUser(data.user)
    })
  }, [router])

  const loadSettings = useCallback(async () => {
    const token = await getSessionToken()
    if (!token) {
      router.replace('/login')
      return
    }
    try {
      const response = await fetch(`${API}/api/settings/notion`, {
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) {
        throw new Error(`설정을 불러오지 못했습니다 (${response.status})`)
      }
      const data: NotionSettings = await response.json()
      setSettings(data)
      setPageInput(data.page_id ?? '')
      setStatus('ready')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '설정을 불러오지 못했습니다')
      setStatus('error')
    }
  }, [getSessionToken, router])

  useEffect(() => {
    if (user) loadSettings()
  }, [user, loadSettings])

  async function handleSave() {
    setStatus('saving')
    setMessage(null)
    const token = await getSessionToken()
    if (!token) {
      router.replace('/login')
      return
    }
    try {
      const response = await fetch(`${API}/api/settings/notion`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ access_token: accessToken, page_id: pageInput }),
      })
      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.detail ?? `저장 실패 (${response.status})`)
      }
      setSettings({ connected: true, page_id: data.page_id })
      setPageInput(data.page_id)
      // 저장 후 입력란을 비운다. 토큰을 화면에 남겨둘 이유가 없다.
      setAccessToken('')
      setMessage('Notion 연동을 저장했습니다.')
      setStatus('ready')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '저장에 실패했습니다')
      setStatus('ready')
    }
  }

  async function handleDisconnect() {
    setStatus('saving')
    setMessage(null)
    const token = await getSessionToken()
    if (!token) {
      router.replace('/login')
      return
    }
    try {
      const response = await fetch(`${API}/api/settings/notion`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      })
      if (!response.ok) {
        throw new Error(`연동 해제 실패 (${response.status})`)
      }
      setSettings({ connected: false, page_id: null })
      setPageInput('')
      setAccessToken('')
      setMessage('Notion 연동을 해제했습니다.')
      setStatus('ready')
    } catch (error) {
      setMessage(error instanceof Error ? error.message : '연동 해제에 실패했습니다')
      setStatus('ready')
    }
  }

  if (!user) return null

  return (
    <div className="min-h-screen bg-gray-950 p-6">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-2xl font-bold">설정</h1>
        <Link href="/dashboard" className="rounded-lg bg-gray-800 px-4 py-1.5 text-sm hover:bg-gray-700">
          대시보드로
        </Link>
      </div>

      <div className="mx-auto max-w-2xl rounded-2xl bg-gray-900 p-6">
        <h2 className="mb-1 text-lg font-semibold">Notion 연동</h2>
        <p className="mb-5 text-sm text-gray-400">
          &quot;Notion 저장&quot; 버튼이 저장할 <strong>본인 Notion 페이지</strong>를 지정합니다.
          토큰은 본인만 접근할 수 있게 저장되며 화면에 다시 표시되지 않습니다.
        </p>

        {status === 'loading' ? (
          <p className="text-sm text-gray-500">불러오는 중...</p>
        ) : (
          <>
            <div
              className={`mb-5 rounded-lg px-3 py-2 text-sm ${
                settings?.connected ? 'bg-green-900 text-green-200' : 'bg-gray-800 text-gray-400'
              }`}
            >
              {settings?.connected ? (
                <>
                  연결됨 — 페이지 <code className="text-xs">{settings.page_id}</code>
                </>
              ) : (
                '연결되지 않음 — 아래에서 설정하세요.'
              )}
            </div>

            <label className="mb-1 block text-sm text-gray-300" htmlFor="notion-token">
              Notion 토큰
            </label>
            <input
              id="notion-token"
              type="password"
              autoComplete="off"
              value={accessToken}
              onChange={event => setAccessToken(event.target.value)}
              placeholder={settings?.connected ? '변경하려면 새 토큰 입력' : 'ntn_ 또는 secret_ 으로 시작'}
              className="mb-4 w-full rounded-lg bg-gray-800 px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-indigo-500"
            />

            <label className="mb-1 block text-sm text-gray-300" htmlFor="notion-page">
              저장할 페이지
            </label>
            <input
              id="notion-page"
              type="text"
              value={pageInput}
              onChange={event => setPageInput(event.target.value)}
              placeholder="페이지 URL 을 그대로 붙여넣어도 됩니다"
              className="mb-5 w-full rounded-lg bg-gray-800 px-3 py-2 text-sm outline-none focus:ring-1 focus:ring-indigo-500"
            />

            <div className="flex gap-2">
              <button
                onClick={handleSave}
                disabled={status === 'saving' || !accessToken || !pageInput}
                className="rounded-lg bg-indigo-700 px-4 py-2 text-sm hover:bg-indigo-600 disabled:opacity-40"
              >
                {status === 'saving' ? '저장 중...' : '저장'}
              </button>
              {settings?.connected && (
                <button
                  onClick={handleDisconnect}
                  disabled={status === 'saving'}
                  className="rounded-lg bg-gray-800 px-4 py-2 text-sm hover:bg-gray-700 disabled:opacity-40"
                >
                  연동 해제
                </button>
              )}
            </div>

            {message && <p className="mt-4 text-sm text-gray-300">{message}</p>}
          </>
        )}

        <div className="mt-8 border-t border-gray-800 pt-5">
          <h3 className="mb-2 text-sm font-semibold text-gray-300">토큰 발급 방법</h3>
          <ol className="list-inside list-decimal space-y-1 text-sm text-gray-400">
            <li>
              <a
                href="https://www.notion.so/my-integrations"
                target="_blank"
                rel="noreferrer"
                className="text-indigo-400 hover:underline"
              >
                notion.so/my-integrations
              </a>{' '}
              에서 새 integration 생성
            </li>
            <li>생성된 Internal Integration Token 복사 → 위 &quot;Notion 토큰&quot; 에 입력</li>
            <li>저장할 Notion 페이지를 열고 ··· → 연결 → 방금 만든 integration 선택</li>
            <li>그 페이지의 URL 을 복사 → 위 &quot;저장할 페이지&quot; 에 붙여넣기</li>
          </ol>
          <p className="mt-3 text-xs text-gray-500">
            3번을 빠뜨리면 integration 이 페이지에 접근할 수 없어 저장 시 오류가 납니다.
          </p>
        </div>
      </div>
    </div>
  )
}
