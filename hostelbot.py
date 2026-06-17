from flask import Flask, request, jsonify
from openai import OpenAI
import os

app = Flask(__name__)

client = OpenAI(
api_key=os.getenv("OPENAI_API_KEY")
)

contexto = """
You are the virtual assistant of Hostel Lagares in Mendoza.

Rules:
- Answer in the guest language.
- Be friendly and helpful.
- Never invent availability.
- Never confirm reservations.
- Reception confirms everything.

Information:

Check-in: 13:00
Check-out: 10:00

Breakfast included:
08:00 - 10:00

WiFi available.
Shared kitchen.
Laundry available.
Towels available.
Extra blankets available.

Tours:
Wine tours.
Classic tours.
Mountain activities.
Termas de Cacheuta.
Adventure activities.
"""


def save_lead(text):

with open(
"leads.txt",
"a",
encoding="utf-8"
) as file:

file.write(text + "\n")


def ask_ai(question):

response = client.chat.completions.create(

model="gpt-4.1-mini",

temperature=0.3,

messages=[
{
"role": "system",
"content": contexto
},
{
"role": "user",
"content": question
}
]
)

return response.choices[0].message.content


@app.route("/")
def home():
return "HostelBot online"


@app.route("/message", methods=["POST"])
def message():

data = request.json

question = data.get(
"message",
""
)

if not question:
return jsonify(
{"error": "No message"}
)


answer = ask_ai(question)


return jsonify(
{
"reply": answer
}
)


if __name__ == "__main__":

app.run(
host="0.0.0.0",
port=int(
os.environ.get(
"PORT",
10000
)
)
)
