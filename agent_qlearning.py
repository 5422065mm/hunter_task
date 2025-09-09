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


prey1_img = pygame.image.load("images/prey1.png")   # 獲物エージェントの画像
prey1_img = pygame.transform.scale(prey1_img, (TILE_SIZE, TILE_SIZE))


# プレイヤー・獲物の初期位置
all_positions = [(x, y) for x in range(len(map_data[0])) for y in range(len(map_data))]
# 重複なしでランダムに座標を決める
player1_pos, prey1_pos = random.sample(all_positions, 2)
player1_x, player1_y = player1_pos
prey1_x, prey1_y = prey1_pos

# 動き判定
#moved1 = False
#moved2 = False
hunt1 = False


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
        prey_y -= 1
        if prey_y  < 0:
            prey_y = len(map_data) - 1
    elif r < 0.6:  # 40%で右に移動
        prey_x += 1
        if prey_x  > len(map_data[0]) - 1:
            prey_x = 0
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

        moved1 = False
        

        # プレイヤー移動（キー入力）
        if event.type == pygame.KEYDOWN:
            
            
            # プレイヤー1の操作
            if event.key == pygame.K_UP:
                player1_y -= 1
                if player1_y  < 0:
                    player1_y = len(map_data) - 1
                moved1 = True
            if event.key == pygame.K_DOWN:
                player1_y += 1
                if player1_y > len(map_data) - 1:
                    player1_y = 0
                moved1 = True
            if event.key == pygame.K_LEFT:
                player1_x -= 1
                if player1_x < 0:
                    player1_x = len(map_data[0]) - 1
                moved1 = True
            if event.key == pygame.K_RIGHT:
                player1_x += 1
                if player1_x > len(map_data[0]) - 1:
                    player1_x = 0
                moved1 = True
            if event.key == pygame.K_SPACE:
                moved1 = True


            

            if moved1:
            
                
                
                # 獲物の動き
                if not hunt1:
                    prey1_x, prey1_y = move_prey(prey1_x, prey1_y)

                # 獲物が捕まるとカウントを止める
                if not hunt1:
                    count += 1

           

                # 捕獲判定
                if not hunt1:  # prey1 がまだ捕まっていないときだけチェック
                    if (player1_x, player1_y) == (prey1_x, prey1_y):
                        hunt1 = True
            
            message_hunt = "Preys are " + ("HUNTED!" if hunt1 else "Not hunted")
            text_hunt = font1.render(message_hunt, True, (255, 0, 0))

            message_count = "Count : " + str(count)
            text_count = font1.render(message_count, True, (255, 0, 0))
            

    # 描画
    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    screen.blit(text_hunt, (670, 10))
    screen.blit(text_count, (670, 50))
    pygame.display.flip()
    

    clock.tick(30)  # 30fpsで描画（ただし獲物はプレイヤー移動時しか動かない）
"""





















"""
import pygame
import sys
import random

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
    #クラスを飛び出されたときに一番最初に必ず実行されるコード
    #今回の場合だと、マップの幅や成長率などを定義する箇所
    def __init__(self, grid_w, grid_h, actions, alpha=0.2, gamma=0.95, eps_start=1.0, eps_end=0.05, eps_decay=0.999):
        self.grid_w = grid_w
        self.grid_h = grid_h
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = eps_start
        self.eps_end = eps_end
        self.eps_decay = eps_decay
        self.Q = {}  # Q[(hx,hy,px,py)][action] = value

    #クラスの最初に呼び出される_init_の風習を真似してつけた名前
    #Qテーブルがないつまり、一度も学習が行われていないときに呼び出される関数
    #Qという変数は行動価値をまとめている辞書
    #今まで見たことのない状態（座標）の時に更新される
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
        #今まで見たことのない状態（座標）の時に更新される
        self._init_state(s)
        #この後に出てくる式でs_nextがあるのでs_nextについても更新されている
        self._init_state(s_next)
        q_sa = self.Q[s][a]
        max_next = max(self.Q[s_next].values())
        #よく出てくる数式の箇所
        self.Q[s][a] = q_sa + self.alpha * (r + self.gamma * max_next - q_sa)
        if self.epsilon > self.eps_end:
            self.epsilon *= self.eps_decay

def wrap_pos(x, y, w, h):
    return x % w, y % h

ACTION_TO_DXY = {
    "UP":    (0, -1),
    "DOWN":  (0,  1),
    "LEFT":  (-1, 0),
    "RIGHT": (1,  0),
    "STAY":  (0,  0),
}

# 位置表示/描画
def draw_map():
    for row in range(len(map_data)):
        for col in range(len(map_data[row])):
            if map_data[row][col] == 0:
                screen.blit(ground_img, (col * TILE_SIZE, row * TILE_SIZE))

def draw_player(img, x, y):
    screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))

def draw_prey(img, x, y):
    screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))

# 獲物のランダム移動（既存仕様：上20%, 右40%, それ以外は停止。トーラス）
def move_prey(prey_x, prey_y):
    r = random.random()
    if r < 0.2:
        prey_y -= 1
    elif r < 0.6:
        prey_x += 1
    else:
        pass
    return wrap_pos(prey_x, prey_y, GRID_W, GRID_H)

# 初期配置（重複なし）
def sample_non_overlapping_positions(n):
    all_positions = [(x, y) for x in range(GRID_W) for y in range(GRID_H)]
    return random.sample(all_positions, n)

(player1_x, player1_y), (prey1_x, prey1_y) = sample_non_overlapping_positions(2)

# 学習用オブジェクトなど
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

def reset_episode():
    global player1_x, player1_y, prey1_x, prey1_y, hunt1, steps_in_episode, episode
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

    # --- Q学習でハンターが行動 ---
    #現在の状態
    state = (player1_x, player1_y, prey1_x, prey1_y)
    #行動を選択
    action = agent.select_action(state)

    #実際に動かす処理
    dx, dy = ACTION_TO_DXY[action]
    #壁に行くと反対から出てくるやつ
    player1_x, player1_y = wrap_pos(player1_x + dx, player1_y + dy, GRID_W, GRID_H)

    if not hunt1:
        prey1_x, prey1_y = move_prey(prey1_x, prey1_y)

    caught = (player1_x, player1_y) == (prey1_x, prey1_y)
    #捕まえたら正の報酬、捕まえていないときは負の報酬
    reward = 10.0 if caught else -0.1
    hunt1 = caught

    #動いた後の状態（位置情報・座標）を表す
    next_state = (player1_x, player1_y, prey1_x, prey1_y)
    #Q値更新
    agent.update(state, action, reward, next_state)

    steps_in_episode += 1
    count_total_steps += 1

    # 捕獲したら新しいエピソードへ
    if hunt1:
        reset_episode()

    # --- 表示文字の更新 ---
    status = "HUNTED!" if hunt1 else "Not hunted"
    text_hunt = font.render(f"Prey: {status}", True, (255, 0, 0))
    text_count = font.render(f"Total Steps: {count_total_steps}", True, (255, 0, 0))
    text_ep = font.render(f"Episode: {episode}  Steps(episode): {steps_in_episode}  epsilon: {agent.epsilon:.3f}", True, (0, 0, 255))

    # --- 描画 ---
    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    screen.blit(text_hunt, (650, 10))
    screen.blit(text_count, (650, 40))
    screen.blit(text_ep, (520, 70))
    pygame.display.flip()

    clock.tick(30)  # 30FPS
"""


import pygame
import sys
import random
import matplotlib.pyplot as plt

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
    def __init__(self, grid_w, grid_h, actions, alpha=0.2, gamma=0.95, eps_start=1.0, eps_end=0.05, eps_decay=0.999):
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
    if r < 0.2:
        prey_y -= 1
    elif r < 0.6:
        prey_x += 1
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
MAX_EPISODES = 1000
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
    #報酬の設定を変えたほうが良いかも
    reward = 10.0 if caught else -0.1
    hunt1 = caught

    next_state = (player1_x, player1_y, prey1_x, prey1_y)
    agent.update(state, action, reward, next_state)

    steps_in_episode += 1
    count_total_steps += 1

    # エピソード終了条件
    if hunt1 or episode > MAX_EPISODES:
        reset_episode()

    # 1000エピソード終了でグラフ描画
    if episode > MAX_EPISODES:
        plt.figure(figsize=(12,6))
        plt.plot(range(1, len(steps_per_episode)+1), steps_per_episode, color="blue")
        plt.xlabel("Episode")
        plt.ylabel("Steps per Episode")
        plt.title("Steps per Episode in Q-Learning Hunter Task")
        plt.xticks(range(0, MAX_EPISODES+1, 100))
        max_steps = max(steps_per_episode)
        plt.yticks(range(0, int(max_steps)+100, 100))
        plt.grid(True)
        plt.show()
        pygame.quit()
        sys.exit()

    # --- 表示更新 ---
    status = "HUNTED!" if hunt1 else "Not hunted"
    text_hunt = font.render(f"Prey: {status}", True, (255, 0, 0))
    text_count = font.render(f"Total Steps: {count_total_steps}", True, (255, 0, 0))
    text_ep = font.render(f"Episode: {episode}  Steps(episode): {steps_in_episode}  epsilon: {agent.epsilon:.3f}", True, (0, 0, 255))

    # --- 描画 ---
    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    screen.blit(text_hunt, (650, 10))
    screen.blit(text_count, (650, 40))
    screen.blit(text_ep, (520, 70))
    pygame.display.flip()

    if episode <= 970:
        clock.tick()
    else:
        clock.tick(30)

