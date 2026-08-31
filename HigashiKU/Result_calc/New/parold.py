import os
import pyarrow as pa
import pyarrow.parquet as pq
import pyarrow.csv as pv
import pyarrow.compute as pc   

# -----------------------------
# Configuration
# -----------------------------
OUTPUT_ROOT = "parqData"
CHECK_COLS = 10
INITIAL_C = 91131
ROWS_PER_SECOND_WINDOW = 600

# -----------------------------
# Helpers
# -----------------------------
def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

# -----------------------------
# Main processing loop
# -----------------------------
def process_rows(batch_iterator, schema):
    c = INITIAL_C

    folder_idx = 0
    file_idx = 0
    rows_in_file = 0
    total_rows = 0

    ensure_dir(OUTPUT_ROOT)
    writer = None

    for batch_num, batch in enumerate(batch_iterator,start=1):
        # ---- 1. Update counter c ----
        col = batch.column(CHECK_COLS)
        c -= pc.equal(col, "-1").sum().as_py()

        if c <= 0:
            c = 1

        max_rows_per_file = c * ROWS_PER_SECOND_WINDOW

        # ---- 2. Open writer ----
        if writer is None:
            folder_path = os.path.join(
                OUTPUT_ROOT, f"batch_{folder_idx:03d}"
            )
            ensure_dir(folder_path)

            file_path = os.path.join(
                folder_path, f"part_{file_idx:03d}.parquet"
            )

            writer = pq.ParquetWriter(
                file_path,
                schema,
                compression="zstd"
            )
            rows_in_file = 0

        # ---- 3. Write batch ----
        writer.write_table(pa.Table.from_batches([batch]))
        batch_rows = batch.num_rows
        rows_in_file += batch_rows
        total_rows += batch_rows

        if batch_num % 10 == 0:
            print(f"[Batch {batch_num}] Total rows: {total_rows},"
            f"Folder {folder_idx}, File {file_idx}, Rows in current file: {rows_in_file}, c={c}")


        # ---- 4. Rotate file ----
        if rows_in_file >= max_rows_per_file:
            writer.close()
            writer = None
            file_idx += 1

            if file_idx == 6:
                file_idx = 0
                folder_idx += 1

            if file_idx % 10 == 0:
                print(f"Folder {folder_idx}, File {file_idx}, rows_in_file {rows_in_file}, c={c}")


    if writer:
        writer.close()
        print(f"Final file written: Folder {folder_idx}, File {file_idx}, Total rows: {total_rows}")


# -----------------------------
# Example usage
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

    csv_path = "/media/kulla/1TB/log_individual_pedestrians.csv"

    def batch_generator():
        def handle_bad_row(row):
            # optional: log bad rows
            # with open("bad_rows.log", "a") as f:
            #     f.write(row + "\n")
            return "skip"

        with pv.open_csv(
            csv_path,
            read_options=pv.ReadOptions(block_size=64_000_000),
            parse_options=pv.ParseOptions(
                delimiter=",",
                invalid_row_handler=handle_bad_row
            )
        ) as reader:
            for batch in reader:
                yield batch.cast(schema)

    process_rows(batch_generator(), schema)
