'use client'

import { useEffect, useState, useRef, Suspense } from 'react'
import { useParams } from 'next/navigation'
import dynamic from 'next/dynamic'
import { useSSE } from '@/lib/useSSE'
import styles from './page.module.css'

// Avatar Panel은 클라이언트 사이드에서만 로드
const AvatarPanel = dynamic(() => import('@/components/avatar/AvatarPanel'), {
    ssr: false,
    loading: () => <div className={styles.avatarPlaceholder}>캐릭터 로딩 중...</div>
})

interface Message {
    id: string
    role: 'user' | 'agent1' | 'agent2' | 'agent3' | 'system'
    content: string
    roundIndex: number
    phase: string
    isStreaming?: boolean
}

interface SessionData {
    id: string
    status: string
    category: string
    topic: string
    round_index: number
    phase: string
}

export default function SessionPage() {
    const params = useParams()
    const sessionId = params.id as string

    const [session, setSession] = useState<SessionData | null>(null)
    const [messages, setMessages] = useState<Message[]>([])
    const [input, setInput] = useState('')
    const [activeSpeaker, setActiveSpeaker] = useState<string | null>(null)
    const [showStopConfirm, setShowStopConfirm] = useState(false)
    const [stopTrigger, setStopTrigger] = useState('')

    const messagesEndRef = useRef<HTMLDivElement>(null)
    const { isConnected, lastEvent } = useSSE(sessionId)

    // 세션 정보 로드
    useEffect(() => {
        const fetchSession = async () => {
            try {
                const res = await fetch(`/api/sessions/${sessionId}`)
                if (res.ok) {
                    const data = await res.json()
                    setSession(data)
                }
            } catch (error) {
                console.error('Failed to fetch session:', error)
            }
        }
        fetchSession()
    }, [sessionId])

    // SSE 이벤트 처리
    useEffect(() => {
        if (!lastEvent) return

        const { type, data } = lastEvent.data

        switch (type) {
            case 'speaker_change':
                setActiveSpeaker(data.active_speaker)
                break

            case 'message_stream_start':
                setMessages(prev => [...prev, {
                    id: `temp-${Date.now()}`,
                    role: data.role,
                    content: '',
                    roundIndex: data.round_index,
                    phase: data.phase,
                    isStreaming: true,
                }])
                break

            case 'message_stream_chunk':
                setMessages(prev => {
                    const newMessages = [...prev]
                    const lastIndex = newMessages.length - 1
                    if (lastIndex >= 0 && newMessages[lastIndex].isStreaming) {
                        newMessages[lastIndex].content += data.text
                    }
                    return newMessages
                })
                break

            case 'message_stream_end':
                setMessages(prev => {
                    const newMessages = [...prev]
                    const lastIndex = newMessages.length - 1
                    if (lastIndex >= 0) {
                        newMessages[lastIndex].id = data.message_id
                        newMessages[lastIndex].isStreaming = false
                    }
                    return newMessages
                })
                setActiveSpeaker(null)
                break

            case 'stop_confirm':
                setStopTrigger(data.trigger)
                setShowStopConfirm(true)
                break

            case 'finalize_start':
                break

            case 'finalize_done':
            case 'session_end':
                window.location.href = `/session/${sessionId}/final`
                break

            case 'round_start':
            case 'round_end':
                fetch(`/api/sessions/${sessionId}`)
                    .then(res => res.json())
                    .then(setSession)
                break
        }
    }, [lastEvent, sessionId])

    // 스크롤 자동 이동
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    // 메시지 전송
    const handleSend = async () => {
        if (!input.trim()) return

        const userMessage: Message = {
            id: `user-${Date.now()}`,
            role: 'user',
            content: input,
            roundIndex: session?.round_index || 0,
            phase: 'user_input',
        }

        setMessages(prev => [...prev, userMessage])
        setInput('')

        try {
            await fetch(`/api/sessions/${sessionId}/messages`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: input }),
            })
        } catch (error) {
            console.error('Failed to send message:', error)
        }
    }

    // 마무리 버튼
    const handleFinalize = async () => {
        try {
            await fetch(`/api/sessions/${sessionId}/finalize`, {
                method: 'POST',
            })
        } catch (error) {
            console.error('Failed to finalize:', error)
        }
    }

    // 키워드 종료 확인
    const handleConfirmStop = async (confirmed: boolean) => {
        setShowStopConfirm(false)
        try {
            await fetch(`/api/sessions/${sessionId}/confirm-stop?confirmed=${confirmed}`, {
                method: 'POST',
            })
        } catch (error) {
            console.error('Failed to confirm stop:', error)
        }
    }

    const getAgentLabel = (role: string) => {
        switch (role) {
            case 'agent1': return '🔵 Agent 1: 구현계획'
            case 'agent2': return '🟠 Agent 2: 리스크'
            case 'agent3': return '🟣 Agent 3: 합의안'
            case 'user': return '👤 You'
            default: return '⚙️ System'
        }
    }

    return (
        <main className={styles.main}>
            {/* 헤더 */}
            <header className={styles.header}>
                <div className={styles.sessionInfo}>
                    <span className={styles.category}>{session?.category}</span>
                    <h1 className={styles.topic}>{session?.topic}</h1>
                </div>
                <div className={styles.headerActions}>
                    <span className={styles.roundBadge}>
                        라운드 {session?.round_index || 0}/3
                    </span>
                    <span className={`${styles.connectionStatus} ${isConnected ? styles.connected : ''}`}>
                        {isConnected ? '● 연결됨' : '○ 연결 중...'}
                    </span>
                    <button className={styles.finalizeBtn} onClick={handleFinalize}>
                        마무리하기
                    </button>
                </div>
            </header>

            {/* 메인 컨텐츠: 아바타 패널 + 채팅 */}
            <div className={styles.contentWrapper}>
                {/* 좌측: 캐릭터 카드 패널 (40%) */}
                <div className={styles.avatarContainer}>
                    <Suspense fallback={<div className={styles.avatarPlaceholder}>캐릭터 로딩 중...</div>}>
                        <AvatarPanel activeSpeaker={activeSpeaker} />
                    </Suspense>
                </div>

                {/* 우측: 채팅 패널 (60%) */}
                <div className={styles.chatContainer}>
                    <div className={styles.messages}>
                        {messages.map((msg) => (
                            <div
                                key={msg.id}
                                className={`${styles.message} ${styles[msg.role]} ${activeSpeaker === msg.role ? styles.speaking : ''}`}
                            >
                                <div className={styles.messageHeader}>
                                    <span className={styles.roleLabel}>{getAgentLabel(msg.role)}</span>
                                    {msg.isStreaming && <span className={styles.streamingDot}>●</span>}
                                </div>
                                <div className={styles.messageContent}>
                                    {msg.content}
                                </div>
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>

                    {/* 입력 영역 */}
                    <div className={styles.inputContainer}>
                        <input
                            type="text"
                            className={styles.input}
                            placeholder="메시지를 입력하세요... (/stop 또는 /마무리로 종료)"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        />
                        <button className={styles.sendBtn} onClick={handleSend}>
                            전송
                        </button>
                    </div>
                </div>
            </div>

            {/* 종료 확인 모달 */}
            {showStopConfirm && (
                <div className={styles.modalOverlay}>
                    <div className={styles.modal}>
                        <h3>토론을 마무리할까요?</h3>
                        <p>"{stopTrigger}" 키워드가 감지되었습니다.</p>
                        <p>마무리하면 Agent3가 최종 결과물을 생성합니다.</p>
                        <div className={styles.modalActions}>
                            <button onClick={() => handleConfirmStop(false)}>계속 토론</button>
                            <button className={styles.primary} onClick={() => handleConfirmStop(true)}>
                                마무리하기
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </main>
    )
}
