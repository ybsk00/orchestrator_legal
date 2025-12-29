'use client'

import { useEffect, useState, useCallback, useRef } from 'react'

export interface SSEEvent {
    id: number
    type: string
    data: any
}

export function useSSE(sessionId: string | null) {
    const [isConnected, setIsConnected] = useState(false)
    const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null)
    const lastEventIdRef = useRef<number | null>(null)
    const eventSourceRef = useRef<EventSource | null>(null)

    const connect = useCallback(() => {
        if (!sessionId) return

        // 기존 연결 종료
        if (eventSourceRef.current) {
            eventSourceRef.current.close()
        }

        // Last-Event-ID 지원
        let url = `/api/sessions/${sessionId}/stream`
        if (lastEventIdRef.current) {
            url += `?lastEventId=${lastEventIdRef.current}`
        }

        const eventSource = new EventSource(url)
        eventSourceRef.current = eventSource

        eventSource.onopen = () => {
            setIsConnected(true)
        }

        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data)
                const sseEvent: SSEEvent = {
                    id: parseInt(event.lastEventId || '0'),
                    type: data.type || 'message',
                    data: data,
                }

                // Last-Event-ID 저장
                if (event.lastEventId) {
                    lastEventIdRef.current = parseInt(event.lastEventId)
                }

                setLastEvent(sseEvent)
            } catch (e) {
                console.error('Failed to parse SSE event:', e)
            }
        }

        eventSource.onerror = () => {
            setIsConnected(false)
            eventSource.close()

            // 재연결 시도
            setTimeout(() => {
                connect()
            }, 3000)
        }
    }, [sessionId])

    const disconnect = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close()
            eventSourceRef.current = null
        }
        setIsConnected(false)
    }, [])

    useEffect(() => {
        if (sessionId) {
            connect()
        }
        return () => {
            disconnect()
        }
    }, [sessionId, connect, disconnect])

    return { isConnected, lastEvent, connect, disconnect }
}
