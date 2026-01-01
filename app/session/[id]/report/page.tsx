'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import ReactMarkdown from 'react-markdown'
import styles from './page.module.css'

export default function ReportPage() {
    const params = useParams()
    const router = useRouter()
    const sessionId = params.id as string
    const [report, setReport] = useState<string | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        if (!sessionId) return

        const fetchReport = async () => {
            try {
                // 1. 먼저 리포트 조회 시도
                const res = await fetch(`/api/sessions/${sessionId}/report`)
                if (res.ok) {
                    const data = await res.json()
                    setReport(data.report_md)
                    setLoading(false)
                    return
                }

                // 2. 없으면 생성 요청 (On-Demand)
                // 사용자가 명시적으로 버튼을 눌러서 들어온 것이므로 자동 생성 트리거
                const genRes = await fetch(`/api/sessions/${sessionId}/report/generate`, {
                    method: 'POST'
                })

                if (genRes.ok) {
                    const data = await genRes.json()
                    setReport(data.report_md)
                } else {
                    setError('리포트 생성에 실패했습니다.')
                }
            } catch (err) {
                console.error(err)
                setError('오류가 발생했습니다.')
            } finally {
                setLoading(false)
            }
        }

        fetchReport()
    }, [sessionId])

    if (loading) {
        return (
            <div className={styles.container}>
                <div className={styles.loading}>
                    <h2>📑 최종 리포트 생성 중...</h2>
                    <p>토론 내용을 종합하여 결론을 도출하고 있습니다. 잠시만 기다려주세요.</p>
                    <div className={styles.spinner}></div>
                </div>
            </div>
        )
    }

    if (error) {
        return (
            <div className={styles.container}>
                <div className={styles.error}>
                    <h2>⚠️ 오류 발생</h2>
                    <p>{error}</p>
                </div>
            </div>
        )
    }

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1>📑 최종 합의 리포트</h1>
                <div className={styles.actions}>
                    <button onClick={() => window.print()}>인쇄 / PDF 저장</button>
                    <button onClick={() => router.back()}>닫기</button>
                </div>
            </header>
            <main className={styles.reportContent}>
                <div className={styles.markdownWrapper}>
                    {report ? (
                        <ReactMarkdown>{report}</ReactMarkdown>
                    ) : (
                        <p>리포트 내용이 없습니다.</p>
                    )}
                </div>
            </main>
        </div>
    )
}
