# Class-Level Decompilation Analysis

## Current Capabilities

### Method-Level (현재 구현됨)
- ✅ 단일 메소드의 bytecode를 Java-like 표현식으로 변환
- ✅ Method index → method signature 해석
- ✅ Register tracking으로 const 값 추적
- ✅ Boolean parameter 값 탐지

**Example**:
```
Input: method@22427, bytecode [const/4 v0, #1, invoke-virtual {v0, v3}, ...]
Output: webSettings.setJavaScriptEnabled(true)
```

### What Class-Level Decompilation Means

클래스 단위 디컴파일은 다음을 의미합니다:

1. **전체 클래스의 모든 메소드를 디컴파일**
   ```java
   class V5.c {
       void onViewCreated() {
           // Decompiled method body
           webSettings.setJavaScriptEnabled(true);
       }

       void otherMethod() {
           // Decompiled method body
       }
   }
   ```

2. **클래스 구조 정보 포함**
   - Class name, package
   - Superclass, interfaces
   - Fields
   - Methods (with decompiled bodies)

3. **Use Cases**
   - 특정 클래스의 전체 구현 이해
   - WebView를 사용하는 Activity/Fragment 전체 분석
   - 클래스의 보안 관련 메소드 일괄 검토

## Implementation Plan

### Option 1: Batch Method Decompilation (간단)
전체 클래스의 메소드들을 반복 처리

**Pros**:
- 기존 코드 재사용
- 빠른 구현 (1-2시간)

**Cons**:
- 메소드 간 관계 표시 안됨
- Field 정보 부족

### Option 2: Full Class Reconstruction (복잡)
전체 클래스 구조를 재구성

**Pros**:
- 완전한 클래스 정보
- IDE-friendly 출력

**Cons**:
- 구현 시간 길음 (4-6시간)
- 필요성 불명확

## Recommended Approach: Enhanced Batch Decompilation

### Phase 1: Batch Method Decompilation
1. 클래스의 모든 메소드 bytecode 추출
2. 각 메소드를 Phase 1 decompilation으로 처리
3. 결과를 구조화된 포맷으로 출력

### Phase 2: Add Class Context
1. 클래스 메타데이터 포함 (superclass, interfaces, fields)
2. 메소드 signature 완전 표시
3. Access flags 표시 (public/private/protected)

## API Design

```python
# Single method (현재)
expressions = core.reconstruct_expressions_from_apk(
    "app.apk",
    "V5.c",
    "onViewCreated"
)

# Whole class (새로 구현)
class_info = core.decompile_class_from_apk(
    "app.apk",
    "V5.c"
)

# class_info structure:
{
    "class_name": "V5.c",
    "package": "V5",
    "superclass": "androidx.fragment.app.Fragment",
    "interfaces": [],
    "fields": [...],
    "methods": [
        {
            "name": "onViewCreated",
            "signature": "onViewCreated(android.view.View, android.os.Bundle): void",
            "access_flags": "public",
            "expressions": [
                {
                    "expression": "webSettings.setJavaScriptEnabled(true)",
                    "line": 65,
                    "bytecode_offset": 128
                }
            ]
        }
    ]
}
```

## Use Cases for WebView Analysis

### Current (Method-level)
```python
# Find specific method
bytecode = extract_method_bytecode("app.apk", "V5.c", "onViewCreated")
# Analyze one method
```

### With Class-level
```python
# Analyze entire WebView Activity
class_info = decompile_class("app.apk", "WebViewActivity")
# Get all methods that use WebView
webview_methods = [m for m in class_info.methods
                   if any("WebView" in e.expression for e in m.expressions)]
# Security overview
```

## Implementation Estimate

### Minimal (Recommended): 2-3 hours
- ✅ Reuse existing method decompilation
- ✅ Add class metadata collection
- ✅ Structure output as dict/dataclass
- ✅ Test with WebView classes

### Full: 5-6 hours
- Above +
- Field resolution in expressions
- Method call graph within class
- Pretty-print Java-like output

## Decision

**Recommendation**: Implement Minimal version

**Rationale**:
1. WebView 보안 분석에 충분
2. 기존 infrastructure 활용
3. 빠른 구현 및 검증
4. 필요시 확장 용이

## Next Steps

1. ✅ Create `decompile_class_from_apk()` function
2. ✅ Collect class metadata (superclass, interfaces, fields)
3. ✅ Batch process all methods in class
4. ✅ Structure output as DecompiledClass dataclass
5. ✅ Test with WebView classes
6. ✅ Create convenience analyzer for security review
