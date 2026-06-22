# CCTV Intrusion Detection System

YOLO 기반 CCTV 침입 감지 시스템입니다.
사용자가 영상에서 감시 구역(ROI, Region of Interest)을 직접 지정하면, 해당 영역 안으로 사람이 들어왔을 때 침입으로 판단하고 스냅샷 저장, 웹 대시보드 기록, Discord 알림을 수행합니다.

## 프로젝트 개요

이 프로젝트는 CCTV 영상에서 사람 객체를 탐지하고, 사용자가 지정한 감시 구역에 사람이 진입했는지를 판단하는 컴퓨터 비전 기반 보안 시스템입니다.

단순히 객체 탐지만 수행하는 것이 아니라, 탐지 결과를 실제 서비스 흐름처럼 활용하기 위해 다음 기능을 함께 구현했습니다.

* YOLO 기반 사람 탐지
* ByteTrack 기반 객체 추적 ID 부여
* 마우스로 감시 구역 직접 지정
* 침입 발생 시 스냅샷 저장
* 침입 기록을 JSON 파일에 저장
* Flask 기반 웹 대시보드 제공
* Discord Webhook을 통한 실시간 알림

## 주요 기능

### 1. 사람 탐지

YOLO 모델을 사용해 영상 프레임에서 사람 객체를 탐지합니다.
현재는 COCO 데이터셋 기준 `person` 클래스만 탐지하도록 설정했습니다.

### 2. 침입 영역 지정

프로그램 실행 시 첫 프레임이 표시되며, 사용자는 마우스로 감시 구역을 직접 지정할 수 있습니다.

* 좌클릭: 감시 구역 꼭짓점 추가
* 우클릭: 감시 구역 선택 완료

지정된 영역은 `zone.json`에 저장됩니다.

### 3. 침입 판정

탐지된 사람의 바운딩 박스 중심점이 사용자가 지정한 다각형 ROI 내부에 들어오면 침입으로 판단합니다.

### 4. 침입 스냅샷 저장

침입이 감지되면 해당 프레임을 이미지로 저장합니다.

저장 경로:

```text
snapshots/
```

### 5. 웹 대시보드

Flask를 사용해 침입 기록을 웹에서 확인할 수 있습니다.

대시보드에서는 다음 정보를 확인할 수 있습니다.

* 총 침입 기록 수
* 침입 감지 시간
* 침입 스냅샷
* 이미지 저장 위치

기본 접속 주소:

```text
http://127.0.0.1:5000
```

WSL 환경에서는 터미널에 표시되는 IP 주소로 접속해야 할 수도 있습니다.

예:

```text
http://172.xx.xx.xx:5000
```

### 6. Discord 알림

Discord Webhook을 설정하면 침입이 발생했을 때 Discord 채널로 알림과 스냅샷 이미지가 전송됩니다.

## 기술 스택

* Python
* PyTorch
* Ultralytics YOLO
* OpenCV
* Flask
* NumPy
* Requests
* Discord Webhook
* ByteTrack

## 프로젝트 구조

```text
cctv_project/
│
├── intrusion.py
├── requirements.txt
├── .env.example
├── .gitignore
│
├── templates/
│   └── index.html
│
├── snapshots/
│   └── intrusion_xxx.jpg
│
├── alerts.json
├── zone.json
├── test.mp4
└── yolo11n.pt
```

GitHub에는 실행 중 생성되는 파일과 민감 정보는 올리지 않습니다.

업로드 제외 대상:

```text
.env
venv/
snapshots/
alerts.json
zone.json
test.mp4
yolo11n.pt
runs/
```

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/cocopo11/cctv-intrusion-detection.git
cd cctv-intrusion-detection
```

### 2. 가상환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate
```

Windows PowerShell에서는 다음 명령을 사용합니다.

```powershell
.\venv\Scripts\activate
```

### 3. 패키지 설치

```bash
pip install -r requirements.txt
```

PyTorch는 사용자의 CUDA 환경에 맞게 별도로 설치하는 것을 권장합니다.

## 환경 변수 설정

Discord 알림을 사용하려면 `.env` 파일을 생성합니다.

```bash
cp .env.example .env
```

`.env` 파일에 Discord Webhook URL을 입력합니다.

```env
DISCORD_WEBHOOK=https://discord.com/api/webhooks/your_webhook_url
```

주의: `.env` 파일은 GitHub에 올리면 안 됩니다.

## 실행 방법

프로젝트 폴더에 테스트 영상 파일을 준비합니다.

기본 영상 파일명:

```text
test.mp4
```

프로그램 실행:

```bash
python intrusion.py
```

실행 후 ROI 선택 창이 나타납니다.

1. 좌클릭으로 감시 구역 꼭짓점 지정
2. 우클릭으로 영역 선택 완료
3. 침입 감지 시작
4. 웹 브라우저에서 대시보드 확인

```text
http://127.0.0.1:5000
```

## 실행 결과

침입이 감지되면 다음과 같은 결과가 생성됩니다.

```text
[ALERT] intrusion detected id=1.0
[DISCORD] alert sent
```

웹 대시보드에서는 침입 시간과 스냅샷 이미지를 확인할 수 있습니다.

## 현재 한계

현재 프로젝트는 포트폴리오용 MVP 단계입니다. 다음과 같은 한계가 있습니다.

* 사전학습된 YOLO 모델을 사용하며, 자체 CCTV 데이터셋으로 재학습하지 않았습니다.
* 테스트 영상 기반으로 동작하며, 실제 RTSP CCTV 연결은 추가 구현이 필요합니다.
* 같은 사람이 여러 번 감지될 경우 중복 알림이 발생할 수 있습니다.
* ROI는 실행 시 수동으로 지정하는 방식입니다.
* 침입 기록은 데이터베이스가 아닌 JSON 파일에 저장됩니다.

## 개선 계획

향후 다음 기능을 추가할 수 있습니다.

* RTSP CCTV 스트림 연결
* SQLite 또는 PostgreSQL 기반 침입 로그 저장
* 웹 대시보드에서 ROI 직접 설정
* 중복 알림 방지 쿨다운 로직
* 여러 카메라 동시 처리
* 침입 통계 시각화
* 자체 CCTV 데이터셋 기반 YOLO 파인튜닝
* Docker 기반 배포 환경 구성

## 프로젝트 의의

이 프로젝트는 컴퓨터 비전 모델을 단순히 실행하는 것에서 끝나지 않고, 실제 보안 시스템에 가까운 흐름으로 연결한 예제입니다.

객체 탐지 모델의 결과를 바탕으로 침입 여부를 판단하고, 기록 저장, 웹 대시보드, 실시간 알림까지 구현하여 AI 모델을 서비스 형태로 활용하는 과정을 경험하는 것을 목표로 했습니다.
