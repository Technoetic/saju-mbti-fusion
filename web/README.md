# 시각화 대시보드

## 실행

```bash
pip install fastapi uvicorn
cd web
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

브라우저에서 `http://localhost:8000` 열기.

## 테스트

```bash
pytest web/test_server.py -v
```
