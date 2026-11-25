"""개별 퀴즈를 표현하는 Quiz 클래스 정의 모듈."""

from __future__ import annotations
from typing import Any


class Quiz:
    """개별 4지선다 퀴즈 문제를 표현하는 클래스.

    Attributes:
        question (str): 퀴즈 문제 문자열
        choices (list[str]): 4개의 선택지 문자열 리스트
        answer (int): 정답 번호 (1 ~ 4)
        hint (str): 문제 풀이 시 참고할 수 있는 힌트 (보너스 과제)
        category (str): 문제 분류 카테고리/태그 (기본값: "Python 기초")
    """

    EXPECTED_CHOICE_COUNT = 4

    def __init__(
        self,
        question: str,
        choices: list[str],
        answer: int,
        hint: str = "",
        category: str = "Python 기초",
    ) -> None:
        if not isinstance(question, str) or not question.strip():
            raise ValueError("문제(question)는 비어 있지 않은 문자열이어야 합니다.")

        if not isinstance(choices, list) or len(choices) != self.EXPECTED_CHOICE_COUNT:
            raise ValueError(
                f"선택지(choices)는 정확히 {self.EXPECTED_CHOICE_COUNT}개의 항목을 가진 리스트여야 합니다."
            )

        cleaned_choices: list[str] = []
        for idx, choice in enumerate(choices, start=1):
            if not isinstance(choice, str) or not choice.strip():
                raise ValueError(f"선택지 {idx}번이 비어 있거나 문자열이 아닙니다.")
            cleaned_choices.append(choice.strip())

        if isinstance(answer, bool) or not isinstance(answer, int):
            raise ValueError("정답(answer)은 1~4 사이의 정수여야 합니다.")
        if not (1 <= answer <= self.EXPECTED_CHOICE_COUNT):
            raise ValueError(
                f"정답(answer)은 1부터 {self.EXPECTED_CHOICE_COUNT} 사이의 번호여야 합니다."
            )

        self.question: str = question.strip()
        self.choices: list[str] = cleaned_choices
        self.answer: int = answer
        self.hint: str = hint.strip() if isinstance(hint, str) else ""
        cleaned_cat = category.strip() if isinstance(category, str) else ""
        self.category: str = cleaned_cat if cleaned_cat else "Python 기초"

    def format_quiz(self, number: int | None = None, total: int | None = None) -> str:
        """문제와 4개의 선택지를 콘솔 출력용 문자열로 포맷팅하여 반환합니다."""
        lines: list[str] = ["----------------------------------------"]
        tag_label = f" [{self.category}]" if self.category else ""
        if number is not None and total is not None:
            lines.append(f"[문제 {number}/{total}]{tag_label}")
        elif number is not None:
            lines.append(f"[문제 {number}]{tag_label}")
        elif tag_label:
            lines.append(tag_label.strip())

        lines.append(self.question)
        lines.append("")
        for idx, choice in enumerate(self.choices, start=1):
            lines.append(f"{idx}. {choice}")
        return "\n".join(lines)

    def display(self, number: int | None = None, total: int | None = None) -> None:
        """콘솔 화면에 문제와 선택지를 출력합니다."""
        print(self.format_quiz(number=number, total=total))

    def check_answer(self, user_answer: int) -> bool:
        """사용자가 입력한 번호(1~4)가 정답과 일치하는지 확인합니다."""
        return user_answer == self.answer

    def get_hint(self) -> str:
        """퀴즈의 힌트 문자열을 반환합니다."""
        if self.hint:
            return self.hint
        return f"정답 선택지는 '{self.choices[self.answer - 1][0]}'(으)로 시작합니다."

    def get_correct_choice_text(self) -> str:
        """정답 번호에 해당하는 선택지 텍스트를 반환합니다."""
        return self.choices[self.answer - 1]

    def to_dict(self) -> dict[str, Any]:
        """JSON 직렬화를 위해 Quiz 객체를 딕셔너리로 변환합니다."""
        data: dict[str, Any] = {
            "question": self.question,
            "choices": list(self.choices),
            "answer": self.answer,
            "category": self.category,
        }
        if self.hint:
            data["hint"] = self.hint
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Quiz":
        """딕셔너리 데이터로부터 Quiz 인스턴스를 생성합니다.

        데이터 형식이 올바르지 않으면 ValueError 또는 TypeError를 발생시킵니다.
        """
        if not isinstance(data, dict):
            raise ValueError("퀴즈 항목 데이터가 딕셔너리 형식이 아닙니다.")

        question = data.get("question")
        choices = data.get("choices")
        answer = data.get("answer")
        hint = data.get("hint", "")
        category = data.get("category", "Python 기초")

        return cls(
            question=question,
            choices=choices,
            answer=answer,
            hint=hint if isinstance(hint, str) else "",
            category=category if isinstance(category, str) else "Python 기초",
        )

    def __repr__(self) -> str:
        return (
            f"Quiz(question={self.question!r}, choices={self.choices!r}, "
            f"answer={self.answer!r}, hint={self.hint!r}, category={self.category!r})"
        )
