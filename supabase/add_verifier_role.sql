-- messages 테이블의 role 체크 제약조건 수정
-- verifier 역할을 추가합니다

-- 기존 제약 조건 삭제
ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_role_check;

-- 새로운 제약 조건 추가 (verifier 포함)
ALTER TABLE messages ADD CONSTRAINT messages_role_check 
CHECK (role IN ('user', 'agent1', 'agent2', 'agent3', 'verifier', 'system'));
