---
name: add-comments
description: 코드 파일에 이번 주 학습 개념을 반영한 주석을 추가한다. "주석 달아줘", "comment", "docstring 추가", "@파일명 주석" 같은 요청에 활성화.
---

# Add Comments Skill

사용자가 코드 파일에 주석을 달아달라고 요청하면 이 스킬을 사용한다.

## 동작 순서

1. `CLAUDE.md`에서 `CURRENT_WEEK` 값 확인
2. `docs/weekly/WEEK_{CURRENT_WEEK}.md` 읽어 이번 주 핵심 개념 파악
3. 대상 파일 읽기
4. 파일 상단 헤더가 없으면 추가
5. 각 함수/클래스에 Google Style docstring 추가 (이미 있으면 덮어쓰지 않음)

## 주석 양식

### Python

```python
# =============================================================
# File   : filename.py
# Author : @git-username
# Week   : XX | Ch.XX~XX
# Created: YYYY-MM-DD
# =============================================================

def function_name(param: type) -> type:
    """함수 역할 한 줄 설명.

    [Week XX | @author]
    이번 주 학습 내용과의 연결 설명 (1~2줄).

    Args:
        param: 파라미터 설명

    Returns:
        반환값 설명

    Raises:
        ExceptionType: 발생 조건
    """
```

### TypeScript / JavaScript

```typescript
// =============================================================
// File   : filename.ts
// Author : @git-username
// Week   : XX | Ch.XX~XX
// Created: YYYY-MM-DD
// =============================================================

/**
 * 함수 역할 한 줄 설명.
 *
 * [Week XX | @author]
 * 이번 주 학습 내용과의 연결 설명 (1~2줄).
 *
 * @param param - 파라미터 설명
 * @returns 반환값 설명
 * @throws 발생 조건
 */
```

## 규칙

- `[Week XX | @author]` 태그는 반드시 포함할 것
- 개념 연결은 반드시 현재 주차 WEEK_XX.md 내용 기반으로 작성
- 이미 docstring이 있는 함수는 덮어쓰지 않음
- 파일 헤더가 이미 있으면 추가하지 않음
- git config user.name 으로 author 자동 추출
