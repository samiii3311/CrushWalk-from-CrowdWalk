import pandas as pd
import numpy as np 
import plotly.express as px

# 1. Add Matplotlib Import
import matplotlib.pyplot as plt 
# 2. Add Matplotlib Backend Fix (Recommended for saving files)
import matplotlib
matplotlib.use('Agg')

from matplotlib.ticker import MultipleLocator
import matplotlib.font_manager as fm

LINUX_CJK_FONT = 'Noto Sans CJK JP' 

# Set the global font preferences
plt.rcParams['font.family'] = 'sans-serif'
# Use the CJK font first, then fall back to standard Linux sans-serif fonts
plt.rcParams['font.sans-serif'] = [LINUX_CJK_FONT, 'DejaVu Sans', 'TakaoGothic']


# === CONFIG ===
input_file = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/log/individual/log_individual_pedestrians.csv" 
output_file = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/logoutput/aggregated_pedestrians.csv"
output_file2 = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/logoutput/totV.csv"
CHUNK_SIZE = 10_000_000  # Process 1 million rows at a time (adjust based on your RAM)

# Initialize lists to store results from each chunk
grouped_results = []
totalV_results = []
all_data_for_viz = [] 


print(f"Starting analysis with chunk size: {CHUNK_SIZE}")

# Define the expected data types BEFORE reading the file
dtype_mapping = {
    'current_traveling_period': 'float64',  
    'pedestrianID': 'object',           
    'current_linkID': 'object', 
    'current_velocity': 'float32',       
    'current_acceleration': 'float32',   
    'current_position_in_model_x': 'float32', 
    'current_position_in_model_y': 'float32'
}

# === STEP 1-3: Load and Aggregate in Chunks ===
for i, chunk in enumerate(pd.read_csv(
    input_file,            
    skipinitialspace=True, 
    chunksize=CHUNK_SIZE, 
    dtype=dtype_mapping
)):
    print(f"Processing chunk {i+1}...")
    
    
    try:
        # --- Step 2: Round time to nearest second ---
        # Perform all necessary transformations within the chunk
        chunk['time_sec'] = chunk['current_traveling_period'].round().astype('int32') # Use 'int32' for robustness

        # --- Step 3: Aggregate per second per agent (grouped) ---
        chunk_grouped = chunk.groupby(['pedestrianID', 'time_sec']).agg({
            'current_linkID': 'first',
            'current_position_in_model_x': 'mean',
            'current_position_in_model_y': 'mean',
            'current_velocity': 'mean',
            'current_acceleration': 'mean'
        }).reset_index()
        grouped_results.append(chunk_grouped)

        # --- Total Velocity (totalV) ---
        chunk_totalV = chunk.groupby(['current_linkID', 'time_sec'])['current_velocity'].sum().reset_index(name='total_velocity')
        totalV_results.append(chunk_totalV)
        
        # --- Sample data for visualization (optional) ---
        all_data_for_viz.append(chunk.sample(n=min(10000, len(chunk)), random_state=42))

  
    except Exception as e:
        print(f"WARNING: Skipping chunk {i+1} due to error: {e}")
        continue

# === Combine Chunk Results ===


grouped_results_clean = [df for df in grouped_results if not df.empty]
totalV_results_clean = [df for df in totalV_results if not df.empty]

# Ensure at least some data exists before proceeding
if not grouped_results_clean:
    print("\nError: No valid data found in any processed chunk. Stopping.")
    import sys
    sys.exit()

grouped_df = pd.concat(grouped_results_clean, ignore_index=True) 
totalV_df = pd.concat(totalV_results_clean, ignore_index=True)   
df_viz = pd.concat(all_data_for_viz, ignore_index=True)


# --- Final Aggregation for 'totalV' (since links/times might be split across chunks) ---
# Group the combined totalV results again to get the final sum
totalV_df['time_sec'] = totalV_df['time_sec'].astype('int32')
final_totalV = totalV_df.groupby(['current_linkID', 'time_sec'])['total_velocity'].sum().reset_index()


# === STEP 4: Save Intermediate Aggregations ===

grouped_df.to_csv(output_file, index=False)
print(f"\nAggregated per-agent data saved to {output_file}")

final_totalV.to_csv(output_file2, index=False)
print(f"Total velocity data saved to {output_file2}")

maxTime = grouped_df['time_sec'].max()
print(f"Max time in data: {maxTime} seconds")


# --- Pivot Tables and Combined Output ---
velocity_pivot = final_totalV.pivot(index='time_sec', columns='current_linkID', values='total_velocity')

# Recalculate agent count from the initial grouped_df for consistency
grouped_df['time_sec'] = grouped_df['time_sec'].astype('int32')

# Using the final_totalV structure, count agents in the grouped_df
agent_count = grouped_df.groupby(['current_linkID', 'time_sec'])['pedestrianID'].count().reset_index(name='agent_count')

# Pivot agent count
agent_count_pivot = agent_count.pivot(index='time_sec', columns='current_linkID', values='agent_count')

# Rename columns and combine
agent_count_pivot.columns = [f"count_link_{col}" for col in agent_count_pivot.columns]
velocity_pivot.columns = [f"velocity_link_{col}" for col in velocity_pivot.columns]
combined = pd.concat([velocity_pivot, agent_count_pivot], axis=1)

# === STEP 7: Save the pivoted and combined data to CSV ===
combined.to_csv("/home/kulla/CrowdWalk/crowdwalk/HigashiKU/logoutput/velocity_pivot.csv")
print("Combined velocity and agent count data saved to velocity_pivot.csv")



print("\nIdentifying top 10 links for plotting...")

# Determine the top 10 links based on total agent count
# Sum agent counts across all time_sec for each link
total_agent_counts = agent_count_pivot.sum().sort_values(ascending=False)
top_10_links_count = [col.replace('count_link_', '') for col in total_agent_counts.head(10).index]

print(f"Top 10 links by agent count: {top_10_links_count}")

# --- Prepare data for plotting only the top 10 links ---
# Filter velocity_pivot for top 10 links
velocity_pivot_top10 = velocity_pivot[[f"velocity_link_{link_id}" for link_id in top_10_links_count]]

# Filter agent_count_pivot for top 10 links
agent_count_pivot_top10 = agent_count_pivot[[f"count_link_{link_id}" for link_id in top_10_links_count]]

# ... (Code up to filtering agent_count_pivot_top10 and velocity_pivot_top10)

# === Configuration for X-Axis Readability ===
TICK_INTERVAL = 600 

# === Generate Image 1: Agent Count per Link per Second (Top 10 Links) ===
plt.figure(figsize=(16, 9))

# PLOT THE FIGURE
ax = agent_count_pivot_top10.plot(
    kind='bar', 
    stacked=True, 
    figsize=(16, 9), 
    width=1.0 
)

# --- X-AXIS FIX: Set major tick marks every 600 seconds (10 minutes) ---

# 1. Identify all time values (index) that are multiples of the interval
tick_time_values = [t for t in agent_count_pivot_top10.index if t % TICK_INTERVAL == 0]

# 2. Find the *positional indices* corresponding to those time values
# We use .get_indexer to safely map time values to their 0-based positions
tick_positions = ax.get_xticks()[ax.get_xticks() < len(agent_count_pivot_top10.index)] 

# Filter the positions to only those where the time value is a multiple of TICK_INTERVAL
# Get the time values at all positions
all_times = agent_count_pivot_top10.index.values

# Select positions where the time value is a multiple of TICK_INTERVAL
# The .where is the safest way to prevent out-of-bounds access
safe_tick_positions = np.where(all_times % TICK_INTERVAL == 0)[0]

# Set the ticks and labels
ax.set_xticks(safe_tick_positions)
ax.set_xticklabels([f'{t:.0f}' for t in all_times[safe_tick_positions]], rotation=90)


plt.title('各道路の毎秒ごとの人口密度 (Top 10 Links)')
plt.xlabel('時間[秒]') # Error line now fixed!
plt.ylabel('エージェント数')
plt.legend(title='Link ID', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig("/home/kulla/CrowdWalk/crowdwalk/HigashiKU/logoutput/agent_count_top10_stacked_bar.png")
plt.close()
print("Generated 'agent_count_top10_stacked_bar.png'")

# === Generate Image 2: Total Velocity per Link per Second (Top 10 Links) ===
plt.figure(figsize=(16, 9))

# PLOT THE FIGURE
ax2 = velocity_pivot_top10.plot(
    kind='line', 
    figsize=(16, 9), 
    marker='o', 
    markersize=4
) 

# --- X-AXIS FIX for Line Plot ---

# Use the same logic for setting ticks to keep charts consistent
all_times_v = velocity_pivot_top10.index.values
safe_tick_positions_v = np.where(all_times_v % TICK_INTERVAL == 0)[0]

ax2.set_xticks(safe_tick_positions_v)
ax2.set_xticklabels([f'{t:.0f}' for t in all_times_v[safe_tick_positions_v]], rotation=90)

plt.title('各道路の毎秒ごとの合計速度 (Top 10 Links)')
plt.xlabel('時間[秒]')
plt.ylabel('速度 [m/s]')
plt.legend(title='Link ID', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(True, linestyle='--', alpha=0.7) 
plt.tight_layout()
plt.savefig("/home/kulla/CrowdWalk/crowdwalk/HigashiKU/logoutput/total_velocity_top10_line.png")
plt.close() 
print("Generated 'total_velocity_top10_line.png'")
# ... (rest of your visualization code)


# === STEP 8: Visualizations (Using the sampled data 'df_viz') ===

print("\nGenerating visualizations...")

# Velocity trend per agent (using the final grouped_df)
# NOTE: This chart may still be slow if 'grouped_df' is massive.
if len(grouped_df) < 10_000_000: # Heuristic check
    fig_velocity = px.line(grouped_df.sample(n=min(10000, len(grouped_df)), random_state=42), 
                           x='time_sec', y='current_velocity', color='pedestrianID',
                           labels={'time_sec': 'Time (s)', 'current_velocity': 'Average Velocity'},
                           title='Average Velocity Over Time per Agent (Sampled)')
    # fig_velocity.show()

# Position density heatmap (using sampled raw data)
fig_heatmap = px.density_heatmap(df_viz, x='current_position_in_model_x', y='current_position_in_model_y',
                                 nbinsx=50, nbinsy=50,
                                 labels={'current_position_in_model_x': 'X Position',
                                         'current_position_in_model_y': 'Y Position'},
                                 title='Agent Position Density Heatmap (Sampled)')
# fig_heatmap.show()

# Speed distribution histogram (using sampled raw data)
fig_hist = px.histogram(df_viz, x='current_velocity', nbins=50,
                        labels={'current_velocity': 'Velocity'},
                        title='Speed Distribution Histogram (Sampled)')
# fig_hist.show()

print("Visualizations ready to be displayed (uncomment .show() to view).")