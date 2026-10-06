import asyncio
from dotenv import load_dotenv; load_dotenv()
import os
import json
from openai import AsyncOpenAI
from app.schemas.literature_analysis import LiteratureAnalysisSchema

async def main():
    client = AsyncOpenAI(
        api_key=os.environ.get('LLM_API_KEY'),
        base_url=os.environ.get('LLM_BASE_URL')
    )
    prompt = "Analyze this paper: Title: 'Attention is All You Need', Abstract: 'We propose the Transformer...'"
    try:
        response = await client.chat.completions.create(
            model=os.environ.get('LLM_MODEL'),
            messages=[{'role': 'user', 'content': prompt}],
            tools=[{
                'type': 'function',
                'function': {
                    'name': 'submit_literature_analysis',
                    'description': 'Submit literature analysis',
                    'parameters': LiteratureAnalysisSchema.model_json_schema()
                }
            }],
            tool_choice={'type': 'function', 'function': {'name': 'submit_literature_analysis'}},
            temperature=0.2
        )
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            args = json.loads(tool_call.function.arguments)
            print('SUCCESS:', args.keys())
        else:
            print('FAILED: No tool calls returned')
            print(response.choices[0].message.content)
    except Exception as e:
        print('FAILED:', str(e))

asyncio.run(main())
