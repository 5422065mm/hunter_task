import pandas as pd
import os

# ==========================================
#  ファイル設定
# ==========================================
INPUT_FILE = "analyzed_detailed_log_2.csv"
OUTPUT_FILE = "cooperation_rate_result_2.csv"

# ==========================================
#  データ処理関数
# ==========================================

def extract_target_from_text(text):
    """
    テキストから '獲物A' または '獲物B' を抽出して正規化する関数
    """
    if pd.isna(text):
        return None
    text = str(text)
    if "獲物A" in text:
        return "獲物A"
    if "獲物B" in text:
        return "獲物B"
    return None

def check_division_of_labor(prediction, self_target):
    """
    分業（協調）判定ロジック
    Lv1の「他者への予想」と「自分の狙い」が【異なる】ならば協調成功(⚪︎)とする
    """
    # どちらかの情報が欠けている場合は判定不能として除外
    if not prediction or not self_target:
        return "-"
    
    # ターゲットが異なる場合 = 分業成功 (Cooperation)
    if prediction != self_target:
        return "⚪︎"
    # ターゲットが同じ場合 = 被り (Conflict)
    else:
        return "✖️"

# ==========================================
#  メイン処理
# ==========================================
def main():
    # ファイル存在確認
    if not os.path.exists(INPUT_FILE):
        print(f"エラー: {INPUT_FILE} が見つかりません。")
        return

    print(f"[{INPUT_FILE}] を読み込み中...")
    try:
        df = pd.read_csv(INPUT_FILE)
    except Exception as e:
        print(f"ファイル読み込みエラー: {e}")
        return

    # 1. データの準備
    col_prediction = '抽出_Lv1予想ターゲット'
    
    # Lv1自身の狙いを抽出・正規化
    print("データを解析中...")
    lv1_self_targets = df['Lv1_狙い(宣言)'].apply(extract_target_from_text)

    # 2. 協調判定の実施
    cooperation_results = []
    for pred, self_target in zip(df[col_prediction], lv1_self_targets):
        result = check_division_of_labor(pred, self_target)
        cooperation_results.append(result)

    # DataFrameに追加
    df['抽出_Lv1自身の狙い'] = lv1_self_targets
    df['判定_分業成功'] = cooperation_results

    # 3. エピソードごとの集計（総ステップ数を含む）
    print("協調率とステップ数を集計中...")
    summary_list = []
    
    grouped = df.groupby('Episode_ID')

    for episode_id, group in grouped:
        # 総ステップ数（そのエピソードの行数＝ターン数）
        total_steps = len(group)

        # 有効データ（⚪︎ または ✖️）のみを抽出
        valid_rows = group[group['判定_分業成功'].isin(['⚪︎', '✖️'])]
        
        valid_count = len(valid_rows)
        success_count = len(valid_rows[valid_rows['判定_分業成功'] == '⚪︎'])
        fail_count = valid_count - success_count
        
        # パーセンテージ計算
        if valid_count > 0:
            success_rate = round((success_count / valid_count) * 100, 2)
        else:
            success_rate = 0.0

        summary_list.append({
            "Episode_ID": episode_id,
            "総ステップ数": total_steps,      # <--- 追加項目
            "有効判定数": valid_count,
            "協調成功数(分業)": success_count,
            "協調失敗数(被り)": fail_count,
            "協調成功率(%)": success_rate
        })

    # 4. ファイル保存
    df_summary = pd.DataFrame(summary_list)
    
    # 全体の平均協調率を表示
    if not df_summary.empty:
        overall_avg = round(df_summary['協調成功率(%)'].mean(), 2)
        avg_steps = round(df_summary['総ステップ数'].mean(), 1)
        print(f"\n=== 分析結果 ===")
        print(f"全エピソード平均ステップ数: {avg_steps}")
        print(f"全エピソード平均 協調成功率: {overall_avg}%")

    df_summary.to_csv(OUTPUT_FILE, index=False, encoding='utf-8_sig')
    print(f"\n集計結果を保存しました: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()