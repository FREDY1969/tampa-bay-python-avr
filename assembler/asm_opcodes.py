# asm_opcodes.py

from asm_inst import *

# Arithmetic and logic instructions
ADD = inst1('ADD', '0000 11rd dddd rrrr', 1)
ADC = inst1('ADC', '0001 11rd dddd rrrr', 1)
ADIW = inst1('ADIW', '1001 0110 KKdd KKKK', 2)
SUB = inst1('SUB', '0001 10rd dddd rrrr', 1)
SUBI = inst1('SUBI', '0101 KKKK dddd KKKK', 1, d=(16,31))
SBC = inst1('SBC', '0000 10rd dddd rrrr', 1)
SBCI = inst1('SBCI', '0100 KKKK dddd KKKK', 1, d=(16,31))
SBIW = inst1('SBIW', '1001 0111 KKdd KKKK', 2, d=(24,30))
AND = inst1('AND', '0010 00rd dddd rrrr', 1)
ANDI = inst1('ANDI', '0111 KKKK dddd KKKK', 1, d=(16,31))
OR = inst1('OR', '0010 10rd dddd rrrr', 1)
ORI = inst1('ORI', '0110 KKKK dddd KKKK', 1, d=(16,31))
EOR = inst1('EOR', '0010 01rd dddd rrrr', 1)
COM = inst1('COM', '1001 010d dddd 0000', 1)
NEG = inst1('NEG', '1001 010d dddd 0001', 1)
SBR = inst1('SBR', '0110 KKKK dddd KKKK', 1, d=(16,31))
CBR = inst1('CBR', '0111 KKKK dddd KKKK', 1, d=(16,31), K='~')
INC = inst1('INC', '1001 010d dddd 0011', 1)
DEC = inst1('DEC', '1001 010d dddd 1010', 1)
TST = inst1('TST', '0010 00Dd dddd DDDD', 1, D='d')
CLR = inst1('CLR', '0010 01Dd dddd DDDD', 1, D='d')
SER = inst1('SER', '1110 1111 dddd 1111', 1, d=(16,31))
MUL = inst1('MUL', '1001 11rd dddd rrrr', 2)
MULS = inst1('MULS', '0000 0010 dddd rrrr', 2, d=(16,31), r=(16,31))
MULSU = inst1('MULSU', '0000 0011 0ddd 0rrr', 2, d=(16,23), r=(16,23))
FMUL = inst1('FMUL', '0000 0011 0ddd 1rrr', 2, d=(16,23), r=(16,23))
FMULS = inst1('FMULS', '0000 0011 1ddd 0rrr', 2, d=(16,23), r=(16,23))
FMULSU = inst1('FMULSU', '0000 0011 1ddd 1rrr', 2, d=(16,23), r=(16,23))

# Branch instructions
RJMP = inst1('RJMP', '1100 kkkk kkkk kkkk', 2, k=(-2048,2047))
IJMP = inst1('IJMP', '1001 0100 0000 1001', 2)
JMP = inst2('JMP', '1001 010k kkkk 110k kkkk kkkk kkkk kkkk', 3)
RCALL = inst1('RCALL', '1101 kkkk kkkk kkkk', 3, k=(-2048,2047))
ICALL = inst1('ICALL', '1001 0101 0000 1001', 3)
CALL = inst2('CALL', '1001 010k kkkk 111k kkkk kkkk kkkk kkkk', 4)
RET = inst1('RET', '1001 0101 0000 1000', 4)
RETI = inst1('RETI', '1001 0101 0001 1000', 4)
CPSE = inst1('CPSE', '0001 00rd dddd rrrr', (1,2,3))
CP = inst1('CP', '0001 01rd dddd rrrr', 1)
CPC = inst1('CPC', '0000 01rd dddd rrrr', 1)
CPI = inst1('CPI', '0011 KKKK dddd KKKK', 1, d=(16,31))
SBRC = inst1('SBRC', '1111 110r rrrr 0bbb', (1,2,3))
SBRS = inst1('SBRS', '1111 111r rrrr 0bbb', (1,2,3))
SBIC = inst1('SBIC', '1001 1001 AAAA Abbb', (1,2,3))
SBIS = inst1('SBIS', '1001 1011 AAAA Abbb', (1,2,3))
BRBS = inst1('BRBS', '1111 00kk kkkk ksss', (1, 2), k=(-64,63))
BRBC = inst1('BRBC', '1111 01kk kkkk ksss', (1, 2), k=(-64,63))
BREQ = inst1('BREQ', '1111 00kk kkkk k001', (1, 2), k=(-64,63))
BRNE = inst1('BRNE', '1111 01kk kkkk k001', (1, 2), k=(-64,63))
BRCS = inst1('BRCS', '1111 00kk kkkk k000', (1, 2), k=(-64,63))
BRCC = inst1('BRCC', '1111 01kk kkkk k000', (1, 2), k=(-64,63))
BRSH = inst1('BRSH', '1111 01kk kkkk k000', (1, 2), k=(-64,63))
BRLO = inst1('BRLO', '1111 00kk kkkk k000', (1, 2), k=(-64,63))
BRMI = inst1('BRMI', '1111 00kk kkkk k010', (1, 2), k=(-64,63))
BRPL = inst1('BRPL', '1111 01kk kkkk k010', (1, 2), k=(-64,63))
BRGE = inst1('BRGE', '1111 01kk kkkk k100', (1, 2), k=(-64,63))
BRLT = inst1('BRLT', '1111 00kk kkkk k100', (1, 2), k=(-64,63))
BRHS = inst1('BRHS', '1111 00kk kkkk k101', (1, 2), k=(-64,63))
BRHC = inst1('BRHC', '1111 01kk kkkk k101', (1, 2), k=(-64,63))
BRTS = inst1('BRTS', '1111 00kk kkkk k110', (1, 2), k=(-64,63))
BRTC = inst1('BRTC', '1111 01kk kkkk k110', (1, 2), k=(-64,63))
BRVS = inst1('BRVS', '1111 00kk kkkk k011', (1, 2), k=(-64,63))
BRVC = inst1('BRVC', '1111 01kk kkkk k011', (1, 2), k=(-64,63))
BRIE = inst1('BRIE', '1111 00kk kkkk k111', (1, 2), k=(-64,63))
BRID = inst1('BRID', '1111 01kk kkkk k111', (1, 2), k=(-64,63))

# Bit and bit-test instructions
SBI = inst1('SBI', '1001 1010 AAAA Abbb', 2)
CBI = inst1('CBI', '1001 1000 AAAA Abbb', 2)
LSL = inst1('LSL', '0000 11Dd dddd DDDD', 1, D='d')
LSR = inst1('LSR', '1001 010d dddd 0110', 1)
ROL = inst1('ROL', '0001 11Dd dddd DDDD', 1, D='d')
ROR = inst1('ROR', '1001 010d dddd 0111', 1)
ASR = inst1('ASR', '1001 010d dddd 0101', 1)
SWAP = inst1('SWAP', '1001 010d dddd 0010', 1)
BSET = inst1('BSET', '1001 0100 0sss 1000', 1)
BCLR = inst1('BCLR', '1001 0100 1sss 1000', 1)
BST = inst1('BST', '1111 101d dddd 0bbb', 1)
BLD = inst1('BLD', '1111 100d dddd 0bbb', 1)
SEC = inst1('SEC', '1001 0100 0000 1000', 1)
CLC = inst1('CLC', '1001 0100 1000 1000', 1)
SEN = inst1('SEN', '1001 0100 0010 1000', 1)
CLN = inst1('CLN', '1001 0100 1010 1000', 1)
SEZ = inst1('SEZ', '1001 0100 0001 1000', 1)
CLZ = inst1('CLZ', '1001 0100 1001 1000', 1)
SEI = inst1('SEI', '1001 0100 0111 1000', 1)
CLI = inst1('CLI', '1001 0100 1111 1000', 1)
SES = inst1('SES', '1001 0100 0100 1000', 1)
CLS = inst1('CLS', '1001 0100 1100 1000', 1)
SEV = inst1('SEV', '1001 0100 0011 1000', 1)
CLV = inst1('CLV', '1001 0100 1011 1000', 1)
SET = inst1('SET', '1001 0100 0110 1000', 1)
CLT = inst1('CLT', '1001 0100 1110 1000', 1)
SEH = inst1('SEH', '1001 0100 0101 1000', 1)
CLH = inst1('CLH', '1001 0100 1101 1000', 1)

# Data transfer instructions
MOV = inst1('MOV', '0010 11rd dddd rrrr', 1)
MOVW = inst1('MOVW', '0000 0001 dddd rrrr', 1, d=(0,30), r=(0,30))
LDI = inst1('LDI', '1110 KKKK dddd KKKK', 1, d=(16,31))
LD = inst1('LD', '1001 000d dddd xxpp', 2) # x=11 for X, 10 for Y, 00 for Z
                                           # pp=00 no inc/dec
                                           #    01 post inc
                                           #    10 pre dec
LDD = inst1('LDD', '10q0 qq0d dddd yqqq', 2) # y=1 for Y, 0 for Z
LDS = inst2('LDS', '1001 000d dddd 0000 kkkk kkkk kkkk kkkk', 2)
ST = inst1('ST', '1001 001r rrrr xxpp', 2) # x=11 for X, 10 for Y, 00 for Z
                                           # pp=00 no inc/dec
                                           #    01 post inc
                                           #    10 pre dec
STD = inst1('STD', '10q0 qq1r rrrr yqqq', 2) # y=1 for Y, 0 for Z
STS = inst2('STS', '1001 001r rrrr 0000 kkkk kkkk kkkk kkkk', 2)
#LPM = inst1('LPM', '1001 0101 1100 1000', 3) # R0 implied
LPM = inst1('LPM', '1001 000d dddd 010p', 3) # pp=00 no inc/dec
                                             #    01 post inc
SPM = inst1('SPM', '1001 0101 1110 1000', None) # written with Z+ operand? no!
IN = inst1('IN', '1011 0AAd dddd AAAA', 1)
OUT = inst1('OUT', '1011 1AAr rrrr AAAA', 1)
PUSH = inst1('PUSH', '1001 001d dddd 1111', 2)
POP = inst1('POP', '1001 000d dddd 1111', 2)

# MCU control instructions
NOP = inst1('NOP', '0000 0000 0000 0000', 1)
SLEEP = inst1('SLEEP', '1001 0101 1000 1000', 1)
WDR = inst1('WDR', '1001 0101 1010 1000', 1)
BREAK = inst1('BREAK', '1001 0101 1001 1000', 1)

