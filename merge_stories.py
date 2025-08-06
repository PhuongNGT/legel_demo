import pandas as pd

# Đọc dữ liệu gốc
df_origin = pd.read_csv("data/legal_doctrines_294.csv")

# Đọc 3 kết quả
df_mistral = pd.read_csv("outputs/294-doctrines-mistral/294_doctrine_stories.tsv", sep='\t')
df_llama3 = pd.read_csv("outputs/294-doctrines-llama3/294_doctrine_stories.tsv", sep='\t')
df_gpt35  = pd.read_csv("outputs/294-doctrines-gpt-3.5/294_doctrine_stories.tsv", sep='\t')

# Đổi tên cột story
df_mistral.rename(columns={"story": "mistral_story"}, inplace=True)
df_llama3.rename(columns={"story": "llama3_story"}, inplace=True)
df_gpt35.rename(columns={"story": "gpt35_story"}, inplace=True)

# Merge lần lượt
df_merged = df_origin.merge(
    df_mistral[['doctrine', 'mistral_story']], on='doctrine'
).merge(
    df_llama3[['doctrine', 'llama3_story']], on='doctrine'
).merge(
    df_gpt35[['doctrine', 'gpt35_story']], on='doctrine'
)

# Xuất file
df_merged.to_csv("outputs/merged_stories.tsv", sep='\t', index=False)
print("✅ Đã xuất: outputs/merged_stories.tsv")
