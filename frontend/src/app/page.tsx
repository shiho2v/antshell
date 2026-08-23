// =============================================================
// File   : page.tsx
// Author : @JaeHoYang
// Week   : 06 | Ch.07 (1/2)
// Created: 2026-08-22
// =============================================================
import { redirect } from 'next/navigation'

export default function Home() {
  redirect('/login')
}
