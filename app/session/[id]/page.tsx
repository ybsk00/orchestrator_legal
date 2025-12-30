import { useSessionEvents } from '@/lib/useSessionEvents'
import GateSummaryCard from '@/components/gate/GateSummaryCard'
import SteeringPanel from '@/components/gate/SteeringPanel'
import EndGateCard from '@/components/gate/EndGateCard'
import styles from './page.module.css'

// ... (existing imports)

export default function SessionPage({ params }: { params: { id: string } }) {
    const sessionId = params.id

    // SSE 이벤트 훅 사용
    const { gateData } = useSessionEvents(sessionId)

    // ... (existing effects)

    // Steering 핸들러
    const handleSteeringAction = async (action: string, steeringData: any = null) => {
        try {
            await fetch(`/api/sessions/${sessionId}/steering`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action,
                    steering: steeringData,
                    request_id: crypto.randomUUID()
                })
            })
        } catch (error) {
            console.error('Steering action failed:', error)
            alert('요청 처리 중 오류가 발생했습니다.')
        }
    }

    // ... (existing render)

    return (
        <main className={styles.container}>
            <div className={styles.splitLayout}>
                {/* ... (Avatar Section) ... */}
                <div className={styles.avatarSection}>
                    <Suspense fallback={<div className={styles.avatarPlaceholder}>로딩 중...</div>}>
                        <AvatarPanel activeSpeaker={activeSpeaker} />
                    </Suspense>
                </div>

                {/* 우측: 채팅 영역 */}
                <div className={styles.chatSection}>
                    {/* ... (Header) ... */}
                    <div className={styles.chatHeader}>
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
                                    {['agent1', 'agent2', 'agent3', 'verifier'].includes(msg.role) ? (
                                        <TypingMessage text={msg.content} speed={20} />
                                    ) : (
                                        msg.content
                                    )}
                                </div>
                            </div>
                        ))}

                        {/* USER_GATE / END_GATE UI 렌더링 */}
                        {(session?.phase === 'USER_GATE' || session?.phase === 'END_GATE') && gateData && (
                            <div className={styles.gateContainer}>
                                <GateSummaryCard
                                    roundIndex={gateData.round_index}
                                    decisionSummary={gateData.decision_summary}
                                    openIssues={gateData.open_issues}
                                    verifierStatus={gateData.verifier_gate_status}
                                />

                                {session.phase === 'USER_GATE' && (
                                    <SteeringPanel
                                        sessionId={sessionId}
                                        onSkip={() => handleSteeringAction('skip')}
                                        onInput={(data) => handleSteeringAction('input', data)}
                                        onFinalize={() => handleSteeringAction('finalize')}
                                    />
                                )}

                                {session.phase === 'END_GATE' && (
                                    <EndGateCard
                                        sessionId={sessionId}
                                        onFinalize={() => handleSteeringAction('finalize')}
                                        onExtend={() => handleSteeringAction('extend')}
                                        onNewSession={() => handleSteeringAction('new_session')}
                                    />
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

            {/* ... (Modals) ... */}
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

            {showReportModal && (
                <div className={styles.modalOverlay} onClick={() => setShowReportModal(false)}>
                    <div className={styles.reportModal} onClick={(e) => e.stopPropagation()}>
                        <div className={styles.reportModalHeader}>
                            <h2>📑 최종 합의 리포트</h2>
                            <div className={styles.reportModalActions}>
                                <button onClick={() => window.print()}>인쇄 / PDF 저장</button>
                                <button onClick={() => setShowReportModal(false)}>닫기</button>
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
            )}
        </main>
    )
}
