"""state.json 데이터 영속성(저장/불러오기 및 손상 복구) 관리 모듈."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from default_data import get_default_quizzes
from quiz import Quiz


DEFAULT_STATE_PATH = Path(__file__).resolve().parent / "state.json"


class StateManager:
    """프로젝트 루트의 state.json 파일 입출력과 데이터 검증·복구를 담당하는 클래스.

    Attributes:
        file_path (Path): 저장할 JSON 파일 경로 (기본값: 프로젝트 루트의 state.json)
    """

    def __init__(self, file_path: str | Path = DEFAULT_STATE_PATH) -> None:
        self.file_path: Path = Path(file_path)

    def load(self) -> dict[str, Any]:
        """state.json 파일에서 퀴즈 목록, 최고 점수, 히스토리를 불러옵니다.

        - 파일이 없는 경우: 기본 퀴즈 데이터를 사용하여 초기 상태를 반환하고 파일에 저장합니다.
        - 파일이 손상되었거나 스키마가 유효하지 않은 경우: 안내 메시지를 출력하고 기본 퀴즈 데이터로 복구합니다.
        """
        if not self.file_path.exists():
            default_state = self._build_default_state()
            self.save(
                quizzes=default_state["quizzes"],
                best_score=default_state["best_score"],
                best_correct=default_state["best_correct"],
                best_total=default_state["best_total"],
                history=default_state["history"],
            )
            return {
                **default_state,
                "status": "initialized",
                "message": (
                    f"📂 저장된 데이터 파일({self.file_path.name})이 없어 "
                    f"기본 퀴즈 데이터를 불러왔습니다. (퀴즈 {len(default_state['quizzes'])}개)"
                ),
            }

        try:
            raw_text = self.file_path.read_text(encoding="utf-8")
            data = json.loads(raw_text)
            parsed = self._validate_and_parse(data)
            return {
                **parsed,
                "status": "loaded",
                "message": (
                    f"📂 저장된 데이터를 불러왔습니다. "
                    f"(퀴즈 {len(parsed['quizzes'])}개, "
                    f"최고점수 {'기록 없음' if parsed['best_score'] is None else str(parsed['best_score']) + '점'})"
                ),
            }
        except (OSError, json.JSONDecodeError, ValueError, TypeError) as exc:
            print(
                f"⚠️ 데이터 파일({self.file_path.name})이 손상되었거나 읽을 수 없어 "
                f"기본 퀴즈 데이터로 복구합니다. (원인: {exc})"
            )
            default_state = self._build_default_state()
            self.save(
                quizzes=default_state["quizzes"],
                best_score=default_state["best_score"],
                best_correct=default_state["best_correct"],
                best_total=default_state["best_total"],
                history=default_state["history"],
            )
            return {
                **default_state,
                "status": "recovered",
                "message": (
                    f"🛠️ 기본 퀴즈 데이터로 초기화되었습니다. "
                    f"(퀴즈 {len(default_state['quizzes'])}개)"
                ),
            }

    def save(
        self,
        quizzes: list[Quiz],
        best_score: int | None,
        best_correct: int = 0,
        best_total: int = 0,
        history: list[dict[str, Any]] | None = None,
    ) -> bool:
        """현재 퀴즈 목록, 최고 점수, 플레이 히스토리를 UTF-8 인코딩으로 state.json에 저장합니다."""
        payload: dict[str, Any] = {
            "quizzes": [quiz.to_dict() for quiz in quizzes],
            "best_score": best_score if best_score is not None else 0,
            "has_played": best_score is not None or bool(history),
            "best_correct": best_correct,
            "best_total": best_total,
            "history": history if history is not None else [],
        }

        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            serialized = json.dumps(payload, ensure_ascii=False, indent=4)
            self.file_path.write_text(serialized + "\n", encoding="utf-8")
            return True
        except OSError as exc:
            print(f"⚠️ 데이터 파일({self.file_path.name}) 저장 중 오류가 발생했습니다: {exc}")
            return False

    def _build_default_state(self) -> dict[str, Any]:
        """기본 퀴즈 데이터와 초기 점수 상태를 생성합니다."""
        return {
            "quizzes": get_default_quizzes(),
            "best_score": None,
            "best_correct": 0,
            "best_total": 0,
            "history": [],
        }

    def _validate_and_parse(self, data: Any) -> dict[str, Any]:
        """불러온 JSON 딕셔너리의 스키마를 검증하고 내부 객체로 변환합니다."""
        if not isinstance(data, dict):
            raise ValueError("최상위 JSON 구조가 객체(dict)가 아닙니다.")

        if "quizzes" not in data or not isinstance(data["quizzes"], list):
            raise ValueError("'quizzes' 필드가 없거나 리스트 형식이 아닙니다.")

        quizzes: list[Quiz] = [Quiz.from_dict(item) for item in data["quizzes"]]

        raw_best = data.get("best_score", None)
        if raw_best is not None:
            if isinstance(raw_best, bool) or not isinstance(raw_best, (int, float)):
                raise ValueError("'best_score' 필드가 숫자 형식이 아닙니다.")
            if raw_best < 0:
                raise ValueError("'best_score' 필드는 0 이상이어야 합니다.")

        raw_history = data.get("history", [])
        if not isinstance(raw_history, list):
            raise ValueError("'history' 필드가 리스트 형식이 아닙니다.")

        has_played = data.get("has_played", None)
        if has_played is False and not raw_history and raw_best == 0:
            best_score: int | None = None
        elif raw_best is None:
            best_score = None
        else:
            best_score = int(raw_best)

        best_correct = data.get("best_correct", 0)
        best_total = data.get("best_total", len(quizzes))
        if not isinstance(best_correct, int) or not isinstance(best_total, int):
            best_correct = 0
            best_total = len(quizzes)

        return {
            "quizzes": quizzes,
            "best_score": best_score,
            "best_correct": best_correct,
            "best_total": best_total,
            "history": raw_history,
        }
