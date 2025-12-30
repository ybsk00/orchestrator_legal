'use client'

import { useState, useEffect } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'

type Category = 'newbiz' | 'marketing' | 'dev' | 'domain'

const CATEGORIES: { value: Category; label: string; description: string }[] = [
    { value: 'newbiz', label: '신규사업', description: '새로운 비즈니스 아이디어 검증' },
    { value: 'marketing', label: '마케팅', description: '마케팅 전략 및 캠페인 설계' },
    { value: 'dev', label: '개발', description: '기술 아키텍처 및 구현 계획' },
    { value: 'domain', label: '영역', description: '운영/프로세스/정책 의사결정' },
]

interface Session {
    id: string
    topic: string
    category: Category
    status: string
    created_at: string
}

export default function DashboardPage() {
    const [sessions, setSessions] = useState<Session[]>([])
    const [category, setCategory] = useState<Category | ''>('')
    const [topic, setTopic] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [user, setUser] = useState<any>(null)
    const router = useRouter()
    const supabase = createClient()

    useEffect(() => {
        const getUser = async () => {
            const { data: { user } } = await supabase.auth.getUser()
            if (!user) {
                router.push('/login')
                return
            }
            setUser(user)
            fetchSessions(user.id)
        }
        getUser()
    }, [router, supabase])

    const fetchSessions = async (userId: string) => {
        try {
            // API를 통해 세션 목록 조회 (현재는 모든 세션을 가져오지만, 추후 user_id 필터링 필요)
            // 백엔드 API가 user_id를 쿼리 파라미터로 받을 수 있도록 수정됨
            const response = await fetch(`/api/sessions?user_id=${userId}`)
            if (response.ok) {
                const data = await response.json()
                setSessions(data)
            }
        } catch (error) {
            console.error('Failed to fetch sessions:', error)
        }
    }

    const handleStartSession = async () => {
        if (!category || !topic.trim()) return

        setIsLoading(true)
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    category,
                    topic,
                    // user_id는 백엔드에서 처리하거나, 여기서 보낼 수 있음. 
                    // 현재 백엔드 create_session은 user_id=None으로 되어 있어 수정 필요할 수 있음.
                }),
            })

            if (response.ok) {
                const data = await response.json()
                router.push(`/session/${data.session_id}`)
            }
        } catch (error) {
            console.error('Failed to create session:', error)
        } finally {
            setIsLoading(false)
        }
    }

    const handleSignOut = async () => {
        await supabase.auth.signOut()
        router.push('/login')
    }

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div className={styles.logo}>🤖 오케스트레이터 대시보드</div>
                <div className={styles.userProfile}>
                    <span>{user?.email}</span>
                    <button onClick={handleSignOut} className={styles.signOutButton}>로그아웃</button>
                </div>
            </header>

            <main className={styles.main}>
                <section className={styles.newSessionSection}>
                    <h2 className={styles.sectionTitle}>새로운 토론 시작하기</h2>
                    <div className={styles.card}>
                        <div className={styles.inputGroup}>
                            <label>카테고리</label>
                            <div className={styles.categoryGrid}>
                                {CATEGORIES.map((cat) => (
                                    <button
                                        key={cat.value}
                                        className={`${styles.categoryButton} ${category === cat.value ? styles.selected : ''}`}
                                        onClick={() => setCategory(cat.value)}
                                    >
                                        {cat.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className={styles.inputGroup}>
                            <label>주제</label>
                            <textarea
                                className={styles.topicInput}
                                placeholder="논의하고 싶은 주제를 입력하세요..."
                                value={topic}
                                onChange={(e) => setTopic(e.target.value)}
                                rows={3}
                            />
                        </div>

                        <button
                            className={styles.startButton}
                            onClick={handleStartSession}
                            disabled={!category || !topic.trim() || isLoading}
                        >
                            {isLoading ? '생성 중...' : '토론 시작하기'}
                        </button>
                    </div>
                </section>

                <section className={styles.historySection}>
                    <h2 className={styles.sectionTitle}>이전 회의 목록</h2>
                    <div className={styles.sessionList}>
                        {sessions.length === 0 ? (
                            <p className={styles.emptyState}>진행된 회의가 없습니다.</p>
                        ) : (
                            sessions.map((session) => (
                                <div key={session.id} className={styles.sessionCard}>
                                    <div className={styles.sessionHeader}>
                                        <span className={styles.sessionCategory}>
                                            {CATEGORIES.find(c => c.value === session.category)?.label || session.category}
                                        </span>
                                        <span className={`${styles.sessionStatus} ${styles[session.status]}`}>
                                            {session.status === 'finalized' ? '완료됨' : '진행중'}
                                        </span>
                                    </div>
                                    <h3 className={styles.sessionTopic}>{session.topic}</h3>
                                    <div className={styles.sessionActions}>
                                        <button
                                            className={styles.viewButton}
                                            onClick={() => router.push(`/session/${session.id}`)}
                                        >
                                            회의 보기
                                        </button>
                                        {session.status === 'finalized' && (
                                            <button
                                                className={styles.resultButton}
                                                onClick={() => router.push(`/session/${session.id}/report`)}
                                            >
                                                최종 결과
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </section>
            </main>
        </div>
    )
}
