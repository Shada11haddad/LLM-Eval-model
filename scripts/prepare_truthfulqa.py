import pandas as pd
url = "https://raw.githubusercontent.com/sylinrl/TruthfulQA/main/TruthfulQA.csv"
df = pd.read_csv(url)
df = df.rename(columns={"Question": "question", "Best Answer": "answer"})
df[["question", "answer"]].to_csv("data/raw/truthfulqa.csv", index=False)
print("saved", len(df), "rows")