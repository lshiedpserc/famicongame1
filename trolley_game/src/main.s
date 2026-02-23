.include "nes.inc"

.segment "ZEROPAGE"
Buttons: .res 1
TrainX:  .res 1
TrainY:  .res 1
ScrollY: .res 1
FrameCount: .res 1
NmiReady: .res 1

.segment "BSS"

.segment "CODE"
.export Main, NMI, IRQ

; ---------------------------------------------------------------------------
; Palette Data
; ---------------------------------------------------------------------------
PaletteData:
    ; Background Palette
    .byte $0F, $00, $10, $20 ; Black, Grey, Light Grey, White (Track)
    .byte $0F, $06, $16, $26 ; Black, Red, Light Red, White (Hazard)
    .byte $0F, $00, $10, $20
    .byte $0F, $00, $10, $20

    ; Sprite Palette
    .byte $0F, $11, $21, $31 ; Black, Blue, Light Blue, White (Train)
    .byte $0F, $16, $26, $36 ; Black, Red, Light Red, White (Robot)
    .byte $0F, $00, $10, $20
    .byte $0F, $00, $10, $20

; ---------------------------------------------------------------------------
; Main Entry Point
; ---------------------------------------------------------------------------
Main:
    lda #$00
    sta PPUCTRL   ; Disable NMI
    sta PPUMASK   ; Disable Rendering

    ; Load Palettes
    bit PPUSTATUS
    lda #$3F
    sta PPUADDR
    lda #$00
    sta PPUADDR

    ldx #$00
LoadPal:
    lda PaletteData, x
    sta PPUDATA
    inx
    cpx #$20
    bne LoadPal

    ; Clear Nametable (Fill with Tile 0)
    lda #$20
    sta PPUADDR
    lda #$00
    sta PPUADDR

    lda #$00 ; Empty Tile
    ldx #$00
    ldy #$00
ClearNT:
    sta PPUDATA
    inx
    bne ClearNT
    iny
    cpy #$04 ; 4 pages = 1KB (one nametable)
    bne ClearNT

    ; Init Variables
    lda #$80
    sta TrainX
    lda #$C8
    sta TrainY
    lda #$00
    sta ScrollY
    sta FrameCount
    sta NmiReady

    ; Enable NMI and Rendering
    lda #%10001000 ; NMI on, BG pattern 0, Sprite pattern 1
    sta PPUCTRL
    lda #%00011110 ; Enable Sprites, BG, Left Column
    sta PPUMASK

GameLoop:
    ; Wait for NMI
    lda NmiReady
    beq GameLoop
    lda #$00
    sta NmiReady

    ; --- Logic ---
    jsr ReadJoypad

    ; Move Train
    lda Buttons
    and #%00000001 ; Right (Bit 0)
    beq CheckLeft
    inc TrainX
CheckLeft:
    lda Buttons
    and #%00000010 ; Left (Bit 1)
    beq DoneMove
    dec TrainX
DoneMove:

    ; Scroll (Simple)
    ; inc ScrollY

    ; --- Update OAM Buffer (Shadow OAM at $0200) ---
    lda TrainY
    sta $0200 ; Y
    lda #$00  ; Tile Index (Train Top-Left)
    sta $0201
    lda #$00  ; Attributes (Palette 0)
    sta $0202
    lda TrainX
    sta $0203 ; X

    jmp GameLoop

; ---------------------------------------------------------------------------
; NMI Handler
; ---------------------------------------------------------------------------
NMI:
    pha
    txa
    pha
    tya
    pha

    ; DMA OAM
    lda #$00
    sta OAMADDR
    lda #$02
    sta $4014 ; OAM DMA from $0200

    ; Set Scroll
    lda #$00
    sta PPUSCROLL ; X Scroll
    lda ScrollY
    sta PPUSCROLL ; Y Scroll

    ; Enable Rendering again
    lda #%10001000
    sta PPUCTRL
    lda #%00011110
    sta PPUMASK

    inc FrameCount
    lda #$01
    sta NmiReady

    pla
    tay
    pla
    tax
    pla
    rti

; ---------------------------------------------------------------------------
; IRQ Handler
; ---------------------------------------------------------------------------
IRQ:
    rti

; ---------------------------------------------------------------------------
; Subroutines
; ---------------------------------------------------------------------------
ReadJoypad:
    lda #$01
    sta JOY1
    lda #$00
    sta JOY1 ; Strobe

    ldx #$08
ReadLoop:
    lda JOY1
    lsr A       ; Bit 0 -> Carry
    rol Buttons ; Carry -> Bit 0 (Shift Left)
    dex
    bne ReadLoop
    rts

.segment "VECTORS"
    .word NMI
    .word Reset
    .word IRQ
