import sys
import re
from py65.assembler import Assembler
from py65.devices.mpu6502 import MPU
from py65.utils.addressing import AddressParser

class SimpleAssembler:
    def __init__(self):
        self.mpu = MPU()
        self.labels = {}
        self.pc = 0
        self.lines = []
        self.binary = bytearray(65536)
        self.min_addr = 65536
        self.max_addr = 0

    def parse_lines(self, lines):
        clean_lines = []
        for line in lines:
            if ';' in line: line = line[:line.index(';')]
            line = line.strip().replace(', ', ',')
            if not line: continue
            clean_lines.append(line)
        self.lines = clean_lines

    def get_instruction_size(self, line, pc, labels):
        parts = line.split()
        mnemonic = parts[0].lower()
        if mnemonic in ['bpl','bmi','bvc','bvs','bcc','bcs','bne','beq']:
            return 2
        if len(parts) == 1:
            return 1
        operand = line[len(mnemonic):].strip()
        if operand.startswith('#'):
            return 2
        if operand.startswith('('):
            return 3

        val = None
        if operand in labels:
            val = labels[operand]
        else:
            try:
                if operand.startswith('$'): val = int(operand[1:], 16)
                elif operand.startswith('%'): val = int(operand[1:], 2)
                else: val = int(operand)
            except:
                pass

        if val is not None:
            if val < 256: return 2
            else: return 3
        return 3

    def assemble_pass(self):
        current_addr = 0
        changes = 0
        new_labels = self.labels.copy()
        for line in self.lines:
            if '=' in line:
                parts = line.split('=')
                try:
                    val_str = parts[1].strip()
                    if val_str.startswith('$'): val = int(val_str[1:], 16)
                    elif val_str.startswith('%'): val = int(val_str[1:], 2)
                    else: val = int(val_str)
                    new_labels[parts[0].strip()] = val
                except: pass
                continue

            if line.endswith(':'):
                label = line[:-1]
                if label not in self.labels or self.labels[label] != current_addr:
                    new_labels[label] = current_addr
                    changes += 1
                continue

            if line.startswith('.'):
                if line.startswith('.org'):
                    parts = line.split()
                    try:
                        current_addr = int(parts[1].replace('$','0x'), 16)
                    except:
                        print(f"Error parsing .org: '{line}'")
                        sys.exit(1)
                elif line.startswith('.byte'):
                    args = line[5:].split(',')
                    current_addr += len(args)
                elif line.startswith('.word'):
                    args = line[5:].split(',')
                    current_addr += len(args) * 2
                continue

            size = self.get_instruction_size(line, current_addr, self.labels)
            current_addr += size

        self.labels = new_labels
        return changes == 0

    def emit_code(self):
        ap = AddressParser(labels=self.labels)
        asm = Assembler(self.mpu, address_parser=ap)
        current_addr = 0
        for line in self.lines:
            if '=' in line: continue
            if line.endswith(':'): continue

            if line.startswith('.'):
                if line.startswith('.org'):
                    parts = line.split()
                    current_addr = int(parts[1].replace('$','0x'), 16)
                elif line.startswith('.byte'):
                    args = line[5:].split(',')
                    for arg in args:
                        val = self.eval_value(arg.strip())
                        self.binary[current_addr] = val
                        current_addr += 1
                elif line.startswith('.word'):
                    args = line[5:].split(',')
                    for arg in args:
                        val = self.eval_value(arg.strip())
                        self.binary[current_addr] = val & 0xFF
                        self.binary[current_addr+1] = (val >> 8) & 0xFF
                        current_addr += 2
                continue
            try:
                b = asm.assemble(line, current_addr)
                for byte in b:
                    self.binary[current_addr] = byte
                    current_addr += 1
            except Exception as e:
                print(f"Error assembling {line} at {hex(current_addr)}: {e}")
                sys.exit(1)

    def eval_value(self, s):
        if s.startswith('$'): return int(s[1:], 16)
        if s.startswith('%'): return int(s[1:], 2)
        if s in self.labels: return self.labels[s]
        try: return int(s)
        except: return 0

    def write_nes(self, filename):
        header = bytearray([0x4E, 0x45, 0x53, 0x1A, 2, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        prg = self.binary[0x8000:0x10000]
        try:
            with open('trolley_game/assets/trolley.chr', 'rb') as f:
                chr_data = f.read()
        except:
            print("CHR not found")
            chr_data = bytearray(8192)
        with open(filename, 'wb') as f:
            f.write(header)
            f.write(prg)
            f.write(chr_data)

def create_source():
    source = []
    # Manually escaped $ for heredoc
    source.append("PPUCTRL=$2000")
    source.append("PPUMASK=$2001")
    source.append("PPUSTATUS=$2002")
    source.append("OAMADDR=$2003")
    source.append("OAMDATA=$2004")
    source.append("PPUSCROLL=$2005")
    source.append("PPUADDR=$2006")
    source.append("PPUDATA=$2007")
    source.append("APUCTRL=$4015")
    source.append("JOY1=$4016")
    source.append("JOY2=$4017")

    source.append("Buttons=$00")
    source.append("TrainX=$01")
    source.append("TrainY=$02")
    source.append("ScrollY=$03")
    source.append("FrameCount=$04")
    source.append("NmiReady=$05")

    source.append(".org $8000")

    def read_file(fname):
        with open(fname, 'r') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip().replace(', ', ',')
            if not line or line.startswith(';'): continue
            if ';' in line: line = line[:line.index(';')]
            line = line.strip().replace(', ', ',')

            if line.startswith('.'):
                if line.startswith('.byte') or line.startswith('.word'):
                    source.append(line)
                continue
            if line.startswith('.include'): continue
            if '.res' in line: continue
            if 'segment' in line: continue # Extra safety

            # If definition, append it
            if '=' in line:
                source.append(line)
                continue

            if line.endswith(':'):
                source.append(line)
            else:
                source.append(line)

    read_file('trolley_game/src/reset.s')
    read_file('trolley_game/src/main.s')

    source.append(".org $FFFA")
    source.append(".word NMI")
    source.append(".word Reset")
    source.append(".word IRQ")
    return source

if __name__ == '__main__':
    lines = create_source()
    asm = SimpleAssembler()
    asm.parse_lines(lines)

    print("Resolving labels...")
    for i in range(20):
        stable = asm.assemble_pass()
        if stable:
            print(f"Converged after {i+1} passes.")
            break
    else:
        print("Warning: Did not converge.")

    print("Emitting code...")
    asm.emit_code()
    asm.write_nes('trolley_game/trolley.nes')
    print("Done.")
