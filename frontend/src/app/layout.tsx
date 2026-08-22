// =============================================================
// File   : layout.tsx
// Author : @JaeHoYang
// Week   : 06 | Ch.07 (1/2)
// Created: 2026-08-22
// =============================================================
import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '불타는 개미지옥 — 주식 분석',
  description: '국내 주식 분석 웹',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko">
      <body className="min-h-screen bg-gray-950 text-gray-100">{children}</body>
    </html>
  )
}
