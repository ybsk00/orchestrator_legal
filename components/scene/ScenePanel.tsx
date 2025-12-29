'use client'

import { useRef, useEffect } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, Environment, ContactShadows } from '@react-three/drei'
import AgentAvatar from './AgentAvatar'
import styles from './ScenePanel.module.css'

interface ScenePanelProps {
    activeSpeaker: string | null
}

export default function ScenePanel({ activeSpeaker }: ScenePanelProps) {
    return (
        <div className={styles.scenePanel}>
            <Canvas
                shadows
                dpr={[1, 1.5]}
                camera={{ position: [0, 1.5, 4], fov: 45 }}
                className={styles.canvas}
            >
                {/* 조명 */}
                <ambientLight intensity={0.4} />
                <directionalLight
                    position={[5, 5, 5]}
                    intensity={1}
                    castShadow
                    shadow-mapSize={[1024, 1024]}
                />
                <pointLight position={[-5, 5, -5]} intensity={0.5} />

                {/* 환경 */}
                <Environment preset="studio" />
                <ContactShadows
                    position={[0, -0.5, 0]}
                    opacity={0.4}
                    scale={10}
                    blur={2}
                />

                {/* 에이전트 캐릭터 3명 */}
                <group position={[0, 0, 0]}>
                    {/* Agent 1 - 왼쪽 */}
                    <AgentAvatar
                        modelPath="/models/agent1.glb"
                        position={[-1.5, -0.5, 0]}
                        rotation={[0, 0.3, 0]}
                        isSpeaking={activeSpeaker === 'agent1'}
                        agentId="agent1"
                        fallbackColor="#10b981"
                    />

                    {/* Agent 2 - 중앙 */}
                    <AgentAvatar
                        modelPath="/models/agent2.glb"
                        position={[0, -0.5, 0.5]}
                        rotation={[0, 0, 0]}
                        isSpeaking={activeSpeaker === 'agent2'}
                        agentId="agent2"
                        fallbackColor="#f59e0b"
                    />

                    {/* Agent 3 - 오른쪽 */}
                    <AgentAvatar
                        modelPath="/models/agent3.glb"
                        position={[1.5, -0.5, 0]}
                        rotation={[0, -0.3, 0]}
                        isSpeaking={activeSpeaker === 'agent3'}
                        agentId="agent3"
                        fallbackColor="#8b5cf6"
                    />
                </group>

                {/* 카메라 컨트롤 (개발용) */}
                <OrbitControls
                    enablePan={false}
                    enableZoom={false}
                    minPolarAngle={Math.PI / 4}
                    maxPolarAngle={Math.PI / 2}
                />
            </Canvas>

            {/* 에이전트 라벨 */}
            <div className={styles.agentLabels}>
                <span className={`${styles.label} ${activeSpeaker === 'agent1' ? styles.active : ''}`}>
                    Agent 1
                </span>
                <span className={`${styles.label} ${activeSpeaker === 'agent2' ? styles.active : ''}`}>
                    Agent 2
                </span>
                <span className={`${styles.label} ${activeSpeaker === 'agent3' ? styles.active : ''}`}>
                    Agent 3
                </span>
            </div>
        </div>
    )
}
