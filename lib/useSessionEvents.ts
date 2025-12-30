import { useEffect, useState } from 'react'

export interface GateData {
    round_index: number
    phase: string
    decision_summary: string
    what_changed: string[]
    open_issues: string[]
    verifier_gate_status: string
}

export function useSessionEvents(sessionId: string | null) {
    const [gateData, setGateData] = useState<GateData | null>(null)
    const [isConnected, setIsConnected] = useState(false)

    useEffect(() => {
        if (!sessionId) return

        const eventSource = new EventSource(`/api/sessions/${sessionId}/events`)

        eventSource.onopen = () => {
            console.log('[SSE] Connected')
            setIsConnected(true)
        }

        eventSource.onerror = (err) => {
            console.error('[SSE] Error:', err)
            setIsConnected(false)
            eventSource.close()
        }

        // ROUND_END 이벤트 수신
        eventSource.addEventListener('ROUND_END', (event) => {
            try {
                const data = JSON.parse(event.data)
                console.log('[SSE] ROUND_END:', data)

                // 게이트 데이터가 포함된 경우 상태 업데이트
                if (data.phase === 'USER_GATE' || data.phase === 'END_GATE') {
                    setGateData(data)
                }
            } catch (e) {
                console.error('[SSE] Failed to parse ROUND_END data:', e)
            }
        })

        // ROUND_START 이벤트 수신 (게이트 데이터 초기화)
        eventSource.addEventListener('ROUND_START', () => {
            console.log('[SSE] ROUND_START')
            setGateData(null)
        })

        return () => {
            eventSource.close()
            setIsConnected(false)
        }
    }, [sessionId])

    return { gateData, isConnected }
}
