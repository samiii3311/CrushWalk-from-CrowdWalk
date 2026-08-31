import json
import random
 
# --- 1. 設定データ ---
GOAL_STATIONS = ["JR-Kashii", "NishiTetsu-Kashii", "Kashii-Miyamae", "JR-Chihaya", "Kashii-Enn"]
START_PLACES = ["Beach", "East", "Path", "Ocean", "Park"]
GOAL_WEIGHTS = [0.40, 0.10, 0.05, 0.40, 0.05]
# B. 一般客の振り分け
PLACE_RATIOS = {"Beach": 0.05, "East": 0.40, "Path": 0.15, "Ocean": 0.05, "Park": 0.35}
 
# --- 2. 有料席・特殊席の計算 ---
 
# ① 有料席（固定）
RESERVED_FIXED = 1438
 
# ② テーブル席: 51個のテーブルに、それぞれ2〜4名をランダムに配置
table_groups = [random.randint(2, 4) for _ in range(248)]
RESERVED_TABLES = sum(table_groups)
 
# ③ ブルーシート席: 50個のシートに、それぞれ2〜8名をランダムに配置
blue_sheet_groups = [random.randint(2, 8) for _ in range(50)]
RESERVED_BLUE = sum(blue_sheet_groups)
 
# 特殊席の合計
SPECIAL_TOTAL = RESERVED_FIXED + RESERVED_TABLES + RESERVED_BLUE
 
# ④ 一般客の合計
TOTAL_POPULATION = 90000
GENERAL_POP = TOTAL_POPULATION - SPECIAL_TOTAL
 
# --- 3. 処理開始 ---
final_scenarios = []
 
def distribute_to_stations(total_people, start_place, scenario_label):
    """人数を駅の重みに基づいて振り分けるヘルパー関数"""
    counts = [0] * len(GOAL_STATIONS)
    for _ in range(total_people):
        chosen_station = random.choices(GOAL_STATIONS, weights=GOAL_WEIGHTS, k=1)[0]
        idx = GOAL_STATIONS.index(chosen_station)
        counts[idx] += 1
    scenarios = []
    for i, goal in enumerate(GOAL_STATIONS):
        if counts[i] > 0:
            scenarios.append({
                
                "rule": "RANDOM",
                "agentType": {"className": "BustleAgent"},
                "speedModel": "CROSSING",
                "startPlace": start_place,
                "goal": goal,
                "duration":60,
                "total": counts[i],
                "startTime": "20:30:00"   
                
            })
    return scenarios
 
# A. 特殊席の振り分け
final_scenarios.extend(distribute_to_stations(RESERVED_FIXED, "PaidSeat", "FIXED"))
final_scenarios.extend(distribute_to_stations(RESERVED_TABLES, "PaidSeat", "TABLE"))
final_scenarios.extend(distribute_to_stations(RESERVED_BLUE, "PaidSeat", "BLUE"))
 

 
for place in START_PLACES:
    base_pop = int(GENERAL_POP * PLACE_RATIOS[place])
    # ±5%の変動
    adjusted_pop = int(base_pop * random.uniform(0.95, 1.05))
    final_scenarios.extend(distribute_to_stations(adjusted_pop, place, f"GEN_{place}"))
 
# --- 4. 保存とレポート ---
total_generated = sum(s["total"] for s in final_scenarios)
output_filename = "kashiihama_90000_detailed_reserved.json"
 
with open(output_filename, "w", encoding="utf-8") as f:
    f.write("[\n") # Start the JSON list
    for i, scenario in enumerate(final_scenarios):
        # Convert each scenario object to a single-line string
        line = json.dumps(scenario, ensure_ascii=False)
        # Add a comma if it's not the last item
        comma = "," if i < len(final_scenarios) - 1 else ""
        f.write(f"    {line}{comma}\n")
    f.write("]\n") # Close the JSON list
 
print("-" * 50)
print(f"✅ シナリオ生成完了: {output_filename}")
print(f"📊 内訳:")
print(f"   固定有料席: {RESERVED_FIXED}人")
print(f"   テーブル席: {RESERVED_TABLES}人 (248組)")
print(f"   ブルーシート: {RESERVED_BLUE}人 (50組)")
print(f"   一般客合計: {total_generated - SPECIAL_TOTAL:,}人")
print(f"   ---")
print(f"   最終生成人数: {total_generated:,}人")
print("-" * 50)