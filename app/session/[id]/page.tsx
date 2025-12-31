'use client'

import { useEffect, useState, useRef, Suspense } from 'react'
import { useParams, useRouter } from 'next/navigation'
import dynamic from 'next/dynamic'
import { useRealtimeMessages, Message } from '@/lib/useRealtimeMessages'
import { useSessionEvents } from '@/lib/useSessionEvents'
import TypingMessage from '@/components/TypingMessage'
import GateSummaryCard from '@/components/gate/GateSummaryCard'
import SteeringPanel from '@/components/gate/SteeringPanel'
import EndGateCard from '@/components/gate/EndGateCard'
// 법무 시뮬레이션 컴포넌트
import { FactsIntakeForm, LegalGateForm, FactsSubmitResponse } from '@/components/legal'
import DevProjectGateForm from '@/components/DevProjectGateForm'
import styles from './page.module.css'

// Avatar Panel은 클라이언트 사이드에서만 로드
const AvatarPanel = dynamic(() => import('@/components/avatar/AvatarPanel'), {
    ssr: false,
    loading: () => <div className={styles.avatarPlaceholder}>캐릭터 로딩 중...</div>
})

interface SessionData {
    id: string
    status: string
    category: string
    topic: string
    round_index: number
    phase: string
    phase: string
    case_type?: string  // 법무 시뮬레이션: 'criminal' | 'civil'
    project_type?: 'general' | 'legal' | 'dev_project'
}

// 법무 Phase 상수
const LEGAL_PHASES = [
    'FACTS_INTAKE', 'FACTS_STIPULATE', 'FACTS_GATE',
    'JUDGE_R1_FRAME', 'CLAIMANT_R1', 'OPPOSING_R1', 'VERIFIER_R1',
    'OPPOSING_R2', 'CLAIMANT_R2', 'JUDGE_R2', 'VERIFIER_R2',
    'OPPOSING_R3', 'CLAIMANT_R3', 'JUDGE_R3', 'VERIFIER_R3',
]

export default function SessionPage() {
    const params = useParams()
    const router = useRouter()
    const sessionId = params.id as string

    const [session, setSession] = useState<SessionData | null>(null)
    const [input, setInput] = useState('')
    const [activeSpeaker, setActiveSpeaker] = useState<string | null>(null)
    const [showStopConfirm, setShowStopConfirm] = useState(false)
    const [stopTrigger, setStopTrigger] = useState('')
    const [showReportModal, setShowReportModal] = useState(false)
    const [reportContent, setReportContent] = useState<string | null>(null)
    const [reportLoading, setReportLoading] = useState(false)

    const messagesEndRef = useRef<HTMLDivElement>(null)

    // Supabase Realtime 훅 사용
    const { messages, isLoading, isConnected } = useRealtimeMessages(sessionId)

    // SSE 이벤트 훅 사용 (Gate 데이터)
    const { gateData } = useSessionEvents(sessionId)

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

        // 주기적으로 세션 상태 확인 (폴링) - 라운드 변경 등 감지용
        const interval = setInterval(fetchSession, 3000)
        return () => clearInterval(interval)
    }, [sessionId])

    // Active Speaker 자동 설정 (마지막 메시지 기준)
    useEffect(() => {
        if (messages.length > 0) {
            const lastMsg = messages[messages.length - 1]
            if (['agent1', 'agent2', 'agent3', 'verifier'].includes(lastMsg.role)) {
                setActiveSpeaker(lastMsg.role)
            } else {
                setActiveSpeaker(null)
            }
        }
    }, [messages])

    // 스크롤 자동 이동
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }, [messages])

    // 메시지 전송
    const handleSend = async () => {
        if (!input.trim()) return

        const messageText = input
        setInput('')

        try {
            await fetch(`/api/sessions/${sessionId}/message`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: messageText }),
            })
        } catch (error) {
            console.error('Failed to send message:', error)
            // 에러 시 입력 복구 (선택사항)
            setInput(messageText)
        }
    }

    // 마무리 버튼
    const handleFinalize = async () => {
        try {
            const res = await fetch(`/api/sessions/${sessionId}/finalize`, {
                method: 'POST',
            })
            if (res.ok) {
                // 대시보드로 이동
                router.push('/dashboard')
            }
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

    // 리포트 모달 열기
    const handleViewReport = async () => {
        setShowReportModal(true)
        setReportLoading(true)

        try {
            // 먼저 리포트 조회 시도
            let res = await fetch(`/api/sessions/${sessionId}/report`)

            if (!res.ok) {
                // 없으면 생성 요청
                res = await fetch(`/api/sessions/${sessionId}/report/generate`, {
                    method: 'POST'
                })
            }

            if (res.ok) {
                const data = await res.json()
                setReportContent(data.report_md)
            } else {
                setReportContent('리포트를 불러오는데 실패했습니다.')
            }
        } catch (error) {
            console.error('Failed to load report:', error)
            setReportContent('오류가 발생했습니다.')
        } finally {
            setReportLoading(false)
        }
    }

    // Steering 핸들러
    const handleSteeringAction = async (action: string, steeringData: any = null) => {
        try {
            const res = await fetch(`/api/sessions/${sessionId}/steering`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action,
                    steering: steeringData,
                    request_id: crypto.randomUUID()
                })
            })

            // finalize 또는 new_session 액션일 경우 대시보드로 이동
            if (res.ok && (action === 'finalize' || action === 'new_session')) {
                router.push('/dashboard')
            }
        } catch (error) {
            console.error('Steering action failed:', error)
            alert('요청 처리 중 오류가 발생했습니다.')
        }
    }

    const getAgentLabel = (role: string) => {
        switch (role) {
            // 일반 토론 에이전트
            case 'agent1': return '🔵 Agent 1: 구현계획'
            case 'agent2': return '🟠 Agent 2: 리스크'
            case 'agent3': return '🟣 Agent 3: 합의안'
            case 'verifier': return '🔴 Verifier: 검증관'
            // 법무 시뮬레이션 에이전트
            case 'judge': return '⚖️ 재판장'
            case 'claimant': return '🔵 원고측 (검사/원고대리)'
            case 'opposing': return '🟠 피고측 (변호인/피고대리)'
            case 'user': return '👤 사용자'
            // 개발 프로젝트 에이전트
            case 'prd': return '🔵 PRD Owner (PM)'
            case 'tech': return '🟠 Tech Lead (CTO)'
            case 'ux': return '🟣 UX Lead (Designer)'
            case 'dm': return '🔴 Delivery Manager (Agile)'
            default: return role
        }
    }

    // 개발 프로젝트 에이전트 설정
    const DEV_PROJECT_AGENTS = [
        { id: 'prd', name: 'PRD Owner', role: 'Product Manager', colorTheme: 'blue' as const },
        { id: 'tech', name: 'Tech Lead', role: 'CTO', colorTheme: 'orange' as const },
        { id: 'ux', name: 'UX Lead', role: 'Product Designer', colorTheme: 'purple' as const },
        { id: 'dm', name: 'Delivery Manager', role: 'Agile Coach', colorTheme: 'red' as const },
    ]

    // 법무 세션 여부 확인
    const isLegalSession = session?.project_type === 'legal' || session?.case_type
    const isDevProject = session?.project_type === 'dev_project'
    const isLegalPhase = session?.phase ? LEGAL_PHASES.includes(session.phase) : false

    return (
        <main className={styles.container}>
            <div className={styles.splitLayout}>
                {/* 좌측: 아바타 패널 */}
                <div className={styles.avatarSection}>
                    <Suspense fallback={<div className={styles.avatarPlaceholder}>로딩 중...</div>}>
                        <AvatarPanel
                            activeSpeaker={activeSpeaker}
                            agents={isDevProject ? DEV_PROJECT_AGENTS : undefined}
                        />
                    </Suspense>
                </div>

                {/* 우측: 채팅 영역 */}
                <div className={styles.chatSection}>
                    {/* 헤더 */}
                    <div className={styles.chatHeader}>
                        <button className={styles.backBtn} onClick={() => router.push('/dashboard')}>
                            ← 대시보드
                        </button>
                        <div className={styles.headerInfo}>
                            <span className={styles.categoryBadge}>{session?.category}</span>
                            <h2>{session?.topic}</h2>
                        </div>
                        <div className={styles.headerActions}>
                            <span className={styles.roundBadge}>
                                라운드 {session?.round_index || 0}/3
                            </span>
                            <span className={`${styles.connectionStatus} ${isConnected ? styles.connected : ''}`}>
                                {isConnected ? '● 연결됨' : '○ 연결 중...'}
                            </span>
                            <button className={styles.reportBtn} onClick={handleViewReport}>
                                📑 최종 리포트 보기/생성하기
                            </button>
                            <button className={styles.finalizeBtn} onClick={handleFinalize}>
                                🛑 마무리하기
                            </button>
                        </div>
                    </div>

                    {/* 메시지 목록 */}
                    <div className={styles.messageList}>
                        {isLoading && <div className={styles.loadingMsg}>메시지 로딩 중...</div>}
                        {messages.map((msg, idx) => (
                            <div
                                key={msg.id || idx}
                                className={`${styles.message} ${styles[msg.role] || ''}`}
                            >
                                <div className={styles.messageHeader}>
                                    <span className={styles.roleLabel}>{getAgentLabel(msg.role)}</span>
                                    {msg.isStreaming && <span className={styles.streamingDot}>●</span>}
                                </div>
                                <div className={styles.messageContent}>
                                    {['agent1', 'agent2', 'agent3', 'verifier', 'judge', 'claimant', 'opposing', 'prd', 'tech', 'ux', 'dm'].includes(msg.role) ? (
                                        <TypingMessage text={msg.content} speed={20} />
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                            </div>
                        ))}

                        {/* 법무 시뮬레이션: FACTS_INTAKE Phase - 사실관계 입력 폼 */}
                        {isLegalSession && session?.phase === 'FACTS_INTAKE' && (
                            <div className={styles.gateContainer}>
                                <FactsIntakeForm
                                    sessionId={sessionId}
                                    onSubmit={(data: FactsSubmitResponse) => {
                                        // Facts 제출 완료 후 세션 새로고침
                                        console.log('Facts submitted:', data)
                                        // 자동으로 다음 Phase로 전환
                                    }}
                                />
                            </div>
                        )}

                        {/* 법무 시뮬레이션: FACTS_GATE Phase - 추가 사실관계 입력 */}
                        {isLegalSession && session?.phase === 'FACTS_GATE' && (
                            <div className={styles.gateContainer}>
                                <div className={styles.factsGateWarning}>
                                    <p>⚠️ 누락된 사실관계가 3개 이상입니다. 추가 정보를 입력해주세요.</p>
                                </div>
                                <FactsIntakeForm
                                    sessionId={sessionId}
                                    onSubmit={(data: FactsSubmitResponse) => {
                                        console.log('Additional facts submitted:', data)
                                    }}
                                />
                            </div>
                        )}

                        {/* 법무 시뮬레이션: USER_GATE / END_GATE - LegalGateForm */}
                        {isLegalSession && (session?.phase === 'USER_GATE' || session?.phase === 'END_GATE') &&
                            !messages.some(m => m.isStreaming) && (
                                <div className={styles.gateContainer}>
                                    <LegalGateForm
                                        sessionId={sessionId}
                                        roundIndex={session.round_index}
                                        phase={session.phase}
                                        caseType={session.case_type || 'civil'}
                                        openIssues={gateData?.open_issues || []}
                                        onSubmit={(result) => {
                                            console.log('Legal steering submitted:', result)
                                            // 다음 라운드 자동 시작
                                        }}
                                    />
                                </div>
                                </div>
                            )}

                    {/* 개발 프로젝트: USER_GATE / END_GATE - DevProjectGateForm */}
                    {isDevProject && (session?.phase === 'USER_GATE' || session?.phase === 'END_GATE') &&
                        !messages.some(m => m.isStreaming) && (
                            <div className={styles.gateContainer}>
                                <DevProjectGateForm
                                    sessionId={sessionId}
                                    roundIndex={session.round_index}
                                    phase={session.phase}
                                    gateData={gateData}
                                    onSubmit={(action, data) => handleSteeringAction(action, data)}
                                />
                            </div>
                        )}

                    {/* 일반 토론: USER_GATE / END_GATE UI 렌더링 */}
                    {!isLegalSession && !isDevProject && (session?.phase === 'USER_GATE' || session?.phase === 'END_GATE') &&
                        !messages.some(m => m.isStreaming) && (
                            <div className={styles.gateContainer}>
                                {/* GateSummaryCard는 gateData가 있을 때만 표시 */}
                                {gateData && (
                                    <GateSummaryCard
                                        roundIndex={gateData.round_index}
                                        decisionSummary={gateData.decision_summary}
                                        openIssues={gateData.open_issues}
                                        verifierStatus={gateData.verifier_gate_status}
                                    />
                                )}

                                {session.phase === 'USER_GATE' && (
                                    <SteeringPanel
                                        sessionId={sessionId}
                                        onSkip={() => handleSteeringAction('skip')}
                                        onInput={(data) => handleSteeringAction('input', data)}
                                        onFinalize={() => handleSteeringAction('finalize')}
                                    />
                                )}

                                {session.phase === 'END_GATE' && (
                                    <EndGateCard sessionId={sessionId} />
                                )}
                            </div>
                        )}

                    <div ref={messagesEndRef} />
                </div>

                {/* 입력 영역 */}
                <div className={styles.inputContainer}>
                    <input
                        type="text"
                        className={styles.input}
                        placeholder={
                            session?.phase === 'USER_GATE' || session?.phase === 'END_GATE'
                                ? "위의 버튼을 사용하여 진행해주세요."
                                : "메시지를 입력하세요... (/stop 또는 /마무리로 종료)"
                        }
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleSend()}
                        disabled={session?.status === 'finalized' || session?.phase === 'USER_GATE' || session?.phase === 'END_GATE'}
                    />
                    <button
                        className={styles.sendBtn}
                        onClick={handleSend}
                        disabled={session?.status === 'finalized' || session?.phase === 'USER_GATE' || session?.phase === 'END_GATE'}
                    >
                        전송
                    </button>
                </div>
            </div>
        </div>

            {/* 종료 확인 모달 */ }
    {
        showStopConfirm && (
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
        )
    }

    {/* 리포트 모달 */ }
    {
        showReportModal && (
            <div className={styles.modalOverlay} onClick={() => setShowReportModal(false)}>
                <div className={styles.reportModal} onClick={(e) => e.stopPropagation()}>
                    <div className={styles.reportModalHeader}>
                        <h2>📑 최종 합의 리포트</h2>
                        <div className={styles.reportModalActions}>
                            <button onClick={() => window.print()}>인쇄 / PDF 저장</button>
                            <button onClick={() => setShowReportModal(false)}>닫기</button>
                            <button
                                className={styles.dashboardBtn}
                                onClick={() => router.push('/dashboard')}
                            >
                                ✅ 대시보드로 이동
                            </button>
                        </div>
                    </div>
                    <div className={styles.reportModalContent}>
                        {reportLoading ? (
                            <div className={styles.reportLoading}>
                                <div className={styles.spinner}></div>
                                <p>리포트 생성 중...</p>
                            </div>
                        ) : (
                            <pre className={styles.reportText}>{reportContent}</pre>
                        )}
                    </div>
                </div>
            </div>
        )
    }
        </main >
    )
}
