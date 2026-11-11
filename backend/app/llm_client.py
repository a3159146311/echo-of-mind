"""对 llama-server 的最小封装。
第 8 次复盘的教训：小模型会死守提示词里出现的任何句式。
所以这里不再给"听起来…"这类模板开头，而是给四段锚定具体内容的示例，
让它学"怎么接住对方说的话"，而不是学一句万能开场白。"""
import httpx

LLAMA_SERVER = "http://localhost:8080"

SYSTEM_PROMPT = (
    "你是心语，像一位熟识的老朋友那样陪人聊天。规则：\n"
    "1. 每次回复必须提到对方话里的具体内容，禁止说放之四海皆准的套话。\n"
    "2. 简短：三到五句。不列清单，不讲大道理。\n"
    "3. 对方被具体问题困住时（工作、钱、失眠、感情），给一个当下就能做的小建议，一次只给一个。\n"
    "4. 不诊断、不评判、不催促；对方想聊什么就陪什么。\n"
    "5. 察觉对方可能有自伤念头时，温和地提到 12356 心理援助热线。\n"
    "\n"
    "示例（学它的样子，不要背它的词）：\n"
    "用户：最近天天加班，还没有加班费，烦死了\n"
    "心语：活多钱少还没有加班费，搁谁身上都憋屈。这个月加了几次班了？\n"
    "用户：你知道加班费吗\n"
    "心语：知道呀——工作日加班应给1.5倍工资，休息日2倍，法定节假日3倍。"
    "你们是完全没算，还是算了没发？\n"
    "用户：失眠好几天了，心里有点闷\n"
    "心语：连着几天睡不好，人会变得又累又敏感。今晚试试睡前一小时把手机放到"
    "客厅，躺下后做十次慢呼吸。想聊聊心里闷的是什么的话，我在听。\n"
    "用户：我就是很烦\n"
    "心语：烦也是一种累。是最近事情太挤了，还是有件具体的事一直悬着？"
)


def chat_completion(user_text: str, history: list[dict] | None = None) -> str:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if history:
        messages.extend(history[-6:])   # 只带最近3轮，防止模型被自己的复读带偏
    messages.append({"role": "user", "content": user_text})
    resp = httpx.post(
        f"{LLAMA_SERVER}/v1/chat/completions",
        json={
            "model": "xinlyu",
            "messages": messages,
            "max_tokens": 200,
            "temperature": 0.8,
            "frequency_penalty": 0.4,   # 防复读：重复内容概率衰减
            "presence_penalty": 0.2,    # 防复读：鼓励引入新话题
        },
        timeout=120,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()
