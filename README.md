# Ontology Evaluation System

GraphRAG/온톨로지 품질 평가 시스템 — OOPS! 기반 구조 검사 + PDF 커버리지 분석 (예정)

## 지원 포맷

| 확장자 | 포맷 |
|--------|------|
| `.owl`, `.rdf`, `.xml` | RDF/XML |
| `.ttl` | Turtle |
| `.n3` | Notation3 |
| `.nt` | N-Triples |
| `.jsonld`, `.json` | JSON-LD |

## 실행 방법

### 1. OOPS! 소스 준비

```bash
git clone https://github.com/oeg-upm/OOPS.git oops-src
```

### 2. Docker Compose 실행

```bash
docker compose up --build -d
```

### 3. 접속

- Flask UI: `http://<서버IP>:20105`
- OOPS! 직접: `http://<서버IP>:20104/oops`

## 구조

```
ontology_evaluation_system/
├── app/
│   ├── main.py              # Flask 라우터
│   ├── utils/
│   │   └── converter.py     # 다양한 포맷 → RDF/XML 변환 (rdflib)
│   └── templates/
│       └── index.html       # 웹 UI
├── oops-src/                # OOPS! 소스 (git clone으로 추가)
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## 향후 계획

- [ ] PDF 원본 vs 온톨로지 커버리지 분석 (LLM 기반)
- [ ] Python dict 형태 온톨로지 변환 지원 확대
- [ ] 평가 결과 저장 및 히스토리 관리
