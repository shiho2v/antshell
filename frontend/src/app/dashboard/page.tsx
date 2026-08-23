// =============================================================
// File   : page.tsx
// Author : @JaeHoYang
// Week   : 06 | Ch.07 (1/2)
// Created: 2026-08-22
// =============================================================
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase'
import type { User } from '@supabase/supabase-js'

export default function DashboardPage() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)

  useEffect(() => {
    const supabase = createClient()
    supabase.auth.getUser().then(({ data }) => {
      if (!data.user) {
        router.replace('/login')
      } else {
        setUser(data.user)
      }
    })
  }, [router])

  async function handleLogout() {
    const supabase = createClient()
    await supabase.auth.signOut()
    router.replace('/login')
  }

  if (!user) return null

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4">
      <h1 className="text-2xl font-bold">대시보드</h1>
      <p className="text-gray-400">로그인된 계정: {user.email}</p>
      <button
        onClick={handleLogout}
        className="rounded-lg bg-red-600 px-6 py-2 font-semibold hover:bg-red-700"
      >
        로그아웃
      </button>
    </div>
  )
}
