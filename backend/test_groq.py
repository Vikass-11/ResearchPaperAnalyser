import asyncio
from dotenv import load_dotenv; load_dotenv()
import os
from pydantic import BaseModel, Field
from openai import AsyncOpenAI
import json

class TestOutput(BaseModel):
    result: str = Field(description='A simple greeting')
    number: int = Field(description='The number 42')

async def main():
    print('API Key starts with:', os.environ.get('LLM_API_KEY', '')[:5])
    print('Base URL:', os.environ.get('LLM_BASE_URL'))
    print('Model:', os.environ.get('LLM_MODEL'))
    client = AsyncOpenAI(
        api_key=os.environ.get('LLM_API_KEY'),
        base_url=os.environ.get('LLM_BASE_URL')
    )
    try:
        response = await client.chat.completions.create(
            model=os.environ.get('LLM_MODEL'),
            messages=[{'role': 'user', 'content': 'Say hello and give me 42'}],
            tools=[{
                'type': 'function',
                'function': {
                    'name': 'submit_test',
                    'description': 'Submit test result',
                    'parameters': TestOutput.model_json_schema()
                }
            }],
            tool_choice={'type': 'function', 'function': {'name': 'submit_test'}}
        )
        tool_call = response.choices[0].message.tool_calls[0]
        args = json.loads(tool_call.function.arguments)
        print('Structured Output:', args)
        print('SUCCESS')
    except Exception as e:
        print('FAILED:', str(e))

asyncio.run(main())
