# Claude Code 연결부

공통 SKILL.md 실행 전에 이 문서를 읽는다. project_root는 이 파일의 parents[3], core_root는 parents[1]이다. 실제 파일 위치로 절대경로를 해석한다. 프로젝트 전체를 옮겨 사용한다.

- delegate: 현재 Claude Code의 Agent 도구와 프로젝트 .claude/agents 정의를 사용한다. discovery-food/discovery-experience/logistics/discovery-lodging는 travel-researcher에 역할을 명시해 각각 배정한다. auditor는 travel-auditor, artifact-producer는 travel-artifact-producer를 사용한다. 호출 스키마는 현재 노출된 도구를 따른다. 등록되지 않았다면 같은 지침을 지원되는 일반 서브에이전트에 전달한다. Agent 자체가 없으면 sequential 모드다.
- search/read_source: WebSearch/WebFetch 또는 현재 허용된 동등 도구를 사용한다. 검색과 출처 페이지 읽기를 구분한다.
- ask: AskUserQuestion이 있으면 사용하고 없으면 대화로 질문한다.
- read/write/run/check: Read/Write/Edit와 Bash 또는 PowerShell 등 현재 제공 도구를 사용한다. Python 경로를 확인하고 공통 검사기를 실행한다. 권한 우회를 설정하지 않는다.
- render: 사용 가능한 형식별 스킬과 로컬 라이브러리·렌더러를 확인한다. Codex 전용 의존성 조회 도구는 요구하지 않는다. 형식 스킬이 없으면 사용 가능한 도구로 동일 검수 기준을 충족할 수 있는지 판단한다. 불가하면 실패를 보고하고 대체 형식을 질문한다.

runtime={platform:claude, delegation:native/sequential, web:available/unavailable, python:경로 또는 null, render_formats:확인된 형식, max_workers:실제 한도와 3 중 작은 값}를 기록한다. 기본 모델을 상속한다. 도구 허용 목록이 있다고 해서 조사자에게 파일 쓰기를 허용하는 것은 아니다. 제작자 쓰기 경계는 지침 기반이며 운영체제 수준 격리를 제공한다고 주장하지 않는다.

위임 전에 roles/registry.json의 해당 역할 지침 경로를 전달한다. 총괄은 roles/coordinator.md를 읽는다. 역할 설명만 전달해 공통 전문 지침을 생략하지 않는다.
