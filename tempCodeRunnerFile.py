import pygame
import sys
import random
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import pickle
import os
import pandas as pd

# ===== Pygame初期化 =====
pygame.init()

# 画面設定
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 640
TILE_SIZE = 32
WHITE = (255, 255, 255)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hunter Task - pretrained Q-table (Fixed Movement)")

# ===== マップ設定 =====
map_data = [[0 for _ in range(20)] for _ in range(20)]
GRID_W, GRID_H = len(map_data[0]), len(map_data)

# ===== CSVからシード値を読み込む =====
CSV_FILE = "summary_stats_1.csv"
REPLAY_SEEDS = []

try:
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE, header=9)
        if 'Seed' in df.columns:
            REPLAY_SEEDS = df['Seed'].tolist()
            print(f"CSVから {len(REPLAY_SEEDS)} 件のシード値を読み込みました。")
        else:
            REPLAY_SEEDS = [random.randint(0, 100000) for _ in range(20)]
    else:
        REPLAY_SEEDS = [random.randint(0, 100000) for _ in range(20)]
except Exception as e:
    print(f"CSV読み込みエラー: {e}")
    REPLAY_SEEDS = [random.randint(0, 100000) for _ in range(20)]

# ===== 画像読み込み =====
def load_scaled(path):
    if not os.path.exists(path):
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        surf.fill((128, 128, 128))
        return surf
    img = pygame.image.load(path)
    return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))

ground_img = load_scaled("images/ground.png")
player1_img = load_scaled("images/player1.png")
player2_img = load_scaled("images/player2.png")
prey1_img = load_scaled("images/prey1.png")
prey2_img = load_scaled("images/prey2.png")

font = pygame.font.SysFont(None, 24)

# ===== Qテーブル読み込み =====
load_path1 = os.path.join(os.path.dirname(__file__), "q_table.pkl")
load_path2 = os.path.join(os.path.dirname(__file__), "q_table.pkl2")

Q1 = {}
Q2 = {}

if os.path.exists(load_path1):
    with open(load_path1, "rb") as f:
        Q1 = pickle.load(f)
if os.path.exists(load_path2):
    with open(load_path2, "rb") as f:
        Q2 = pickle.load(f)

# ===== パラメータ =====
LV1 = 0
LV2 = 1

ACTION_TO_DXY = {
    "UP":    (0, -1),
    "DOWN":  (0,  1),
    "LEFT":  (-1, 0),
    "RIGHT": (1,  0),
    "STAY":  (0,  0),
}
ACTIONS = list(ACTION_TO_DXY.keys())

# ===== ユーティリティ関数 =====
def wrap_pos(x, y, w, h):
    return x % w, y % h

def move_prey(x, y):
    r = random.random()
    if r < 0.2: y -= 1
    elif r < 0.6: x += 1
    return wrap_pos(x, y, GRID_W, GRID_H)

def draw_map():
    for row in range(GRID_H):
        for col in range(GRID_W):
            screen.blit(ground_img, (col * TILE_SIZE, row * TILE_SIZE))

def draw_player(img, x, y): screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))
def draw_prey(img, x, y): screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))

def sample_non_overlapping_positions(n):
    all_positions = [(x, y) for x in range(GRID_W) for y in range(GRID_H)]
    return random.sample(all_positions, n)

# ===== 相手の獲物推定 =====
def estimate_opponent_target(own_Q, opp_state_prey1, opp_state_prey2):
    q1_val = max(own_Q.get(opp_state_prey1, {a:0 for a in ACTIONS}).values())
    q2_val = max(own_Q.get(opp_state_prey2, {a:0 for a in ACTIONS}).values())
    return "prey1" if q1_val > q2_val else "prey2"

# ===== 行動決定 =====
def decide_target(LV, own_Q, own_pos, opp_pos, prey1_pos, prey2_pos):
    if LV == 0:
        s1 = (*own_pos, *prey1_pos)
        s2 = (*own_pos, *prey2_pos)
        q1_val = max(own_Q.get(s1, {a:0 for a in ACTIONS}).values())
        q2_val = max(own_Q.get(s2, {a:0 for a in ACTIONS}).values())
        return "prey1" if q1_val > q2_val else "prey2"
    else:
        s1_opp = (*opp_pos, *prey1_pos)
        s2_opp = (*opp_pos, *prey2_pos)
        G_o = estimate_opponent_target(own_Q, s1_opp, s2_opp)
        return "prey2" if G_o == "prey1" else "prey1"

# ===== グラフ描画関数 (横軸調整済み) =====
def plot_results(steps_list):
    if not steps_list: return
    
    episodes = range(1, len(steps_list) + 1)
    n_episodes = len(steps_list)
    
    plt.figure(figsize=(12, 6))
    
    plt.bar(episodes, steps_list, color='skyblue', edgecolor='black', zorder=3)

    plt.xlabel("Episode ID")
    plt.ylabel("Steps (Moves)")
    plt.title("Steps per Episode")

    # Y軸範囲設定
    plt.ylim(0, 105)
    
    # ★変更点: X軸の表示範囲をデータ数に合わせて制限 (余分な余白や21を表示させない)
    plt.xlim(0.5, n_episodes + 0.5)

    ax = plt.gca()
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.xaxis.set_major_locator(MultipleLocator(1))

    plt.grid(which='major', axis='both', linestyle='--', linewidth=0.7, zorder=0)
    
    filename = "episode_steps_graph.png"
    plt.savefig(filename)
    print(f"グラフを保存しました: {filename}")
    plt.show()

# ===== シミュレーション初期化 =====
def setup_episode_positions(ep_num):
    idx = ep_num - 1
    if idx < len(REPLAY_SEEDS):
        seed_val = int(REPLAY_SEEDS[idx])
    else:
        seed_val = random.randint(0, 999999)
    
    random.seed(seed_val)
    return sample_non_overlapping_positions(4), seed_val

# 初期セットアップ
MAX_EPISODES = len(REPLAY_SEEDS) if REPLAY_SEEDS else 20
episode = 1
steps_in_episode = 0
steps_per_episode = []

(positions), current_seed = setup_episode_positions(episode)
(player1_x, player1_y) = positions[0]
(player2_x, player2_y) = positions[1]
(prey1_x, prey1_y)     = positions[2]
(prey2_x, prey2_y)     = positions[3]

hunt1, hunt2 = False, False
clock = pygame.time.Clock()

print(f"シミュレーション開始: 全{MAX_EPISODES}エピソード")

# ===== メインループ =====
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            plot_results(steps_per_episode)
            pygame.quit()
            sys.exit()

    # --- 行動決定 ---
    goal1 = decide_target(LV1, Q1, (player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y))
    goal2 = decide_target(LV2, Q2, (player2_x, player2_y), (player1_x, player1_y), (prey1_x, prey1_y), (prey2_x, prey2_y))

    # --- 移動ロジック (トーラス対応) ---
    def move_toward(px, py, tx, ty):
        dx = tx - px
        if dx > GRID_W / 2: dx -= GRID_W
        elif dx < -GRID_W / 2: dx += GRID_W
        if dx > 0: px += 1
        elif dx < 0: px -= 1

        dy = ty - py
        if dy > GRID_H / 2: dy -= GRID_H
        elif dy < -GRID_H / 2: dy += GRID_H
        if dy > 0: py += 1
        elif dy < 0: py -= 1
        
        return wrap_pos(px, py, GRID_W, GRID_H)

    if not hunt1 or not hunt2:
        if goal1 == "prey1" and not hunt1:
            player1_x, player1_y = move_toward(player1_x, player1_y, prey1_x, prey1_y)
        elif goal1 == "prey2" and not hunt2:
            player1_x, player1_y = move_toward(player1_x, player1_y, prey2_x, prey2_y)

        if goal2 == "prey1" and not hunt1:
            player2_x, player2_y = move_toward(player2_x, player2_y, prey1_x, prey1_y)
        elif goal2 == "prey2" and not hunt2:
            player2_x, player2_y = move_toward(player2_x, player2_y, prey2_x, prey2_y)

    # --- 捕獲判定 ---
    if (player1_x, player1_y) == (prey1_x, prey1_y) or (player2_x, player2_y) == (prey1_x, prey1_y):
        hunt1 = True
    if (player1_x, player1_y) == (prey2_x, prey2_y) or (player2_x, player2_y) == (prey2_x, prey2_y):
        hunt2 = True

    # --- 獲物移動 ---
    if not hunt1:
        prey1_x, prey1_y = move_prey(prey1_x, prey1_y)
    if not hunt2:
        prey2_x, prey2_y = move_prey(prey2_x, prey2_y)

    # --- エピソード管理 ---
    steps_in_episode += 1
    
    if hunt1 and hunt2:
        steps_per_episode.append(steps_in_episode)
        print(f"Episode {episode} finished in {steps_in_episode} steps.")
        
        episode += 1
        if episode > MAX_EPISODES:
            plot_results(steps_per_episode)
            running = False
            continue
        
        (positions), current_seed = setup_episode_positions(episode)
        (player1_x, player1_y) = positions[0]
        (player2_x, player2_y) = positions[1]
        (prey1_x, prey1_y)     = positions[2]
        (prey2_x, prey2_y)     = positions[3]
        
        hunt1, hunt2 = False, False
        steps_in_episode = 0

    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_player(player2_img, player2_x, player2_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    draw_prey(prey2_img, prey2_x, prey2_y)

    status = f"Ep:{episode}/{MAX_EPISODES} Step:{steps_in_episode} Seed:{current_seed}"
    text = font.render(status, True, (0,0,255))
    screen.blit(text, (20, 10))

    pygame.display.flip()
    clock.tick(0)

pygame.quit()