'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import styles from './page.module.css'

export default function LoginPage() {
    const [email, setEmail] = useState('')
    const [password, setPassword] = useState('')
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState<string | null>(null)
    const router = useRouter()
    const supabase = createClient()

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault()
        setLoading(true)
        setError(null)

        try {
            const { error } = await supabase.auth.signInWithPassword({
                email,
                password,
            })

            if (error) throw error

            router.push('/dashboard')
            router.refresh()
        } catch (err: any) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const handleSignUp = async () => {
        setLoading(true)
        setError(null)

        try {
            const { error } = await supabase.auth.signUp({
                email,
                password,
                options: {
                    emailRedirectTo: `${location.origin}/auth/callback`,
                },
            })

            if (error) throw error

            alert('회원가입 확인 이메일을 발송했습니다.')
        } catch (err: any) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className={styles.container}>
            <div className={styles.card}>
                <h1 className={styles.title}>로그인</h1>
                <p className={styles.subtitle}>오케스트레이터 시스템에 접속하세요</p>

                <form onSubmit={handleLogin} className={styles.form}>
                    <div className={styles.inputGroup}>
                        <label htmlFor="email">이메일</label>
                        <input
                            id="email"
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            placeholder="name@example.com"
                            required
                        />
                    </div>

                    <div className={styles.inputGroup}>
                        <label htmlFor="password">비밀번호</label>
                        <input
                            id="password"
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="••••••••"
                            required
                        />
                    </div>

                    {error && <div className={styles.error}>{error}</div>}

                    <button type="submit" className={styles.loginButton} disabled={loading}>
                        {loading ? '처리 중...' : '로그인'}
                    </button>

                    <button
                        type="button"
                        className={styles.signupButton}
                        onClick={handleSignUp}
                        disabled={loading}
                    >
                        회원가입
                    </button>
                </form>
            </div>
        </div>
    )
}
