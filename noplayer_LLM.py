import pygame
import sys
import random
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# ====== 環境変数読み込み ======
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ====== Pygame初期化 ======
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 640
TILE_SIZE = 32
WHITE = (255, 255, 255)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hunter Task - LLM Intent System")

# ====== 画像読み込み ======
def load_scaled(path):
    img = pygame.image.load(path)
    return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))

ground_img = load_scaled("images/ground.png")
player1_img = load_scaled("images/player1.png")
player2_img = load_scaled("images/player2.png")
prey1_img = load_scaled("images/prey1.png")
prey2_img = load_scaled("images/prey2.png")

font = pygame.font.SysFont(None, 24)

# ====== マップ設定 ======
GRID_W, GRID_H = 20, 20
def wrap_pos(x, y): return x % GRID_W, y % GRID_H

def move_prey(x, y):
    r = random.random()
    if r < 0.25: y -= 1
    elif r < 0.5: y += 1
    elif r < 0.75: x -= 1
    else: x += 1
    return wrap_pos(x, y)

def draw_map():
    for row in range(GRID_H):
        for col in range(GRID_W):
            screen.blit(ground_img, (col * TILE_SIZE, row * TILE_SIZE))

def draw_player(img, x, y): screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))
def draw_prey(img, x, y): screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))
def sample_non_overlapping_positions(n):
    all_positions = [(x, y) for x in range(GRID_W) for y in range(GRID_H)]
    return random.sample(all_positions, n)

# ====== レベル設定 ======
LV1 = 1  # 自己
LV2 = 0  # 相手
print(f"現在の設定: Player1(Lv{LV1}) / Player2(Lv{LV2})")

# =========================================================
#  ① 他者の意図推定
# =========================================================
def estimate_opponent_intention(state_info):
    prompt = f"""
あなたは「ハンタータスク」という環境において、他者（もう一体のハンター）の意図を推定するシステムです。
私が指示した以外の返答は一切不要です。

これ以降、あなた自身のことを「自己」、協力相手であるもう一体のハンターを「他者」と呼びます。

---

# ■ ハンタータスクの説明
ハンタータスクは、20×20のトーラス構造のグリッドで構成される環境です。
この中には2体のハンター（自己と他者）と2体の獲物（AとB）が存在します。
ハンターは獲物を捕獲することを目的とし、獲物は逃走します。

端から出ると反対側に現れるトーラス構造のため、距離の概念は循環的です。

---

# ■ あなたのタスク
入力として与えられるマップ情報から、合理的かつ一貫した形で「他者の意図（どちらの獲物を狙っているか）」を推定してください。

---

# ■ 入力（観測情報）
{json.dumps(state_info, ensure_ascii=False, indent=2)}

---

# ■ 出力フォーマット
以下のJSON形式で出力してください。
{{
  "他者の意図": "（例：獲物Aを狙っている）"
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたはハンタータスクの意図推定AIです。"},
            {"role": "user", "content": prompt},
        ]
    )
    text = response.choices[0].message.content
    try:
        result = json.loads(text)
        return result.get("他者の意図", "不明")
    except Exception:
        return text

# =========================================================
#  ② 自己の意図生成
# =========================================================
def generate_self_intention(state_info, opponent_intention):
    prompt = f"""
あなたは意図生成システムです。私が指示した以外の返答は一切不要です。
これ以降、意図生成システムであるあなたを「自己」、協力相手であるもう一体のハンターを「他者」と呼びます。

---

# ■ ハンタータスク概要
このタスクは20×20のトーラス構造マップ上で、2体のハンターと2体の獲物が存在します。
ハンターの目的は協力して獲物を捕獲することです。

---

# ■ 内部表現
あなた（自己）は以下を持ちます：
・自己の信念
・他者の信念
・自己の願望
・他者の願望
・自己の意図
・他者の意図

---

# ■ 信念・願望・意図の定義
信念：現在の世界状態の理解。箇条書き形式。
願望：達成したい目標や状態。箇条書き形式。
意図：行動を起こすための計画や戦略。1つのみ。

---

# ■ あなたのタスク
与えられた「自己の信念」「自己の願望」「他者の意図」から、矛盾のない「自己の意図」を生成してください。

---

# 入力
## 自己の信念
・自己の位置と獲物の位置から見て、捕獲までの距離が異なる
・他者は別の方向に移動している可能性がある
・マップはトーラス構造で端から端がつながっている
## 自己の願望
・タスク全体の成功（双方が異なる獲物を効率的に捕獲）
・他者との衝突を避け、効率的に探索する
## 他者の意図
{opponent_intention}

---

# 出力
## 自己の意図
（例：「他者が獲物Aを狙うなら、自分は獲物Bを狙う」など、1文で明確に記述）
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたはハンタータスクの意図生成AIです。"},
            {"role": "user", "content": prompt},
        ]
    )
    text = response.choices[0].message.content
    try:
        result = json.loads(text)
        return result.get("自己の意図", text)
    except Exception:
        return text

# =========================================================
#  ③ 行動決定
# =========================================================
def decide_action(state_info, self_intention, opponent_intention):
    prompt = f"""
あなたは「ハンタータスク」において次の行動を決定するエージェントです。
他者と協力し、全体の成功（両方の獲物を捕獲）を目指します。

---

# 入力情報
#ここで座標情報をわたしている。
{json.dumps(state_info, ensure_ascii=False, indent=2)}

自己の意図: {self_intention}
他者の意図: {opponent_intention}

---

# 出力形式
{{
  "次の行動": "上 / 下 / 左 / 右 / その場に留まる",
  "理由": "簡潔に説明"
}}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたはハンタータスクの行動決定AIです。"},
            {"role": "user", "content": prompt},
        ]
    )
    text = response.choices[0].message.content
    try:
        result = json.loads(text)
        return result
    except Exception:
        return {"次の行動": "不明", "理由": text}

# =========================================================
#  メインループ
# =========================================================
(player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y) = sample_non_overlapping_positions(4)
hunt1, hunt2 = False, False
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
    #座標の渡し方が少し変→Lv0がいる前提の渡し方になっている
    state_info = {
        "自己座標": (player1_x, player1_y),
        "他者座標": (player2_x, player2_y),
        "獲物A座標": (prey1_x, prey1_y),
        "獲物B座標": (prey2_x, prey2_y),
    }

    # --- Lv0は意図推定を行わない ---
    opponent_action = decide_action(state_info, "なし", "不明")["次の行動"]

    # --- Lv1: 意図推定 → 自己の意図生成 → 行動決定 ---
    opponent_intention = estimate_opponent_intention(state_info)
    self_intention = generate_self_intention(state_info, opponent_intention)
    result = decide_action(state_info, self_intention, opponent_intention)
    own_action = result["次の行動"]

    def apply_action(x, y, action):
        if action == "上": y -= 1
        elif action == "下": y += 1
        elif action == "左": x -= 1
        elif action == "右": x += 1
        return wrap_pos(x, y)

    player1_x, player1_y = apply_action(player1_x, player1_y, own_action)
    player2_x, player2_y = apply_action(player2_x, player2_y, opponent_action)

    if (player1_x, player1_y) == (prey1_x, prey1_y) or (player2_x, player2_y) == (prey1_x, prey1_y):
        hunt1 = True
    if (player1_x, player1_y) == (prey2_x, prey2_y) or (player2_x, player2_y) == (prey2_x, prey2_y):
        hunt2 = True

    if not hunt1:
        prey1_x, prey1_y = move_prey(prey1_x, prey1_y)
    if not hunt2:
        prey2_x, prey2_y = move_prey(prey2_x, prey2_y)

    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_player(player2_img, player2_x, player2_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    draw_prey(prey2_img, prey2_x, prey2_y)

    info = f"Lv1={LV1} Lv2={LV2} | prey1={'X' if hunt1 else 'O'} prey2={'X' if hunt2 else 'O'}"
    screen.blit(font.render(info, True, (0,0,255)), (20, 10))

    pygame.display.flip()
    clock.tick(5)
