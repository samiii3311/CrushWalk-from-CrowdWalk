import os 
import pyarrow as pa 
import pyarrow.parquet as pq 
import pyarrow.csv as pv 

# ----------------------------- 
# # Configuration 
# ----------------------------- 
OUTPUT_ROOT = "parqData" 
CHECK_COLS = 10 # 10th column 
#INITIAL_C = 25 
INITIAL_C = 91131 
ROWS_PER_SECOND_WINDOW = 300 # 10 minutes 

# ----------------------------- 
# Helpers 
# ----------------------------- 
def ensure_dir(path): 
    os.makedirs(path, exist_ok=True) 

def write_parquet(rows, schema, folder_idx, file_idx): 
    folder_path = os.path.join(OUTPUT_ROOT, f"batch_{folder_idx:03d}") 
    ensure_dir(folder_path) 
    
    file_path = os.path.join( 
        folder_path, 
        f"part_{file_idx:03d}.parquet" 
    ) 
    
    table = pa.Table.from_pylist(rows, schema=schema) 
    pq.write_table( table, file_path, compression="zstd" ) 
    
    # ----------------------------- 
    # Main processing loop 
    # ----------------------------- 
    
    def process_rows(row_iterator, schema): 
        c = INITIAL_C 
        buffer = [] 
        
        folder_idx = 0 
        file_idx = 0 
        rows_written = 0 
        
        ensure_dir(OUTPUT_ROOT) 
        
        for row in row_iterator: 
            # 1. Check column 10 for -1 
            if row[CHECK_COLS] == -1: 
                c -= 1 
                
            # Safety: avoid zero or negative c 
            if c <= 0: 
                c = 1 
                
            buffer.append(row) rows_written += 1 
            
            # 2. Determine threshold 
            file_row_limit = c * ROWS_PER_SECOND_WINDOW 
            
            # 3. Write file when threshold reached 
            if rows_written >= file_row_limit: 
                write_parquet( 
                    rows=buffer, 
                    schema=schema, 
                    folder_idx=folder_idx, 
                    file_idx=file_idx 
                ) 
                
                buffer.clear() 
                rows_written = 0 
                file_idx += 1 
                
                # 4. New folder every 6 files 
                if file_idx == 6: 
                    file_idx = 0 
                    folder_idx += 1 
            
        # Flush remaining rows 
        if buffer: 
            write_parquet( 
                rows=buffer, 
                schema=schema, 
                folder_idx=folder_idx, 
                file_idx=file_idx 
            ) 
            
# ----------------------------- 
# # Example usage 
# # ----------------------------- 
if __name__ == "__main__": 
    # Example schema (adjust to your real data) 
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
    #csv_path = "/home/kulla/CrowdWalk/crowdwalk/HigashiKU/log/individual/log_individual_pedestrians.csv" 
    # Example row generator (replace with real source) 
    
    def row_generator(): 
        with pv.open_csv(csv_path) as reader: 
            for next_batch in reader: 
                columns = next_batch.to_pydict() 
                num_rows = next_batch.num_rows 
                
            for i in range(1,num_rows): 
                yield [columns[col][i] for col in columns] 
                
    process_rows(row_generator(), schema)