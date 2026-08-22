// =============================================================
// File   : page.tsx
// Author : @JaeHoYang
// Week   : 06 | Ch.07 (1/2)
// Created: 2026-08-22
// =============================================================
'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { createClient } from '@/lib/supabase'

export default function LoginPage() {
  const router = useRouter()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    const supabase = createClient()
    const { error } = await supabase.auth.signInWithPassword({ email, password })

    if (error) {
      setError('이메일 또는 비밀번호가 올바르지 않습니다.')
    } else {
      router.push('/dashboard')
    }
    setLoading(false)
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm rounded-2xl bg-gray-900 p-8 shadow-lg">
        <h1 className="mb-6 text-center text-2xl font-bold">로그인</h1>
        <form onSubmit={handleLogin} className="flex flex-col gap-4">
          <input
            type="email"
            placeholder="이메일"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
            className="rounded-lg bg-gray-800 px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500"
          />
          <input
            type="password"
            placeholder="비밀번호"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            className="rounded-lg bg-gray-800 px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500"
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-blue-600 py-2 font-semibold hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '로그인 중...' : '로그인'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-400">
          계정이 없으신가요?{' '}
          <Link href="/signup" className="text-blue-400 hover:underline">
            회원가입
          </Link>
        </p>
      </div>
    </div>
  )
}
