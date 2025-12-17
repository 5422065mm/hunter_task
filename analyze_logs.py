import pandas as pd
import numpy as np
import math
import os

# ==========================================
#  設定
# ==========================================
INPUT_FILE = "detailed_log_2.csv"             # 読み込むログファイル
OUTPUT_DETAIL_FILE = "analyzed_detailed_log_2.csv" # 出力：詳細分析データ
OUTPUT_SUMMARY_FILE = "analyzed_summary_2.csv"     # 出力：集計サマリー

# マップサイズ（トーラス計算用）
GRID_W = 20
GRID_H = 20

# ==========================================
#  距離計算関数 (トーラス考慮)
# ==========================================

def calc_torus_manhattan(x1, y1, x2, y2, w, h):
    """トーラス環境でのマンハッタン距離 (|dx| + |dy|)"""
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    # 通常の距離と、反対側から回った距離の小さい方を採用
    dx_torus = min(dx, w - dx)
    dy_torus = min(dy, h - dy)
    return dx_torus + dy_torus

def calc_torus_euclidean(x1, y1, x2, y2, w, h):
    """トーラス環境でのユークリッド距離 (sqrt(dx^2 + dy^2))"""
    dx = abs(x1 - x2)
    dy = abs(y1 - y2)
    # 通常の距離と、反対側から回った距離の小さい方を採用
    dx_torus = min(dx, w - dx)
    dy_torus = min(dy, h - dy)
    return math.sqrt(dx_torus**2 + dy_torus**2)

# ==========================================
#  分析ロジック
# ==========================================

def extract_target_from_text(text):
    """
    ログの文章から '獲物A' または '獲物B' を抽出する
    """
    if pd.isna(text):
        return None
    text = str(text)
    if "獲物A" in text:
        return "獲物A"
    if "獲物B" in text:
        return "獲物B"
    return None

def verify_target_choice(dist_a, dist_b, declared_target):
    """
    宣言したターゲットが、距離的に近い方の獲物と一致しているか判定する
    戻り値: '⚪︎' (合理的), '✖️' (不合理), '△' (距離が同じ), '-' (不明)
    """
    if declared_target is None:
        return "-"
    
    closer_prey = ""
    # 距離比較（浮動小数点の誤差を考慮して少し余裕を持たせても良いが、今回は単純比較）
    if dist_a < dist_b:
        closer_prey = "獲物A"
    elif dist_b < dist_a:
        closer_prey = "獲物B"
    else:
        return "△" # 距離が全く同じ

    if closer_prey == declared_target:
        return "⚪︎" # 近い方を選んでいる
    else:
        return "✖️" # 遠い方を選んでいる（あるいは別の意図がある）

def analyze_row(row):
    """
    1行ごとのデータを処理し、新しい分析結果列を返す
    """
    # 1. 座標データの取得
    lv0_x = row['Lv0_X']
    lv0_y = row['Lv0_Y']
    prey_a_x = row['PreyA_X']
    prey_a_y = row['PreyA_Y']
    prey_b_x = row['PreyB_X']
    prey_b_y = row['PreyB_Y']

    # 2. ターゲット情報の抽出
    # シミュレーションのログ列名に合わせています
    target_predicted_by_lv1 = extract_target_from_text(row.get('Lv1_意図推定'))
    target_declared_by_lv0 = extract_target_from_text(row.get('Lv0_狙い(宣言)'))

    # 3. 距離の再計算 (トーラス考慮)
    # --- マンハッタン距離 ---
    dist_m_a = calc_torus_manhattan(lv0_x, lv0_y, prey_a_x, prey_a_y, GRID_W, GRID_H)
    dist_m_b = calc_torus_manhattan(lv0_x, lv0_y, prey_b_x, prey_b_y, GRID_W, GRID_H)
    
    # --- ユークリッド距離 ---
    dist_e_a = calc_torus_euclidean(lv0_x, lv0_y, prey_a_x, prey_a_y, GRID_W, GRID_H)
    dist_e_b = calc_torus_euclidean(lv0_x, lv0_y, prey_b_x, prey_b_y, GRID_W, GRID_H)

    # 4. 分析A: 意図推定の正解判定 (Lv1予想 vs Lv0宣言)
    prediction_result = "✖️"
    if target_predicted_by_lv1 and target_declared_by_lv0:
        if target_predicted_by_lv1 == target_declared_by_lv0:
            prediction_result = "⚪︎"
        else:
            prediction_result = "✖️"
    elif target_predicted_by_lv1 is None or target_declared_by_lv0 is None:
         prediction_result = "-" # どちらかの情報が欠けている

    # 5. 分析B: Lv0の合理性判定 (マンハッタン距離基準)
    rationality_manhattan = verify_target_choice(dist_m_a, dist_m_b, target_declared_by_lv0)

    # 6. 分析C: Lv0の合理性判定 (ユークリッド距離基準)
    rationality_euclidean = verify_target_choice(dist_e_a, dist_e_b, target_declared_by_lv0)

    # 計算結果をシリーズとして返す（これが新しい列になります）
    return pd.Series([
        dist_m_a, dist_m_b, 
        round(dist_e_a, 2), round(dist_e_b, 2),
        target_predicted_by_lv1, target_declared_by_lv0,
        prediction_result,
        rationality_manhattan,
        rationality_euclidean
    ])

# ==========================================
#  メイン実行部分
# ==========================================
def main():
    # 入力チェック
    if not os.path.exists(INPUT_FILE):
        print(f"エラー: {INPUT_FILE} が見つかりません。先にシミュレーションを実行してください。")
        return

    print(f"[{INPUT_FILE}] を読み込み中...")
    df = pd.read_csv(INPUT_FILE)

    # 新しく追加する列名の定義
    new_cols = [
        '再計算_Lv0-A距離(マンハッタン)', '再計算_Lv0-B距離(マンハッタン)',
        '再計算_Lv0-A距離(ユークリッド)', '再計算_Lv0-B距離(ユークリッド)',
        '抽出_Lv1予想ターゲット', '抽出_Lv0宣言ターゲット',
        '判定_意図推定一致',           # Lv1の予想が当たったか
        '判定_距離合理性(マンハッタン)', # Lv0はマンハッタン距離で近い方を狙ったか
        '判定_距離合理性(ユークリッド)'  # Lv0はユークリッド距離で近い方を狙ったか
    ]

    print("データを分析中...")
    # 1行ずつ関数を適用
    analysis_results = df.apply(analyze_row, axis=1)
    analysis_results.columns = new_cols

    # 元のデータと結合
    df_out = pd.concat([df, analysis_results], axis=1)

    # 詳細ログの保存
    df_out.to_csv(OUTPUT_DETAIL_FILE, index=False, encoding='utf-8_sig')
    print(f"詳細な分析結果を保存しました: {OUTPUT_DETAIL_FILE}")

    # ==========================================
    #  サマリー（集計表）の作成
    # ==========================================
    print("集計サマリーを作成中...")
    
    summary_list = []
    # エピソードIDごとにグループ化して集計
    grouped = df_out.groupby('Episode_ID')

    for episode_id, group in grouped:
        total_steps = len(group)
        
        # 各判定の「⚪︎」の数をカウント
        count_prediction_ok = (group['判定_意図推定一致'] == '⚪︎').sum()
        count_rational_manhattan = (group['判定_距離合理性(マンハッタン)'] == '⚪︎').sum()
        count_rational_euclidean = (group['判定_距離合理性(ユークリッド)'] == '⚪︎').sum()

        # パーセンテージ計算
        rate_prediction = round((count_prediction_ok / total_steps) * 100, 1) if total_steps > 0 else 0
        rate_manhattan = round((count_rational_manhattan / total_steps) * 100, 1) if total_steps > 0 else 0
        rate_euclidean = round((count_rational_euclidean / total_steps) * 100, 1) if total_steps > 0 else 0

        summary_list.append({
            "Episode_ID": episode_id,
            "総ステップ数": total_steps,
            "意図推定一致数": count_prediction_ok,
            "意図推定正答率(%)": rate_prediction,
            "合理的選択数(マンハッタン)": count_rational_manhattan,
            "合理的選択率_Manhattan(%)": rate_manhattan,
            "合理的選択数(ユークリッド)": count_rational_euclidean,
            "合理的選択率_Euclidean(%)": rate_euclidean
        })

    # サマリーの保存
    df_summary = pd.DataFrame(summary_list)
    df_summary.to_csv(OUTPUT_SUMMARY_FILE, index=False, encoding='utf-8_sig')
    print(f"集計サマリーを保存しました: {OUTPUT_SUMMARY_FILE}")
    print("完了しました。")

if __name__ == "__main__":
    main()