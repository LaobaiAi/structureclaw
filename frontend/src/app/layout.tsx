import type { Metadata } from 'next'
import './globals.css'
import { Providers } from './providers'
import { GeistSans, GeistMono } from '@/lib/fonts'

export const metadata: Metadata = {
  title: 'StructureClaw - 结构工程 AI 控制台',
  description: 'StructureClaw 前端控制台：统一调试 Agent 编排、Chat 路由与结构分析能力',
  keywords: ['结构分析', '有限元', '结构设计', 'Agent', 'Chat', 'OpenSees'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN" className={`${GeistSans.variable} ${GeistMono.variable}`} suppressHydrationWarning>
      <body>
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}
