# AGENTS.md

## 프로젝트 개요

이 저장소는 NEIS 교육정보 개방 포털 API로 학교를 검색하고 지정한 기간의 중식
메뉴를 조회하는 **급식 배틀** 웹 애플리케이션과 단계별 워크숍 문서를 함께
관리합니다.

현재 애플리케이션은 다음 구성으로 구현되어 있습니다.

- `src/web`: React, TypeScript, Vite 기반 프론트엔드
- `src/api`: FastAPI, Pydantic, HTTPX 기반 백엔드
- `src/e2e`: Docker Compose 스택을 대상으로 실행하는 Playwright E2E
- `src/openapi.json`: 프론트엔드와 백엔드 사이의 내부 API 계약
- `data/openapi.json`: 백엔드가 호출하는 외부 NEIS API 계약
- `compose.yml`: 프론트엔드와 백엔드 컨테이너 구성
- `scripts`: Bash 및 PowerShell 실행·전체 테스트 스크립트

AI 분석, MCP, 멀티 에이전트 및 데이터베이스 기능은 이후 워크숍 단계의
범위이며 현재 급식 조회 MVP에 미리 추가하지 않습니다.

## 핵심 동작과 제약

- 프론트엔드는 학교 검색, 날짜 선택, 결과 표시를 단일 URL(`/`)에서 처리하며
  선택 조건은 React 내부 상태로 관리합니다.
- 브라우저는 NEIS를 직접 호출하지 않고 `/api/v1` 백엔드만 사용합니다.
- 백엔드는 NEIS 원본 필드를 내부 camelCase 응답 모델로 정규화합니다.
- 급식 종류는 `MMEAL_SC_CODE=2`인 중식으로 고정합니다.
- 검색어는 공백 제거 후 2자 이상이어야 합니다.
- 조회 기간은 한국 표준시 기준 직전 달 1일부터 오늘까지입니다.
- NEIS가 반환하지 않은 날짜는 프론트엔드에서 `급식 정보 없음` 카드로
  보완합니다.
- `NEIS_FIXTURE_MODE=true`는 실제 API 키와 NEIS 가용성에 의존하지 않는
  로컬 데모 및 E2E 전용 모드입니다.

## 일반 작업 지침

- 요청된 변경 범위 안에서만 작업하고 관련 없는 코드는 수정하지 않습니다.
- `PRD.md`, `TRD.md`, `CONTRIBUTING.md`와 디렉터리별 설정을 확인하고 기존
  구현과 명령을 우선 사용합니다.
- 새로운 추상화나 의존성을 추가하기 전에 기존 컴포넌트, 훅, 서비스 및
  클라이언트를 재사용할 수 있는지 확인합니다.
- 외부 NEIS 모델과 내부 API 모델의 경계를 유지하고 원본 응답을 프론트엔드에
  노출하지 않습니다.
- 사용자에게 표시되는 문구와 날짜 표기는 한국어 사용자를 기준으로 합니다.

## 프론트엔드 지침

- `src/web/src/App.tsx`가 학교, 날짜 범위 및 현재 단계의 상태 원본입니다.
  검색 조건을 URL path, query parameter 또는 전역 상태 라이브러리에
  중복 저장하지 않습니다.
- 서버 상태는 TanStack Query 훅을 통해 관리하고 API 호출은
  `src/web/src/api-client/client.ts`에 모읍니다.
- Date Picker는 `react-day-picker`를 감싼 기존 `DateRangePicker`를
  재사용하며 날짜 경계 검증은 `src/web/src/lib/dateRange.ts`에 둡니다.
- TypeScript의 엄격한 타입을 유지하고 `any`, 불필요한 타입 단언 및 null
  가능성 무시를 피합니다.
- 로딩, 빈 결과, 검증 오류 및 네트워크·백엔드 오류를 서로 구분해 표시합니다.
- 모바일 우선 레이아웃, 키보드 조작, 명확한 포커스와 접근 가능한 이름을
  유지합니다.
- `src/web/src/api-client/schema.d.ts`는 `src/openapi.json`에서 생성된
  파일입니다. 직접 수정하지 말고 다음 명령을 사용합니다.

  ```sh
  cd src/web
  npm run generate:api
  ```

## 백엔드 지침

- 계층별 책임을 유지합니다.
  - `api`: FastAPI 라우팅과 요청 파라미터
  - `services`: 날짜 검증, 유스케이스 및 내부 모델 정규화
  - `clients`: NEIS HTTP 호출과 외부 응답 구조 파싱
  - `models`: 내부 응답 스키마
  - `settings.py`: 환경 변수 검증
- 비동기 외부 호출에는 기존 `NeisClient`와 `SchoolAndMealClient` 경계를
  사용해 테스트에서 fixture 또는 HTTP mock으로 교체할 수 있게 합니다.
- NEIS의 문서상 타입과 실제 JSON 타입이 다를 수 있으므로 외부 값을 사용하기
  전에 검증하고 좁힙니다. 잘못된 값을 임의로 성공 데이터로 변환하지 않습니다.
- 예상 가능한 오류는 구체적인 내부 예외로 변환하고 `ProblemDetail` 응답으로
  전달합니다. 원본 응답, 스택 추적 및 API 키를 사용자 응답에 포함하지
  않습니다.
- 공개 함수와 계층 경계에는 명확한 타입 힌트를 사용하고 광범위한 `Any`나
  무분별한 형 변환을 피합니다.

## 의존성과 생성 파일

- 프론트엔드 의존성은 `src/web/package.json`과 `package-lock.json`,
  E2E 의존성은 `src/e2e/package.json`과 `package-lock.json`으로
  관리합니다. 변경 시 npm 명령으로 잠금 파일을 함께 갱신합니다.
- 백엔드 의존성은 `src/api/pyproject.toml`과 `uv.lock`으로 관리하며
  `uv add` 또는 `uv remove`를 사용합니다.
- 잠금 파일, OpenAPI 생성 타입 및 빌드 산출물을 수동으로 편집하지 않습니다.
- 표준 라이브러리나 기존 의존성으로 해결 가능한 기능을 위해 새 패키지를
  추가하지 않습니다.

## 실행과 테스트

저장소 루트에서 전체 애플리케이션을 직접 실행합니다.

```sh
./scripts/run-app.sh
```

```powershell
.\scripts\run-app.ps1
```

스크립트는 Vite와 FastAPI 개발 서버를 직접 실행하고 `Ctrl+C` 입력 시 두
프로세스를 모두 종료합니다. 실제 NEIS를 사용할 때는 `.env.example`을
참고해 루트 `.env`에 `NEIS_API_KEY`를 설정합니다.

전체 검증은 다음 스크립트를 우선 사용합니다.

```sh
./scripts/run-test.sh
```

```powershell
.\scripts\run-test.ps1
```

전체 테스트는 잠금 파일 기준 의존성을 복원하고 백엔드 pytest, 프론트엔드
Vitest, fixture 모드 Compose 스택의 Playwright E2E를 실행한 뒤 스택을
정리합니다.

변경 범위가 작을 때는 다음 명령으로 대상 검사만 먼저 실행할 수 있습니다.

```sh
cd src/api && uv run pytest
cd src/web && npm run lint && npm run build && npm test
cd src/e2e && npm test
docker compose config
```

- 변경된 동작에는 해당 계층의 단위 또는 통합 테스트를 추가합니다.
- 학교 검색부터 급식 결과까지의 사용자 흐름, 모바일 레이아웃 또는 키보드
  조작이 바뀌면 Playwright 테스트도 갱신합니다.
- E2E는 반드시 fixture 모드를 사용해 실제 NEIS와 비밀 값에 의존하지 않게
  유지합니다.

## 보안

- 비밀, 자격 증명, 토큰 및 개인정보를 코드, 로그, 테스트 데이터 또는 커밋에
  포함하지 않습니다.
- `.env`, `.env.*`(예제 파일 제외), 개인 키 및 자격 증명 파일을 커밋하지
  않습니다.
- `NEIS_API_KEY`는 백엔드 프로세스와 컨테이너에만 주입하고 `VITE_*`,
  프론트엔드 번들 또는 브라우저 응답에 포함하지 않습니다.
- 외부 입력과 NEIS 응답을 신뢰하지 않으며 최소 권한과 안전한 기본값을
  사용합니다.
- 보안 취약점은 공개 이슈에 작성하지 않고 `SECURITY.md` 절차를 따릅니다.

## 문서와 Git

- 사용자 동작, 내부 API, 환경 변수, 실행 또는 테스트 절차가 바뀌면 관련
  문서와 예제도 함께 갱신합니다.
- 주석은 코드만으로 경계나 의도를 설명하기 어려운 경우에만 작성합니다.
- 커밋은 하나의 논리적 변경에 집중하고 Conventional Commits 형식
  (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`)을 따릅니다.
- PR은 `.github/PULL_REQUEST_TEMPLATE.md` 구조를 유지하고 관련 이슈,
  변경 유형, 검증 결과 및 체크리스트를 작성합니다.
- 기존 사용자 변경을 덮어쓰거나 요청 없이 파괴적 Git 명령, 전면 포맷팅 또는
  대규모 이름 변경을 수행하지 않습니다.
