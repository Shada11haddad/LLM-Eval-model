import sys, os
sys.path.insert(0, '.')
from src.storage.database import list_runs, load_results
import pandas as pd

runs = list_runs()
print(runs[['run_id', 'dataset_name', 'task_type', 'started_at']].to_string())
