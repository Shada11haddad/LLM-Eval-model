import pandas as pd
import os
import kagglehub
from config import cfg

def load_truthfulqa():
    url = "https://raw.githubusercontent.com/sylinrl/TruthfulQA/main/TruthfulQA.csv"
    df = pd.read_csv(url)
    print(f" TruthfulQA loaded: {len(df)} questions")
    return df

def load_podcast_transcript():
    """Load podcast transcript from local raw folder or download from Kaggle"""
    raw_path = os.path.join(cfg.DATA_RAW_DIR, "acquired_transcripts_all.txt")
    if os.path.exists(raw_path):
        with open(raw_path, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"Loaded podcast transcript from local file ({len(text):,} chars)")
        return text
    
    print(" Downloading podcast dataset from Kaggle...")
    dataset_path = kagglehub.dataset_download("harrywang/acquired-podcast-transcripts-and-rag-evaluation")
    for f in os.listdir(dataset_path):
        if f.endswith(".txt"):
            with open(os.path.join(dataset_path, f), "r", encoding="utf-8") as fp:
                text = fp.read()
            # save a copy locally for next time
            with open(raw_path, "w", encoding="utf-8") as out:
                out.write(text)
            print(f" Loaded and saved podcast transcript ({len(text):,} chars)")
            return text
    raise FileNotFoundError("No podcast transcript found in Kaggle dataset")