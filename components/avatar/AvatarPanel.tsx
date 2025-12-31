'use client'

import { useRef, useEffect, useState, Suspense } from 'react'
import dynamic from 'next/dynamic'
import styles from './AvatarPanel.module.css'

const WaveBackground = dynamic(() => import('@/components/ui/WaveBackground'), { ssr: false })

interface AgentConfig {
    id: string
    name: string
    role: string
    colorTheme: 'blue' | 'orange' | 'purple' | 'red'
}

interface AgentCardProps {
    agentId: string
    name: string
    role: string
    isSpeaking: boolean
    colorTheme: 'blue' | 'orange' | 'purple' | 'red'
}

function AgentCard({ agentId, name, role, isSpeaking, colorTheme }: AgentCardProps) {
    const videoRef = useRef<HTMLVideoElement>(null)

    useEffect(() => {
        if (videoRef.current) {
            const newSrc = isSpeaking ? '/Talk.mp4' : '/Idle.mp4'
            // Only update if src changed to avoid flickering
            if (!videoRef.current.src.endsWith(newSrc)) {
                videoRef.current.src = newSrc
                videoRef.current.play().catch(() => { })
            }
        }
    }, [isSpeaking])

    return (
        <div className={`${styles.agentCard} ${styles[colorTheme]} ${isSpeaking ? styles.speaking : ''}`}>
            <div className={styles.cardHeader}>
                <span className={styles.agentName}>{name}</span>
                <span className={styles.agentRole}>{role}</span>
            </div>
            <div className={styles.videoContainer}>
                <video
                    ref={videoRef}
                    className={styles.video}
                    loop
                    muted
                    playsInline
                    autoPlay
                    src="/Idle.mp4"
                />
                <div className={styles.statusLabel}>
                    {isSpeaking ? (
                        <div className={styles.speakingStatus}>
                            <span>●</span> Speaking
                        </div>
                    ) : (
                        <div className={styles.idleStatus}>
                            <span>○</span> Idle
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

interface AvatarPanelProps {
    activeSpeaker: string | null
    agents?: AgentConfig[]
}

export default function AvatarPanel({ activeSpeaker, agents: customAgents }: AvatarPanelProps) {
    const defaultAgents: AgentConfig[] = [
        { id: 'agent1', name: 'Agent 1', role: 'Planner', colorTheme: 'blue' },
        { id: 'agent2', name: 'Agent 2', role: 'Critic', colorTheme: 'orange' },
        { id: 'agent3', name: 'Agent 3', role: 'Synthesizer', colorTheme: 'purple' },
        { id: 'verifier', name: 'Verifier', role: 'Verifier', colorTheme: 'red' },
    ]

    const agents = customAgents || defaultAgents

    // 4인 그리드 레이아웃 (2x2)
    const topAgents = agents.slice(0, 2)
    const bottomAgents = agents.slice(2, 4)

    return (
        <div className={styles.avatarPanel}>
            <Suspense fallback={null}>
                <WaveBackground />
            </Suspense>

            {/* 상단: Agent 1, Agent 2 */}
            <div className={styles.topRow}>
                {topAgents.map((agent) => (
                    <div key={agent.id} className={styles.monitorWrapper}>
                        <AgentCard
                            agentId={agent.id}
                            name={agent.name}
                            role={agent.role}
                            isSpeaking={activeSpeaker === agent.id}
                            colorTheme={agent.colorTheme}
                        />
                        <div className={styles.monitorStand} />
                    </div>
                ))}
            </div>

            {/* 하단: Agent 3 */}
            <div className={styles.bottomRow}>
                {bottomAgents.map((agent) => (
                    <div key={agent.id} className={styles.monitorWrapper}>
                        <AgentCard
                            agentId={agent.id}
                            name={agent.name}
                            role={agent.role}
                            isSpeaking={activeSpeaker === agent.id}
                            colorTheme={agent.colorTheme}
                        />
                        <div className={styles.monitorStand} />
                    </div>
                ))}
            </div>
        </div>
    )
}
