# Railway 연결 & 작업 환경 셋업 가이드

이 프로젝트(**saju-mbti-fusion**)에 다른 컴퓨터에서 이어 작업할 때 따라야 할 절차. 한 번 셋업하면 `/railway:resume` 슬래시 커맨드 한 줄로 끝난다.

---

## TL;DR — 다른 컴퓨터에서 한 줄로 이어가기

```
/railway:resume https://saju-mbti-fusion-production.up.railway.app/
```

Claude Code가 위 커맨드를 받으면 자동으로:
1. Railway에 link
2. 활성 배포에서 소스 + 데이터 추출
3. `Dockerfile`, `.env`, `.gitignore`, `.dockerignore` 생성
4. Python venv + `pip install`
5. `from web.server import app` 검증

→ 약 2~3분이면 작업 가능 상태.

---

## 사전 준비 (다른 컴퓨터에서 최초 1회)

### 1. Railway CLI 설치
```powershell
# Windows (winget)
winget install Railway.Railway
# 또는 npm
npm i -g @railway/cli
```

### 2. Railway API 토큰 발급
https://railway.app/account/tokens 에서 새 토큰 만들고 복사.

### 3. 슬래시 커맨드 파일 복사
다음 파일을 그 컴퓨터의 `~/.claude/commands/railway/resume.md` 위치에 저장.

> **원본 위치:** 이 컴퓨터(작업 PC)의 [C:\Users\Admin\.claude\commands\railway\resume.md](file:///C:/Users/Admin/.claude/commands/railway/resume.md)

복사 방법 (Windows 기준):
```powershell
# 다른 컴퓨터에서 폴더 생성
mkdir "$env:USERPROFILE\.claude\commands\railway"
# 그리고 resume.md 파일을 그 안에 복사 (USB/클라우드/Github 어느 경로든)
```

### 4. Python 설치 (3.12 또는 3.13 권장)
이 프로젝트의 활성 배포는 Python **3.12.13** 기준. 정확히 같은 버전이 없으면 **3.13**으로도 호환됨 (실제 검증 완료).

---

## 이번 케이스에서 성공한 정확한 절차 (참고용)

### 인증
```bash
export RAILWAY_API_TOKEN="<토큰>"
railway whoami    # → Logged in as <email>
```

### 프로젝트 검색 (워크스페이스 경로로!)
> ⚠️ `me { projects }`는 빈 배열을 반환했음. 반드시 워크스페이스 경유.

```bash
# 워크스페이스 조회
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ me { workspaces { id name } } }"}'

# 프로젝트 조회
curl -s -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "{ workspace(workspaceId: \"ba72f80a-7517-47eb-b1c3-30042e58a64b\") { projects { edges { node { id name } } } } }"}'
```

### 비대화형 link
```bash
railway link --project 585d6fb2-3438-48eb-9010-5b291a7f1fa1 \
             --workspace ba72f80a-7517-47eb-b1c3-30042e58a64b
railway service saju-mbti-fusion
railway status
```

### 컨테이너에서 코드 추출 (핵심 트릭 2개)
```bash
# 1) MSYS_NO_PATHCONV=1 — Git Bash가 /app을 Windows 경로로 바꿔버리는 것 방지
# 2) base64 -w0 — railway ssh의 PTY가 binary stdout을 차단하므로 base64로 통과

mkdir -p /c/temp/railway_extract

MSYS_NO_PATHCONV=1 railway ssh -- 'tar czf - -C /app . | base64 -w0' \
  > /c/temp/railway_extract/app.b64
base64 -d /c/temp/railway_extract/app.b64 > /c/temp/railway_extract/app.tar.gz

MSYS_NO_PATHCONV=1 railway ssh -- 'tar czf - -C /data . | base64 -w0' \
  > /c/temp/railway_extract/data.b64
base64 -d /c/temp/railway_extract/data.b64 > /c/temp/railway_extract/data.tar.gz
```

### 한글 디렉토리에 풀기
> ⚠️ Windows `tar.exe`도, `powershell -Command`도 cp949 환경에서 한글 인수 깨뜨림. bash에서 cd 후 tar.

```bash
cd "/c/Users/Admin/Desktop/사주 프로그램"
tar -xzf /c/temp/railway_extract/app.tar.gz
mkdir -p .data
tar -xzf /c/temp/railway_extract/data.tar.gz -C .data/
```

### 시작 명령 + 환경변수 추출
```bash
MSYS_NO_PATHCONV=1 railway ssh -- 'cat /proc/1/cmdline | tr "\0" " "; echo'
# → sh -c python -m uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8000}

railway variables --json   # ⚠️ 시크릿 포함 — 화면에 띄우지 말고 바로 .env로
```

### venv + 의존성 + 검증
```bash
py -3.13 -m venv .venv
.venv/Scripts/python.exe -m pip install --upgrade pip
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -c "from web.server import app; print('OK', type(app).__name__)"
# → OK FastAPI
```

---

## 이 프로젝트의 핵심 정보 (다른 컴 셋업 시 검증용)

| 항목 | 값 |
|---|---|
| Railway 프로젝트명 | `saju-mbti-fusion` |
| 프로젝트 ID | `585d6fb2-3438-48eb-9010-5b291a7f1fa1` |
| 워크스페이스 | technoetic's Projects (`ba72f80a-7517-47eb-b1c3-30042e58a64b`) |
| 환경 | production (`36ecbd1d-b0f0-4683-a4b5-d125ab37cb94`) |
| 서비스 | saju-mbti-fusion (`00fbc238-ae49-4db6-8548-b4bf3478a7c8`) |
| 공개 URL | https://saju-mbti-fusion-production.up.railway.app/ |
| Python 버전 | 3.12.13 (3.13 호환 검증됨) |
| 시작 명령 | `python -m uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8000}` |
| DB 경로 (운영) | `/data/app.db` (env `DREAM_APP_DB_PATH`) |
| DB 경로 (로컬) | `./.data/app.db` |
| 볼륨 | `/data` (50GB / 1.06GB 사용) |

### Dockerfile 구조 (활성 배포 e6d19eb1 기준)
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY engine ./engine
COPY web ./web
COPY front ./front
CMD ["sh", "-c", "python -m uvicorn web.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### 사용자 환경변수 (8개)
- `BIZROUTER_API_KEY` (시크릿)
- `BIZROUTER_BASE_URL` = `https://api.bizrouter.ai/v1`
- `BIZROUTER_IMAGE_MODEL` = `google/gemini-2.5-flash-image`
- `BIZROUTER_MODEL` = `google/gemini-2.5-flash-lite`
- `MINIMAX_API_KEY` (시크릿)
- `MINIMAX_MUSIC_MODEL` = `music-2.6-free`
- `DREAM_APP_DB_PATH` = `/data/app.db` (운영) / `./.data/app.db` (로컬)

---

## 트러블슈팅 (실제 마주친 문제 모음)

| 증상 | 원인 | 해결 |
|---|---|---|
| `Unauthorized. Please login` | 토큰 미설정 | `export RAILWAY_API_TOKEN="..."` |
| `me { projects }` 빈 배열 | 워크스페이스 소속 프로젝트는 me로 안 보임 | `workspace(workspaceId: ...)` 경로 사용 |
| `railway link`가 인터랙티브로 멈춤 | 옵션 누락 | `--project <PID> --workspace <WID>` 명시 |
| `ls: cannot access 'C:/Program'` | Git Bash가 `/app`을 Windows 경로로 변환 | `MSYS_NO_PATHCONV=1` 환경변수 |
| `tar: Refusing to write archive contents to terminal` | railway ssh가 PTY 할당, tar가 stdout=tty 거부 | `tar czf - ... \| base64 -w0` |
| `tar.exe: could not chdir to ...` | Windows tar가 한글 인수 못 받음 | bash에서 `cd "한글경로" && tar -xzf ...` |
| `tar (child): Cannot connect to C:` | PowerShell 안 `tar` 호출이 git bash로 위임됨 | `cmd.exe //c "C:\Windows\System32\tar.exe ..."` 또는 bash 사용 |
| `py -3.12` 없음 | Python 3.12 미설치 | `py -3.13`로 폴백 (호환됨) |

---

## 일상 작업 명령

```powershell
# 로컬 실행
cd "c:\Users\Admin\Desktop\사주 프로그램"
.\.venv\Scripts\python.exe -m uvicorn web.server:app --reload --port 8000
# → http://localhost:8000

# Railway 재배포
$env:RAILWAY_API_TOKEN="<토큰>"
railway up --detach
railway logs --tail 30

# 도메인 확인
railway domain
```

---

## 슬래시 커맨드 원본 (`~/.claude/commands/railway/resume.md`)

다른 컴퓨터에서 같은 동작을 쓰려면 위 경로의 파일을 복사. **현재 PC**에서는 이미 글로벌에 등록되어 있음:

`C:\Users\Admin\.claude\commands\railway\resume.md`

내용은 [그 파일](file:///C:/Users/Admin/.claude/commands/railway/resume.md)을 직접 열어서 복사.
