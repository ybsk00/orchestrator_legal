'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import styles from './EndGateCard.module.css'

interface EndGateCardProps {
    sessionId: string
}

export default function EndGateCard({ sessionId }: EndGateCardProps) {
    const router = useRouter()

    const handleGoToDashboard = () => {
        router.push('/')
    }

    return (
        <div className={styles.card}>
            <h3>🏁 토론이 종료되었습니다 (Round 3)</h3>
            <p className={styles.description}>
                모든 라운드가 완료되었습니다. 대시보드에서 결과를 확인하세요.
            </p>

            <button
                className={styles.dashboardBtn}
                onClick={handleGoToDashboard}
            >
                🏠 대시보드로 이동
            </button>
        </div>
    )
}
