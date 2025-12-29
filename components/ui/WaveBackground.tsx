'use client'

import React, { useRef, useMemo } from 'react'
import { Canvas, useFrame } from '@react-three/fiber'
import * as THREE from 'three'

function WaveParticles() {
    const count = 2000
    const mesh = useRef<THREE.InstancedMesh>(null)
    const dummy = useMemo(() => new THREE.Object3D(), [])

    const particles = useMemo(() => {
        const temp = []
        for (let i = 0; i < count; i++) {
            const t = Math.random() * 100
            const factor = 20 + Math.random() * 100
            const speed = 0.01 + Math.random() / 200
            const xFactor = -50 + Math.random() * 100
            const yFactor = -50 + Math.random() * 100
            const zFactor = -50 + Math.random() * 100
            temp.push({ t, factor, speed, xFactor, yFactor, zFactor, mx: 0, my: 0 })
        }
        return temp
    }, [count])

    useFrame((state) => {
        if (!mesh.current) return

        particles.forEach((particle, i) => {
            let { t, factor, speed, xFactor, yFactor, zFactor } = particle
            t = particle.t += speed / 2
            const a = Math.cos(t) + Math.sin(t * 1) / 10
            const b = Math.sin(t) + Math.cos(t * 2) / 10
            const s = Math.cos(t)

            // 파동 움직임 계산
            dummy.position.set(
                (particle.mx / 10) * a + xFactor + Math.cos((t / 10) * factor) + (Math.sin(t * 1) * factor) / 10,
                (particle.my / 10) * b + yFactor + Math.sin((t / 10) * factor) + (Math.cos(t * 2) * factor) / 10,
                (particle.my / 10) * b + zFactor + Math.cos((t / 10) * factor) + (Math.sin(t * 3) * factor) / 10
            )
            dummy.scale.set(s, s, s)
            dummy.rotation.set(s * 5, s * 5, s * 5)
            dummy.updateMatrix()

            mesh.current!.setMatrixAt(i, dummy.matrix)
        })
        mesh.current.instanceMatrix.needsUpdate = true
    })

    return (
        <instancedMesh ref={mesh} args={[undefined, undefined, count]}>
            <dodecahedronGeometry args={[0.2, 0]} />
            <meshPhongMaterial color="#4a4e69" transparent opacity={0.8} />
        </instancedMesh>
    )
}

function GridWave() {
    const mesh = useRef<THREE.Points>(null)

    // 그리드 포인트 생성
    const { positions, colors } = useMemo(() => {
        const positions = []
        const colors = []
        const width = 100
        const depth = 100
        const sep = 1.5

        for (let x = 0; x < width; x++) {
            for (let z = 0; z < depth; z++) {
                const posX = (x - width / 2) * sep
                const posZ = (z - depth / 2) * sep
                const posY = 0
                positions.push(posX, posY, posZ)

                // 그라데이션 컬러
                const color = new THREE.Color()
                color.setHSL(0.6 + (x / width) * 0.2, 0.8, 0.5) // Blue-Purple range
                colors.push(color.r, color.g, color.b)
            }
        }
        return {
            positions: new Float32Array(positions),
            colors: new Float32Array(colors)
        }
    }, [])

    useFrame((state) => {
        if (!mesh.current) return

        const time = state.clock.getElapsedTime()
        const positions = mesh.current.geometry.attributes.position.array as Float32Array

        let i = 0
        const width = 100
        const depth = 100

        for (let x = 0; x < width; x++) {
            for (let z = 0; z < depth; z++) {
                // 사인파 애니메이션
                const y = Math.sin(x / 5 + time) * 2 + Math.sin(z / 5 + time) * 2
                positions[i + 1] = y - 10 // Y축 위치 업데이트 (약간 아래로 배치)
                i += 3
            }
        }

        mesh.current.geometry.attributes.position.needsUpdate = true
    })

    return (
        <points ref={mesh} rotation={[0.2, 0, 0]}> {/* 약간 기울임 */}
            <bufferGeometry>
                <bufferAttribute
                    attach="attributes-position"
                    count={positions.length / 3}
                    array={positions}
                    itemSize={3}
                />
                <bufferAttribute
                    attach="attributes-color"
                    count={colors.length / 3}
                    array={colors}
                    itemSize={3}
                />
            </bufferGeometry>
            <pointsMaterial
                size={0.15}
                vertexColors
                transparent
                opacity={0.6}
                sizeAttenuation
            />
        </points>
    )
}

export default function WaveBackground() {
    return (
        <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 0, pointerEvents: 'none' }}>
            <Canvas camera={{ position: [0, 20, 50], fov: 60 }}>
                <color attach="background" args={['#050505']} />
                <fog attach="fog" args={['#050505', 20, 100]} />
                <ambientLight intensity={0.5} />
                <pointLight position={[10, 10, 10]} />
                <GridWave />
            </Canvas>
        </div>
    )
}
