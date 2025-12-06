import pygame
import sys
import random
import json
import os
import math
import statistics
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# ====== 環境変数読み込み ======
load_dotenv()
try:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except Exception:
    print("エラー: OPENAI_API_KEYが設定されていません。")
    sys.exit()

# =========================================================
#  ★ シード値設定 (再現用)
# =========================================================
# 特定の配置・展開を再現したい場合は、ここにログに記録された数値を入れてください。
# 例: REPLAY_SEEDS = [837412, 102938]
# 空リスト [] の場合は、毎回ランダムなシード値が生成されます。
REPLAY_SEEDS = [] 

# =========================================================
#  ログ収集・分析用クラス
# =========================================================
class SimulationLogger:
    def __init__(self, map_width=20, map_height=20):
        self.turn_logs = []
        self.episode_results = []
        self.width = map_width
        self.height = map_height

    def _calc_manhattan(self, p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])

    def _calc_torus_manhattan(self, p1, p2):
        dx = abs(p1[0] - p2[0])
        dy = abs(p1[1] - p2[1])
        dx_torus = min(dx, self.width - dx)
        dy_torus = min(dy, self.height - dy)
        return dx_torus + dy_torus

    # ★ seed引数を追加
    def add_turn_log(self, episode_id, current_turn, seed, lv1_info, lv0_info, pos_lv1, pos_lv0, pos_prey_a, pos_prey_b):
        dist_m_lv0_a = self._calc_manhattan(pos_lv0, pos_prey_a)
        dist_t_lv0_a = self._calc_torus_manhattan(pos_lv0, pos_prey_a)
        dist_m_lv0_b = self._calc_manhattan(pos_lv0, pos_prey_b)
        dist_t_lv0_b = self._calc_torus_manhattan(pos_lv0, pos_prey_b)

        record = {
            "Episode_ID": episode_id,
            "Seed": seed,  # ★ シード値を記録
            "現在のターン": current_turn,
            # Lv1
            "Lv1_意図推定": lv1_info.get("intent", ""),
            "Lv1_推定理由": lv1_info.get("intent_reason", ""),
            "Lv1_決定行動": lv1_info.get("action", ""),
            "Lv1_行動理由": lv1_info.get("action_reason", ""),
            # Lv0
            "Lv0_決定行動": lv0_info.get("action", ""),
            "Lv0_行動理由": lv0_info.get("action_reason", ""),
            # 座標
            "Lv1_X": pos_lv1[0], "Lv1_Y": pos_lv1[1],
            "Lv0_X": pos_lv0[0], "Lv0_Y": pos_lv0[1],
            "PreyA_X": pos_prey_a[0], "PreyA_Y": pos_prey_a[1],
            "PreyB_X": pos_prey_b[0], "PreyB_Y": pos_prey_b[1],
            # 距離
            "Lv0-PreyA(Manhattan)": dist_m_lv0_a,
            "Lv0-PreyA(Torus)": dist_t_lv0_a,
            "Lv0-PreyB(Manhattan)": dist_m_lv0_b,
            "Lv0-PreyB(Torus)": dist_t_lv0_b
        }
        self.turn_logs.append(record)

    def log_episode_end(self, episode_id, final_turn, seed, result_note=""):
        self.episode_results.append({
            "Episode_ID": episode_id,
            "Seed": seed, # ★ 結果一覧にもシード値を記録
            "End_Turn": final_turn,
            "Note": result_note
        })

    def save_all_logs(self, detail_filename="detailed_log.csv", summary_filename="summary_stats.csv"):
        print("\n--- ログ保存処理開始 ---")
        if self.turn_logs:
            df_detail = pd.DataFrame(self.turn_logs)
            sort_order = [
                "Episode_ID", "Seed", "現在のターン", # Seedを先頭付近に
                "Lv1_意図推定", "Lv1_推定理由", "Lv1_決定行動", "Lv1_行動理由",
                "Lv0_決定行動", "Lv0_行動理由",
                "Lv1_X", "Lv1_Y", "Lv0_X", "Lv0_Y", 
                "PreyA_X", "PreyA_Y", "PreyB_X", "PreyB_Y",
                "Lv0-PreyA(Manhattan)", "Lv0-PreyA(Torus)", 
                "Lv0-PreyB(Manhattan)", "Lv0-PreyB(Torus)"
            ]
            existing_cols = [c for c in sort_order if c in df_detail.columns]
            df_detail[existing_cols].to_csv(detail_filename, index=False, encoding='utf-8_sig')
            print(f"詳細ログを保存しました: {detail_filename}")

        if self.episode_results:
            turns = [r["End_Turn"] for r in self.episode_results]
            count = len(turns)
            avg_turn = round(statistics.mean(turns), 2) if count > 0 else 0
            max_turn = max(turns) if count > 0 else 0
            min_turn = min(turns) if count > 0 else 0
            
            with open(summary_filename, 'w', encoding='utf-8_sig') as f:
                f.write("【統計サマリー】\n")
                f.write(f"試行回数,{count}\n")
                f.write(f"平均ターン数,{avg_turn}\n")
                f.write(f"最大ターン数,{max_turn}\n")
                f.write(f"最小ターン数,{min_turn}\n")
                f.write("\n")
                f.write("【エピソード別結果】\n")
                f.write("Episode_ID,Seed,終了ターン,結果メモ\n")
                for res in self.episode_results:
                    f.write(f"{res['Episode_ID']},{res['Seed']},{res['End_Turn']},{res['Note']}\n")
            print(f"統計サマリーを保存しました: {summary_filename}")
        print("--- 処理完了 ---")

# =========================================================
#  Pygame初期化
# =========================================================
pygame.init()
SCREEN_WIDTH, SCREEN_HEIGHT = 900, 640
TILE_SIZE = 32
WHITE = (255, 255, 255)
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Hunter Task - Reproducible Seed System")

GRID_W, GRID_H = 20, 20

def load_scaled(path):
    try:
        img = pygame.image.load(path)
        return pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
    except pygame.error:
        surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
        color = (200, 200, 200) if 'ground' in path else (255, 0, 0)
        surf.fill(color)
        return surf

ground_img = load_scaled("images/ground.png")
player1_img = load_scaled("images/player1.png")
player2_img = load_scaled("images/player2.png")
prey1_img = load_scaled("images/prey1.png")
prey2_img = load_scaled("images/prey2.png")

font = pygame.font.SysFont(None, 24)

def wrap_pos(x, y): return x % GRID_W, y % GRID_H

def move_prey(x, y):
    r = random.random()
    if r < 0.2: y -= 1
    elif r < 0.6: x += 1
    return wrap_pos(x, y)

def draw_map():
    for row in range(GRID_H):
        for col in range(GRID_W):
            screen.blit(ground_img, (col * TILE_SIZE, row * TILE_SIZE))

def draw_player(img, x, y): screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))
def draw_prey(img, x, y): screen.blit(img, (x * TILE_SIZE, y * TILE_SIZE))

# 初期配置関数
def sample_non_overlapping_positions(n):
    all_positions = [(x, y) for x in range(GRID_W) for y in range(GRID_H)]
    return random.sample(all_positions, n)

def make_state_info(self_pos, other_pos, preyA_pos, preyB_pos, hunt_A, hunt_B):
    return {
        "自己座標": self_pos,
        "他者座標": other_pos,
        "獲物A座標": preyA_pos,
        "獲物B座標": preyB_pos,
        "獲物Aの状態": "捕獲中(HOLD)" if hunt_A else "未捕獲(FREE)",
        "獲物Bの状態": "捕獲中(HOLD)" if hunt_B else "未捕獲(FREE)"
    }

# =========================================================
#  LLM API 呼び出し
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
        print(f"LLM Error: {e}")
        return {"次の行動": "その場に留まる", "理由": "API Error", "他者の意図": "不明", "推定理由": "Error"}

def estimate_opponent_intention(state_info):
    system_prompt = f"""
    あなたは意図推定システムです。私が指示した以外の返答は一切不要です。
    これ以降、意図推定システムであるあなた自身のことを「自己」、協力相手であるもう一体のハンターを「他者」と呼びます。
    
    # ■ ハンタータスクの説明
    - マップ：幅20×高さ20のグリッド。トーラス構造のため、端から出ると反対側に回り込みます。
    - エンティティ：2体のハンター（自己・他者）と2体の獲物（A・B）が存在します。
        -獲物の動きはランダムに動くものであり、ハンターを避けるなどの意思はない。
        -20%の確率で上、40%の確率で右、40%の確率でその場に留まる。
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
    観測JSON（座標と捕獲フラグ）から、
    「他者の意図（他者がどの獲物を狙っているか）」を1つ推定し、**その推定に至った理由も簡潔に出力**してください。

    # ■ 入力
    {json.dumps(state_info, ensure_ascii=False, indent=2)}

    # ■ 出力フォーマット（厳守）
    以下のJSONのみを出力してください（追加テキスト禁止）：
    {{
    "他者の意図": "（獲物Aを狙っている / 獲物Bを狙っている / 獲物A捕獲中のためその場に留まる / 獲物B捕獲中のためその場に留まる / 不明）",
    "次の行動": "上 / 下 / 左 / 右 / その場に留まる", 
    "理由": "簡潔に説明",
    "推定理由": "他者や獲物の位置に基づいて、推定に至った具体的な理由"
    }}
    """.strip()
    user_prompt = f"""{json.dumps(state_info, ensure_ascii=False, indent=2)}""".strip()
    return call_llm(system_prompt, user_prompt)

def decide_cooperative_action(state_info, opponent_intention_result):
    system_prompt = f"""
    あなたは行動決定システムです。私が指示した以外の返答は一切不要です。
    これ以降、行動決定システムであるあなた自身のことを「自己」、協力相手であるもう一体のハンターを「他者」と呼びます。

    # ■ ハンタータスクの説明
    - マップ：幅20×高さ20のグリッド。トーラス構造のため、端から出ると反対側に回り込みます。
    - エンティティ：2体のハンター（自己・他者）と2体の獲物（A・B）が存在します。
        -獲物の動きはランダムに動くものであり、ハンターを避けるなどの意思はない。
        -20%の確率で上、40%の確率で右、40%の確率でその場に留まる。
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

def decide_solo_action(state_info):
    system_prompt = f"""
    あなたは行動決定システムです。私が指示した以外の返答は一切不要です。
    これ以降、行動決定システムであるあなた自身のことを「自己」、協力相手であるもう一体のハンターを「他者」と呼びます。


    # ■ ハンタータスクの説明
    - マップ：幅20×高さ20のグリッド。トーラス構造のため、端から出ると反対側に回り込みます。
    - エンティティ：2体のハンター（自己・他者）と2体の獲物（A・B）が存在します。
        -獲物の動きはランダムに動くものであり、ハンターを避けるなどの意思はない。
        -20%の確率で上、40%の確率で右、40%の確率でその場に留まる。
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
#  メインループ (シード値管理付き)
# =========================================================
logger = SimulationLogger(map_width=GRID_W, map_height=GRID_H)

episode_count = 1
current_steps = 0
clock = pygame.time.Clock()

ACTION_TO_DXY = {
    "上": (0, -1), "下": (0, 1), "左": (-1, 0), "右": (1, 0), "その場に留まる": (0, 0),
}

# --- ★ エピソード開始の準備関数 ---
def setup_episode(ep_num):
    # シード値の決定: REPLAY_SEEDSリストにあればそれを、なければランダム
    if len(REPLAY_SEEDS) >= ep_num:
        seed_val = REPLAY_SEEDS[ep_num - 1]
    else:
        seed_val = random.randint(0, 999999)
    
    # ★ シード値を適用 (これで座標と獲物の動きが固定される)
    random.seed(seed_val)
    
    # 座標生成 (シード値の影響を受ける)
    positions = sample_non_overlapping_positions(4)
    
    print(f"\n>>> Episode {ep_num} Start | Seed: {seed_val} <<<")
    return seed_val, positions[0], positions[1], positions[2], positions[3]

# 初回エピソードのセットアップ
current_seed, (player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y) = setup_episode(episode_count)
hunt1, hunt2 = False, False

print("=== シミュレーション開始 ===")
print(f"再現用シード値リスト: {REPLAY_SEEDS}")

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            print("\n終了シグナル受信。ログを保存します...")
            logger.save_all_logs()
            pygame.quit()
            sys.exit()

    current_steps += 1

    # State Info
    state_info_p1 = make_state_info((player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y), hunt1, hunt2) 
    state_info_p2 = make_state_info((player2_x, player2_y), (player1_x, player1_y), (prey1_x, prey1_y), (prey2_x, prey2_y), hunt1, hunt2)

    # 行動決定
    p2_result = decide_solo_action(state_info_p2)
    p2_action = p2_result.get("次の行動", "その場に留まる")

    p2_intention = estimate_opponent_intention(state_info_p1)
    p1_result = decide_cooperative_action(state_info_p1, p2_intention)
    p1_action = p1_result.get("次の行動", "その場に留まる")

    # ログ記録
    lv1_log_info = {
        "intent": p2_intention.get("他者の意図", "不明"),
        "intent_reason": p2_intention.get("推定理由", ""),
        "action": p1_action,
        "action_reason": p1_result.get("理由", "")
    }
    lv0_log_info = {
        "action": p2_action,
        "action_reason": p2_result.get("理由", "")
    }
    
    logger.add_turn_log(
        episode_id=episode_count,
        current_turn=current_steps,
        seed=current_seed, # ★シード値を保存
        lv1_info=lv1_log_info,
        lv0_info=lv0_log_info,
        pos_lv1=(player1_x, player1_y),
        pos_lv0=(player2_x, player2_y),
        pos_prey_a=(prey1_x, prey1_y),
        pos_prey_b=(prey2_x, prey2_y)
    )

    # コンソール出力 (詳細形式)
    print("==================================================================")
    print(f"Ep:{episode_count} Turn: {current_steps} (Seed:{current_seed}) | Prey1:{'X' if hunt1 else 'O'}, Prey2:{'X' if hunt2 else 'O'}")
    print(f"P1 (自己) 推定意図: {p2_intention.get('他者の意図', '---')}")
    print(f"P1 (自己) 推定理由: {p2_intention.get('推定理由', '---')}") 
    print(f"P1 (自己) 行動/理由: {p1_action} / {p1_result.get('理由', '---')}")
    print(f"P2 (他者) 行動/理由: {p2_action} / {p2_result.get('理由', '---')}")
    print("==================================================================")

    # 行動反映
    def apply_action(x, y, action):
        dxy = ACTION_TO_DXY.get(action, (0, 0))
        return wrap_pos(x + dxy[0], y + dxy[1])

    player1_x, player1_y = apply_action(player1_x, player1_y, p1_action)
    player2_x, player2_y = apply_action(player2_x, player2_y, p2_action)

    # 捕獲判定
    hunt1 = ((player1_x, player1_y) == (prey1_x, prey1_y)) or ((player2_x, player2_y) == (prey1_x, prey1_y))
    hunt2 = ((player1_x, player1_y) == (prey2_x, prey2_y)) or ((player2_x, player2_y) == (prey2_x, prey2_y))
    
    # 終了判定
    if (hunt1 and hunt2) or current_steps >= 100:
        note = "Clear" if (hunt1 and hunt2) else "TimeUp"
        print(f"\n--- Ep {episode_count} Finished: {note} ---")
        
        logger.log_episode_end(episode_id=episode_count, final_turn=current_steps, seed=current_seed, result_note=note)
        
        # 次のエピソードへ
        episode_count += 1
        current_steps = 0
        current_seed, (player1_x, player1_y), (player2_x, player2_y), (prey1_x, prey1_y), (prey2_x, prey2_y) = setup_episode(episode_count)
        hunt1, hunt2 = False, False

    # 獲物移動
    if not hunt1: prey1_x, prey1_y = move_prey(prey1_x, prey1_y)
    if not hunt2: prey2_x, prey2_y = move_prey(prey2_x, prey2_y)

    screen.fill(WHITE)
    draw_map()
    draw_player(player1_img, player1_x, player1_y)
    draw_player(player2_img, player2_x, player2_y)
    draw_prey(prey1_img, prey1_x, prey1_y)
    draw_prey(prey2_img, prey2_x, prey2_y)

    info1 = f"Ep:{episode_count} St:{current_steps} | Seed:{current_seed}"
    screen.blit(font.render(info1, True, (0,0,255)), (20, 10))

    pygame.display.flip()
    clock.tick(0)