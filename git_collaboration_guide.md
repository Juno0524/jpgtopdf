# Git을 통한 협업 및 원격 작업 가이드

집이나 다른 PC에서 작업을 이어서 하시려면 Git과 GitHub(또는 다른 Git 원격 저장소)을 사용하는 것이 가장 좋습니다.

## 1. 초기 연동 방법 (현재 PC)

현재 폴더([JPGTODPF](file:///c:/Users/user/Downloads/Coding/JPGTODPF))에서 다음 명령어를 실행하여 저장소를 초기화하고 파일을 업로드합니다.

```powershell
# Git 초기화
git init

# 파일 상태 확인 및 추가
git add .

# 첫 커밋
git commit -m "feat: TDS 스타일 적용 및 v29 빌드 완료"

# GitHub 저장소 연결 (GitHub에서 새 Repo를 만든 후 URL을 넣으세요)
# git remote add origin https://github.com/사용자계정/JPGTODPF.git
# git push -u origin main
```

## 2. 다른 PC(집)에서 가져오기

집에 있는 PC에서 작업을 시작할 때 다음 과정을 따르세요.

```powershell
# 프로젝트 복제
git clone https://github.com/사용자계정/JPGTODPF.git
cd JPGTODPF

# 가상 환경 설정 및 라이브러리 설치
python -m venv .venv
.\.venv\Scripts\activate
pip install customtkinter pytesseract Pillow reportlab tkcalendar tkinterdnd2
```

## 3. 주의사항

- **.gitignore**: 이미 생성해 드린 `.gitignore` 파일 덕분에 불필요한 빌드 파일(`dist`, `build`)과 가상 환경(`.venv`)은 Git에 올라가지 않습니다.
- **Tesseract OCR**: 집 PC에도 [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)이 설치되어 있어야 자동 인식 기능이 작동합니다.
- **라이브러리**: `customtkinter`를 포함한 필수 라이브러리를 꼭 설치해 주세요.
