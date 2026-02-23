import sys
import re
from py65.assembler import Assembler
from py65.devices.mpu6502 import MPU

# Directives
# .org $XXXX
# .byte $XX, ...
# .word $XXXX, ...
# .include "filename"
# .incbin "filename" (for CHR)
# label:
# name = value

class SimpleAssembler:
    def __init__(self):
        self.mpu = MPU()
        self.labels = {}
        self.pc = 0
        self.lines = []
        self.binary = bytearray(65536) # Full 64k map
        self.used_map = [False] * 65536
        self.min_addr = 65536
        self.max_addr = 0
        self.ines_header = bytearray()

    def parse_file(self, filename):
        with open(filename, 'r') as f:
            raw_lines = f.readlines()

        # Flatten includes
        flattened = []
        for line in raw_lines:
            line = line.strip()
            # Remove comments
            if ';' in line:
                line = line[:line.index(';')]
            line = line.strip()

            if not line:
                continue

            if line.startswith('.include'):
                # parse filename
                m = re.match(r'\.include\s+"([^"]+)"', line)
                if m:
                    inc_file = m.group(1)
                    # path relative to current file? Assume relative to project root or src
                    # Try src/ + filename or just filename
                    try:
                        with open(inc_file, 'r') as inc:
                             # Recursively parse? Or just read?
                             # Let's just read simple includes (macros/consts)
                             # Better: recursively call parse_file logic, but return lines
                             flattened.extend(self.read_include(inc_file))
                    except FileNotFoundError:
                        try:
                            with open('trolley_game/src/' + inc_file, 'r') as inc:
                                flattened.extend(self.read_include('trolley_game/src/' + inc_file))
                        except:
                            print(f"Could not find include {inc_file}")
                            sys.exit(1)
                else:
                    print(f"Invalid include: {line}")
            else:
                flattened.append(line)
        return flattened

    def read_include(self, filename):
        lines = []
        with open(filename, 'r') as f:
            for line in f:
                line = line.strip()
                if ';' in line: line = line[:line.index(';')]
                line = line.strip()
                if line:
                    lines.append(line)
        return lines

    def pass1(self, lines):
        # Scan labels and calculate addresses
        self.pc = 0
        # Pre-scan for assignments
        for line in lines:
            if '=' in line and not line.startswith('.'):
                parts = line.split('=')
                name = parts[0].strip()
                val_str = parts[1].strip()
                # Parse value
                val = self.parse_value(val_str)
                self.labels[name] = val

        # Estimate PC
        current_pc = 0

        # Fill labels with dummy if not exists
        # We need to know which are labels.
        for line in lines:
            if line.endswith(':'):
                label = line[:-1]
                self.labels[label] = 0xFFFF # Dummy for now

        for line in lines:
            if line.endswith(':'):
                label = line[:-1]
                self.labels[label] = current_pc
                continue

            if '=' in line: continue

            if line.startswith('.'):
                if line.startswith('.org'):
                    parts = line.split()
                    current_pc = self.parse_value(parts[1])
                elif line.startswith('.byte'):
                    # count args
                    args = line[5:].split(',')
                    current_pc += len(args)
                elif line.startswith('.word'):
                    args = line[5:].split(',')
                    current_pc += len(args) * 2
                elif line.startswith('.incbin'):
                    # read file size
                    m = re.match(r'\.incbin\s+"([^"]+)"', line)
                    if m:
                        fname = m.group(1)
                        # adjust path
                        if fname.startswith('../'): fname = 'trolley_game/' + fname[3:]
                        try:
                            with open(fname, 'rb') as f:
                                content = f.read()
                                current_pc += len(content)
                        except:
                            pass # Fail later
                continue

            # Instruction
            # Estimate size
            # Try to assemble with dummy labels
            asm = Assembler(self.mpu)
            # We need to inject our labels into assembler?
            # py65 Assembler doesn't take labels dict easily in constructor for some versions?
            # Actually AddressParser does.
            # But let's just try to guess size.

            parts = line.split()
            mnemonic = parts[0].lower()

            # Branches: 2 bytes
            if mnemonic in ['bpl','bmi','bvc','bvs','bcc','bcs','bne','beq']:
                current_pc += 2
                continue

            # Brk, php, pha, etc (implied): 1 byte
            if len(parts) == 1:
                current_pc += 1
                continue

            # Others: 2 or 3 bytes.
            # If operand is #, 2 bytes.
            # If operand is zpg, 2 bytes.
            # If operand is abs, 3 bytes.
            operand = line[len(mnemonic):].strip()
            if operand.startswith('#'):
                current_pc += 2
            elif operand.startswith('('): # Indirect
                current_pc += 3
            else:
                # Could be ZP or ABS.
                # If label, we assumed 0xFFFF -> ABS -> 3 bytes.
                # If number < 256 -> 2 bytes.
                val = self.try_parse_value(operand)
                if val is not None and val < 256:
                    current_pc += 2
                else:
                    current_pc += 3

    def pass2(self, lines):
        # Real assembly
        self.pc = 0

        # Setup AddressParser with resolved labels
        from py65.utils.addressing import AddressParser
        ap = AddressParser(labels=self.labels)
        asm = Assembler(self.mpu, address_parser=ap)

        for line in lines:
            if line.endswith(':'):
                continue # Label already resolved

            if '=' in line: continue

            if line.startswith('.'):
                if line.startswith('.org'):
                    parts = line.split()
                    self.pc = self.parse_value(parts[1])
                elif line.startswith('.byte'):
                    args = line[5:].split(',')
                    for arg in args:
                        val = self.parse_value(arg.strip())
                        self.emit(val)
                elif line.startswith('.word'):
                    args = line[5:].split(',')
                    for arg in args:
                        val = self.parse_value(arg.strip())
                        self.emit(val & 0xFF)
                        self.emit((val >> 8) & 0xFF)
                elif line.startswith('.incbin'):
                    m = re.match(r'\.incbin\s+"([^"]+)"', line)
                    if m:
                        fname = m.group(1)
                        if fname.startswith('../'): fname = 'trolley_game/' + fname[3:]
                        with open(fname, 'rb') as f:
                            content = f.read()
                            for b in content:
                                self.emit(b)
                continue

            # Instruction
            try:
                # py65 doesn't like 'lda #' sometimes? It expects 'lda #' or similar?
                # It handles it.
                # However, it might pick ZP addressing for labels if value < 256.
                # If we assumed ABS in pass 1 (3 bytes) and it generates ZP (2 bytes), offsets shift!
                # IMPORTANT: We must enforce size or ensure consistency.
                # If label < 256, Pass 1 saw it as 2 bytes?
                # No, Pass 1 used dummy 0xFFFF -> 3 bytes.
                # So if label ends up being < 256, we have a mismatch.
                # Simple fix: Force everything to ABS if possible?
                # Or just re-run Pass 1 with resolved labels?
                # Yes! Multi-pass.
                pass

                # Let's trust assemble()
                # But we need to handle branch offsets manually if py65 fails on them with custom labels?
                # AddressParser handles labels for values.
                # Branch instructions in py65 expect relative offset or absolute target?
                # They expect target address and calculate offset.

                # Check for branch
                parts = line.split()
                mnemonic = parts[0].lower()
                if mnemonic in ['bpl','bmi','bvc','bvs','bcc','bcs','bne','beq']:
                     # py65 might output 2 bytes.
                     # ensure we only emit 2 bytes.
                     pass

                # Assemble
                # We need to normalize the line for py65?
                # 'lda Buttons' -> 'lda -bash0'

                bytes_list = asm.assemble(line, self.pc)
                for b in bytes_list:
                    self.emit(b)

            except Exception as e:
                print(f"Error assembling '{line}' at {hex(self.pc)}: {e}")
                sys.exit(1)

    def emit(self, byte):
        if 0 <= self.pc < 65536:
            self.binary[self.pc] = byte
            self.used_map[self.pc] = True
            if self.pc < self.min_addr: self.min_addr = self.pc
            if self.pc > self.max_addr: self.max_addr = self.pc
        self.pc += 1

    def parse_value(self, s):
        s = s.strip()
        if s.startswith('$'):
            return int(s[1:], 16)
        if s.startswith('%'):
            return int(s[1:], 2)
        if s in self.labels:
            return self.labels[s]
        try:
            return int(s)
        except:
            return 0 # Should fail?

    def try_parse_value(self, s):
        try:
            return self.parse_value(s)
        except:
            return None

    def write_nes(self, filename):
        # Construct NES ROM
        # Header (16 bytes)
        # PRG (32KB) -> 000-
        # CHR (8KB) -> Appended?

        # We need to know where CHR is.
        # In my code, I put CHR in .segment "CHARS" which likely isn't used here.
        # I should just append CHR file data at the end.

        # Fetch PRG data
        # NROM: 32KB PRG.
        # We need to grab bytes from 000 to .
        prg_data = self.binary[0x8000:0x10000]

        # Header
        # NES + 1A
        header = bytearray([0x4E, 0x45, 0x53, 0x1A])
        header.append(2) # 32KB PRG
        header.append(1) # 8KB CHR
        header.append(1) # Mapper 0, Vertical Mirroring
        header.append(0)
        header.extend([0]*8)

        with open(filename, 'wb') as f:
            f.write(header)
            f.write(prg_data)
            # Append CHR
            try:
                with open('trolley_game/assets/trolley.chr', 'rb') as chr_file:
                    f.write(chr_file.read())
            except:
                print("Warning: trolley.chr not found, using empty CHR")
                f.write(bytearray(8192))

if __name__ == '__main__':
    assembler = SimpleAssembler()
    lines = assembler.parse_file('trolley_game/src/main_flat.s') # We will create this

    # Multipass to resolve labels correctly
    assembler.pass1(lines) # Initial guess
    assembler.pass1(lines) # Refine with known labels
    assembler.pass2(lines) # Final emit

    assembler.write_nes('trolley_game/trolley.nes')
    print("Built trolley_game/trolley.nes")
