# deepdeepbar-be

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
