import pygame
import sys
import random
import matplotlib.pyplot as plt
import pickle
import os

#絶対座標によるQ辞書作成#


# ===== Pygame初期化 =====
pygame.init()

# 画面サイズとタイル
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 640
TILE_SIZE = 32
WHITE = (255, 255, 255)

# ウィンドウ
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("hunter task - Q Learning")

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
    def __init__(self, grid_w, grid_h, actions, alpha=0.2, gamma=0.95, eps_start=1.0, eps_end=0.05, eps_decay=0.995):
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay
        self.Q = {}  # Q[(hx,hy,px,py)][action] = value

    def _init_state(self, s):
        if s not in self.Q:
            self.Q[s] = {a: 0.0 for a in self.actions}

    def select_action(self, s):
        self._init_state(s)
        if random.random() < self.epsilon:
            return random.choice(self.actions)
        q = self.Q[s]
        return max(q, key=q.get)

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

# 行動の方向ベクトル
ACTION_TO_DXY = {
    "UP":    (0, -1),
    "DOWN":  (0,  1),
    "LEFT":  (-1, 0),
    "RIGHT": (1,  0),
    "STAY":  (0,  0),
}

#ハンターと獲物の距離計算式（マンハッタン距離）
""""
def torus_distance(x1, y1, x2, y2, w, h):
    dx = min(abs(x1 - x2), w - abs(x1 - x2))
    dy = min(abs(y1 - y2), h - abs(y1 - y2))
    return dx + dy
"""
#ハンターと獲物の距離計算式（ユークリッド距離）
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
    if episode >= 1000:
        if r < 0.2:
            prey_y -= 1
        elif r < 0.6:
            prey_x += 1
        else:
            #初期段階はこの動かない確率を増やす設計もあり
            #ある一定のエピソード数に達したらここの確率を変更する形式でOK
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
    eps_start=1.0, eps_end=0.05, eps_decay=0.999
)

hunt1 = False
count_total_steps = 0
episode = 1
steps_in_episode = 0
MAX_EPISODES = 100000
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
    state = (player1_x, player1_y, prey1_x, prey1_y)
    action = agent.select_action(state)
    dx, dy = ACTION_TO_DXY[action]
    player1_x, player1_y = wrap_pos(player1_x + dx, player1_y + dy, GRID_W, GRID_H)

    if not hunt1:
        prey1_x, prey1_y = move_prey(prey1_x, prey1_y)

    caught = (player1_x, player1_y) == (prey1_x, prey1_y)
    # --- 距離計算 ---
    #ユークリッド距離を使う（トーラスなのでmod計算込み）

    dist_before = torus_distance(state[0], state[1], state[2], state[3], GRID_W, GRID_H)
    dist_after  = torus_distance(player1_x, player1_y, prey1_x, prey1_y, GRID_W, GRID_H)

    if caught:
        reward = 10.0  # 捕獲したら大きな報酬
    else:
        reward = -0.1  # 時間ペナルティ
        if dist_after < dist_before:
            reward += 0.1   # 近づいたら小さな報酬
        elif dist_after > dist_before:
            reward -= 0.3   # 離れたら小さなペナルティ

    hunt1 = caught

    next_state = (player1_x, player1_y, prey1_x, prey1_y)
    agent.update(state, action, reward, next_state)

    steps_in_episode += 1
    count_total_steps += 1

    # エピソード終了条件
    if hunt1 or episode > MAX_EPISODES:
        reset_episode()

  
    if episode > MAX_EPISODES:
        #Q辞書保存
        save_path = os.path.join(os.path.dirname(__file__), "q_table.pkl")
        with open("q_table.pkl", "wb") as f:
            pickle.dump(agent.Q, f)

        print("保存しました:", save_path)
        plt.figure(figsize=(20,10))
        plt.plot(range(1, len(steps_per_episode)+1), steps_per_episode, color="blue")
        plt.xlabel("Episode")
        plt.ylabel("Steps per Episode")
        plt.title("Steps per Episode in Q-Learning Hunter Task")
        plt.xticks(range(0, MAX_EPISODES+1, 100))
        max_steps = max(steps_per_episode)
        plt.yticks(range(0, int(max_steps)+100, 10))
        plt.grid(True)
        plt.show()
        pygame.quit()
        sys.exit()
        

    # --- 表示更新 ---

    text_count = font.render(f"Total Steps: {count_total_steps}", True, (255, 0, 0))
    text_ep = font.render(f"Episode: {episode}  Steps(episode): {steps_in_episode}  epsilon: {agent.epsilon:.3f}", True, (0, 0, 255))

    # --- 描画 ---
    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    screen.blit(text_count, (650, 40))
    screen.blit(text_ep, (650, 70))
    pygame.display.flip()

    if episode <= MAX_EPISODES - 30:
        clock.tick()
    else:
        clock.tick(30)

