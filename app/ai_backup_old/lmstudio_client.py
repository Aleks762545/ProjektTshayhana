import requests

LMSTUDIO_URL = "http://localhost:1234/v1/chat/completions"

def ask_llm(messages, temperature=0.3):
    """messages = [ {"role": "user","content": "..."} ] """
    payload = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 400,
        "stream": False
    }
    r = requests.post(LMSTUDIO_URL, json=payload)
    data = r.json()
    return data["choices"][0]["message"]["content"]
