'use client'

import { useEffect, useRef } from 'react'
import Link from 'next/link'
import styles from './page.module.css'

// Animated particles background
function AnimatedBackground() {
    const canvasRef = useRef<HTMLCanvasElement>(null)

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return

        const ctx = canvas.getContext('2d')
        if (!ctx) return

        let animationId: number
        const particles: { x: number; y: number; vx: number; vy: number; size: number; alpha: number }[] = []
        const particleCount = 80

        const resize = () => {
            canvas.width = window.innerWidth
            canvas.height = window.innerHeight
        }
        resize()
        window.addEventListener('resize', resize)

        // Initialize particles
        for (let i = 0; i < particleCount; i++) {
            particles.push({
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1,
                alpha: Math.random() * 0.5 + 0.2
            })
        }

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height)

            // Draw connections
            particles.forEach((p1, i) => {
                particles.slice(i + 1).forEach(p2 => {
                    const dx = p1.x - p2.x
                    const dy = p1.y - p2.y
                    const dist = Math.sqrt(dx * dx + dy * dy)
                    if (dist < 150) {
                        ctx.beginPath()
                        ctx.strokeStyle = `rgba(99, 102, 241, ${0.15 * (1 - dist / 150)})`
                        ctx.lineWidth = 1
                        ctx.moveTo(p1.x, p1.y)
                        ctx.lineTo(p2.x, p2.y)
                        ctx.stroke()
                    }
                })
            })

            // Draw and update particles
            particles.forEach(p => {
                ctx.beginPath()
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
                ctx.fillStyle = `rgba(139, 92, 246, ${p.alpha})`
                ctx.fill()

                p.x += p.vx
                p.y += p.vy

                if (p.x < 0 || p.x > canvas.width) p.vx *= -1
                if (p.y < 0 || p.y > canvas.height) p.vy *= -1
            })

            animationId = requestAnimationFrame(animate)
        }
        animate()

        return () => {
            window.removeEventListener('resize', resize)
            cancelAnimationFrame(animationId)
        }
    }, [])

    return <canvas ref={canvasRef} className={styles.canvas} />
}

const AGENTS = [
    { id: 'agent1', name: 'Agent 1', role: '구현계획 전문가', desc: '구체적인 실행 방안과 KPI를 제시합니다', color: '#10b981' },
    { id: 'agent2', name: 'Agent 2', role: '리스크 분석가', desc: '허점과 리스크를 분석하고 검증 방안을 제시합니다', color: '#f59e0b' },
    { id: 'agent3', name: 'Agent 3', role: '합의안 설계자', desc: '절충안과 개선된 실행 계획을 도출합니다', color: '#8b5cf6' },
    { id: 'verifier', name: 'Verifier', role: '검증관', desc: '법적 안전장치 및 리스크 대응을 검증합니다', color: '#ef4444' },
]

const FEATURES = [
    { icon: '🤖', title: '다중 AI 에이전트', desc: '4명의 전문 AI가 서로 다른 관점에서 토론합니다' },
    { icon: '💡', title: '자동 합의 도출', desc: '여러 라운드를 거쳐 최적의 합의안을 생성합니다' },
    { icon: '📊', title: '실시간 협업', desc: '실시간으로 AI 토론 과정을 확인할 수 있습니다' },
    { icon: '📑', title: '최종 리포트', desc: '토론 결과를 정리한 상세 리포트를 제공합니다' },
]

export default function HomePage() {
    return (
        <main className={styles.main}>
            <AnimatedBackground />

            <div className={styles.content}>
                {/* Hero Section */}
                <section className={styles.hero}>
                    <div className={styles.badge}>AI-Powered Collaboration</div>
                    <h1 className={styles.title}>
                        AI 회의 <span className={styles.gradient}>협업시스템</span>
                    </h1>
                    <p className={styles.subtitle}>
                        새로운 아이디어와 계획을 AI에게 회의를 맡겨서 만들어보세요.
                        <br />
                        4명의 AI 전문가가 다양한 관점에서 토론하고 최적의 결론을 도출합니다.
                    </p>
                    <div className={styles.heroButtons}>
                        <Link href="/login" className={styles.primaryButton}>
                            시작하기 →
                        </Link>
                        <Link href="/dashboard" className={styles.secondaryButton}>
                            대시보드
                        </Link>
                    </div>
                </section>

                {/* Features Section */}
                <section className={styles.features}>
                    <h2 className={styles.sectionTitle}>주요 기능</h2>
                    <div className={styles.featureGrid}>
                        {FEATURES.map((feature, idx) => (
                            <div key={idx} className={styles.featureCard}>
                                <span className={styles.featureIcon}>{feature.icon}</span>
                                <h3>{feature.title}</h3>
                                <p>{feature.desc}</p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* Agents Section */}
                <section className={styles.agents}>
                    <h2 className={styles.sectionTitle}>참여 에이전트</h2>
                    <div className={styles.agentGrid}>
                        {AGENTS.map(agent => (
                            <div key={agent.id} className={styles.agentCard}>
                                <div className={styles.agentAvatar} style={{ background: agent.color }}>
                                    {agent.name.charAt(0)}
                                </div>
                                <span className={styles.agentName} style={{ color: agent.color }}>{agent.name}</span>
                                <strong className={styles.agentRole}>{agent.role}</strong>
                                <p className={styles.agentDesc}>{agent.desc}</p>
                            </div>
                        ))}
                    </div>
                </section>

                {/* CTA Section */}
                <section className={styles.cta}>
                    <div className={styles.ctaCard}>
                        <h2>지금 바로 시작하세요</h2>
                        <p>로그인하여 AI 협업 시스템의 모든 기능을 경험해보세요.</p>
                        <Link href="/login" className={styles.ctaButton}>
                            무료로 시작하기
                        </Link>
                    </div>
                </section>

                {/* Footer */}
                <footer className={styles.footer}>
                    <p>© 2024 AI 회의 협업시스템. All rights reserved.</p>
                </footer>
            </div>
        </main>
    )
}
