# 구축 검증 기록

검증일: 2026-09-12

- Python 표준 라이브러리 테스트 16개 통과: 정상 일정, 휴무, 브레이크타임, 이동 부족, 중복 시간, 예산 초과, 미확인 비용, 필수 방문 누락, 출처 충돌, 시간대 누락, 음수 비용, 자정 넘김, 빈 일정, 입장 마감, 첫 이동, 단순 통과와 방문 구분.
- 별도 서브에이전트가 파일을 읽고 날짜 미정·숙박 조회 실패·영업시간 출처 충돌 시나리오를 모의 검토했다. 실제 웹 조사는 하지 않았다.
- 검토 결과 반영: 날짜 미정은 상대 일차 탐색 문서로 보존, 미확인 비용은 총액 null/알려진 부분합 분리, 입장 마감 검사 추가.
- skill-creator의 quick_validate.py는 두 Python 환경 모두 PyYAML 미설치로 실행 불가. 검사기 원문과 생성 파일을 대조하여 frontmatter의 name/description, 이름 형식, 미완성 자리표시자 부재를 수동 확인했다. 참조 문서와 실행 스크립트가 존재한다.
- 실제 여행 조사·예약 가능 여부·운영 정보의 정확성은 아직 검증하지 않았다. 첫 여행 실행에서 실제 서브에이전트 조사와 독립 감사가 필요하다.

설치 범위: 현재 프로젝트. 전역 스킬 등록이나 별도 API 서비스 설치는 하지 않았다. 프로젝트 AGENTS.md가 로컬 스킬을 연결한다.

## 범용화 검증

- 대구 목적지·한국 시간대·원화 고정을 제거하고 목적지와 통화를 실행 입력으로 변경했다.
- version 2 비용 계약과 통화 불일치 거절을 추가했다. version 1은 명시적 이관 안내와 함께 거절한다.
- 해외 통화, 혼합 통화 거절, 날짜변경선, 일광절약시간 종료, 서로 다른 시간대의 중복, 이전 버전 거절 테스트를 추가했다.
- 실제 해외 정보 조회나 환율 자동 연동을 구현했다는 의미는 아니다. 원문 조회와 현지 시간대·환산 근거 확인은 여행 실행 때 담당 에이전트가 수행한다.

## 산출물 제작 역할 추가

- artifact-producer 역할과 총괄의 제작 배정·검수·최종 등록 경로를 추가했다.
- 사용자 지정 형식을 입력받으며, 미지정 시 총괄이 질문한다. 임의 MD 생성 및 실패 시 무단 형식 대체를 금지했다.
- 조사자의 읽기 전용 규칙과 구분해 제작자의 작업별 staging 쓰기 범위, 입력 버전·해시, 산출물 manifest 계약을 정의했다.
- 변경된 지침에서 형식 기본값과 쓰기 권한 충돌을 정적 점검했다. 실제 PDF·MD 생성은 여행 원본과 사용자 형식 입력을 받은 후 실행한다. 이번 변경은 지침이며 별도의 파일 변환 프로그램을 추가한 것은 아니다.

## 최종 리뷰 지적 수정

- 금액 합산·예산 비교를 Decimal로 변경했다. 1.1+2.2가 예산 3.3을 초과한다고 판정하던 사례와 실제 초과 사례를 회귀 검사했다.
- 최상위 객체, 배열 필드, 중첩 레코드, ID, 영업 구간의 입력 형태를 검사한다. 잘못된 costs 객체 등은 CLI에서 종료코드 2로 반환한다.
- 조건 변경 시 revision을 먼저 증가시키고 기존 원본·감사·제작 작업을 무효화하는 규칙을 명시했다.
- current_source에 탐색/확정 원본 종류·경로·버전·상태·해시를 저장하고 날짜 미정 전환 및 기존 상태 이관을 정의했다.
- 제작 job의 형식·경로·원본·제작 버전을 실행 전에 저장하며, 복사 중단 후 동일 해시 파일 재사용과 중복 없는 최종 등록을 정의했다.
- 29개 Python 테스트 통과. 최초 실행은 Windows 임시 폴더 권한으로 CLI 테스트 2건이 실패했으며 승인된 재실행에서 모두 통과했다.
- 상태·제작 복구 수정은 에이전트 실행 지침이다. 실제 PDF/MD 생성·중단·복구를 종단간 실행한 결과는 아니다.
- 독립 리뷰어가 조사 중 날짜 변경, 확정→미정 후 MD 요청, 파일 복사 후 상태 저장 전 중단의 세 시나리오를 정적 검토했다. 모두 지침상 통과했으며 명확한 모순은 발견하지 못했다.

## Codex / Claude Code 공통화

- 공통 코어에서 플랫폼 전용 도구명을 제거하고 adapters/codex.md, adapters/claude.md와 공통 runtime 계약으로 분리했다.
- 프로젝트 Codex 스킬 진입점(.agents/skills), Claude Code 스킬 진입점(.claude/skills), CLAUDE.md, Claude 조사·감사·제작 에이전트 3개를 추가했다.
- 전체 프로젝트를 옮기는 배포 방식이며 진입점만 전역 복사하는 설치는 지원하지 않는다. 경로 계산과 기능 미지원 처리, 플랫폼 전환 시 단일 작성자와 실행 ID 처리 규칙을 정의했다.
- 공통 테스트와 호환 구조 테스트 33개 통과. 실제 경로와 에이전트 정의 존재, 공통 문서에 특정 호스트 도구명 부재를 검사했다.
- 로컬 CLI 확인: Codex 0.154.0-alpha.6.2, Claude Code 2.1.224. CLI 존재는 모델 실행 검증과 다르다.
- Claude 읽기 전용 스모크 테스트는 자동 승인 검토가 명령 실행 전에 거절했다. 이유는 프로젝트 내용을 외부 Claude 서비스에 전송하고 최대 1달러를 사용하는 것에 대한 명시적 승인 부재다. 우회 실행하지 않았다.
- 따라서 Claude 실제 모델 실행, 양쪽 PDF 제작 및 플랫폼 전환 종단간 테스트는 미검증이다. 현재 결과는 공통화 구현 및 로컬 테스트 통과이며 완전한 실환경 호환 인증이 아니다.

## Claude Code 실제 실행 스모크테스트 (Codex 토큰 소진 후 Claude가 이어받아 검증)

검증일: 2026-09-12

- 목적: VERIFICATION.md가 남긴 "Claude 실제 모델 실행 미검증" 항목을 실제로 해소한다. 실제 여행이 아니라 실존하지 않는 가상 목적지("Testville")로 `runs/smoketest-001/`을 만들어 총괄(현재 Claude Code 세션) → travel-researcher → travel-auditor → travel-artifact-producer 전체 경로를 실제 Agent 도구 호출로 실행했다. 목적지를 가상으로 둔 이유는 진짜 지리 정보 정확성이 아니라 하네스의 위임·상태·경계 계약 자체가 동작하는지만 보기 위함이다.
- 후보 2개(c-museum 필수, c-cafe)와 검사 통과(errors=0, 경고 7건)하는 plan-v002 계약 JSON을 만들어 `scripts/validate_plan.py`로 통과시켰다.
- travel-researcher(Agent 도구, subagent_type=travel-researcher)에게 role=discovery-experience로 실제 WebSearch를 수행하게 했다. "Testville"이 실존하지 않음을 실제 검색으로 재확인했고, 이름이 비슷한 실제 지명(Test Valley, Titusville)을 대신 채택하지 않고 status=failed와 이유를 정직하게 반환했다 — 허구 생성 금지 원칙이 실제로 지켜짐을 확인했다.
- travel-auditor(Agent 도구)에게 실제 감사를 맡겨 verdict=conditional, status=partial과 blocker 3건(F1 개장 미확인, F2 입장료 미확인으로 예산 판단 불가, F3 이동 근거 없음), warning 2건을 받았다. 코드 검사 결과와 파일 내용을 대조해 임의로 통과 판정하지 않았다.
- **발견한 결함과 조치**: 총괄이 state.json에 plan 파일의 sha256을 손으로 옮겨 적으며 마지막 글자를 빠뜨렸다. travel-auditor는 코드 실행 도구가 없어 원본 바이트로 해시를 재계산하지 못하고 총괄이 준 값과 state.json 기록값의 문자열 일치만 확인하므로 이 오탈자를 잡아내지 못했다 — 감사 결과 자체는 그 사실을 unchecked 항목으로 정직하게 표시했다. 재발 방지를 위해 `references/protocol.md`의 상태 절에 "해시는 항상 실행 도구로 계산한 값을 그대로 복사하고 손으로 옮겨 적지 않는다"는 규칙을 추가했다.
- travel-artifact-producer(Agent 도구)에게 MD 형식 제작을 맡겼다. staging(`runs/smoketest-001/staging/produce-001/`) 밖에는 쓰지 않았고, PowerShell Get-FileHash로 원본 3개 파일의 해시를 직접 재계산해 총괄이 전달한 값과 대조한 뒤 제작을 시작했다. 결과 itinerary.md는 상태(조건부 초안)·blocker/warning 5건·감사 unchecked 4건·미확인 비용으로 인한 총액 null을 전부 보존했고, 어떤 금액·시간도 검증됨으로 격상하거나 0으로 대체하지 않았다.
- 총괄(현재 세션)이 producer의 manifest.json과 itinerary.md를 다시 읽고 Python으로 해시를 독립 재계산해 일치를 확인한 뒤 `runs/smoketest-001/artifacts/v001/itinerary.md`로 등록하고 state.json의 phase를 delivered로, artifacts 배열을 갱신했다.
- 회귀 확인: 33개 기존 Python 테스트 모두 통과 유지.
- **이번에 검증된 것**: Claude Code에서 Agent 도구로 조사자·감사자·제작자 3개 프로젝트 서브에이전트를 실제로 호출·완료했고, 각자 배정된 역할 파일만 읽고 재위임 없이 결과 계약(candidates/findings/verdict/manifest)을 반환했으며, 제작자의 staging 쓰기 경계와 총괄의 해시 대조·최종 등록 절차가 실제로 동작했다. 허구 생성 금지·경고 비생략 원칙도 실제 모델 출력에서 지켜졌다.
- **여전히 미검증인 것**: (1) Codex 쪽 실제 모델 실행 — 이 세션은 Claude이므로 Codex CLI로 동일 스모크테스트를 재현하지 못했다. (2) 실제 지리·영업시간·가격 조사 — 목적지를 의도적으로 가상으로 두었으므로 이번 테스트는 사실 검증 능력을 증명하지 않는다. (3) PDF/DOCX/XLSX 등 MD 이외 형식의 실제 렌더링 — 이번에는 MD만 제작했다. (4) 플랫폼 전환(Codex↔Claude) 종단간 재개 시나리오. `runs/smoketest-001/`은 합성 테스트 데이터이며 실제 여행에 재사용하지 않는다.

## 스모크테스트 이후 보완 (같은 검증일)

- **제작자 도구 범위 축소**: `.claude/agents/travel-artifact-producer.md`에 `tools:` 목록이 없어 호스트의 모든 도구(WebSearch·Agent 재위임 포함)를 기술적으로 상속하고 있었다. 지침(재위임 금지, 웹 조사 아님)과 실제 권한이 불일치했던 것을 발견해 `tools: Read, Write, Edit, Bash, PowerShell, Glob, Grep, Skill`로 명시 축소하고, WebSearch/WebFetch/Agent를 제외했다.
- **레지스트리 파일 존재 테스트 추가**: `roles/registry.json`이 가리키는 역할 파일이 실제 존재하는지 확인하는 `test_registry_paths_exist`, 그리고 세 Claude 서브에이전트의 `tools:` 목록이 각자 역할 경계(조사자·감사자는 쓰기·실행·재위임 도구 없음, 제작자는 웹조사·재위임 도구 없음)를 벗어나지 않는지 확인하는 `test_producer_tools_scoped`/`test_researcher_and_auditor_tools_scoped`를 추가했다. 총 36개 테스트로 확장, 모두 통과.
- **위임 전 규모 고지 추가**: 이번 검증을 촉발한 원인("Codex 토큰 소진")과 직결된 보완이다. `SKILL.md` 3단계와 `roles/coordinator.md` 의사결정 2단계에 "실제 서브에이전트 위임 전 예상 조사자 수·라운드를 한 줄로 사용자에게 알린다"는 규칙을 추가해, 다도시·다분야로 라운드가 늘어나는 큰 여행에서 사용자가 진행 전 규모를 가늠할 수 있게 했다.
- 이 세 항목은 지침·테스트 변경이며, 실제 대규모 다도시 여행에서 라운드가 실제로 어떻게 늘어나는지는 첫 실제 여행 실행에서 확인한다.

## 에이전트 설계 검토 후 보완 (같은 검증일)

기술적 권한·테스트가 아니라 역할 설계 자체를 다시 검토해 3가지를 수정했다.

1. **탈락 사유 로그(decisions-vNNN.md) 도입**: `references/protocol.md`에 새 계약을 추가했다. 총괄이 후보 비교 시 채택·탈락 이유(candidate_id, decision, reason, compared_with)를 `decisions-vNNN.md`에 남기고 state.json에 `latest_decisions`로 포인터를 저장한다. 기존 상태에 없으면 null로 취급해 하위 호환한다. `roles/coordinator.md` 4단계와 `SKILL.md` 8단계에서 이 저장을 명시적으로 요구하도록 연결했다. 대화 맥락이 압축·소실돼도 "왜 이 후보를 뺐는지" 답할 근거가 남는다.
2. **logistics/숙박 역할 분리 기준 명문화**: `roles/logistics.md`를 이동 전용으로 축소하고, 숙박 전용 `roles/lodging.md`(discovery-lodging)를 새로 만들어 `roles/registry.json`에 등록했다. 기본 분리 기준(2개 도시 이상 이동 또는 숙박 3박 이상)을 `references/roles.md` 표와 `SKILL.md` 5단계에 명시했다. 그 미만 규모는 기존처럼 logistics가 겸임한다. `adapters/claude.md`의 delegate 목록도 갱신했다. `test_registry_paths_exist`가 새 역할 파일 존재를 자동으로 검증했다(수정 없이 통과).
3. **부분 재감사(scoped audit) 경로 추가**: 이번 세션의 발단(Codex 토큰 소진)과 직결된 항목이다. `references/protocol.md`에 부분 재감사 조건(budget·통화·required_ids·인원/객실·날짜·일수 불변, 변경 item/후보/cost 2개 이하)과 절차를 추가했다. `roles/auditor.md`에 scope(full/scoped) 입력·출력 필드, 선언되지 않은 변경을 발견하면 즉시 failed로 중단하는 안전장치, carried_forward(직전 감사에서 재검증 없이 옮긴 항목)를 추가했다. `roles/coordinator.md` 6단계와 `SKILL.md` 7단계에서 조건 충족 시에만 scope=scoped를 요청하도록 연결했다.
- 36개 테스트 회귀 통과 유지. 세 항목 모두 지침·계약 변경이며, scoped audit이 실제 다회차 수정 시나리오에서 비용을 얼마나 줄이는지와 lodging 분리가 실제 다도시 여행에서 잘 작동하는지는 첫 실제 여행 실행에서 확인한다.

## 첫 실제 여행 실행 — 서울→대구 1박2일 (같은 검증일)

- 사용자가 실제 여행(서울 출발, 대구 1박2일 2026-09-18~19, 2인, 대중교통, 2인 총 60만원 KRW)을 요청해 총괄·조사자 3명(discovery-food/discovery-experience/logistics+lodging 겸임 — 1개 도시·1박이라 분리 기준 미달)을 실제로 실행했다. 합성 데이터가 아니라 실제 웹 조사(뭉티기·막창 실존 매장, 2026-09 KTX·SR 통합 요금, 대구도시철도 실제 노선도)다.
- **실제 버그 발견·수정**: `scripts/validate_plan.py`를 Windows Git Bash(cp949 콘솔)에서 실행하니, 계획 JSON 자체는 문제없는데 `unresolved` 문구의 줄표(—, U+2014)가 cp949로 인코딩 불가해 `print()`가 UnicodeEncodeError를 던졌고, 이를 broad except가 잡아 "input_error"(입력 형태 오류)로 잘못 보고했다. PowerShell(UTF-8 콘솔)에서는 동일 파일이 정상 통과(exit 0)해 계획 자체는 정상임을 먼저 확인했다. `sys.stdout.reconfigure(encoding='utf-8')`을 추가해 콘솔 코드페이지와 무관하게 항상 UTF-8로 출력하도록 고쳤다. 이 버그는 한글 텍스트 자체는 cp949로 정상 인코딩되기 때문에 이전의 어떤 합성 스모크테스트에서도 드러나지 않았고, 줄표 같은 문장부호가 실제 한국어 글쓰기 습관으로 자연스럽게 들어간 이번 실사용에서야 발견됐다.
- `tests/test_validate_plan.py`에 회귀 테스트(`test_cli_handles_non_cp949_characters`)를 추가했다. 자식 프로세스만 `PYTHONIOENCODING=cp949`로 강제하고 부모 프로세스는 `subprocess.run(..., encoding='utf-8')`로 명시 디코딩해야 한다는 것도 직접 겪었다 — 그렇지 않으면 이 Windows 환경의 기본 로케일이 cp949라 테스트 자체도 부모 쪽에서 같은 종류의 디코딩 오류로 거짓 실패했다. 37개 테스트 통과.
- 코드 검사 결과: errors=0, known_cost_subtotal=[351000, 502000] KRW, budget_amount=600000 KRW — 동대구역 인근 식사(장소 미지정, 비용 unknown) 1건을 제외하고도 상한선 기준 예산 내(여유 약 98,000원 이상).
