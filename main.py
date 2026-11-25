"""나만의 파이썬 콘솔 퀴즈 게임 실행 진입점(Entrypoint) 모듈."""

from __future__ import annotations
from quiz_game import QuizGame


def main() -> None:
    """QuizGame 인스턴스를 생성하고 콘솔 게임을 시작합니다."""
    game = QuizGame()
    game.run()


if __name__ == "__main__":
    main()
