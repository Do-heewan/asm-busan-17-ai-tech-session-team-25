from pydantic import BaseModel, Field
from typing import Dict, Any

class TurnResult(BaseModel):
    next_scene_trigger: bool = Field(
        ..., 
        description="이번 턴을 끝으로 다음 씬/챕터로 넘어가는지 여부 (True일 경우 프론트는 화면 전환 애니메이션 실행)"
    )
    current_chapter: str = Field(
        ..., 
        description="현재(또는 전환될) 챕터 ID"
    )
    affinity_delta: int = Field(
        default=0, 
        description="이번 턴의 호감도 증감치 (예: +2, -1 등. 프론트엔드 게이지 애니메이션용)"
    )
    agent_dialogue: str = Field(
        ..., 
        description="유저에게 보여질 캐릭터의 최종 대사"
    )
    emotion_code: str = Field(
        ..., 
        description="렌더링할 표정 코드 (예: 'idle', 'smile', 'sad', 'surprise')"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="도구 호출 결과, 씬 전환의 이유 등 형태가 유동적인 추가 정보"
    )