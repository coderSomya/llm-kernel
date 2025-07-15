import requests

def ask_ollama_stream(query, model="qwen2.5:latest"):
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": query}],
        "stream": True
    }
    buffer = []
    try:
        with requests.post(url, json=payload, stream=True) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if line:
                    data = line.decode("utf-8")
                    import json
                    chunk = json.loads(data)
                    content = chunk.get("message", {}).get("content")
                    if content:
                        buffer.append(content)
        return "".join(buffer)
    except requests.RequestException as e:
        return f"Error communicating with Ollama: {e}"


ques = """Create a simple character device driver that supports basic read/write operations with a
 1KB internal buffer"""
result = ask_ollama_stream(ques)
print(result)