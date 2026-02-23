from py65.assembler import Assembler
import sys

code = """
.org $8000
start:
  lda #$FF
  sta $2000
  jmp start
"""

try:
    a = Assembler()
    binary = a.assemble(code.splitlines())
    print(f"Assembled {len(binary)} bytes.")
    print(f"First few bytes: {[hex(b) for b in list(binary)[:10]]}")
except Exception as e:
    print(f"Error: {e}")
