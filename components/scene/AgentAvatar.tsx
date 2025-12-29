'use client'

import { useRef, useEffect, useState, Suspense } from 'react'
import { useFrame } from '@react-three/fiber'
import { useGLTF, useAnimations } from '@react-three/drei'
import * as THREE from 'three'

interface AgentAvatarProps {
    modelPath: string
    position: [number, number, number]
    rotation?: [number, number, number]
    isSpeaking: boolean
    agentId: string
    fallbackColor: string
}

// 폴백 캐릭터 (3D 모델 로드 실패 시)
function FallbackAvatar({
    position,
    isSpeaking,
    color
}: {
    position: [number, number, number]
    isSpeaking: boolean
    color: string
}) {
    const meshRef = useRef<THREE.Mesh>(null)
    const [hue, setHue] = useState(0)

    useFrame((state, delta) => {
        if (meshRef.current) {
            // Idle 애니메이션: 위아래 움직임
            meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 2) * 0.05

            // Speaking 상태: 더 빠르게 움직임 + 스케일 변화
            if (isSpeaking) {
                meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 6) * 0.1
                meshRef.current.scale.setScalar(1 + Math.sin(state.clock.elapsedTime * 8) * 0.05)
            } else {
                meshRef.current.scale.setScalar(1)
            }
        }
    })

    return (
        <mesh ref={meshRef} position={position}>
            <capsuleGeometry args={[0.3, 0.8, 8, 16]} />
            <meshStandardMaterial
                color={color}
                emissive={isSpeaking ? color : '#000000'}
                emissiveIntensity={isSpeaking ? 0.3 : 0}
            />
        </mesh>
    )
}

// 3D 모델 캐릭터
function ModelAvatar({
    modelPath,
    position,
    rotation = [0, 0, 0],
    isSpeaking,
}: {
    modelPath: string
    position: [number, number, number]
    rotation?: [number, number, number]
    isSpeaking: boolean
}) {
    const group = useRef<THREE.Group>(null)
    const { scene, animations } = useGLTF(modelPath)
    const { actions, names } = useAnimations(animations, group)

    // 애니메이션 이름 매핑
    const getAnimationName = (type: 'idle' | 'talk') => {
        const patterns = type === 'idle'
            ? ['idle', 'Idle', 'IDLE', 'stand', 'Stand']
            : ['talk', 'Talk', 'TALK', 'speak', 'Speak', 'SPEAK', 'talking', 'Talking']

        return names.find(name =>
            patterns.some(pattern => name.toLowerCase().includes(pattern.toLowerCase()))
        ) || names[0]
    }

    useEffect(() => {
        const idleAnim = getAnimationName('idle')
        const talkAnim = getAnimationName('talk')

        if (isSpeaking && talkAnim && actions[talkAnim]) {
            // Talk 애니메이션으로 전환
            actions[talkAnim]?.reset().fadeIn(0.3).play()
            if (idleAnim && actions[idleAnim]) {
                actions[idleAnim]?.fadeOut(0.3)
            }
        } else if (idleAnim && actions[idleAnim]) {
            // Idle 애니메이션으로 전환
            actions[idleAnim]?.reset().fadeIn(0.3).play()
            if (talkAnim && actions[talkAnim]) {
                actions[talkAnim]?.fadeOut(0.3)
            }
        }
    }, [isSpeaking, actions, names])

    // Speaking 상태 시각적 강조
    useFrame((state) => {
        if (group.current && isSpeaking) {
            // 살짝 위아래 움직임 추가
            group.current.position.y = position[1] + Math.sin(state.clock.elapsedTime * 4) * 0.02
        }
    })

    return (
        <group ref={group} position={position} rotation={rotation}>
            <primitive object={scene} />
        </group>
    )
}

export default function AgentAvatar({
    modelPath,
    position,
    rotation,
    isSpeaking,
    agentId,
    fallbackColor,
}: AgentAvatarProps) {
    const [modelError, setModelError] = useState(false)

    // 모델 로드 실패 시 폴백
    if (modelError) {
        return (
            <FallbackAvatar
                position={position}
                isSpeaking={isSpeaking}
                color={fallbackColor}
            />
        )
    }

    return (
        <Suspense fallback={
            <FallbackAvatar
                position={position}
                isSpeaking={isSpeaking}
                color={fallbackColor}
            />
        }>
            <ErrorBoundary onError={() => setModelError(true)}>
                <ModelAvatar
                    modelPath={modelPath}
                    position={position}
                    rotation={rotation}
                    isSpeaking={isSpeaking}
                />
            </ErrorBoundary>
        </Suspense>
    )
}

// 에러 바운더리 컴포넌트
class ErrorBoundary extends React.Component<
    { children: React.ReactNode; onError: () => void },
    { hasError: boolean }
> {
    constructor(props: { children: React.ReactNode; onError: () => void }) {
        super(props)
        this.state = { hasError: false }
    }

    static getDerivedStateFromError() {
        return { hasError: true }
    }

    componentDidCatch() {
        this.props.onError()
    }

    render() {
        if (this.state.hasError) {
            return null
        }
        return this.props.children
    }
}

// React 임포트 추가
import React from 'react'
