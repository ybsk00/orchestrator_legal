'use client'

import { useEffect, useState, Suspense } from 'react'
import { useParams } from 'next/navigation'
import dynamic from 'next/dynamic'
import styles from './page.module.css'

// ResultAvatar는 클라이언트 사이드에서만 로드
const ResultAvatar = dynamic(() => import('@/components/avatar/ResultAvatar'), {
    ssr: false,
    loading: () => <div className={styles.avatarPlaceholder}>캐릭터 로딩 중...</div>
})

interface RoadmapItem {
    week: string
    tasks: string[]
}

interface RiskItem {
    risk: string
    mitigation: string
}

interface FinalReport {
    session_id: string
    category: string
    executive_summary: string
    top_decisions: string[]
    roadmap: RoadmapItem[]
    risks: RiskItem[]
    kpis: string[]
    open_issues: string[]
    round_summaries?: string[]
}

export default function FinalPage() {
    const params = useParams()
    const sessionId = params.id as string

    const [report, setReport] = useState<FinalReport | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [isPresenting, setIsPresenting] = useState(true)

    useEffect(() => {
        const fetchReport = async () => {
            try {
                const res = await fetch(`/api/sessions/${sessionId}/report`)
                if (!res.ok) {
                    throw new Error('Failed to fetch report')
                }
                const data = await res.json()
                setReport(data)

                // 프레젠테이션 효과: 5초 후 idle로 전환
                setTimeout(() => setIsPresenting(false), 5000)
            } catch (err) {
                setError('최종 리포트를 불러오는데 실패했습니다.')
            } finally {
                setLoading(false)
            }
        }

        fetchReport()
    }, [sessionId])

    if (loading) {
        return (
            <main className={styles.main}>
                <div className={styles.loading}>
                    <div className={styles.spinner}></div>
                    <p>최종 결과물을 생성하고 있습니다...</p>
                </div>
            </main>
        )
    }

    if (error || !report) {
        return (
            <main className={styles.main}>
                <div className={styles.error}>
                    <h2>⚠️ 오류</h2>
                    <p>{error || '리포트를 찾을 수 없습니다.'}</p>
                    <a href="/" className={styles.backButton}>홈으로 돌아가기</a>
                </div>
            </main>
        )
    }

    return (
        <main className={styles.main}>
            <div className={styles.container}>
                {/* 헤더 */}
                <header className={styles.header}>
                    <span className={styles.category}>{report.category}</span>
                    <h1 className={styles.title}>🎯 최종 결과 리포트</h1>
                    <p className={styles.sessionId}>세션: {sessionId}</p>
                </header>

                {/* AI 어시스턴트 캐릭터 */}
                <Suspense fallback={<div className={styles.avatarPlaceholder}>캐릭터 로딩 중...</div>}>
                    <ResultAvatar
                        isSpeaking={isPresenting}
                        message="안녕하세요! 3명의 AI 에이전트가 논의한 결과를 정리했습니다. 아래에서 최종 결론과 실행 로드맵을 확인해주세요."
                    />
                </Suspense>

                {/* Executive Summary */}
                <section className={styles.section}>
                    <h2 className={styles.sectionTitle}>📋 최종 결론</h2>
                    <div className={styles.summaryBox}>
                        {report.executive_summary}
                    </div>
                </section>

                {/* Top Decisions */}
                <section className={styles.section}>
                    <h2 className={styles.sectionTitle}>✅ 채택된 방향 (Top 5)</h2>
                    <ol className={styles.decisionsList}>
                        {report.top_decisions.map((decision, index) => (
                            <li key={index}>{decision}</li>
                        ))}
                    </ol>
                </section>

                {/* Roadmap */}
                <section className={styles.section}>
                    <h2 className={styles.sectionTitle}>🗓️ 실행 로드맵</h2>
                    <div className={styles.roadmapGrid}>
                        {report.roadmap.map((item, index) => (
                            <div key={index} className={styles.roadmapCard}>
                                <h3>{item.week}</h3>
                                <ul>
                                    {item.tasks.map((task, taskIndex) => (
                                        <li key={taskIndex}>{task}</li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Risks */}
                <section className={styles.section}>
                    <h2 className={styles.sectionTitle}>⚠️ 리스크 및 대응</h2>
                    <table className={styles.riskTable}>
                        <thead>
                            <tr>
                                <th>리스크</th>
                                <th>대응 방안</th>
                            </tr>
                        </thead>
                        <tbody>
                            {report.risks.map((item, index) => (
                                <tr key={index}>
                                    <td>{item.risk}</td>
                                    <td>{item.mitigation}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </section>

                {/* KPIs */}
                <section className={styles.section}>
                    <h2 className={styles.sectionTitle}>📊 KPI / 측정 지표</h2>
                    <ul className={styles.kpiList}>
                        {report.kpis.map((kpi, index) => (
                            <li key={index}>{kpi}</li>
                        ))}
                    </ul>
                </section>

                {/* Open Issues */}
                <section className={styles.section}>
                    <h2 className={styles.sectionTitle}>❓ 오픈 이슈</h2>
                    <ul className={styles.issuesList}>
                        {report.open_issues.map((issue, index) => (
                            <li key={index}>{issue}</li>
                        ))}
                    </ul>
                </section>

                {/* Round Summaries (Optional) */}
                {report.round_summaries && report.round_summaries.length > 0 && (
                    <section className={styles.section}>
                        <h2 className={styles.sectionTitle}>📝 라운드별 요약</h2>
                        <div className={styles.roundSummaries}>
                            {report.round_summaries.map((summary, index) => (
                                <div key={index} className={styles.roundCard}>
                                    <h4>라운드 {index + 1}</h4>
                                    <p>{summary}</p>
                                </div>
                            ))}
                        </div>
                    </section>
                )}

                {/* Actions */}
                <div className={styles.actions}>
                    <button className={styles.downloadBtn} onClick={() => window.print()}>
                        📄 PDF 다운로드
                    </button>
                    <a href="/" className={styles.newSessionBtn}>
                        ➕ 새 세션 시작
                    </a>
                </div>
            </div>
        </main>
    )
}
