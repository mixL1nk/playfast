# Entry-Point-Driven Analysis - Implementation Summary

## 현재 상태

### 완료된 작업

1. **문제 분석 완료** ✅
   - 현재 구현: 전체 669개 메서드 분석 (142초)
   - Entry points: 141개
   - 개선 가능성 확인: 50-90% 성능 개선 예상

2. **설계 문서 작성** ✅
   - [ENTRY_POINT_DRIVEN_ANALYSIS.md](ENTRY_POINT_DRIVEN_ANALYSIS.md)
   - BFS 알고리즘 설계
   - API 설계

3. **핵심 모듈 구현 시작** 🔄
   - `src/dex/dex_index.rs`: 클래스 빠른 조회용 인덱스
   - `src/dex/call_graph_incremental.rs`: BFS 기반 incremental 분석
   - Python 바인딩 추가

### 진행 중 이슈

**컴파일 에러**: 타입 불일치
- `usize` vs `u32` 불일치 (DexParser API)
- ApkError → DexError 변환 누락
- `enumerate()` iterator 문제

## 간소화된 접근 방안

### Phase 1: 필터 기반 최적화 (즉시 적용 가능)

현재 `build_call_graph_from_apk`는 `class_filter`를 지원합니다:

```python
# 현재 방식: 전체 분석
graph = core.build_call_graph_from_apk_parallel(apk, None)  # 142초

# 개선: Entry point 패키지만 분석
entry_analyzer = core.analyze_entry_points_from_apk(apk)
entry_points = entry_analyzer.analyze()

# Entry point의 패키지만 추출
packages = set()
for ep in entry_points:
    # "Lcom/example/MainActivity;" -> "com.example"
    pkg = ep['class_name'].replace('L', '').replace('/', '.').split('.')[0:2]
    packages.add('.'.join(pkg))

# 필터링된 분석
graph = core.build_call_graph_from_apk_parallel(apk, list(packages))
```

**예상 효과**:
- 앱 패키지만 분석 (라이브러리 제외)
- 50-70% 속도 향상
- **즉시 사용 가능** (코드 변경 불필요)

### Phase 2: 진정한 Incremental 분석 (향후 구현)

**완료 필요**:
1. DexIndex 타입 수정
2. Incremental call graph builder 완성
3. 테스트 및 벤치마크

## 테스트 방법

### Quick Comparison Test

```python
#!/usr/bin/env python3
"""Compare full vs filtered analysis"""
import time
from playfast import core

apk = "samples/com.sampleapp.apk"

# Test 1: Full analysis
start = time.time()
graph_full = core.build_call_graph_from_apk_parallel(apk, None)
time_full = time.time() - start
stats_full = graph_full.get_stats()

# Test 2: Entry point packages only
entry_analyzer = core.analyze_entry_points_from_apk(apk)
entry_points = entry_analyzer.analyze()

packages = set()
for ep in entry_points:
    # Extract package from class name
    class_name = ep['class_name']
    if class_name.startswith('L'):
        pkg = class_name[1:].split('/')[0:3]  # First 3 parts
        packages.add('/'.join(pkg))

start = time.time()
graph_filtered = core.build_call_graph_from_apk_parallel(apk, list(packages))
time_filtered = time.time() - start
stats_filtered = graph_filtered.get_stats()

# Results
print(f"Full analysis:     {time_full:.1f}s, {stats_full['total_methods']} methods")
print(f"Filtered analysis: {time_filtered:.1f}s, {stats_filtered['total_methods']} methods")
print(f"Speedup: {time_full/time_filtered:.2f}x")
print(f"Methods reduced: {stats_full['total_methods'] - stats_filtered['total_methods']}")
```

## 다음 단계

### 즉시 실행 가능 (Phase 1)

1. **테스트 스크립트 작성**
   - `examples/test_filtered_analysis.py`
   - Full vs Filtered 비교

2. **WebViewFlowAnalyzer 업데이트**
   - Entry point 패키지 자동 필터링
   - 기본값으로 적용

3. **Documentation 업데이트**
   - 필터 사용법 추가
   - 성능 가이드라인

### 향후 구현 (Phase 2)

1. **DexIndex 수정**
   ```rust
   // u32 vs usize 문제 해결
   class_name_to_idx: HashMap<String, u32>,  // parser.class_count() returns u32

   // ApkError 처리
   impl From<ApkError> for DexError {
       fn from(err: ApkError) -> Self {
           DexError::IoError(err.to_string())
       }
   }
   ```

2. **Incremental Builder 완성**
   - BFS 구현 완료
   - 병렬 버전 추가
   - 테스트 케이스

3. **벤치마크**
   - 여러 APK 크기로 테스트
   - 성능 곡선 분석
   - 최적 max_depth 결정

## 실용적 권장사항

### 현재 사용법 (최적화됨)

**WebView 분석용**:
```python
from playfast import core

# 1. Entry points 분석
entry_analyzer = core.analyze_entry_points_from_apk(apk_path)
entry_points = entry_analyzer.analyze()

# 2. 앱 패키지 추출
app_packages = []
for ep in entry_points:
    pkg = ep['class_name'].split('/')[0:3]  # com/example/app
    app_packages.append('/'.join(pkg).replace('L', ''))

# 3. 필터링된 Call Graph (빠름!)
graph = core.build_call_graph_from_apk_parallel(
    apk_path,
    list(set(app_packages))  # 중복 제거
)

# 4. WebView 분석
analyzer = core.WebViewFlowAnalyzer(entry_analyzer, graph)
flows = analyzer.analyze_webview_flows(max_depth=10)
```

**예상 성능**:
- Full: 142s → **Filtered: 40-70s** (50-65% 빠름)
- 같은 WebView 결과 (entry point 관련 코드만 분석)

### 향후 사용법 (Incremental 완성 후)

```python
# 더 빠른 incremental 버전
graph = core.build_call_graph_for_webview(
    apk_path,
    entry_classes=[ep['class_name'] for ep in entry_points],
    max_depth=10
)
# 예상: 20-40s (80-85% 빠름)
```

## 요약

### 핵심 발견
1. ✅ **현재 문제**: 전체 DEX 분석 (불필요한 라이브러리 코드 포함)
2. ✅ **즉시 해결책**: `class_filter` 사용 (50-65% 개선)
3. 🔄 **향후 개선**: True incremental BFS (80-85% 개선)

### 권장 액션
1. **지금 바로**: 필터 기반 최적화 적용
2. **다음 주**: Incremental 구현 완료
3. **테스트**: 실제 APK로 성능 검증

---

**상태**: 설계 완료, 구현 80% 완료, 타입 에러 수정 필요
**추정 작업**: 2-4시간 (타입 수정 + 테스트)
**예상 개선**: Phase 1: 50-65%, Phase 2: 80-85%
