from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import datetime

from database import attempt_extend_reservation, flag_extension_for_approval

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

SYSTEM_PROMPT = """
Today's date is {today_date}. Use this as your reference for anything
relative ("tomorrow", "next week", "2 more nights", etc.) — always convert
relative dates to actual YYYY-MM-DD dates based on it, never guess.

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

EXTENDING A STAY — IMPORTANT:
If the guest already has a reservation and asks to extend their stay for
more nights in the SAME room, at the SAME rate (a pure date change, nothing
else different), call extend_reservation with the new checkout date. This
executes automatically — you don't need extra approval from anyone, just
confirm it warmly to the guest afterward based on the real result you get back.
If instead the guest wants a different room, a discount, or any condition
that isn't simply "more nights, same everything", do NOT call
extend_reservation — call flag_extension_for_approval instead, summarizing
what they asked for, and tell the guest the team will confirm shortly
(reception needs to review that one manually).

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

SAVE_GUEST_NAME_TOOL = {
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

RESERVATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "extend_reservation",
            "description": (
                "Extends the guest's current reservation to a new checkout date, "
                "keeping the SAME room and SAME nightly rate. Only use this for a "
                "pure date extension — if the guest wants a different room, a "
                "discount, or any other different condition, use "
                "flag_extension_for_approval instead."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "new_checkout_date": {
                        "type": "string",
                        "description": "New checkout date, format YYYY-MM-DD"
                    }
                },
                "required": ["new_checkout_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "flag_extension_for_approval",
            "description": (
                "Registers that the guest wants to extend their stay under "
                "different conditions (different room, discount, etc.) so the "
                "hostel team can review it manually. Use this instead of "
                "extend_reservation whenever the request isn't simply "
                "'same everything, more nights'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {
                        "type": "string",
                        "description": "Short summary of what the guest asked for, in Portuguese, for the team to read."
                    }
                },
                "required": ["note"]
            }
        }
    }
]


def ask_ai(history, message, guest_phone=None, hostel_id=None):
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

    system_prompt = SYSTEM_PROMPT.format(
        phone_instruction=phone_instruction,
        today_date=datetime.date.today().isoformat()
    )

    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": message}]
    )

    # extend_reservation/flag_extension_for_approval precisam de
    # hostel_id+telefone reais pra saber de qual hospede/reserva se
    # trata - sem isso (ex: endpoint de teste manual sem hostel_id),
    # essas ferramentas nem aparecem pro modelo.
    tools = [SAVE_GUEST_NAME_TOOL]
    if hostel_id and guest_phone:
        tools = tools + RESERVATION_TOOLS

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        temperature=0.6,
        messages=messages,
        tools=tools,
        tool_choice="auto"
    )

    response_message = response.choices[0].message
    extracted_name = None

    if response_message.tool_calls:
        messages.append(response_message)

        for tool_call in response_message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")
            tool_content = "ok"

            if name == "save_guest_name":
                extracted_name = args.get("name")
            elif name == "extend_reservation":
                try:
                    result = attempt_extend_reservation(
                        hostel_id, guest_phone, args.get("new_checkout_date")
                    )
                    tool_content = json.dumps(result, ensure_ascii=False)
                except ValueError as error:
                    tool_content = json.dumps({"error": str(error)}, ensure_ascii=False)
            elif name == "flag_extension_for_approval":
                try:
                    result = flag_extension_for_approval(
                        hostel_id, guest_phone, args.get("note", "")
                    )
                    tool_content = json.dumps(result, ensure_ascii=False)
                except ValueError as error:
                    tool_content = json.dumps({"error": str(error)}, ensure_ascii=False)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_content
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
