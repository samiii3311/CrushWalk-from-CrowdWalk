import json
import random
import os
from datetime import datetime, timedelta

# --- 1. 設定データ ---
GOAL_STATIONS = ["JR-Kashii", "NishiTetsu-Kashii", "Kashii-Miyamae", "JR-Chihaya", "Kashii-Enn"]
START_PLACES = ["Beach", "East", "Path", "Ocean", "Park"]
GOAL_WEIGHTS = [0.40, 0.10, 0.05, 0.40, 0.05]
PLACE_RATIOS = {"Beach": 0.05, "East": 0.40, "Path": 0.15, "Ocean": 0.05, "Park": 0.35}

TOTAL_POPULATION = 131000
NAIVE_RATIO = 0.02  # 2% を「単純な動き」のエージェントにする

# --- 2. Helpers ---
def get_random_time_in_window(start_time_str, window_minutes):
    base_time = datetime.strptime(start_time_str, "%H:%M:%S")
    random_seconds = random.randint(0, window_minutes * 60)
    new_time = base_time + timedelta(seconds=random_seconds)
    return new_time.strftime("%H:%M:%S")

def create_scenarios(total_people, start_place, role="smart"):
    """
    role="smart": 混雑を避ける (weight 0.1)
    role="naive": 混雑を無視して最短距離 (weight 0.0)
    """
    counts = [0] * len(GOAL_STATIONS)
    for _ in range(total_people):
        chosen_station = random.choices(GOAL_STATIONS, weights=GOAL_WEIGHTS, k=1)[0]
        idx = GOAL_STATIONS.index(chosen_station)
        counts[idx] += 1
    
    # 役割に応じた設定
    if role == "smart":
        config = {"weight": 0.1, "margin": 1000.0, "trail": 0.0}
    else:
        # 古い NaiveAgent の代わり。最短距離で行くが、詰まった時のために margin を高くする
        config = {"weight": 0.0, "margin": 2000.0, "trail": 0.0}

    scenarios = []
    for i, goal in enumerate(GOAL_STATIONS):
        if counts[i] > 0:
            scenarios.append({
                "rule": "RANDOM",
                "agentType": {
                    "className": "RationalAgent", # クラスは常に RationalAgent を使う
                    "config": config
                },
                "startTime": get_random_time_in_window("20:30:00", 60),
                "total": counts[i],
                "duration": 300, # 60から600に延長。10分かけてゆっくり登場させる
                "startPlace": start_place,
                "goal": goal
            })
    return scenarios

# --- 3. 処理実行 ---
final_scenarios = []

RESERVED_FIXED = 1438
RESERVED_TABLES = sum([random.randint(2, 4) for _ in range(248)])
RESERVED_BLUE = sum([random.randint(2, 8) for _ in range(50)])
PAID_TOTAL = RESERVED_FIXED + RESERVED_TABLES + RESERVED_BLUE
GENERAL_TOTAL = TOTAL_POPULATION - PAID_TOTAL

# ループ 1: 有料席 (Smart と Naive を分ける)
naive_paid = int(PAID_TOTAL * NAIVE_RATIO)
smart_paid = PAID_TOTAL - naive_paid
final_scenarios.extend(create_scenarios(smart_paid, "PaidSeat", role="smart"))
final_scenarios.extend(create_scenarios(naive_paid, "PaidSeat", role="naive"))

# ループ 2: 一般エリア
for place in START_PLACES:
    base_pop = int(GENERAL_TOTAL * PLACE_RATIOS[place])
    adjusted_pop = int(base_pop * random.uniform(0.95, 1.05))
    
    naive_gen = int(adjusted_pop * NAIVE_RATIO)
    smart_gen = adjusted_pop - naive_gen
    
    final_scenarios.extend(create_scenarios(smart_gen, place, role="smart"))
    final_scenarios.extend(create_scenarios(naive_gen, place, role="naive"))

# --- 4. 保存とレポート ---
output_filename = f"gen_rational_fluid{datetime.now().strftime('%Y%m%d')}.json"
total_generated = sum(s["total"] for s in final_scenarios)

with open(output_filename, "w", encoding="utf-8") as f:
    f.write('#{ "version" : 2}\n')
    f.write("[\n") 
    for i, scenario in enumerate(final_scenarios):
        line = json.dumps(scenario, ensure_ascii=False)
        comma = "," if i < len(final_scenarios) - 1 else ""
        f.write(f"  {line}{comma}\n")
    f.write("]\n")

print("-" * 50)
print(f"✅ シナリオ生成完了: {output_filename}")
print(f"📊 設定:")
print(f"   Duration: 300s (詰まり防止のため延長)")
print(f"   Smart Agent Weight: 0.1 / Naive Role Weight: 0.0")
print(f"   最終生成人数: {total_generated:,}人")
print("-" * 50)