import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt 
import matplotlib
import duckdb
import os
from datetime import datetime

# Matplotlibをバックグラウンド（GUIなし）で動作させる設定
matplotlib.use('Agg')

# --- 設定 ---
INPUT_PIVOT = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/Result_calc/New/logoutput/13k/combined_pivot_2026-01-07_14-12-46.parquet"
INPUT_AGGREGATED = "Result_calc/New/logoutput/aggregated_data.parquet"
IMAGE_DIR = "HigashiKU/Result_calc/New/logoutput/image"

# 【追加】除外したいリンクIDのリスト（例：スポーン地点）
# XMLでのIDが "_p00060" の場合、ここにもアンダースコアを含めて記述してください
EXCLUDE_LINKS = ["_p00072","_p00068","_p00004", "_p00007", "_p00013", "_p00015", "_p00067", "_p00093","_p00091","_p00133","_p00038","_p00043","_p00046","_p00074","_p00075"]

# Format the time into a file-safe string (e.g., '2025-12-24_10-55-45')
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

# 横軸の刻み設定：3600秒（1時間）ごと
TICK_INTERVAL = 1800 

def load_data():
    """DuckDBを使用してデータを読み込み、除外リンクをフィルタリングする"""
    if not os.path.exists(INPUT_PIVOT):
        raise FileNotFoundError(f"ファイルが見つかりません: {INPUT_PIVOT}")
    
    print(f"Loading {INPUT_PIVOT}...")
    pivot_df = pd.read_parquet(INPUT_PIVOT).set_index('time_sec')

    # 【修正】ピボットテーブルの列から除外リンクを削除
    if EXCLUDE_LINKS:
        cols_to_keep = [col for col in pivot_df.columns 
                        if not any(link in col for link in EXCLUDE_LINKS)]
        pivot_df = pivot_df[cols_to_keep]
    
    aggregated_sample = None
    if os.path.exists(INPUT_AGGREGATED):
        print(f"Sampling {INPUT_AGGREGATED}...")
        con = duckdb.connect()
        # 【修正】サンプル時にもリンクIDでフィルタリング
        filter_str = ""
        if EXCLUDE_LINKS:
            # SQLの IN 句用にリストを整形 ('_p00060', '_p00107')
            links_str = ", ".join([f"'{l}'" for l in EXCLUDE_LINKS])
            filter_str = f"WHERE current_linkID NOT IN ({links_str})"
            
        aggregated_sample = con.execute(f"""
            SELECT x_mean, y_mean, v_mean 
            FROM '{INPUT_AGGREGATED}' 
            {filter_str}
            USING SAMPLE 100000 ROWS
        """).df()
    
    return pivot_df, aggregated_sample

def get_top_links(pivot_df, n=10):
    """除外後のデータから上位N個のリンクを特定する"""
    count_cols = [col for col in pivot_df.columns if col.endswith('_count')]
    
    # 既にload_dataでフィルタリングされているが、念のため再確認
    top_cols = pivot_df[count_cols].sum().sort_values(ascending=False).head(n).index
    return [col.replace('_count', '') for col in top_cols]

def plot_metric(pivot_df, top_links, metric_suffix, title, ylabel, save_path, kind='line'):
    target_cols = [f"{link}_{metric_suffix}" for link in top_links if f"{link}_{metric_suffix}" in pivot_df.columns]
    if not target_cols: return

    data_to_plot = pivot_df[target_cols].copy()
    data_to_plot.columns = [col.lstrip('_').replace(f'_{metric_suffix}', '') for col in data_to_plot.columns]

    plt.figure(figsize=(16, 9))
    if kind == 'bar':
        ax = data_to_plot.plot(kind='bar', stacked=True, figsize=(16, 9), width=1.0)
    else:
        ax = data_to_plot.plot(kind='line', figsize=(16, 9))
    
    all_times = pivot_df.index.values
    tick_positions = np.where(all_times % TICK_INTERVAL == 0)[0]
    
    if len(tick_positions) > 0:
        labels = [f'{all_times[pos]:.0f}s' for pos in tick_positions]
        ax.set_xticks(tick_positions)
        ax.set_xticklabels(labels, rotation=45)

    plt.title(title)
    plt.xlabel('Time [seconds]')
    plt.ylabel(ylabel)
    plt.legend(title='Link ID', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()
    print(f"Generated: {save_path}")

if __name__ == "__main__":
    os.makedirs(IMAGE_DIR, exist_ok=True)
    try:
        pivot_df, df_sample = load_data()
        top_10 = get_top_links(pivot_df, n=10)
        
        # 密度のプロット
        plot_metric(pivot_df, top_10, "density", "Population Density per Link", "Density [Agents/m²]", 
                    os.path.join(IMAGE_DIR, f"population_density_top10_{timestamp}.png"), kind='line')
        
        # 人数のプロット
        plot_metric(pivot_df, top_10, "count", "Agent Count per Link", "Number of Agents", 
                    os.path.join(IMAGE_DIR, f"agent_count_top10_{timestamp}.png"), kind='bar')

        print("\n除外設定を適用してグラフ生成を完了しました。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")