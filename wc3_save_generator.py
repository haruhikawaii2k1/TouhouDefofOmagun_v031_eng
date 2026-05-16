#!/usr/bin/env python3
"""
WC3 Save Code Generator — tái tạo hoàn chỉnh từ JASS đã deobfuscate.

Cách dùng:
    python wc3_save_generator.py <tên_player> <chỉ_số> [--players N]
    python wc3_save_generator.py Dragon 1250
    python wc3_save_generator.py Dragon 1250 --verify AB7S6I4K4
    python wc3_save_generator.py --decode AB7S6I4K4 --name Dragon

Nguồn gốc các bảng: tái tạo từ War3map.j bằng jass_deobfuscator.py
    Trigger O156030 → Bảng 1 (vị trí 3 trong chuỗi seed)
    Trigger O154606 → Bảng 2 (vị trí 4)
    Trigger O156716 → Bảng 3 (vị trí 5)
    Trigger O153840 → Bảng 4 (vị trí 6)
    Trigger O151805 → Bảng 5 (vị trí 7)
    Trigger O155499 → Bảng 6 (vị trí 8)
    Trigger O152820 → Bảng 7 (vị trí 9)
"""

import argparse
import sys

# ─────────────────────────────────────────────────────────────
# 7 Bảng mã hóa: digit (0-9) → ký tự
# Đọc từ các function O151805, O152820, ..., O156030, O156716
# Thứ tự trong mỗi bảng: digit 0,1,2,...,9
# ─────────────────────────────────────────────────────────────
ENCODE_TABLES = [
    # Bảng 1 — O156030 (TriggerExecute O52842, vị trí 3 của seed)
    # O156010=0→'7', O155960=1→'6', O155926=2→'8', O155854=3→'S',
    # O155771=4→'W', O155756=5→'A', O155742=6→'T', O155627=7→'1',
    # O155608=8→'2', O155586=9→'4'
    {0:'7', 1:'2', 2:'8', 3:'S', 4:'W', 5:'A', 6:'T', 7:'1', 8:'6', 9:'4'},

    # Bảng 2 — O154606 (TriggerExecute O52779, vị trí 4)
    # O154503=0→'5', O154486=1→'U', O154428=2→'6', O154401=3→'I',
    # O154337=4→'8', O154218=5→'O', O154158=6→'L', O154047=7→'J',
    # O154024=8→'F', O153968=9→'E'
    {0:'5', 1:'U', 2:'6', 3:'I', 4:'8', 5:'O', 6:'L', 7:'J', 8:'F', 9:'E'},

    # Bảng 3 — O156716 (TriggerExecute O52968, vị trí 5)
    # O156695=0→'8', O156614=1→'4', O156523=2→'F', O156423=3→'6',
    # O156407=4→'9', O156332=5→'I', O156300=6→'3', O156201=7→'5',
    # O156145=8→'B', O156098=9→'S'
    {0:'8', 1:'4', 2:'F', 3:'6', 4:'9', 5:'I', 6:'3', 7:'5', 8:'B', 9:'S'},

    # Bảng 4 — O153840 (TriggerExecute O52698, vị trí 6)
    # O153788=0→'7', O153682=1→'T', O153632=2→'2', O153586=3→'D',
    # O153465=4→'3', O153380=5→'F', O153310=6→'1', O153218=7→'G',
    # O153120=8→'9', O153014=9→'H'
    {0:'7', 1:'T', 2:'2', 3:'D', 4:'3', 5:'F', 6:'1', 7:'G', 8:'9', 9:'H'},

    # Bảng 5 — O151805 (TriggerExecute O52597, vị trí 7)
    # O151770=0→'Y', O151672=1→'S', O151566=2→'G', O151526=3→'H',
    # O151465=4→'M', O151425=5→'C', O151309=6→'O', O151298=7→'P',
    # O151285=8→'Q', O151192=9→'B'
    {0:'Y', 1:'S', 2:'G', 3:'H', 4:'M', 5:'C', 6:'O', 7:'P', 8:'Q', 9:'B'},

    # Bảng 6 — O155499 (TriggerExecute O52804, vị trí 8)
    # O155429=0→'K', O155379=1→'3', O155284=2→'S', O155213=3→'8',
    # O155154=4→'Y', O155107=5→'2', O155083=6→'O', O155006=7→'4',
    # O154901=8→'P', O154781=9→'6'
    {0:'K', 1:'3', 2:'S', 3:'8', 4:'Y', 5:'2', 6:'O', 7:'4', 8:'P', 9:'6'},

    # Bảng 7 — O152820 (TriggerExecute O52672, vị trí 9)
    # O152699=0→'4', O152584=1→'G', O152580=2→'8', O152565=3→'A',
    # O152446=4→'C', O152324=5→'Z', O152299=6→'X', O152231=7→'V',
    # O152124=8→'N', O152017=9→'M'
    {0:'4', 1:'G', 2:'8', 3:'A', 4:'C', 5:'Z', 6:'X', 7:'V', 8:'N', 9:'M'},
]

# Bảng nghịch: ký tự → digit (dùng để decode)
DECODE_TABLES = [
    {v: k for k, v in table.items()} for table in ENCODE_TABLES
]

# Thứ tự hoán vị (1-based → 0-based): vị trí output[i] = input[perm[i]]
# set O122898 = pos5, pos8, pos2, pos4, pos7, pos1, pos6, pos9, pos3
PERMUTATION = [4, 7, 1, 3, 6, 0, 5, 8, 2]  # 0-based

# Nghịch hoán vị: để decode biết pos gốc nào → pos output nào
INVERSE_PERM = [0] * 9
for out_i, in_i in enumerate(PERMUTATION):
    INVERSE_PERM[in_i] = out_i


# ─────────────────────────────────────────────────────────────
# Điều kiện hợp lệ (O148227): cần >=2 player đang chơi
# Ở đây bỏ qua, giả sử luôn hợp lệ
# ─────────────────────────────────────────────────────────────

def get_prefix(name: str) -> str:
    """
    Lấy 2 ký tự prefix từ tên player.
    O122895 = char[1] + char[3] của tên viết hoa.
    JASS dùng 1-based index.
    """
    upper = name.upper()
    c1 = upper[0] if len(upper) >= 1 else 'X'
    c3 = upper[2] if len(upper) >= 3 else 'X'
    return c1 + c3


def pad_index(index: int) -> str:
    """
    Ghép padding + chỉ số thành chuỗi 5 ký tự.
    Tái tạo logic if/else O148743..O148365.
    """
    if index <= 9:
        return f"0000{index}"       # O148743: <=9
    elif index <= 99:
        return f"000{index}"        # O148630: <=99
    elif index <= 999:
        return f"00{index}"         # O148568: <=999
    elif index <= 9999:
        return f"0{index}"          # O148484: <=9999
    elif index <= 99999:
        return f"{index}"           # O148365: <=99999
    else:
        return "99999"              # overflow


def compute_checksum(seed: str) -> str:
    """
    Tính checksum = tổng 5 chữ số từ vị trí 3→7 (1-based) của seed.
    O117113 = S2I(pos3) + S2I(pos4) + S2I(pos5) + S2I(pos6) + S2I(pos7)
    Trả về chuỗi 2 chữ số (có thể có leading zero nếu <=9).
    """
    total = sum(int(seed[i]) for i in range(2, 7))  # 0-based: 2..6
    if total <= 9:      # O148849: <=9 → thêm "0"
        return f"0{total}"
    return str(total)


def encode_digits(seed9: str) -> str:
    """
    Mã hóa 7 chữ số (vị trí 3→9, 1-based = index 2→8, 0-based) qua 7 bảng.
    Trả về chuỗi 9 ký tự: prefix(2) + 7 ký tự đã mã hóa.
    """
    prefix = seed9[:2]
    encoded = ""
    for table_i, digit_char in enumerate(seed9[2:9]):
        digit = int(digit_char)
        encoded += ENCODE_TABLES[table_i][digit]
    return prefix + encoded


def permute(s9: str) -> str:
    """
    Hoán vị 9 ký tự theo thứ tự [5,8,2,4,7,1,6,9,3] (1-based).
    = [4,7,1,3,6,0,5,8,2] (0-based).
    """
    return "".join(s9[i] for i in PERMUTATION)


def colorize(s: str) -> str:
    """
    Mô phỏng O148937: tô màu vàng ký tự nào KHÔNG phải chữ số 0-9.
    |CFFFFCC00 X |R
    """
    result = ""
    for ch in s:
        if ch.isdigit():
            result += ch
        else:
            result += f"|CFFFFCC00{ch}|R"
    return result


# ─────────────────────────────────────────────────────────────
# ENCODE: tên + chỉ số → password
# ─────────────────────────────────────────────────────────────

def generate(name: str, index: int, verbose: bool = False) -> str:
    prefix    = get_prefix(name)
    padded    = pad_index(index)
    seed7     = prefix + padded          # 7 ký tự
    checksum  = compute_checksum(seed7)
    seed9     = seed7 + checksum         # 9 ký tự

    if verbose:
        print(f"\n[ENCODE STEPS]")
        print(f"  Tên player   : {name!r}")
        print(f"  Prefix (1+3) : {prefix!r}")
        print(f"  Chỉ số       : {index}")
        print(f"  Sau padding  : {seed7!r}")
        print(f"  Checksum     : {checksum!r}  (tổng digits [{seed7[2:7]}] = {sum(int(c) for c in seed7[2:7])})")
        print(f"  Seed 9 ký tự : {seed9!r}")

    encoded9  = encode_digits(seed9)
    if verbose:
        print(f"  Sau mã hóa   : {encoded9!r}")
        for i, (d, ch) in enumerate(zip(seed9[2:], encoded9[2:])):
            print(f"    Bảng {i+1}: digit {d} → '{ch}'")

    final     = permute(encoded9)
    if verbose:
        print(f"  Sau hoán vị  : {final!r}")
        print(f"  Perm order   : {[i+1 for i in PERMUTATION]} (1-based)")

    return final


# ─────────────────────────────────────────────────────────────
# DECODE: password → (prefix, index) để xác minh
# ─────────────────────────────────────────────────────────────

def decode(password: str, verbose: bool = False) -> dict | None:
    if len(password) != 9:
        print(f"[ERROR] Password phải đúng 9 ký tự, nhận được {len(password)}")
        return None

    # Bước 1: đảo hoán vị
    unpermed = ["?"] * 9
    for out_i, in_i in enumerate(PERMUTATION):
        unpermed[in_i] = password[out_i]
    unpermed_str = "".join(unpermed)

    if verbose:
        print(f"\n[DECODE STEPS]")
        print(f"  Password     : {password!r}")
        print(f"  Đảo hoán vị : {unpermed_str!r}")

    # Bước 2: giải mã 7 ký tự
    prefix  = unpermed_str[:2]
    decoded_digits = ""
    for i, ch in enumerate(unpermed_str[2:9]):
        tbl = DECODE_TABLES[i]
        if ch not in tbl:
            print(f"[ERROR] Ký tự '{ch}' không hợp lệ trong bảng {i+1}")
            return None
        decoded_digits += str(tbl[ch])

    seed9 = prefix + decoded_digits
    if verbose:
        print(f"  Giải mã digit: {seed9!r}")

    # Bước 3: kiểm tra checksum
    # seed9[2:7] là 5 chữ số dữ liệu, seed9[7:9] là 2 chữ số checksum
    actual_checksum  = int(seed9[7:9])
    expected_sum     = sum(int(seed9[i]) for i in range(2, 7))
    if actual_checksum != expected_sum:
        print(f"[WARN] Checksum sai! Tính được {expected_sum}, trong code là {actual_checksum}")
    else:
        if verbose:
            print(f"  Checksum OK  : {actual_checksum} == {expected_sum}")

    # Bước 4: đọc chỉ số
    padded_index = seed9[2:7]
    index = int(padded_index)

    result = {
        "prefix":    prefix,
        "raw_index": padded_index,
        "index":     index,
        "checksum":  actual_checksum,
        "checksum_ok": actual_checksum == expected_sum,
    }

    if verbose:
        print(f"  Prefix       : {prefix!r}")
        print(f"  Chỉ số       : {index}")

    return result


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="WC3 Save Code Generator/Verifier"
    )
    parser.add_argument("name",  nargs="?", help="Tên player")
    parser.add_argument("index", nargs="?", type=int, help="Chỉ số (điểm/level/...)")
    parser.add_argument("--verify",  metavar="CODE", help="Xác minh password có đúng không")
    parser.add_argument("--decode",  metavar="CODE", help="Giải mã password (không cần tên)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Hiện chi tiết từng bước")
    parser.add_argument("--table",   action="store_true", help="In toàn bộ 7 bảng mã hóa")
    args = parser.parse_args()

    # In bảng mã hóa
    if args.table:
        print("7 BẢNG MÃ HÓA")
        print("─" * 60)
        for i, table in enumerate(ENCODE_TABLES):
            row = "  ".join(f"{d}→{table[d]}" for d in range(10))
            print(f"  Bảng {i+1}: {row}")
        return

    # Chỉ decode
    if args.decode:
        result = decode(args.decode, verbose=True)
        if result:
            print(f"\n  → Prefix: {result['prefix']}")
            print(f"  → Chỉ số: {result['index']}")
            print(f"  → Checksum: {'OK' if result['checksum_ok'] else 'SAI!'}")
        return

    # Cần tên + chỉ số
    if args.name is None or args.index is None:
        parser.print_help()
        sys.exit(1)

    password = generate(args.name, args.index, verbose=args.verbose)
    print(f"\nPassword: {password}")
    print(f"Colored : {colorize(password)}")

    # Xác minh nếu có
    if args.verify:
        if args.verify.upper() == password:
            print(f"\n✓ Password khớp!")
        else:
            print(f"\n✗ Không khớp. Mong đợi: {password}")
            # Decode ngược để xem password kia chứa gì
            print(f"\nGiải mã '{args.verify}':")
            decode(args.verify.upper(), verbose=args.verbose)

    # Tự kiểm tra nội bộ
    decoded = decode(password)
    if decoded:
        ok = decoded["index"] == args.index
        print(f"\nSelf-check: decode → index={decoded['index']}  {'✓' if ok else '✗'}")


if __name__ == "__main__":
    # Demo nhanh nếu không có argument
    if len(sys.argv) == 1:
        print("=== DEMO ===")
        test_cases = [
            ("Dragon", 47),
            ("Dragon", 1250),
            ("AB",     99999),
            ("XYZ",    0),
        ]
        print(f"\n{'Tên':<12} {'Chỉ số':>8}  {'Password':>12}  {'Decode OK'}")
        print("─" * 50)
        for name, idx in test_cases:
            pw = generate(name, idx)
            dec = decode(pw)
            ok = dec and dec["index"] == idx and dec["checksum_ok"]
            print(f"{name:<12} {idx:>8}  {pw:>12}  {'✓' if ok else '✗'}")

        print("\n--- Chi tiết ví dụ 'Dragon' index=1250 ---")
        pw = generate("Dragon", 1250, verbose=True)
        print(f"\nKết quả: {pw}")
        print(f"Màu WC3: {colorize(pw)}")
    else:
        main()
