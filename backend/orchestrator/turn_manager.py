from typing import Dict, Optional, List
from enum import Enum

class AgentRole(str, Enum):
    AGENT1 = "agent1"
    AGENT2 = "agent2"
    AGENT3 = "agent3"
    VERIFIER = "verifier"

class TurnType(str, Enum):
    PLAN = "plan"
    CRITIQUE = "critique"
    COMPROMISE = "compromise"
    DEFENSE = "defense"
    REBUTTAL = "rebuttal"
    FINAL_REPORT = "final_report"
    VERIFICATION = "verification"

class TurnSpec:
    def __init__(self, role: AgentRole, turn_type: TurnType, description: str, max_chars: int):
        self.role = role
        self.turn_type = turn_type
        self.description = description
        self.max_chars = max_chars

class TurnManager:
    def __init__(self):
        from config import MAX_ROUNDS
        
        self.turns: List[TurnSpec] = []
        
        # Round 1: 초기 제안
        self.turns.extend([
            TurnSpec(AgentRole.AGENT1, TurnType.PLAN, "초기 구현 계획 제시", 500),
            TurnSpec(AgentRole.AGENT2, TurnType.CRITIQUE, "핵심 비판 및 리스크 지적", 300),
            TurnSpec(AgentRole.AGENT3, TurnType.COMPROMISE, "1차 절충안 제시", 300),
            TurnSpec(AgentRole.VERIFIER, TurnType.VERIFICATION, "1차 라운드 검증 및 정리", 300),
        ])

        # Round 2 ~ N-1: 심화 토론
        for i in range(2, MAX_ROUNDS):
            self.turns.extend([
                TurnSpec(AgentRole.AGENT2, TurnType.REBUTTAL, f"절충안에 대한 추가 반박 (Round {i})", 300),
                TurnSpec(AgentRole.AGENT1, TurnType.DEFENSE, f"비판에 대한 방어 및 보완책 (Round {i})", 300),
                TurnSpec(AgentRole.AGENT3, TurnType.COMPROMISE, f"{i}차 절충안 및 방향성 정리", 300),
                TurnSpec(AgentRole.VERIFIER, TurnType.VERIFICATION, f"{i}차 라운드 검증 및 정리", 300),
            ])

        # Round N (Final): 최종 정리
        self.turns.extend([
            TurnSpec(AgentRole.AGENT2, TurnType.REBUTTAL, "마지막 점검 및 우려사항", 300),
            TurnSpec(AgentRole.AGENT1, TurnType.DEFENSE, "최종 실행 의지 및 해결책", 300),
            TurnSpec(AgentRole.AGENT3, TurnType.FINAL_REPORT, "최종 합의안 및 리포트 작성", 1500),
            TurnSpec(AgentRole.VERIFIER, TurnType.VERIFICATION, "최종 결과 검증 및 승인", 500),
        ])

    def get_turn(self, turn_index: int) -> Optional[TurnSpec]:
        """
        특정 인덱스의 턴 정보를 반환합니다. (0-based index)
        범위를 벗어나면 None을 반환합니다.
        """
        if 0 <= turn_index < len(self.turns):
            return self.turns[turn_index]
        return None

    def get_total_turns(self) -> int:
        return len(self.turns)

    def get_round_index(self, turn_index: int) -> int:
        """
        턴 인덱스를 기반으로 현재 라운드(1, 2, 3)를 반환합니다.
        각 라운드는 4개의 턴으로 구성됩니다 (Agent1, Agent2, Agent3, Verifier).
        """
        return (turn_index // 4) + 1

turn_manager = TurnManager()

