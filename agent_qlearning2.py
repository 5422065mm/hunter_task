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
pygame.display.set_caption("hunter task - Q Learning (Relative State)")

# マップ（20x20）
map_data = [[0 for _ in range(20)] for _ in range(20)]

# 画像
ground_img = pygame.image.load("images/ground.png")
ground_img = pygame.transform.scale(ground_img, (TILE_SIZE, TILE_SIZE))
player1_img = pygame.image.load("images/player1.png")
player1_img = pygame.transform.scale(player1_img, (TILE_SIZE, TILE_SIZE))
prey1_img = pygame.image.load("images/prey1.png")
prey1_img = pygame.transform.scale(prey1_img, (TILE_SIZE, TILE_SIZE))

# フォント
font = pygame.font.SysFont(None, 24)

# グリッドサイズ
GRID_W = len(map_data[0])
GRID_H = len(map_data)

# ===== Q学習エージェント =====
class QLearningAgent:
    def __init__(self, grid_w, grid_h, actions, alpha=0.2, gamma=0.95, eps_start=1.0, eps_end=0.05, eps_decay=0.999):
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay
        self.Q = {}  # Q[(dx, dy)][action] = value  <-- ★ここが変わります（相対座標）

    def _init_state(self, s):
        if s not in self.Q:
            self.Q[s] = {a: 0.0 for a in self.actions}

    def select_action(self, s):
        self._init_state(s)
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        q = self.Q[s]
        # 最大値を持つ行動が複数ある場合ランダムに選ぶ（動作の偏り防止）
        max_q = max(q.values())
        actions_with_max_q = [a for a, v in q.items() if v == max_q]
        return random.choice(actions_with_max_q)

    def update(self, s, a, r, s_next):
        self._init_state(s)
        self._init_state(s_next)
        q_sa = self.Q[s][a]
        max_next = max(self.Q[s_next].values())
        self.Q[s][a] = q_sa + self.alpha * (r + self.gamma * max_next - q_sa)
        if self.epsilon > self.eps_end:
            self.epsilon *= self.eps_decay

# 位置ラップ処理
def wrap_pos(x, y, w, h):
    return x % w, y % h

# ★追加関数：相対状態の取得（トーラス考慮）
def get_relative_state(px, py, tx, ty, w, h):
    """
    プレイヤー(px, py)から見たターゲット(tx, ty)の相対位置(dx, dy)を返す。
    トーラス構造を考慮し、近い方の距離を採用する。
    """
    dx = tx - px
    dy = ty - py

    # 横方向のラップ処理
    if dx > w / 2:
        dx -= w
    elif dx < -w / 2:
        dx += w
    
    # 縦方向のラップ処理
    if dy > h / 2:
        dy -= h
    elif dy < -h / 2:
        dy += h
        
    return (dx, dy)

# 行動の方向ベクトル
ACTION_TO_DXY = {
    "UP":    (0, -1),
    "DOWN":  (0,  1),
    "LEFT":  (-1, 0),
    "RIGHT": (1,  0),
    "STAY":  (0,  0),
}

#ハンターと獲物の距離計算式（ユークリッド距離・トーラス考慮）
def torus_distance(x1, y1, x2, y2, w, h):
    dx = min(abs(x1 - x2), w - abs(x1 - x2))
    dy = min(abs(y1 - y2), h - abs(y1 - y2))
    return (dx**2 + dy**2) ** 0.5

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

# 獲物ランダム移動
def move_prey(prey_x, prey_y):
    r = random.random()
    # 学習が早いため、最初から少し動くようにしても良いが、元のロジックを維持
    if episode >= 500: # 学習が早まるので条件を緩和
        if r < 0.2:
            prey_y -= 1
        elif r < 0.6:
            prey_x += 1
        else:
            pass
    else:
        pass

    return wrap_pos(prey_x, prey_y, GRID_W, GRID_H)

# 初期配置（重複なし）
def sample_non_overlapping_positions(n):
    all_positions = [(x, y) for x in range(GRID_W) for y in range(GRID_H)]
    return random.sample(all_positions, n)

(player1_x, player1_y), (prey1_x, prey1_y) = sample_non_overlapping_positions(2)

# 学習用オブジェクト
agent = QLearningAgent(
    grid_w=GRID_W,
    grid_h=GRID_H,
    actions=["UP", "DOWN", "LEFT", "RIGHT", "STAY"],
    alpha=0.25, gamma=0.95,
    eps_start=1.0, eps_end=0.05, eps_decay=0.9995 
)

hunt1 = False
count_total_steps = 0
episode = 1
steps_in_episode = 0
MAX_EPISODES = 10000 # ★学習効率が良いので10万回も不要。1万回で十分収束します。
steps_per_episode = []

# エピソードリセット
def reset_episode():
    global player1_x, player1_y, prey1_x, prey1_y, hunt1, steps_in_episode, episode
    steps_per_episode.append(steps_in_episode)
    (player1_x, player1_y), (prey1_x, prey1_y) = sample_non_overlapping_positions(2)
    hunt1 = False
    steps_in_episode = 0
    episode += 1

clock = pygame.time.Clock()

# ===== メインループ =====
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    # --- Q学習でハンター行動 ---
    
    # ★変更点1: 現在の状態を相対座標で取得
    state = get_relative_state(player1_x, player1_y, prey1_x, prey1_y, GRID_W, GRID_H)
    
    action = agent.select_action(state)
    dx, dy = ACTION_TO_DXY[action]
    player1_x, player1_y = wrap_pos(player1_x + dx, player1_y + dy, GRID_W, GRID_H)

    if not hunt1:
        prey1_x, prey1_y = move_prey(prey1_x, prey1_y)

    caught = (player1_x, player1_y) == (prey1_x, prey1_y)
    
    # --- 距離計算 ---
    dist_before = torus_distance(state[0], state[1], 0, 0, GRID_W, GRID_H) # 相対位置なので相手は(0,0)とみなせるが、元の距離計算を使うなら座標を工夫
    # 注: torus_distance関数は絶対座標用なので、報酬計算用に絶対座標も保持するか、
    # あるいは以下のように計算しなおすのが安全です。
    
    # 報酬計算用に「行動前の絶対座標」は保持していないので、
    # ここでは簡易的に「行動後の距離」だけで評価するか、
    # 本当は step 実行前に dist_before を計算しておくのがベターです。
    # 今回は元のコードの流れを崩さず、再計算します。
    
    # ここでは「行動後の絶対座標」と「獲物の絶対座標」で距離を測ります
    dist_after = torus_distance(player1_x, player1_y, prey1_x, prey1_y, GRID_W, GRID_H)
    
    # dist_before を正確に出すには「行動前の座標」が必要ですが、
    # ループの最初で state を取ったときの距離と比較したい場合、
    # state は (dx, dy) なので、そのベクトルの長さが dist_before に相当します。
    dist_before_from_state = (state[0]**2 + state[1]**2) ** 0.5 
    
    # ただし state[0], state[1] はトーラス補正済みなので、そのままユークリッド距離計算でOK
    
    if caught:
        reward = 10.0
    else:
        reward = -0.1
        if dist_after < dist_before_from_state:
            reward += 0.2   # 近づいた（報酬を少し強化）
        elif dist_after > dist_before_from_state:
            reward -= 0.3   # 遠ざかった

    hunt1 = caught

    # ★変更点2: 次の状態も相対座標で取得
    next_state = get_relative_state(player1_x, player1_y, prey1_x, prey1_y, GRID_W, GRID_H)
    
    agent.update(state, action, reward, next_state)

    steps_in_episode += 1
    count_total_steps += 1

    # エピソード終了条件
    if hunt1 or episode > MAX_EPISODES:
        reset_episode()
  
    if episode > MAX_EPISODES:
        # Q辞書保存
        save_path = os.path.join(os.path.dirname(__file__), "q_table.pkl2")
        with open("q_table.pkl2", "wb") as f:
            pickle.dump(agent.Q, f)

        print("保存しました:", save_path)
        plt.figure(figsize=(20,10))
        plt.plot(range(1, len(steps_per_episode)+1), steps_per_episode, color="blue")
        plt.xlabel("Episode")
        plt.ylabel("Steps per Episode")
        plt.title("Steps per Episode (Relative State Q-Learning)")
        plt.xticks(range(0, MAX_EPISODES+1, 1000))
        plt.grid(True)
        plt.show()
        pygame.quit()
        sys.exit()
        

    # --- 表示更新 ---
    text_count = font.render(f"Total Steps: {count_total_steps}", True, (255, 0, 0))
    text_ep = font.render(f"Ep: {episode}  Steps: {steps_in_episode}  eps: {agent.epsilon:.3f}", True, (0, 0, 255))

    # --- 描画 ---
    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    screen.blit(text_count, (650, 40))
    screen.blit(text_ep, (650, 70))
    pygame.display.flip()

    if episode <= MAX_EPISODES - 10: # 最後の100エピソードだけゆっくり見せる
        clock.tick() # 最高速
    else:
        clock.tick(30)