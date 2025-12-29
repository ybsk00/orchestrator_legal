# 3 에이전트 오케스트레이터

Google Gemini 3 Pro를 활용한 3개 AI 에이전트 토론형 의사결정 시스템

## 아키텍처

```
Vercel 단일 프로젝트
├── Next.js (React) - UI/라우팅
├── Python FastAPI - Vercel Functions (/api/*)
└── Supabase - DB/Auth/Storage
```

## 프로젝트 구조

```
orchestrator/
├── app/                    # Next.js App Router (React UI)
│   ├── layout.tsx
│   ├── page.tsx           # 홈페이지 (카테고리 선택)
│   ├── globals.css
│   └── session/[id]/      # 세션 페이지
├── api/                    # Vercel Python Functions
│   └── index.py           # FastAPI 앱 노출
├── backend/               # Python 백엔드 로직
│   ├── main.py
│   ├── config.py
│   ├── agents/
│   ├── orchestrator/
│   ├── models/
│   ├── storage/
│   └── prompts/
├── lib/                   # 프론트엔드 라이브러리
│   ├── supabase.ts
│   └── useSSE.ts
├── supabase/
│   └── schema.sql        # DB 스키마
├── requirements.txt      # Python deps (Vercel이 인식)
├── package.json          # Next.js deps
├── vercel.json          # Vercel 설정
└── .env.example
```

## 설치 및 실행

### 로컬 개발

```bash
# 의존성 설치
npm install
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 키 입력

# Vercel CLI로 로컬 실행
npm install -g vercel
vercel dev
```

### Vercel 배포

1. GitHub 연결
2. Vercel 프로젝트 생성
3. 환경변수 설정:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `GEMINI_API_KEY`

### Supabase 설정

1. Supabase 프로젝트 생성
2. `supabase/schema.sql` 실행
3. RLS 정책 활성화 확인

## 환경변수

```bash
# 프론트엔드 공개
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# 서버 전용 (절대 프론트 노출 금지)
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
GEMINI_API_KEY=your-gemini-api-key
GEMINI_MODEL=gemini-3-pro-preview
```

## 주요 기능

- 4종 카테고리 (신규사업/마케팅/개발/영역)
- 라운드당 5턴 토론 프로토콜
- 최대 3라운드 사이클
- 조기 종료 (/stop 명령어 또는 마무리 버튼)
- SSE 스트리밍 (Last-Event-ID 지원)
- Agent3 Finalizer가 최종 결과물 생성
