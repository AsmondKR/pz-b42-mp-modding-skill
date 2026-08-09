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
클라이언트 요청은 서버에서 다시 검증하도록 만들어줘.
```

스킬은 다음 원칙을 에이전트 작업 흐름에 적용합니다.

- 설치된 Steam 빌드와 바닐라 Lua 근거를 먼저 확인
- 클라이언트, 서버, shared 코드의 책임 분리
- 권한, 저장, 보상, 월드 상태 변경은 서버 권위로 처리
- 승인된 작업공간 안에서만 신규 B42 모드 구조 생성
- 기존 파일 덮어쓰기와 작업공간 밖 경로 이탈 거부
- 전용 서버와 실제 클라이언트를 사용한 멀티플레이 검증 요구

## 안전 범위

포함된 도구는 Project Zomboid 설치 폴더, 구독한 Workshop 콘텐츠, 세이브, 자격증명, 운영 중인 서버 설정, 제3자 모드를 수정하지 않습니다. 쓰기 작업은 명시적으로 승인된 전용 작업공간 안에서만 허용되며 기존 대상이 있으면 중단합니다.

스킬만으로 임의의 프로세스를 완전히 샌드박스할 수는 없습니다. 악의적인 동시 프로세스까지 격리해야 한다면 ACL로 보호된 작업공간, VM 또는 읽기 전용 소스 마운트를 사용해야 합니다.

## 저장소 구성

- `SKILL.md`: 에이전트가 따르는 핵심 작업 절차
- `references/source-of-truth.md`: Build 42 근거 우선순위
- `references/multiplayer-authority.md`: 서버 권위형 네트워크 설계
- `references/safety-boundaries.md`: 파일 쓰기 승인 범위

## 라이선스

MIT. Project Zomboid와 관련 자산의 권리는 The Indie Stone에 있습니다. 이 저장소는 게임 코드나 자산을 재배포하지 않습니다.
