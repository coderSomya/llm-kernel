import requests


def ask_ollama_stream(query, model="qwen2.5:latest", system_prompt=None):
    url = "http://192.168.1.2:11434/api/chat"
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": query})
    payload = {
        "model": model,
        "messages": messages,
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


with open("kernel_standards.txt", "r") as f:
    kernel_standards = f.read()

ques = """
Create a simple character device driver that supports basic read/write operations with a
1KB internal buffer
Return only the code, no other text. No backticks. Just the simple executable code.
Follow the linux kernel coding style.
Use the latest linux kernel version.
Do not include any other text or explanation in the response.
"""

result = ask_ollama_stream(ques, system_prompt=kernel_standards)

with open("generated_driver.c", "w") as f:
    f.write(result)