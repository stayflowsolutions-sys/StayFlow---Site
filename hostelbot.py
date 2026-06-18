from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv
import os
import json
from datetime import datetime

load_dotenv()

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


MEMORY_FILE = "conversations.json"


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}

    with open(
        MEMORY_FILE,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)



def save_memory(data):

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )



def save_message(phone, role, text):

    memory = load_memory()

    if phone not in memory:
        memory[phone] = {
            "status": "AI",
            "messages": []
        }


    memory[phone]["messages"].append(
        {
            "role": role,
            "text": text,
            "time": str(datetime.now())
        }
    )


    save_memory(memory)



contexto = """
You are the virtual assistant of Hostel Lagares in Mendoza.

Rules:
Answer in the guest language.
Be friendly.
Never invent availability.
Reception confirms reservations.

If the guest asks for human, reception or staff,
say you are transferring them.

Check in: 13:00
Check out: 10:00

Breakfast: 08:00 to 10:00

WiFi available.
Shared kitchen.
Laundry available.
Towels available.

Tours:
Wine tours.
Mountain activities.
Termas de Cacheuta.
"""



def ask_ai(phone, question):

    memory = load_memory()

    history = []


    if phone in memory:

        for item in memory[phone]["messages"][-10:]:

            history.append(
                {
                    "role": item["role"],
                    "content": item["text"]
                }
            )


    response = client.chat.completions.create(

        model="gpt-4.1-mini",

        temperature=0.3,

        messages=[
            {
                "role":"system",
                "content":contexto
            }
        ]
        +
        history
        +
        [
            {
                "role":"user",
                "content":question
            }
        ]

    )


    return response.choices[0].message.content




@app.route("/")
def home():

    return "StayFlow Bot online"



@app.route("/message", methods=["POST"])
def message():

    data = request.json


    phone = data.get(
        "phone",
        "unknown"
    )


    text = data.get(
        "message",
        ""
    )


    save_message(
        phone,
        "user",
        text
    )


    answer = ask_ai(
        phone,
        text
    )


    save_message(
        phone,
        "assistant",
        answer
    )


    return jsonify(
        {
            "reply": answer
        }
    )



if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=10000
    )
