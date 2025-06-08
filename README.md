# So'z Hujumi

**So'z Hujumi** — Pygame asosida ishlab chiqilgan dinamik o'yin. Ekranda yuqoridan pastga tushayotgan so'zlarni to'g'ri kiritib, ularga "hujum qiling". Har bir so'z ochko qo'shadi, ammo ekran chetiga yetsa, hayotlar kamayadi. O'yin turli qiyinlik darajalari, so'z fayllarini boshqarish va jozibali multimedia effektlarini taqdim etadi.

**Birinchi o'qish uchun**: O'yin qoidalari va maqsadlari haqida `data/about.txt` faylini yoki menyudagi "O'yin haqida" bo'limini o'qing.

## Funksiyalar

- **Dinamik so'zlar**: SQLite ma'lumotlar bazasidagi `.txt` fayllardan so'zlar olinadi, foydalanuvchi fayllarni qo'shishi/o'chirishi mumkin.
- **Qiyinlik darajalari**: Oson (3 hayot), O'rtacha (5 hayot), Qiyin (7 hayot) rejimlari.
- **To'lqin tizimi**: Har bir to'lqinda so'zlar soni va tezligi oshadi, 5 soniyali pauza bilan.
- **Interfeys**: Ochko, hayotlar, to'lqin raqami va kiritilgan so'zlar ekranda ko'rsatiladi.
- **Multimedia**: Har rejim uchun alohida fon musiqasi va video (MoviePy orqali).
- **Fayl boshqaruvi**: Tkinter orqali so'z fayllarini qo'shish/o'chirish/faollashtirish.
- **Kross-platforma**: PyInstaller bilan `.exe` formatida ishlaydi.

## Qanday ishlaydi

1. **Ma'lumotlar bazasi**: `init_db` SQLite bazasini yaratadi, so'z fayllari va natijalarni saqlaydi.
2. **O'yin mexanikasi**: So'zlar tasodifiy paydo bo'ladi (`add_word`), pastga siljiydi (`update_words`), foydalanuvchi kiritadi (`check_input`).
3. **Menyu**: Bosh menu qiyinlik tanlash, fayl boshqaruvi va "O'yin haqida" bo'limini ochadi.
4. **To'lqinlar**: Har to'lqin tugagach, keyingi to'lqinga o'tiladi yoki hayotlar tugasa o'yin yakunlanadi.

## O'rnatish

1. Repozitoriyani klonlang:
   ```bash
   git clone <repo-url>
   cd <repo-folder>
   ```

2. Kutubxonalarni o'rnating:
   ```bash
   pip install pygame sqlite3 moviepy
   ```

3. O'yinni ishga tushiring:
   ```bash
   python main.py
   ```

**.exe uchun**:
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "media;media" --add-data "data;data" main.py
```

## Fayl tuzilmasi

- `main.py`: Asosiy o'yin kodi.
- `data/`: So'z fayllari, `game.db`, `about.txt`.
- `media/`: Fon musiqalari (`*.wav`) va videolar (`*.mp4`).

## Kelajakdagi yaxshilanishlar

- Ko'proq qiyinlik darajalari.
- Animatsiyalar va yangi multimedia.
- Onlayn reyting tizimi.
