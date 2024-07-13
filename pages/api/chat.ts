import OpenAI from "openai";
import type { NextApiRequest, NextApiResponse } from "next";

const openai = new OpenAI({
  apiKey: "", // Replace with your actual OpenAI API key
});

// Replace this with your actual Assistant ID
const assistantId = "";

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
    const thread = await openai.beta.threads.create();

    await openai.beta.threads.messages.create(thread.id, {
      role: "user",
      content: req.body.messages[req.body.messages.length - 1].content,
    });

    const run = await openai.beta.threads.runs.create(thread.id, {
      assistant_id: assistantId,
    });

    while (true) {
      const runStatus = await openai.beta.threads.runs.retrieve(thread.id, run.id);

      if (runStatus.status === "completed") {
        const messages = await openai.beta.threads.messages.list(thread.id);
        const assistantMessage = messages.data
          .filter(message => message.role === "assistant")
          .pop();

        if (assistantMessage && assistantMessage.content[0].type === "text") {
          const text = assistantMessage.content[0].text.value;
          // Send the response word by word to simulate streaming
          const words = text.split(' ');
          for (const word of words) {
            res.write(`data: ${JSON.stringify({ text: word + ' ' })}\n\n`);
            await new Promise(resolve => setTimeout(resolve, 50)); // Reduced from 100ms to 50ms
          }
        }
        break;
      } else if (runStatus.status === "failed") {
        throw new Error("Assistant run failed");
      }

      // Wait a bit before checking again
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    res.write('data: [DONE]\n\n');
    res.end();

  } catch (error) {
    console.error('Error:', error);
    res.status(500).json({ error: 'An error occurred', details: error instanceof Error ? error.message : String(error) });
  }
}
