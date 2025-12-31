'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import styles from './page.module.css'
import NeuralNetworkBackground from '@/components/3d/NeuralNetworkBackground'

const PROJECTS = [
    {
        id: 'general',
        title: '일반 프로젝트',
        desc: '데이터 분석 및 리서치 업무를 위한 표준 오케스트레이션입니다.',
        icon: '📁',
        link: '/dashboard?mode=general'
    },
    {
        id: 'dev',
        title: '개발 프로젝트',
        desc: '풀스택 코드 생성, 리팩토링 및 배포 파이프라인을 관리합니다.',
        icon: '💻',
        link: '/dashboard?mode=dev_project'
    },
    {
        id: 'legal',
        title: '법무 검토',
        desc: '계약서 분석, 규제 준수 확인 및 리스크 평가를 수행합니다.',
        icon: '⚖️',
        link: '/dashboard?mode=legal'
    },
]

const AGENTS = [
    {
        id: 'alpha',
        name: 'Agent Alpha',
        role: '전략 노드',
        status: 'Idle',
        load: '12%',
        desc: '새로운 전략 지시를 대기하고 있습니다.',
        color: '#10b981'
    },
    {
        id: 'beta',
        name: 'Agent Beta',
        role: '개발 노드',
        status: 'Active',
        load: '89%',
        desc: '현재 API 엔드포인트 리팩토링 작업을 수행 중입니다...',
        color: '#8b5cf6'
    },
    {
        id: 'gamma',
        name: 'Agent Gamma',
        role: '법무 노드',
        status: 'Idle',
        load: '0%',
        desc: '규제 준수 스캔 완료. 대기 상태입니다.',
        color: '#f59e0b'
    },
    {
        id: 'delta',
        name: 'Agent Delta',
        role: 'QA 노드',
        status: 'Waiting',
        load: '5%',
        desc: 'Agent Beta의 산출물을 기다리고 있습니다.',
        color: '#f97316'
    },
]

const LOGS = [
    { time: '10:42:01', msg: 'System initialization complete. Orchestrator ready.', type: 'info' },
    { time: '10:42:05', msg: 'Connection to Neural Cluster established (4 nodes).', type: 'info' },
    { time: '10:45:12', msg: 'Agent Beta started task: "API Refactoring - Module Auth".', type: 'highlight' },
    { time: '10:46:30', msg: 'Agent Gamma completed compliance scan. 0 issues found.', type: 'success' },
    { time: '10:48:15', msg: 'Warning: Memory usage spike on Node Delta. Stabilizing...', type: 'warning' },
    { time: '10:48:18', msg: 'Stability restored. Optimization routines active.', type: 'success' },
]

export default function HomePage() {
    const [isLoggedIn, setIsLoggedIn] = useState(false)
    const router = useRouter()
    const supabase = createClient()

    useEffect(() => {
        const checkAuth = async () => {
            const { data: { user } } = await supabase.auth.getUser()
            setIsLoggedIn(!!user)
        }
        checkAuth()
    }, [supabase])

    return (
        <main className={styles.main}>
            {/* Header */}
            <header className={styles.header}>
                <div className={styles.headerLeft}>
                    <Link href="/" className={styles.logo}>
                        <span className={styles.logoIcon}>❖</span>
                        Orchestra AI
                    </Link>
                </div>

                <nav className={styles.nav}>
                    <Link href="/dashboard" className={styles.navLink}>대시보드</Link>
                    <span className={styles.navLink}>네트워크</span>
                    <span className={styles.navLink}>뉴럴 로그</span>
                    <span className={styles.navLink}>설정</span>
                </nav>

                <div className={styles.headerRight}>
                    <div className={styles.systemStatus}>
                        <div className={styles.statusDot} />
                        SYSTEM OPTIMAL
                    </div>
                    {/* User Profile Placeholder */}
                    <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'linear-gradient(135deg, #6366f1, #a855f7)' }} />
                </div>
            </header>

            <div className={styles.content}>
                {/* Hero / Network Section */}
                <section className={styles.heroGrid}>
                    <div className={styles.heroInfo}>
                        <div className={styles.badge}>⚡ NEURAL SYNC ACTIVE</div>
                        <h1 className={styles.heroTitle}>
                            AI 협업<br />
                            오케스트레이션
                        </h1>
                        <p className={styles.heroDesc}>
                            실시간 뉴럴 동기화가 활성화되었습니다.<br />
                            4개의 에이전트 노드 간의 상호작용과 효율성을 모니터링합니다.
                        </p>

                        <div className={styles.heroActions}>
                            <Link href="/dashboard" className={styles.primaryBtn}>
                                <span>📊</span> 네트워크 그래프 보기
                            </Link>
                            <button className={styles.secondaryBtn}>
                                <span>💻</span> 시스템 진단
                            </button>
                        </div>

                        <div className={styles.statsRow}>
                            <div className={styles.statItem}>
                                <h4>98.4%</h4>
                                <p>성공률</p>
                            </div>
                            <div className={styles.statItem}>
                                <h4>12ms</h4>
                                <p>레이턴시</p>
                            </div>
                            <div className={styles.statItem}>
                                <h4>4.2TB</h4>
                                <p>데이터 처리량</p>
                            </div>
                        </div>
                    </div>

                    <div className={styles.networkVisual}>
                        <NeuralNetworkBackground />

                        {/* Overlay Elements inside Visual */}
                        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', pointerEvents: 'none' }}>
                            <div style={{
                                width: 80, height: 80,
                                borderRadius: '50%',
                                border: '2px solid #6366f1',
                                boxShadow: '0 0 30px rgba(99, 102, 241, 0.5)',
                                display: 'flex', alignItems: 'center', justifyContent: 'center',
                                background: 'rgba(5, 5, 8, 0.8)',
                                color: '#fff', fontSize: '2rem'
                            }}>
                                ❖
                            </div>
                        </div>
                    </div>
                </section>

                {/* Initialize Project Section */}
                <section className={styles.projects}>
                    <div className={styles.sectionTitle}>
                        <h2>프로젝트 시작</h2>
                        <span className={styles.viewAll}>모든 템플릿 보기</span>
                    </div>
                    <div className={styles.projectGrid}>
                        {PROJECTS.map(project => (
                            <Link href={project.link} key={project.id} style={{ textDecoration: 'none' }}>
                                <div className={styles.projectCard}>
                                    <div className={styles.cardIcon}>{project.icon}</div>
                                    <h3>{project.title}</h3>
                                    <p>{project.desc}</p>
                                </div>
                            </Link>
                        ))}
                    </div>
                </section>

                {/* Active Agents Section */}
                <section className={styles.agents}>
                    <div className={styles.sectionTitle}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                            <h2>활성 에이전트</h2>
                            <span style={{ padding: '0.2rem 0.6rem', background: 'rgba(255,255,255,0.1)', borderRadius: 12, fontSize: '0.75rem', color: '#94a3b8' }}>4 Online</span>
                        </div>

                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            <button className={styles.primaryBtn} style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}>
                                + 새 작업
                            </button>
                        </div>
                    </div>

                    <div className={styles.agentGrid}>
                        {AGENTS.map(agent => (
                            <div key={agent.id} className={styles.agentCard}>
                                <div className={styles.agentImage}>
                                    {/* Placeholder for agent visual */}
                                    <div style={{ width: '100%', height: '100%', background: `linear-gradient(45deg, ${agent.color}22, ${agent.color}44)` }} />
                                    <div style={{ position: 'absolute', top: 5, left: 5, fontSize: '0.6rem', padding: '2px 6px', background: 'rgba(0,0,0,0.6)', borderRadius: 4, color: '#fff' }}>
                                        ID: {agent.id.toUpperCase()}
                                    </div>
                                </div>
                                <div className={styles.agentInfo}>
                                    <div className={styles.agentHeader}>
                                        <span className={styles.agentRole} style={{ color: agent.color }}>{agent.role}</span>
                                        <div className={styles.agentStatus}>
                                            <div className={`${styles.statusIndicator} ${agent.status === 'Active' ? styles.active : agent.status === 'Waiting' ? styles.waiting : styles.idle}`} />
                                            {agent.status}
                                        </div>
                                    </div>
                                    <h3 className={styles.agentName}>{agent.name}</h3>
                                    <p className={styles.agentDesc}>{agent.desc}</p>
                                    <div className={styles.agentFooter}>
                                        <span>LOAD: {agent.load}</span>
                                        <span className={styles.actionLink}>LOGS ↗</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </section>

                {/* System Logs Section */}
                <section className={styles.logsSection}>
                    <div className={styles.logsHeader}>
                        <div className={styles.logsTitle}>
                            <span>📟</span> SYSTEM LOGS
                        </div>
                        <div className={styles.windowControls}>
                            <div className={styles.controlDot} />
                            <div className={styles.controlDot} />
                            <div className={styles.controlDot} />
                        </div>
                    </div>
                    <div className={styles.logContent}>
                        {LOGS.map((log, idx) => (
                            <div key={idx} className={styles.logEntry}>
                                <span className={styles.logTime}>[{log.time}]</span>
                                <span className={`${styles.logMessage} ${styles[log.type]}`}>{log.msg}</span>
                            </div>
                        ))}
                    </div>
                </section>
            </div>
        </main>
    )
}
