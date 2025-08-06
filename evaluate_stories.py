import pandas as pd
from textstat import flesch_reading_ease

# Đọc 3 kết quả
df_mistral = pd.read_csv("outputs/294-doctrines-mistral/294_doctrine_stories.tsv", sep='\t')
df_llama3  = pd.read_csv("outputs/294-doctrines-llama3/294_doctrine_stories.tsv", sep='\t')
df_gpt35   = pd.read_csv("outputs/294-doctrines-gpt-3.5/294_doctrine_stories.tsv", sep='\t')

# Gộp thành 1 DataFrame dài
df_all = pd.concat([
    df_mistral.assign(model="mistral"),
    df_llama3.assign(model="llama3"),
    df_gpt35.assign(model="gpt-3.5"),
])

def compute_metrics(row):
    story = str(row['story'])
    words = story.split()
    word_count = len(words)
    ttr = len(set(words)) / len(words) if words else 0
    flesch = flesch_reading_ease(story) if story else 0
    return pd.Series({
        "length": len(story),
        "word_count": word_count,
        "ttr": ttr,
        "flesch_score": flesch
    })

metrics = df_all.apply(compute_metrics, axis=1)
df_all = pd.concat([df_all, metrics], axis=1)

df_all.to_csv("outputs/story_evaluation.tsv", sep='\t', index=False)
print("✅ Created outputs/story_evaluation.tsv with all metrics.")

