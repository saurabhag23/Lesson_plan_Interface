import asyncio
import openai
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import os
from openai import OpenAI

# Replace 'YOUR_OPENAI_API_KEY' with your actual OpenAI API key or set it as an environment variable
#OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'YOUR_OPENAI_API_KEY')
OPENAI_API_KEY="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"
openai.api_key = OPENAI_API_KEY
client=OpenAI(api_key = OPENAI_API_KEY)

app = FastAPI()

def openai_stream(prompt: str):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    for chunk in response:
        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
            text=chunk.choices[0].delta.content 
            yield text  
            #yield chunk['choices'][0]['delta']['content']
'''
async def openai_stream(prompt: str):
    response = await client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )

    async for chunk in response:
        if chunk['choices'] and chunk['choices'][0]['delta'] and chunk['choices'][0]['delta']['content']:
            yield chunk['choices'][0]['delta']['content']
'''


@app.post("/chat")
async def stream_data(request: Request):
    """Handle POST requests to stream data from OpenAI API."""
    body = await request.json()
    prompt = body.get('prompt', 'Tell me a story.')

    generator = openai_stream(prompt)
    return StreamingResponse(generator, media_type="text/event-stream")
'''
@app.get("/stream")
async def stream_data(request: Request):
    prompt = request.query_params.get('prompt', 'Tell me a story.')
    generator = openai_stream(prompt)
    return StreamingResponse(generator, media_type="text/event-stream")
'''

