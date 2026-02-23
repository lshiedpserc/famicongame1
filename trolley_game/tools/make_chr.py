import struct

def make_tile(pattern_lines):
    # pattern_lines is a list of 8 strings like "........" or "XX..XX.."
    # . = 00, X = 01 (color 1), O = 10 (color 2), # = 11 (color 3)
    p0 = []
    p1 = []
    for line in pattern_lines:
        byte0 = 0
        byte1 = 0
        for i, char in enumerate(line):
            val = 0
            if char == '.': val = 0
            elif char == 'X': val = 1
            elif char == 'O': val = 2
            elif char == '#': val = 3

            if val & 1:
                byte0 |= (1 << (7 - i))
            if val & 2:
                byte1 |= (1 << (7 - i))
        p0.append(byte0)
        p1.append(byte1)
    return bytes(p0 + p1)

# Define patterns
empty = ["........"] * 8

track_v = [
    ".X....X.",
    ".X....X.",
    ".X....X.",
    ".X....X.",
    ".X....X.",
    ".X....X.",
    ".X....X.",
    ".X....X."
]

track_l = [ # Turn Left
    "........",
    ".......X",
    "......X.",
    ".....X..",
    "....X...",
    "...X....",
    "..X.....",
    ".X......"
] # Simplified diagonal

track_r = [ # Turn Right
    "........",
    "X.......",
    ".X......",
    "..X.....",
    "...X....",
    "....X...",
    ".....X..",
    "......X."
]

fork = [
    ".X....X.",
    ".X...X..",
    ".X..X...",
    ".X.X....",
    ".XX.....",
    ".X.X....",
    ".X..X...",
    ".X...X.."
]

hole = [
    "........",
    ".OOOOOO.",
    "OOOOOOOO",
    "OOOOOOOO",
    "OOOOOOOO",
    "OOOOOOOO",
    ".OOOOOO.",
    "........"
]

ground = [
    "........",
    "..#.....",
    ".....#..",
    ".#......",
    "......#.",
    "..#.....",
    ".....#..",
    "........"
]

# Train (2x2 tiles)
train_tl = [
    "..XXXXX.",
    ".XOOXOXX",
    "XOOOOOOX",
    "XOOOOOOX",
    "XOOOOOOX",
    "XOOOOOOX",
    "XOOOOOOX",
    "XOOOOOOX"
]

train_tr = train_tl # reused for now

robot = [
    "........",
    "...##...",
    "..#OO#..",
    "..#OO#..",
    "...##...",
    "..####..",
    ".#....#.",
    "........"
]

# Generate tiles
tiles = []
# Background Bank (0-255)
tiles.append(make_tile(empty)) # 0
tiles.append(make_tile(track_v)) # 1
tiles.append(make_tile(track_l)) # 2
tiles.append(make_tile(track_r)) # 3
tiles.append(make_tile(fork))    # 4
tiles.append(make_tile(hole))    # 5
tiles.append(make_tile(ground))  # 6

# Fill rest of BG bank with empty
while len(tiles) < 256:
    tiles.append(make_tile(empty))

# Sprite Bank (256-511)
# Train sprites at index 0 in sprite bank (tile 256 total index)
tiles.append(make_tile(train_tl)) # 0
tiles.append(make_tile(train_tr)) # 1
tiles.append(make_tile(train_tl)) # 2
tiles.append(make_tile(train_tr)) # 3
tiles.append(make_tile(robot))    # 4

# Fill rest
while len(tiles) < 512:
    tiles.append(make_tile(empty))

with open("trolley_game/assets/trolley.chr", "wb") as f:
    for t in tiles:
        f.write(t)

print("Generated trolley.chr")
