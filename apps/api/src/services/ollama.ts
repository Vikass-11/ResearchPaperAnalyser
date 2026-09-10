export async function askOllama(prompt: string): Promise<string | null> {
  if ((process.env.AI_PROVIDER ?? 'heuristic').toLowerCase() !== 'ollama') {
    return null;
  }

  const host = process.env.OLLAMA_HOST ?? 'http://localhost:11434';
  const model = process.env.OLLAMA_CHAT_MODEL ?? 'llama3.1:8b';

  try {
    const response = await fetch(`${host}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model,
        prompt,
        stream: false,
        options: {
          temperature: 0.1,
          num_ctx: 8192,
        },
      }),
    });

    if (!response.ok) return null;
    const data = (await response.json()) as { response?: string };
    return data.response?.trim() || null;
  } catch {
    return null;
  }
}
