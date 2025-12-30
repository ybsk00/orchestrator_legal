-- sessions 테이블의 status 제약 조건 수정
-- 'waiting' 상태를 허용하도록 변경

ALTER TABLE sessions DROP CONSTRAINT IF EXISTS sessions_status_check;

ALTER TABLE sessions ADD CONSTRAINT sessions_status_check 
CHECK (status IN ('active', 'waiting', 'completed', 'finalized', 'cancelled', 'paused'));
