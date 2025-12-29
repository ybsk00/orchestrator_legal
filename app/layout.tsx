import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
    title: '3 에이전트 오케스트레이터',
    description: 'AI 에이전트 토론형 의사결정 시스템',
}

export default function RootLayout({
    children,
}: {
    children: React.ReactNode
}) {
    return (
        <html lang="ko">
            <body>{children}</body>
        </html>
    )
}
