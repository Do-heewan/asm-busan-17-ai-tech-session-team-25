# ✈️ Travel Mate Agent: 나만의 여행 메이트 (25조 프로젝트)

## 📖 프로젝트 개요
**"나만의 여행 메이트와 대화하며 호감도를 쌓고, 함께 항공권을 검색하며 여행 일정을 완성해가는 인터랙티브 비주얼 노벨 게임"** 

기존의 일방적 정보 제공에 머무르는 여행 추천 서비스에서 벗어나, 사용자가 AI 캐릭터와 자연스럽게 상호작용하며 함께 여행을 계획하는 경험을 제공합니다. 본 프로젝트는 LLM, 외부 API 연동(항공권 검색), 분기 로직, 상태 관리 등 **Agentic Workflow의 핵심 요소가 모두 통합된 시스템**을 구축하는 것을 목표로 합니다.

## ✨ 핵심 기능
- **캐릭터 대화 시스템**: AI 캐릭터의 일관된 페르소나 유지 및 단기/장기 메모리 관리 
- **의도 및 감정 분류기 (Intent Classifier)**: 유저의 발화를 구조화된 형태로 분석하여 '대화 / 도구 호출 필요 / 선택 응답'으로 자동 분기
- **호감도 엔진 (Affinity Engine)**: 대화의 감정과 선택 결과를 점수화하여 단계별 분기 조건을 평가 
- **여행 도구 호출 (Tool Router)**: 대화 맥락에 맞춰 실제 항공권 조회(Amadeus API) 등 외부 도구 자동 호출 
- **다중 분기 스토리 시스템**: 도시별, 호감도별 이벤트 발생 및 누적 상태에 따른 멀티 엔딩 제공 

---

## ⚠️ 팀원 필수 숙지 사항 (Git 전략 및 개발 규칙)
> **안정적인 협업과 Agentic Workflow 모듈 간의 충돌 방지를 위해 아래 규칙을 반드시 엄수해 주세요.**

### 1. 브랜치 명명 규칙
브랜치 이름은 반드시 **`[작업파일경로]-[작업명]`** 형태로 생성합니다. 본인이 맡은 파일의 경로를 명시하여 작업 영역을 명확히 분리해야 합니다.
- **예시 (프론트엔드)**: `[frontend/src/components/chat/ChatWindow]-[ui-update]`
- **예시 (백엔드)**: `[backend/app/agents/intent_classifier]-[add-structured-output]`

### 2. 절대 금지 사항 (Do Not Direct Push)
- **`main` 브랜치에 직접 커밋 및 푸시하는 것은 절대 금지**됩니다.
- 모든 기능 개발과 수정은 반드시 본인의 작업 브랜치에서 진행해야 합니다.

### 3. PR(Pull Request) 및 Merge 규칙
- 작업이 완료되면 반드시 `main` 브랜치를 향해 **PR(Pull Request)**을 생성해야 합니다.
- 코드 리뷰 및 테스트 완료 후, **Merge는 오직 '팀장'만이 수행**할 수 있습니다.
- PR 제목은 직관적으로 작성하고, 본문에 어떤 파일을 수정/추가했는지 명시해 주세요.

---

## 📂 프로젝트 구조 (파일별 업무 분담도)
본 프로젝트는 로컬 실행에 최적화된 일체형(Monorepo) 구조로 설계되었습니다. 프론트엔드 빌드 결과물을 백엔드(FastAPI)가 정적으로 서빙하여 동작합니다.

[Status] 진행완료 : 🟢  |  진행중/보류 : 🟡  |  진행전 : 🔴

```text
travel-mate-agent/
├── README.md                 # [재혁 | 🟢] 프로젝트 실행 방법 및 환경 변수 세팅 안내 가이드                          
├── run_local.sh              # [재혁 | 🟡] (Mac/Linux) 프론트 빌드 -> 백엔드 static 복사 -> FastAPI 실행 스크립트
├── run_local.bat             # [재혁 | 🟡] (Windows) 위와 동일한 배치 스크립트
├── .env                      # [재혁 | 🟢] 환경변수(Upstage API, Amadeus API 등) 템플릿
├── .gitignore                # [재혁 | 🟢] 가상환경, 빌드 결과물, 로컬 세션 데이터 등 제외
│
├── frontend/                 # [React + TypeScript + Tailwind] 웹 UI 및 전역 상태 관리 
│   ├── package.json              # [대희 | 🔴]    
│   ├── tsconfig.json             # [대희 | 🔴] 
│   ├── tailwind.config.js        # [대희 | 🔴] 
│   ├── public/assets/            # [나슬 | 🔴] 일러스트 자산 (캐릭터 표정 4종, 3개 도시 배경 등)      # 나슬님 죄송.. 사다리타기했는데 나오셨어요..   
│   └── src/
│       ├── main.tsx              # [대희 | 🔴] 
│       ├── App.tsx               # [대희 | 🔴] 전체 화면 레이아웃 및 뷰 라우팅
│       ├── api/client.ts         # [대희 | 🔴] Axios/Fetch 설정. 백엔드(FastAPI) API 호출 로직
│       ├── store/useGameStore.ts # [대희 | 🔴] Zustand 전역 상태 관리 (대화 기록, 호감도, 현재 챕터 등)
│       ├── types/index.ts        # [대희 | 🔴] 백엔드 TurnResult 스키마와 동기화된 프론트엔드 타입 정의
│       └── components/           # UI 컴포넌트 분할
│           ├── chat/ChatWindow.tsx       # [대희 | 🔴] 대화 스크롤 영역
│           ├── chat/MessageBubble.tsx    # [대희 | 🔴] 유저/캐릭터 말풍선
│           ├── chat/ChatInput.tsx        # [대희 | 🔴] 텍스트 입력창 및 버튼
│           ├── game/AffinityGauge.tsx    # [나슬 | 🔴] 상단 호감도 바
│           ├── game/CharacterSprite.tsx  # [나슬 | 🔴] 상태(emotion_code)에 따른 캐릭터 표정 렌더링
│           ├── game/SceneBackground.tsx  # [나슬 | 🔴] 챕터에 따른 배경 이미지 렌더링
│           └── game/SelectionMenu.tsx    # [나슬 | 🔴] 이벤트 분기용 선택지 버튼
│
└── backend/                  # [Python FastAPI] LLM 오케스트레이션 및 상태/메모리 관리
    ├── requirements.txt          # [재혁 | 🟢] 
    ├── static/                   # [⚠️자동작업] 수동 작업 금지 (프론트 빌드 결과물이 모이는 곳)
    └── app/
        ├── main.py               # [희완 | 🔴] FastAPI 앱 선언 및 정적 파일(static) 서빙(Mount) 처리
        ├── core/config.py        # [희완 | 🔴] .env 환경 변수 관리 (Pydantic Settings)
        ├── api/routes.py         # [희완 | 🔴] API 라우터 (대화 턴 진행, 상태 초기화 등)
        ├── schemas/              # Pydantic 데이터 모델 규격
        │   ├── request.py            # [재혁 | 🟢] client -> server 유저 입력 규격
        │   └── response.py           # [재혁 | 🟢] server -> client 서버 응답 규격 (TurnResult 스키마 등)
        ├── agents/               # 🧠 Agentic Workflow 핵심 로직
        │   ├── intent_classifier.py  # [혜성 | 🔴] 유저 발화 의도 분류 (대화/도구/선택)
        │   ├── story_engine.py       # [희완 | 🔴] 챕터 전환 로직, 이벤트 트리거 평가, 엔딩 결정
        │   ├── tool_router.py        # [혜성 | 🔴] 의도에 따른 도구(API) 선택 및 실행
        │   └── dialogue_generator.py # [희완 | 🔴] 컨텍스트 종합 후 최종 대사/표정 생성 (Solar API)
        ├── services/             # 🛠️ 외부 API 연동 및 비즈니스 로직
        │   ├── llm_client.py         # [희완 | 🔴] Upstage Solar API 통신 공통 모듈
        │   ├── amadeus_client.py     # [혜성 | 🔴] Amadeus 항공권 검색 (캐싱 및 Fallback 포함)
        │   └── affinity_calculator.py# [희완 | 🔴] 발화 감정 기반 호감도 증감 연산
        ├── prompts/system_prompts.py # [희완 | 🔴] 페르소나 설정, 말투, 금지 규칙, Few-shot 예시 문자열
        └── memory/               # 💾 로컬 세션 데이터 저장소
            ├── store.py              # [희완 | 🔴] 단기/장기 메모리 JSON 파일 읽기/쓰기 로직
            └── data/                 # [희완 | 🔴] 세션별 JSON 파일 저장 디렉토리 (Git 무시됨)