'use client'

import { useState } from 'react'
import styles from './FactsIntakeForm.module.css'

interface FactsIntakeFormProps {
    sessionId: string
    onSubmit: (data: FactsSubmitResponse) => void
    onCancel?: () => void
}

export interface FactsSubmitResponse {
    status: string
    confirmed_facts: string[]
    disputed_facts: string[]
    missing_facts_questions: string[]
    facts_gate_required: boolean
}

export default function FactsIntakeForm({ sessionId, onSubmit, onCancel }: FactsIntakeFormProps) {
    const [caseOverview, setCaseOverview] = useState('')
    const [parties, setParties] = useState('')
    const [facts, setFacts] = useState('')
    const [evidence, setEvidence] = useState('')
    const [isLoading, setIsLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setIsLoading(true)
        setError(null)

        try {
            const response = await fetch(`/api/sessions/${sessionId}/facts`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    case_overview: caseOverview,
                    parties: parties.split('\n').filter(p => p.trim()),
                    facts: facts,
                    evidence: evidence.split('\n').filter(e => e.trim()),
                }),
            })

            if (!response.ok) {
                throw new Error('사실관계 제출 실패')
            }

            const data: FactsSubmitResponse = await response.json()
            onSubmit(data)
        } catch (err) {
            setError(err instanceof Error ? err.message : '오류가 발생했습니다')
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <div className={styles.container}>
            <div className={styles.header}>
                <h2>📋 사실관계 입력</h2>
                <p className={styles.description}>
                    사건의 기본 정보를 입력해주세요. 입력된 내용을 바탕으로 AI가 사실관계를 분류합니다.
                </p>
            </div>

            <form onSubmit={handleSubmit} className={styles.form}>
                <div className={styles.formGroup}>
                    <label htmlFor="caseOverview">
                        <span className={styles.required}>*</span> 사건 개요
                    </label>
                    <textarea
                        id="caseOverview"
                        value={caseOverview}
                        onChange={(e) => setCaseOverview(e.target.value)}
                        placeholder="사건의 전체적인 개요를 설명해주세요. (예: 계약 위반으로 인한 손해배상 청구 사건...)"
                        rows={4}
                        required
                    />
                </div>

                <div className={styles.formGroup}>
                    <label htmlFor="parties">당사자</label>
                    <textarea
                        id="parties"
                        value={parties}
                        onChange={(e) => setParties(e.target.value)}
                        placeholder="당사자를 줄바꿈으로 구분하여 입력해주세요.&#10;예:&#10;원고: 홍길동&#10;피고: 주식회사 OO"
                        rows={3}
                    />
                </div>

                <div className={styles.formGroup}>
                    <label htmlFor="facts">
                        <span className={styles.required}>*</span> 사실관계
                    </label>
                    <textarea
                        id="facts"
                        value={facts}
                        onChange={(e) => setFacts(e.target.value)}
                        placeholder="주요 사실관계를 상세히 기술해주세요.&#10;시간 순서대로 작성하면 분석에 도움이 됩니다."
                        rows={8}
                        required
                    />
                </div>

                <div className={styles.formGroup}>
                    <label htmlFor="evidence">보유 증거</label>
                    <textarea
                        id="evidence"
                        value={evidence}
                        onChange={(e) => setEvidence(e.target.value)}
                        placeholder="보유 중인 증거를 줄바꿈으로 구분하여 입력해주세요.&#10;예:&#10;계약서 사본&#10;이메일 교신 내역&#10;업무 일지"
                        rows={4}
                    />
                </div>

                {error && (
                    <div className={styles.error}>
                        ⚠️ {error}
                    </div>
                )}

                <div className={styles.actions}>
                    {onCancel && (
                        <button type="button" onClick={onCancel} className={styles.cancelBtn}>
                            취소
                        </button>
                    )}
                    <button 
                        type="submit" 
                        className={styles.submitBtn}
                        disabled={isLoading || !caseOverview.trim() || !facts.trim()}
                    >
                        {isLoading ? '분석 중...' : '사실관계 제출 →'}
                    </button>
                </div>
            </form>
        </div>
    )
}
