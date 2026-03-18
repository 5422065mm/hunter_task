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

SCREEN_WIDTH, SCREEN_HEIGHT = 900, 640
TILE_SIZE = 32
WHITE = (255, 255, 255)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hunter Task - Manual Seed Entry")

# ===== マップ設定 =====
map_data = [[0 for _ in range(20)] for _ in range(20)]
GRID_W, GRID_H = len(map_data[0]), len(map_data)

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
    with open(load_path1, "rb") as f: Q1 = pickle.load(f)
if os.path.exists(load_path2):
    with open(load_path2, "rb") as f: Q2 = pickle.load(f)

# =================================================================
#  ★重要: シード値をここに直接入力してください
# =================================================================
REPLAY_SEEDS = [
    # --- 判明している分 (1〜11) ---
    968602,  # Ep 1
    351877,  # Ep 2
    312937,  # Ep 3
    434391,  # Ep 4
    807993,  # Ep 5
    938993,  # Ep 6
    253501,  # Ep 7
    243205,  # Ep 8
    213863,  # Ep 9
    206352,  # Ep 10
    461676,  # Ep 11
    
    # --- ★ここに画像の数値 (12〜20) を書き換えてください ---
    397444,       # Ep 12
    218267,       # Ep 13
    61843,       # Ep 14
    567974,       # Ep 15
    762326,       # Ep 16
    320300,       # Ep 17
    437558,       # Ep 18
    197282,       # Ep 19
    236707        # Ep 20
]

print("-" * 50)
print(f"シード値固定モード: 全{len(REPLAY_SEEDS)}件")
print("※ Ep12以降が0の場合は、コード内のREPLAY_SEEDSリストを編集してください。")
print("-" * 50)

# ===== パラメータ =====
ACTION_TO_DXY = {"UP":(0,-1), "DOWN":(0,1), "LEFT":(-1,0), "RIGHT":(1,0), "STAY":(0,0)}
ACTIONS = list(ACTION_TO_DXY.keys())

raw_intention_log = []   
episode_summary_log = [] 

def wrap_pos(x, y, w, h): return x % w, y % h
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

def get_relative_state(px, py, tx, ty, w, h):
    dx = tx - px
    dy = ty - py
    if dx > w / 2: dx -= w
    elif dx < -w / 2: dx += w
    if dy > h / 2: dy -= h
    elif dy < -h / 2: dy += h
    return (dx, dy)

def get_action_pure_q(q_table, px, py, tx, ty):
    rel_state = get_relative_state(px, py, tx, ty, GRID_W, GRID_H)
    q_vals = q_table.get(rel_state, {a: 0.0 for a in ACTIONS})
    max_q = max(q_vals.values())
    best_actions = [a for a, q in q_vals.items() if q == max_q]
    return random.choice(best_actions), max_q

def decide_lv0_action(own_Q, own_pos, prey1_pos, prey2_pos):
    act1, val1 = get_action_pure_q(own_Q, *own_pos, *prey1_pos)
    act2, val2 = get_action_pure_q(own_Q, *own_pos, *prey2_pos)
    if val1 > val2: return act1, "prey1"
    elif val2 > val1: return act2, "prey2"
    else: return (act1, "prey1") if random.random()<0.5 else (act2, "prey2")

def decide_lv1_action(own_Q, opp_Q, own_pos, opp_pos, prey1_pos, prey2_pos):
    _, opp_val1 = get_action_pure_q(opp_Q, *opp_pos, *prey1_pos)
    _, opp_val2 = get_action_pure_q(opp_Q, *opp_pos, *prey2_pos)
    est_target = "prey1" if opp_val1 > opp_val2 else ("prey2" if opp_val2 > opp_val1 else ("prey1" if random.random()<0.5 else "prey2"))
    
    if est_target == "prey1":
        act, _ = get_action_pure_q(own_Q, *own_pos, *prey2_pos)
        return act, "prey2", est_target
    else:
        act, _ = get_action_pure_q(own_Q, *own_pos, *prey1_pos)
        return act, "prey1", est_target

def plot_results(summary_data):
    if not summary_data: return
    df_sum = pd.DataFrame(summary_data)
    episodes = df_sum["Episode"]
    steps = df_sum["Steps"]
    n_episodes = len(episodes)
    plt.figure(figsize=(12, 6))
    plt.bar(episodes, steps, color='skyblue', edgecolor='black', zorder=3)
    plt.xlabel("Episode ID")
    plt.ylabel("Steps (Moves)")
    plt.title("Steps per Episode")
    plt.ylim(0, 105)
    plt.xlim(0.5, n_episodes + 0.5)
    ax = plt.gca()
    ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.xaxis.set_major_locator(MultipleLocator(1))
    plt.grid(which='major', axis='both', linestyle='--', linewidth=0.7, zorder=0)
    plt.savefig("episode_steps_graph.png")
    print("Graph saved.")
    plt.show()

def setup_episode_positions(ep_num):
    # シード値リストの範囲内ならそれを使う、範囲外ならランダム
    idx = ep_num - 1
    if idx < len(REPLAY_SEEDS):
        seed_val = int(REPLAY_SEEDS[idx])
        if seed_val == 0:
            print(f"注意: Ep {ep_num} のシード値が0です。設定を確認してください。")
    else:
        seed_val = random.randint(0, 999999)
        
    random.seed(seed_val)
    return sample_non_overlapping_positions(4), seed_val

# ===== 初期化 =====
MAX_EPISODES = len(REPLAY_SEEDS)
episode = 1
steps_in_episode = 0
(positions), current_seed = setup_episode_positions(episode)
(player1_x, player1_y), (player2_x, player2_y) = positions[0], positions[1]
(prey1_x, prey1_y), (prey2_x, prey2_y) = positions[2], positions[3]
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
            pygame.quit(); sys.exit()

    action1, target1 = decide_lv0_action(Q1, (player1_x, player1_y), (prey1_x, prey1_y), (prey2_x, prey2_y))
    action2, target2, est_target = decide_lv1_action(Q2, Q1, (player2_x, player2_y), (player1_x, player1_y), (prey1_x, prey1_y), (prey2_x, prey2_y))

    if not hunt1 and not hunt2:
        raw_intention_log.append({"Episode": episode, "Step": steps_in_episode + 1, "Real": target1, "Est": est_target, "Correct": (target1 == est_target)})

    if not hunt1:
        dx, dy = ACTION_TO_DXY[action1]
        player1_x, player1_y = wrap_pos(player1_x + dx, player1_y + dy, GRID_W, GRID_H)
    if not hunt2:
        dx, dy = ACTION_TO_DXY[action2]
        player2_x, player2_y = wrap_pos(player2_x + dx, player2_y + dy, GRID_W, GRID_H)

    if (player1_x, player1_y) == (prey1_x, prey1_y) or (player1_x, player1_y) == (prey2_x, prey2_y): hunt1 = True
    if (player2_x, player2_y) == (prey1_x, prey1_y) or (player2_x, player2_y) == (prey2_x, prey2_y): hunt2 = True

    if not hunt1: prey1_x, prey1_y = move_prey(prey1_x, prey1_y)
    if not hunt2: prey2_x, prey2_y = move_prey(prey2_x, prey2_y)

    steps_in_episode += 1
    
    if (hunt1 and hunt2) or steps_in_episode >= 100:
        ep_logs = [l for l in raw_intention_log if l["Episode"] == episode]
        acc = (sum(1 for l in ep_logs if l["Correct"]) / len(ep_logs) * 100) if ep_logs else 0.0
        print(f"Ep {episode}: {steps_in_episode} steps (Acc: {acc:.1f}%) Seed:{current_seed}")
        episode_summary_log.append({"Episode": episode, "Steps": steps_in_episode, "Accuracy": acc, "Seed": current_seed})
        episode += 1
        
        if episode > MAX_EPISODES:
            if raw_intention_log: pd.DataFrame(raw_intention_log).to_csv("raw_intention_log.csv", index=False)
            if episode_summary_log:
                pd.DataFrame(episode_summary_log).to_csv("episode_summary.csv", index=False)
                plot_results(episode_summary_log)
            running = False
            continue
        
        (positions), current_seed = setup_episode_positions(episode)
        (player1_x, player1_y), (player2_x, player2_y) = positions[0], positions[1]
        (prey1_x, prey1_y), (prey2_x, prey2_y) = positions[2], positions[3]
        hunt1, hunt2 = False, False
        steps_in_episode = 0

    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_player(player2_img, player2_x, player2_y)
    if not ((player1_x, player1_y) == (prey1_x, prey1_y) or (player2_x, player2_y) == (prey1_x, prey1_y)): draw_prey(prey1_img, prey1_x, prey1_y)
    if not ((player1_x, player1_y) == (prey2_x, prey2_y) or (player2_x, player2_y) == (prey2_x, prey2_y)): draw_prey(prey2_img, prey2_x, prey2_y)
    screen.blit(font.render(f"Ep:{episode}/{MAX_EPISODES} Step:{steps_in_episode} Seed:{current_seed}", True, (0,0,255)), (20, 10))
    pygame.display.flip()
    clock.tick(0) # 最高速で実行

pygame.quit()