.include "nes.inc"
.import Main
.include "nes.inc" ; Need to define registers or use raw addresses

.segment "CODE"
.export Reset

Reset:
    sei         ; Disable IRQs
    cld         ; Disable decimal mode
    ldx #$40
    stx $4017  ; Disable APU frame IRQ
    ldx #$FF
    txs         ; Set stack pointer
    inx         ; X = 0
    stx $2000  ; Disable NMI
    stx $2001  ; Disable rendering
    stx $4010  ; Disable DMC IRQs

vblankwait1:
    bit $2002
    bpl vblankwait1

clrmem:
    lda #$00
    sta $00,x
    sta $0100,x
    sta $0300,x
    sta $0400,x
    sta $0500,x
    sta $0600,x
    sta $0700,x
    lda #$FE
    sta $0200,x ; Move sprites off screen
    inx
    bne clrmem

vblankwait2:
    bit $2002
    bpl vblankwait2

    jmp Main
