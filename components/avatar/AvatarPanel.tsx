'use client'

import { useRef, useEffect, useState } from 'react'
import styles from './AvatarPanel.module.css'

interface AvatarPanelProps {
    activeSpeaker: string | null
}

interface AgentCardProps {
    agentId: string
    name: string
    role: string
    isSpeaking: boolean
    colorTheme: 'blue' | 'orange' | 'purple'
}

function AgentCard({ agentId, name, role, isSpeaking, colorTheme }: AgentCardProps) {
    const videoRef = useRef<HTMLVideoElement>(null)
    const [videoError, setVideoError] = useState(false)
    const [isLoading, setIsLoading] = useState(true)

    const videoSrc = isSpeaking ? '/Talk.mp4' : '/Idle.mp4'

    useEffect(() => {
        const video = videoRef.current
        if (!video) return

        // 영상 소스 변경 시 자연스럽게 전환
        const currentTime = video.currentTime
        video.src = videoSrc
        video.load()
        video.play().catch(() => {
            setVideoError(true)
        })
    }, [videoSrc])

    const handleVideoLoad = () => {
        setIsLoading(false)
        setVideoError(false)
    }

    const handleVideoError = () => {
        setVideoError(true)
        setIsLoading(false)
    }

    return (
        <div
            className={`
        ${styles.agentCard} 
        ${styles[colorTheme]} 
        ${isSpeaking ? styles.speaking : ''}
      `}
        >
            {/* 에이전트 이름 */}
            <div className={styles.cardHeader}>
                <span className={styles.agentName}>{name}</span>
                <span className={styles.agentRole}>{role}</span>
            </div>

            {/* 비디오 영역 */}
            <div className={styles.videoContainer}>
                {isLoading && (
                    <div className={styles.loadingPlaceholder}>
                        <img
                            src="/avatar.png"
                            alt={name}
                            className={styles.fallbackImage}
                            onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none'
                            }}
                        />
                    </div>
                )}

                {videoError ? (
                    <div className={styles.fallback}>
                        <img
                            src="/avatar.png"
                            alt={name}
                            className={styles.fallbackImage}
                            onError={(e) => {
                                (e.target as HTMLImageElement).style.display = 'none'
                            }}
                        />
                        <span className={styles.errorText}>Video load failed</span>
                    </div>
                ) : (
                    <video
                        ref={videoRef}
                        className={styles.video}
                        src={videoSrc}
                        autoPlay
                        loop
                        muted
                        playsInline
                        onLoadedData={handleVideoLoad}
                        onError={handleVideoError}
                    />
                )}
            </div>

            {/* 상태 라벨 */}
            <div className={styles.statusLabel}>
                {isSpeaking ? (
                    <span className={styles.speakingStatus}>● Speaking</span>
                ) : (
                    <span className={styles.idleStatus}>○ Idle</span>
                )}
            </div>
        </div>
    )
}

export default function AvatarPanel({ activeSpeaker }: AvatarPanelProps) {
    const agents = [
        { id: 'agent1', name: 'Agent 1', role: 'Planner', colorTheme: 'blue' as const },
        { id: 'agent2', name: 'Agent 2', role: 'Critic', colorTheme: 'orange' as const },
        { id: 'agent3', name: 'Agent 3', role: 'Synthesizer', colorTheme: 'purple' as const },
    ]

    return (
        <div className={styles.avatarPanel}>
            <div className={styles.cardGrid}>
                {agents.map((agent) => (
                    <AgentCard
                        key={agent.id}
                        agentId={agent.id}
                        name={agent.name}
                        role={agent.role}
                        isSpeaking={activeSpeaker === agent.id}
                        colorTheme={agent.colorTheme}
                    />
                ))}
            </div>
        </div>
    )
}
