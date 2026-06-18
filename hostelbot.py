from flask import Flask, request, jsonify
from openai import OpenAI
import os
import json
from datetime import datetime

app = Flask(__name__)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)


contexto = """
You are the virtual assistant of Hostel Lagares in Mendoza.

Rules:
Answer in the guest language.
Be friendly.
Never invent availability.
Reception confirms reservations.

If the guest asks for a human, reception, staff or someone real,
say you are transferring to reception.

Check in: 13:00
Check out: 10:00
Breakfast: 08:00 to 10:00

WiFi available.
Shared kitchen.
Laundry available.
Towels available.
Extra blankets available.

Tours:
Wine tours.
Mountain activities.
Termas de Cacheuta.
"""


MEMORY_FILE = "conversations.json"


def load_memory():

    if not os.path.exists(MEMORY_FILE):
        return {}

    with open(MEMORY_FILE, "r", encoding="utf-8") as f:
        return json.load(f)



def save_memory(memory):

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(
            memory,
            f,
            indent=4,
            ensure_ascii=False
        )



def save_message(user, role, text):

    memory = load_memory()

    if user not in memory:
        memory[user] = {
            "status":"AI",
            "messages":[]
        }


    memory[user]["messages"].append(
        {
            "role": role,
            "text": text,
            "time": str(datetime.now())
        }
    )

    save_memory(memory)




def ask_ai(user, question):

    memory = load_memory()

    history = []


    if user in memory:

        for msg in memory[user]["messages"][-10:]:

            history.append(
                {
                    "role": msg["role"],
                    "content": msg["text"]
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


    user = data.get(
        "phone",
        "unknown"
    )


    question = data.get(
        "message",
        ""
    )


    save_message(
        user,
        "user",
        question
    )


    answer = ask_ai(
        user,
        question
    )


    if any(word in question.lower() for word in [
        "human",
        "person",
        "reception",
        "staff"
    ]):

        memory = load_memory()

        memory[user]["status"] = "HUMAN"

        save_memory(memory)



    save_message(
        user,
        "assistant",
        answer
    )



    return jsonify(
        {
            "reply":answer
        }
    )





if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )


    app.run(
        host="0.0.0.0",
        port=port
    )
