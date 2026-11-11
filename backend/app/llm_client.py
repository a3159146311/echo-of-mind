"""对 llama-server 的最小封装。系统提示词在此固定注入——
这是心语人格的唯一出处，修改需谨慎。"""
import httpx

LLAMA_SERVER = "http://localhost:8080"

SYSTEM_PROMPT = (
    "你是心语，一位温和的倾听者。你的原则：\n"
    "1. 先接住情绪，再谈建议。多回应感受，如'听起来…''这种感觉确实…'。\n"
    "2. 回复简短，通常不超过三句话，像朋友聊天，绝不列编号清单。\n"
    "3. 不诊断、不评判、不催促。对方想聊什么就陪什么。\n"
    "4. 对方询问具体建议时才给建议，且一次只给一条。\n"
    "5. 察觉对方可能有自伤念头时，温和地提到 12356 心理援助热线。"
)


def chat_completion(user_text: str, history: list[dict] | None = None) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": user_text})
    resp = httpx.post(
        f"{LLAMA_SERVER}/v1/chat/completions",
        json={"model": "xinlyu", "messages": messages,
              "max_tokens": 200, "temperature": 0.8},
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
