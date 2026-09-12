# 상태·근거·계획 계약

## 상태

플랫폼 기능·경로 이관·실행 식별자 분리는 runtime.md를 따른다. 영속 state/manifest의 프로젝트 파일 경로는 프로젝트 상대경로로 저장하고, 도구 호출과 작업 지시서에서는 절대경로로 해석한다. 플랫폼을 바꾸어도 계획·revision·원본 해시 계약은 동일하다.

state.json: version=1, trip_id, brief_revision(정수), phase(intake/research/compose/audit/produce/delivered), brief(사용자 입력), assumptions, jobs(작업ID·역할·revision·상태; 감사 job은 scope:full/scoped를 포함), unresolved, latest_plan, latest_decisions, next_action, artifacts(파일 경로·제작 버전·원본 버전·검수 상태 배열). 기존 상태에 artifacts 또는 latest_decisions가 없으면 각각 빈 배열·null로 취급한다. 총괄은 단계 완료와 사용자 수정 후 저장한다. 중단 후 완료된 작업은 재사용하고 실행 중이던 작업은 결과 유무를 확인한 뒤 재배정한다. 제작 작업의 복구·등록은 artifact-producer.md를 따른다.

현재 원본의 단일 기준은 current_source다. 값은 null 또는 {kind: plan/exploration, path, version, brief_revision, status: exploration/conditional/verified, sha256}이다. 검증·제작은 이 포인터만 사용하고 파일명·수정 시각으로 최신 원본을 추측하지 않는다. latest_plan은 호환용이며 current_source.kind=plan일 때만 같은 경로, 그 외에는 null이다. 탐색 초안의 경로·버전·상태도 current_source에 보존한다. phase=delivered는 전달 단계이지 검증 상태가 아니다.

초기 brief_revision은 1이다. 목적지·날짜·인원·예산·통화·선호·필수 조건·예약 등 계획에 영향을 주는 변경을 수락하면, 새 작업이나 결과 병합 전에 반드시 revision을 1 증가시킨다. 같은 저장 작업에서 brief를 갱신하고 current_source/latest_plan을 null로, 이전 감사와 계획·제작 작업을 stale로 표시하고 phase=research로 되돌린다. 이전 파일과 산출물은 이력으로 보존하되 최신 검증 결과로 제공하지 않는다. 형식·서체 등 표현만 바꾸면 brief_revision은 유지하고 제작 버전만 올린다.

revision이 다른 조사 결과는 직접 병합하지 않는다. 영향 없는 결과도 총괄이 변경 조건과 대조한 뒤 현재 revision의 재사용 기록(reused_from 작업ID와 원래 확인 시점)을 남겨 채택한다. 날짜를 미정으로 변경하면 기존 plan은 최신 포인터에서 해제하고 새 exploration을 작성한다. 새 원본을 저장한 후 해시와 revision을 포함해 current_source를 설정한다. 감사 결과도 원본 경로·해시·revision에 연결하며 불일치한 감사는 재사용하지 않는다.

state 저장은 총괄 단일 작성자로 제한한다. 같은 디렉터리의 임시 파일에 완전한 JSON을 쓴 뒤 원자적 replace로 교체한다. 새 세션은 current_source 경로·해시·revision을 확인한다. 이전 state에 current_source가 없으면 latest_plan과 원본을 대조해 검증 상태를 conditional로 이관하고 재감사한다. 식별 불가하면 current_source=null로 두고 조사 기록에서 복구한다. 파일명만으로 verified를 부여하지 않는다. 해시는 항상 read/write/run/check 실행 도구로 계산한 값을 그대로 복사해 저장한다. 총괄이 손으로 옮겨 적은 해시는 오탈자를 감사자가 걸러낼 수 없다 — 감사자는 대개 코드 실행 도구가 없어 전달받은 해시 문자열을 원본 바이트와 대조하지 못하고 state.json 기록값과의 문자열 일치만 확인하기 때문이다.

날짜 변경 시 운영·행사·숙박·교통·날씨를 무효화한다. 인원 변경 시 객실·총비용·예약 조건을 무효화한다. 장소 교체 시 연결된 앞뒤 이동·시간·비용을 무효화한다. 영향 없는 조사 결과는 출처 확인 시점을 보존하며 재사용한다.

## 후보와 근거

후보: id, name, category, address, area, fit_reason, duration_minutes, price_range, claims, alternatives. 정보가 없으면 null 또는 빈 배열로 남긴다. 지점이 다르면 별도 후보다.

각 claim: field, value, status(verified/estimated/unknown/conflicting), sources(URL·publisher·checked_at·적용 날짜), note. 출처는 주장별로 연결한다. checked_at은 시간대 포함 ISO 형식이다. 운영자·공식 교통·공공기관을 운영 사실의 우선 출처로 삼고 후기·블로그는 취향과 발견에 활용한다. 충돌은 소수결로 해결하지 않는다.

영업시간은 일정 날짜에 적용되는 복수 구간으로 정규화한다. 휴무는 빈 구간, 미확인은 null이다. 브레이크타임·자정 넘김·입장 마감을 반영한다. 추정 이동은 근거와 여유 시간을 명시한다. 가격은 인원·객실·박수·세금 포함 여부를 기록한다. 무료와 가격 미확인을 구별한다. 알레르기나 접근성을 후기만으로 보장하지 않는다.

최신성은 '오늘 확인했으므로 항상 유효'가 아니다. 여행 날짜에 적용되는지 확인한다. 날짜 변경과 출발 전 갱신 요청 때 주요 정보를 다시 확인한다. 날씨 예보 범위 밖이면 예측을 만들지 말고 우천 시나리오를 준비한다. 자동 모니터링은 사용자가 요청한 경우에만 설정한다.

## decisions-vNNN.md (선택·탈락 근거)

총괄은 coordinator.md 4단계의 후보 비교 결과를 decisions-vNNN.md에 남긴다. 채택 후보뿐 아니라 함께 비교했던 탈락 후보도 기록한다: candidate_id, name, category, decision(selected/rejected/alternative), reason(어떤 기준 — 필수조건/취향/동선/비용/근거확실성 — 에서 갈렸는지), compared_with(같이 비교한 candidate_id 배열), brief_revision. plan-vNNN과 같은 번호를 쓰며 후보 구성이 바뀌어 계획이 새 버전으로 올라갈 때 함께 갱신한다. 이전 버전은 지우지 않고 이력으로 보존한다. state.json의 latest_decisions에 현재 경로를 저장한다. 이 문서는 코드 검사 대상이 아니며, 대화 맥락이 압축되거나 사라진 뒤에도 "왜 이 후보를 뺐는지" 물었을 때 답할 근거를 남기기 위한 것이다.

## 부분 재감사(scoped audit)

총괄은 결함 수정 범위가 작을 때만 감사자에게 scope=scoped를 요청할 수 있다. 조건: budget_amount·budget_currency·required_ids·인원/객실 수·날짜·전체 일수가 이전 감사 시점과 동일하고, 변경된 item·후보·cost를 합쳐 2개 이하여야 한다. 하나라도 어긋나면 scope=full로 요청한다. scoped를 요청할 때는 직전 감사 결과 전체(task_id, brief_revision, verdict, findings)와 변경된 item/후보/cost id 목록, 수정 전후 근거를 함께 전달한다. 감사자가 총괄이 표시하지 않은 차이를 발견하면 scoped를 중단하고 failed로 반환한다 — 이 경우 총괄은 scoped 실패를 조건부 초안의 근거로 쓰지 않고 즉시 scope=full로 재요청한다. scoped 감사 결과의 carried_forward 항목(이번에 재검증하지 않고 직전 감사에서 그대로 옮긴 findings)은 원래 checked_at·근거를 유지하며, 다음 전체 재감사 때 다시 확인한다. 각 감사 job의 scope를 state.json에 기록해 이력을 추적한다.

## plan-vNNN.json (코드 검사 입력)

날짜 미정이면 exploration-vNNN.md에 상대 1일차/2일차 후보와 이동 가설을 저장한다. 임의 날짜로 코드 검증하지 않는다. 조사 중 state.phase는 research이고 결과는 '탐색 초안'이다. 제작·전달 때 produce/delivered로 이동해도 탐색 상태는 유지한다. 날짜 확정 후에만 아래 JSON을 만든다. 가상 날짜는 tests에서만 허용한다.

입장 마감·라스트오더가 있는 item은 latest_entry(시간대 포함 ISO datetime)를 추가한다. 미확인 여부는 unresolved에 기록하고 감사에서 확인한다. 마감이 없는 항목은 생략할 수 있다.

version=2; budget_currency=사용자가 선택한 예산 기준 통화(ISO 4217 세 글자 코드); budget_amount=전체 일행의 여행 전체 상한 또는 null; required_ids=필수 방문 후보 ID 배열; items=실제 시간순 항목 배열; costs=비용 배열; unresolved=미해결 문자열 배열. 단일 전역 시간대를 강제하지 않는다. 출발·도착 현지 시간에 각각 해당 날짜의 UTC 오프셋을 넣는다. 시간대 지역명과 오프셋의 일치 여부는 조사/감사에서 확인하며 코드 검사는 제공된 오프셋으로 실제 시간을 비교한다.

기존 version=1 계획은 보존하고 새 버전으로 명시적으로 이관한다: budget_krw→budget_amount, low_krw/high_krw→low_amount/high_amount, budget_currency와 각 cost.currency에 KRW 설정, 고정 timezone 제거. 기존 타임스탬프 오프셋은 보존한다. 기존 runs 자료가 없는 초기 구성은 이관 작업이 필요 없다.

각 item은 id(일정 항목 고유ID), candidate_id(후보 ID 또는 null), kind(visit/meal/rest/lodging/transport), start/end(시간대 포함 ISO datetime), windows(적용 가능한 [시작,종료] 배열 또는 null), incoming_minutes(직전 항목 이후 필요한 이동·대기·여유 분 또는 null), evidence_status(verified/estimated/unknown/conflicting). 첫 항목 incoming_minutes는 0. 도시 간 교통과 숙박 체크인은 항목으로 표시한다. 숙박 밤 전체를 주간 일정과 중복시키지 않는다. rest/transport의 windows가 null인 것은 정상이다.

각 cost: id, label, currency(예산 기준 통화), low_amount, high_amount(둘 다 전체 일행 총액; 미확인은 둘 다 null). 다른 통화의 금액은 그대로 합산하지 않는다. 환산 시 original_currency, original_low/high, fx_rate(현지 1단위당 기준 통화), fx_source, fx_checked_at을 함께 기록한다. 환율이나 수수료가 불확실하면 범위·가정을 명시하거나 환산 금액을 null로 두고 원금액만 보존한다. 검사기는 통화 불일치를 거절하며 실시간 환율을 조회하지 않는다. items 비용을 별도로 중복 합산하지 않는다. 숙박·이동·식사·입장·필요한 세금과 수수료 누락은 감사에서 확인한다. 후보 price_range에도 currency와 low/high를 명시한다.

검사 출력: errors, warnings, known_cost_subtotal, costs_complete, cost_range. 미확인 비용이 있으면 전체 총액은 null이며 알려진 부분합만 표시한다. costs_complete는 입력된 비용의 완결성으로 필수 항목 누락까지 보증하지 않는다. 오류 시 종료코드 1, 입력 형태 오류 시 2, 시간·비용 검사 통과 시 0. 0은 웹 사실이나 취향 검증 통과를 의미하지 않는다. 실행: python harness/travel-planner/scripts/validate_plan.py <계획 JSON 경로>.

입력은 객체이며 items/costs/required_ids/unresolved는 반드시 배열이다. 각 항목의 필수 필드·문자열 ID·영업 구간 쌍을 구조 검사하고 잘못된 형태는 입력 오류로 거절한다. 금액은 Decimal로 합산·비교하며 출력은 기존 JSON 숫자 형식을 유지한다. 출력 숫자를 다시 합산하지 말고 검사 결과를 사용한다.
