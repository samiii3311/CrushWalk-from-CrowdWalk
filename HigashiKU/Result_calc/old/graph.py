import pandas as pd
import numpy as np 
import plotly.express as px
import matplotlib.pyplot as plt 
import matplotlib
import sys
# Set the backend for Matplotlib to prevent display issues when saving
matplotlib.use('Agg')

# Import configuration and data loading functions
from config import TICK_INTERVAL, PLOT_AGENT_COUNT, PLOT_TOTAL_VELOCITY, PLOT_POPULATION_DENSITY
from data_process import load_preprocessed_data


def get_top_links(agent_count_pivot, n=10):
    """
    Identifies the top N links based on the total agent count.
    """
    print("\nIdentifying top links for plotting...")
    # Sum agent counts across all time_sec for each link
    total_agent_counts = agent_count_pivot.sum().sort_values(ascending=False)
    # Extract the Link IDs (removing the 'count_link_' prefix)
    top_links_id = [col.replace('count_link_', '') for col in total_agent_counts.head(n).index]
    print(f"Top {n} links by agent count: {top_links_id}")
    return top_links_id

def plot_stacked_agent_count(agent_count_pivot, top_links_id):
    """
    Generates and saves the stacked bar plot for agent count.
    """
    # Filter agent_count_pivot for top links
    agent_count_pivot_topN = agent_count_pivot[[f"count_link_{link_id}" for link_id in top_links_id]]

    plt.figure(figsize=(16, 9))

    # PLOT THE FIGURE
    ax = agent_count_pivot_topN.plot(
        kind='bar', 
        stacked=True, 
        figsize=(16, 9), 
        width=1.0 
    )

    # --- X-AXIS FIX: Set major tick marks every TICK_INTERVAL seconds ---
    all_times = agent_count_pivot_topN.index.values
    safe_tick_positions = np.where(all_times % TICK_INTERVAL == 0)[0]

    # Set the ticks and labels
    ax.set_xticks(safe_tick_positions)
    ax.set_xticklabels([f'{t:.0f}' for t in all_times[safe_tick_positions]], rotation=90, fontname="Noto Sans CJK JP")

    plt.title('各道路の毎秒ごとの人口密度 (Top 10 Links)', fontname="Noto Sans CJK JP")
    plt.xlabel('時間[秒]', fontname="Noto Sans CJK JP")
    plt.ylabel('エージェント数', fontname="Noto Sans CJK JP")
    plt.legend(title='Link ID', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    plt.savefig(PLOT_AGENT_COUNT)
    plt.close()
    print(f"Generated 'agent_count_top10_stacked_bar.png' at {PLOT_AGENT_COUNT}")

def plot_total_velocity(velocity_pivot, top_links_id):
    """
    Generates and saves the line plot for total velocity.
    """
    # Filter velocity_pivot for top links
    velocity_pivot_topN = velocity_pivot[[f"velocity_link_{link_id}" for link_id in top_links_id]]

    plt.figure(figsize=(16, 9))

    # PLOT THE FIGURE
    ax2 = velocity_pivot_topN.plot(
        kind='line', 
        figsize=(16, 9), 
        marker='o', 
        markersize=4
    ) 

    # --- X-AXIS FIX for Line Plot ---
    all_times_v = velocity_pivot_topN.index.values
    safe_tick_positions_v = np.where(all_times_v % TICK_INTERVAL == 0)[0]

    ax2.set_xticks(safe_tick_positions_v)
    ax2.set_xticklabels([f'{t:.0f}' for t in all_times_v[safe_tick_positions_v]], rotation=90, fontname="Noto Sans CJK JP")

    plt.title('各道路の毎秒ごとの合計速度 (Top 10 Links)', fontname="Noto Sans CJK JP")
    plt.xlabel('時間[秒]', fontname="Noto Sans CJK JP")
    plt.ylabel('速度 [m/s]', fontname="Noto Sans CJK JP")
    plt.legend(title='Link ID', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.7) 
    plt.tight_layout()
    plt.savefig(PLOT_TOTAL_VELOCITY)
    plt.close() 
    print(f"Generated 'total_velocity_top10_line.png' at {PLOT_TOTAL_VELOCITY}")

def plot_population_density(density_pivot, top_links_id):
    """
    Generates and saves the line plot for population density (agents/m^2).
    """
    # Filter density_pivot for top links
    density_pivot_topN = density_pivot[[f"density_link_{link_id}" for link_id in top_links_id]]
    
    # Check if the density pivot contains any data (in case XML loading failed)
    if density_pivot_topN.empty or density_pivot_topN.isnull().all().all():
        print("WARNING: Density data is missing or all NaN. Skipping density plot.")
        return

    plt.figure(figsize=(16, 9))

    # PLOT THE FIGURE
    ax3 = density_pivot_topN.plot(
        kind='line', 
        figsize=(16, 9), 
        marker='o', 
        markersize=4
    ) 

    # --- X-AXIS FIX for Line Plot ---
    all_times_d = density_pivot_topN.index.values
    safe_tick_positions_d = np.where(all_times_d % TICK_INTERVAL == 0)[0]

    ax3.set_xticks(safe_tick_positions_d)
    ax3.set_xticklabels([f'{t:.0f}' for t in all_times_d[safe_tick_positions_d]], rotation=90, fontname="Noto Sans CJK JP")

    plt.title('各道路の毎秒ごとの人口密度 (Top 10 Links)', fontname="Noto Sans CJK JP")
    plt.xlabel('時間[秒]', fontname="Noto Sans CJK JP")
    plt.ylabel('人口密度 [人/m²]', fontname="Noto Sans CJK JP")
    plt.legend(title='Link ID', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, linestyle='--', alpha=0.7) 
    plt.tight_layout()
    plt.savefig(PLOT_POPULATION_DENSITY)
    plt.close() 
    print(f"Generated 'population_density_top10_line.png' at {PLOT_POPULATION_DENSITY}")


def generate_plotly_visualizations(grouped_df, df_viz):
    """
    Generates Plotly interactive visualizations.
    """
    print("\nGenerating interactive visualizations (Plotly)...")

    # Velocity trend per agent 
    if len(grouped_df) < 10_000_000: # Heuristic check
        df_sample = grouped_df.sample(n=min(10000, len(grouped_df)), random_state=42)
        fig_velocity = px.line(df_sample, 
                               x='time_sec', y='current_velocity', color='pedestrianID',
                               labels={'time_sec': 'Time (s)', 'current_velocity': 'Average Velocity'},
                               title='Average Velocity Over Time per Agent (Sampled)')
        # fig_velocity.show()
        print("Velocity trend visualization ready.")

    # Position density heatmap 
    fig_heatmap = px.density_heatmap(df_viz, x='current_position_in_model_x', y='current_position_in_model_y',
                                     nbinsx=50, nbinsy=50,
                                     labels={'current_position_in_model_x': 'X Position',
                                             'current_position_in_model_y': 'Y Position'},
                                     title='Agent Position Density Heatmap (Sampled)')
    # fig_heatmap.show()
    print("Position density heatmap ready.")

    # Speed distribution histogram
    fig_hist = px.histogram(df_viz, x='current_velocity', nbins=50,
                            labels={'current_velocity': 'Velocity'},
                            title='Speed Distribution Histogram (Sampled)')
    # fig_hist.show()
    print("Speed distribution histogram ready.")

    print("To view Plotly charts, uncomment the '.show()' calls in this file.")


if __name__ == "__main__":
    # Load the pivots and visualization dataframes
    try:
        # Load all three pivots and visualization dataframes
        velocity_pivot, agent_count_pivot, density_pivot, grouped_df, df_viz = load_preprocessed_data()
    except FileNotFoundError as e:
        print(f"\nError: Could not load data for visualization. Please ensure 'data_processor.py' has been run (entered 'n') to generate the required CSV files. Missing file: {e}")
        sys.exit()

    # 1. Identify top links
    top_10_links = get_top_links(agent_count_pivot, n=10)
    
    # 2. Generate Matplotlib plots (saved to disk)
    plot_stacked_agent_count(agent_count_pivot, top_10_links)
    plot_total_velocity(velocity_pivot, top_10_links)
    plot_population_density(density_pivot, top_10_links)
    
    # 3. Generate Plotly visualizations (interactive, need .show() to display)
    generate_plotly_visualizations(grouped_df, df_viz)