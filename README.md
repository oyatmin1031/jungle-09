# jungle-09

## 가이드

### 프로젝트 설치

```bash
pip install -r requirements.txt
```

```bash
npm init -y
```

```bash
npm install -D tailwindcss @tailwindcss/cli
```

### 프로젝트 실행

1. 플라스크 앱을 실행합니다.

```bash
flask --app . run
```

2. tailwindcss 빌드

```bash
npx @tailwincss/cli -i ./static/css/input.css -o ./static/css/output.css --watch
```
