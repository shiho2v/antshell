// =============================================================
// File   : page.tsx
// Author : @JaeHoYang
// Week   : 06 | Ch.07 (1/2)
// Created: 2026-08-22
// =============================================================
'use client'

import { useState } from 'react'
import Link from 'next/link'
import { createClient } from '@/lib/supabase'

export default function SignupPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)
  const [loading, setLoading] = useState(false)

  async function handleSignup(e: React.FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)

    const supabase = createClient()
    const { error } = await supabase.auth.signUp({ email, password })

    if (error) {
      setError(error.message)
    } else {
      setDone(true)
    }
    setLoading(false)
  }

  if (done) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="w-full max-w-sm rounded-2xl bg-gray-900 p-8 text-center shadow-lg">
          <p className="mb-2 text-xl font-bold">확인 이메일을 보냈습니다</p>
          <p className="text-sm text-gray-400">
            {email}으로 전송된 링크를 클릭해 인증을 완료해주세요.
          </p>
          <Link href="/login" className="mt-6 inline-block text-blue-400 hover:underline">
            로그인 페이지로 이동
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="w-full max-w-sm rounded-2xl bg-gray-900 p-8 shadow-lg">
        <h1 className="mb-6 text-center text-2xl font-bold">회원가입</h1>
        <form onSubmit={handleSignup} className="flex flex-col gap-4">
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
            placeholder="비밀번호 (6자 이상)"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
            minLength={6}
            className="rounded-lg bg-gray-800 px-4 py-2 outline-none focus:ring-2 focus:ring-blue-500"
          />
          {error && <p className="text-sm text-red-400">{error}</p>}
          <button
            type="submit"
            disabled={loading}
            className="rounded-lg bg-blue-600 py-2 font-semibold hover:bg-blue-700 disabled:opacity-50"
          >
            {loading ? '가입 중...' : '회원가입'}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-gray-400">
          이미 계정이 있으신가요?{' '}
          <Link href="/login" className="text-blue-400 hover:underline">
            로그인
          </Link>
        </p>
      </div>
    </div>
  )
}
