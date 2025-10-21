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
# --- System Prompt: 意図推定モジュール（最新版） ------------------------------------
    system_prompt = f"""
    あなたは「ハンタータスク」という環境において、他者（もう一体のハンター）の意図を推定するシステムです。
    私が指示した以外の返答は一切不要です。

    これ以降、意図推定システムであるあなた自身のことを「自己」、協力相手であるもう一体のハンターのことを「他者」と呼びます。

    ---

    # ■ ハンタータスクの説明
    - マップ：幅20×高さ20のグリッド。トーラス構造のため、端から出ると反対側に回り込みます。
    - エンティティ：2体のハンター（自己・他者）と2体の獲物（A・B）が存在します。
    - ターン制：各ターンで全エージェント（ハンターと獲物）が**同時に**1行動を実行します。
    - 距離の定義（トーラス・マンハッタン距離）：
    - dx = min(|x1−x2|, W−|x1−x2|), dy = min(|y1−y2|, H−|y1−y2|)
    - dist = dx + dy（ここで W=20, H=20）
    - **捕獲条件**：ターンの行動更新**後**に、ハンターと獲物の**座標が一致**したとき、その獲物は捕獲されたとみなされます。
    - 同一ターンに複数ハンターが同一獲物を捕獲した場合も、捕獲は1回として扱います。
    - 2体の獲物が同ターンに別々に捕獲されることもあります。
    - ハンター同士の位置衝突：同一セルへの同時進入や停止は**許可**（ブロッキングなし）。
    - エピソード終了条件：① 両方の獲物が捕獲された、または ② 最大ターン数 T に到達した場合。
    - 観測：各ターンで、自己・他者・獲物A・獲物Bの**現在座標のみ**が観測可能です。
    - 目的：
    - ハンターは協調的に行動し、可能な限り少ないターンで全ての獲物を捕獲することを目指します。


    ---

    # ■ タスク
    与えられた観測情報（環境状態）から、合理的かつ一貫した形で
    「他者の意図（どの獲物を狙っているか）」を推定することです。
    他者の位置、獲物との相対距離、自己の位置を考慮して、
    もっとも整合的な意図を1つだけ推定してください。

    ---

    # ■ 入力フォーマット
    入力として、環境の観測状態をJSON形式で与えます。
    {json.dumps(state_info, ensure_ascii=False, indent=2)}

    ---

    # ■ 出力フォーマット
    以下のJSON形式で出力してください。
    {{
    "他者の意図": "（例：獲物Aを狙っている）"
    }}
    """

    # --- User Prompt: 観測情報を入力 ---------------------------------------------------
    user_prompt = f"""
    # ■ 入力（観測情報）
    {json.dumps(state_info, ensure_ascii=False, indent=2)}
    """

    # --- 推論実行 ---------------------------------------------------------------------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    # --- 出力パース処理（堅牢な形式判定付き） -----------------------------------------
    text = response.choices[0].message.content
    try:
        result = json.loads(text)
        他者の意図 = result.get("他者の意図", "不明")
    except Exception:
        他者の意図 = text  # JSON以外で出力された場合のフォールバック

    print("他者の意図:", 他者の意図)



# =========================================================
#  ② 自己の意図生成
# =========================================================
def generate_self_intention(client, state_info, self_beliefs, self_desires, opponent_intention):
    # --- System prompt -----------------------------------------------------
    system_prompt = f"""
あなたは意図生成システムです。私が指示した以外の返答は一切不要です。
これ以降、意図生成システムであるあなたを「自己」、協力相手であるもう一体のハンターを「他者」と呼びます。

---

# ■ ハンタータスクの説明
- マップ：幅20×高さ20のグリッド。トーラス構造のため、端から出ると反対側に回り込みます。
- エンティティ：2体のハンター（自己・他者）と2体の獲物（A・B）が存在します。
- ターン制：各ターンで全エージェント（ハンターと獲物）が**同時に**1行動を実行します。
- 距離の定義（トーラス・マンハッタン距離）：
  - dx = min(|x1−x2|, W−|x1−x2|), dy = min(|y1−y2|, H−|y1−y2|)
  - dist = dx + dy（ここで W=20, H=20）
- **捕獲条件**：ターンの行動更新**後**に、ハンターと獲物の**座標が一致**したとき、その獲物は捕獲されたとみなされます。
  - 同一ターンに複数ハンターが同一獲物を捕獲した場合も、捕獲は1回として扱います。
  - 2体の獲物が同ターンに別々に捕獲されることもあります。
- ハンター同士の位置衝突：同一セルへの同時進入や停止は**許可**（ブロッキングなし）。
- エピソード終了条件：① 両方の獲物が捕獲された、または ② 最大ターン数 T に到達した場合。
- 観測：各ターンで、自己・他者・獲物A・獲物Bの**現在座標のみ**が観測可能です。
- 目的：
  - ハンターは協調的に行動し、可能な限り少ないターンで全ての獲物を捕獲することを目指します。


---

# ■ 内部表現
あなたは次の内部表現を持ちます。ただし、指示がない限り、これらを出力する必要はありません。

・自己の信念  
・他者の信念  
・自己の願望  
・他者の願望  
・自己の意図  
・他者の意図  

---

# ■ 信念・願望・意図の定義
- **信念（Belief）**：  
  現在の世界状態に関する認識の集合です。  
  例：自己や他者、獲物の位置関係・距離・環境構造に関する理解。  
  複数の信念を同時に保持できます。

- **願望（Desire）**：  
  達成したい目標や望ましい状態を表します。  
  例：「獲物Aを捕獲したい」「自己と他者が異なる獲物を追いたい」など。  
  複数の願望を同時に保持できます。

- **意図（Intention）**：  
  願望を実現するために採るべき具体的な行動方針または戦略を表します。  
  例：「獲物Aに接近する」「他者の反対方向を探索する」など。  
  同時に保持できる意図は1つのみです。

なお、「他者の信念」「他者の願望」「他者の意図」は、
「自己が想定する他者の内部状態」であり、実際の内部状態と一致するとは限りません。

---

# ■ タスク
与えられた「自己の信念」「自己の願望」「他者の意図」および観測JSON（座標のみ）から、
矛盾がなく協調的合理性の高い**自己の意図**を1文で生成してください（同時に保持できる意図は1つ）。

---

# ■ 入力（Input）
- 観測情報（JSON；座標のみ）
- 自己の信念（箇条書き）
- 自己の願望（箇条書き）
- 他者の意図（テキスト1行）

---

# ■ 出力（Output）
次の**JSONのみ**を返してください（追加テキスト禁止）：
{{
  "自己の意図": "（例：他者が獲物Aを狙うなら、自分は獲物Bを狙う）"
}}
""".strip()

    # --- User prompt -------------------------------------------------------
    user_prompt = f"""
# 観測情報（JSON；座標のみ）
{json.dumps(state_info, ensure_ascii=False, indent=2)}

# 自己の信念
{chr(10).join('・' + b for b in self_beliefs)}

# 自己の願望
{chr(10).join('・' + d for d in self_desires)}

# 他者の意図
{opponent_intention}

# 出力指示
指定JSONのみを返してください。
""".strip()

    # --- 実行 ---------------------------------------------------------------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
    )

    # --- パース（堅牢な形式判定付き） ------------------------------------------
    text = response.choices[0].message.content
    try:
        result = json.loads(text)
        self_intention = result.get("自己の意図", "不明")
    except Exception:
        self_intention = text

    print("自己の意図:", self_intention)
    return self_intention


# =========================================================
#  ③ 行動決定
# =========================================================
def decide_action(state_info, self_intention, opponent_intention):
    # --- System prompt -----------------------------------------------------
    system_prompt = f"""
あなたはハンタータスクの行動決定システムです。私が指示した以外の返答は一切不要です。
これ以降、あなた自身を「自己」、協力相手のもう一体のハンターを「他者」と呼びます。

---

# ■ ハンタータスクの説明
- マップ：幅20×高さ20のグリッド。トーラス構造のため、端から出ると反対側に回り込みます。
- エンティティ：2体のハンター（自己・他者）と2体の獲物（A・B）。
- ターン制：各ターンで全エージェント（ハンターと獲物）が**同時に**1行動を実行します。
- 距離（トーラス・マンハッタン）：
  - dx = min(|x1−x2|, W−|x1−x2|), dy = min(|y1−y2|, H−|y1−y2|)
  - dist = dx + dy（W=20, H=20）
- **捕獲条件**：行動更新**後**、ハンターと獲物の**座標が一致**すると捕獲。
- ハンター同士の位置衝突：同一セルへの同時進入・停止は**許可**（ブロッキングなし）。
- エピソード終了：① 両獲物捕獲、② 最大ターン数 T 到達。
- 観測：各ターン、自己・他者・A・Bの**現在座標のみ**が観測可能。


---

# ■ 内部表現
・自己の信念
・他者の信念
・自己の願望
・他者の願望
・自己の意図
・他者の意図

# ■ 信念・願望・意図の定義
- 信念：世界状態に関する認識の集合（複数可）。
- 願望：達成したい目標や状態（複数可）。
- 意図：願望を実現するための行動方針（同時に1つ）。

なお、「他者の信念/願望/意図」は「自己が想定する他者の内部状態」であり、実際と一致するとは限りません。

---

# ■ タスク
与えられた観測JSON（座標のみ）、自己の意図、他者の意図に基づき、
次ターンの**自己の行動**を {上, 下, 左, 右, その場に留まる} のいずれか1つで決定し、簡潔な理由とともに出力してください。
トーラス距離と捕獲条件に整合し、協調（無駄な重複追跡の回避）に配慮してください。

---

# ■ 出力フォーマット（厳守）
以下のJSONのみを出力してください（追加テキスト禁止）：
{{
  "次の行動": "上 / 下 / 左 / 右 / その場に留まる",
  "理由": "簡潔に説明"
}}
""".strip()

    # --- User prompt -------------------------------------------------------
    prompt = f"""
# 入力情報（観測JSON）
{json.dumps(state_info, ensure_ascii=False, indent=2)}

自己の意図: {self_intention}
他者の意図: {opponent_intention}

# 出力指示
指定のJSONのみを返してください。
""".strip()

    # --- 実行 ---------------------------------------------------------------
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": prompt},
        ]
    )

    # --- パース -------------------------------------------------------------
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
