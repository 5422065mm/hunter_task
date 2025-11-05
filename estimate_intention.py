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
self_pos = (5,5)
other_pos = (15, 5)
preyA_pos = (5, 15)
preyB_pos = (15, 15)

state_info = {
    "自己座標": self_pos,
    "他者座標": other_pos,
    "獲物A座標": preyA_pos,
    "獲物B座標": preyB_pos,
}

def estimate_opponent_intention(state_info):
    system_prompt = f"""
    あなたは意図推定システムです。私が指示した以外の返答は一切不要です。
    これ以降、意図推定システムであるあなた自身のことを「自己」、協力相手であるもう一体のハンターを「他者」と呼びます。

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
      - ただし本プロンプトでは、行動方針や移動戦略の詳細は扱いません。
        入力としては、位置情報（座標）のみを使用します。

    ---

    # ■ 内部表現
    あなたは次の内部表現を持ちます。ただし、指示がない限り、これらを出力する必要はありません。
    ・自己の信念
    ・他者の信念
    ・自己の願望
    ・他者の願望
    ・自己の意図
    ・他者の意図

    # ■ 信念・願望・意図の定義
    - 信念：世界状態に関する認識の集合（複数可）
    - 願望：達成したい目標や状態（複数可）
    - 意図：願望を実現するための行動方針（同時に1つ）
    （他者の内部状態は自己の推定であり、実際と一致するとは限りません）

    ---

    # ■ タスク
    観測情報（座標のみ）から、合理的かつ一貫した形で
    「他者の意図（どの獲物を狙っているか）」を1つ推定してください。
    他者の位置、獲物との相対距離、自己の位置を考慮してください。

    ---

    # ■ 入力
    {json.dumps(state_info, ensure_ascii=False, indent=2)}

    ---

    # ■ 出力フォーマット
    以下のJSON形式で出力してください。
    {{
      "他者の意図": "（例：獲物Aを狙っている）"
      "意図推定の理由": "（例：獲物Aの方が近かったから）"
    }}
    """

    user_prompt = f"""{json.dumps(state_info, ensure_ascii=False, indent=2)}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
    )

    text = response.choices[0].message.content
    try:
        result = json.loads(text)
        inferred_intention = result.get("他者の意図", "不明")
        reason = result.get("意図推定の理由", "理由不明")
    except Exception:
        inferred_intention = text
        reason = "JSON解析エラーのため理由不明" 
    print("他者の意図:", inferred_intention)
    print("推定理由:", reason)
    return inferred_intention


opponent_intention = estimate_opponent_intention(state_info)