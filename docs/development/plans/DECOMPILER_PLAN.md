# 부분 디컴파일 기능 구현 계획

## 목표

WebView 보안 분석을 위한 **최소한의 디컴파일 기능** 구현

### 왜 필요한가?

현재 상태:
```
✓ invoke-direct {v0, v1, v3, v6}, method@1505
  → Register v3 = TRUE
  → Method call @ index 1505
```

원하는 상태:
```java
webSettings.setJavaScriptEnabled(true);
```

**핵심**: method_idx → 실제 메서드 이름 매핑 + 간단한 표현식 재구성

## Androguard 디컴파일러 구조 분석

### 전체 파이프라인

```
Dalvik Bytecode
    ↓
[1] Instruction Parsing (✅ 우리가 이미 구현)
    ↓
[2] Basic Block Analysis
    ↓
[3] Control Flow Graph (CFG)
    ↓
[4] Data Flow Analysis
    ↓
[5] AST Construction
    ↓
[6] Code Generation
    ↓
Java-like Code
```

### 우리에게 필요한 것

**WebView 분석만을 위한 최소 구현:**

```
Dalvik Bytecode
    ↓
[1] Instruction Parsing ← ✅ 완료
    ↓
[2] Method Index Resolution ← 🎯 여기만 구현
    ↓
[3] Simple Expression Reconstruction ← 🎯 여기만 구현
    ↓
Simplified Statement
```

## 구현 계획

### Phase 1: Method Index Resolution (1-2시간)

**목표**: `method@1505` → `setJavaScriptEnabled`

**구현**:
```rust
// src/dex/method_resolver.rs

pub struct MethodResolver {
    parser: DexParser,
}

impl MethodResolver {
    /// Resolve method_idx to method signature
    pub fn resolve_method(&self, method_idx: u32) -> Result<MethodSignature> {
        // 1. Get method_id_item
        let method_info = self.parser.get_method_info(method_idx)?;

        // 2. Get class name
        let class_name = self.parser.get_type_name(method_info.class_idx)?;

        // 3. Get method name
        let method_name = self.parser.get_string(method_info.name_idx)?;

        // 4. Get prototype (params + return type)
        let proto = self.parser.get_proto_info(method_info.proto_idx)?;

        Ok(MethodSignature {
            class_name,
            method_name,
            parameters: proto.parameters,
            return_type: proto.return_type,
        })
    }
}
```

**Python API**:
```python
# 사용 예시
resolver = core.create_method_resolver(dex_data)
method_sig = resolver.resolve(method_idx=1505)

print(method_sig.class_name)    # "android.webkit.WebSettings"
print(method_sig.method_name)   # "setJavaScriptEnabled"
print(method_sig.parameters)    # ["boolean"]
```

### Phase 2: Simple Expression Reconstruction (2-3시간)

**목표**: 바이트코드 패턴 → 간단한 표현식

**지원할 패턴**:

#### Pattern 1: Direct Constant Call
```
const/4 v1, #1
invoke-virtual {v0, v1}, method@1505

→ webSettings.setJavaScriptEnabled(true)
```

#### Pattern 2: Field Access
```
iget-object v0, v2, field@234
invoke-virtual {v0, v1}, method@1505

→ this.webSettings.setJavaScriptEnabled(true)
```

#### Pattern 3: Method Chain
```
invoke-virtual {v0}, method@1234  # getSettings()
move-result-object v1
const/4 v2, #1
invoke-virtual {v1, v2}, method@1505

→ webView.getSettings().setJavaScriptEnabled(true)
```

**구현**:
```rust
// src/dex/simple_decompiler.rs

pub struct SimpleDecompiler {
    resolver: MethodResolver,
}

impl SimpleDecompiler {
    /// Decompile a simple method call pattern
    pub fn decompile_invoke_pattern(
        &self,
        instructions: &[Instruction],
        start_idx: usize,
    ) -> Option<String> {
        // Find the invoke instruction
        if let Instruction::InvokeVirtual { args, method_idx } = &instructions[start_idx] {
            // Resolve method
            let method_sig = self.resolver.resolve_method(*method_idx).ok()?;

            // Track register values backwards
            let mut arg_values = Vec::new();
            for &arg_reg in args {
                // Look backwards for const that loaded into this register
                for i in (0..start_idx).rev() {
                    match &instructions[i] {
                        Instruction::Const4 { dest, value } if *dest == arg_reg => {
                            arg_values.push(format!("{}", value));
                            break;
                        }
                        Instruction::Const16 { dest, value } if *dest == arg_reg => {
                            arg_values.push(format!("{}", value));
                            break;
                        }
                        _ => {}
                    }
                }
            }

            // Generate simple expression
            Some(format!(
                "{}.{}({})",
                simplify_class_name(&method_sig.class_name),
                method_sig.method_name,
                arg_values.join(", ")
            ))
        } else {
            None
        }
    }
}

fn simplify_class_name(full_name: &str) -> String {
    // "android.webkit.WebSettings" → "webSettings" (heuristic)
    full_name.split('.').last().unwrap_or(full_name).to_lowercase()
}
```

### Phase 3: Integration with WebView Analysis (1시간)

**목표**: 분석 결과에 디컴파일된 코드 표시

```python
# test_webview_decompiled.py

def analyze_webview_with_decompilation(apk_path):
    results = core.extract_methods_bytecode(apk_path, webview_classes)

    for class_name, method_name, bytecode in results:
        instructions = core.decode_bytecode(bytecode)

        # Decompile invoke patterns
        decompiler = core.SimpleDecompiler(apk_path)

        for i, insn in enumerate(instructions):
            if insn.is_invoke():
                # Try to decompile this call
                code = decompiler.decompile_invoke_pattern(instructions, i)

                if code and 'setJavaScriptEnabled' in code:
                    print(f"📍 {class_name}.{method_name}()")
                    print(f"   {code}")  # ← 디컴파일된 코드!
```

**예상 출력**:
```
📍 K5.k.onClick()
   webSettings.setJavaScriptEnabled(true)

📍 HelpWebViewActivity.onCreate()
   webSettings.setJavaScriptEnabled(false)
```

## 구현 우선순위

### Must Have (핵심 기능)

1. ✅ **Method Index Resolution**
   - DEX method_ids 테이블 조회
   - Class + Method name 추출
   - 예상 시간: 1-2시간

2. ✅ **Const → Invoke 패턴 디컴파일**
   - 가장 흔한 패턴
   - WebView 분석에 충분
   - 예상 시간: 2시간

### Nice to Have (추가 기능)

3. ⚪ **Field Resolution**
   - field_idx → field name
   - `this.webView` 같은 표현
   - 예상 시간: 1시간

4. ⚪ **Move-result 추적**
   - 메서드 체이닝 지원
   - `webView.getSettings().setX()`
   - 예상 시간: 2시간

5. ⚪ **String Resolution**
   - const-string → 실제 문자열 값
   - URL, 설정 값 표시
   - 예상 시간: 30분

### Won't Have (불필요)

- ❌ Control Flow Graph
- ❌ Data Flow Analysis
- ❌ Full AST Construction
- ❌ Loop Reconstruction
- ❌ Try-Catch Handling

이런 것들은 WebView 분석에 필요 없음!

## 비교: Full vs Partial Decompilation

### Full Decompiler (Androguard)

```
구현 시간: 수개월
복잡도: 매우 높음
코드 품질: 거의 원본 Java와 유사
사용 사례: 전체 앱 리버싱
```

### Partial Decompiler (우리)

```
구현 시간: 4-6시간
복잡도: 낮음
코드 품질: 간단한 표현식만
사용 사례: WebView 보안 감사
```

## 구현 예제

### Input (현재)
```
invoke-direct {v0, v1, v3, v6}, method@1505
  → Register v3 = TRUE
  → Method call @ index 1505
```

### Output (Phase 1 후)
```
invoke-direct {v0, v1, v3, v6}, method@1505
  → android.webkit.WebSettings.setJavaScriptEnabled(boolean)
  → Register v3 = TRUE
```

### Output (Phase 2 후)
```
webSettings.setJavaScriptEnabled(true)
```

## 다음 단계

1. **즉시 시작 가능**: Method Resolution
   - DEX 파서에 이미 필요한 함수 대부분 존재
   - `get_method_info`, `get_string`, `get_type_name` 등

2. **테스트 주도 개발**:
   ```python
   # test_method_resolution.py
   method_sig = resolve_method(apk, method_idx=1505)
   assert method_sig.method_name == "setJavaScriptEnabled"
   ```

3. **점진적 기능 추가**:
   - Phase 1 완료 → 테스트
   - Phase 2 추가 → 테스트
   - 필요시 Phase 3, 4 추가

## 참고 자료

- [Dalvik Bytecode Format](https://source.android.com/docs/core/runtime/dalvik-bytecode)
- [Androguard Decompiler](https://github.com/androguard/androguard/tree/master/androguard/decompiler)
- [DEX Method ID 구조](https://source.android.com/docs/core/runtime/dex-format#method-id-item)

## 기대 효과

### Before
```
🟢 JavaScript ENABLED Methods:
   K5.k.onClick()
   ✓ invoke-direct {v0, v1, v3, v6}, method@1505
     → Register v3 = TRUE
```

### After
```
🟢 JavaScript ENABLED Methods:
   K5.k.onClick()
   ✓ webSettings.setJavaScriptEnabled(true)
```

훨씬 명확하고 사용자 친화적! 🎯
