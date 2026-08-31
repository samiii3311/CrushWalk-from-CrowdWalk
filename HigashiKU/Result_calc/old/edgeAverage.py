import pandas as pd
import plotly.express as px

# === CONFIG ===
input_file = r"C:\Users\School\Documents\GitHub\CrowdWalk\crowdwalk\HigashiKU\log\individual\log_individual_pedestrians.csv"  # Replace with your file path
output_file = r"C:\Users\School\Documents\GitHub\CrowdWalk\crowdwalk\HigashiKU\logoutput\aggregated_pedestrians.csv"
output_file2 = r"C:\Users\School\Documents\GitHub\CrowdWalk\crowdwalk\HigashiKU\logoutput\totV.csv"

# === STEP 1: Load CSV ===
df = pd.read_csv(input_file, skipinitialspace=True)

# === STEP 2: Round time to nearest second ===
df['time_sec'] = df['current_traveling_period'].round().astype(int)

# === STEP 3: Aggregate per second per agent ===
grouped = df.groupby(['pedestrianID', 'time_sec']).agg({
    
    'current_linkID': 'first',
    'current_position_in_model_x': 'mean',
    'current_position_in_model_y': 'mean',
    'current_velocity': 'mean',
    'current_acceleration': 'mean'
}).reset_index()

grouped.to_csv(output_file, index=False)
print(f"Aggregated data saved to {output_file}")

maxTime = df['time_sec'].max()
print(f"Max time in data: {maxTime} seconds/n")

totalV = df.groupby(['current_linkID', 'time_sec'])['current_velocity'].sum().reset_index(name='total_velocity')
print(totalV)
totalV.to_csv(output_file2, index=False)
print(f"Aggregated data saved to {output_file2}")


velocity_pivot = totalV.pivot(index='time_sec', columns='current_linkID', values='total_velocity')

# === STEP 7: Save the pivoted data to CSV ===
velocity_pivot.to_csv("velocity_pivot.csv")
print("Pivoted velocity data saved to velocity_pivot.csv")



# === Count of agents per link per second ===
agent_count = df.groupby(['current_linkID', 'time_sec'])['pedestrianID'].count().reset_index(name='agent_count')

# === Pivot agent count ===
agent_count_pivot = agent_count.pivot(index='time_sec', columns='current_linkID', values='agent_count')

# === Rename columns to distinguish from velocity ===
agent_count_pivot.columns = [f"count_link_{col}" for col in agent_count_pivot.columns]
velocity_pivot.columns = [f"velocity_link_{col}" for col in velocity_pivot.columns]

# === Combine both pivot tables ===
combined = pd.concat([velocity_pivot, agent_count_pivot], axis=1)

# === Save to CSV ===
combined.to_csv("velocity_pivot.csv")
print("Combined velocity and agent count data saved to velocity_pivot.csv")

#for t in range(maxTime + 1):
 #   for pid in df['current_linkID'].unique() & df['time_sec']==t:
  #      totalV = df[(df['current_linkID'])]
        

# Save aggregated data


# === STEP 4: Visualizations ===

# Velocity trend per agent
fig_velocity = px.line(grouped, x='time_sec', y='current_velocity', color='pedestrianID',
                       labels={'time_sec': 'Time (s)', 'current_velocity': 'Average Velocity'},
                       title='Average Velocity Over Time per Agent')
#fig_velocity.show()

# Position density heatmap
fig_heatmap = px.density_heatmap(df, x='current_position_in_model_x', y='current_position_in_model_y',
                                 nbinsx=50, nbinsy=50,
                                 labels={'current_position_in_model_x': 'X Position',
                                         'current_position_in_model_y': 'Y Position'},
                                 title='Agent Position Density Heatmap')
#fig_heatmap.show()

# Speed distribution histogram
fig_hist = px.histogram(df, x='current_velocity', nbins=50,
                        labels={'current_velocity': 'Velocity'},
                        title='Speed Distribution Histogram')
#fig_hist.show()

# === STEP 5: Summary statistics ===
#speed_stats = {
    # 'median_speed': df['current_velocity'].median(),
    #'max_speed': df['current_velocity'].max(),
    #'min_speed': df['current_velocity'].min()
#}

#print("\nSpeed Summary:")
#for key, value in speed_stats.items():
 #   print(f"{key}: {value:.3f}")