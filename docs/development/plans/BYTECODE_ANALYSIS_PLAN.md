# 바이트코드 분석 기능 검토 및 구현 계획

## 현재 상태 분석

### 1. 파라미터 값 분석 (true/false)

**현재 가능한 것:**
- ✅ 메서드 시그니처 파싱 (메서드 이름, 파라미터 타입, 리턴 타입)
- ✅ 메서드가 호출되는지 여부 확인
- ✅ 파라미터 **타입** 확인 (예: `boolean`, `String`, `int`)

**현재 불가능한 것:**
- ❌ 메서드 호출 시 전달되는 **실제 값** 분석
- ❌ `setJavaScriptEnabled(true)` vs `setJavaScriptEnabled(false)` 구분
- ❌ 상수 값, 문자열 리터럴 추출

**왜 불가능한가?**

현재 구현은 DEX 파일의 **메타데이터 영역**만 파싱합니다:
```
DEX 파일 구조:
├── Header (파일 메타데이터) ✅ 파싱 완료
├── String Pool (문자열) ✅ 파싱 완료
├── Type IDs (타입 정의) ✅ 파싱 완료
├── Method IDs (메서드 시그니처) ✅ 파싱 완료
├── Class Definitions (클래스 구조) ✅ 파싱 완료
└── Code Items (바이트코드 인스트럭션) ❌ 파싱 안됨 <- 여기에 true/false가 있음
```

파라미터 값은 **바이트코드 인스트럭션** 안에 있습니다:
```
예시: setJavaScriptEnabled(true) 호출

바이트코드:
  const/4 v0, 0x1        # v0 = 1 (true)
  invoke-virtual {p1, v0}, Landroid/webkit/WebSettings;->setJavaScriptEnabled(Z)V

const/4 인스트럭션에서 0x1 = true 값을 알 수 있음
```

### 2. 크로스 레퍼런스 (Cross-Reference) 검색

**크로스 레퍼런스란?**
특정 메서드/클래스가 **어디서 호출되는지** 역추적하는 기능

예시:
```
질문: "setJavaScriptEnabled() 메서드를 누가 호출하나?"

크로스 레퍼런스 결과:
  com.example.WebViewActivity.initWebView()  → setJavaScriptEnabled()
  com.example.BrowserFragment.setupWebView() → setJavaScriptEnabled()
  com.thirdparty.AdSDK.loadAd()              → setJavaScriptEnabled()
```

**현재 가능한 것:**
- ✅ 메서드 정의 찾기 (어떤 메서드들이 존재하는지)
- ✅ 메서드 시그니처로 필터링 (파라미터에 WebView가 포함된 메서드)
- ✅ 클래스 이름으로 검색

**현재 불가능한 것:**
- ❌ 메서드 호출 지점 찾기 (invoke-virtual 인스트럭션 분석)
- ❌ "이 메서드를 누가 호출하나?" 역추적
- ❌ 호출 그래프 (Call Graph) 생성

**왜 불가능한가?**

크로스 레퍼런스는 **바이트코드 인스트럭션**의 `invoke-*` 명령을 분석해야 합니다:
```
바이트코드에서 메서드 호출:
  invoke-virtual {v1, v2}, Landroid/webkit/WebView;->loadUrl(Ljava/lang/String;)V
  invoke-static {v0}, Lcom/example/Utils;->helper(I)V
  invoke-direct {p0}, Ljava/lang/Object;-><init>()V

이런 인스트럭션들을 파싱해야 "누가 무엇을 호출하는지" 알 수 있음
```

## 구현 방안

### 옵션 1: 바이트코드 파서 직접 구현 (추천)

**장점:**
- 완전한 제어 가능
- 필요한 기능만 선택적으로 구현
- 외부 의존성 없음
- 성능 최적화 가능

**단점:**
- 구현 복잡도 높음
- DEX 바이트코드 명세 이해 필요
- 개발 시간 오래 걸림

**구현 단계:**

1. **Code Item 파서 구현** (2-3일)
   ```rust
   pub struct CodeItem {
       pub registers_size: u16,
       pub ins_size: u16,
       pub outs_size: u16,
       pub tries_size: u16,
       pub debug_info_off: u32,
       pub insns_size: u32,
       pub insns: Vec<u16>,  // 바이트코드 인스트럭션
   }
   ```

2. **Dalvik 인스트럭션 디코더** (3-4일)
   ```rust
   pub enum DalvikInstruction {
       Const4 { dest: u8, value: i8 },
       Const16 { dest: u8, value: i16 },
       InvokeVirtual { args: Vec<u8>, method_idx: u32 },
       InvokeStatic { args: Vec<u8>, method_idx: u32 },
       // ... 218개 인스트럭션 타입
   }
   ```

3. **상수 값 추출기** (1-2일)
   ```rust
   pub fn extract_constant_values(method: &EncodedMethod) -> Vec<ConstantValue> {
       // const/4, const/16, const-string 등에서 값 추출
   }
   ```

4. **크로스 레퍼런스 빌더** (2-3일)
   ```rust
   pub struct CrossReferenceIndex {
       method_calls: HashMap<u32, Vec<CallSite>>,  // method_idx -> 호출 지점들
       field_accesses: HashMap<u32, Vec<AccessSite>>,
   }
   ```

**총 예상 개발 기간: 8-12일**

### 옵션 2: dex-rs 라이브러리 사용

**장점:**
- 빠른 구현 (1-2일)
- 검증된 라이브러리
- 바이트코드 파싱 이미 구현됨

**단점:**
- 의존성 추가
- 커스터마이징 어려움
- 라이브러리 API에 종속

**구현 예시:**
```rust
// Cargo.toml
[dependencies]
dex = "0.5"  // https://crates.io/crates/dex

// 사용 예시
use dex::Dex;

let dex = Dex::from_file("classes.dex")?;
for class in dex.classes() {
    for method in class.methods() {
        if let Some(code) = method.code() {
            for insn in code.instructions() {
                match insn {
                    Instruction::Const4(dest, value) => {
                        println!("const/4 v{}, {}", dest, value);
                    }
                    Instruction::InvokeVirtual { args, method } => {
                        println!("invoke-virtual {:?}, {}", args, method.name());
                    }
                    _ => {}
                }
            }
        }
    }
}
```

### 옵션 3: 디컴파일러 통합 (jadx, apktool)

**장점:**
- 완성도 높은 도구
- 소스 코드 수준 분석 가능
- GUI 도구와 통합 가능

**단점:**
- 외부 프로세스 실행 필요
- 성능 오버헤드 큼
- 디컴파일 실패 가능성

## 사용 사례별 구현 우선순위

### 사용 사례 1: WebView 보안 설정 분석

**필요한 기능:**
- `setJavaScriptEnabled(true/false)` 값 확인
- `addJavascriptInterface()` 호출 위치
- `setAllowFileAccess()` 설정 값

**추천 구현:**
- 옵션 1 (부분 구현): `const/*` 인스트럭션만 파싱
- boolean 상수 값만 추출
- 개발 기간: 3-4일

### 사용 사례 2: API 사용 패턴 분석

**필요한 기능:**
- 특정 API 호출 지점 찾기
- 호출 컨텍스트 분석
- 데이터 흐름 추적

**추천 구현:**
- 옵션 1 (전체 구현): 전체 바이트코드 파서
- 크로스 레퍼런스 인덱스 구축
- 개발 기간: 8-12일

### 사용 사례 3: 빠른 프로토타입

**필요한 기능:**
- 바로 사용 가능한 분석
- 최소한의 개발 시간

**추천 구현:**
- 옵션 2: dex-rs 라이브러리 사용
- 개발 기간: 1-2일

## 구현 제안: 단계별 접근

### Phase 1: 기본 바이트코드 접근 (1일)

현재 있는 `code_off` 활용하여 바이트코드 읽기만 구현:

```rust
// src/dex/parser.rs에 추가
impl DexParser {
    pub fn get_method_code(&self, code_off: u32) -> Result<Vec<u16>> {
        if code_off == 0 {
            return Ok(Vec::new());
        }

        let mut cursor = Cursor::new(&self.data);
        cursor.seek(SeekFrom::Start(code_off as u64))?;

        let _registers_size = cursor.read_u16::<LittleEndian>()?;
        let _ins_size = cursor.read_u16::<LittleEndian>()?;
        let _outs_size = cursor.read_u16::<LittleEndian>()?;
        let _tries_size = cursor.read_u16::<LittleEndian>()?;
        let _debug_info_off = cursor.read_u32::<LittleEndian>()?;
        let insns_size = cursor.read_u32::<LittleEndian>()?;

        let mut insns = Vec::new();
        for _ in 0..insns_size {
            insns.push(cursor.read_u16::<LittleEndian>()?);
        }

        Ok(insns)
    }
}
```

### Phase 2: 상수 값 추출기 (2-3일)

boolean, int 상수만 추출:

```rust
pub fn extract_boolean_constants(insns: &[u16]) -> Vec<bool> {
    let mut constants = Vec::new();
    let mut i = 0;

    while i < insns.len() {
        let opcode = (insns[i] & 0xFF) as u8;

        match opcode {
            0x12 => {  // const/4
                let value = ((insns[i] >> 12) & 0xF) as i8;
                constants.push(value != 0);
                i += 1;
            }
            _ => {
                i += 1;  // 다른 인스트럭션은 스킵
            }
        }
    }

    constants
}
```

### Phase 3: 메서드 호출 추출기 (2-3일)

`invoke-*` 인스트럭션에서 호출 정보 추출:

```rust
pub struct MethodCall {
    pub caller_method_idx: u32,
    pub callee_method_idx: u32,
    pub arguments: Vec<u8>,  // 레지스터 번호
}

pub fn extract_method_calls(insns: &[u16]) -> Vec<u32> {
    let mut calls = Vec::new();
    let mut i = 0;

    while i < insns.len() {
        let opcode = (insns[i] & 0xFF) as u8;

        match opcode {
            0x6e..=0x72 => {  // invoke-virtual, invoke-super, etc.
                let method_idx = insns[i + 1] as u32;
                calls.push(method_idx);
                i += 3;
            }
            _ => {
                i += 1;
            }
        }
    }

    calls
}
```

### Phase 4: 크로스 레퍼런스 인덱스 (3-4일)

전체 DEX를 스캔하여 역참조 맵 생성:

```rust
pub struct XRefIndex {
    // method_idx -> 이 메서드를 호출하는 (caller_class_idx, caller_method_idx) 목록
    pub method_xrefs: HashMap<u32, Vec<(u32, u32)>>,
}

pub fn build_xref_index(dex: &DexParser) -> Result<XRefIndex> {
    let mut index = XRefIndex {
        method_xrefs: HashMap::new(),
    };

    for class_idx in 0..dex.class_count() {
        let class_def = dex.get_class_def(class_idx)?;
        let class_data = dex.parse_class_data(class_def.class_data_off)?;

        for method in class_data.direct_methods.iter()
                        .chain(class_data.virtual_methods.iter()) {
            if method.code_off == 0 {
                continue;
            }

            let insns = dex.get_method_code(method.code_off)?;
            let calls = extract_method_calls(&insns);

            for callee_method_idx in calls {
                index.method_xrefs
                    .entry(callee_method_idx)
                    .or_insert_with(Vec::new)
                    .push((class_idx, method.method_idx));
            }
        }
    }

    Ok(index)
}
```

## Python API 설계

```python
# WebView 보안 설정 분석 (Phase 2 이후)
analyzer = ApkAnalyzer("app.apk")

# 파라미터 값 포함 검색
js_enabled_calls = analyzer.find_method_calls(
    method_name="setJavaScriptEnabled",
    with_parameters=True
)

for call in js_enabled_calls:
    print(f"{call.caller_class}.{call.caller_method}()")
    print(f"  → setJavaScriptEnabled({call.arguments[0]})")  # true or false
    print(f"  at {call.source_file}:{call.line_number}")

# 크로스 레퍼런스 검색 (Phase 4 이후)
xrefs = analyzer.find_cross_references(
    target_class="android.webkit.WebSettings",
    target_method="setJavaScriptEnabled"
)

print(f"setJavaScriptEnabled()이 {len(xrefs)}곳에서 호출됨:")
for xref in xrefs:
    print(f"  - {xref.caller_class}.{xref.caller_method}()")
    print(f"    {xref.source_file}:{xref.line_number}")
```

## 결론 및 추천

### 현재 상태:
- ✅ 메서드 시그니처 분석 완료
- ✅ 클래스 구조 분석 완료
- ❌ 바이트코드 인스트럭션 분석 미구현

### 단기 목표 (1-2주):
**Phase 1-2 구현**을 추천합니다:
- 바이트코드 읽기 기능
- boolean 상수 값 추출
- WebView 보안 설정 분석 완성

이렇게 하면 사용자님이 원하시는 `setJavaScriptEnabled(true)` vs `false` 구분이 가능합니다.

### 중장기 목표 (1개월):
**Phase 3-4 구현**으로 확장:
- 전체 크로스 레퍼런스 시스템
- 호출 그래프 생성
- API 사용 패턴 분석

### 대안:
빠른 프로토타입이 필요하다면 **dex-rs 라이브러리 통합** (1-2일)도 좋은 선택입니다.

## 다음 단계

어떤 방향으로 진행할까요?

1. **Phase 1-2만 빠르게 구현** (WebView 분석에 집중)
2. **전체 바이트코드 파서 구현** (완전한 기능)
3. **dex-rs 라이브러리 통합** (빠른 프로토타입)
4. **현재 수준 유지** (메타데이터 분석만)

사용 사례와 우선순위를 알려주시면 구체적인 구현을 시작하겠습니다!
