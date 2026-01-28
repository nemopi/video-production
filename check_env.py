import os
import sys

try:
    import google.generativeai as genai
    print("google.generativeai: INSTALLED")
except ImportError:
    print("google.generativeai: NOT INSTALLED")

api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
if api_key:
    print("API Key: FOUND")
else:
    print("API Key: NOT FOUND")

# 念のため openai も確認
try:
    import openai
    print("openai: INSTALLED")
except ImportError:
    print("openai: NOT INSTALLED")
