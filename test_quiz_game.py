"""나만의 파이썬 콘솔 퀴즈 게임 전체 기능 및 예외 처리 검증 테스트 스위트."""

from __future__ import annotations
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from default_data import get_default_quizzes
from input_utils import prompt_answer_or_hint, prompt_int, prompt_non_empty_str
from quiz import Quiz
from quiz_game import QuizGame
from storage import StateManager


class TestQuizModel(unittest.TestCase):
    """Quiz 클래스 속성, 메서드 및 직렬화 검증."""

    def test_quiz_creation_and_methods(self) -> None:
        quiz = Quiz(
            question="  Python의 창시자는?  ",
            choices=[" Guido ", "Linus", "Bjarne", "James"],
            answer=1,
            hint="  네덜란드 개발자  ",
        )
        self.assertEqual(quiz.question, "Python의 창시자는?")
        self.assertEqual(quiz.choices[0], "Guido")
        self.assertEqual(quiz.answer, 1)
        self.assertEqual(quiz.hint, "네덜란드 개발자")
        self.assertTrue(quiz.check_answer(1))
        self.assertFalse(quiz.check_answer(2))
        self.assertIn("[문제 1/5]", quiz.format_quiz(number=1, total=5))

        serialized = quiz.to_dict()
        restored = Quiz.from_dict(serialized)
        self.assertEqual(restored.question, quiz.question)
        self.assertEqual(restored.choices, quiz.choices)
        self.assertEqual(restored.answer, quiz.answer)
        self.assertEqual(restored.hint, quiz.hint)

    def test_quiz_validation_errors(self) -> None:
        with self.assertRaises(ValueError):
            Quiz(question="", choices=["1", "2", "3", "4"], answer=1)
        with self.assertRaises(ValueError):
            Quiz(question="Q", choices=["1", "2", "3"], answer=1)
        with self.assertRaises(ValueError):
            Quiz(question="Q", choices=["1", "2", "3", "4"], answer=0)
        with self.assertRaises(ValueError):
            Quiz(question="Q", choices=["1", "2", "3", "4"], answer=5)

    def test_default_quizzes_count(self) -> None:
        quizzes = get_default_quizzes()
        self.assertGreaterEqual(len(quizzes), 5)
        for q in quizzes:
            self.assertIsInstance(q, Quiz)
            self.assertEqual(len(q.choices), 4)
            self.assertIn(q.answer, (1, 2, 3, 4))


class TestInputValidation(unittest.TestCase):
    """공통 입력/예외 처리 기준(공백 제거, 빈 입력, 문자 입력, 범위 밖 숫자) 검증."""

    def test_prompt_int_handles_whitespace_empty_alpha_and_out_of_range(self) -> None:
        inputs = ["", "   ", "abc", "0", "9", "  3  "]
        with patch("builtins.input", side_effect=inputs), patch(
            "sys.stdout", new_callable=io.StringIO
        ) as fake_out:
            result = prompt_int("선택: ", min_value=1, max_value=6)
            output = fake_out.getvalue()

        self.assertEqual(result, 3)
        self.assertIn("입력이 비어 있습니다", output)
        self.assertIn("잘못된 입력입니다", output)

    def test_prompt_answer_or_hint(self) -> None:
        inputs = ["", "xyz", "0", "5", " h ", " 2 "]
        with patch("builtins.input", side_effect=inputs), patch(
            "sys.stdout", new_callable=io.StringIO
        ):
            first = prompt_answer_or_hint("정답: ")
            second = prompt_answer_or_hint("정답: ")

        self.assertEqual(first, "HINT")
        self.assertEqual(second, 2)

    def test_prompt_non_empty_str(self) -> None:
        with patch("builtins.input", side_effect=["", "   ", "  파이썬 문제  "]), patch(
            "sys.stdout", new_callable=io.StringIO
        ):
            val = prompt_non_empty_str("문제: ", field_name="문제")
        self.assertEqual(val, "파이썬 문제")


class TestStorageAndQuizGame(unittest.TestCase):
    """state.json 저장/불러오기, 손상 파일 복구, 게임 핵심 및 보너스 기능 통합 검증."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_path = Path(self.temp_dir.name) / "state.json"

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_missing_and_corrupted_state_recovery(self) -> None:
        # 1. 파일이 없을 때 기본 퀴즈로 초기화
        game = QuizGame(state_path=self.state_path, shuffle_questions=False)
        self.assertTrue(self.state_path.exists())
        self.assertGreaterEqual(len(game.quizzes), 5)
        self.assertIsNone(game.best_score)

        # 2. 파일이 손상되었을 때 경고 출력 후 기본 데이터로 복구
        self.state_path.write_text("{corrupted_json...", encoding="utf-8")
        with patch("sys.stdout", new_callable=io.StringIO) as fake_out:
            recovered_game = QuizGame(state_path=self.state_path, shuffle_questions=False)
            out = fake_out.getvalue()
        self.assertIn("손상", out)
        self.assertGreaterEqual(len(recovered_game.quizzes), 5)

        # 3. 최소 스키마(quizzes, best_score) 호환성 확인
        minimal_payload = {
            "quizzes": [
                {
                    "question": "Python의 창시자는?",
                    "choices": ["Guido", "Linus", "Bjarne", "James"],
                    "answer": 1,
                }
            ],
            "best_score": 80,
        }
        self.state_path.write_text(
            json.dumps(minimal_payload, ensure_ascii=False),
            encoding="utf-8",
        )
        minimal_game = QuizGame(state_path=self.state_path, shuffle_questions=False)
        self.assertEqual(len(minimal_game.quizzes), 1)
        self.assertEqual(minimal_game.best_score, 80)

    def test_play_add_list_delete_score_and_persistence(self) -> None:
        game = QuizGame(state_path=self.state_path, shuffle_questions=False)
        initial_count = len(game.quizzes)

        # 1. 아직 퀴즈를 풀지 않은 상태에서 점수 확인
        with patch("sys.stdout", new_callable=io.StringIO) as out1:
            game.show_scores()
        self.assertIn("아직", out1.getvalue())

        # 2. 퀴즈 풀기 (2문제 선택: 1번 문제는 힌트 사용 후 정답, 2번 문제는 바로 정답)
        q1_ans = str(game.quizzes[0].answer)
        q2_ans = str(game.quizzes[1].answer)
        with patch("builtins.input", side_effect=["2", "h", q1_ans, q2_ans]), patch(
            "sys.stdout", new_callable=io.StringIO
        ) as play_out:
            game.play_quiz()
        self.assertIn("새로운 최고 점수", play_out.getvalue())
        self.assertEqual(game.best_score, 75)  # (0.5 + 1.0) / 2 * 100 = 75점
        self.assertEqual(len(game.history), 1)

        # 3. 퀴즈 추가
        add_inputs = [
            "영화 '기생충'의 감독은?",
            "박찬욱",
            "봉준호",
            "김기덕",
            "이창동",
            "2",
            "칸 영화제 황금종려상 수상 감독",
        ]
        with patch("builtins.input", side_effect=add_inputs), patch(
            "sys.stdout", new_callable=io.StringIO
        ):
            game.add_quiz()
        self.assertEqual(len(game.quizzes), initial_count + 1)

        # 4. 재시작 후 데이터(추가한 퀴즈 + 최고 점수 + 히스토리) 영속성 확인
        reloaded = QuizGame(state_path=self.state_path, shuffle_questions=False)
        self.assertEqual(len(reloaded.quizzes), initial_count + 1)
        self.assertEqual(reloaded.best_score, 75)
        self.assertEqual(len(reloaded.history), 1)

        # 5. 퀴즈 삭제
        with patch("builtins.input", side_effect=[str(initial_count + 1)]), patch(
            "sys.stdout", new_callable=io.StringIO
        ):
            reloaded.delete_quiz()
        self.assertEqual(len(reloaded.quizzes), initial_count)

    def test_graceful_exit_on_keyboard_interrupt_and_eof(self) -> None:
        game = QuizGame(state_path=self.state_path, shuffle_questions=False)
        with patch("builtins.input", side_effect=KeyboardInterrupt), patch(
            "sys.stdout", new_callable=io.StringIO
        ) as out_kb:
            game.run()
        self.assertIn("안전하게 저장하고 종료", out_kb.getvalue())

        with patch("builtins.input", side_effect=EOFError), patch(
            "sys.stdout", new_callable=io.StringIO
        ) as out_eof:
            game.run()
        self.assertIn("안전하게 저장하고 종료", out_eof.getvalue())


if __name__ == "__main__":
    unittest.main()
