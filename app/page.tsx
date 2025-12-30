'use client'

import { useState, Suspense } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment, ContactShadows } from '@react-three/drei'
import styles from './page.module.css'
import AgentAvatar from '@/components/scene/AgentAvatar'

type Category = 'newbiz' | 'marketing' | 'dev' | 'domain'

const CATEGORIES: { value: Category; label: string; description: string }[] = [
    { value: 'newbiz', label: '신규사업', description: '새로운 비즈니스 아이디어 검증' },
    { value: 'marketing', label: '마케팅', description: '마케팅 전략 및 캠페인 설계' },
    { value: 'dev', label: '개발', description: '기술 아키텍처 및 구현 계획' },
    { value: 'domain', label: '영역', description: '운영/프로세스/정책 의사결정' },
]

function HeroScene() {
    return (
        <Canvas camera={{ position: [0, 2, 6], fov: 45 }}>
            <ambientLight intensity={0.5} />
            <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={1} castShadow />
            <Environment preset="city" />

            <group position={[0, -1, 0]}>
                {/* Agent 1 */}
                <AgentAvatar
                    agentId="agent1"
                    modelPath="/models/agent1.glb"
                    position={[-2, 0, 0]}
                    rotation={[0, 0.5, 0]}
                    isSpeaking={false}
                    fallbackColor="#10b981"
                />
                {/* Agent 2 */}
                <AgentAvatar
                    agentId="agent2"
                    modelPath="/models/agent2.glb"
                    position={[-0.7, 0, 0.5]}
                    rotation={[0, 0.2, 0]}
                    isSpeaking={false}
                    fallbackColor="#f59e0b"
                />
                {/* Agent 3 */}
                <AgentAvatar
                    agentId="agent3"
                    modelPath="/models/agent3.glb"
                    position={[0.7, 0, 0.5]}
                    rotation={[0, -0.2, 0]}
                    isSpeaking={false}
                    fallbackColor="#8b5cf6"
                />
                {/* Verifier */}
                <AgentAvatar
                    agentId="verifier"
                    modelPath="/models/verifier.glb"
                    position={[2, 0, 0]}
                    rotation={[0, -0.5, 0]}
                    isSpeaking={false}
                    fallbackColor="#ef4444"
                />
                <ContactShadows resolution={1024} scale={10} blur={1} opacity={0.5} far={1} color="#000000" />
            </group>

            <OrbitControls enableZoom={false} enablePan={false} minPolarAngle={Math.PI / 3} maxPolarAngle={Math.PI / 2} />
        </Canvas>
    )
}

export default function Home() {
    const [category, setCategory] = useState<Category | ''>('')
    const [topic, setTopic] = useState('')
    const [isLoading, setIsLoading] = useState(false)

    const handleStartSession = async () => {
        if (!category || !topic.trim()) return

        setIsLoading(true)
        try {
            const response = await fetch('/api/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ category, topic }),
            })

            if (response.ok) {
                const data = await response.json()
                // 세션 페이지로 이동
                window.location.href = `/session/${data.session_id}`
            }
        } catch (error) {
            console.error('Failed to create session:', error)
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <main className={styles.main}>
            <div className={styles.container}>
                <header className={styles.header}>
                    <div className={styles.heroScene}>
                        <Suspense fallback={null}>
                            <HeroScene />
                        </Suspense>
                    </div>
                    <h1 className={styles.title}>🤖 3 에이전트 오케스트레이터</h1>
                    <p className={styles.subtitle}>
                        AI에게 회의 새로운 아이디어 및 계획을 AI에게 회의를 맡겨서 만들어보는 시스템입니다.
                    </p>
                </header>

                <section className={styles.categorySection}>
                    <h2>카테고리 선택</h2>
                    <div className={styles.categoryGrid}>
                        {CATEGORIES.map((cat) => (
                            <button
                                key={cat.value}
                                className={`${styles.categoryCard} ${category === cat.value ? styles.selected : ''}`}
                                onClick={() => setCategory(cat.value)}
                            >
                                <span className={styles.categoryLabel}>{cat.label}</span>
                                <span className={styles.categoryDesc}>{cat.description}</span>
                            </button>
                        ))}
                    </div>
                </section>

                <section className={styles.topicSection}>
                    <h2>토론 주제 입력</h2>
                    <textarea
                        className={styles.topicInput}
                        placeholder="예: 'AI 기반 고객 상담 챗봇 도입을 고려하고 있습니다. MVP 범위와 일정을 논의해주세요.'"
                        value={topic}
                        onChange={(e) => setTopic(e.target.value)}
                        rows={4}
                    />
                </section>

                <button
                    className={styles.startButton}
                    onClick={handleStartSession}
                    disabled={!category || !topic.trim() || isLoading}
                >
                    {isLoading ? '세션 생성 중...' : '토론 시작하기'}
                </button>

                <div className={styles.agentIntro}>
                    <h3>참여 에이전트</h3>
                    <div className={styles.agentGrid}>
                        <div className={styles.agentCard}>
                            <span className="agent1" style={{ color: 'var(--agent1)' }}>Agent 1</span>
                            <strong>구현계획 전문가</strong>
                            <p>구체적인 실행 방안과 KPI를 제시합니다</p>
                        </div>
                        <div className={styles.agentCard}>
                            <span className="agent2" style={{ color: 'var(--agent2)' }}>Agent 2</span>
                            <strong>리스크 오피서</strong>
                            <p>허점과 리스크를 공격하고 검증 방안을 제시합니다</p>
                        </div>
                        <div className={styles.agentCard}>
                            <span className="agent3" style={{ color: 'var(--agent3)' }}>Agent 3</span>
                            <strong>합의안 설계자</strong>
                            <p>절충안과 개선된 실행 계획을 도출합니다</p>
                        </div>
                        <div className={styles.agentCard}>
                            <span className="verifier" style={{ color: 'var(--verifier)' }}>Verifier</span>
                            <strong>검증관</strong>
                            <p>법적 안전장치 및 리스크 대응을 검증하고 정리합니다</p>
                        </div>
                    </div>
                </div>
            </div>
        </main>
    )
}
