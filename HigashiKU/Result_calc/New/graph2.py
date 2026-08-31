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
INPUT_PIVOT = "HigashiKU/Result_calc/New/logoutput/combined_pivot.parquet"
INPUT_AGGREGATED = "HigashiKU/Result_calc/New/logoutput/aggregated_data.parquet"
IMAGE_DIR = "HigashiKU/Result_calc/New/logoutput/image"

now = datetime.now()

# Format the time into a file-safe string (e.g., '2025-12-24_10-55-45')
timestamp_str = now.strftime("%Y-%m-%d_%H-%M-%S")

# 横軸の刻み設定：3600秒（1時間）ごと
TICK_INTERVAL = 3600 

def load_data():
    """DuckDBを使用してメモリを節約しながらデータを読み込む"""
    if not os.path.exists(INPUT_PIVOT):
        raise FileNotFoundError(f"ファイルが見つかりません: {INPUT_PIVOT}")
    
    print(f"Loading {INPUT_PIVOT}...")
    # ピボットテーブルの読み込み
    pivot_df = pd.read_parquet(INPUT_PIVOT).set_index('time_sec')
    
    # グラフ用のサンプルデータの読み込み（aggregated_dataがある場合のみ）
    aggregated_sample = None
    if os.path.exists(INPUT_AGGREGATED):
        print(f"Sampling {INPUT_AGGREGATED}...")
        con = duckdb.connect()
        aggregated_sample = con.execute(f"""
            SELECT x_mean, y_mean, v_mean 
            FROM '{INPUT_AGGREGATED}' 
            USING SAMPLE 100000 ROWS
        """).df()
    
    return pivot_df, aggregated_sample

def get_top_links(pivot_df, n=10):
    """エージェント数が多い上位N個のリンクを特定する"""
    count_cols = [col for col in pivot_df.columns if col.endswith('_count')]
    top_cols = pivot_df[count_cols].sum().sort_values(ascending=False).head(n).index
    return [col.replace('_count', '') for col in top_cols]

def plot_metric(pivot_df, top_links, metric_suffix, title, ylabel, save_path, kind='line'):
    """各指標（人数、速度、密度）をプロットする共通関数"""
    target_cols = [f"{link}_{metric_suffix}" for link in top_links if f"{link}_{metric_suffix}" in pivot_df.columns]
    if not target_cols:
        print(f"指標 {metric_suffix} のデータが見つかりません。")
        return

    # カラム名から先頭のアンダースコアを削除（凡例表示のため）
    data_to_plot = pivot_df[target_cols].copy()
    data_to_plot.columns = [col.lstrip('_').replace(f'_{metric_suffix}', '') for col in data_to_plot.columns]

    plt.figure(figsize=(16, 9))
    
    if kind == 'bar':
        ax = data_to_plot.plot(kind='bar', stacked=True, figsize=(16, 9), width=1.0)
    else:
        ax = data_to_plot.plot(kind='line', figsize=(16, 9))
    
    # --- X軸の刻みを1時間（3600秒）単位に設定 ---
    all_times = pivot_df.index.values
    # 指定した間隔（3600秒）ごとのインデックスを取得
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
        # データの読み込み
        pivot_df, _ = load_data()
        
        # 上位10個のリンクを取得
        top_10 = get_top_links(pivot_df, n=10)
        
        # 1. リンクごとの人口密度のプロット
        plot_metric(pivot_df, top_10, "density", 
                    "Population Density per Link (1-hour intervals)", 
                    "Density [Agents/m²]", 
                    os.path.join(IMAGE_DIR, "population_density_top10{timestamp_str}.png"), 
                    kind='line')
        
        # 2. リンクごとのエージェント数のプロット（積み上げ棒グラフ）
        plot_metric(pivot_df, top_10, "count", 
                    "Agent Count per Link (1-hour intervals)", 
                    "Number of Agents", 
                    os.path.join(IMAGE_DIR, "agent_count_top10{timestamp_str}.png"), 
                    kind='bar')
        
        # 3. リンクごとの合計速度のプロット
        plot_metric(pivot_df, top_10, "velocity", 
                    "Total Velocity per Link (1-hour intervals)", 
                    "Velocity Sum [m/s]", 
                    os.path.join(IMAGE_DIR, "total_velocity_top10{timestamp_str}.png"), 
                    kind='line')
        
        print("\n全てのグラフの生成が完了しました。")

    except Exception as e:
        print(f"エラーが発生しました: {e}")