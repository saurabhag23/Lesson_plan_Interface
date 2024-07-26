import type { NextApiRequest, NextApiResponse } from "next";

export default async function chatHandler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== 'POST') {
    res.status(405).json({ error: 'Method not allowed' });
    return;
  }

  res.writeHead(200, {
    'Content-Type': 'text/event-stream',
    'Cache-Control': 'no-cache, no-transform',
    'Connection': 'keep-alive',
  });

  try {
    // Call the FastAPI server's /chat endpoint
    const response = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt: req.body.messages[req.body.messages.length - 1].content, session_id: req.body.session_id }),
    });

    if (!response.ok) {
      throw new Error(response.statusText);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (reader) {
      while (true) {
        const { done, value } = await reader.read();
	console.log("done-", done)
	console.log("value-", value) 
        if (done) break;
        const text = decoder.decode(value, { stream: true });
	console.log("text:", text)
        res.write(text); 
        //const lines = text.split('\n');
        //for (const line of lines) {
          //if (line.startsWith('data: ')) {
          //  res.write(line + '\n');
         // }
        //}
      }
    }

    //res.write('data: [DONE]\n\n');
    res.end();
  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'An error occurred', details: error instanceof Error ? error.message : String(error) });
  }
}

