import asyncio
import openai
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import os
from openai import OpenAI

from typing_extensions import override
from openai import AssistantEventHandler

'''
# To create new assistant
assistant = client.beta.assistants.create(
  name="Math Tutor",
  instructions="You are a personal math tutor. Write and run code to answer math questions.",
  tools=[{"type": "code_interpreter"}],
  model="gpt-4o",
)
'''

from openai import OpenAI
OPENAI_API_KEY='sk-None-VjP53dJpWzsqdMI6e57rT3BlbkFJfQy1nUIqja2UJgEXGjtw'
client=OpenAI(api_key = OPENAI_API_KEY)


class EventHandler(AssistantEventHandler):
  @override
  def on_text_created(self, text) -> None:
    print(f"\nassistant > ", end="", flush=True)

  @override
  def on_text_delta(self, delta, snapshot):
    print(delta.value, end="", flush=True)

  def on_tool_call_created(self, tool_call):
    print(f"\nassistant > {tool_call.type}\n", flush=True)

  def on_tool_call_delta(self, delta, snapshot):
    if delta.type == 'code_interpreter':
      if delta.code_interpreter.input:
        print(delta.code_interpreter.input, end="", flush=True)
      if delta.code_interpreter.outputs:
        print(f"\n\noutput >", flush=True)
        for output in delta.code_interpreter.outputs:
          if output.type == "logs":
            print(f"\n{output.logs}", flush=True)


threadids=dict()
app = FastAPI()
ASSISTANT_ID='asst_sGo1CzVWutfVbEzHmkmhCnIc'


def openai_stream(prompt: str, sessionid: str, close_session: bool):

    if sessionid in threadids.keys():
        thread = threadids[sessionid]
    else:
        thread = client.beta.threads.create()
        threadids[sessionid] = thread

    print("session id:", sessionid, "thread id:", thread.id)
    message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=prompt
    )


            
    with client.beta.threads.runs.stream(
    thread_id=thread.id,
    assistant_id=ASSISTANT_ID
    ) as stream:
       for text in stream.text_deltas:
            yield text  

    if close_session:
        print("Deleting thread :", thread.id)
        client.beta.threads.delete(thread.id) 


@app.post("/chat")
async def stream_data(request: Request):
    """Handle POST requests to stream data from OpenAI API."""
    body = await request.json()
    prompt = body.get('prompt', 'Tell me a story.')
    sessionid = body.get('session_id',"default_session")
    if prompt == "Exit":
        print("Closing session..")
        close_session=True
    else:
        close_session=False

    generator = openai_stream(prompt, sessionid, close_session=close_session)
    return StreamingResponse(generator, media_type="text/event-stream")
'''
@app.get("/stream")
async def stream_data(request: Request):
    prompt = request.query_params.get('prompt', 'Tell me a story.')
    generator = openai_stream(prompt)
    return StreamingResponse(generator, media_type="text/event-stream")
'''

