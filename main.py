import pygame
import random
import sys
from moviepy import VideoFileClip

import sys, os


def resource_path(relative_path):
    """ .exe formatda to‘g‘ri yo‘l olish uchun yordamchi funksiya """
    try:
        base_path = sys._MEIPASS  # PyInstaller tomonidan yaratilgan vaqtinchalik katalog
    except AttributeError:
        base_path = os.path.abspath(".")  # .py fayl ishga tushsa — hozirgi katalog
    return os.path.join(base_path, relative_path)


import sqlite3

DB_PATH = "data/game.db"
DATA_DIR = "data"


def init_db():
    # Papka mavjudligini ta’minlash
    if not os.path.isdir(DATA_DIR):
        os.makedirs(DATA_DIR)

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Jadval yaratish
    c.execute("""
        CREATE TABLE IF NOT EXISTS word_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL UNIQUE,
            path TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 0
        )
    """)
    # Boshqa jadvallar (scores)…
    # Scores table
    c.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                score INTEGER NOT NULL,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

    # Data papkasidagi .txt fayllarni ro‘yxatga olish
    txt_files = [f for f in os.listdir(DATA_DIR) if f.lower().endswith(".txt")]
    for fname in txt_files:
        path = os.path.join(DATA_DIR, fname)
        c.execute("""
            INSERT OR IGNORE INTO word_files (filename, path)
            VALUES (?, ?)
        """, (fname, path))

    # Agar hali faollashtirilgan fayl bo‘lmasa – birinchisini aktiv qilamiz
    c.execute("SELECT COUNT(*) FROM word_files WHERE is_active = 1")
    if c.fetchone()[0] == 0 and txt_files:
        first_fname = txt_files[0]
        c.execute("""
            UPDATE word_files
            SET is_active = 1
            WHERE filename = ?
        """, (first_fname,))

    conn.commit()
    conn.close()


# Dastur boshida chaqiring
init_db()

# Initialize Pygame
pygame.init()

# Constants
FPS = 60
FONT_SIZE = 32
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Get screen size dynamically
SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h

# Setup screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("So'z Hujumi")

# Fonts
font = pygame.font.SysFont("Comic Sans MS", FONT_SIZE)
large_font = pygame.font.SysFont("Comic Sans MS", 64)

# Clock
clock = pygame.time.Clock()

# Game Variables
paused = False
pause_start_time = 0
spawn_count = 0
spawn_timer = 0
wave_word_counts = {1: 5, 2: 8}
default_count = 12
mode_speed_map = {"easy": 1.0, "medium": 1.6, "hard": 2.4}
lives_map = {"easy": 3, "medium": 5, "hard": 7}
mode_speed = 1.0
spawn_interval = 0
lives = 0
#####
words = []  # To be loaded dynamically
active_words = []
user_input = ""
score = 0
high_score = 0  # New high score variable
wave_number = 1
mode = None  # Easy, Medium, Hard

background_music = {
    "easy": resource_path("media/river.wav"),
    "medium": resource_path("media/Virginio.wav"),
    "hard": resource_path("media/music.wav"),
    "menu": resource_path("media/start_menu.wav"),
    "game_over": resource_path("media/game-over.wav")
}

video_paths = {
    "game": resource_path("media/back1.mp4"),
    "menu": resource_path("media/back2.mp4"),
    "game_over": resource_path("media/back3.mp4")
}


def load_video_clip(video_path):
    try:
        video = VideoFileClip(video_path)
        video = video.resized((SCREEN_WIDTH, SCREEN_HEIGHT))
        return video
    except FileNotFoundError:
        print(f"Error: Video file '{video_path}' not found!")
        pygame.quit()
        sys.exit()


game_video = load_video_clip(video_paths["game"])
menu_video = load_video_clip(video_paths["menu"])
game_over_video = load_video_clip(video_paths["game_over"])


# Functions
def get_wave_word_count(wave):
    return wave_word_counts.get(wave, default_count)


def save_score(new_score):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO scores (score) VALUES (?)", (new_score,))
    conn.commit()
    conn.close()


def get_high_score():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT MAX(score) FROM scores")
    result = c.fetchone()[0] or 0
    conn.close()
    return result


import os


def list_word_files():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT id, filename, is_active FROM word_files")
    files = c.fetchall()
    conn.close()
    return files  # [(id, filename, is_active), ...]


def add_word_file(filepath):
    filename = os.path.basename(filepath)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO word_files (filename, path) VALUES (?, ?)", (filename, filepath))
    conn.commit()
    conn.close()


def add_multiple_word_files():
    # Native OS dialogida bir nechta fayl tanlashga ruxsat
    paths = filedialog.askopenfilenames(
        title="Qo'shish uchun fayl(lar)ni tanlang",
        filetypes=[("Text files", "*.txt")])
    for path in paths:
        add_word_file(path)  # oldin yozilgan add_word_file funksiyasiga uzatamiz


def remove_word_file(file_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM word_files WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()


import tkinter.simpledialog as sd


def remove_multiple_word_files(files):
    # files: [(id, filename, is_active), ...] roʻyxati
    # Foydalanuvchidan "1,3,5" ko'rinishida raqamlar so‘raymiz
    s = sd.askstring(
        "Fayllarni o‘chirish",
        f"O‘chirish uchun ro‘yxat raqamlarini vergul bilan kiriting (1–{len(files)}):"
    )
    if not s:
        return
    # Pars qilish
    try:
        idxs = set(int(x.strip()) for x in s.split(",") if x.strip())
    except ValueError:
        return  # noto‘g‘ri kiritilgan bo‘lsa, bekor qilamiz

    for idx in idxs:
        if 1 <= idx <= len(files):
            file_id = files[idx - 1][0]
            remove_word_file(file_id)


def activate_word_file(file_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Barcha recordsni aktivlikdan chiqarish
    c.execute("UPDATE word_files SET is_active = 0")
    # Tanlangan faylni faollashtirish
    c.execute("UPDATE word_files SET is_active = 1 WHERE id = ?", (file_id,))
    conn.commit()
    conn.close()


def get_active_file_path():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT path FROM word_files WHERE is_active = 1 LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else None


def play_background_music(track):
    pygame.mixer.music.load(track)
    pygame.mixer.music.play(-1)


def stop_background_music():
    pygame.mixer.music.stop()


def draw_text(text, position, color=WHITE, font_type=font):
    render = font_type.render(text, True, color)
    screen.blit(render, position)


def load_words(mode):
    global words
    active_path = get_active_file_path()
    if not active_path:
        print("Error: Faollashtirilgan word file topilmadi!")
        pygame.quit();
        sys.exit()
    with open(active_path, "r", encoding="utf-8") as f:
        words = [line.strip() for line in f if line.strip()]


# def load_words(mode):
#     global words
#     try:
#         with open(f"data/{mode}_words.txt", "r", encoding="utf-8") as file:
#             words = [line.strip() for line in file.readlines() if line.strip()]
#     except FileNotFoundError:
#         print(f"Error: {mode}_words.txt not found!")
#         pygame.quit()
#         sys.exit()


def show_game_over_menu():
    global mode, high_score
    stop_background_music()
    play_background_music(background_music["game_over"])
    video_frames = game_over_video.iter_frames(fps=FPS, dtype="uint8")  # Load game over video
    while True:
        try:
            frame = next(video_frames)
            pygame_frame = pygame.image.frombuffer(frame.tobytes(), (SCREEN_WIDTH, SCREEN_HEIGHT), "RGB")
            screen.blit(pygame_frame, (0, 0))
        except StopIteration:
            video_frames = game_over_video.iter_frames(fps=FPS, dtype="uint8")  # Loop the video

        draw_text("Yutqazdingiz!", (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 4 - 120), RED, large_font)
        draw_text(f"Umumiy natija: {score}", (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 4 + 10))
        draw_text("1. Bosh menyuga qaytish", (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 20))
        draw_text("2. Qayta o'ynash", (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 + 40))
        draw_text("Q - Chiqish", (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT - 120))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:  # Bosh menyuga qaytish
                    return "menu"
                elif event.key == pygame.K_2:  # Qayta o'ynash
                    return "restart"
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()


def show_about_screen():
    scroll_position = 0  # Initialize the scroll position

    while True:
        screen.fill(BLACK)
        draw_text("O'yin haqida", (SCREEN_WIDTH // 2 - 100, 50), RED, large_font)

        try:
            with open("data/about.txt", "r", encoding="utf-8") as file:
                lines = file.readlines()

                # Display lines based on the current scroll position
                for i, line in enumerate(lines[scroll_position:scroll_position + 15]):  # Show up to 15 lines
                    draw_text(line.strip(), (50, 150 + i * 40), WHITE)

        except FileNotFoundError:
            draw_text("O'yin haqida ma'lumot mavjud emas!", (50, 150), RED)

        draw_text("Orqaga qaytish uchun ESC ni bosing", (50, SCREEN_HEIGHT - 100), GREEN)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return  # Exit the about screen
                elif event.key == pygame.K_UP:  # Scroll up
                    if scroll_position > 0:
                        scroll_position -= 1
                elif event.key == pygame.K_DOWN:  # Scroll down
                    if scroll_position + 15 < len(lines):  # Ensure there are more lines to scroll
                        scroll_position += 1


UI_AREAS = [
    pygame.Rect(10, 10, 200, FONT_SIZE),  # Score
    pygame.Rect(10, 50, 200, FONT_SIZE),  # Lives
    pygame.Rect(10, 90, 200, FONT_SIZE),  # Input
    pygame.Rect(SCREEN_WIDTH - 150, 10, 150, FONT_SIZE)  # Wave Number
]


def add_word():
    global wave_number
    if not words:
        return

    word = random.choice(words)
    min_distance = 20
    valid_position = False
    while not valid_position:
        x = random.randint(50, SCREEN_WIDTH - 150)
        y = -FONT_SIZE
        valid_position = True
        for ui_rect in UI_AREAS:
            word_rect = pygame.Rect(x, y, font.size(word)[0], FONT_SIZE)
            if word_rect.colliderect(ui_rect.inflate(min_distance * 2, min_distance * 2)):
                valid_position = False
                break

    active_words.append({"word": word, "x": x, "y": y})


def update_words():
    global lives
    for word in active_words[:]:
        word["y"] += 1 + (wave_number - 1) * 0.2
        if word["y"] > SCREEN_HEIGHT:
            active_words.remove(word)
            lives -= 1


def check_input():
    global score, high_score, user_input
    for word in active_words[:]:
        if word["word"] == user_input:
            active_words.remove(word)
            score += 10
            if score > high_score:
                high_score = score
            user_input = ""


def show_start_menu():
    play_background_music(background_music["menu"])
    video_frames = menu_video.iter_frames(fps=FPS, dtype="uint8")
    while True:
        try:
            frame = next(video_frames)
            pygame_frame = pygame.image.frombuffer(frame.tobytes(), (SCREEN_WIDTH, SCREEN_HEIGHT), "RGB")
            screen.blit(pygame_frame, (0, 0))
        except StopIteration:
            video_frames = menu_video.iter_frames(fps=FPS, dtype="uint8")

        draw_text("So'z Hujumi", (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 8 - 40), font_type=large_font)
        draw_text("Tirik qolish uchun so'zlarga hujum qiling!", (SCREEN_WIDTH // 2 - 240, SCREEN_HEIGHT // 4))
        draw_text("O'yin uchun qiyinlik darajasi tanlang", (SCREEN_WIDTH // 2 - 210, SCREEN_HEIGHT // 4 + 100))
        draw_text("1. Oson", (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 10))
        draw_text("2. O'rtacha", (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 50))
        draw_text("3. Qiyin", (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 90))
        draw_text("4. O'yin haqida", (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 130))
        draw_text("5. So‘z qo‘shish", (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT // 2 + 170))

        draw_text("Eng yuqori ko'rsatkich: " + str(high_score), (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 100))
        draw_text("Q - Chiqish", (SCREEN_WIDTH // 2 - 70, SCREEN_HEIGHT - 120))

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    return "easy"
                elif event.key == pygame.K_2:
                    return "medium"
                elif event.key == pygame.K_3:
                    return "hard"
                elif event.key == pygame.K_4:
                    show_about_screen()
                elif event.key == pygame.K_5:
                    file_management_menu()
                elif event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()


import tkinter as tk
from tkinter import filedialog
import tkinter.simpledialog as sd


def file_management_menu():
    while True:
        screen.fill(BLACK)
        draw_text("Word-file boshqaruvi", (50, 50), RED, large_font)
        files = list_word_files()  # [(id, filename, is_active), ...]
        for idx, (fid, fname, active) in enumerate(files, start=1):
            status = " (ACTIVE)" if active else ""
            draw_text(f"{idx}. {fname}{status}", (50, 150 + idx * 40))
        draw_text("A – Qo‘shish, D – O‘chirish, S – Faollashtirish, ESC – Orqaga",
                  (50, SCREEN_HEIGHT - 100), GREEN)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                root = tk.Tk();
                root.withdraw()
                if event.key == pygame.K_a:
                    add_multiple_word_files()
                elif event.key == pygame.K_d:
                    remove_multiple_word_files(files)
                elif event.key == pygame.K_s:
                    idx = sd.askinteger("Faollashtirish",
                                        f"1–{len(files)} oralig‘ida raqam kiriting:")
                    if idx and 1 <= idx <= len(files):
                        activate_word_file(files[idx - 1][0])
                elif event.key == pygame.K_ESCAPE:
                    return


# def file_management_menu():
#     while True:
#         screen.fill(BLACK)
#         draw_text("Word-file boshqaruvi", (50, 50), RED, large_font)
#         files = list_word_files()
#         # Ro‘yxatni chizish
#         for idx, (fid, fname, active) in enumerate(files, start=1):
#             status = "ACTIVE" if active else ""
#             draw_text(f"{idx}. {fname} {status}", (50, 150 + idx*40))
#         draw_text("A – Qo‘shish, D – O‘chirish, S – Faollashtirish, ESC – Orqaga", (50, SCREEN_HEIGHT-100), GREEN)
#         pygame.display.flip()
#         for event in pygame.event.get():
#             if event.type == pygame.KEYDOWN:
#                 if event.key == pygame.K_d:  # O‘chirish
#                     root = tk.Tk()
#                     root.withdraw()
#                     # 1 dan len(files) gacha bo‘lgan integer so‘raymiz
#                     idx = sd.askinteger("Delete word file",
#                                         f"1–{len(files)} oralig‘ida raqam kiriting:")
#                     if idx and 1 <= idx <= len(files):
#                         file_id = files[idx - 1][0]
#                         remove_word_file(file_id)
#                 elif event.key == pygame.K_s:  # Faollashtirish
#                     root = tk.Tk()
#                     root.withdraw()
#                     idx = sd.askinteger("Activate word file",
#                                         f"1–{len(files)} oralig‘ida raqam kiriting:")
#                     if idx and 1 <= idx <= len(files):
#                         file_id = files[idx - 1][0]
#                         activate_word_file(file_id)
#                 elif event.key == pygame.K_ESCAPE:
#                     return


def validate_key(event):
    allowed_keys = (
        pygame.K_a, pygame.K_b, pygame.K_c, pygame.K_d, pygame.K_e, pygame.K_f, pygame.K_g,
        pygame.K_h, pygame.K_i, pygame.K_j, pygame.K_k, pygame.K_l, pygame.K_m, pygame.K_n,
        pygame.K_o, pygame.K_p, pygame.K_q, pygame.K_r, pygame.K_s, pygame.K_t, pygame.K_u,
        pygame.K_v, pygame.K_w, pygame.K_x, pygame.K_y, pygame.K_z,
        pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_ESCAPE, pygame.K_BACKSPACE, pygame.K_DELETE
    )
    return event.key in allowed_keys


total_this_wave = get_wave_word_count(wave_number)


def start_game():
    global mode, mode_speed, lives, spawn_interval, paused, pause_start_time
    global spawn_count, spawn_timer, score, active_words, user_input, wave_number

    mode = show_start_menu()
    load_words(mode)
    mode_speed = mode_speed_map[mode]
    lives = lives_map[mode]

    # First wave runs immediately (no pause)
    wave_number = 1
    total = get_wave_word_count(1)
    spawn_interval = 10000 / total
    paused = False
    spawn_count = 0
    spawn_timer = 0
    score = 0
    active_words.clear()
    user_input = ""


# Main loop
start_game()
video_frames = game_video.iter_frames(fps=FPS, dtype="uint8")
running = True
pygame.mixer.music.load(background_music[mode])
pygame.mixer.music.play(-1)

restart_game = False  # Qo'shimcha flag

while running:
    now = pygame.time.get_ticks()
    if paused and wave_number > 1:
        # Handle quick keys ESC and Q
        for e in pygame.event.get():
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    mode = show_start_menu()
                    start_game()
                    break
                if e.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()
        if now - pause_start_time >= 5000:
            paused = False
            spawn_count = 0
            active_words.clear()
        else:
            if not restart_game:
                try:
                    frame = next(video_frames)
                    pygame_frame = pygame.image.frombuffer(frame.tobytes(), (SCREEN_WIDTH, SCREEN_HEIGHT), "RGB")
                    screen.blit(pygame_frame, (0, 0))
                except StopIteration:
                    video_frames = game_video.iter_frames(fps=FPS, dtype="uint8")
                draw_text(f"Next wave in {(5000 - (now - pause_start_time)) // 1000 + 1}s",
                          (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2), RED, large_font)
                pygame.display.flip()
                clock.tick(FPS)
                continue
            else:
                restart_game = False  # Qayta o'yinni tiklash uchun flagni o'chiramiz

    # Render background
    try:
        frame = next(video_frames)
    except StopIteration:
        video_frames = game_video.iter_frames(fps=FPS, dtype='uint8')
        frame = next(video_frames)
    screen.blit(pygame.image.frombuffer(frame.tobytes(), (SCREEN_WIDTH, SCREEN_HEIGHT), 'RGB'), (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if not validate_key(event):
                continue
            if event.key == pygame.K_ESCAPE:
                stop_background_music()
                result = show_game_over_menu()
                if result == "menu":
                    mode = show_start_menu()
                    load_words(mode)
                    score = 0
                    lives = lives_map[mode]
                    wave_number = 1
                    active_words = []
                    user_input = ""
                    pygame.mixer.music.load(background_music[mode])
                    pygame.mixer.music.play(-1)
                elif result == "restart":
                    # O'yin qiymatlarini qayta tiklash
                    score = 0
                    wave_number = 1
                    active_words = []
                    lives = lives_map[mode]
                    user_input = ""
                    pygame.mixer.music.load(background_music[mode])
                    pygame.mixer.music.play(-1)
                    restart_game = True  # To'liq qayta boshlash emas, davom etish uchun flagni sozlaymiz
            elif event.key == pygame.K_BACKSPACE:
                user_input = user_input[:-1]
            elif event.key == pygame.K_DELETE:
                user_input = ""
            elif event.key != pygame.K_RETURN and event.key != pygame.K_SPACE:
                user_input += event.unicode

    spawn_timer += clock.get_time()
    if not paused and spawn_count < get_wave_word_count(wave_number) and spawn_timer >= spawn_interval:
        add_word()
        spawn_count += 1
        spawn_timer = 0

    # Update and check input
    if not paused:
        update_words()
        check_input()

    for word in active_words:
        draw_text(word["word"], (word["x"], word["y"]))

    draw_text(f"Score: {score}", (10, 10))
    draw_text(f"Lives: {lives}", (10, 50))
    draw_text(f"Input: {user_input}", (10, 90), GREEN)
    draw_text(f"Wave: {wave_number}", (SCREEN_WIDTH - 150, 10))

    # Wave over detection
    if spawn_count == total_this_wave and not active_words:
        # barcha so‘zlar tugadi → yangi wave
        wave_number += 1
        total_this_wave = get_wave_word_count(wave_number)
        spawn_interval = 10000 / total_this_wave
        paused = True
        pause_start_time = now

    if lives <= 0:
        pygame.mixer.music.stop()
        result = show_game_over_menu()
        if result == "menu":
            mode = show_start_menu()
            load_words(mode)
            score = 0
            lives = lives_map[mode]
            wave_number = 1
            active_words = []
            user_input = ""
            pygame.mixer.music.load(background_music[mode])
            pygame.mixer.music.play(-1)
        elif result == "restart":
            score = 0
            wave_number = 1
            lives = lives_map[mode]
            active_words = []
            user_input = ""
            pygame.mixer.music.load(background_music[mode])
            pygame.mixer.music.play(-1)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
