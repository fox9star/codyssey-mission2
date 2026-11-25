"""state.json 데이터 영속성(원자적 저장/불러오기, 스키마 버전 관리 및 손상 파일 .bak 백업 복구) 관리 모듈."""

from __future__ import annotations
import json
from pathlib import Path
import shutil
from typing import Any

from default_data import get_default_quizzes
from quiz import Quiz


DEFAULT_STATE_PATH = Path(__file__).resolve().parent / "state.json"


class StateManager:
    """프로젝트 루트의 state.json 파일 입출력과 데이터 검증·백업·복구를 담당하는 클래스.

    Attributes:
        SCHEMA_VERSION (str): state.json 데이터 스키마 버전 ("1.1")
        file_path (Path): 저장할 JSON 파일 경로 (기본값: 프로젝트 루트의 state.json)
    """

    SCHEMA_VERSION = "1.1"

    def __init__(self, file_path: str | Path = DEFAULT_STATE_PATH) -> None:
        self.file_path: Path = Path(file_path)

    def load(self) -> dict[str, Any]:
        """state.json 파일에서 퀴즈 목록, 최고 점수, 히스토리를 불러옵니다.

        - 파일이 없는 경우: 기본 퀴즈 데이터를 사용하여 초기 상태를 반환하고 파일에 저장합니다.
        - 파일이 손상되었거나 스키마가 유효하지 않은 경우: 손상된 원본 파일을 .bak으로 백업한 뒤
          안내 메시지를 출력하고 기본 퀴즈 데이터로 복구합니다.
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
            backup_path = self._backup_corrupted_file()
            backup_notice = (
                f" 손상된 원본은 '{backup_path.name}'으로 백업했습니다."
                if backup_path is not None
                else ""
            )
            print(
                f"⚠️ 데이터 파일({self.file_path.name})이 손상되었거나 읽을 수 없어 "
                f"기본 퀴즈 데이터로 복구합니다.{backup_notice} (원인: {exc})"
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

    def _backup_corrupted_file(self) -> Path | None:
        """손상된 기존 데이터 파일을 덮어쓰기 전에 .bak 백업 파일로 보존합니다."""
        if not self.file_path.exists():
            return None
        backup_path = self.file_path.with_name(f"{self.file_path.name}.bak")
        try:
            shutil.copy2(self.file_path, backup_path)
            return backup_path
        except OSError:
            return None

    def save(
        self,
        quizzes: list[Quiz],
        best_score: int | None,
        best_correct: int = 0,
        best_total: int = 0,
        history: list[dict[str, Any]] | None = None,
    ) -> bool:
        """현재 퀴즈 목록, 최고 점수, 플레이 히스토리를 UTF-8 인코딩으로 state.json에 원자적(Atomic)으로 저장합니다.

        저장 중 강제 종료(Ctrl+C)나 시스템 중단이 발생해도 기존 파일이 깨지지 않도록
        임시 파일(.tmp)에 먼저 기록한 뒤 원본 파일로 원자적 교체(Path.replace)합니다.
        """
        payload: dict[str, Any] = {
            "schema_version": self.SCHEMA_VERSION,
            "quizzes": [quiz.to_dict() for quiz in quizzes],
            "best_score": best_score if best_score is not None else 0,
            "has_played": best_score is not None or bool(history),
            "best_correct": best_correct,
            "best_total": best_total,
            "history": history if history is not None else [],
        }

        temp_path = self.file_path.with_name(f"{self.file_path.name}.tmp")
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            serialized = json.dumps(payload, ensure_ascii=False, indent=4)
            temp_path.write_text(serialized + "\n", encoding="utf-8")
            temp_path.replace(self.file_path)
            return True
        except OSError as exc:
            print(f"⚠️ 데이터 파일({self.file_path.name}) 저장 중 오류가 발생했습니다: {exc}")
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            return False

    def _build_default_state(self) -> dict[str, Any]:
        """기본 퀴즈 데이터와 초기 점수 상태를 생성합니다."""
        return {
            "schema_version": self.SCHEMA_VERSION,
            "quizzes": get_default_quizzes(),
            "best_score": None,
            "best_correct": 0,
            "best_total": 0,
            "history": [],
        }

    def _validate_and_parse(self, data: Any) -> dict[str, Any]:
        """불러온 JSON 딕셔너리의 스키마와 버전을 검증하고 내부 객체로 변환합니다."""
        if not isinstance(data, dict):
            raise ValueError("최상위 JSON 구조가 객체(dict)가 아닙니다.")

        schema_version = str(data.get("schema_version", "1.0"))

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
            "schema_version": schema_version,
            "quizzes": quizzes,
            "best_score": best_score,
            "best_correct": best_correct,
            "best_total": best_total,
            "history": raw_history,
        }
