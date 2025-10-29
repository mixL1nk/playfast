# ApkAnalyzer API Improvements

## 현재 문제점

### 1. API 수준 불일치
```python
# 예제 1: apk_security_audit.py (고수준, 좋음)
from playfast import ApkAnalyzer
analyzer = ApkAnalyzer("app.apk")
dangerous_perms = analyzer.manifest.permissions

# 예제 2: webview_flow_quick_demo.py (저수준, 나쁨)
from playfast import core
analyzer = core.analyze_entry_points_from_apk(apk)
entry_points = analyzer.analyze()
flows = core.find_webview_flows_from_apk(apk, max_depth=10)
```

**문제**: 같은 라이브러리인데 API 수준이 다름

### 2. 기능 격차
`ApkAnalyzer`에는:
- ✅ 기본 검색: `find_classes()`, `find_methods()`
- ✅ WebView 검색: `find_webview_usage()` (단순)
- ❌ **Data Flow 분석 없음** - `core`를 직접 사용해야 함
- ❌ Entry Point 분석 없음
- ❌ Call Graph 분석 없음

## 제안하는 개선사항

### Phase 1: Data Flow 분석 메서드 추가

```python
class ApkAnalyzer:
    # 새로운 메서드들

    def analyze_entry_points(self):
        """Analyze Android entry points (Activity, Service, etc.)"""

    def find_webview_flows(self, max_depth=10, optimize=True):
        """Find data flows from entry points to WebView APIs"""

    def find_file_flows(self, max_depth=10):
        """Find data flows to file I/O operations"""

    def find_network_flows(self, max_depth=10):
        """Find data flows to network operations"""

    def find_sql_flows(self, max_depth=10):
        """Find data flows to SQL operations"""

    def find_custom_flows(self, sink_patterns, max_depth=10):
        """Find data flows to custom sink patterns"""

    def find_deeplink_flows(self, sink_type="webview"):
        """Find flows from deeplink handlers to sinks"""
```

### Phase 2: 통합 보안 분석

```python
class ApkAnalyzer:
    def security_audit(self, checks=None):
        """Comprehensive security audit

        Returns dict with:
        - dangerous_permissions
        - exported_components
        - webview_flows (Intent → WebView)
        - file_flows (suspicious file access)
        - network_flows (HTTP usage)
        - deeplink_vulnerabilities
        """
```

## 구현 계획

### Step 1: `ApkAnalyzer`에 Data Flow 메서드 추가

파일: `python/playfast/apk.py`

```python
def analyze_entry_points(self):
    """Analyze Android entry points.

    Returns:
        EntryPointAnalysis with:
        - entry_points: List[EntryPoint]
        - deeplink_handlers: List[EntryPoint]
        - statistics: dict
    """
    if not hasattr(self, '_entry_analysis'):
        analyzer = core.analyze_entry_points_from_apk(self._apk_path_str)
        self._entry_analysis = {
            'analyzer': analyzer,
            'entry_points': analyzer.analyze(),
            'deeplink_handlers': analyzer.get_deeplink_handlers(),
            'stats': analyzer.get_stats()
        }
    return self._entry_analysis

def find_webview_flows(
    self,
    max_depth: int = 10,
    optimize: bool = True
) -> List:
    """Find data flows from entry points to WebView APIs.

    Args:
        max_depth: Maximum call chain depth
        optimize: Use optimized filtering (default: True)

    Returns:
        List of Flow objects

    Example:
        >>> apk = ApkAnalyzer("app.apk")
        >>> flows = apk.find_webview_flows(max_depth=10)
        >>> for flow in flows:
        ...     print(f"{flow.entry_point} → {flow.sink_method}")
        ...     if flow.is_deeplink_handler:
        ...         print("  ⚠️  Deeplink vulnerability!")
    """
    if optimize:
        # Use optimized version with entry-point filtering
        analyzer = core.create_data_flow_analyzer(self._apk_path_str)
        return analyzer.find_webview_flows(max_depth)
    else:
        # Full analysis (slower)
        return core.find_webview_flows_from_apk(
            self._apk_path_str,
            max_depth
        )

def find_file_flows(self, max_depth: int = 10) -> List:
    """Find data flows to file I/O operations."""
    analyzer = core.create_data_flow_analyzer(self._apk_path_str)
    return analyzer.find_file_flows(max_depth)

def find_network_flows(self, max_depth: int = 10) -> List:
    """Find data flows to network operations."""
    analyzer = core.create_data_flow_analyzer(self._apk_path_str)
    return analyzer.find_network_flows(max_depth)

def find_sql_flows(self, max_depth: int = 10) -> List:
    """Find data flows to SQL operations."""
    analyzer = core.create_data_flow_analyzer(self._apk_path_str)
    return analyzer.find_sql_flows(max_depth)

def find_custom_flows(
    self,
    sink_patterns: List[str],
    max_depth: int = 10
) -> List:
    """Find data flows to custom sink patterns.

    Args:
        sink_patterns: List of method patterns to find
        max_depth: Maximum call chain depth

    Example:
        >>> # Find flows to Runtime.exec (command execution)
        >>> flows = apk.find_custom_flows(
        ...     ["Runtime.exec", "ProcessBuilder.start"],
        ...     max_depth=15
        ... )
    """
    analyzer = core.create_data_flow_analyzer(self._apk_path_str)
    return analyzer.find_flows_to(sink_patterns, max_depth)
```

### Step 2: 예제 업데이트

**Before** (`webview_flow_quick_demo.py`):
```python
from playfast import core

analyzer = core.analyze_entry_points_from_apk(apk_path)
entry_points = analyzer.analyze()

flows = core.analyze_webview_flows_from_apk(apk_path, max_depth=5)
```

**After**:
```python
from playfast import ApkAnalyzer

apk = ApkAnalyzer(apk_path)

# Simple!
flows = apk.find_webview_flows(max_depth=5)

# More details if needed
entry_analysis = apk.analyze_entry_points()
print(f"Entry points: {len(entry_analysis['entry_points'])}")
print(f"Deeplink handlers: {len(entry_analysis['deeplink_handlers'])}")
```

## Benefits

### 1. 일관된 API
- 모든 분석 기능이 `ApkAnalyzer`를 통해 접근
- 저수준 `core` API는 고급 사용자만 사용

### 2. 사용성 개선
```python
# Before (3단계, 저수준)
from playfast import core
analyzer = core.analyze_entry_points_from_apk(apk)
entry_points = analyzer.analyze()
flows = core.find_webview_flows_from_apk(apk, max_depth=10)

# After (1단계, 고수준)
from playfast import ApkAnalyzer
apk = ApkAnalyzer(apk)
flows = apk.find_webview_flows(max_depth=10)
```

### 3. 성능 최적화 기본 제공
`optimize=True` (default)로 자동으로 32.8x 최적화 적용

### 4. 통합 보안 분석
```python
apk = ApkAnalyzer("app.apk")

# Individual checks
webview_flows = apk.find_webview_flows()
file_flows = apk.find_file_flows()
network_flows = apk.find_network_flows()

# Or comprehensive audit
audit_results = apk.security_audit()
```

## Migration Guide

### Simple Usage
기존 `core` 사용 코드는 `ApkAnalyzer`로 간단히 변경:

```python
# Before
from playfast import core
flows = core.find_webview_flows_from_apk("app.apk", max_depth=10)

# After
from playfast import ApkAnalyzer
apk = ApkAnalyzer("app.apk")
flows = apk.find_webview_flows(max_depth=10)
```

### Advanced Usage
고급 사용자는 여전히 `core` 직접 사용 가능:

```python
from playfast import core

# Full control
entry_analyzer = core.analyze_entry_points_from_apk(apk)
entry_points = entry_analyzer.analyze()

packages = extract_packages(entry_points, depth=2)
graph = core.build_call_graph_from_apk_parallel(apk, packages)

analyzer = core.DataFlowAnalyzer(entry_analyzer.analyzer, graph)
flows = analyzer.find_flows_to(["custom_pattern"], max_depth=20)
```

## Implementation Priority

1. **High Priority**: Data flow 메서드 추가
   - `find_webview_flows()`
   - `find_file_flows()`
   - `find_network_flows()`
   - `find_custom_flows()`

2. **Medium Priority**: Entry point 메서드
   - `analyze_entry_points()`
   - `find_deeplink_flows()`

3. **Low Priority**: 통합 보안 분석
   - `security_audit()`

## 예상 효과

### Before (불편)
- 예제마다 다른 API 사용
- 저수준 API 학습 필요
- 성능 최적화 직접 구현

### After (편리)
- 일관된 고수준 API
- 직관적인 메서드 이름
- 자동 최적화 적용
- 쉬운 보안 분석

---

**Status**: 제안 단계
**Next Step**: ApkAnalyzer 확장 구현
