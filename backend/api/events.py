"""
SSE 이벤트 관리자

핵심 보완사항 반영:
- Last-Event-ID 지원으로 이벤트 유실 방지
- 이벤트 버퍼링으로 재전송 가능
"""
import asyncio
import itertools
from enum import Enum
from typing import Dict, List, Optional, AsyncGenerator
from pydantic import BaseModel
from datetime import datetime

from config import SSE_BUFFER_SIZE


class EventType(str, Enum):
    """SSE 이벤트 타입"""
    SPEAKER_CHANGE = "speaker_change"
    MESSAGE_STREAM_START = "message_stream_start"
    MESSAGE_STREAM_CHUNK = "message_stream_chunk"
    MESSAGE_STREAM_END = "message_stream_end"
    ROUND_START = "round_start"
    ROUND_END = "round_end"
    FINALIZE_START = "finalize_start"
    FINALIZE_DONE = "finalize_done"
    SESSION_END = "session_end"
    STOP_CONFIRM = "stop_confirm"  # 키워드 종료 확인 요청
    ERROR = "error"


class SSEEvent(BaseModel):
    """SSE 이벤트"""
    id: int
    type: EventType
    data: dict
    timestamp: datetime = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()
    
    def to_sse_format(self) -> str:
        """SSE 전송 포맷으로 변환"""
        import json
        return f"id: {self.id}\nevent: {self.type.value}\ndata: {json.dumps(self.data, ensure_ascii=False)}\n\n"


class SSEEventManager:
    """
    SSE 이벤트 관리자
    
    - 이벤트 생성 및 버퍼링
    - Last-Event-ID 기반 재전송
    - 세션별 이벤트 큐 관리
    """
    
    def __init__(self):
        self._event_counter = itertools.count(1)
        self._event_buffers: Dict[str, List[SSEEvent]] = {}
        self._event_queues: Dict[str, asyncio.Queue] = {}
        self._buffer_size = SSE_BUFFER_SIZE
    
    def get_or_create_queue(self, session_id: str) -> asyncio.Queue:
        """세션 이벤트 큐 생성 또는 반환"""
        if session_id not in self._event_queues:
            self._event_queues[session_id] = asyncio.Queue()
            self._event_buffers[session_id] = []
        return self._event_queues[session_id]
    
    async def emit(self, session_id: str, event_type: EventType, data: dict) -> SSEEvent:
        """
        이벤트 발생
        
        Args:
            session_id: 세션 ID
            event_type: 이벤트 타입
            data: 이벤트 데이터
            
        Returns:
            생성된 SSEEvent
        """
        event = SSEEvent(
            id=next(self._event_counter),
            type=event_type,
            data=data
        )
        
        # 버퍼에 저장
        if session_id not in self._event_buffers:
            self._event_buffers[session_id] = []
        
        buffer = self._event_buffers[session_id]
        buffer.append(event)
        
        # 버퍼 크기 제한
        if len(buffer) > self._buffer_size:
            buffer.pop(0)
        
        # 큐에 추가
        queue = self.get_or_create_queue(session_id)
        await queue.put(event)
        
        return event
    
    def get_missed_events(self, session_id: str, last_event_id: int) -> List[SSEEvent]:
        """
        Last-Event-ID 이후 미수신 이벤트 반환
        
        Args:
            session_id: 세션 ID
            last_event_id: 마지막으로 수신한 이벤트 ID
            
        Returns:
            미수신 이벤트 목록
        """
        buffer = self._event_buffers.get(session_id, [])
        return [e for e in buffer if e.id > last_event_id]
    
    async def stream_events(
        self, 
        session_id: str, 
        last_event_id: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        SSE 이벤트 스트림 생성기
        
        Args:
            session_id: 세션 ID
            last_event_id: 마지막 수신 이벤트 ID (재연결 시)
            
        Yields:
            SSE 포맷 문자열
        """
        # 재연결 시 미수신 이벤트 재전송
        if last_event_id:
            missed = self.get_missed_events(session_id, last_event_id)
            for event in missed:
                yield event.to_sse_format()
        
        # 새 이벤트 스트리밍
        queue = self.get_or_create_queue(session_id)
        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=30)
                yield event.to_sse_format()
                
                # SESSION_END 이벤트 시 종료
                if event.type == EventType.SESSION_END:
                    break
            except asyncio.TimeoutError:
                # 타임아웃 시 keepalive 전송
                yield ": keepalive\n\n"
    
    def cleanup_session(self, session_id: str):
        """세션 정리"""
        if session_id in self._event_buffers:
            del self._event_buffers[session_id]
        if session_id in self._event_queues:
            del self._event_queues[session_id]


# 싱글톤 인스턴스
sse_event_manager = SSEEventManager()
