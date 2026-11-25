"""퀴즈 게임 전체 흐름을 관리하는 QuizGame 클래스 모듈."""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
import random
from typing import Any

from input_utils import (
    prompt_answer_or_hint,
    prompt_int,
    prompt_non_empty_str,
    prompt_optional_str,
)
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
        """저장된 퀴즈를 출제하고 정답 판정, 힌트 차감, 점수 계산 및 최고 점수/히스토리 저장을 수행합니다."""
        if not self.quizzes:
            print("⚠️ 등록된 퀴즈가 없습니다. 먼저 '2. 퀴즈 추가'에서 퀴즈를 등록해 주세요.")
            return

        total_available = len(self.quizzes)
        print(f"📝 퀴즈를 시작합니다! (현재 등록된 퀴즈: 총 {total_available}문제)")
        selected_count = prompt_int(
            f"출제할 문제 수를 입력하세요 (1-{total_available}): ",
            min_value=1,
            max_value=total_available,
        )

        if self.shuffle_questions:
            selected_quizzes = random.sample(self.quizzes, selected_count)
            print(f"\n🎲 총 {selected_count}문제를 랜덤 순서로 출제합니다! (힌트 보기: 'h' 입력 시 해당 문제 배점 50% 차감)")
        else:
            selected_quizzes = list(self.quizzes[:selected_count])
            print(f"\n📝 총 {selected_count}문제를 출제합니다! (힌트 보기: 'h' 입력 시 해당 문제 배점 50% 차감)")

        correct_count = 0
        hints_used = 0
        earned_units = 0.0

        for idx, quiz in enumerate(selected_quizzes, start=1):
            print()
            quiz.display(number=idx, total=selected_count)
            print()

            used_hint_for_question = False
            while True:
                user_choice = prompt_answer_or_hint(
                    "정답 입력 (1-4, 힌트: h): ",
                    min_value=1,
                    max_value=Quiz.EXPECTED_CHOICE_COUNT,
                    allow_hint=True,
                )
                if user_choice == "HINT":
                    print(f"💡 [힌트] {quiz.get_hint()}")
                    if not used_hint_for_question:
                        used_hint_for_question = True
                        hints_used += 1
                        print("   (ℹ️ 힌트를 사용하여 이 문제 정답 시 배점의 50%가 차감됩니다.)")
                    continue
                answer_num = int(user_choice)
                break

            if quiz.check_answer(answer_num):
                correct_count += 1
                if used_hint_for_question:
                    earned_units += 0.5
                    print("✅ 정답입니다! (힌트 사용으로 50% 배점 인정)")
                else:
                    earned_units += 1.0
                    print("✅ 정답입니다!")
            else:
                print(
                    f"❌ 오답입니다! (정답: {quiz.answer}번 - {quiz.get_correct_choice_text()})"
                )

        score = int(round((earned_units / selected_count) * 100))

        print("\n========================================")
        print(f"🏆 결과: {selected_count}문제 중 {correct_count}문제 정답! ({score}점)")
        if hints_used > 0:
            print(f"💡 힌트 사용: {hints_used}회 (점수 차감 반영)")

        if self.best_score is None or score > self.best_score:
            self.best_score = score
            self.best_correct = correct_count
            self.best_total = selected_count
            print("🎉 새로운 최고 점수입니다!")
        else:
            print(f"📊 현재 최고 점수: {self.best_score}점")
        print("========================================")

        self.history.append(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_questions": selected_count,
                "correct_count": correct_count,
                "hints_used": hints_used,
                "score": score,
            }
        )
        self.save_state()

    def add_quiz(self) -> None:
        """사용자로부터 문제, 선택지 4개, 정답 번호, 힌트를 입력받아 새 퀴즈를 등록하고 파일에 저장합니다."""
        print("📌 새로운 퀴즈를 추가합니다.\n")
        question = prompt_non_empty_str("문제를 입력하세요: ", field_name="문제")

        choices: list[str] = []
        for idx in range(1, Quiz.EXPECTED_CHOICE_COUNT + 1):
            choice_text = prompt_non_empty_str(
                f"선택지 {idx}: ",
                field_name=f"선택지 {idx}",
            )
            choices.append(choice_text)

        answer = prompt_int(
            f"정답 번호 (1-{Quiz.EXPECTED_CHOICE_COUNT}): ",
            min_value=1,
            max_value=Quiz.EXPECTED_CHOICE_COUNT,
        )
        hint = prompt_optional_str(
            "힌트를 입력하세요 (선택 사항, 없으면 Enter): ",
            default="",
        )

        new_quiz = Quiz(
            question=question,
            choices=choices,
            answer=answer,
            hint=hint,
        )
        self.quizzes.append(new_quiz)
        self.save_state()
        print(f"\n✅ 퀴즈가 추가되었습니다! (현재 총 {len(self.quizzes)}개)")

    def list_quizzes(self) -> None:
        """등록된 모든 퀴즈 목록을 출력합니다. 퀴즈가 없는 경우 안내 메시지를 출력합니다."""
        if not self.quizzes:
            print("📋 등록된 퀴즈가 없습니다.")
            return

        print(f"📋 등록된 퀴즈 목록 (총 {len(self.quizzes)}개)\n")
        print("----------------------------------------")
        for idx, quiz in enumerate(self.quizzes, start=1):
            hint_badge = " [💡힌트 있음]" if quiz.hint else ""
            print(f"[{idx}] {quiz.question}{hint_badge}")
        print("----------------------------------------")

    def show_scores(self) -> None:
        """최고 점수와 전체 게임 플레이 히스토리를 출력합니다. 아직 퀴즈를 풀지 않은 경우를 처리합니다."""
        if self.best_score is None and not self.history:
            print("📊 아직 플레이한 기록이 없습니다. 먼저 퀴즈를 풀어 보세요!")
            return

        if self.best_total > 0:
            print(
                f"🏆 최고 점수: {self.best_score}점 "
                f"({self.best_total}문제 중 {self.best_correct}문제 정답)"
            )
        else:
            print(f"🏆 최고 점수: {self.best_score}점")

        print()
        if not self.history:
            print("📜 상세 플레이 히스토리가 없습니다.")
            return

        print(f"📜 게임 플레이 히스토리 (총 {len(self.history)}회)")
        print("------------------------------------------------------------")
        for idx, record in enumerate(self.history, start=1):
            ts = record.get("timestamp", "-")
            total_q = record.get("total_questions", 0)
            correct_q = record.get("correct_count", 0)
            hints = record.get("hints_used", 0)
            rec_score = record.get("score", 0)
            print(
                f"[{idx}] {ts} | {total_q}문제 중 {correct_q}문제 정답 | "
                f"힌트 {hints}회 | {rec_score}점"
            )
        print("------------------------------------------------------------")

    def delete_quiz(self) -> None:
        """등록된 퀴즈 중 선택한 번호의 퀴즈를 삭제하고 파일(state.json)에 반영합니다."""
        if not self.quizzes:
            print("⚠️ 삭제할 퀴즈가 없습니다. 현재 등록된 퀴즈가 0개입니다.")
            return

        print("🗑️ 삭제할 퀴즈를 선택해 주세요.\n")
        self.list_quizzes()
        print()
        target_num = prompt_int(
            f"삭제할 퀴즈 번호 (1-{len(self.quizzes)}): ",
            min_value=1,
            max_value=len(self.quizzes),
        )
        removed_quiz = self.quizzes.pop(target_num - 1)
        self.save_state()
        print(
            f"\n✅ [{target_num}] '{removed_quiz.question}' 퀴즈가 삭제되었습니다! "
            f"(남은 퀴즈: {len(self.quizzes)}개)"
        )
