"""
조기 종료 감지 - 명령어/키워드 분리

핵심 보완사항 반영:
- 명령어 (/stop, /final): 확실한 종료
- 키워드 (마무리, 끝내자): 확인 필요
- 오탐 방지를 위한 2단계 감지
"""
import re
from enum import Enum
from typing import Tuple, List, Optional


class StopConfidence(str, Enum):
    """종료 의도 확실성"""
    NONE = "none"           # 종료 의도 없음
    COMMAND = "command"     # 명령어로 확실한 종료 (/stop, /final)
    KEYWORD = "keyword"     # 키워드 감지 (확인 필요)


# 명령어 프리픽스 (확실한 종료)
COMMAND_TRIGGERS = [
    r"^/stop\b",
    r"^/final\b",
    r"^/마무리\b",
    r"^/종료\b",
]

# 키워드 트리거 (확인 필요)
KEYWORD_TRIGGERS = [
    r"마무리\s*하자",
    r"마무리\s*할게",
    r"결론\s*내자",
    r"여기서\s*끝",
    r"그만\s*하자",
    r"끝내자",
    r"종료\s*하자",
]


class StopDetector:
    """
    조기 종료 감지기
    
    2단계 감지:
    1. 명령어 (확실한 종료): /stop, /final 등
    2. 키워드 (확인 필요): 마무리, 끝내자 등
    """
    
    def __init__(
        self, 
        custom_commands: Optional[List[str]] = None,
        custom_keywords: Optional[List[str]] = None
    ):
        self.command_patterns = [
            re.compile(t, re.IGNORECASE) for t in COMMAND_TRIGGERS
        ]
        self.keyword_patterns = [
            re.compile(t, re.IGNORECASE) for t in KEYWORD_TRIGGERS
        ]
        
        if custom_commands:
            self.command_patterns.extend([
                re.compile(t, re.IGNORECASE) for t in custom_commands
            ])
        if custom_keywords:
            self.keyword_patterns.extend([
                re.compile(t, re.IGNORECASE) for t in custom_keywords
            ])
    
    def detect(self, user_input: str) -> Tuple[StopConfidence, Optional[str]]:
        """
        종료 의도 감지
        
        Args:
            user_input: 사용자 입력 텍스트
            
        Returns:
            (StopConfidence, matched_trigger)
            - COMMAND: 즉시 종료 실행
            - KEYWORD: UI에서 확인 모달 표시 필요
            - NONE: 정상 메시지
        """
        user_input = user_input.strip()
        
        # 1. 명령어 확인 (확실한 종료)
        for pattern in self.command_patterns:
            if pattern.search(user_input):
                return StopConfidence.COMMAND, pattern.pattern
        
        # 2. 키워드 확인 (확인 필요)
        for pattern in self.keyword_patterns:
            if pattern.search(user_input):
                return StopConfidence.KEYWORD, pattern.pattern
        
        return StopConfidence.NONE, None


# 싱글톤 인스턴스
stop_detector = StopDetector()
