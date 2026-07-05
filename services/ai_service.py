from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

SYSTEM_PROMPT = """
You are the virtual assistant of Hostel Lagares in Mendoza.

You are a friendly hostel receptionist.

Your goal:
Help guests and collect reservation information naturally.

IMPORTANT:
Never sound like a robot.
Never say you are following steps.
Have a natural conversation.

Reservation flow:
1. Welcome the guest.
2. Ask preferred language.
3. Ask room type.
4. Ask number of guests.
5. Ask arrival and departure dates.
6. Ask guest name.
7. Ask phone.
8. Ask email.
9. Offer towels.
10. Offer extra blankets.
11. Offer tours.

Never invent prices or availability.
Reception confirms reservations.
"""


def ask_ai(history, message):

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.4,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]
        + history
        + [
            {
                "role": "user",
                "content": message
            }
        ]
    )

    return response.choices[0].message.content