import pandas as pd
import numpy as np 
import sys
# Import configuration settings
from config import INPUT_FILE, OUTPUT_FILE_AGGREGATED, OUTPUT_FILE_TOTAL_V, OUTPUT_FILE_PIVOT, CHUNK_SIZE, DTYPE_MAPPING
# Import the XML parsing logic
from xml_retriver import get_link_geometry
from datetime import datetime

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def process_data_in_chunks():
    """
    Loads large CSV data in chunks, performs aggregation, and saves intermediate results.

    Returns:
        tuple: (grouped_df, final_totalV, df_viz) or None if processing fails.
    """
    
    grouped_results = []
    totalV_results = []
    all_data_for_viz = [] 

    print(f"Starting analysis with chunk size: {CHUNK_SIZE} on file: {INPUT_FILE}")

    # === STEP 1-3: Load and Aggregate in Chunks ===
    for i, chunk in enumerate(pd.read_csv(
        INPUT_FILE,             
        skipinitialspace=True, 
        chunksize=CHUNK_SIZE, 
        dtype=DTYPE_MAPPING
    )):
        print(f"Processing chunk {i+1}...")
        
        try:
            # --- Step 2: Round time to nearest second ---
            chunk['time_sec'] = chunk['current_traveling_period'].round().astype('int32') 

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
            
            # --- Sample data for visualization ---
            all_data_for_viz.append(chunk.sample(n=min(10000, len(chunk)), random_state=42))

        except Exception as e:
            print(f"WARNING: Skipping chunk {i+1} due to error: {e}")
            continue

    # === Combine Chunk Results ===
    grouped_results_clean = [df for df in grouped_results if not df.empty]
    totalV_results_clean = [df for df in totalV_results if not df.empty]

    if not grouped_results_clean:
        print("\nError: No valid data found in any processed chunk. Stopping.")
        return None, None, None

    grouped_df = pd.concat(grouped_results_clean, ignore_index=True)
    totalV_df = pd.concat(totalV_results_clean, ignore_index=True)
    df_viz = pd.concat(all_data_for_viz, ignore_index=True)

    # --- Final Aggregation for 'totalV' ---
    totalV_df['time_sec'] = totalV_df['time_sec'].astype('int32')
    final_totalV = totalV_df.groupby(['current_linkID', 'time_sec'])['total_velocity'].sum().reset_index()

    # === STEP 4: Save Intermediate Aggregations ===
    grouped_df.to_csv(OUTPUT_FILE_AGGREGATED, index=False)
    print(f"\nAggregated per-agent data saved to {OUTPUT_FILE_AGGREGATED}")

    final_totalV.to_csv(OUTPUT_FILE_TOTAL_V, index=False)
    print(f"Total velocity data saved to {OUTPUT_FILE_TOTAL_V}")

    return grouped_df, final_totalV, df_viz

def create_pivot_and_save(grouped_df, final_totalV):
    """
    Creates and saves the combined velocity, agent count, and density pivot tables.
    """
    # 1. Get Link Geometry Data (Area)
    df_geometry = get_link_geometry()
    density_pivot = pd.DataFrame()

    # --- Pivot Tables ---
    velocity_pivot = final_totalV.pivot(index='time_sec', columns='current_linkID', values='total_velocity')

    # Recalculate agent count from the initial grouped_df for consistency
    grouped_df['time_sec'] = grouped_df['time_sec'].astype('int32')
    agent_count = grouped_df.groupby(['current_linkID', 'time_sec'])['pedestrianID'].count().reset_index(name='agent_count')

    if not df_geometry.empty:
        # Merge agent count (Population) with link area (Geometry)
        density_df = agent_count.merge(df_geometry, on='current_linkID', how='left')
        
        # Calculate density (Agent Count / Area)
        # np.where handles division by zero or NaN area gracefully
        density_df['population_density'] = np.where(
            density_df['area'].gt(0), 
            density_df['agent_count'] / density_df['area'], 
            0.0
        )
        
        # Pivot density
        density_pivot = density_df.pivot(index='time_sec', columns='current_linkID', values='population_density')
        density_pivot.columns = [f"density_link_{col}" for col in density_pivot.columns]
    else:
        print("WARNING: Link geometry data is missing. Density calculation skipped.")
    
    # Pivot agent count
    agent_count_pivot = agent_count.pivot(index='time_sec', columns='current_linkID', values='agent_count')

    # Rename columns and combine
    agent_count_pivot.columns = [f"count_link_{col}" for col in agent_count_pivot.columns]
    velocity_pivot.columns = [f"velocity_link_{col}" for col in velocity_pivot.columns]
    
    # Combine all pivots (Density pivot will be empty if geometry failed, resulting in NaN columns)
    combined = pd.concat([velocity_pivot, agent_count_pivot, density_pivot], axis=1)

    # === Save the pivoted and combined data to CSV ===
    combined.to_csv(OUTPUT_FILE_PIVOT)
    print(f"Combined velocity, agent count, AND density data saved to {OUTPUT_FILE_PIVOT}")
    
    return combined

def load_preprocessed_data():
    """
    Loads pre-processed combined pivot data and aggregated data for visualization.
    """
    print("Loading pre-processed data...")
    
    # Load combined data
    combined = pd.read_csv(OUTPUT_FILE_PIVOT)
    
    # Separate back into velocity, agent count, and density pivots
    velocity_cols = [col for col in combined.columns if col.startswith('velocity_link_')]
    agent_count_cols = [col for col in combined.columns if col.startswith('count_link_')]
    density_cols = [col for col in combined.columns if col.startswith('density_link_')]
    
    velocity_pivot = combined[['time_sec'] + velocity_cols].set_index('time_sec')
    agent_count_pivot = combined[['time_sec'] + agent_count_cols].set_index('time_sec')
    density_pivot = combined[['time_sec'] + density_cols].set_index('time_sec')
    
    # Load grouped_df for visualizations
    grouped_df = pd.read_csv(OUTPUT_FILE_AGGREGATED)
    # Sample data for quick visualization
    df_viz = grouped_df.sample(n=min(100000, len(grouped_df)), random_state=42)
    
    return velocity_pivot, agent_count_pivot, density_pivot, grouped_df, df_viz

if __name__ == "__main__":
    form = input("Did you run this file already? (y/n): ")
    
    if form.lower() == 'n':
        # Run full processing pipeline
        grouped_df, final_totalV, df_viz = process_data_in_chunks()
        if grouped_df is not None:
            combined = create_pivot_and_save(grouped_df, final_totalV)
            print(f"Max time in data: {grouped_df['time_sec'].max()} seconds")
            
    elif form.lower() == 'y':
        print("Data is processed. Please run 'graph.py' to load and visualize the data.")
        
    else:
        print("Invalid input. Please enter 'y' or 'n'.")