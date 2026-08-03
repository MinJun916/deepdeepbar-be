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
