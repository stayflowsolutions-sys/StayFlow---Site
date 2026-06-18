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
You are StayFlow AI assistant for Hostel Lagares in Mendoza.

You are a reservation assistant.

LANGUAGE:
Detect the guest language and answer in Spanish, English or Portuguese.

BOOKING FLOW:
If guest wants to reserve, guide naturally:

First ask:
- arrival date
- departure date

Then ask:
- number of guests

Then offer room options:

1 - Private Room
2 - Shared Room

Do not invent prices or availability.

After that collect:
- guest name

Save useful reservation information.

SERVICES:
Mention when relevant:

- WiFi
- Shared kitchen
- Laundry
- Towels available
- Extra blankets available

TOURS:
Offer:
- Wine tours
- Mountain activities
- Termas de Cacheuta
- Local excursions

If guest asks about tours:
ask what activity they prefer.

RULES:
Be friendly.
Do not send to reception unless guest asks for a human.
Reception confirms final availability.

Check in: 13:00
Check out: 10:00
Breakfast: 08:00 - 10:00
"""


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}

    with open(MEMORY_FILE,"r",encoding="utf-8") as f:
        return json.load(f)


def save_memory(data):
    with open(MEMORY_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,indent=4,ensure_ascii=False)


def save_message(phone, role, text):

    memory = load_memory()

    if phone not in memory:
        memory[phone] = {"messages":[]}

    memory[phone]["messages"].append(
        {
            "role":role,
            "text":text,
            "time":str(datetime.now())
        }
    )

    save_memory(memory)


def save_lead(phone,text):

    with open(LEADS_FILE,"a",encoding="utf-8") as f:
        f.write(phone+" | "+text+"\n")


def ask_ai(phone,question):

    memory = load_memory()

    history=[]

    if phone in memory:
        for m in memory[phone]["messages"][-10:]:
            history.append(
                {
                    "role":m["role"],
                    "content":m["text"]
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
        ]+history+[
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


@app.route("/message",methods=["POST"])
def message():

    data=request.json

    phone=data.get("phone","unknown")
    text=data.get("message","")

    save_message(phone,"user",text)
    save_lead(phone,text)

    answer=ask_ai(phone,text)

    save_message(phone,"assistant",answer)

    return jsonify(
        {
            "reply":answer
        }
    )


if __name__=="__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )
