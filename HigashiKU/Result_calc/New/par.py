import os
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.csv as pv
import pyarrow.compute as pc   
from datetime import datetime

# -----------------------------
# Configuration
# -----------------------------
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

csv_path = "/media/kulla/1TB/２Crowdwalk_sim/log010626-9/individual/log_individual_pedestrians.csv"
OUTPUT_ROOT = f"parqData/parqData_{timestamp}"
# How many seconds of simulation time to put in each file
SECONDS_PER_FILE = 600 



# -----------------------------
# Helpers
# -----------------------------
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

# -----------------------------
# Main processing loop
# -----------------------------
def process_rows(batch_iterator, schema):
    folder_idx = 0
    file_idx = 0
    total_rows = 0
    current_window_idx = -1  # Tracks which 600s block we are in

    ensure_dir(OUTPUT_ROOT)
    writer = None

    for batch_num, batch in enumerate(batch_iterator, start=1):
        # ---- 1. Check Time for Rotation ----
        # Extract the 'current_traveling_period' column (index 15)
        time_col = batch.column("current_traveling_period")
        max_time = pc.max(time_col).as_py()
        
        # Calculate which 600-second window this batch belongs to
        this_batch_window = int(max_time // SECONDS_PER_FILE)

        # Rotate file if we have moved into a new time window
        if this_batch_window > current_window_idx:
            if writer:
                writer.close()
                file_idx += 1
                # Group files into folders (6 files per folder as per your original structure)
                if file_idx >= 6:
                    file_idx = 0
                    folder_idx += 1
            
            # Prepare new file path
            folder_path = os.path.join(OUTPUT_ROOT, f"batch_{folder_idx:03d}")
            ensure_dir(folder_path)
            file_path = os.path.join(folder_path, f"part_{file_idx:03d}.parquet")

            print(f"Opening new file: {file_path} for time window starting at {this_batch_window * SECONDS_PER_FILE}s")
            
            writer = pq.ParquetWriter(file_path, schema, compression="zstd")
            current_window_idx = this_batch_window

        # ---- 2. Write batch ----
        writer.write_table(pa.Table.from_batches([batch]))
        total_rows += batch.num_rows

        if batch_num % 10 == 0:
            print(f"[Batch {batch_num}] Total rows processed: {total_rows} | Current Sim Time: {max_time}s")

    if writer:
        writer.close()
        print(f"Processing complete. Total rows: {total_rows}")

# -----------------------------
# Schema and Generator (Same as before)
# -----------------------------
if __name__ == "__main__":
    schema = pa.schema([
        ("pedestrianID", pa.string()),
        ("current_position_in_model_x", pa.float64()),
        ("current_position_in_model_y", pa.float64()),
        ("current_position_in_model_z", pa.float64()),
        ("current_position_for_drawing_x", pa.float64()),
        ("current_position_for_drawing_y", pa.float64()),
        ("current_position_for_drawing_z", pa.float64()),
        ("current_acceleration", pa.float64()),
        ("current_velocity", pa.float64()),
        ("current_linkID", pa.string()),
        ("current_nodeID_of_forward_movement", pa.string()),
        ("current_nodeID_of_backward_movement", pa.string()),
        ("current_distance_from_node_of_forward_movement", pa.float64()),
        ("current_moving_direction", pa.int32()),
        ("generated_time", pa.int32()),
        ("current_traveling_period", pa.int32()),
        ("current_exposure", pa.float64()),
        ("amount_exposure", pa.float64()),
        ("current_status_by_exposure", pa.string()),
        ("next_assigned_passage_node", pa.string())
    ])

    def batch_generator():
        # Correctly nest the handler inside ParseOptions
        parse_opts = pv.ParseOptions(
            delimiter=",",
            invalid_row_handler=lambda row: "skip"
        )
        
        with pv.open_csv(
            csv_path,
            read_options=pv.ReadOptions(block_size=64_000_000),
            parse_options=parse_opts  # Pass the object here
        ) as reader:
            for batch in reader:
                yield batch.cast(schema)

    process_rows(batch_generator(), schema)