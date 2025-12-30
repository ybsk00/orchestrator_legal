-- ======================================
-- 이전 회의 데이터 복구 SQL
-- 특정 사용자 ID로 기존 세션 업데이트
-- ======================================

-- 1. 먼저 사용자 ID를 확인합니다
-- Supabase Dashboard > Authentication > Users에서 사용자 ID를 찾으세요

-- 2. 아래 쿼리에서 'YOUR_USER_ID'를 실제 사용자 ID로 교체하세요
-- 예: '12345678-1234-1234-1234-123456789012'

-- 모든 user_id가 NULL인 세션을 특정 사용자에게 할당
UPDATE sessions 
SET user_id = 'YOUR_USER_ID'
WHERE user_id IS NULL;

-- 또는 특정 날짜 이후의 세션만 업데이트
-- UPDATE sessions 
-- SET user_id = 'YOUR_USER_ID'
-- WHERE user_id IS NULL 
-- AND created_at > '2024-12-01';

-- 3. 확인 쿼리
SELECT id, topic, category, user_id, created_at 
FROM sessions 
ORDER BY created_at DESC 
LIMIT 20;
