import pygame
import sys
import random
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

# ====== 環境変数読み込み ======
# .env ファイルから OPENAI_API_KEY を読み込みます
load_dotenv()
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    print("エラー: OPENAI_API_KEYが設定されていません。")
    print(".env ファイルを作成し、APIキーを記述してください。")
    sys.exit()


# ====== Pygame初期化 ======
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 640
TILE_SIZE = 32
WHITE = (255, 255, 255)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hunter Task - LLM Intent System")

# ===== パラメータ設定 =====
# LV1: 意図推定あり（協調）/ LV0: 意図推定なし（単独）
LV1 = 1 
LV2 = 0 
GRID_W, GRID_H = 20, 20

# ====== 画像読み込みと描画関数 ======
def load_scaled(path):
    try:
        img = pygame.image.load(path)
        return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    except pygame.error:
        # 代替として、白い四角を生成
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        color = (200, 200, 200) if 'ground' in path else (255, 0, 0)
        surf.fill(color)
        return surf


# 画像パスはプロジェクト構造に合わせて調整してください
ground_img = load_scaled("images/ground.png")
player1_img = load_scaled("images/player1.png")
player2_img = load_scaled("images/player2.png")
prey1_img = load_scaled("images/prey1.png")
prey2_img = load_scaled("images/prey2.png")

font = pygame.font.SysFont(None, 24)

def wrap_pos(x, y): return x % GRID_W, y % GRID_H

def move_prey(x, y):
    r = random.random()
    if r < 0.2:
        y -= 1
    elif r < 0.6:
        x += 1
    else:
        pass
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


# ====== 視点ごとのstate_infoを作る（捕獲フラグを追加） ======
def make_state_info(self_pos, other_pos, preyA_pos, preyB_pos, hunt_A, hunt_B):
    return {
        "自己座標": self_pos,
        "他者座標": other_pos,
        "獲物A座標": preyA_pos,
        "獲物B座標": preyB_pos,
        "獲物Aを現在捕獲中": hunt_A,
        "獲物Bを現在捕獲中": hunt_B
    }


# =========================================================
#  LLM API 呼び出し共通関数
# =========================================================
def call_llm(system_prompt, user_prompt, model="gpt-4o-mini"):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            response_format={"type": "json_object"}
        )
        text = response.choices[0].message.content
        return json.loads(text)
    except Exception as e:
        print(f"\n--- LLM通信エラー ---")
        print(f"エラー内容: {e}")
        print(f"-------------------\n")
        return {"次の行動": "その場に留まる", "理由": f"LLMエラー: {e}", "他者の意図": "不明", "推定理由": "通信エラーにより推定できませんでした"}


# =========================================================
#  他者の意図推定（共通関数）
# =========================================================
def estimate_opponent_intention(state_info):
    system_prompt = f"""
    あなたは意図推定システムです。私が指示した以外の返答は一切不要です。
    これ以降、意図推定システムであるあなた自身のことを「自己」、協力相手であるもう一体のハンターを「他者」と呼びます。
    
    # ■ ハンタータスクの説明
    - マップ：幅20×高さ20のグリッド。トーラス構造のため、端から出ると反対側に回り込みます。
    - エンティティ：2体のハンター（自己・他者）と2体の獲物（A・B）が存在します。
    - ターン制：各ターンで全エージェント（ハンターと獲物）が**同時に**1行動を実行します。
    - **捕獲条件**：ターンの行動更新**後**に、ハンター一体と獲物一体の**座標が一致**したとき、その獲物は捕獲状態であるとみなされます。
        - ハンターがその座標から移動すると、即座に「未捕獲状態」に戻る。
        - 2体の獲物が同ターンに別々に捕獲されることもあります。
    - ハンター同士の位置衝突：同一セルへの同時進入や停止は**許可**（ブロッキングなし）。
    - エピソード終了条件：① 両方の獲物が捕獲された、または ② 最大ターン数 T に到達した場合。
    - 観測：各ターンで、自己・他者・獲物A・獲物Bの**現在座標**と獲物A・獲物Bが捕まっているかという情報が観測可能です。
    - 目的：
        - 目的：
        - ハンターは効率的に全ての獲物を捕獲することを目指します。
        - ターンの終了時に、**「獲物A」と「獲物B」が両方とも「捕獲中」**であればクリア。
            - 片方だけが捕獲状態であっても、ゲームは終わらない。

    # ■ タスク
    観測JSON（座標と捕獲フラグ）から、
    「他者の意図（他者がどの獲物を狙っているか）」を1つ推定し、**その推定に至った理由も簡潔に出力**してください。

    # ■ 入力
    {json.dumps(state_info, ensure_ascii=False, indent=2)}

    # ■ 出力フォーマット（厳守）
    以下のJSONのみを出力してください（追加テキスト禁止）：
    {{
    "他者の意図": "（獲物Aを狙っている / 獲物Bを狙っている / 不明）",
    "次の行動": "上 / 下 / 左 / 右 / その場に留まる", 
    "理由": "簡潔に説明",
    "推定理由": "他者や獲物の位置に基づいて、推定に至った具体的な理由"
    }}
    """.strip()

    user_prompt = f"""{json.dumps(state_info, ensure_ascii=False, indent=2)}""".strip()
    return call_llm(system_prompt, user_prompt)

# =========================================================
#  協調行動決定（LLM-Lv1）
# =========================================================
def decide_cooperative_action(state_info, opponent_intention_result):
    system_prompt = f"""
    あなたは行動決定システムです。私が指示した以外の返答は一切不要です。
    これ以降、行動決定システムであるあなた自身のことを「自己」、協力相手であるもう一体のハンターを「他者」と呼びます。

    # ■ ハンタータスクの説明
    - マップ：幅20×高さ20のグリッド。トーラス構造のため、端から出ると反対側に回り込みます。
    - エンティティ：2体のハンター（自己・他者）と2体の獲物（A・B）が存在します。
    - ターン制：各ターンで全エージェント（ハンターと獲物）が**同時に**1行動を実行します。
    - **捕獲条件**：ターンの行動更新**後**に、ハンター一体と獲物一体の**座標が一致**したとき、その獲物は捕獲状態であるとみなされます。
        - ハンターがその座標から移動すると、即座に「未捕獲状態」に戻る。
        - 2体の獲物が同ターンに別々に捕獲されることもあります。
    - ハンター同士の位置衝突：同一セルへの同時進入や停止は**許可**（ブロッキングなし）。
    - エピソード終了条件：① 両方の獲物が捕獲された、または ② 最大ターン数 T に到達した場合。
    - 観測：各ターンで、自己・他者・獲物A・獲物Bの**現在座標**と獲物A・獲物Bが捕まっているかという情報が観測可能です。
    - 目的：
        - ハンターは効率的に全ての獲物を捕獲することを目指します。
        - ターンの終了時に、**「獲物A」と「獲物B」が両方とも「捕獲中」**であればクリア。
            - 片方だけが捕獲状態であっても、ゲームは終わらない。   
        

    # ■ タスク
    観測JSON（座標と捕獲フラグ）と他者の意図に基づき、
    次ターンの**自己の行動**を （上, 下, 左, 右, その場に留まる）のいずれか1つで決定し、簡潔な理由とともに出力してください。
 
    # ■ 入力
    {json.dumps(state_info, ensure_ascii=False, indent=2)}

     ■ 他者の推定意図
    {json.dumps(opponent_intention_result, ensure_ascii=False, indent=2)}

    # ■ 出力フォーマット（厳守）
    以下のJSONのみを出力してください（追加テキスト禁止）：
    {{
    "次の行動": "上 / 下 / 左 / 右 / その場に留まる",
    "理由": "なぜその獲物を狙ったのという理由を具体的に説明"
    }}
    """.strip()

    user_prompt = f"""{json.dumps(state_info, ensure_ascii=False, indent=2)}""".strip()
    return call_llm(system_prompt, user_prompt)


# =========================================================
#  単独行動決定（LLM-Lv0）
# =========================================================
def decide_solo_action(state_info):
    system_prompt = f"""
    あなたは行動決定システムです。私が指示した以外の返答は一切不要です。
    これ以降、行動決定システムであるあなた自身のことを「自己」、協力相手であるもう一体のハンターを「他者」と呼びます。


    # ■ ハンタータスクの説明
    - マップ：幅20×高さ20のグリッド。トーラス構造のため、端から出ると反対側に回り込みます。
    - エンティティ：2体のハンター（自己・他者）と2体の獲物（A・B）が存在します。
    - ターン制：各ターンで全エージェント（ハンターと獲物）が**同時に**1行動を実行します。
    - **捕獲条件**：ターンの行動更新**後**に、ハンター一体と獲物一体の**座標が一致**したとき、その獲物は捕獲状態であるとみなされます。
        - ハンターがその座標から移動すると、即座に「未捕獲状態」に戻る。
        - 2体の獲物が同ターンに別々に捕獲されることもあります。
    - ハンター同士の位置衝突：同一セルへの同時進入や停止は**許可**（ブロッキングなし）。
    - エピソード終了条件：① 両方の獲物が捕獲された、または ② 最大ターン数 T に到達した場合。
    - 観測：各ターンで、自己・他者・獲物A・獲物Bの**現在座標**と獲物A・獲物Bが捕まっているかという情報が観測可能です。
    - 目的：
        - ハンターは効率的に全ての獲物を捕獲することを目指します。
        - ターンの終了時に、**「獲物A」と「獲物B」が両方とも「捕獲中」**であればクリア。
            - 片方だけが捕獲状態であっても、ゲームは終わらない。

    # ■ タスク
    観測JSON（座標と捕獲フラグ）のみに基づき、
    次ターンの**自己の行動**を （上, 下, 左, 右, その場に留まる）のいずれか1つで決定し、簡潔な理由とともに出力してください。

    # ■ 入力
    {json.dumps(state_info, ensure_ascii=False, indent=2)}

    # ■ 出力フォーマット（厳守）
    以下のJSONのみを出力してください（追加テキスト禁止）：
    {{
    "次の行動": "上 / 下 / 左 / 右 / その場に留まる",
    "理由": "なぜその獲物を狙ったのという理由を具体的に説明"
    }}
    """.strip()

    user_prompt = f"""{json.dumps(state_info, ensure_ascii=False, indent=2)}""".strip()
    return call_llm(system_prompt, user_prompt)


# =========================================================
#  メインループ
# =========================================================
(player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y) = sample_non_overlapping_positions(4)
hunt1, hunt2 = False, False
steps = 0
clock = pygame.time.Clock()

ACTION_TO_DXY = {
    "上": (0, -1), "下": (0, 1), "左": (-1, 0), "右": (1, 0), "その場に留まる": (0, 0),
}


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    steps += 1

    # === 視点ごとのstate_infoを作成（P1視点 / P2視点） ===
    # **P1視点 (Lv.1)**
    state_info_p1 = make_state_info(
        (player1_x, player1_y), (player2_x, player2_y),
        (prey1_x, prey1_y), (prey2_x, prey2_y), hunt1, hunt2
    ) 
    # **P2視点 (Lv.0)**
    state_info_p2 = make_state_info(
        (player2_x, player2_y), (player1_x, player1_y),
        (prey1_x, prey1_y), (prey2_x, prey2_y), hunt1, hunt2
    )

    # --- P2 (Lv0): 意図推定なしで行動決定 ---
    p2_result = decide_solo_action(state_info_p2)
    p2_action = p2_result["次の行動"]


    # --- P1 (Lv1): 意図推定 → 行動決定 ---
    # 1. P1視点から、P2の意図を推定する
    p2_intention = estimate_opponent_intention(state_info_p1)
    
    # 2. P1は、P2の意図と自分のstate_infoに基づいて行動を決定する
    p1_result = decide_cooperative_action(state_info_p1, p2_intention)
    p1_action = p1_result["次の行動"]


    # **【コンソールにLLMの結果を出力】**
    print("==================================================================")
    print(f"ターン: {steps} | Prey1:{'X' if hunt1 else 'O'}, Prey2:{'X' if hunt2 else 'O'}")
    # P2の推定意図とその理由を出力
    print(f"P1 (自己) 推定意図: {p2_intention.get('他者の意図', '---')}")
    print(f"P1 (自己) 推定理由: {p2_intention.get('推定理由', '---')}") 
    print(f"P1 (自己) 行動/理由: {p1_action} / {p1_result.get('理由', '---')}")
    print(f"P2 (他者) 行動/理由: {p2_action} / {p2_result.get('理由', '---')}")
    print("==================================================================")


    # === 行動の適用 ===
    def apply_action(x, y, action):
        dxy = ACTION_TO_DXY.get(action, (0, 0))
        return wrap_pos(x + dxy[0], y + dxy[1])

    player1_x, player1_y = apply_action(player1_x, player1_y, p1_action)
    player2_x, player2_y = apply_action(player2_x, player2_y, p2_action)


    # 捕獲判定
    prey1_captured = (player1_x, player1_y) == (prey1_x, prey1_y) or (player2_x, player2_y) == (prey1_x, prey1_y)
    prey2_captured = (player1_x, player1_y) == (prey2_x, prey2_y) or (player2_x, player2_y) == (prey2_x, prey2_y)
    
    # === 捕獲判定（毎ターンリセットして判定） ===
    # どちらかのプレイヤーがPrey1と同じ位置にいれば捕獲中
    hunt1 = ((player1_x, player1_y) == (prey1_x, prey1_y)) or \
            ((player2_x, player2_y) == (prey1_x, prey1_y))
            
    # どちらかのプレイヤーがPrey2と同じ位置にいれば捕獲中
    hunt2 = ((player1_x, player1_y) == (prey2_x, prey2_y)) or \
            ((player2_x, player2_y) == (prey2_x, prey2_y))
    

    # エピソード終了判定
    if hunt1 and hunt2:
        print("\n--- 全ての獲物を捕獲しました！リセットします ---")
        # リセット処理
        (player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y) = sample_non_overlapping_positions(4)
        hunt1, hunt2 = False, False
        steps = 0


    # 獲物移動
    if not hunt1:
        prey1_x, prey1_y = move_prey(prey1_x, prey1_y)
    if not hunt2:
        prey2_x, prey2_y = move_prey(prey2_x, prey2_y)

    # 描画
    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_player(player2_img, player2_x, player2_y)
    
    # 獲物の表示を常に実行 (捕獲後も同じ位置に留まる)
    draw_prey(prey1_img, prey1_x, prey1_y)
    draw_prey(prey2_img, prey2_x, prey2_y)

    # ステータス表示（Pygame画面）
    info1 = f"STEP:{steps} | P1(協調) ACT:{p1_action} | P2(単独) ACT:{p2_action} | H1:{'X' if hunt1 else 'O'} H2:{'X' if hunt2 else 'O'}"
    screen.blit(font.render(info1, True, (0,0,255)), (20, 10))

    pygame.display.flip()
    clock.tick(5) # 1秒間に5ターン