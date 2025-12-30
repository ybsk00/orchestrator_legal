import React, { useState } from 'react'
import styles from './SteeringPanel.module.css'

interface SteeringPanelProps {
    sessionId: string
    onSkip: () => void
    onInput: (steering: any) => void
    onFinalize: () => void
}

export default function SteeringPanel({
    sessionId,
    onSkip,
    onInput,
    onFinalize
}: SteeringPanelProps) {
    const [mode, setMode] = useState<'view' | 'edit'>('view')
    const [goal, setGoal] = useState('')
    const [priority, setPriority] = useState('')
    const [constraints, setConstraints] = useState<string[]>([])
    const [exclusions, setExclusions] = useState<string[]>([])
    const [freeText, setFreeText] = useState('')

    const [constraintInput, setConstraintInput] = useState('')
    const [exclusionInput, setExclusionInput] = useState('')
    const [isSubmitting, setIsSubmitting] = useState(false)

    const handleAddConstraint = () => {
        if (constraintInput.trim()) {
            setConstraints([...constraints, constraintInput.trim()])
            setConstraintInput('')
        }
    }

    const handleAddExclusion = () => {
        if (exclusionInput.trim()) {
            setExclusions([...exclusions, exclusionInput.trim()])
            setExclusionInput('')
        }
    }

    const handleSubmit = async () => {
        setIsSubmitting(true)
        const steeringData = {
            goal,
            priority,
            constraints,
            exclusions,
            free_text: freeText
        }

        try {
            await onInput(steeringData)
        } catch (error) {
            console.error('Failed to submit steering:', error)
            setIsSubmitting(false)
        }
    }

    if (mode === 'view') {
        return (
            <div className={styles.panel}>
                <div className={styles.actions}>
                    <button className={styles.skipBtn} onClick={onSkip} disabled={isSubmitting}>
                        ⏩ 그대로 진행 (Skip)
                    </button>
                    <button className={styles.editBtn} onClick={() => setMode('edit')} disabled={isSubmitting}>
                        ✏️ 방향/조건 추가
                    </button>
                    <button className={styles.finalizeBtn} onClick={onFinalize} disabled={isSubmitting}>
                        🛑 여기서 마무리
                    </button>
                </div>
            </div>
        )
    }

    return (
        <div className={styles.panel}>
            <h3>🎯 방향 제어 (Steering)</h3>
            <p className={styles.description}>
                다음 라운드 에이전트들에게 지시할 내용을 입력하세요.
            </p>

            <div className={styles.formGroup}>
                <label>목표 (Goal)</label>
                <input
                    type="text"
                    value={goal}
                    onChange={(e) => setGoal(e.target.value)}
                    placeholder="예: 비용 절감을 최우선으로 검토"
                />
            </div>

            <div className={styles.formGroup}>
                <label>우선순위 (Priority)</label>
                <input
                    type="text"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    placeholder="예: 보안 > 비용 > 편의성"
                />
            </div>

            <div className={styles.formGroup}>
                <label>필수 제약조건 (Constraints)</label>
                <div className={styles.tagInput}>
                    <input
                        type="text"
                        value={constraintInput}
                        onChange={(e) => setConstraintInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddConstraint()}
                        placeholder="예: 2주 내 완료"
                    />
                    <button onClick={handleAddConstraint}>추가</button>
                </div>
                <div className={styles.tags}>
                    {constraints.map((c, i) => (
                        <span key={i} className={styles.tag}>
                            {c} <button onClick={() => setConstraints(constraints.filter((_, idx) => idx !== i))}>×</button>
                        </span>
                    ))}
                </div>
            </div>

            <div className={styles.formGroup}>
                <label>금지 사항 (Exclusions)</label>
                <div className={styles.tagInput}>
                    <input
                        type="text"
                        value={exclusionInput}
                        onChange={(e) => setExclusionInput(e.target.value)}
                        onKeyPress={(e) => e.key === 'Enter' && handleAddExclusion()}
                        placeholder="예: 외부 API 사용 금지"
                    />
                    <button onClick={handleAddExclusion}>추가</button>
                </div>
                <div className={styles.tags}>
                    {exclusions.map((e, i) => (
                        <span key={i} className={`${styles.tag} ${styles.exclusion}`}>
                            {e} <button onClick={() => setExclusions(exclusions.filter((_, idx) => idx !== i))}>×</button>
                        </span>
                    ))}
                </div>
            </div>

            <div className={styles.formGroup}>
                <label>추가 지시사항 (Free Text)</label>
                <textarea
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
    )
}
