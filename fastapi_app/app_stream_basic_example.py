import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse

app = FastAPI()

async def async_generator():
    """An async generator that yields data periodically."""
    for i in range(10):
        await asyncio.sleep(1)
        yield f"data: {i}\n\n"

@app.get("/stream")
async def stream_data(request: Request):
    """Stream data to the client."""
    generator = async_generator()
    return StreamingResponse(generator, media_type="text/event-stream")

