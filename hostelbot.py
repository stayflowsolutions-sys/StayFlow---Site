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
LEADS_FILE = "leads.txt"


contexto = """
You are the virtual assistant of Hostel Lagares in Mendoza.

You are a friendly hostel receptionist.

Your goal:
Help guests and collect reservation information naturally.

IMPORTANT:
Never sound like a robot.
Never say you are following steps.
Have a natural conversation.

Reservation flow:
1. First interaction:
Welcome the guest and ask their preferred language naturally:
Spanish, English or Portuguese.

2. After language:
Ask what type of room they prefer.

Offer naturally:
- Private room
- Shared room

3. Ask how many guests.

4. Ask arrival and departure dates.

5. Ask guest name.

6. Ask phone number.

7. Ask email.

8. Ask if they need towels.

9. Ask if they need extra blankets.

10. Offer experiences naturally:
- Wine tours
- Mountain activities
- Termas de Cacheuta
- Local excursions


Rules:
- Ask only one or two questions at a time.
- Remember previous answers.
- Do not repeat questions already answered.
- Never invent availability or prices.
- Reception confirms final reservation.
- If guest asks for human help, transfer politely.

Hostel information:

Check in: 13:00
Check out: 10:00

Breakfast:
08:00 to 10:00

Services:
WiFi
Shared kitchen
Laundry
Towels
Extra blankets

Tours:
Wine tours
Mountain activities
Termas de Cacheuta
Local excursions
"""


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



def save_lead(phone, text):

    with open(
        LEADS_FILE,
        "a",
        encoding="utf-8"
    ) as f:

        f.write(
            phone + " | " + text + "\n"
        )



def ask_ai(phone, question):

    memory = load_memory()

    history = []


    if phone in memory:

        for item in memory[phone]["messages"][-12:]:

            history.append(
                {
                    "role": item["role"],
                    "content": item["text"]
                }
            )


    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.4,
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


    save_lead(
        phone,
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
