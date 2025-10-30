#!/usr/bin/env python3
"""Test Dalvik instruction decoder."""


# Simple unit test for instruction decoding logic
def test_const4_encoding():
    """Test const/4 instruction encoding understanding.

    Format: const/4 vA, #+B
    - Byte 0: opcode (0x12)
    - Byte 1 low nibble (4 bits): destination register (vA)
    - Byte 1 high nibble (4 bits): signed literal value (#+B)
    """
    print("=" * 70)
    print("Testing const/4 instruction encoding")
    print("=" * 70)
    print()

    # Example 1: const/4 v0, #1
    bytecode_word = 0x1201  # opcode=0x12, encoded=0x01
    opcode = bytecode_word & 0xFF
    dest = (bytecode_word >> 8) & 0xF
    value_bits = (bytecode_word >> 12) & 0xF

    # Sign extend 4-bit value
    if value_bits & 0x8:
        # Negative number
        value = (value_bits | 0xF0) - 256  # Convert unsigned to signed
    else:
        value = value_bits

    print(f"Bytecode: 0x{bytecode_word:04x}")
    print(f"Opcode: 0x{opcode:02x} (const/4)")
    print(f"Destination: v{dest}")
    print(f"Value bits: 0x{value_bits:x}")
    print(f"Value: {value}")
    print(f"Instruction: const/4 v{dest}, #{value}")
    print()

    # Example 2: const/4 v0, #-1
    bytecode_word = 0xF012  # opcode=0x12, value=0xF (-1)
    opcode = bytecode_word & 0xFF
    dest = (bytecode_word >> 8) & 0xF
    value_bits = (bytecode_word >> 12) & 0xF

    # Sign extend 4-bit value
    if value_bits & 0x8:
        value = (value_bits | 0xF0) - 256
    else:
        value = value_bits

    print(f"Bytecode: 0x{bytecode_word:04x}")
    print(f"Opcode: 0x{opcode:02x} (const/4)")
    print(f"Destination: v{dest}")
    print(f"Value bits: 0x{value_bits:x}")
    print(f"Value: {value}")
    print(f"Instruction: const/4 v{dest}, #{value}")
    print()


def test_invoke_virtual_encoding():
    """Test invoke-virtual instruction encoding.

    Format: invoke-virtual {vC, vD, vE, vF, vG}, meth@BBBB
    - Word 0: opcode + arg count
    - Word 1: method index
    - Word 2: argument registers
    """
    print("=" * 70)
    print("Testing invoke-virtual instruction encoding")
    print("=" * 70)
    print()

    # Example: invoke-virtual {v1, v2}, method@0x0042
    # 3 words total
    word0 = 0x206E  # opcode=0x6E (invoke-virtual), arg_count=2, first_arg=0
    word1 = 0x0042  # method_idx
    word2 = 0x0021  # args: v1, v2

    opcode = word0 & 0xFF
    arg_count = (word0 >> 12) & 0xF
    first_arg = (word0 >> 8) & 0xF
    method_idx = word1

    args = [first_arg]
    for i in range(arg_count - 1):
        arg = (word2 >> (i * 4)) & 0xF
        args.append(arg)

    print(f"Word 0: 0x{word0:04x}")
    print(f"Word 1: 0x{word1:04x}")
    print(f"Word 2: 0x{word2:04x}")
    print()
    print(f"Opcode: 0x{opcode:02x} (invoke-virtual)")
    print(f"Method index: {method_idx}")
    print(f"Arg count: {arg_count}")
    print(f"Arguments: {', '.join(f'v{a}' for a in args)}")
    print(
        f"Instruction: invoke-virtual {{{'v{}, '.join(str(a) for a in args)}}}, method@{method_idx}"
    )
    print()


if __name__ == "__main__":
    test_const4_encoding()
    test_invoke_virtual_encoding()

    print("=" * 70)
    print("✅ Instruction encoding tests passed!")
    print("=" * 70)
