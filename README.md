# PZ Build 42 멀티플레이 모딩 스킬

AI 코딩 에이전트가 오래된 Build 41 지식을 추측해서 사용하지 않고, 설치된 Project Zomboid Build 42 파일을 근거로 멀티플레이 모드를 설계하도록 돕는 Agent Skills 호환 스킬입니다.

## 바로 설치

Node.js가 설치되어 있다면 저장소를 직접 내려받거나 Python 명령을 입력할 필요가 없습니다.

```bash
npx skills add AsmondKR/pz-b42-mp-modding-skill
```

설치 과정에서 사용할 AI 에이전트와 프로젝트/전역 범위를 선택할 수 있습니다. 특정 에이전트에 전역 설치하려면 다음처럼 실행합니다.

```bash
npx skills add AsmondKR/pz-b42-mp-modding-skill -g -a codex -y
npx skills add AsmondKR/pz-b42-mp-modding-skill -g -a claude-code -y
npx skills add AsmondKR/pz-b42-mp-modding-skill -g -a opencode -y
```

업데이트:

```bash
npx skills update pz-b42-mp-modding-skill -g -y
```

## 사용 방법

설치한 AI 에이전트에게 원하는 모드를 자연어로 요청하면 됩니다.

```text
PZ Build 42 전용 멀티플레이 모드 구조를 설계해줘.
설치된 바닐라 Lua에서 사용할 이벤트 근거를 먼저 확인하고,
치팅 이익이나 공유 상태 불일치가 생기는 결과만 서버에서 확정하고,
UI와 로컬 표현은 클라이언트에 남겨 서버 부하가 인원수에 따라 폭증하지 않게 해줘.
```

스킬은 다음 원칙을 에이전트 작업 흐름에 적용합니다.

- 설치된 Steam 빌드와 바닐라 Lua 근거를 먼저 확인
- Steam manifest에서 빌드 정보를 확인하고 이벤트, 함수, 클래스 근거를 상대 경로와 줄 번호로 추출
- 여러 API 의존성을 동일한 Build ID와 branch 아래에서 일괄 확인
- generic reference보다 event, class, function 근거를 우선하여 제한 적용
- 모든 read-only JSON 결과에 `schema_version`을 포함한 안정적 파싱 계약
- Lua 근거 조회 중 symlink, junction, reparse 경로 추적 거부
- Build 42 패키지·Workshop metadata와 client/server 명령 경계를 읽기 전용으로 사전 검사
- B41식 unversioned `media/lua` 레이아웃을 명시적인 migration finding으로 구분
- 클라이언트 로컬, 서버 확정, 하이브리드 상태를 비용과 신뢰 경계에 따라 분류
- 권한·보상·경제·공유 영속 상태만 서버에서 확정하고 로컬 표현·파생 데이터는 전송하지 않음
- 이벤트 기반 처리, 수신자 필터링, 배치·병합, 제한된 주기로 인원 증가에 따른 서버 부하 억제
- 승인된 작업공간 안에서만 신규 B42 모드 구조 생성
- 기존 파일 덮어쓰기와 작업공간 밖 경로 이탈 거부
- 전용 서버와 실제 클라이언트를 사용한 멀티플레이 검증 요구

`npx skills`는 `skills/pz-b42-mp-modding-skill` 전용 폴더만 설치합니다. 저장소의 CI, 테스트, 기여 문서와 내부 검증 기록은 에이전트 스킬에 포함되지 않습니다.

## 안전 범위

포함된 도구는 Project Zomboid 설치 폴더, 구독한 Workshop 콘텐츠, 세이브, 자격증명, 운영 중인 서버 설정, 제3자 모드를 수정하지 않습니다. 쓰기 작업은 명시적으로 승인된 전용 작업공간 안에서만 허용되며 기존 대상이 있으면 중단합니다.

스킬만으로 임의의 프로세스를 완전히 샌드박스할 수는 없습니다. 악의적인 동시 프로세스까지 격리해야 한다면 ACL로 보호된 작업공간, VM 또는 읽기 전용 소스 마운트를 사용해야 합니다.

## 저장소 구성

- `skills/pz-b42-mp-modding-skill/SKILL.md`: 에이전트가 따르는 핵심 작업 절차
- `skills/pz-b42-mp-modding-skill/references/`: 설치되는 근거·권위·안전·검증 지침
- `tests/`: 배포 패키지 밖의 회귀 테스트
- `docs/evidence-ledger.md`: 배포 패키지 밖의 검증 기록

## 라이선스

MIT. Project Zomboid와 관련 자산의 권리는 The Indie Stone에 있습니다. 이 저장소는 게임 코드나 자산을 재배포하지 않습니다.
