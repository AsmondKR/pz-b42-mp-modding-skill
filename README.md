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

## 이미지와 Blender FBX 에셋

이 스킬은 이미지 생성 API를 호출하지 않습니다. 에이전트가 모드의 시각 세계와 에셋 brief를 작성하고, Codex 앱에 붙여 넣을 이미지 프롬프트를 출력합니다. 생성한 콘셉트, 아이콘, 정사영 reference와 texture reference는 사람이 검토한 뒤 Blender 제작에 사용합니다.

Blender 5.1 이상이 설치되어 있으면 정책으로 승인된 작업공간 안에서 다음 단계를 사용할 수 있습니다.

```bash
python skills/pz-b42-mp-modding-skill/scripts/validate_asset_manifest.py \
  --policy <workspace>/.pz-skill-policy.json \
  --manifest <workspace>/asset.json

python skills/pz-b42-mp-modding-skill/scripts/plan_blender_asset.py validate \
  --policy <workspace>/.pz-skill-policy.json \
  --manifest <workspace>/asset.json
```

두 번째 명령은 Blender를 바로 실행하지 않고 검토 가능한 명령 배열과 SHA-256을 출력합니다. 에이전트는 그 명령을 검토하고 정확히 실행합니다. `export` 계획은 scene 품질 검사를 통과해야 FBX를 신규 생성하며, 기존 FBX는 덮어쓰지 않습니다. 생성 직후 FBX를 Blender에 다시 불러와 mesh, UV, material, bounds와 armature 이름이 유지됐는지 검사합니다.

자동 검사는 topology나 경로 결함을 찾을 수 있지만 미적 품질을 승인하지 않습니다. silhouette, 재질, deformation, PZ 카메라 가독성과 실제 게임 적합성은 사람의 Blender 검수와 Build 42 게임 내 QA가 필수입니다. Build 42에서 확인되지 않은 축, skeleton, texture 또는 성능 수치는 추측해서 고정하지 않습니다.

### 실제 바닐라 FBX 크기·방향 근거

전역 PZ 축이나 단위를 가정하지 않습니다. 설치된 Build 42에서 같은 역할의 바닐라 FBX를 선택하고 다음 명령으로 읽기 전용 분석 계획을 만듭니다.

```bash
python skills/pz-b42-mp-modding-skill/scripts/plan_pz_fbx_reference.py \
  --sample held_open_razor=media/models_X/StraightRazor_Open.fbx \
  --sample vehicle_normal=media/models_X/vehicles/Vehicles_CarNormal.fbx
```

계획은 Build ID, branch, Blender 경로와 정확한 파일을 SHA-256 명령으로 묶습니다. 실행 결과에는 FBX encoding, version, 축 metadata, unit metadata, raw 또는 Blender-imported bounds, triangle 수와 파일 hash가 포함되며 게임 설치에는 아무것도 쓰지 않습니다.

public Build `24574865`의 shipped 표본에서는 `Front -X / Coord +Z`와 `Front +Z / Coord +X`가 동시에 발견됐고 unit metadata도 서로 달랐습니다. 무기 geometry도 실제로 작습니다. 예를 들어 `Machete.x`의 raw envelope는 약 `0.0094 x 0.3345 x 0.0566`이고, closed butterfly knife는 큰 raw FBX에 model-script `scale = 0.01`을 적용합니다. 따라서 `0.01`은 필요할 수 있는 geometry/conversion 또는 script layer이지 universal FBX exporter setting은 아닙니다. 한 vanilla reference의 raw geometry와 그 reference의 model-script transform을 한 쌍으로 맞추고, `0.01`이 필요하면 geometry bake 또는 script scale 중 한 계층에서만 적용합니다. checked-in exporter의 `Global Scale = 1.0`은 유지합니다. FBX bounds와 model-script `scale`을 곱해 runtime metre라고 주장하지 않습니다.

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
