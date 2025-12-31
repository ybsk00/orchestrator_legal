'use client'

import { useRef, useMemo, useState } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import { Points, PointMaterial, Line } from '@react-three/drei'
import * as THREE from 'three'

function Network({ count = 100, mouse }: { count?: number; mouse: React.MutableRefObject<[number, number]> }) {
    const points = useMemo(() => {
        const p = new Float32Array(count * 3)
        for (let i = 0; i < count; i++) {
            p[i * 3] = (Math.random() - 0.5) * 10
            p[i * 3 + 1] = (Math.random() - 0.5) * 10
            p[i * 3 + 2] = (Math.random() - 0.5) * 10
        }
        return p
    }, [count])

    const ref = useRef<THREE.Points>(null)
    const linesRef = useRef<THREE.LineSegments>(null)

    useFrame((state) => {
        if (!ref.current) return

        // Rotate the entire cloud slowly
        ref.current.rotation.x += 0.001
        ref.current.rotation.y += 0.001

        // Mouse interaction
        const positions = ref.current.geometry.attributes.position.array as Float32Array
        const time = state.clock.getElapsedTime()

        for (let i = 0; i < count; i++) {
            const x = positions[i * 3]
            const y = positions[i * 3 + 1]
            const z = positions[i * 3 + 2]

            // Gentle floating motion
            positions[i * 3 + 1] += Math.sin(time + x) * 0.002

            // Mouse repulsion/attraction (simplified 2D projection)
            // Note: Proper 3D mouse interaction requires raycasting, but for background effect,
            // mapping normalized mouse coordinates to world space is often "good enough" for feel.
            const mx = (mouse.current[0] * 10)
            const my = (mouse.current[1] * 10)

            const dx = x - mx
            const dy = y - (-my) // Invert Y for 3D space
            const dist = Math.sqrt(dx * dx + dy * dy)

            if (dist < 2) {
                const force = (2 - dist) * 0.02
                positions[i * 3] += dx * force
                positions[i * 3 + 1] += dy * force
            }
        }
        ref.current.geometry.attributes.position.needsUpdate = true
    })

    return (
        <group>
            <Points ref={ref} positions={points} stride={3} frustumCulled={false}>
                <PointMaterial
                    transparent
                    color="#6366f1"
                    size={0.05}
                    sizeAttenuation={true}
                    depthWrite={false}
                    opacity={0.8}
                />
            </Points>
        </group>
    )
}

export default function NeuralNetworkBackground() {
    const mouse = useRef<[number, number]>([0, 0])

    return (
        <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0, pointerEvents: 'none' }}>
            <Canvas
                camera={{ position: [0, 0, 5], fov: 60 }}
                onMouseMove={(e) => {
                    // Normalize mouse coordinates -1 to 1
                    mouse.current = [
                        (e.clientX / window.innerWidth) * 2 - 1,
                        -(e.clientY / window.innerHeight) * 2 + 1
                    ]
                }}
            >
                <color attach="background" args={['#050508']} />
                <ambientLight intensity={0.5} />
                <Network mouse={mouse} />
                <fog attach="fog" args={['#050508', 5, 15]} />
            </Canvas>
        </div>
    )
}
