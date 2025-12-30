import React, { useState } from 'react'
import styles from './EndGateCard.module.css'

interface EndGateCardProps {
    sessionId: string
    onFinalize: () => void
    onExtend: () => void
    onNewSession: () => void
}

export default function EndGateCard({
    sessionId,
    onFinalize,
    onExtend,
    onNewSession
}: EndGateCardProps) {
    const [isSubmitting, setIsSubmitting] = useState(false)

    const handleAction = async (action: () => void) => {
        setIsSubmitting(true)
        try {
            await action()
        } catch (error) {
            console.error('Action failed:', error)
            setIsSubmitting(false)
        }
    }

    return (
        <div className={styles.card}>
            <h3>🏁 토론이 종료되었습니다 (Round 3)</h3>
            <p className={styles.description}>
                최종 결론을 도출하거나, 필요하다면 토론을 연장할 수 있습니다.
            </p>

            <div className={styles.actions}>
                <div className={styles.actionGroup}>
                    <h4>📑 리포트 생성</h4>
                    <p>현재까지의 논의를 바탕으로 최종 합의안을 작성합니다.</p>
                    <button
                        className={styles.finalizeBtn}
                        onClick={() => handleAction(onFinalize)}
                        disabled={isSubmitting}
                    >
                        최종 리포트 생성 및 종료
                    </button>
                </div>

                <div className={styles.divider}></div>

                <div className={styles.actionGroup}>
                    <h4>🔄 토론 연장</h4>
                    <p>미해결 이슈가 있다면 1라운드 더 진행합니다.</p>
                    <button
                        className={styles.extendBtn}
                        onClick={() => handleAction(onExtend)}
                        disabled={isSubmitting}
                    >
                        1라운드 연장 (+1)
                    </button>
                </div>

                <div className={styles.divider}></div>

                <div className={styles.actionGroup}>
                    <h4>✨ 새 세션</h4>
                    <p>현재 결론을 확정하고, 새로운 주제로 다시 시작합니다.</p>
                    <button
                        className={styles.newSessionBtn}
                        onClick={() => handleAction(onNewSession)}
                        disabled={isSubmitting}
                    >
                        결론 저장 후 새 세션 시작
                    </button>
                </div>
            </div>
        </div>
    )
}
