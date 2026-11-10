# deepdeepbar-be

## 인증 환경변수

운영 프론트엔드와 API가 서로 다른 site에 있으므로 refresh token cookie는 HTTPS
환경에서 아래 설정을 사용한다.

```env
AUTH_REFRESH_COOKIE_SECURE=true
AUTH_REFRESH_COOKIE_SAMESITE=none
AUTH_REFRESH_COOKIE_DOMAIN=
```

로컬 HTTP 환경에서는 두 값을 함께 변경한다.

```env
AUTH_REFRESH_COOKIE_SECURE=false
AUTH_REFRESH_COOKIE_SAMESITE=lax
```

## 최초 관리자 생성

공개 HTTP 관리자 생성 API는 제공하지 않는다. 최초 관리자는 실행 중인 컨테이너
안에서 다음 명령으로 생성한다. 비밀번호는 화면에 표시되지 않는다.

```bash
docker compose exec deepdeepbar-be python -m scripts.create_admin
```

비대화형 환경에서는 `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD`,
`BOOTSTRAP_ADMIN_NAME` 환경변수를 일회성으로 전달한다. 계정 생성 후에는 bootstrap
비밀번호를 서버 환경변수에 남겨두지 않는다.

## 테이블 없는 관리자 입장

테이블 입력 화면의 `WELCOME`를 누르면 관리자 로그인 모달이 열린다. 로그인 후
`POST /table-sessions/admin-enter`가 관리자 권한을 확인하고 테이블 번호가 `null`인
별도 세션을 발급한다. 기존 관리자 로그인만으로는 테이블 입력을 생략하지 않는다.
이 세션의 주문과 Discord 체크인·주문 알림은 테이블 번호 대신 `관리자`로 표시한다.

백엔드 배포는 새 이미지로 `alembic upgrade head`를 먼저 실행하고, 성공한 뒤 API
컨테이너를 교체한다. 백엔드 배포가 성공하면 프론트엔드를 배포한다.
`a1d7e9f3c2b5`가 관리자 입장 스키마를 적용한다. 관리자 세션·주문이 존재하면 해당
마이그레이션의 downgrade는 실패하며, 데이터를 삭제하거나 임의 번호로 바꾸지 않는다.

## Discord 주문 모드 명령어

배포 환경에서 다음 명령을 한 번 실행하면 현재 서버에 `/주문모드` 길드 명령어가
등록된다. 같은 이름의 명령어가 이미 있으면 최신 설정으로 갱신된다.

```bash
docker compose exec -T deepdeepbar-be python -m scripts.register_discord_commands
```

명령어는 `DISCORD_TABLE_CHANNEL_ID`로 지정한 채널에서만 실행할 수 있다. 별도의
Discord 역할 제한은 없으므로 해당 채널을 볼 수 있는 모든 사용자가 아래 두 모드 중
하나를 선택할 수 있다.

- `주문 가능`: 고객이 메뉴를 주문할 수 있다.
- `메뉴판 전용`: 메뉴 조회만 가능하고 주문 생성은 차단된다.

다른 채널이나 DM에서 들어온 요청은 백엔드가 거부한다. 등록에는 기존
`DISCORD_APPLICATION_ID`, `DISCORD_BOT_TOKEN`, `DISCORD_GUILD_ID` 환경변수를
사용하므로 추가 환경변수는 필요하지 않다.

[혼술바 딥딥(deepdeep)](https://deepdeepbar.vercel.app/) 메뉴·레시피·관리 기능을 제공하는 백엔드 API 서버입니다.

Python + FastAPI 기반으로 구성되어 있습니다.

## API Docs

- Production: `https://deepdeep-api.gomoving.shop/docs`
- Local: `http://localhost:8000/docs`

## Tech Stack

- Python
- FastAPI
- SQLAlchemy 2.x (AsyncSession)
- PostgreSQL
- Alembic

## Local Development

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check: `GET /health`

---

© 2026 MinJun Shin. All rights reserved.


## 직원 호출

메뉴판의 직원 호출은 주문 모드와 독립적으로 동작한다. 활성 테이블 세션 토큰이
필요하며 관리자 입장 세션은 `테이블 관리자`로 표시한다. 관리자 페이지에서 호출
항목의 문구, 표시 순서, 사용 여부를 편집하고 삭제할 수 있다. 기존 호출에는 당시
문구를 보존한다. 같은 테이블에서 처리 전인 동일 항목은 중복 생성하지 않으며,
Discord 전송 실패 시 같은 요청을 재시도한다.

알림은 기존 `DISCORD_TABLE_CHANNEL_ID` 채널을 사용한다. Discord의 `처리 완료`
버튼은 기존 서명 검증 경로와 서버·채널·메시지 검증을 통과해야 반영된다.
배포 전에 `b2e8f0a4d3c6` 마이그레이션을 적용해야 한다. 최초 항목 세 개는
마이그레이션에서 한 번만 등록하므로 관리자의 편집·삭제 내용이 재시작 때 복원되지 않는다.
