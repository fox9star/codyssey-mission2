"""퀴즈 게임 전체 흐름을 관리하는 QuizGame 클래스 모듈."""

from __future__ import annotations
from pathlib import Path
from typing import Any

from input_utils import prompt_int
from quiz import Quiz
from storage import DEFAULT_STATE_PATH, StateManager


class QuizGame:
    """콘솔 퀴즈 게임의 상태(퀴즈 목록, 최고 점수, 히스토리)와 메뉴 흐름을 관리하는 클래스."""

    MENU_MIN = 1
    MENU_MAX = 6

    def __init__(
        self,
        state_path: str | Path = DEFAULT_STATE_PATH,
        shuffle_questions: bool = True,
    ) -> None:
        self.state_manager = StateManager(state_path)
        self.shuffle_questions = shuffle_questions
        self.quizzes: list[Quiz] = []
        self.best_score: int | None = None
        self.best_correct: int = 0
        self.best_total: int = 0
        self.history: list[dict[str, Any]] = []
        self.startup_message: str = ""
        self.load_state()

    def load_state(self) -> None:
        """state.json에서 게임 데이터를 불러옵니다."""
        state = self.state_manager.load()
        self.quizzes = state["quizzes"]
        self.best_score = state["best_score"]
        self.best_correct = state["best_correct"]
        self.best_total = state["best_total"]
        self.history = state["history"]
        self.startup_message = state["message"]

    def save_state(self) -> bool:
        """현재 게임 데이터를 state.json에 저장합니다."""
        return self.state_manager.save(
            quizzes=self.quizzes,
            best_score=self.best_score,
            best_correct=self.best_correct,
            best_total=self.best_total,
            history=self.history,
        )

    def display_header(self) -> None:
        """프로그램 시작 시 상단 배너와 데이터 로드 상태를 출력합니다."""
        print("========================================")
        print("        🎯 나만의 퀴즈 게임 🎯")
        print("========================================")
        if self.startup_message:
            print(self.startup_message)

    def display_menu(self) -> None:
        """메인 메뉴 화면을 출력합니다."""
        print("========================================")
        print("1. 퀴즈 풀기")
        print("2. 퀴즈 추가")
        print("3. 퀴즈 목록")
        print("4. 점수 확인")
        print("5. 퀴즈 삭제")
        print("6. 종료")
        print("========================================")

    def run(self) -> None:
        """메인 메뉴 루프를 실행하고 사용자 입력에 따라 기능을 호출합니다."""
        self.display_header()
        try:
            while True:
                self.display_menu()
                choice = prompt_int(
                    "선택: ",
                    min_value=self.MENU_MIN,
                    max_value=self.MENU_MAX,
                )
                print()

                if choice == 1:
                    self.play_quiz()
                elif choice == 2:
                    self.add_quiz()
                elif choice == 3:
                    self.list_quizzes()
                elif choice == 4:
                    self.show_scores()
                elif choice == 5:
                    self.delete_quiz()
                elif choice == 6:
                    self.save_state()
                    print("👋 퀴즈 게임을 종료합니다. 이용해 주셔서 감사합니다!")
                    break
                print()
        except (KeyboardInterrupt, EOFError):
            print("\n\n⚠️ 입력이 중단되었습니다(Ctrl+C / EOF). 현재 데이터를 안전하게 저장하고 종료합니다.")
            self.save_state()

    def play_quiz(self) -> None:
        """퀴즈 풀기 기능 (feature/quiz-play 브랜치에서 구현)."""
        raise NotImplementedError("퀴즈 풀기 기능은 아직 구현되지 않았습니다.")

    def add_quiz(self) -> None:
        """퀴즈 추가 기능."""
        raise NotImplementedError("퀴즈 추가 기능은 아직 구현되지 않았습니다.")

    def list_quizzes(self) -> None:
        """퀴즈 목록 조회 기능."""
        raise NotImplementedError("퀴즈 목록 기능은 아직 구현되지 않았습니다.")

    def show_scores(self) -> None:
        """점수 및 히스토리 확인 기능."""
        raise NotImplementedError("점수 확인 기능은 아직 구현되지 않았습니다.")

    def delete_quiz(self) -> None:
        """퀴즈 삭제 기능."""
        raise NotImplementedError("퀴즈 삭제 기능은 아직 구현되지 않았습니다.")
