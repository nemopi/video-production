import os
print(f"OPENAI_API_KEY: {'FOUND' if os.environ.get('OPENAI_API_KEY') else 'NOT FOUND'}")
