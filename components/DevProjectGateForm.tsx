'use client'

import React, { useState, useEffect } from 'react'
import styles from './DevProjectGateForm.module.css'
import GateSummaryCard from './gate/GateSummaryCard'

interface DevProjectGateFormProps {
    sessionId: string
    roundIndex: number
    phase: string
    gateData: any
    onSubmit: (action: string, data?: any) => void
}

export default function DevProjectGateForm({
    sessionId,
    roundIndex,
    phase,
    gateData,
    onSubmit
}: DevProjectGateFormProps) {
    const [focus, setFocus] = useState('')
    const [goal, setGoal] = useState('')
    const [constraints, setConstraints] = useState<string[]>([])
    const [changes, setChanges] = useState('')

    const [constraintInput, setConstraintInput] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [showForm, setShowForm] = useState(true) // Default true, unless pending logic changes it

    // Pending 상태 처리
    const isPending = gateData?.verifier_gate_status === 'pending'

    useEffect(() => {
        // Pending 상태면 폼을 숨기고 선택을 기다릴 수도 있지만, 
        // 기획상 "Fix now"를 누르면 폼을 보여주는게 자연스러움.
        // 여기서는 상단에 경고를 띄우고 폼은 열어두되, "Proceed" 버튼을 제공하는 방식
    }, [isPending])

    const handleAddConstraint = () => {
        if (constraintInput.trim()) {
            setConstraints([...constraints, constraintInput.trim()])
            setConstraintInput('')
        }
    }

    const removeConstraint = (index: number) => {
        setConstraints(constraints.filter((_, i) => i !== index))
    }

    const handleSubmit = async () => {
        setIsSubmitting(true)
        try {
            const steeringData = {
                focus,
                goal,
                constraints,
                changes
            }
            await onSubmit('input', steeringData)
        } catch (error) {
            console.error('Failed to submit steering:', error)
            setIsSubmitting(false)
        }
    }

    const handleProceedDefaults = async () => {
        setIsSubmitting(true)
        try {
            await onSubmit('skip')
        } catch (error) {
            console.error('Failed to skip:', error)
            setIsSubmitting(false)
        }
    }

    const handleFinalize = async () => {
        setIsSubmitting(true)
        try {
            await onSubmit('finalize')
        } catch (error) {
            console.error('Failed to finalize:', error)
            setIsSubmitting(false)
        }
    }

    return (
        <div className={styles.container}>
            {/* 1. 라운드 요약 카드 */}
            {gateData && (
                <GateSummaryCard
                    roundIndex={roundIndex}
                    decisionSummary={gateData.decision_summary || '요약 정보 없음'}
                    openIssues={gateData.open_issues || []}
                    verifierStatus={gateData.verifier_gate_status || 'Unknown'}
                />
            )}

            {/* 2. Pending 경고 및 액션 */}
            {isPending && (
                <div className={styles.pendingWarning}>
                    <div className={styles.warningHeader}>
                        ⚠️ 의견 불일치 또는 리스크 감지됨 (Pending)
                    </div>
                    <p>
                        에이전트 간 합의가 완벽하지 않거나 리스크가 높습니다.
                        직접 개입하여 방향을 수정하시겠습니까, 아니면 기본값으로 진행하시겠습니까?
                    </p>
                    <div className={styles.pendingActions}>
                        <button
                            className={styles.proceedBtn}
                            onClick={handleProceedDefaults}
                            disabled={isSubmitting}
                        >
                            ⏩ 기본값으로 진행 (Proceed)
                        </button>
                        {/* Fix now는 폼 입력을 유도하므로 별도 버튼 액션 없이 아래 폼 사용 */}
                    </div>
                </div>
            )}

            {/* 3. Steering 입력 폼 */}
            <div className={styles.form}>
                <div className={styles.header}>
                    <h3>🎯 다음 라운드 방향 설정 (Steering)</h3>
                    <p className={styles.description}>
                        에이전트들에게 구체적인 지시사항을 전달하세요.
                    </p>
                </div>

                <div className={styles.formGroup}>
                    <label>중점 분야 (Focus)</label>
                    <input
                        type="text"
                        className={styles.textInput}
                        value={focus}
                        onChange={(e) => setFocus(e.target.value)}
                        placeholder="예: 비용 절감, 사용자 경험 개선, 보안 강화"
                    />
                    {/* 추천 옵션 */}
                    {gateData?.recommended_focus_options && gateData.recommended_focus_options.length > 0 && (
                        <div className={styles.recommendations}>
                            {gateData.recommended_focus_options.map((opt: string, idx: number) => (
                                <button
                                    key={idx}
                                    className={styles.recChip}
                                    onClick={() => setFocus(opt)}
                                >
                                    {opt}
                                </button>
                            ))}
                        </div>
                    )}
                </div>

                <div className={styles.formGroup}>
                    <label>목표 (Goal)</label>
                    <input
                        type="text"
                        className={styles.textInput}
                        value={goal}
                        onChange={(e) => setGoal(e.target.value)}
                        placeholder="예: MVP 출시를 위한 필수 기능 확정"
                    />
                </div>

                <div className={styles.formGroup}>
                    <label>제약조건 (Constraints)</label>
                    <div className={styles.tagInput}>
                        <input
                            type="text"
                            className={styles.textInput}
                            value={constraintInput}
                            onChange={(e) => setConstraintInput(e.target.value)}
                            onKeyPress={(e) => e.key === 'Enter' && handleAddConstraint()}
                            placeholder="예: 3개월 내 완료, 예산 5천만원"
                        />
                        <button className={styles.addBtn} onClick={handleAddConstraint}>추가</button>
                    </div>
                    <div className={styles.tags}>
                        {constraints.map((c, i) => (
                            <span key={i} className={styles.tag}>
                                {c}
                                <button className={styles.removeTag} onClick={() => removeConstraint(i)}>×</button>
                            </span>
                        ))}
                    </div>
                </div>

                <div className={styles.formGroup}>
                    <label>변경 요청 사항 (Changes)</label>
                    <textarea
                        className={styles.textArea}
                        value={changes}
                        onChange={(e) => setChanges(e.target.value)}
                        placeholder="현재 논의된 내용 중 변경하고 싶은 부분을 자유롭게 기술하세요."
                    />
                </div>

                <button
                    className={styles.submitBtn}
                    onClick={handleSubmit}
                    disabled={isSubmitting}
                >
                    {isSubmitting ? '처리 중...' : '지시사항 적용 및 다음 라운드 시작'}
                </button>

                {phase === 'END_GATE' && (
                    <button
                        className={styles.submitBtn}
                        style={{ background: '#10b981', marginTop: '10px' }}
                        onClick={handleFinalize}
                        disabled={isSubmitting}
                    >
                        ✅ 최종 확정 및 리포트 생성
                    </button>
                )}
            </div>
        </div>
    )
}
