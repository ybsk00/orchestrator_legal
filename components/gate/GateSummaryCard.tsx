import React from 'react'
import styles from './GateSummaryCard.module.css'

interface GateSummaryCardProps {
    roundIndex: number
    decisionSummary: string
    openIssues: string[]
    verifierStatus: string
}

export default function GateSummaryCard({
    roundIndex,
    decisionSummary,
    openIssues,
    verifierStatus
}: GateSummaryCardProps) {
    const isNoGo = verifierStatus === 'No-Go'
    const statusColor = isNoGo ? '#ff4444' : verifierStatus === 'Conditional' ? '#ffbb33' : '#00C851'

    return (
        <div className={styles.card}>
            <div className={styles.header}>
                <h3>Round {roundIndex} 완료</h3>
                <span className={styles.statusBadge} style={{ backgroundColor: statusColor }}>
                    Verifier: {verifierStatus}
                </span>
            </div>

            <div className={styles.content}>
                <div className={styles.section}>
                    <h4>📝 결정 사항 요약</h4>
                    <p>{decisionSummary}</p>
                </div>

                {openIssues.length > 0 && (
                    <div className={styles.section}>
                        <h4>⚠️ 미해결 이슈</h4>
                        <ul>
                            {openIssues.map((issue, idx) => (
                                <li key={idx}>{issue}</li>
                            ))}
                        </ul>
                    </div>
                )}
            </div>
        </div>
    )
}
