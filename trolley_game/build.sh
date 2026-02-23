#!/bin/bash
mkdir -p obj
if ! command -v ca65 &> /dev/null; then
    echo "Error: ca65 not found. Please install cc65 toolchain."
    exit 1
fi
ca65 src/header.s -o obj/header.o || exit 1
ca65 src/reset.s -o obj/reset.o -I src || exit 1
ca65 src/main.s -o obj/main.o -I src || exit 1
ld65 -C cfg/nrom.cfg -o trolley.nes obj/header.o obj/reset.o obj/main.o || exit 1
echo "Build success! trolley.nes created."
