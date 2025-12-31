-- =====================================================
-- v3.3 메시지 테이블 role 제약조건 업데이트
-- =====================================================

-- 기존 제약조건 삭제
ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_role_check;

-- 새로운 제약조건 추가 (Dev Project 역할 포함)
ALTER TABLE messages ADD CONSTRAINT messages_role_check CHECK (role IN (
    'user', 'agent1', 'agent2', 'agent3', 'verifier', 'system',
    'judge', 'claimant', 'opposing',
    'prd', 'tech', 'ux', 'dm'
));
