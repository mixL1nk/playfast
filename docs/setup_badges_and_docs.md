# 배지 및 문서 호스팅 설정 가이드

이 가이드는 GitHub에서 커버리지 배지와 GitHub Pages 문서 호스팅을 설정하는 방법을 설명합니다.

## 📊 Coverage Badge 설정

Coverage badge는 GitHub Gist를 사용하여 동적으로 업데이트됩니다.

### 1. GitHub Gist 생성

1. <https://gist.github.com> 으로 이동
1. 새 Gist 생성:
   - **Filename**: `playfast-coverage.json`
   - **Content**: `{"schemaVersion": 1, "label": "coverage", "message": "0%", "color": "red"}`
1. "Create public gist" 클릭
1. **Gist ID 복사** (URL에서 `gist.github.com/username/GIST_ID` 부분)

### 2. GitHub Personal Access Token 생성

1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
1. "Generate new token (classic)" 클릭
1. 설정:
   - **Note**: `Playfast Coverage Badge`
   - **Expiration**: 90 days (또는 원하는 기간)
   - **Scopes**: `gist` 체크
1. "Generate token" 클릭
1. **토큰 복사** (한 번만 표시됨!)

### 3. GitHub Repository Secrets 설정

Repository → Settings → Secrets and variables → Actions → New repository secret

두 개의 secret 추가:

1. **Name**: `GIST_SECRET`

   - **Value**: 위에서 생성한 Personal Access Token

1. **Name**: `GIST_ID`

   - **Value**: Gist ID (예: `a1b2c3d4e5f6g7h8i9j0`)

### 4. README.md 수정

README.md의 Coverage badge URL을 실제 Gist ID로 변경:

```markdown
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/YOUR_USERNAME/YOUR_GIST_ID/raw/playfast-coverage.json)](https://github.com/mixL1nk/playfast/actions/workflows/ci.yml)
```

**변경:**

- `YOUR_USERNAME` → 실제 GitHub username
- `YOUR_GIST_ID` → 위에서 복사한 Gist ID

## 📚 GitHub Pages 문서 호스팅 설정

### 1. GitHub Pages 활성화

1. Repository → Settings → Pages
1. **Source** 섹션:
   - Source: `GitHub Actions` 선택 (Deploy from a branch가 아님!)
1. 저장

### 2. 워크플로우 확인

`.github/workflows/docs.yml` 파일이 이미 생성되어 있습니다. 이 워크플로우는:

- `main` 브랜치에 push할 때마다 자동 실행
- MkDocs로 문서 빌드
- GitHub Pages에 자동 배포

### 3. 첫 배포

```bash
# 변경사항 커밋 및 푸시
git push origin main

# GitHub Actions에서 "Deploy Documentation" 워크플로우 확인
# 완료되면 https://mixL1nk.github.io/playfast/ 에서 문서 확인 가능
```

### 4. 문서 URL 확인

배포 완료 후:

- **문서 URL**: <https://YOUR_USERNAME.github.io/REPO_NAME/>
- 예시: <https://mixL1nk.github.io/playfast/>

## 🧪 테스트

### Coverage Badge 테스트

1. 코드 변경 및 커밋
1. GitHub Actions → CI workflow 확인
1. "Create coverage badge" 단계 성공 확인
1. Gist에서 `playfast-coverage.json` 내용 확인
1. README의 coverage badge가 업데이트되었는지 확인

### Documentation 테스트

1. `docs/` 폴더의 파일 수정
1. 커밋 및 푸시
1. GitHub Actions → "Deploy Documentation" workflow 확인
1. 배포 완료 후 GitHub Pages URL 접속하여 변경사항 확인

## 🎨 Badge 커스터마이징

### 색상 범위 조정

`.github/workflows/ci.yml`의 coverage badge 설정에서:

```yaml
valColorRange: ${{ steps.coverage.outputs.percentage }}
maxColorRange: 100
minColorRange: 0
```

- `maxColorRange`: 100% (초록색)
- `minColorRange`: 0% (빨간색)
- 중간값은 자동으로 노란색/주황색

### 배지 스타일 변경

README.md에서 shields.io 스타일 파라미터 추가:

```markdown
[![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/USERNAME/GIST_ID/raw/playfast-coverage.json&style=flat-square)](...)
```

스타일 옵션:

- `flat` (기본)
- `flat-square`
- `plastic`
- `for-the-badge`

## 🔧 트러블슈팅

### Coverage Badge가 업데이트되지 않음

1. **Secrets 확인**: `GIST_SECRET`과 `GIST_ID`가 올바르게 설정되었는지 확인
1. **Token 권한**: Personal Access Token에 `gist` scope이 있는지 확인
1. **Gist ID**: README의 Gist ID가 정확한지 확인
1. **브랜치**: CI는 `main` 브랜치에서만 badge를 업데이트합니다

### GitHub Pages 배포 실패

1. **Pages 설정**: Settings → Pages에서 Source가 "GitHub Actions"인지 확인
1. **Permissions**: Settings → Actions → General → Workflow permissions에서 "Read and write permissions" 체크
1. **빌드 로그**: Actions 탭에서 에러 메시지 확인
1. **MkDocs 설정**: `mkdocs.yml` 파일이 올바른지 확인

### Badge가 표시되지 않음

1. **캐시**: Ctrl+F5로 브라우저 캐시 새로고침
1. **Gist 공개**: Gist가 public으로 설정되었는지 확인
1. **URL**: README의 badge URL이 정확한지 확인

## 📝 참고 문서

- [GitHub Actions - Pages](https://github.com/actions/deploy-pages)
- [MkDocs](https://www.mkdocs.org/)
- [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
- [Shields.io](https://shields.io/)
- [Dynamic Badges](https://github.com/schneegans/dynamic-badges-action)
