import os
import csv
from dotenv import load_dotenv
from model import get_model_name
from tqdm import tqdm
import argparse
import httpx

# ==== Load API key từ .env ====
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ OPENAI_API_KEY is missing. Please check your .env file.")
# ==== Tham số dòng lệnh ====
parser = argparse.ArgumentParser()
parser.add_argument("--model", type=str, required=True)
args = parser.parse_args()
model_name = get_model_name(args.model)

# ==== Đường dẫn ====
input_path = "data/legal_doctrines_294.csv"
output_dir = f"outputs/294-doctrines-{args.model}"
os.makedirs(output_dir, exist_ok=True)
output_file = os.path.join(output_dir, "294_doctrine_stories.tsv")

# ==== Hàm sinh truyện từ định nghĩa ====
def gen_story(definition, doctrine):
    prompt = f"""
You are a legal storytelling assistant. Your task is to create a short, fictional but realistic story that illustrates the legal concept of '{doctrine}'.

Definition: {definition}

Write a story (around 150-300 words) that helps a non-expert understand this legal concept through a relatable scenario.
"""
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": "You are a helpful legal storytelling assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    resp = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

# ==== Đọc dữ liệu và ghi kết quả ====
with open(input_path, newline='', encoding='utf-8') as infile, \
     open(output_file, 'w', encoding='utf-8', newline='') as outfile:
    reader = csv.DictReader(infile)
    writer = csv.writer(outfile, delimiter='\t')
    writer.writerow(["doctrine", "definition", "story"])

    for row in tqdm(reader, desc=f"Generating stories with {args.model}"):
        try:
            story = gen_story(row["definition"], row["doctrine"])
            writer.writerow([row["doctrine"], row["definition"], story])
        except Exception as e:
            print(f"[⚠️] Failed on {row['doctrine']} → {e}")
