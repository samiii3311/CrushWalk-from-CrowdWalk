import pyarrow.parquet as pq

table = pq.read_table("/home/kulla/CrowdWalk/crowdwalk/parqData/batch_000/part_000.parquet")
print(table.schema)
print(table.to_pandas().head())
