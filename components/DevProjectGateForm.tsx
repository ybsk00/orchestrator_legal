'use client'

import React, { useState } from 'react'
import { useRouter } from 'next/navigation'
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
    const router = useRouter()
    const [mode, setMode] = useState<'view' | 'edit'>('view')
    const [focus, setFocus] = useState('')
    const [goal, setGoal] = useState('')
    const [constraints, setConstraints] = useState<string[]>([])
    const [freeText, setFreeText] = useState('')
    const [constraintInput, setConstraintInput] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)

    const isEndGate = phase === 'END_GATE'

    const handleAddConstraint = () => {
        if (constraintInput.trim()) {
            setConstraints([...constraints, constraintInput.trim()])
            setConstraintInput('')
        }
    }

    const handleSubmit = async () => {
        setIsSubmitting(true)
        try {
            const steeringData = { focus, goal, constraints, free_text: freeText }
            await onSubmit('input', steeringData)
        } catch (error) {
            console.warn('Steering submission warning:', error)
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleSkip = async () => {
        setIsSubmitting(true)
        try {
            await onSubmit('skip')
        } catch (error) {
            console.warn('Skip warning:', error)
        } finally {
            setIsSubmitting(false)
        }
    }

    const handleFinalize = async () => {
        setIsSubmitting(true)
        try {
            await onSubmit('finalize')
            router.push('/dashboard')
        } catch (error) {
            console.error('Failed to finalize:', error)
            router.push('/dashboard')
        }
    }

    // END_GATE: 3라운드 종료 - 최종 확정만 표시
    if (isEndGate) {
        return (
            <div className={styles.container}>
                {/* 라운드 요약 카드 */}
                {gateData && (
                    <GateSummaryCard
                        roundIndex={roundIndex}
                        decisionSummary={gateData.decision_summary || '요약 정보 없음'}
                        openIssues={gateData.open_issues || []}
                        verifierStatus={gateData.verifier_gate_status || 'Unknown'}
                    />
                )}

                {/* 종료 카드 */}
                <div className={styles.endGateCard}>
                    <h3>🏁 토론이 종료되었습니다 (Round 3)</h3>
                    <p className={styles.description}>
                        모든 라운드가 완료되었습니다. 최종 리포트를 생성하고 대시보드에서 결과를 확인하세요.
                    </p>
                    <button
                        className={styles.finalizeBtn}
                        onClick={handleFinalize}
                        disabled={isSubmitting}
                    >
                        {isSubmitting ? '처리 중...' : '✅ 최종 확정 및 리포트 생성'}
                    </button>
                </div>
            </div>
        )
    }

    // USER_GATE: 라운드 종료 후 사용자 개입 대기 (일반토론과 동일한 UI)
    return (
        <div className={styles.container}>
            {/* 라운드 요약 카드 */}
            {gateData && (
                <GateSummaryCard
                    roundIndex={roundIndex}
                    decisionSummary={gateData.decision_summary || '요약 정보 없음'}
                    openIssues={gateData.open_issues || []}
                    verifierStatus={gateData.verifier_gate_status || 'Unknown'}
                />
            )}

            {/* 간단한 3버튼 UI (view 모드) */}
            {mode === 'view' && (
                <div className={styles.actionsPanel}>
                    <button className={styles.skipBtn} onClick={handleSkip} disabled={isSubmitting}>
                        ⏩ 그대로 진행 (Skip)
                    </button>
                    <button className={styles.editBtn} onClick={() => setMode('edit')} disabled={isSubmitting}>
                        ✏️ 방향/조건 추가
                    </button>
                    <button className={styles.finalizeBtn} onClick={handleFinalize} disabled={isSubmitting}>
                        🛑 여기서 마무리
                    </button>
                </div>
            )}

            {/* Steering 입력 폼 (edit 모드) */}
            {mode === 'edit' && (
                <div className={styles.form}>
                    <div className={styles.header}>
                        <h3>🎯 방향 제어 (Steering)</h3>
                        <p className={styles.description}>
                            다음 라운드 에이전트들에게 지시할 내용을 입력하세요.
                        </p>
                    </div>

                    <div className={styles.formGroup}>
                        <label>목표 (Goal)</label>
                        <input
                            type="text"
                            className={styles.textInput}
                            value={goal}
                            onChange={(e) => setGoal(e.target.value)}
                            placeholder="예: 비용 절감을 최우선으로 검토"
                        />
                    </div>

                    <div className={styles.formGroup}>
                        <label>중점 분야 (Focus)</label>
                        <input
                            type="text"
                            className={styles.textInput}
                            value={focus}
                            onChange={(e) => setFocus(e.target.value)}
                            placeholder="예: 보안 > 비용 > 편의성"
                        />
                    </div>

                    <div className={styles.formGroup}>
                        <label>필수 제약조건 (Constraints)</label>
                        <div className={styles.tagInput}>
                            <input
                                type="text"
                                className={styles.textInput}
                                value={constraintInput}
                                onChange={(e) => setConstraintInput(e.target.value)}
                                onKeyPress={(e) => e.key === 'Enter' && handleAddConstraint()}
                                placeholder="예: 2주 내 완료"
                            />
                            <button className={styles.addBtn} onClick={handleAddConstraint}>추가</button>
                        </div>
                        <div className={styles.tags}>
                            {constraints.map((c, i) => (
                                <span key={i} className={styles.tag}>
                                    {c}
                                    <button onClick={() => setConstraints(constraints.filter((_, idx) => idx !== i))}>×</button>
                                </span>
                            ))}
                        </div>
                    </div>

                    <div className={styles.formGroup}>
                        <label>추가 지시사항 (Free Text)</label>
                        <textarea
                            className={styles.textArea}
                            value={freeText}
                            onChange={(e) => setFreeText(e.target.value)}
                            placeholder="자유롭게 지시사항을 입력하세요..."
                            rows={3}
                        />
                    </div>

                    <div className={styles.formActions}>
                        <button className={styles.cancelBtn} onClick={() => setMode('view')} disabled={isSubmitting}>
                            취소
                        </button>
                        <button className={styles.submitBtn} onClick={handleSubmit} disabled={isSubmitting}>
                            {isSubmitting ? '처리 중...' : '적용하고 다음 라운드 시작'}
                        </button>
                    </div>
                </div>
            )}
        </div>
    )
}
