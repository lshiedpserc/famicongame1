from py65.assembler import Assembler
from py65.devices.mpu6502 import MPU

code = """
.org $8000
start:
  nop
  nop
  jmp start

.org $FFFA
.word start
"""

try:
    mpu = MPU()
    a = Assembler(mpu)
    # The assemble method might return a list of bytes.
    # But it also modifies mpu memory?
    # Let's inspect the return value.
    binary = a.assemble(code)
    print(f"Result type: {type(binary)}")
    print(f"Result: {binary}")
except Exception as e:
    import traceback
    traceback.print_exc()
