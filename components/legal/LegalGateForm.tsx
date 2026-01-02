'use client'

import { useState, useEffect } from 'react'
import styles from './LegalGateForm.module.css'

interface LegalGateFormProps {
    sessionId: string
    roundIndex: number
    phase: string  // USER_GATE, END_GATE, FACTS_GATE
    caseType: string
    openIssues?: string[]
    onSubmit: (result: { status: string; next_round?: number }) => void
}

// Round별 Goal 옵션
const GOAL_OPTIONS = [
    { value: 'win_rate', label: '승소 가능성 분석', icon: '⚖️' },
    { value: 'risk_min', label: '리스크 최소화', icon: '🛡️' },
    { value: 'settlement', label: '조기종결/합의', icon: '🤝' },
    { value: 'evidence_first', label: '증거 보강 우선', icon: '📂' },
]

// Round 2 입증 우선순위
const PROOF_PRIORITY_OPTIONS = [
    { value: 'key_evidence', label: '핵심 증거 확보', icon: '📌' },
    { value: 'procedural_defense', label: '절차적 방어', icon: '📋' },
    { value: 'damage_calc', label: '손해액 산정', icon: '💰' },
    { value: 'testimony', label: '증인/진술 확보', icon: '🗣️' },
]

// 증거 수준
const EVIDENCE_LEVEL_OPTIONS = [
    { value: 'sufficient', label: '충분', color: '#10b981' },
    { value: 'partial', label: '일부 보유', color: '#f59e0b' },
    { value: 'insufficient', label: '부족', color: '#ef4444' },
]

// 제약조건
const CONSTRAINT_OPTIONS = [
    { value: 'deadline_2weeks', label: '2주 내 처리 필요' },
    { value: 'budget_limit', label: '비용 제한' },
    { value: 'no_external_counsel', label: '외부 자문 없이 처리' },
    { value: 'no_personal_data_exposure', label: '개인정보 노출 금지' },
]

// Round 3 END 액션
const END_ACTION_OPTIONS = [
    { value: 'finalize', label: '최종 리포트 생성', icon: '📑' },
    { value: 'extend_once', label: '1회 추가 논의', icon: '🔄' },
    { value: 'new_session', label: '새 세션 시작', icon: '➕' },
]

// 리포트 스타일
const REPORT_STYLE_OPTIONS = [
    { value: 'risk', label: '리스크 중심', icon: '⚠️' },
    { value: 'strategy', label: '전략 중심', icon: '🎯' },
    { value: 'settlement', label: '합의안 중심', icon: '🤝' },
]

export default function LegalGateForm({
    sessionId,
    roundIndex,
    phase,
    caseType,
    openIssues = [],
    onSubmit,
}: LegalGateFormProps) {
    // Round 1 필수
    const [focusIssue, setFocusIssue] = useState('')
    const [goal, setGoal] = useState('')

    // Round 2 필수
    const [proofPriority, setProofPriority] = useState('')
    const [evidenceLevel, setEvidenceLevel] = useState('')
    const [constraints, setConstraints] = useState<string[]>([])

    // Round 3 필수
    const [endAction, setEndAction] = useState('')
    const [reportStyle, setReportStyle] = useState('')

    // Advanced (모든 라운드)
    const [showAdvanced, setShowAdvanced] = useState(false)
    const [stance, setStance] = useState('')
    const [exclusions, setExclusions] = useState<string[]>([])
    const [notes, setNotes] = useState('')

    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const [isSubmitted, setIsSubmitted] = useState(false)  // 제출 완료 상태 추적

    // 필수 필드 검증
    const isValid = () => {
        if (phase === 'FACTS_GATE') {
            return true // Facts Gate는 추가 입력만 받음
        }
        if (roundIndex === 1 || phase === 'USER_GATE' && roundIndex <= 1) {
            return focusIssue.trim() !== '' && goal !== ''
        }
        if (roundIndex === 2) {
            return proofPriority !== '' && evidenceLevel !== '' && constraints.length > 0
        }
        if (roundIndex === 3 || phase === 'END_GATE') {
            return endAction !== '' && reportStyle !== ''
        }
        return true
    }

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError(null)

        try {
            const response = await fetch(`/api/sessions/${sessionId}/legal-steering`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    focus_issue: focusIssue,
                    goal,
                    proof_priority: proofPriority,
                    evidence_level: evidenceLevel,
                    constraints,
                    end_action: endAction,
                    report_style: reportStyle,
                    stance,
                    exclusions,
                    notes,
                }),
            })

            if (!response.ok) {
                throw new Error('Steering 제출 실패')
            }

            const data = await response.json()
            setIsSubmitted(true)  // 성공 시 제출 완료 상태로 변경
            onSubmit(data)
        } catch (err) {
            // 에러 발생 시 사용자에게 알리고 재시도 가능하게 함
            const errorMessage = err instanceof Error ? err.message : '요청 처리 중 오류가 발생했습니다.'
            console.warn('Steering submission error:', errorMessage)
            setError('잠시 후 다시 시도해주세요. (서버가 아직 준비 중일 수 있습니다)')
        } finally {
            setIsLoading(false)
        }
    }

    const toggleConstraint = (value: string) => {
        setConstraints(prev =>
            prev.includes(value)
                ? prev.filter(c => c !== value)
                : [...prev, value]
        )
    }

    const getRoundTitle = () => {
        if (phase === 'FACTS_GATE') return '📋 사실관계 보완'
        if (phase === 'END_GATE') return '📑 최종 선택'
        return `🎯 Round ${roundIndex} 방향 설정`
    }

    const getRoundDescription = () => {
        if (phase === 'FACTS_GATE') return '누락된 사실관계를 보완해주세요.'
        if (phase === 'END_GATE') return '시뮬레이션을 마무리하거나 추가 논의를 진행하세요.'
        if (roundIndex === 1) return 'AI 토론의 집중 쟁점과 목표를 설정하세요.'
        if (roundIndex === 2) return '입증 우선순위와 증거 수준, 제약조건을 설정하세요.'
        return '최종 리포트 스타일을 선택하세요.'
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h3>{getRoundTitle()}</h3>
                <p className={styles.description}>{getRoundDescription()}</p>
            </div>

            <form onSubmit={handleSubmit} className={styles.form}>
                {/* Round 1: Focus & Goal */}
                {(roundIndex === 1 || phase === 'FACTS_GATE') && (
                    <>
                        <div className={styles.formGroup}>
                            <label>
                                <span className={styles.required}>*</span> 집중 쟁점
                            </label>
                            {openIssues.length > 0 ? (
                                <div className={styles.issueOptions}>
                                    {openIssues.map((issue, idx) => (
                                        <button
                                            key={idx}
                                            type="button"
                                            className={`${styles.issueOption} ${focusIssue === issue ? styles.selected : ''}`}
                                            onClick={() => setFocusIssue(issue)}
                                        >
                                            {issue}
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <input
                                    type="text"
                                    value={focusIssue}
                                    onChange={(e) => setFocusIssue(e.target.value)}
                                    placeholder="집중할 핵심 쟁점을 입력하세요"
                                    className={styles.textInput}
                                />
                            )}
                        </div>

                        <div className={styles.formGroup}>
                            <label>
                                <span className={styles.required}>*</span> 목표
                            </label>
                            <div className={styles.optionGrid}>
                                {GOAL_OPTIONS.map(opt => (
                                    <button
                                        key={opt.value}
                                        type="button"
                                        className={`${styles.optionCard} ${goal === opt.value ? styles.selected : ''}`}
                                        onClick={() => setGoal(opt.value)}
                                    >
                                        <span className={styles.optionIcon}>{opt.icon}</span>
                                        <span>{opt.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </>
                )}

                {/* Round 2: Proof, Evidence, Constraints */}
                {roundIndex === 2 && phase === 'USER_GATE' && (
                    <>
                        <div className={styles.formGroup}>
                            <label>
                                <span className={styles.required}>*</span> 입증 우선순위
                            </label>
                            <div className={styles.optionGrid}>
                                {PROOF_PRIORITY_OPTIONS.map(opt => (
                                    <button
                                        key={opt.value}
                                        type="button"
                                        className={`${styles.optionCard} ${proofPriority === opt.value ? styles.selected : ''}`}
                                        onClick={() => setProofPriority(opt.value)}
                                    >
                                        <span className={styles.optionIcon}>{opt.icon}</span>
                                        <span>{opt.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className={styles.formGroup}>
                            <label>
                                <span className={styles.required}>*</span> 증거 수준
                            </label>
                            <div className={styles.levelOptions}>
                                {EVIDENCE_LEVEL_OPTIONS.map(opt => (
                                    <button
                                        key={opt.value}
                                        type="button"
                                        className={`${styles.levelOption} ${evidenceLevel === opt.value ? styles.selected : ''}`}
                                        style={{ '--level-color': opt.color } as React.CSSProperties}
                                        onClick={() => setEvidenceLevel(opt.value)}
                                    >
                                        {opt.label}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className={styles.formGroup}>
                            <label>
                                <span className={styles.required}>*</span> 제약조건 (1개 이상)
                            </label>
                            <div className={styles.checkboxGroup}>
                                {CONSTRAINT_OPTIONS.map(opt => (
                                    <label key={opt.value} className={styles.checkbox}>
                                        <input
                                            type="checkbox"
                                            checked={constraints.includes(opt.value)}
                                            onChange={() => toggleConstraint(opt.value)}
                                        />
                                        <span>{opt.label}</span>
                                    </label>
                                ))}
                            </div>
                        </div>
                    </>
                )}

                {/* Round 3 / END_GATE */}
                {(roundIndex === 3 || phase === 'END_GATE') && (
                    <>
                        <div className={styles.formGroup}>
                            <label>
                                <span className={styles.required}>*</span> 종료 액션
                            </label>
                            <div className={styles.optionGrid}>
                                {END_ACTION_OPTIONS.map(opt => (
                                    <button
                                        key={opt.value}
                                        type="button"
                                        className={`${styles.optionCard} ${endAction === opt.value ? styles.selected : ''}`}
                                        onClick={() => setEndAction(opt.value)}
                                    >
                                        <span className={styles.optionIcon}>{opt.icon}</span>
                                        <span>{opt.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className={styles.formGroup}>
                            <label>
                                <span className={styles.required}>*</span> 리포트 스타일
                            </label>
                            <div className={styles.optionGrid}>
                                {REPORT_STYLE_OPTIONS.map(opt => (
                                    <button
                                        key={opt.value}
                                        type="button"
                                        className={`${styles.optionCard} ${reportStyle === opt.value ? styles.selected : ''}`}
                                        onClick={() => setReportStyle(opt.value)}
                                    >
                                        <span className={styles.optionIcon}>{opt.icon}</span>
                                        <span>{opt.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </>
                )}

                {/* Advanced Options Toggle */}
                <button
                    type="button"
                    className={styles.advancedToggle}
                    onClick={() => setShowAdvanced(!showAdvanced)}
                >
                    {showAdvanced ? '▲ 고급 옵션 접기' : '▼ 고급 옵션 펼치기'}
                </button>

                {showAdvanced && (
                    <div className={styles.advancedSection}>
                        <div className={styles.formGroup}>
                            <label>입장 (Stance)</label>
                            <div className={styles.levelOptions}>
                                {['강경', '중립', '유연'].map(s => (
                                    <button
                                        key={s}
                                        type="button"
                                        className={`${styles.levelOption} ${stance === s ? styles.selected : ''}`}
                                        onClick={() => setStance(s)}
                                    >
                                        {s}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div className={styles.formGroup}>
                            <label>추가 메모</label>
                            <textarea
                                value={notes}
                                onChange={(e) => setNotes(e.target.value)}
                                placeholder="AI에게 전달할 추가 지시사항 (선택)"
                                rows={3}
                                maxLength={300}
                            />
                            <span className={styles.charCount}>{notes.length}/300</span>
                        </div>
                    </div>
                )}

                {error && (
                    <div className={styles.error}>
                        ⚠️ {error}
                    </div>
                )}

                <button
                    type="submit"
                    className={styles.submitBtn}
                    disabled={!isValid() || isLoading || isSubmitted}
                >
                    {isLoading ? '처리 중...' : isSubmitted ? '✓ 제출됨' : phase === 'END_GATE' ? '완료' : '다음 라운드 시작 →'}
                </button>
            </form>
        </div>
    )
}
