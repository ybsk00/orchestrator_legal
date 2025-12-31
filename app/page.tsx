'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { createClient } from '@/lib/supabase/client'
import styles from './page.module.css'
import NeuralNetworkBackground from '@/components/3d/NeuralNetworkBackground'

const FEATURES = [
    {
        id: 'realtime',
        title: '실시간 AI 협업',
        desc: '여러 AI 에이전트가 동시에 참여하여 다각적인 관점에서 논의를 진행합니다.',
        icon: '🤝'
    },
    {
        id: 'expert',
        title: '전문 분야별 AI',
        desc: '법률, 기술, 전략 등 각 분야 전문 AI가 깊이 있는 분석을 제공합니다.',
        icon: '🎯'
    },
    {
        id: 'synthesis',
        title: '의견 종합 리포트',
        desc: '회의 결과를 자동으로 정리하여 실행 가능한 인사이트를 도출합니다.',
        icon: '📊'
    },
]

const MEETING_TYPES = [
    {
        id: 'strategy',
        title: '전략 회의',
        desc: '비즈니스 전략 수립 및 의사결정을 위한 AI 브레인스토밍',
        icon: '🚀',
        link: '/dashboard?mode=general',
        gradient: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)'
    },
    {
        id: 'development',
        title: '개발 리뷰',
        desc: '코드 리뷰, 아키텍처 설계, 기술 스택 선정 논의',
        icon: '💻',
        link: '/dashboard?mode=dev_project',
        gradient: 'linear-gradient(135deg, #10b981 0%, #14b8a6 100%)'
    },
    {
        id: 'legal',
        title: '법률 검토',
        desc: '계약서 분석, 리스크 평가, 규제 준수 확인',
        icon: '⚖️',
        link: '/dashboard?mode=legal',
        gradient: 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)'
    },
]

const STATS = [
    { value: '50+', label: '연동 가능 AI' },
    { value: '99.9%', label: '시스템 가동률' },
    { value: '24/7', label: '상시 운영' },
    { value: '< 100ms', label: '응답 속도' },
]

export default function HomePage() {
    const [isLoggedIn, setIsLoggedIn] = useState(false)
    const [isLoading, setIsLoading] = useState(true)
    const router = useRouter()
    const supabase = createClient()

    useEffect(() => {
        const checkAuth = async () => {
            const { data: { user } } = await supabase.auth.getUser()
            setIsLoggedIn(!!user)
            setIsLoading(false)
        }
        checkAuth()
    }, [supabase])

    const handleLogout = async () => {
        await supabase.auth.signOut()
        setIsLoggedIn(false)
        router.refresh()
    }

    return (
        <main className={styles.main}>
            {/* Header */}
            <header className={styles.header}>
                <div className={styles.headerLeft}>
                    <Link href="/" className={styles.logo}>
                        <span className={styles.logoIcon}>✦</span>
                        AI Meeting Hub
                    </Link>
                </div>

                <div className={styles.headerRight}>
                    {/* Status Indicator */}
                    <div className={styles.systemStatus}>
                        <div className={styles.statusPulse}>
                            <div className={styles.statusCore} />
                        </div>
                        <span className={styles.statusText}>시스템 정상</span>
                    </div>

                    {/* Auth Button */}
                    {!isLoading && (
                        isLoggedIn ? (
                            <button onClick={handleLogout} className={styles.authButton}>
                                <span className={styles.authIcon}>👤</span>
                                로그아웃
                            </button>
                        ) : (
                            <Link href="/login" className={styles.authButton}>
                                <span className={styles.authIcon}>🔐</span>
                                로그인
                            </Link>
                        )
                    )}
                </div>
            </header>

            <div className={styles.content}>
                {/* Hero Section */}
                <section className={styles.heroSection}>
                    <div className={styles.heroInfo}>
                        <div className={styles.badge}>
                            <span className={styles.badgeIcon}>⚡</span>
                            REAL-TIME AI COLLABORATION
                        </div>
                        <h1 className={styles.heroTitle}>
                            AI 협업<br />
                            <span className={styles.heroTitleGradient}>회의 시스템</span>
                        </h1>
                        <p className={styles.heroDesc}>
                            여러 AI 전문가들이 함께 논의하고, 다각적인 관점에서<br />
                            최적의 솔루션을 도출하는 차세대 협업 플랫폼입니다.
                        </p>

                        <div className={styles.heroActions}>
                            <Link href="/dashboard" className={styles.primaryBtn}>
                                <span>🎬</span> 회의 시작하기
                            </Link>
                            <button className={styles.secondaryBtn}>
                                <span>📖</span> 시스템 안내
                            </button>
                        </div>
                    </div>

                    <div className={styles.heroVisual}>
                        <NeuralNetworkBackground />
                        <div className={styles.heroOverlay}>
                            <div className={styles.centralOrb}>
                                <span>✦</span>
                            </div>
                            {/* Orbiting Dots */}
                            <div className={styles.orbitRing}>
                                <div className={styles.orbitDot} style={{ animationDelay: '0s' }}>🤖</div>
                                <div className={styles.orbitDot} style={{ animationDelay: '1s' }}>🧠</div>
                                <div className={styles.orbitDot} style={{ animationDelay: '2s' }}>⚖️</div>
                                <div className={styles.orbitDot} style={{ animationDelay: '3s' }}>💡</div>
                            </div>
                        </div>
                    </div>
                </section>

                {/* Stats Bar */}
                <section className={styles.statsBar}>
                    {STATS.map((stat, idx) => (
                        <div key={idx} className={styles.statItem}>
                            <span className={styles.statValue}>{stat.value}</span>
                            <span className={styles.statLabel}>{stat.label}</span>
                        </div>
                    ))}
                </section>

                {/* Features Section */}
                <section className={styles.features}>
                    <div className={styles.sectionHeader}>
                        <h2 className={styles.sectionTitle}>왜 AI 협업 회의인가?</h2>
                        <p className={styles.sectionDesc}>
                            단일 AI의 한계를 넘어, 다양한 전문 AI가 협력하여 더 나은 결과를 만듭니다.
                        </p>
                    </div>
                    <div className={styles.featureGrid}>
                        {FEATURES.map(feature => (
                            <div key={feature.id} className={styles.featureCard}>
                                <div className={styles.featureIcon}>{feature.icon}</div>
                                <h3>{feature.title}</h3>
                                <p>{feature.desc}</p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Meeting Types Section */}
                <section className={styles.meetingTypes}>
                    <div className={styles.sectionHeader}>
                        <h2 className={styles.sectionTitle}>회의 유형 선택</h2>
                        <p className={styles.sectionDesc}>
                            목적에 맞는 회의 유형을 선택하여 전문 AI 팀과 함께 시작하세요.
                        </p>
                    </div>
                    <div className={styles.meetingGrid}>
                        {MEETING_TYPES.map(meeting => (
                            <Link href={meeting.link} key={meeting.id} className={styles.meetingCard}>
                                <div className={styles.meetingIconWrapper} style={{ background: meeting.gradient }}>
                                    <span className={styles.meetingIcon}>{meeting.icon}</span>
                                </div>
                                <div className={styles.meetingContent}>
                                    <h3>{meeting.title}</h3>
                                    <p>{meeting.desc}</p>
                                </div>
                                <div className={styles.meetingArrow}>→</div>
                            </Link>
                        ))}
                    </div>
                </section>

                {/* How It Works Section */}
                <section className={styles.howItWorks}>
                    <div className={styles.sectionHeader}>
                        <h2 className={styles.sectionTitle}>어떻게 작동하나요?</h2>
                    </div>
                    <div className={styles.stepsGrid}>
                        <div className={styles.stepCard}>
                            <div className={styles.stepNumber}>01</div>
                            <h3>주제 설정</h3>
                            <p>논의할 주제와 목표를 설정하면 적합한 AI 패널이 자동 구성됩니다.</p>
                        </div>
                        <div className={styles.stepConnector}>
                            <div className={styles.connectorLine} />
                            <div className={styles.connectorDot} />
                        </div>
                        <div className={styles.stepCard}>
                            <div className={styles.stepNumber}>02</div>
                            <h3>AI 토론</h3>
                            <p>각 전문 분야 AI가 자신의 관점에서 의견을 제시하고 토론합니다.</p>
                        </div>
                        <div className={styles.stepConnector}>
                            <div className={styles.connectorLine} />
                            <div className={styles.connectorDot} />
                        </div>
                        <div className={styles.stepCard}>
                            <div className={styles.stepNumber}>03</div>
                            <h3>결과 도출</h3>
                            <p>논의 결과가 종합 분석되어 실행 가능한 결론으로 정리됩니다.</p>
                        </div>
                    </div>
                </section>

                {/* CTA Section */}
                <section className={styles.ctaSection}>
                    <div className={styles.ctaContent}>
                        <h2>지금 바로 AI 협업 회의를 시작하세요</h2>
                        <p>복잡한 문제도 여러 AI 전문가와 함께라면 명쾌한 해답을 찾을 수 있습니다.</p>
                        <Link href="/dashboard" className={styles.ctaButton}>
                            <span>🚀</span> 무료로 시작하기
                        </Link>
                    </div>
                </section>

                {/* Footer */}
                <footer className={styles.footer}>
                    <div className={styles.footerLogo}>
                        <span>✦</span> AI Meeting Hub
                    </div>
                    <p className={styles.footerText}>
                        © 2024 AI Meeting Hub. 차세대 AI 협업 회의 시스템.
                    </p>
                </footer>
            </div>
        </main>
    )
}
