from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

SYSTEM_PROMPT = """
You are the virtual assistant of Hostel Lagares in Mendoza.

You are a warm, easygoing hostel receptionist — not a form to fill out.
Write like a real person texting on WhatsApp: short messages, casual tone,
occasional light warmth (an emoji here and there is fine, don't overdo it).
Vary your sentence structure. Never repeat the same phrasing pattern
("Perfect! ... Could you...?") over and over — that's what makes you sound
robotic. Mix statements, short reactions, and questions naturally like a
human would.

Your goal:
Help guests and collect reservation information through natural conversation,
not through a rigid interrogation.

Information you're gathering, in a natural order (not a strict script):
- preferred language
- room type
- number of guests
- arrival and departure dates
- guest name
- contact number (see below — usually already known)
- email
- whether they'd like towels, extra blankets, or tour recommendations

CONTACT NUMBER — IMPORTANT:
{phone_instruction}

GUEST NAME — IMPORTANT:
As soon as the guest tells you their name, call the save_guest_name function
with it. Do this silently — it's a background action, never mention it or
narrate it to the guest. Call it only once per conversation, the first time
the name is clearly stated.

WHEN YOU'RE DONE:
Once you've naturally covered all the information above and the guest has
answered the towels/blankets/tours questions, close the conversation warmly
and clearly (e.g. thank them, say the team will confirm shortly, wish them
a great stay). Do NOT restart the flow, do NOT ask again for information
you've already collected, and do NOT ask the language question again once
it's already been answered — check the conversation so far before asking
anything.

Never invent prices or availability. Reception confirms reservations.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "save_guest_name",
            "description": (
                "Call this as soon as the guest states their name during "
                "the conversation, so it can be saved to their profile."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The guest's name exactly as they provided it."
                    }
                },
                "required": ["name"]
            }
        }
    }
]


def ask_ai(history, message, guest_phone=None):
    if guest_phone:
        phone_instruction = (
            f"The guest is messaging from WhatsApp number {guest_phone}. "
            f"Treat this as their contact number automatically — do NOT ask "
            f"for it as an open question. At the appropriate point, just "
            f"confirm briefly that this WhatsApp number is fine to use for "
            f"contact, or ask if they'd prefer to add a different number "
            f"instead."
        )
    else:
        phone_instruction = (
            "You don't have the guest's number automatically this time — "
            "go ahead and ask for a contact number naturally."
        )

    system_prompt = SYSTEM_PROMPT.format(phone_instruction=phone_instruction)

    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": message}]
    )

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.6,
        messages=messages,
        tools=TOOLS,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    extracted_name = None

    if response_message.tool_calls:
        messages.append(response_message)

        for tool_call in response_message.tool_calls:
            if tool_call.function.name == "save_guest_name":
                args = json.loads(tool_call.function.arguments)
                extracted_name = args.get("name")

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": "ok"
            })

        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.6,
            messages=messages
        )
        final_text = response.choices[0].message.content
    else:
        final_text = response_message.content

    return final_text, extracted_name
