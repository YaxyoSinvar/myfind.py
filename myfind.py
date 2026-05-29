#!/usr/bin/env python3
import os
import argparse
import fnmatch
import pwd

def main():
    # Argumentlarni qabul qilish (xuddi find kabi)
    parser = argparse.ArgumentParser(description="Custom Find dasturi")
    parser.add_argument("path", nargs="?", default=".", help="Qidiruv boshlanadigan papka (masalan: /)")
    parser.add_argument("-name", help="Fayl nomi bo'yicha qidirish (masalan: *.txt)")
    parser.add_argument("-type", choices=["f", "d"], help="Turi bo'yicha: f (fayl) yoki d (papka)")
    parser.add_argument("-perm", help="Ruxsatlar bo'yicha (masalan: -4000, 0777)")
    parser.add_argument("-user", help="Fayl egasi bo'yicha (masalan: root)")
    
    args = parser.parse_args()

    # Foydalanuvchini UID raqamiga o'girish
    target_uid = None
    if args.user:
        try:
            target_uid = pwd.getpwnam(args.user).pw_uid
        except KeyError:
            print(f"Xato: '{args.user}' ismli foydalanuvchi topilmadi.")
            return

    # Papkalarni aylanib chiqish (os.walk ruxsat etilmagan papkalardagi xatolarni chetlab o'tadi)
    for root, dirs, files in os.walk(args.path):
        items = []
        if args.type == "d" or not args.type:
            items.extend(dirs)
        if args.type == "f" or not args.type:
            items.extend(files)

        for item in items:
            full_path = os.path.join(root, item)
            
            # 1. Nomi bo'yicha tekshirish
            if args.name and not fnmatch.fnmatch(item, args.name):
                continue
            
            try:
                stat = os.stat(full_path)
            except OSError:
                continue # Ruxsat yo'q yoki buzilgan fayllarni o'tkazib yuborish

            # 2. Turi bo'yicha tekshirish
            is_dir = os.path.isdir(full_path)
            if args.type == 'f' and is_dir: continue
            if args.type == 'd' and not is_dir: continue

            # 3. Egasi (User) bo'yicha tekshirish
            if target_uid is not None and stat.st_uid != target_uid:
                continue

            # 4. Ruxsatlar (Permissions / SUID) bo'yicha tekshirish
            if args.perm:
                mode = stat.st_mode
                if args.perm == "-4000": # SUID fayllarni topish
                    if not (mode & 0o4000): continue
                elif args.perm.startswith("-"): # Ichida kamida shu ruxsatlar borligini tekshirish
                    try:
                        req_perm = int(args.perm[1:], 8)
                        if (mode & req_perm) != req_perm: continue
                    except ValueError: pass
                else: # Aniq mos keladigan ruxsatlarni tekshirish (masalan: 0777)
                    try:
                        req_perm = int(args.perm, 8)
                        if (mode & 0o7777) != req_perm: continue
                    except ValueError: pass

            # Agar barcha shartlardan o'tsa, ekranga chiqarish
            print(full_path)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nQidiruv to'xtatildi.")
