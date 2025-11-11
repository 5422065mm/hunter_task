import pygame
import sys
import random
import matplotlib.pyplot as plt
import pickle
import os

# ===== Pygame初期化 =====
pygame.init()

# 画面設定
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 640
TILE_SIZE = 32
WHITE = (255, 255, 255)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hunter Task - pretrained Q-table (auto mode)")

# ===== マップ設定 =====
map_data = [[0 for _ in range(20)] for _ in range(20)]
GRID_W, GRID_H = len(map_data[0]), len(map_data)

# ===== 画像読み込み =====
def load_scaled(path):
    img = pygame.image.load(path)
    return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))

ground_img = load_scaled("images/ground.png")
player1_img = load_scaled("images/player1.png")
player2_img = load_scaled("images/player2.png")
prey1_img = load_scaled("images/prey1.png")
prey2_img = load_scaled("images/prey2.png")

font = pygame.font.SysFont(None, 24)

# ===== Qテーブル読み込み（事前学習済み） =====
load_path1 = os.path.join(os.path.dirname(__file__), "q_table.pkl")
load_path2 = os.path.join(os.path.dirname(__file__), "q_table.pkl2")

with open(load_path1, "rb") as f:
    Q1 = pickle.load(f)
with open(load_path2, "rb") as f:
    Q2 = pickle.load(f)

print("読み込み完了:", load_path1, load_path2)

# ===== パラメータ =====
LV1 = 0  # ハンター1のレベル（0 or 1）
LV2 = 1  # ハンター2のレベル（0 or 1）

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
    if r < 0.2:   # 上
        y -= 1
    elif r < 0.6: # 右
        x += 1
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



# ===== 相手の獲物推定 (G^o = argGmax P(G|so,ao)) =====
def estimate_opponent_target(own_Q, opp_state_prey1, opp_state_prey2):
    """相手の行動価値(Q値)から、どちらの獲物を狙っているか推定"""
    q1_val = max(own_Q.get(opp_state_prey1, {a:0 for a in ACTIONS}).values())
    q2_val = max(own_Q.get(opp_state_prey2, {a:0 for a in ACTIONS}).values())
    return "prey1" if q1_val > q2_val else "prey2"

# ===== 行動決定 (式(2): G* = argGmax Q_i(G|s_i,a_i,G^o)) =====
def decide_target(LV, own_Q, own_pos, opp_pos, prey1_pos, prey2_pos):
    if LV == 0:
        # Lv.0: 自身のQ値が高い方を選ぶ
        s1 = (*own_pos, *prey1_pos)
        s2 = (*own_pos, *prey2_pos)
        q1_val = max(own_Q.get(s1, {a:0 for a in ACTIONS}).values())
        q2_val = max(own_Q.get(s2, {a:0 for a in ACTIONS}).values())
        return "prey1" if q1_val > q2_val else "prey2"

    else:
        # Lv.1: 相手の狙い G^o を推定し、別を選ぶ
        s1_opp = (*opp_pos, *prey1_pos)
        s2_opp = (*opp_pos, *prey2_pos)
        G_o = estimate_opponent_target(own_Q, s1_opp, s2_opp)
        return "prey2" if G_o == "prey1" else "prey1"  # 式(2): 別の獲物を選択

# ===== シミュレーション初期化 =====
(player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y) = sample_non_overlapping_positions(4)
hunt1, hunt2 = False, False
count_total_steps, episode, steps_in_episode = 0, 1, 0
MAX_EPISODES = 1000
steps_per_episode = []
clock = pygame.time.Clock()

# ===== メインループ =====
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            plt.figure(figsize=(20,10))
            plt.plot(range(1, len(steps_per_episode)+1), steps_per_episode, color="blue")
            plt.xlabel("エピソード")
            plt.ylabel("各エピソードのステップ数")
            plt.title("各エピソードのステップ数 (pretrained Q-table)")
            plt.grid(True)
            plt.show()
            pygame.quit()
            sys.exit()

    # --- 各ハンターの行動目標を決定 ---
    goal1 = decide_target(LV1, Q1, (player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y))
    goal2 = decide_target(LV2, Q2, (player2_x, player2_y), (player1_x, player1_y), (prey1_x, prey1_y), (prey2_x, prey2_y))

    # --- 目標方向に移動 ---
    def move_toward(px, py, tx, ty):
        if tx > px: px += 1
        elif tx < px: px -= 1
        if ty > py: py += 1
        elif ty < py: py -= 1
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

    # --- 獲物移動（捕まっていない場合のみ） ---
    if not hunt1:
        prey1_x, prey1_y = move_prey(prey1_x, prey1_y)
    if not hunt2:
        prey2_x, prey2_y = move_prey(prey2_x, prey2_y)

    # --- エピソード管理 ---
    steps_in_episode += 1
    count_total_steps += 1
    if hunt1 and hunt2:
        steps_per_episode.append(steps_in_episode)
        steps_in_episode = 0
        episode += 1
        if episode > MAX_EPISODES:
            plt.figure(figsize=(20,10))
            plt.plot(range(1, len(steps_per_episode)+1), steps_per_episode, color="blue")
            plt.xlabel("エピソード")
            plt.ylabel("各エピソードのステップ数")
            plt.title("各エピソードのステップ数 (pretrained Q-table)")
            plt.grid(True)
            plt.show()
            pygame.quit()
            sys.exit()
        (player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y) = sample_non_overlapping_positions(4)
        hunt1, hunt2 = False, False

    # --- 描画 ---
    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_player(player2_img, player2_x, player2_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    draw_prey(prey2_img, prey2_x, prey2_y)

    status = f"Ep:{episode}  Step:{steps_in_episode}  Lv1={LV1} Lv2={LV2}  Prey1={'X' if hunt1 else 'O'} Prey2={'X' if hunt2 else 'O'}"
    text = font.render(status, True, (0,0,255))
    screen.blit(text, (20, 10))

    pygame.display.flip()
    if episode <= MAX_EPISODES - 30:
        clock.tick()
    else:
        clock.tick(30)

