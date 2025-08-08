import pandas as pd
import os
from dotenv import load_dotenv
import httpx
from tqdm import tqdm
import json
import re

# ==== Load API ====
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
headers = {"Authorization": f"Bearer {api_key}"}

# Đọc dữ liệu stories đã merge
df = pd.read_csv("outputs/merged_stories.tsv", sep='\t')
rows = []

# ==== Hàm gọi API sinh MCQ ====
def gen_mcq(story):
    prompt = f"""Given the following legal story:

\"\"\"{story}\"\"\"

Write 3 multiple-choice questions (with 4 options each, and mark the correct one) to test understanding of:
1. the legal concept illustrated by the story (type: "concept"),
2. the expected outcome or ending (type: "ending"),
3. the limitation or boundary of the legal doctrine (type: "limitation").

Return the result as a JSON array, with each item having:
- 'type' (one of: "concept", "ending", "limitation"),
- 'question',
- 'options' (list of 4 strings),
- 'answer' (one of the 4 options)."""

    data = {
        "model": "gpt-3.5-turbo",  # hoặc dùng openrouter model khác như mistralai/mistral-7b-instruct
        "messages": [
            {"role": "system", "content": "You are a legal teaching assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    resp = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=120)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]

# ==== Hàm làm sạch phản hồi JSON ====
def clean_json_content(content):
    content = content.strip()
    content = re.sub(r"^```json", "", content, flags=re.IGNORECASE).strip()
    content = re.sub(r"^```", "", content).strip()
    content = re.sub(r"```$", "", content).strip()
    try:
        json.loads(content)
    except Exception:
        return json.dumps({"error": "Invalid JSON returned by model", "raw": content})
    return content

# ==== Sinh MCQ cho từng story của từng model ====
model_mapping = {
    "mistral": "mistralai/mistral-7b-instruct",
    "llama3": "meta-llama/llama-3-8b-instruct",
    "gpt35": "gpt-3.5-turbo"
}

for _, row in tqdm(df.iterrows(), total=len(df)):
    for model_key in model_mapping:
        story = row.get(f"{model_key}_story", "")
        if pd.isna(story) or not story.strip():
            continue

        try:
            mcqs_raw = gen_mcq(story)
            mcqs_clean = clean_json_content(mcqs_raw)
        except Exception as e:
            mcqs_clean = json.dumps({"error": str(e)})

        result_row = {
            "doctrine": row.get("doctrine", ""),
            "definition": row.get("definition", ""),
            "model": model_key,
            "story": story,
            "mcqs_json": mcqs_clean
        }
        rows.append(result_row)

        # Hiển thị ngay kết quả vừa xử lý
        print(f"\n✅ Done: {row.get('doctrine', '')} | Model: {model_key}")
        try:
            mcqs_parsed = json.loads(mcqs_clean)
            if isinstance(mcqs_parsed, list) and mcqs_parsed:
                for mcq in mcqs_parsed:
                    print(f"  [{mcq.get('type', '?')}] Q: {mcq.get('question', '')}")
                    print(f"     Options: {mcq.get('options', [])}")
                    print(f"     Answer: {mcq.get('answer', '')}")
                    
            else:
                print(f"  Error or Empty: {mcqs_parsed}")
        except Exception as e:
            print(f"  Failed to parse MCQs: {e}")

# ==== Ghi kết quả ra file ====
os.makedirs("outputs", exist_ok=True)
output_path = "outputs/merged_mcq.tsv"
pd.DataFrame(rows).to_csv(output_path, sep='\t', index=False)

# ==== In 3 mẫu kết quả ====
print("\n📋 Sample results:")
for r in rows[:3]:
    print(f"\nDoctrine: {r['doctrine']} | Model: {r['model']}")
    try:
        mcqs = json.loads(r["mcqs_json"])
        if isinstance(mcqs, list) and mcqs:
            print(f"  [✔] {mcqs[0]['type']} - {mcqs[0]['question']}")
            print(f"      Options: {mcqs[0]['options']}")
            print(f"      Answer: {mcqs[0]['answer']}")
        else:
            print(f"  [✖] Error or Empty: {mcqs}")
    except Exception as e:
        print(f"  Failed to parse JSON: {e}")

print(f"\n✅ MCQs generated and saved to: {output_path}")
