# AI Harness Engineering - Project Structure Standard

## 1. 목적

Project Structure는 프로젝트의 **범용성**, **유지보수성**, **확장성**을 확보하기 위한 공통 구조를 정의한다.

프로젝트마다 개발 방식이 달라지는 것을 방지하고, AI와 개발자가 동일한 기준으로 프로젝트를 이해하고 수정할 수 있도록 한다.

본 표준은 특정 언어나 프레임워크(Spring, .NET, Python 등)에 종속되지 않는 것을 목표로 한다.

---

## 2. 설계 원칙

### 2.1 범용성

- 특정 언어나 프레임워크에 종속되지 않는다.
- CAD Add-on, Web, Desktop, CLI, AI Agent 등 다양한 프로젝트에 동일하게 적용 가능해야 한다.

### 2.2 유지보수성

- 기능이 증가해도 구조는 변경되지 않는다.
- 기능은 정해진 위치에 추가한다.

### 2.3 변경 경계(Boundary)

프로젝트 내부를 역할(Level)별로 구분하여 변경 범위를 명확히 정의한다.

목적은 수정을 막는 것이 아니라 **변경 영향도를 관리**하는 것이다.

---

## 3. 프로젝트 구조

```text
project/
├── README.md
├── docs/
│   ├── requirements/
│   ├── architecture/
│   ├── api/
│   ├── database/
│   ├── adr/
│   ├── proposals/
│   └── releases/
├── src/
│   ├── foundation/
│   ├── platform/
│   ├── features/
│   └── customization/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config/
├── tools/
└── .github/
```

---

## 4. Layer(Level)

### L0 - Foundation

역할
- Logging
- Exception
- Common Utility
- Security
- Contracts

변경 정책
- 공통 표준 변경 시에만 수정
- 일반 기능 개발로는 수정하지 않음

---

### L1 - Platform

역할
- AutoCAD API
- External API
- File System
- Authentication
- Database

변경 정책
- 변경 가능
- 리뷰 권장
- 외부 시스템 영향 확인

---

### L2 - Features

역할
- 실제 비즈니스 기능 구현

예시
- Layer Management
- Block Management
- Drawing Cleanup
- Export

변경 정책
- 일반 개발 영역
- 새로운 기능은 우선 L2에서 구현

---

### L3 - Customization

역할
- 프로젝트별 규칙
- 고객사 설정
- 템플릿
- Mapping

변경 정책
- 프로젝트별 자유 변경
- 공통 모듈에는 영향 없음

---

## 5. 의존성 규칙

```text
Customization
        ↓
Features
        ↓
Platform
        ↓
Foundation
```

| From | To | 허용 |
|------|----|------|
| Feature | Foundation | ✅ |
| Platform | Foundation | ✅ |
| Customization | Feature | ✅ |
| Foundation | Feature | ❌ |
| Foundation | Platform | ❌ |

Foundation은 상위 비즈니스 기능을 알지 않아야 한다.

---

## 6. AI Harness 적용 원칙

AI는 다음 순서로 작업한다.

```text
Task 분석
    ↓
Project Context 확인
    ↓
영향 범위 분석
    ↓
가능하면 L2에서 해결
    ↓
L1 변경 필요 여부 판단
    ↓
L0 변경 필요 여부 판단
    ↓
구현
```

원칙

1. 기능 구현은 L2를 우선한다.
2. 프로젝트별 차이는 L3에서 해결한다.
3. L1 변경은 리뷰를 권장한다.
4. L0 변경은 공통 구조 개선이 필요한 경우에만 수행한다.

---

## 7. 적용 예시

### 레이어 자동 정리 기능 추가

변경 대상
- Features
- Customization

변경 없음
- Foundation
- Platform

### 인증 서버 연동

변경 대상
- Platform
- Features

### Logging Framework 교체

변경 대상
- Foundation

---

## 8. 핵심 원칙

- 구조는 기술이 아닌 역할 중심으로 설계한다.
- 변경은 가능한 낮은 영향도의 Layer에서 해결한다.
- 공통 기능과 프로젝트 기능을 분리한다.
- 프로젝트별 차이는 Customization으로 해결한다.
- AI와 개발자는 동일한 구조와 규칙을 기준으로 작업한다.
