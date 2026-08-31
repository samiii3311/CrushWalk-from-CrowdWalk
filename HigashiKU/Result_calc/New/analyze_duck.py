import duckdb
import os
from datetime import datetime 

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


# --- Configuration ---
BASE_PATH = "/home/kulla/CrowdWalk/crowdwalk"
LAKE_PATH = os.path.join(BASE_PATH, "parqData/parqData_2026-01-07_14-40-27/**/*.parquet")
GEOMETRY_FILE = os.path.join(BASE_PATH, "HigashiKU/Result_calc/New/logoutput/link_geometry.csv")
OUTPUT_DIR = os.path.join(BASE_PATH, "HigashiKU/Result_calc/New/logoutput")
OUTPUT_AGGREGATED = os.path.join(OUTPUT_DIR, f"aggregated_data_{timestamp}.parquet")
OUTPUT_PIVOT = os.path.join(OUTPUT_DIR, f"combined_pivot_{timestamp}.parquet")
# 密度データのみのファイル（オプション）
OUTPUT_DENSITY = os.path.join(OUTPUT_DIR, f"link_density_long{timestamp}.parquet")

def run_pipeline():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    con = duckdb.connect()

    # 大型データ用の設定
    con.execute("PRAGMA max_temp_directory_size='500GiB'")
    con.execute("PRAGMA temp_directory='/home/kulla/CrowdWalk/crowdwalk/HigashiKU/Result_calc/New/logoutput/temp'")
    con.execute("SET preserve_insertion_order=false")
    con.execute("SET memory_limit='24GB'")

    print("Registering data...")
    con.execute(f"CREATE VIEW raw_data AS SELECT * FROM read_parquet('{LAKE_PATH}', union_by_name=True)")
    
    if os.path.exists(GEOMETRY_FILE):
        con.execute(f"CREATE TABLE geometry AS SELECT * FROM read_csv_auto('{GEOMETRY_FILE}')")
        has_geo = True
    else:
        print("WARNING: Geometry file missing!")
        has_geo = False

    # 1. 密度計算を含むピボットテーブルの作成
    print("Step: Generating Pivot with Density...")
    if has_geo:
        pivot_query = """
            PIVOT (
                SELECT 
                    r.current_linkID,
                    r.current_traveling_period AS time_sec,
                    SUM(r.current_velocity) as total_v,
                    COUNT(DISTINCT r.pedestrianID) as agent_count,
                    -- 人口密度 = 合計人数 / リンク面積
                    (COUNT(DISTINCT r.pedestrianID) / FIRST(g.area)) as density
                FROM raw_data r
                LEFT JOIN geometry g ON r.current_linkID = g.current_linkID
                GROUP BY r.current_linkID, time_sec
            ) 
            ON current_linkID 
            USING SUM(total_v) AS velocity, SUM(agent_count) AS count, SUM(density) AS density
            GROUP BY time_sec
            ORDER BY time_sec
        """
    else:
        # 面積がない場合は人数のみ
        pivot_query = "PIVOT (SELECT current_linkID, current_traveling_period AS time_sec, COUNT(DISTINCT pedestrianID) as count FROM raw_data GROUP BY ALL) ON current_linkID USING SUM(count) AS count GROUP BY time_sec ORDER BY time_sec"

    con.execute(f"COPY ({pivot_query}) TO '{OUTPUT_PIVOT}' (FORMAT PARQUET, COMPRESSION 'ZSTD')")

    # (追加) 2. リンクごとの密度データを「縦持ち」形式で保存（後で特定のリンクを調べやすい）
    if has_geo:
        print("Step: Generating long-format density data...")
        con.execute(f"""
            COPY (
                SELECT 
                    r.current_traveling_period AS time_sec,
                    r.current_linkID,
                    COUNT(DISTINCT r.pedestrianID) / FIRST(g.area) AS density
                FROM raw_data r
                JOIN geometry g ON r.current_linkID = g.current_linkID
                GROUP BY ALL
            ) TO '{OUTPUT_DENSITY}' (FORMAT PARQUET, COMPRESSION 'ZSTD')
        """)

    print(f"Success! Data saved to {OUTPUT_DIR}")

if __name__ == "__main__":
    run_pipeline()