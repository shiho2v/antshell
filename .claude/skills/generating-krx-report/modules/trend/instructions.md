# trend — 주가 추세와 CANSLIM 모듈 지침

> 이 파일은 **trend 모듈이 실행될 때만** 읽는다. 미리 읽지 않는다.

## 1. 목적

주가의 추세·수급·시장 환경을 CANSLIM 7항목(C·A·N·S·L·I·M)으로 점검한다.

**중요:** 이 스킬에서 CANSLIM 은 최상위 분석 프레임이 아니라 **trend 모듈의 하위 루브릭**이다.
기업의 사업·품질·성장·해자·밸류에이션·위험은 각자의 모듈이 담당한다.
trend 는 "지금 이 주식이 어떤 추세와 수급 위에 있는가"만 다룬다.

7개 criterion(TRD-C/A/N/S/L/I/M)은 전부 `type: auto` 다.
→ **점수는 score_modules.py 가 계산한다. Claude 는 level 을 제출하지 않고 해석 서술만 쓴다.**

## 2. 읽을 파일

| 파일 | 용도 |
|------|------|
| `data/normalized/{ticker}_metrics.json` | 7개 지표 값 + na_reason |
| `data/evidence/{ticker}_evidence.json` | `packs.trend` (+ C·A 재사용을 위한 growth evidence id) |
| `data/module-results/{ticker}_growth.json` | **C·A 는 여기서 재참조한다 (재계산 금지)** |
| `data/raw/{ticker}_dart_events.json` | N 의 "신제품·신경영" 정성 서술 근거 |
| `modules/trend/canslim-rubric.md` | 7항목 등급 정의 |
| `modules/trend/market-regime.md` | M(시장 방향) 해석 한계 |
| `data/{ticker}_analysis_contract.json` | credentials_available, prohibited_inferences |

사용 지표 키: `eps_yoy_q`(C), `op_cagr_3y`(A), `pct_from_52w_high`(N),
`volume_ratio_vs_60d`(S), `rs_vs_index_6m_pp`(L), `inst_foreign_net_60d_to_mktcap`(I),
`index_vs_ma200_pct`(M)

## 3. 분석 절차

1. **C·A 먼저 확인 — 재계산하지 않는다.**
   - TRD-C(`eps_yoy_q`)는 growth 모듈 **GRO-03** 과 동일 지표다.
   - TRD-A(`op_cagr_3y`)는 growth 모듈 **GRO-05** 와 동일 지표다.
   - growth 결과의 **evidence_ids 를 그대로 재참조**한다. 값이 growth 와 달라지면 오류다.
   - 주의: 밴드는 growth 와 다르다(C: 15/25 경계, A: 10/20 경계). 밴드는 Python 이 적용한다.
2. **N**: `pct_from_52w_high` 로 신고가 근접도를 확인한다. 0에 가까울수록 신고가 근접.
   정성적 "신제품·신경영" 근거는 `dart_events.json` 의 공시(신규수주/설비투자/지배구조 등)에서
   **보조 서술로만** 인용한다 — **점수는 신고가 근접도 지표가 결정한다.**
3. **S**: `volume_ratio_vs_60d` (최근 거래량 / 60일 평균). 거래량 급증이 상승과 함께인지
   하락과 함께인지를 `pct_from_52w_high` 와 함께 서술한다. 거래량 자체는 방향을 말하지 않는다.
4. **L / I / M**: `credentials_available` 에 **KRX_ID, KRX_PW 가 없으면 세 항목 모두 N/A** 다.
   - N/A 사유를 명시하고 **0점으로 처리하지 않는다.**
   - 이때 CANSLIM 7항목 중 4개(C·A·N·S)만 채점되므로 `evidence_coverage` 가 낮아진다.
     이 사실을 verdict 와 unknowns 에 반드시 적는다.
5. **M** 해석은 `market-regime.md` 를 따른다. 지수 데이터가 없으면 시장 국면은 **미확인**이다.
   뉴스·기억으로 "현재 강세장/약세장"을 서술하지 않는다.
6. 마지막으로 7항목을 종합해 "추세가 실적 개선과 같은 방향인지, 아니면 실적 없이
   가격만 움직이는지"를 서술한다. 상충되는 신호는 `counter_evidence` 에 남긴다.

## 4. 판단 규칙

- **N/A ≠ 0점.** L·I·M 은 자격증명 없으면 N/A. `na_reason: "자격증명 없음 (KRX_ID, KRX_PW)"`.
- **C·A 재계산 금지.** growth 모듈 값과 evidence 를 재사용한다. 두 모듈의 수치가 어긋나면
  보고서 전체의 재현 검증(Gate 3)이 실패한다.
- 가격 데이터는 pykrx(**비공식 래퍼**) 경유, 기본 OHLCV 는 Naver Finance 를 거친다 — 한계 명시.
- 추세는 **미래를 말하지 않는다.** "돌파가 임박했다", "곧 신고가를 낼 것" 같은 예측 금지.
- 차트 패턴(컵앤핸들, 손잡이 등)은 **데이터로 검증되지 않았다.** 만들어 쓰지 않는다.
- 뉴스로 N(신제품)을 만들지 않는다. 공시(rcept_no)가 있는 사건만 인용한다.
- 컨센서스·목표주가·시장점유율: 존재하지 않는 데이터다. 생성 금지.

## 5. 출력

`data/module-results/{ticker}_trend_judgment.json`

```json
{
  "module": "trend",
  "ticker": "009150",
  "criteria": [],
  "strengths":  [{"point": "…", "evidence_ids": ["T-PCTFROM52W-001"]}],
  "weaknesses": [{"point": "…", "evidence_ids": ["G-EPSYOYQ-001"]}],
  "counter_evidence": [{"point": "거래량은 늘었으나 주가는 52주 고점 대비 -20%", "evidence_ids": ["…","…"]}],
  "unknowns": ["L·I·M — KRX 자격증명 없음으로 미채점 (시장 국면 미확인)"],
  "invalidating_conditions": ["…"],
  "verdict": "500단어 이내"
}
```

- **auto 모듈이므로 `criteria` 는 비운다. level 제출 금지.**
- strengths/weaknesses 각 5개 이내, 항목마다 evidence_ids 1개 이상.
- verdict 500단어 이내, 매수/매도 표현 금지.

## 6. 금지 사항

1. C·A 를 이 모듈에서 다시 계산·재추정하는 것.
2. KRX 자격증명 없이 L·I·M 에 0점 부여 (반드시 N/A).
3. 지수 데이터 없이 시장 방향을 기억·뉴스로 단정하는 것.
4. 차트 패턴·목표가·돌파 시점 예측.
5. 뉴스 기반 촉매/신제품 서술 (공시 rcept_no 없는 사건).
6. level 제출 및 모든 직접 산술.
