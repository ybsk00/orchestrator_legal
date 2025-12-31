'use client'

import { useEffect, useState, useMemo } from 'react'
import { createClient } from '@/lib/supabase/client'

export interface Message {
    id: string
    role: 'user' | 'agent1' | 'agent2' | 'agent3' | 'verifier' | 'system' | 'judge' | 'claimant' | 'opposing'
    content: string
    roundIndex: number
    phase: string
    isStreaming?: boolean
}

export function useRealtimeMessages(sessionId: string | null) {
    const [messages, setMessages] = useState<Message[]>([])
    const [isLoading, setIsLoading] = useState(true)

    const [isConnected, setIsConnected] = useState(false)

    // 인증된 Supabase 클라이언트 (useMemo로 안정적 인스턴스)
    const supabase = useMemo(() => createClient(), [])

    useEffect(() => {
        if (!sessionId) return

        // 1. 초기 메시지 로드
        const fetchMessages = async () => {
            try {
                const { data, error } = await supabase
                    .from('messages')
                    .select('*')
                    .eq('session_id', sessionId)
                    .order('created_at', { ascending: true })

                if (error) throw error

                if (data) {
                    setMessages(data.map(msg => ({
                        id: msg.id,
                        role: msg.role,
                        content: msg.content_text, // DB 컬럼명: content_text
                        roundIndex: msg.round_index,
                        phase: msg.phase,
                        isStreaming: false
                    })))
                }
            } catch (error) {
                console.error('Failed to fetch messages:', error)
            } finally {
                setIsLoading(false)
            }
        }

        fetchMessages()

        // 2. Realtime 구독 설정
        const channel = supabase
            .channel(`session-${sessionId}`)
            .on(
                'postgres_changes',
                {
                    event: 'INSERT',
                    schema: 'public',
                    table: 'messages',
                    filter: `session_id=eq.${sessionId}`
                },
                (payload) => {
                    const newMsg = payload.new
                    setMessages(prev => {
                        // 중복 방지
                        if (prev.some(msg => msg.id === newMsg.id)) return prev

                        return [...prev, {
                            id: newMsg.id,
                            role: newMsg.role,
                            content: newMsg.content_text,
                            roundIndex: newMsg.round_index,
                            phase: newMsg.phase,
                            isStreaming: false
                        }]
                    })
                }
            )
            .subscribe((status: string) => {
                if (status === 'SUBSCRIBED') {
                    setIsConnected(true)
                } else if (status === 'CLOSED' || status === 'CHANNEL_ERROR') {
                    setIsConnected(false)
                }
            })

        return () => {
            supabase.removeChannel(channel)
            setIsConnected(false)
        }
    }, [sessionId, supabase])

    return { messages, isLoading, isConnected }
}
