'use client'

import { useState, useEffect, useMemo } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import styles from './page.module.css'

type Category = 'newbiz' | 'marketing' | 'dev' | 'domain' | ''

const CATEGORIES: { value: Category; label: string; icon: string }[] = [
    { value: '', label: '전체', icon: '📋' },
    { value: 'newbiz', label: '신규사업', icon: '🚀' },
    { value: 'marketing', label: '마케팅', icon: '📈' },
    { value: 'dev', label: '개발', icon: '💻' },
    { value: 'domain', label: '영역', icon: '🏢' },
]

const DATE_FILTERS = [
    { value: 'all', label: '전체 기간' },
    { value: 'today', label: '오늘' },
    { value: 'week', label: '최근 7일' },
    { value: 'month', label: '최근 30일' },
]

interface Session {
    id: string
    topic: string
    category: Category
    status: string
    created_at: string
}

const ITEMS_PER_PAGE = 10

export default function DashboardPage() {
    const [sessions, setSessions] = useState<Session[]>([])
    const [category, setCategory] = useState<Category>('')
    const [topic, setTopic] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [user, setUser] = useState<any>(null)
    const [sidebarOpen, setSidebarOpen] = useState(false)
    const [filterCategory, setFilterCategory] = useState<Category>('')
    const [filterDate, setFilterDate] = useState('all')
    const [searchQuery, setSearchQuery] = useState('')
    const [activeTab, setActiveTab] = useState<'new' | 'history'>('history')
    const [currentPage, setCurrentPage] = useState(1)
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
            const response = await fetch(`/api/sessions?user_id=${userId}`)
            if (response.ok) {
                const data = await response.json()
                setSessions(data)
            }
        } catch (error) {
            console.error('Failed to fetch sessions:', error)
        }
    }

    const filteredSessions = useMemo(() => {
        let result = [...sessions]

        // Category filter
        if (filterCategory) {
            result = result.filter(s => s.category === filterCategory)
        }

        // Date filter
        if (filterDate !== 'all') {
            const now = new Date()
            result = result.filter(s => {
                const created = new Date(s.created_at)
                switch (filterDate) {
                    case 'today':
                        return created.toDateString() === now.toDateString()
                    case 'week':
                        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
                        return created >= weekAgo
                    case 'month':
                        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)
                        return created >= monthAgo
                    default:
                        return true
                }
            })
        }

        // Search filter
        if (searchQuery.trim()) {
            result = result.filter(s =>
                s.topic.toLowerCase().includes(searchQuery.toLowerCase())
            )
        }

        return result
    }, [sessions, filterCategory, filterDate, searchQuery])

    // 페이지네이션 계산
    const totalPages = Math.ceil(filteredSessions.length / ITEMS_PER_PAGE)
    const paginatedSessions = useMemo(() => {
        const start = (currentPage - 1) * ITEMS_PER_PAGE
        return filteredSessions.slice(start, start + ITEMS_PER_PAGE)
    }, [filteredSessions, currentPage])

    // 필터 변경시 1페이지로 리셋
    useEffect(() => {
        setCurrentPage(1)
    }, [filterCategory, filterDate, searchQuery])

    const handleStartSession = async () => {
        if (!category || !topic.trim()) return

        setIsLoading(true)
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category, topic, user_id: user?.id }),
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

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr)
        return date.toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        })
    }

    const stats = useMemo(() => ({
        total: sessions.length,
        completed: sessions.filter(s => s.status === 'finalized').length,
        inProgress: sessions.filter(s => s.status !== 'finalized').length,
    }), [sessions])

    return (
        <div className={styles.layout}>
            {/* Sidebar */}
            <aside className={`${styles.sidebar} ${sidebarOpen ? styles.open : ''}`}>
                <div className={styles.sidebarHeader}>
                    <Link href="/dashboard" className={styles.logoLink}>
                        <span className={styles.logoIcon}>🤖</span>
                        <span className={styles.logoText}>AI 협업시스템</span>
                    </Link>
                </div>

                <nav className={styles.nav}>
                    <button
                        className={`${styles.navItem} ${activeTab === 'history' ? styles.active : ''}`}
                        onClick={() => setActiveTab('history')}
                    >
                        <span className={styles.navIcon}>📋</span>
                        회의 목록
                    </button>
                    <button
                        className={`${styles.navItem} ${activeTab === 'new' ? styles.active : ''}`}
                        onClick={() => setActiveTab('new')}
                    >
                        <span className={styles.navIcon}>➕</span>
                        새 회의 시작
                    </button>
                </nav>

                <div className={styles.sidebarSection}>
                    <h4 className={styles.sidebarLabel}>카테고리 필터</h4>
                    <div className={styles.filterList}>
                        {CATEGORIES.map(cat => (
                            <button
                                key={cat.value}
                                className={`${styles.filterItem} ${filterCategory === cat.value ? styles.active : ''}`}
                                onClick={() => setFilterCategory(cat.value)}
                            >
                                <span>{cat.icon}</span>
                                <span>{cat.label}</span>
                                <span className={styles.filterCount}>
                                    {cat.value === '' ? sessions.length : sessions.filter(s => s.category === cat.value).length}
                                </span>
                            </button>
                        ))}
                    </div>
                </div>

                <div className={styles.sidebarSection}>
                    <h4 className={styles.sidebarLabel}>기간 필터</h4>
                    <div className={styles.filterList}>
                        {DATE_FILTERS.map(df => (
                            <button
                                key={df.value}
                                className={`${styles.filterItem} ${filterDate === df.value ? styles.active : ''}`}
                                onClick={() => setFilterDate(df.value)}
                            >
                                <span>{df.label}</span>
                            </button>
                        ))}
                    </div>
                </div>

                <div className={styles.sidebarFooter}>
                    <div className={styles.userInfo}>
                        <div className={styles.userAvatar}>
                            {user?.email?.charAt(0).toUpperCase() || 'U'}
                        </div>
                        <div className={styles.userDetails}>
                            <span className={styles.userName}>{user?.email?.split('@')[0]}</span>
                            <span className={styles.userEmail}>{user?.email}</span>
                        </div>
                    </div>
                    <button onClick={handleSignOut} className={styles.logoutBtn}>
                        로그아웃
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className={styles.main}>
                <header className={styles.header}>
                    <button className={styles.menuToggle} onClick={() => setSidebarOpen(!sidebarOpen)}>
                        ☰
                    </button>
                    <h1 className={styles.pageTitle}>
                        {activeTab === 'history' ? '회의 목록' : '새 회의 시작'}
                    </h1>
                    <div className={styles.headerRight}>
                        {activeTab === 'history' && (
                            <div className={styles.searchBox}>
                                <input
                                    type="text"
                                    placeholder="주제 검색..."
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className={styles.searchInput}
                                />
                            </div>
                        )}
                    </div>
                </header>

                <div className={styles.content}>
                    {activeTab === 'history' ? (
                        <>
                            {/* Stats */}
                            <div className={styles.statsGrid}>
                                <div className={styles.statCard}>
                                    <span className={styles.statNumber}>{stats.total}</span>
                                    <span className={styles.statLabel}>전체 회의</span>
                                </div>
                                <div className={styles.statCard}>
                                    <span className={styles.statNumber}>{stats.completed}</span>
                                    <span className={styles.statLabel}>완료됨</span>
                                </div>
                                <div className={styles.statCard}>
                                    <span className={styles.statNumber}>{stats.inProgress}</span>
                                    <span className={styles.statLabel}>진행중</span>
                                </div>
                            </div>

                            {/* Session List */}
                            <div className={styles.sessionListHeader}>
                                <span>총 {filteredSessions.length}개의 회의</span>
                                <span className={styles.pageInfo}>
                                    {totalPages > 0 ? `${currentPage} / ${totalPages} 페이지` : ''}
                                </span>
                            </div>

                            {/* 리스트 형태 테이블 */}
                            <div className={styles.sessionTable}>
                                <div className={styles.tableHeader}>
                                    <div className={styles.colCategory}>카테고리</div>
                                    <div className={styles.colTopic}>주제</div>
                                    <div className={styles.colStatus}>상태</div>
                                    <div className={styles.colDate}>생성일</div>
                                    <div className={styles.colActions}>액션</div>
                                </div>

                                {paginatedSessions.length === 0 ? (
                                    <div className={styles.emptyState}>
                                        <span className={styles.emptyIcon}>📭</span>
                                        <h3>회의가 없습니다</h3>
                                        <p>새 회의를 시작해보세요!</p>
                                        <button
                                            className={styles.emptyButton}
                                            onClick={() => setActiveTab('new')}
                                        >
                                            새 회의 시작하기
                                        </button>
                                    </div>
                                ) : (
                                    paginatedSessions.map(session => (
                                        <div key={session.id} className={styles.tableRow}>
                                            <div className={styles.colCategory}>
                                                <span className={styles.categoryBadge}>
                                                    {CATEGORIES.find(c => c.value === session.category)?.icon || '📋'}
                                                    {CATEGORIES.find(c => c.value === session.category)?.label || session.category}
                                                </span>
                                            </div>
                                            <div className={styles.colTopic}>
                                                <span className={styles.topicText}>{session.topic}</span>
                                            </div>
                                            <div className={styles.colStatus}>
                                                <span className={`${styles.statusBadge} ${session.status === 'finalized' ? styles.completed : styles.active}`}>
                                                    {session.status === 'finalized' ? '완료' : '진행중'}
                                                </span>
                                            </div>
                                            <div className={styles.colDate}>
                                                {formatDate(session.created_at)}
                                            </div>
                                            <div className={styles.colActions}>
                                                <button
                                                    className={styles.viewBtn}
                                                    onClick={() => router.push(`/session/${session.id}`)}
                                                >
                                                    회의 보기
                                                </button>
                                                {session.status === 'finalized' && (
                                                    <button
                                                        className={styles.reportBtn}
                                                        onClick={() => router.push(`/session/${session.id}/report`)}
                                                    >
                                                        리포트
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>

                            {/* 페이지네이션 */}
                            {totalPages > 1 && (
                                <div className={styles.pagination}>
                                    <button
                                        className={styles.pageBtn}
                                        onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                                        disabled={currentPage === 1}
                                    >
                                        &lt; 이전
                                    </button>

                                    {Array.from({ length: totalPages }, (_, i) => i + 1).map(page => (
                                        <button
                                            key={page}
                                            className={`${styles.pageBtn} ${currentPage === page ? styles.activePage : ''}`}
                                            onClick={() => setCurrentPage(page)}
                                        >
                                            {page}
                                        </button>
                                    ))}

                                    <button
                                        className={styles.pageBtn}
                                        onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                                        disabled={currentPage === totalPages}
                                    >
                                        다음 &gt;
                                    </button>
                                </div>
                            )}
                        </>
                    ) : (
                        /* New Session Form */
                        <div className={styles.newSessionForm}>
                            <div className={styles.formCard}>
                                <h2>새로운 AI 회의 시작</h2>
                                <p className={styles.formDesc}>카테고리와 주제를 선택하여 AI 에이전트들과의 협업 회의를 시작하세요.</p>

                                <div className={styles.formGroup}>
                                    <label>카테고리 선택</label>
                                    <div className={styles.categoryOptions}>
                                        {CATEGORIES.filter(c => c.value !== '').map(cat => (
                                            <button
                                                key={cat.value}
                                                className={`${styles.categoryOption} ${category === cat.value ? styles.selected : ''}`}
                                                onClick={() => setCategory(cat.value)}
                                            >
                                                <span className={styles.categoryIcon}>{cat.icon}</span>
                                                <span className={styles.categoryLabel}>{cat.label}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div className={styles.formGroup}>
                                    <label>토론 주제</label>
                                    <textarea
                                        className={styles.topicTextarea}
                                        placeholder="예: 'AI 기반 고객 상담 챗봇 도입을 고려하고 있습니다. MVP 범위와 일정을 논의해주세요.'"
                                        value={topic}
                                        onChange={(e) => setTopic(e.target.value)}
                                        rows={5}
                                    />
                                </div>

                                <button
                                    className={styles.startBtn}
                                    onClick={handleStartSession}
                                    disabled={!category || !topic.trim() || isLoading}
                                >
                                    {isLoading ? '생성 중...' : '🚀 토론 시작하기'}
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        </div>
    )
}
