from dotenv import load_dotenv
import os

load_dotenv()

print("API KEY:", os.getenv("OPENAI_API_KEY"))
print("BASE URL:", os.getenv("OPENAI_BASE"))

