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
pygame.display.set_caption("Hunter Task - Q-Table (Graph: Steps Only)")

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
    print("Q1 (Lv0) loaded.")
else:
    print("Warning: q_table.pkl not found.")

if os.path.exists(load_path2):
    with open(load_path2, "rb") as f:
        Q2 = pickle.load(f)
    print("Q2 (Lv1) loaded.")
else:
    print("Warning: q_table.pkl2 not found.")

# ===== パラメータ =====
ACTION_TO_DXY = {
    "UP":    (0, -1),
    "DOWN":  (0,  1),
    "LEFT":  (-1, 0),
    "RIGHT": (1,  0),
    "STAY":  (0,  0),
}
ACTIONS = list(ACTION_TO_DXY.keys())

# ログ用リスト
raw_intention_log = []   # 全ステップ詳細
episode_summary_log = [] # エピソードごとのまとめ

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

# ===== 相対座標計算 =====
def get_relative_state(px, py, tx, ty, w, h):
    dx = tx - px
    dy = ty - py
    if dx > w / 2: dx -= w
    elif dx < -w / 2: dx += w
    if dy > h / 2: dy -= h
    elif dy < -h / 2: dy += h
    return (dx, dy)

# ===== 純粋なQ値参照 =====
def get_action_pure_q(q_table, px, py, tx, ty):
    rel_state = get_relative_state(px, py, tx, ty, GRID_W, GRID_H)
    q_vals = q_table.get(rel_state, {a: 0.0 for a in ACTIONS})
    max_q = max(q_vals.values())
    best_actions = [a for a, q in q_vals.items() if q == max_q]
    selected_action = random.choice(best_actions)
    return selected_action, max_q

# ===== エージェント思考ロジック =====
def decide_lv0_action(own_Q, own_pos, prey1_pos, prey2_pos):
    act1, val1 = get_action_pure_q(own_Q, *own_pos, *prey1_pos)
    act2, val2 = get_action_pure_q(own_Q, *own_pos, *prey2_pos)
    
    if val1 > val2:
        target = "prey1"
        final_action = act1
    elif val2 > val1:
        target = "prey2"
        final_action = act2
    else:
        if random.random() < 0.5:
            target = "prey1"
            final_action = act1
        else:
            target = "prey2"
            final_action = act2
    return final_action, target

def decide_lv1_action(own_Q, opp_Q, own_pos, opp_pos, prey1_pos, prey2_pos):
    _, opp_val1 = get_action_pure_q(opp_Q, *opp_pos, *prey1_pos)
    _, opp_val2 = get_action_pure_q(opp_Q, *opp_pos, *prey2_pos)
    
    if opp_val1 > opp_val2:
        est_target = "prey1"
    elif opp_val2 > opp_val1:
        est_target = "prey2"
    else:
        est_target = "prey1" if random.random() < 0.5 else "prey2"

    if est_target == "prey1":
        my_target = "prey2"
        final_action, _ = get_action_pure_q(own_Q, *own_pos, *prey2_pos)
    else:
        my_target = "prey1"
        final_action, _ = get_action_pure_q(own_Q, *own_pos, *prey1_pos)

    return final_action, my_target, est_target

# ===== グラフ描画関数 (以前のスタイルに復元) =====
def plot_results(summary_data):
    if not summary_data: return
    
    # データを抽出
    df_sum = pd.DataFrame(summary_data)
    episodes = df_sum["Episode"]
    steps = df_sum["Steps"]
    n_episodes = len(episodes)
    
    plt.figure(figsize=(12, 6))
    
    # 以前と同じ棒グラフの設定
    plt.bar(episodes, steps, color='skyblue', edgecolor='black', zorder=3)

    plt.xlabel("Episode ID")
    plt.ylabel("Steps (Moves)")
    plt.title("Steps per Episode")

    # Y軸範囲設定
    plt.ylim(0, 105)
    
    # X軸範囲設定
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
            if episode_summary_log:
                pd.DataFrame(episode_summary_log).to_csv("episode_summary.csv", index=False)
                plot_results(episode_summary_log)
            pygame.quit()
            sys.exit()

    # --- 行動決定 ---
    action1, target1 = decide_lv0_action(
        Q1, (player1_x, player1_y), (prey1_x, prey1_y), (prey2_x, prey2_y)
    )

    action2, target2, est_target = decide_lv1_action(
        Q2, Q1, (player2_x, player2_y), (player1_x, player1_y), (prey1_x, prey1_y), (prey2_x, prey2_y)
    )

    # --- 詳細ログ記録 ---
    if not hunt1 and not hunt2:
        raw_intention_log.append({
            "Episode": episode,
            "Step": steps_in_episode + 1,
            "Real": target1,
            "Est": est_target,
            "Correct": (target1 == est_target)
        })

    # --- 移動 ---
    if not hunt1:
        dx, dy = ACTION_TO_DXY[action1]
        player1_x, player1_y = wrap_pos(player1_x + dx, player1_y + dy, GRID_W, GRID_H)

    if not hunt2:
        dx, dy = ACTION_TO_DXY[action2]
        player2_x, player2_y = wrap_pos(player2_x + dx, player2_y + dy, GRID_W, GRID_H)

    # --- 捕獲判定 ---
    if (player1_x, player1_y) == (prey1_x, prey1_y): hunt1 = True
    if (player1_x, player1_y) == (prey2_x, prey2_y): hunt1 = True
    
    if (player2_x, player2_y) == (prey1_x, prey1_y): hunt2 = True
    if (player2_x, player2_y) == (prey2_x, prey2_y): hunt2 = True

    # --- 獲物移動 ---
    if not hunt1:
        prey1_x, prey1_y = move_prey(prey1_x, prey1_y)
    if not hunt2:
        prey2_x, prey2_y = move_prey(prey2_x, prey2_y)

    steps_in_episode += 1
    
    # --- エピソード終了判定 ---
    if (hunt1 and hunt2) or steps_in_episode >= 100:
        
        # 精度計算
        ep_logs = [l for l in raw_intention_log if l["Episode"] == episode]
        if ep_logs:
            correct_count = sum(1 for l in ep_logs if l["Correct"])
            accuracy = correct_count / len(ep_logs) * 100
        else:
            accuracy = 0.0

        print(f"Ep {episode}: {steps_in_episode} steps (Acc: {accuracy:.1f}%)")

        # まとめログに追加 (CSV用)
        episode_summary_log.append({
            "Episode": episode,
            "Steps": steps_in_episode,
            "Accuracy": accuracy,
            "Seed": current_seed
        })
            
        episode += 1
        
        # --- 全エピソード終了 ---
        if episode > MAX_EPISODES:
            # 1. 生ログ保存
            if raw_intention_log:
                pd.DataFrame(raw_intention_log).to_csv("raw_intention_log.csv", index=False)
                print("raw_intention_log.csv saved.")
            
            # 2. まとめログ保存 (Acc含む)
            if episode_summary_log:
                pd.DataFrame(episode_summary_log).to_csv("episode_summary.csv", index=False)
                print("episode_summary.csv saved.")
                
                # 3. グラフ描画 (ステップのみ)
                plot_results(episode_summary_log)

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
    if not ((player1_x, player1_y) == (prey1_x, prey1_y) or (player2_x, player2_y) == (prey1_x, prey1_y)):
        draw_prey(prey1_img, prey1_x, prey1_y)
    if not ((player1_x, player1_y) == (prey2_x, prey2_y) or (player2_x, player2_y) == (prey2_x, prey2_y)):
        draw_prey(prey2_img, prey2_x, prey2_y)

    status = f"Ep:{episode}/{MAX_EPISODES} Step:{steps_in_episode} Seed:{current_seed}"
    text = font.render(status, True, (0,0,255))
    screen.blit(text, (20, 10))

    pygame.display.flip()
    clock.tick(0)

pygame.quit()