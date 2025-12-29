'use client'

import { useRef, useEffect, useState } from 'react'
import styles from './ResultAvatar.module.css'

interface ResultAvatarProps {
    isSpeaking?: boolean
    message?: string
}

export default function ResultAvatar({ isSpeaking = false, message }: ResultAvatarProps) {
    const videoRef = useRef<HTMLVideoElement>(null)
    const [videoError, setVideoError] = useState(false)
    const [isLoading, setIsLoading] = useState(true)
    const [displayText, setDisplayText] = useState('')
    const [isTyping, setIsTyping] = useState(false)

    const videoSrc = isSpeaking ? '/Talk.mp4' : '/Idle.mp4'

    useEffect(() => {
        const video = videoRef.current
        if (!video) return

        video.src = videoSrc
        video.load()
        video.play().catch(() => {
            setVideoError(true)
        })
    }, [videoSrc])

    // 타이핑 효과
    useEffect(() => {
        if (!message) return

        setIsTyping(true)
        setDisplayText('')

        let index = 0
        const interval = setInterval(() => {
            if (index < message.length) {
                setDisplayText(prev => prev + message[index])
                index++
            } else {
                setIsTyping(false)
                clearInterval(interval)
            }
        }, 30)

        return () => clearInterval(interval)
    }, [message])

    const handleVideoLoad = () => {
        setIsLoading(false)
        setVideoError(false)
    }

    const handleVideoError = () => {
        setVideoError(true)
        setIsLoading(false)
    }

    return (
        <div className={styles.resultAvatarContainer}>
            {/* 캐릭터 영역 */}
            <div className={`${styles.avatarCard} ${isSpeaking ? styles.speaking : ''}`}>
                <div className={styles.videoContainer}>
                    {isLoading && (
                        <div className={styles.loadingPlaceholder}>
                            <img
                                src="/avatar.png"
                                alt="AI Assistant"
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
                                alt="AI Assistant"
                                className={styles.fallbackImage}
                                onError={(e) => {
                                    (e.target as HTMLImageElement).style.display = 'none'
                                }}
                            />
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

                <div className={styles.statusLabel}>
                    <span className={styles.assistantName}>🤖 AI 어시스턴트</span>
                </div>
            </div>

            {/* 말풍선 영역 */}
            {message && (
                <div className={styles.speechBubble}>
                    <p className={styles.messageText}>
                        {displayText}
                        {isTyping && <span className={styles.cursor}>|</span>}
                    </p>
                </div>
            )}
        </div>
    )
}
