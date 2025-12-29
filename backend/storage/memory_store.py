"""
인메모리 저장소 (MVP용)
"""
from typing import Dict, List, Optional
from datetime import datetime

from models.session import Session
from models.message import Message
from models.case_file import CaseFile
from models.final_report import FinalReport


class MemoryStore:
    """
    인메모리 저장소
    
    MVP용 간단한 저장소 구현
    운영 환경에서는 DB 저장소로 교체
    """
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._messages: Dict[str, List[Message]] = {}  # session_id -> messages
        self._case_files: Dict[str, CaseFile] = {}
        self._final_reports: Dict[str, FinalReport] = {}
    
    # Session 관련
    def save_session(self, session: Session) -> Session:
        self._sessions[session.id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)
    
    def update_session(self, session: Session) -> Session:
        session.updated_at = datetime.utcnow()
        self._sessions[session.id] = session
        return session
    
    # Message 관련
    def save_message(self, message: Message) -> Message:
        if message.session_id not in self._messages:
            self._messages[message.session_id] = []
        self._messages[message.session_id].append(message)
        return message
    
    def get_messages(self, session_id: str) -> List[Message]:
        return self._messages.get(session_id, [])
    
    def get_recent_messages(self, session_id: str, count: int = 10) -> List[Message]:
        messages = self._messages.get(session_id, [])
        return messages[-count:] if len(messages) > count else messages
    
    # CaseFile 관련
    def save_case_file(self, case_file: CaseFile) -> CaseFile:
        self._case_files[case_file.session_id] = case_file
        return case_file
    
    def get_case_file(self, session_id: str) -> Optional[CaseFile]:
        return self._case_files.get(session_id)
    
    def update_case_file(self, case_file: CaseFile) -> CaseFile:
        case_file.updated_at = datetime.utcnow()
        self._case_files[case_file.session_id] = case_file
        return case_file
    
    # FinalReport 관련
    def save_final_report(self, report: FinalReport) -> FinalReport:
        self._final_reports[report.session_id] = report
        return report
    
    def get_final_report(self, session_id: str) -> Optional[FinalReport]:
        return self._final_reports.get(session_id)


# 싱글톤 인스턴스
memory_store = MemoryStore()
