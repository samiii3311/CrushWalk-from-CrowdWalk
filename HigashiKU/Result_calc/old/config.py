import datetime

# Timestamp for unique file names
DT_STR = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

# === INPUT/OUTPUT FILE PATHS ===
# The large input log file
INPUT_FILE = "/media/kulla/1TB/log_individual_pedestrians.csv"

# The XML file containing link length and width (used for density calculation)
XML_FILE = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/Higashi.xml" 

# Intermediate output files
OUTPUT_FILE_AGGREGATED = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/logoutput/aggregated_pedestrians.csv"
OUTPUT_FILE_TOTAL_V = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/logoutput/totV.csv"

# Final combined and pivoted data file (contains Velocity, Count, and Density pivots)
OUTPUT_FILE_PIVOT = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/logoutput/velocity_pivot.csv"

# Visualization output file paths (using the global DT_STR)
PLOT_AGENT_COUNT = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/logoutput/agent_count_top10_stacked_bar_" + DT_STR + ".png"
PLOT_TOTAL_VELOCITY = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/logoutput/total_velocity_top10_line_" + DT_STR + ".png"
PLOT_POPULATION_DENSITY = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/logoutput/population_density_top10_line_" + DT_STR + ".png"


# === PROCESSING CONFIGURATION ===
CHUNK_SIZE = 1_000_000  # Process 1 million rows at a time (adjust based on your RAM)
TICK_INTERVAL = 600     # X-axis tick interval for plots (e.g., every 10 minutes)

# Define the expected data types BEFORE reading the file (optimizes memory)
DTYPE_MAPPING = {
    'current_traveling_period': 'float64',  
    'pedestrianID': 'object',           
    'current_linkID': 'object', 
    'current_velocity': 'float32',      
    'current_acceleration': 'float32',  
    'current_position_in_model_x': 'float32', 
    'current_position_in_model_y': 'float32'
}