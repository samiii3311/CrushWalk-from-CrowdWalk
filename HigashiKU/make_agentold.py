import json
import random
 
# 1. 設定データ
GOAL_STATIONS = ["JR-Kashii", "NishiTetsu-Kashii", "Kashii-Miyamae", "JR-Chihaya","Kashii-Enn"]
START_PLACES = ["Beach", "East", "Path", "Ocean", "Park", "Bridge"]
TOTAL_POPULATION = 90000 - 1438
 
# 2. 比率の設定（ベースとなる重み）
PLACE_RATIOS = {
    "Beach": 0.25, "East": 0.15, "Path": 0.16,
    "Ocean": 0.12, "Park": 0.20, "Bridge": 0.12
}
 
# 駅の重み（40%, 12.5%, 7.5%, 40%）
GOAL_WEIGHTS = [0.40, 0.10, 0.05, 0.40,0.05]
 
# 3. 処理開始
final_scenarios = []
total_count_check = 0
 
# 各出発地点ごとに計算
for place in START_PLACES:
    # その場所に割り当てられるベースの人数
    base_pop_for_place = int(TOTAL_POPULATION * PLACE_RATIOS[place])
   
    # 【ランダム要素1】場所ごとの人数を ±5% の範囲でわずかに変動させる
    variation = random.uniform(0.95, 1.05)
    adjusted_pop = int(base_pop_for_place * variation)
   
    # この地点の人数を各駅にランダムに振り分ける
    # 1人ずつ駅を選ぶと計算が重いため、多項分布（multinomial）的なランダム振り分けを行う
    counts_per_station = [0] * len(GOAL_STATIONS)
    for _ in range(adjusted_pop):
        # 【ランダム要素2】重みに基づいて駅をランダムに1つ選択
        chosen_station = random.choices(GOAL_STATIONS, weights=GOAL_WEIGHTS, k=1)[0]
        idx = GOAL_STATIONS.index(chosen_station)
        counts_per_station[idx] += 1
 
    # 各駅への振り分け結果をシナリオに追加
    for i, goal in enumerate(GOAL_STATIONS):
        num = counts_per_station[i]
        if num > 0:
            item = {
                "scenarioId": f"SCENE_{place}_TO_{goal}_RANDOM","parameters": {"rule": "EACH","startPlace": place,"goal": f"{goal}","total": num,"startTime": "20:30"}
            }
            final_scenarios.append(item)
            total_count_check += num

    item = {
                "scenarioId": f"SCENE_{place}_TO_{goal}_RANDOM","parameters": {"rule": "EACH","startPlace": place,"goal": "JR-Chihaya","total": 1438,"startTime": "20:30"}
            }
    final_scenarios.append(item)
    total_count_check += num    
 
# 4. JSONファイルとして保存
output_filename = "kashiihama_90000_random.json"
with open(output_filename, "w", encoding="utf-8") as f:
    json.dump(final_scenarios, f, indent=4, ensure_ascii=False)
 
print("-" * 50)
print(f"✅ ランダム設定で完了しました！")
print(f"📁 保存ファイル: {output_filename}")
print(f"🔢 最終生成人数: {total_count_check:,}人")
print("-" * 50)
 
# 確認用：駅ごとの合計人数がどうなったか表示
print("\n[駅ごとのランダム集計結果]")
for goal in GOAL_STATIONS:
    count = sum(s["parameters"]["total"] for s in final_scenarios if s["parameters"]["goal"] == f"EXIT_{goal}")
    print(f"{goal}: {count:,}人 ({count/total_count_check*100:.1f}%)")