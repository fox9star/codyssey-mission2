"""공통 콘솔 입력 및 예외 처리 유틸리티 모듈.

공통 입력/예외 처리 기준:
1. 입력 앞뒤 공백 제거(.strip()) 후 처리
2. 빈 입력(Enter) 시 안내 메시지 출력 후 재입력 흐름으로 복귀
3. 숫자 변환 실패(예: abc) 시 안내 메시지 출력 후 재입력 흐름으로 복귀
4. 허용 범위 밖 숫자(예: 메뉴 9, 정답 0) 입력 시 안내 메시지 출력 후 재입력 흐름으로 복귀
5. Ctrl+C(KeyboardInterrupt) 및 입력 스트림 종료(EOFError)는 상위로 전달하여 안전 저장 후 종료
"""

from __future__ import annotations


def prompt_int(
    prompt: str,
    min_value: int,
    max_value: int,
    allow_default: int | None = None,
) -> int:
    """지정된 범위(min_value ~ max_value) 내의 정수를 안전하게 입력받습니다.

    Args:
        prompt: 사용자에게 출력할 입력 프롬프트 문자열
        min_value: 허용 최소 정수
        max_value: 허용 최대 정수
        allow_default: 빈 입력 시 반환할 기본값 (None이면 빈 입력을 허용하지 않고 재입력 요구)

    Returns:
        검증된 정수 값
    """
    while True:
        raw = input(prompt).strip()

        if raw == "":
            if allow_default is not None:
                return allow_default
            print(
                f"⚠️ 입력이 비어 있습니다. {min_value}-{max_value} 사이의 숫자를 입력하세요."
            )
            continue

        try:
            value = int(raw)
        except ValueError:
            print(
                f"⚠️ 잘못된 입력입니다. {min_value}-{max_value} 사이의 숫자를 입력하세요."
            )
            continue

        if not (min_value <= value <= max_value):
            print(
                f"⚠️ 잘못된 입력입니다. {min_value}-{max_value} 사이의 숫자를 입력하세요."
            )
            continue

        return value


def prompt_answer_or_hint(
    prompt: str,
    min_value: int = 1,
    max_value: int = 4,
    allow_hint: bool = True,
) -> int | str:
    """퀴즈 정답 번호(1~4) 또는 힌트 요청('h'/'hint')을 안전하게 입력받습니다.

    Returns:
        1~4 사이의 정수 또는 힌트 요청 시 문자열 "HINT"
    """
    while True:
        raw = input(prompt).strip()

        if raw == "":
            print(
                f"⚠️ 입력이 비어 있습니다. {min_value}-{max_value} 사이의 숫자를 입력하세요."
            )
            continue

        if allow_hint and raw.lower() in ("h", "hint", "힌트"):
            return "HINT"

        try:
            value = int(raw)
        except ValueError:
            hint_guide = " (힌트 보기: h)" if allow_hint else ""
            print(
                f"⚠️ 잘못된 입력입니다. {min_value}-{max_value} 사이의 숫자를 입력하세요.{hint_guide}"
            )
            continue

        if not (min_value <= value <= max_value):
            hint_guide = " (힌트 보기: h)" if allow_hint else ""
            print(
                f"⚠️ 잘못된 입력입니다. {min_value}-{max_value} 사이의 숫자를 입력하세요.{hint_guide}"
            )
            continue

        return value


def prompt_non_empty_str(prompt: str, field_name: str = "값") -> str:
    """비어 있지 않은 문자열을 입력받아 앞뒤 공백을 제거한 뒤 반환합니다."""
    while True:
        raw = input(prompt).strip()
        if raw == "":
            print(f"⚠️ {field_name}은(는) 비워 둘 수 없습니다. 다시 입력해 주세요.")
            continue
        return raw


def prompt_optional_str(prompt: str, default: str = "") -> str:
    """선택적 문자열을 입력받습니다. 빈 입력 시 default를 반환합니다."""
    raw = input(prompt).strip()
    return raw if raw else default


def prompt_yes_no(prompt: str, default_yes: bool = True) -> bool:
    """y/n 여부를 안전하게 입력받습니다."""
    while True:
        raw = input(prompt).strip().lower()
        if raw == "":
            return default_yes
        if raw in ("y", "yes", "1", "네", "예"):
            return True
        if raw in ("n", "no", "2", "아니오", "아니요"):
            return False
        print("⚠️ 잘못된 입력입니다. 'y' 또는 'n'을 입력하세요.")
