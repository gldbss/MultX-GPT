import requests
from time import sleep as slp
import asyncio
from telegram import Bot, Update



# Define API key
openrouter_API = "PAST_YOUR_OPENROUTER_API_KEY"
multx_gpt = "PAST_YOUR_TELEGRAM_TOKEN"

# Define models
deepseek_model = "deepseek/deepseek-chat-v3.1:free"
nemotron_nano = "nvidia/nemotron-nano-9b-v2:free"
gemma = "google/gemma-3n-e4b-it:free"
glm = "z-ai/glm-4.5-air:free"
#venice = "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"

models_list = [deepseek_model, nemotron_nano, gemma, glm] #List of models

# Setup openrouter
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {openrouter_API}",
    "Content-Type": "application/json",
}

# Receiver
async def resv_msg(bot: Bot, offset: int = None, timeout: int = 20):
    try:
        updates = await bot.get_updates(offset=offset, timeout=timeout)
    except Exception as e:
        # network / api error -> log and return nothing
        print(f"[resv_msg] get_updates error: {e}")
        return None, None, None

    if not updates:
        return None, None, None

    for upd in updates:
        # prefer direct message text; skip non-text or command-only updates
        if upd is None:
            continue
        msg = getattr(upd, "message", None)
        if msg is None:
            continue
        text = getattr(msg, "text", None)
        if not text:
            continue
        chat_id = getattr(msg.chat, "id", None)
        update_id = getattr(upd, "update_id", None)
        # return first text message
        print(f"[resv_msg] got update_id={update_id} chat_id={chat_id} text={text!r}")
        return update_id, chat_id, text

        # nothing suitable found
    return None, None, None


# Send
async def trns_msg(bot: Bot, chat_id: int, text: str):
    """
    Sends `text` to `chat_id` using the provided Bot.
    Autonomous: only performs sending and minimal logging.
    """
    if chat_id is None or text is None:
        return
    try:
        await bot.send_message(chat_id=chat_id, text=text)
        print(f"[trns_msg] sent to {chat_id}: {text!r}")
    except Exception as e:
        print(f"[trns_msg] send error to {chat_id}: {e}")

# Generator
def gen_reply(prompt):
    prev_out = ""
    if prompt != "quit":
        for i in range(len(models_list)):
            cmd = prompt + "\nYou are a bunch of ai tools that are connected in sequence such that the output of one will be feeded to an other. Also the input is take and the output is give through a telegram bot named \"MultX GPT\". Be helpful to the user. The following is the replay given by previous ai models to the above prompt. Please refine it and give me the appropriate result. Also make the output be compatable with telegram interface. Also give me only the relateable answer and do not give me statments like,\n Okay, that's a good start! Here's a refined version, focusing on clarity, Telegram-friendliness, and incorporating elements of being a multi-stage AI system, while keeping it concise and welcoming:\n**Key improvements and explanations:**\n*   **Stronger opening:** \"Hey there!\" is more welcoming than just \"Hi there!\"\n*   **Clearer explanation:**  Emphasizes the \"team\" aspect and the collaborative process (\"super-charged knowledge engine\"). The emojis help highlight key aspects.\n*   **Concise descriptions:**  The bullet points clearly list capabilities.\n*   **Direct call to action:**  \"Just type your message below!\" is obvious and encourages interaction.\n*   **Telegram-appropriate tone:**  The language and emojis are suitable for a chatbot environment.\n*    **Visual separation:**  Using line breaks and emojis helps with readability in a chat.\n*   **Emojis for visual appeal**: added emojis to enhance user experience.\nThis version is designed to be engaging and informative within the context of a Telegram bot interface.  It tells the user *what* MultX is, *how* it works (in a simplified way), and *what* it can do, all while being friendly and approachable.  Hopefully, it clearly communicates that MultX is not just *one* AI, but a coordinated system!\n\nJust give me the corrected output\n" + prev_out
            data = {
                "model": models_list[i],
                "messages": [
                    {"role": "user", "content": cmd}
                ]
            }
            resp = requests.post(url, headers=headers, json=data)
            resp.raise_for_status()
            reply = resp.json()
            prev_out = reply["choices"][0]["message"]["content"]
        slp(0.4)
        return prev_out
    else:
        return None

# main loop
print("Welcome to MultX GPT")

async def main():
    bot = Bot(token=multx_gpt)
    offset = None
    loop = asyncio.get_running_loop()
    print("Minimal Telegram bridge started. Polling for messages... (Ctrl-C to stop)")
    while True:
        update_id, chat_id, text = await resv_msg(bot, offset=offset, timeout=20)
        #prompt=input("user:\n").strip().lower()
        if update_id is None:
            continue
        offset = update_id + 1
        if text is None:
            print("[main] warning: received update with no text; skipping")
            continue
        #gen_out = gen_reply(text)
        try:
            gen_out = await loop.run_in_executor(None, gen_reply, text)
        except Exception as e:
            gen_out = f"Error generating reply: {e}"
            print("[main] gen_reply exception:", e)

        await trns_msg(bot, chat_id, gen_out)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:

        print("\nExiting.")
