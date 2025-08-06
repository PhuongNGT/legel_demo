import subprocess

models = ["mistral", "llama3", "gpt-3.5"]

for model in models:
    print(f"🚀 Generating stories with model: {model}")
    subprocess.run(["python", "main.py", "--model", model])

