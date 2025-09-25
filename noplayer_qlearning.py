"""
import pygame
import sys
import random

# Pygameの初期化
pygame.init()

# 画面サイズとタイルサイズの設定
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 640
TILE_SIZE = 32  # タイルのサイズ

# カラー定義
WHITE = (255, 255, 255)

# ウィンドウの設定
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("hunter task")

# マップデータ（20x20のグリッド）
map_data = [[0 for _ in range(20)] for _ in range(20)]

# 画像データ読み込み
ground_img = pygame.image.load("images/ground.png")
ground_img = pygame.transform.scale(ground_img, (TILE_SIZE, TILE_SIZE))

player1_img = pygame.image.load("images/player1.png")
player1_img = pygame.transform.scale(player1_img, (TILE_SIZE, TILE_SIZE))

player2_img = pygame.image.load("images/player2.png")
player2_img = pygame.transform.scale(player2_img, (TILE_SIZE, TILE_SIZE))

prey1_img = pygame.image.load("images/prey1.png")   # 獲物エージェントの画像
prey1_img = pygame.transform.scale(prey1_img, (TILE_SIZE, TILE_SIZE))

prey2_img = pygame.image.load("images/prey2.png")   # 獲物エージェントの画像
prey2_img = pygame.transform.scale(prey2_img, (TILE_SIZE, TILE_SIZE))

# プレイヤーの初期位置
player1_x, player1_y = 5, 5

player2_x, player2_y = 5, 10

# 獲物の初期位置
prey1_x, prey1_y = 10, 10

prey2_x, prey2_y = 10, 5

# 動き判定
moved1 = False
moved2 = False
hunt1 = False
hunt2 = False

# ウィンドウに表示する文字の設定
font1 = pygame.font.SysFont(None, 30)
message_hunt = "Preys are Not hunted"
text_hunt = font1.render(message_hunt, True, (255, 0, 0))

message_count = "Count : 0"
text_count = font1.render(message_count, True, (255, 0, 0))

# 移動回数
count = 0

# 意図推定から行動決定までLLMにやらせる？


# マップ生成
def draw_map():
    for row in range(len(map_data)):
        for col in range(len(map_data[row])):
            tile = map_data[row][col]
            if tile == 0:
                screen.blit(ground_img, (col * TILE_SIZE, row * TILE_SIZE))

def draw_player(player_img, x, y):
    screen.blit(player_img, (x * TILE_SIZE, y * TILE_SIZE))

def draw_prey(prey_img, x, y):
    screen.blit(prey_img, (x * TILE_SIZE, y * TILE_SIZE))

def move_prey(prey_x, prey_y):
    r = random.random()  # 0.0〜1.0 の乱数
    if r < 0.2:  # 20%で上に移動
        prey_y = max(0, prey_y - 1)
    elif r < 0.6:  # 40%で右に移動
        prey_x = min(len(map_data[0]) - 1, prey_x + 1)
    else:  # 40%は動かない
        pass

    return prey_x, prey_y

# メインループ
clock = pygame.time.Clock()
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # プレイヤー移動（キー入力）
        if event.type == pygame.KEYDOWN:
            
            
            # プレイヤー1の操作
            if event.key == pygame.K_UP:
                player1_y = max(0, player1_y - 1); moved1 = True
            if event.key == pygame.K_DOWN:
                player1_y = min(len(map_data) - 1, player1_y + 1); moved1 = True
            if event.key == pygame.K_LEFT:
                player1_x = max(0, player1_x - 1); moved1 = True
            if event.key == pygame.K_RIGHT:
                player1_x = min(len(map_data[0]) - 1, player1_x + 1); moved1 = True

            # プレイヤー2の操作
            if event.key == pygame.K_w:
                player2_y = max(0, player2_y - 1); moved2 = True
            if event.key == pygame.K_s:
                player2_y = min(len(map_data) - 1, player2_y + 1); moved2 = True
            if event.key == pygame.K_a:
                player2_x = max(0, player2_x - 1); moved2 = True
            if event.key == pygame.K_d:
                player2_x = min(len(map_data[0]) - 1, player2_x + 1); moved2 = True

            
            # 獲物がハンターに捕まっていると動けなくなる
            if not hunt1:
                prey1_x, prey1_y = move_prey(prey1_x, prey1_y)

            if not hunt2:
                prey2_x, prey2_y = move_prey(prey2_x, prey2_y)

            # 獲物が二体とも同じ位置に入るとハンター一体でどちらもつかまってしまう
            if ((player1_x == prey1_x) and (player1_y == prey1_y)) or ((player2_x == prey1_x) and (player2_y == prey1_y)):
                hunt1 = True

            if ((player1_x == prey2_x) and (player1_y == prey2_y)) or ((player2_x == prey2_x) and (player2_y == prey2_y)):
                hunt2 = True

            # countもハンターが二体とも動いたときにのみ増やすようにしたい
            # 獲物が二体とも捕まるとカウントを止める
            if (not hunt1) or (not hunt2):
                count += 1
            
            message_hunt = "Preys are " + ("HUNTED!" if (hunt1 and hunt2) else "Not hunted")
            text_hunt = font1.render(message_hunt, True, (255, 0, 0))

            message_count = "Count : " + str(count)
            text_count = font1.render(message_count, True, (255, 0, 0))
            

    # 描画
    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_player(player2_img, player2_x, player2_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    draw_prey(prey2_img, prey2_x, prey2_y)
    screen.blit(text_hunt, (670, 10))
    screen.blit(text_count, (670, 50))
    pygame.display.flip()
    

    clock.tick(30)  # 30fpsで描画（ただし獲物はプレイヤー移動時しか動かない）
"""
"""
import pygame
import sys
import random
import matplotlib.pyplot as plt
import pickle
import os

# ===== Pygame初期化 =====
pygame.init()

# 画面サイズとタイル
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 640
TILE_SIZE = 32
WHITE = (255, 255, 255)

# ウィンドウ
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("hunter task - Q table (pretrained)")

# マップ（20x20）
map_data = [[0 for _ in range(20)] for _ in range(20)]
GRID_W = len(map_data[0])
GRID_H = len(map_data)

# 画像
ground_img = pygame.image.load("images/ground.png")
ground_img = pygame.transform.scale(ground_img, (TILE_SIZE, TILE_SIZE))
player1_img = pygame.image.load("images/player1.png")
player1_img = pygame.transform.scale(player1_img, (TILE_SIZE, TILE_SIZE))
player2_img = pygame.image.load("images/player2.png")
player2_img = pygame.transform.scale(player2_img, (TILE_SIZE, TILE_SIZE))
prey1_img = pygame.image.load("images/prey1.png")
prey1_img = pygame.transform.scale(prey1_img, (TILE_SIZE, TILE_SIZE))
prey2_img = pygame.image.load("images/prey2.png")
prey2_img = pygame.transform.scale(prey2_img, (TILE_SIZE, TILE_SIZE))

# フォント
font = pygame.font.SysFont(None, 24)

# ===== Qテーブル読み込み =====
load_path = os.path.join(os.path.dirname(__file__), "q_table.pkl")
with open("q_table.pkl", "rb") as f:
    Q = pickle.load(f)

print("読み込みました:", load_path)

# 行動の方向ベクトル
ACTION_TO_DXY = {
    "UP":    (0, -1),
    "DOWN":  (0,  1),
    "LEFT":  (-1, 0),
    "RIGHT": (1,  0),
    "STAY":  (0,  0),
}
ACTIONS = list(ACTION_TO_DXY.keys())

# 位置ラップ処理
def wrap_pos(x, y, w, h):
    return x % w, y % h

# 獲物ランダム移動
def move_prey(x, y):
    r = random.random()
    if r < 0.2:   # 上
        y -= 1
    elif r < 0.6: # 右
        x += 1
    else:         # 停止
        pass
    return wrap_pos(x, y, GRID_W, GRID_H)

# 描画
def draw_map():
    for row in range(len(map_data)):
        for col in range(len(map_data[row])):
            if map_data[row][col] == 0:
                screen.blit(ground_img, (col * TILE_SIZE, row * TILE_SIZE))

def draw_player(img, x, y):
    screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))

def draw_prey(img, x, y):
    screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))

# 初期配置（重複なし）
def sample_non_overlapping_positions(n):
    all_positions = [(x, y) for x in range(GRID_W) for y in range(GRID_H)]
    return random.sample(all_positions, n)

# ===== エージェント制御 =====
def select_action(Q, state):
    if state not in Q:
        return random.choice(ACTIONS)  # 未知状態はランダム
    q = Q[state]
    return max(q, key=q.get)

# ===== シミュレーション用変数 =====
(player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y) = sample_non_overlapping_positions(4)

hunt1, hunt2 = False, False
count_total_steps = 0
episode = 1
steps_in_episode = 0
MAX_EPISODES = 1000
steps_per_episode = []

# エピソードリセット
def reset_episode():
    global player1_x, player1_y, player2_x, player2_y
    global prey1_x, prey1_y, prey2_x, prey2_y
    global hunt1, hunt2, steps_in_episode, episode

    steps_per_episode.append(steps_in_episode)
    (player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y) = sample_non_overlapping_positions(4)
    hunt1, hunt2 = False, False
    steps_in_episode = 0
    episode += 1

clock = pygame.time.Clock()

# ===== メインループ =====
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # グラフ描画して終了
            plt.figure(figsize=(20,10))
            plt.plot(range(1, len(steps_per_episode)+1), steps_per_episode, color="blue")
            plt.xlabel("Episode")
            plt.ylabel("Steps per Episode")
            plt.title("Steps per Episode (pretrained Q-table)")
            plt.grid(True)
            plt.show()
            pygame.quit()
            sys.exit()

    # --- エージェント行動 ---
    state1 = (player1_x, player1_y, prey1_x, prey1_y)
    state2 = (player2_x, player2_y, prey2_x, prey2_y)

    action1 = select_action(Q, state1)
    action2 = select_action(Q, state2)

    dx1, dy1 = ACTION_TO_DXY[action1]
    dx2, dy2 = ACTION_TO_DXY[action2]

    player1_x, player1_y = wrap_pos(player1_x + dx1, player1_y + dy1, GRID_W, GRID_H)
    player2_x, player2_y = wrap_pos(player2_x + dx2, player2_y + dy2, GRID_W, GRID_H)

    if not hunt1:
        prey1_x, prey1_y = move_prey(prey1_x, prey1_y)
    if not hunt2:
        prey2_x, prey2_y = move_prey(prey2_x, prey2_y)

    # 捕獲判定
    if (player1_x, player1_y) == (prey1_x, prey1_y) or (player2_x, player2_y) == (prey1_x, prey1_y):
        hunt1 = True
    if (player1_x, player1_y) == (prey2_x, prey2_y) or (player2_x, player2_y) == (prey2_x, prey2_y):
        hunt2 = True

    steps_in_episode += 1
    count_total_steps += 1

    # 両方捕まったらエピソード終了
    if hunt1 and hunt2:
        if episode >= MAX_EPISODES:
            plt.figure(figsize=(20,10))
            plt.plot(range(1, len(steps_per_episode)+1), steps_per_episode, color="blue")
            plt.xlabel("Episode")
            plt.ylabel("Steps per Episode")
            plt.title("Steps per Episode (pretrained Q-table)")
            plt.grid(True)
            plt.show()
            pygame.quit()
            sys.exit()
        reset_episode()

    # --- 表示更新 ---
    status = "HUNTED!" if (hunt1 and hunt2) else "Not hunted"
    text_hunt = font.render(f"Prey: {status}", True, (255, 0, 0))
    text_count = font.render(f"Total Steps: {count_total_steps}", True, (255, 0, 0))
    text_ep = font.render(f"Episode: {episode}  Steps(episode): {steps_in_episode}", True, (0, 0, 255))

    # --- 描画 ---
    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_player(player2_img, player2_x, player2_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    draw_prey(prey2_img, prey2_x, prey2_y)
    screen.blit(text_hunt, (650, 10))
    screen.blit(text_count, (650, 40))
    screen.blit(text_ep, (520, 70))
    pygame.display.flip()

    if episode <= MAX_EPISODES - 30:
        clock.tick()
    else:
        clock.tick(30)
"""

import pygame
import sys
import random
import matplotlib.pyplot as plt
import pickle
import os

# ===== Pygame初期化 =====
pygame.init()

# 画面サイズとタイルサイズ
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 640
TILE_SIZE = 32
WHITE = (255, 255, 255)

# ウィンドウ設定
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("hunter task - Q table (pretrained)")

# マップ（20x20のグリッド）
map_data = [[0 for _ in range(20)] for _ in range(20)]
GRID_W = len(map_data[0])
GRID_H = len(map_data)

# 画像読み込み
ground_img = pygame.image.load("images/ground.png")
ground_img = pygame.transform.scale(ground_img, (TILE_SIZE, TILE_SIZE))
player1_img = pygame.image.load("images/player1.png")
player1_img = pygame.transform.scale(player1_img, (TILE_SIZE, TILE_SIZE))
player2_img = pygame.image.load("images/player2.png")
player2_img = pygame.transform.scale(player2_img, (TILE_SIZE, TILE_SIZE))
prey1_img = pygame.image.load("images/prey1.png")
prey1_img = pygame.transform.scale(prey1_img, (TILE_SIZE, TILE_SIZE))
prey2_img = pygame.image.load("images/prey2.png")
prey2_img = pygame.transform.scale(prey2_img, (TILE_SIZE, TILE_SIZE))

# フォント設定
font = pygame.font.SysFont(None, 24)

# ===== Qテーブル読み込み（事前学習済み） =====
# 後ほどQテーブルを別々のものにする
load_path1 = os.path.join(os.path.dirname(__file__), "q_table.pkl")
load_path2 = os.path.join(os.path.dirname(__file__), "q_table.pkl")

with open(load_path1, "rb") as f:
    Q1 = pickle.load(f)   # prey1 用
with open(load_path2, "rb") as f:
    Q2 = pickle.load(f)   # prey2 用

print("読み込みました:", load_path1, load_path2)

# ===== パラメータ =====
# Lv.0: 固定で自分のターゲットを選ぶ
# Lv.1: 相手の狙いを推定して別を選ぶ
LV1 = 0  # プレイヤー1のレベル
LV2 = 1  # プレイヤー2のレベル

# 行動の方向ベクトル
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
    """座標のラップ処理（端から出ると反対側に移動する）"""
    return x % w, y % h

def move_prey(x, y):
    """獲物のランダム移動"""
    r = random.random()
    if r < 0.2:   # 上に移動
        y -= 1
    elif r < 0.6: # 右に移動
        x += 1
    return wrap_pos(x, y, GRID_W, GRID_H)

def draw_map():
    """マップ描画"""
    for row in range(len(map_data)):
        for col in range(len(map_data[row])):
            if map_data[row][col] == 0:
                screen.blit(ground_img, (col * TILE_SIZE, row * TILE_SIZE))

def draw_player(img, x, y):
    """プレイヤー描画"""
    screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))

def draw_prey(img, x, y):
    """獲物描画"""
    screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))

def sample_non_overlapping_positions(n):
    """重複しない位置をランダムにサンプリング"""
    all_positions = [(x, y) for x in range(GRID_W) for y in range(GRID_H)]
    return random.sample(all_positions, n)

def select_action(Q, state):
    """Qテーブルに基づいて行動選択"""
    if state not in Q:
        return random.choice(ACTIONS)
    q = Q[state]
    return max(q, key=q.get)

def estimate_opponent_target(player_x, player_y, prey1_pos, prey2_pos):
    """相手の狙いを推定する"""
    d1 = abs(player_x - prey1_pos[0]) + abs(player_y - prey1_pos[1])
    d2 = abs(player_x - prey2_pos[0]) + abs(player_y - prey2_pos[1])
    return "prey1" if d1 < d2 else "prey2"

# ===== シミュレーション用変数 =====
(player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y) = sample_non_overlapping_positions(4)

hunt1, hunt2 = False, False
count_total_steps = 0
episode = 1
steps_in_episode = 0
MAX_EPISODES = 5
steps_per_episode = []

def reset_episode():
    """エピソードリセット"""
    global player1_x, player1_y, player2_x, player2_y
    global prey1_x, prey1_y, prey2_x, prey2_y
    global hunt1, hunt2, steps_in_episode, episode

    steps_per_episode.append(steps_in_episode)
    (player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y) = sample_non_overlapping_positions(4)
    hunt1, hunt2 = False, False
    steps_in_episode = 0
    episode += 1

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

    # --- プレイヤーの行動選択 ---
    state1 = (player1_x, player1_y, prey1_x, prey1_y)
    state2 = (player2_x, player2_y, prey2_x, prey2_y)

    # プレイヤー1
    if LV1 == 0:
        action1 = select_action(Q1, state1)
    else:
        opponent_target = estimate_opponent_target(player2_x, player2_y, (prey1_x, prey1_y), (prey2_x, prey2_y))
        action1 = select_action(Q2, state2) if opponent_target == "prey1" else select_action(Q1, state1)

    # プレイヤー2
    if LV2 == 0:
        action2 = select_action(Q2, state2)
    else:
        opponent_target = estimate_opponent_target(player1_x, player1_y, (prey1_x, prey1_y), (prey2_x, prey2_y))
        action2 = select_action(Q1, state1) if opponent_target == "prey2" else select_action(Q2, state2)

    # 移動
    dx1, dy1 = ACTION_TO_DXY[action1]
    dx2, dy2 = ACTION_TO_DXY[action2]
    player1_x, player1_y = wrap_pos(player1_x + dx1, player1_y + dy1, GRID_W, GRID_H)
    player2_x, player2_y = wrap_pos(player2_x + dx2, player2_y + dy2, GRID_W, GRID_H)

    # 獲物移動
    if not hunt1:
        prey1_x, prey1_y = move_prey(prey1_x, prey1_y)
    if not hunt2:
        prey2_x, prey2_y = move_prey(prey2_x, prey2_y)

    # 捕獲判定
    if (player1_x, player1_y) == (prey1_x, prey1_y) or (player2_x, player2_y) == (prey1_x, prey1_y):
        hunt1 = True
    if (player1_x, player1_y) == (prey2_x, prey2_y) or (player2_x, player2_y) == (prey2_x, prey2_y):
        hunt2 = True

    steps_in_episode += 1
    count_total_steps += 1

    # エピソード終了処理
    if hunt1 and hunt2:
        if episode >= MAX_EPISODES:
            plt.figure(figsize=(20,10))
            plt.plot(range(1, len(steps_per_episode)+1), steps_per_episode, color="blue")
            plt.xlabel("エピソード")
            plt.ylabel("各エピソードのステップ数")
            plt.title("各エピソードのステップ数 (pretrained Q-table)")
            plt.grid(True)
            plt.show()
            pygame.quit()
            sys.exit()
        reset_episode()

    # --- ステータス表示 ---
    status = "HUNTED!" if (hunt1 and hunt2) else "Not hunted"
    text_hunt = font.render(f"Prey: {status}", True, (255, 0, 0))
    text_count = font.render(f"Total Steps: {count_total_steps}", True, (255, 0, 0))
    text_ep = font.render(f"Episode: {episode}  Steps(episode): {steps_in_episode}", True, (0, 0, 255))

    # --- 描画 ---
    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_player(player2_img, player2_x, player2_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    draw_prey(prey2_img, prey2_x, prey2_y)
    screen.blit(text_hunt, (650, 10))
    screen.blit(text_count, (650, 40))
    screen.blit(text_ep, (520, 70))
    pygame.display.flip()

    if episode <= MAX_EPISODES - 30:
        clock.tick()
    else:
        clock.tick(30)
