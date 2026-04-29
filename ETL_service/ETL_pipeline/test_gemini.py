import os, sys
from google import genai
from google.genai import types

key = os.environ.get("GEMINI_API_KEY", "")
print(f"Key present: {bool(key)} len={len(key)}")

client = genai.Client(api_key=key)
r = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Say hello in one word",
    config=types.GenerateContentConfig(temperature=0.1),
)
print("Gemini response:", r.text)
