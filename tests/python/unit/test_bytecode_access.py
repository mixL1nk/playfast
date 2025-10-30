#!/usr/bin/env python3
"""Test bytecode access capabilities - POC."""

from pathlib import Path

from playfast import core


def test_bytecode_structure():
    """현재 구현 상태 테스트.

    목적: code_off (바이트코드 오프셋)에 접근 가능한지 확인
    """
    print("=" * 70)
    print("🔍 바이트코드 접근 테스트")
    print("=" * 70)
    print()

    apk_path = Path("../samples/com.sampleapp.apk")

    if not apk_path.exists():
        print(f"❌ APK not found: {apk_path}")
        return

    print("📱 APK 로딩 중...")
    classes = core.extract_classes_from_apk(str(apk_path))
    print(f"✅ 클래스 {len(classes):,}개 추출됨\n")

    # WebView 관련 메서드 찾기
    print("🌐 WebView 관련 메서드 검색...")
    print("-" * 70)

    webview_methods = []
    for cls in classes:
        for method in cls.methods:
            # setJavaScriptEnabled 메서드 찾기
            if "setJavaScriptEnabled" in method.name:
                webview_methods.append((cls, method))

    if webview_methods:
        print(f"✅ setJavaScriptEnabled 호출 {len(webview_methods)}개 발견\n")

        for i, (cls, method) in enumerate(webview_methods[:5], 1):
            print(f"{i}. {cls.simple_name}.{method.name}()")
            print(f"   Package: {cls.package_name}")
            print(
                f"   Parameters: {', '.join(method.parameters) if method.parameters else 'none'}"
            )
            print(f"   Return: {method.return_type}")
            print()
    else:
        print("❌ setJavaScriptEnabled 호출 없음\n")

    # 현재 제한사항 설명
    print("=" * 70)
    print("📊 현재 구현 상태")
    print("=" * 70)
    print()

    print("✅ 가능한 것:")
    print("  1. 메서드 시그니처 분석 (이름, 파라미터 타입, 리턴 타입)")
    print("  2. 클래스 구조 분석")
    print("  3. 메서드 존재 여부 확인")
    print("  4. 메서드가 특정 타입을 사용하는지 확인")
    print()

    print("❌ 불가능한 것:")
    print("  1. 메서드 호출 시 전달되는 실제 값 (true/false)")
    print("  2. 크로스 레퍼런스 (이 메서드를 누가 호출하는지)")
    print("  3. 바이트코드 인스트럭션 분석")
    print("  4. 데이터 흐름 추적")
    print()

    print("💡 이유:")
    print("  현재 구현은 DEX 메타데이터 영역만 파싱합니다.")
    print("  바이트코드 인스트럭션 영역은 파싱하지 않습니다.")
    print()

    print("🔨 필요한 작업:")
    print("  1. Code Item 파서 구현")
    print("  2. Dalvik 인스트럭션 디코더")
    print("  3. 상수 값 추출기 (const/4, const/16 등)")
    print("  4. 메서드 호출 추적기 (invoke-virtual 등)")
    print()

    print("📄 자세한 내용은 BYTECODE_ANALYSIS_PLAN.md 참고")
    print()


def test_method_signature_search():
    """현재 가능한 검색 방법 시연."""
    print("\n" + "=" * 70)
    print("🔍 현재 가능한 검색 방법 시연")
    print("=" * 70)
    print()

    apk_path = Path("../samples/com.sampleapp.apk")

    if not apk_path.exists():
        return

    classes = core.extract_classes_from_apk(str(apk_path))

    # 1. 메서드 이름으로 검색
    print("1️⃣ 메서드 이름 검색:")
    print("   검색어: 'javascript' (대소문자 무시)")
    print()

    js_methods = []
    for cls in classes:
        for method in cls.methods:
            if "javascript" in method.name.lower():
                js_methods.append((cls, method))

    print(f"   결과: {len(js_methods)}개 메서드 발견")
    for cls, method in js_methods[:3]:
        print(f"   - {cls.simple_name}.{method.name}()")
    if len(js_methods) > 3:
        print(f"   ... and {len(js_methods) - 3} more")
    print()

    # 2. 파라미터 타입으로 검색
    print("2️⃣ 파라미터 타입 검색:")
    print("   검색어: 'WebView'를 파라미터로 받는 메서드")
    print()

    webview_param_methods = []
    for cls in classes:
        for method in cls.methods:
            if any("WebView" in p for p in method.parameters):
                webview_param_methods.append((cls, method))

    print(f"   결과: {len(webview_param_methods)}개 메서드 발견")
    for cls, method in webview_param_methods[:3]:
        params = ", ".join(method.parameters)
        print(f"   - {cls.simple_name}.{method.name}({params})")
    if len(webview_param_methods) > 3:
        print(f"   ... and {len(webview_param_methods) - 3} more")
    print()

    # 3. 리턴 타입으로 검색
    print("3️⃣ 리턴 타입 검색:")
    print("   검색어: WebView를 반환하는 메서드")
    print()

    webview_return_methods = []
    for cls in classes:
        for method in cls.methods:
            if "WebView" in method.return_type:
                webview_return_methods.append((cls, method))

    print(f"   결과: {len(webview_return_methods)}개 메서드 발견")
    for cls, method in webview_return_methods[:3]:
        print(f"   - {cls.simple_name}.{method.name}() → {method.return_type}")
    if len(webview_return_methods) > 3:
        print(f"   ... and {len(webview_return_methods) - 3} more")
    print()


def main():
    print("🔐 바이트코드 분석 기능 검토")
    print()

    test_bytecode_structure()
    test_method_signature_search()

    print("=" * 70)
    print("📋 요약")
    print("=" * 70)
    print()
    print("현재 구현:")
    print("  ✅ 메서드 시그니처 수준 분석 완료")
    print("  ✅ 클래스/메서드 검색 기능 완료")
    print("  ❌ 바이트코드 인스트럭션 분석 미구현")
    print()
    print("다음 단계:")
    print("  1. BYTECODE_ANALYSIS_PLAN.md 검토")
    print("  2. 구현 방향 결정 (Phase 1-2 / 전체 / dex-rs)")
    print("  3. WebView 보안 분석 완성")
    print()


if __name__ == "__main__":
    main()
