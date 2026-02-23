.segment "HEADER"
    .byte $4E, $45, $53, $1A ; "NES" + EOF
    .byte 2                    ; PRG-ROM (32KB)
    .byte 1                    ; CHR-ROM (8KB)
    .byte $00                 ; Mapper 0, Horizontal Mirroring (Vertical Arrangement)
    .byte $00                 ; Mapper 0
    .byte $00, $00, $00, $00, $00, $00, $00, $00 ; Padding
