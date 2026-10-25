# World Civilization Simulation

Python과 Pygame으로 만든 랜덤 세계·문명 시뮬레이션입니다.

OpenSimplex Noise를 이용해 지형을 생성하고, 지형·기후·자원·자연재해·전염병 등의 환경 조건이 문명의 성장과 쇠퇴에 어떤 영향을 주는지 시뮬레이션합니다.

## 주요 기능

- OpenSimplex Noise 기반 랜덤 지형 생성
- 바다, 강, 평야, 숲, 산, 사막 생성
- 온도·습도·건조도 기반 기후 모델
- 식량, 물, 목재, 철, 광물, 석유 자원 분포
- 홍수, 가뭄, 화산, 지진, 폭풍, 산불 자연재해
- 국가 생성 및 영토 확장
- 도시 성장 및 수도 관리
- 무역, 외교, 전쟁
- 전염병과 의료 수준
- 인구·부·식량 변화
- 국가 붕괴, 분열, 멸망
- 국가 순위 및 자원 오버레이

## 실행 환경

- Python 3
- Pygame
- OpenSimplex

## 설치

```bash
pip install -r requirements.txt
```

## 실행

```bash
python world_civilization_simulation.py
```

Windows에서 `python` 명령이 연결되어 있지 않다면 다음과 같이 실행할 수 있습니다.

```bash
py world_civilization_simulation.py
```

## 프로젝트 구조

```text
World-Civilization-Simulation/
├─ world_civilization_simulation.py
├─ requirements.txt
├─ README.md
└─ .gitignore
```

## 사용 라이브러리

프로젝트 소스에서 직접 사용하는 외부 라이브러리는 다음 두 가지입니다.

- `pygame`
- `opensimplex`

`random`, `math`, `heapq`는 Python 표준 라이브러리입니다.
