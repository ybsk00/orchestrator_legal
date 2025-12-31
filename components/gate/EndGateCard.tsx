'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
import styles from './EndGateCard.module.css'

interface EndGateCardProps {
    sessionId: string
}

export default function EndGateCard({ sessionId }: EndGateCardProps) {
    const router = useRouter()
    const [isLoading, setIsLoading] = useState(false)

    const handleGoToDashboard = async () => {
        setIsLoading(true)

        try {
            // 세션 종료 (finalize) API 호출
            await fetch(`/api/sessions/${sessionId}/finalize`, {
                method: 'POST',
            })

            // /dashboard로 이동
            router.push('/dashboard')
        } catch (error) {
            console.error('Failed to finalize session:', error)
            // 에러가 나도 대시보드로 이동
            router.push('/dashboard')
        }
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
                disabled={isLoading}
            >
                {isLoading ? '종료 중...' : '🏠 대시보드로 이동'}
            </button>
        </div>
    )
}
