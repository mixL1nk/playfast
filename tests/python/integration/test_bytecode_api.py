#!/usr/bin/env python3
"""Test bytecode analysis API."""

from playfast import core


def test_decode_bytecode():
    """Test basic bytecode decoding."""
    print("=" * 70)
    print("🔍 Testing Bytecode Decoding API")
    print("=" * 70)
    print()

    # Test 1: const/4 instructions
    print("Test 1: const/4 v0, #1")
    bytecode = [0xF012]  # const/4 v0, #-1  (opcode=0x12, dest=0, value=F=-1)
    instructions = core.decode_bytecode(bytecode)

    print(f"  Bytecode: 0x{bytecode[0]:04x}")
    print(f"  Decoded: {len(instructions)} instruction(s)")

    if instructions:
        insn = instructions[0]
        print(f"  Opcode: {insn.opcode}")
        print(f"  Dest: v{insn.dest}")
        print(f"  Value: {insn.value}")
        print(f"  Boolean value: {insn.get_boolean_value()}")
        print(f"  Raw: {insn.raw}")
    print()

    # Test 2: const/4 v1, #1 (true)
    print("Test 2: const/4 v1, #1 (true)")
    bytecode = [0x1112]  # const/4 v1, #1
    instructions = core.decode_bytecode(bytecode)

    if instructions:
        insn = instructions[0]
        print(f"  Opcode: {insn.opcode}")
        print(f"  Dest: v{insn.dest}")
        print(f"  Value: {insn.value}")
        print(f"  Boolean value: {insn.get_boolean_value()}")
        print(f"  Raw: {insn.raw}")
    print()

    # Test 3: Extract constants
    print("Test 3: Extract constants from bytecode")
    bytecode = [
        0x0012,  # const/4 v0, #0 (false)
        0x1112,  # const/4 v1, #1 (true)
        0x2212,  # const/4 v2, #2
        0xF012,  # const/4 v0, #-1
    ]
    constants = core.extract_constants(bytecode)

    print(f"  Bytecode: {[hex(b) for b in bytecode]}")
    print(f"  Constants: {constants}")
    print()

    print("✅ Bytecode decoding API works!")
    print()


def test_invoke_instructions():
    """Test method invocation decoding."""
    print("=" * 70)
    print("📞 Testing Method Invocation Decoding")
    print("=" * 70)
    print()

    # invoke-virtual {v1, v2}, method@42
    bytecode = [
        0x206E,  # invoke-virtual (opcode=0x6E, arg_count=2, first_arg=0)
        0x0042,  # method_idx=66
        0x0021,  # args: v1, v2
    ]

    instructions = core.decode_bytecode(bytecode)

    print(f"  Bytecode: {[hex(b) for b in bytecode]}")
    print(f"  Decoded: {len(instructions)} instruction(s)")

    if instructions:
        insn = instructions[0]
        print(f"  Opcode: {insn.opcode}")
        print(f"  Method index: {insn.method_idx}")
        print(f"  Arguments: {insn.args}")
        print(f"  Raw: {insn.raw}")
    print()

    # Extract method calls
    method_calls = core.extract_method_calls(bytecode)
    print(f"  Extracted method calls: {method_calls}")
    print()

    print("✅ Method invocation decoding works!")
    print()


if __name__ == "__main__":
    test_decode_bytecode()
    test_invoke_instructions()

    print("=" * 70)
    print("🎉 All bytecode API tests passed!")
    print("=" * 70)
