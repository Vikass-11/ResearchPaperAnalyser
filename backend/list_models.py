from dotenv import load_dotenv; load_dotenv()
from openai import OpenAI
import os
client = OpenAI(api_key=os.environ.get('LLM_API_KEY'), base_url=os.environ.get('LLM_BASE_URL'))
for m in client.models.list(): print(m.id)
