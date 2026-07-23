from openai import OpenAI
from dotenv import load_dotenv
import os
import json
import datetime

from database import (
    attempt_extend_reservation,
    flag_extension_for_approval,
    create_reservation_from_chat,
    list_room_categories,
    find_available_beds,
    get_offerings_for_chat,
    save_guest_date_of_birth,
    save_guest_nationality,
)

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

SYSTEM_PROMPT = """
Today's date is {today_date}. Use this as your reference for anything
relative ("tomorrow", "next week", "2 more nights", etc.) — always convert
relative dates to actual YYYY-MM-DD dates based on it, never guess.

LANGUAGE — IMPORTANT, DO NOT SWITCH MID-CONVERSATION:
{language_instruction}

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
- room category (see PRICING below)
- number of guests
- arrival and departure dates
- guest name
- contact number (see below — usually already known)
- email
- whether they'd like towels, extra blankets, or tour recommendations

AFTER THE RESERVATION IS CREATED — HOSTEL REGISTRATION (IMPORTANT):
The moment create_reservation succeeds, treat that as the trigger to start
the hostel's legal guest registration — this is a required checklist, not
optional small talk, even though you still ask for it warmly and one or two
items per message (never dump the whole list in one message). Go through
these, in order, skipping anything you've already collected earlier in the
conversation:
1. Full legal name, as it appears on their ID (confirm it matches what
   they already told you, or ask if unsure).
2. Contact number (usually already known from WhatsApp — just confirm it's
   fine to use, per the CONTACT NUMBER section below).
3. Email address.
4. Nationality. As soon as the guest states it, call save_guest_nationality
   with it.
5. Date of birth. As soon as the guest states it, call
   save_guest_date_of_birth with it.
6. A photo of their ID/passport. Just ask them to send it — you don't need
   to do anything else, the system automatically receives and confirms the
   photo on its own; don't ask again once you've asked once, and don't
   worry if you can't tell whether it arrived — a separate confirmation
   message is sent directly to the guest when it's received.
Do not consider the conversation wrapped up (see WHEN YOU'RE DONE below)
until you've gone through all six of these at least once.

PRICING AND ROOM OPTIONS — IMPORTANT:
Never invent a price or say a room type is available without checking first.
As soon as the guest asks about room types, prices, or what's included, call
get_room_options to see the real categories this hostel actually has
configured (name, price per night, capacity, description/what's included).
Quote the real price_per_night and multiply by the number of nights to give
the total for their stay. NEVER count nights yourself by subtracting dates in
your head — that kind of date arithmetic is exactly where mistakes happen.
The moment you know both checkin_date and checkout_date, call
calculate_nights to get the exact number, then multiply that exact number by
price_per_night. If a category has no price configured yet, say pricing
needs to be confirmed by the team instead of guessing a number.
NEVER rescale or reformat the number — if price_per_night is 20000, say
"20.000" (or "20000"), never "200" or "R$200". Don't guess a currency
symbol either; just state the plain number, since the hostel's actual
currency isn't ARS/BRL/USD-labeled in the data — say "20.000 por noite"
without inventing a symbol, unless the guest tells you their currency.
If the guest asks about extras (towel, blanket, etc.), call get_addons and
quote the real price from there — never invent an extra's price either.

CHOOSING A SPECIFIC BED — IMPORTANT, NEVER SKIP THIS:
Once the guest has picked a room category and you know their dates, call
get_available_beds with that category name and the dates to see which
specific beds are actually free for that period. If it's a shared/dorm-style
category with bunk beds, mention the options naturally (e.g. "tenho uma cama
de cima e uma de baixo livres nessa data, tem preferência?") — like choosing
a window or aisle seat on a bus site. Once the guest states a preference
(top/bottom, or a specific bed), match it to one of the beds you just fetched
and use that bed's id when creating the reservation. A bed_id is REQUIRED to
book any category that has beds cataloged — create_reservation will refuse
without one, on purpose, so two guests can never accidentally get booked into
the same physical bed. If get_available_beds comes back empty, that means
every bed for that category is taken for those dates — tell the guest
honestly and offer to check other dates, don't force it.

IF THE CATEGORY HAS NO BEDS CATALOGED AT ALL: some categories (often private
rooms) may not have any individual beds set up yet in the system. In that
case create_reservation will error out on purpose, saying it can't confirm
availability automatically — when that happens, tell the guest their request
was received and the team will reach out shortly to confirm manually (the
system already registered it for the team). Never try to force it through a
second way.

RIGHT BEFORE BOOKING — IMPORTANT (do not skip):
Availability can change between messages (another guest may book in the
meantime), so immediately before calling create_reservation with a bed_id,
call get_available_beds ONE more time for that same category and dates to
confirm the bed is still on the list. Only use a bed_id you just confirmed
is still free in that fresh call — never reuse an id from earlier in the
conversation without re-checking it first.

category_name vs room name — DO NOT MIX THESE UP: category_name is the
room CATEGORY (e.g. "Compartilhado", "Privado" — from get_room_options),
never a specific room's number/name (e.g. "Dorm 1", which get_available_beds
returns per-bed as room_name, just for display). Every call to
get_available_beds in the same conversation must reuse the exact same
category_name string — copy it from get_room_options or from your own
previous call, never from a bed's room_name field.

CREATING THE RESERVATION — IMPORTANT:
Once you have the guest's name, the room category, and both dates, call
create_reservation (include the bed_id if one was chosen/resolved above).
This creates the reservation as 'pending' automatically — you don't need
anyone's approval to call it, but always tell the guest their request was
received and the team will confirm shortly, never that it's 100% guaranteed
yet. Call it only once per stay request — if the guest already confirmed
these same dates and category earlier in the conversation, don't call it
again, just reference the existing reservation.

DON'T DELAY THE BOOKING — IMPORTANT: name, room category, and both dates are
the ONLY things required to call create_reservation. The moment you have
those three, call it in that same reply — do not wait until you've also
collected email, towels/blankets preferences, or anything else first. Those
extra details can keep being collected naturally in the messages after the
reservation is already created.

IF create_reservation RETURNS AN ERROR — IMPORTANT:
Never guess why it failed and never tell the guest something specific was
"just taken" unless you actually just confirmed that with a fresh
get_available_beds call. If the tool errors, call get_available_beds again
right away, see what's actually still free now, and offer that to the guest
based on the real fresh result — don't improvise an explanation.

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

Never invent prices or availability — always check with the tools above.
"""

SAVE_GUEST_LANGUAGE_TOOL = {
    "type": "function",
    "function": {
        "name": "save_guest_language",
        "description": (
            "Call this once you've determined the guest's established "
            "language for this conversation — either right after their "
            "first message (inferred from what they wrote), or whenever "
            "the guest explicitly asks to switch to a different language. "
            "Do NOT call this again just because a message happens to "
            "contain a foreign word or emoji — only when the language they "
            "are actually conversing in changes or is first established."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "language": {
                    "type": "string",
                    "description": (
                        "Short language code for the language the guest is "
                        "conversing in, e.g. 'pt', 'en', 'es', 'fr', 'de'."
                    )
                }
            },
            "required": ["language"]
        }
    }
}

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
    },
    {
        "type": "function",
        "function": {
            "name": "get_room_options",
            "description": (
                "Returns the hostel's real room categories, with price per "
                "night, capacity and description (e.g. what's included). "
                "Always call this before quoting a price or describing room "
                "options to a guest."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_available_beds",
            "description": (
                "Returns which specific beds are actually free for a room "
                "category in a given date range, so the guest can pick one "
                "(e.g. top or bottom bunk)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category_name": {"type": "string"},
                    "checkin_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "checkout_date": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["category_name", "checkin_date", "checkout_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_addons",
            "description": "Returns real extras (towel, blanket, tours, etc.) with their actual prices.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_nights",
            "description": (
                "Calculates the exact number of nights between a check-in and "
                "check-out date. ALWAYS call this before telling the guest how "
                "many nights they're booking or quoting a total price — never "
                "count the days yourself, that kind of date arithmetic is "
                "exactly where mistakes happen."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "checkin_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "checkout_date": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["checkin_date", "checkout_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_reservation",
            "description": (
                "Creates the guest's reservation as 'pending' once you have "
                "their name, room category, and both dates. Include bed_id if "
                "a specific bed was chosen via get_available_beds. Call this "
                "only once per stay request."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "guest_name": {"type": "string"},
                    "category_name": {"type": "string"},
                    "checkin_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "checkout_date": {"type": "string", "description": "YYYY-MM-DD"},
                    "bed_id": {"type": "integer", "description": "Required if the category has any beds cataloged - specific bed chosen via get_available_beds. Omit only if the category has no beds cataloged at all (the call will then explain what to tell the guest)."}
                },
                "required": ["guest_name", "category_name", "checkin_date", "checkout_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_guest_date_of_birth",
            "description": (
                "Call this as soon as the guest states their date of birth "
                "(part of hostel registration, asked after the reservation "
                "is created), so it can be saved to their profile."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date_of_birth": {"type": "string", "description": "YYYY-MM-DD"}
                },
                "required": ["date_of_birth"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_guest_nationality",
            "description": (
                "Call this as soon as the guest states their nationality "
                "(part of hostel registration, asked after the reservation "
                "is created), so it can be saved to their profile."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "nationality": {"type": "string"}
                },
                "required": ["nationality"]
            }
        }
    }
]

MAX_TOOL_ROUNDS = 4


def ask_ai(history, message, guest_phone=None, hostel_id=None, guest_language=None):
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

    if guest_language:
        language_instruction = (
            f"This guest's established language for this conversation is "
            f"'{guest_language}'. ALWAYS reply in this language for the rest "
            f"of the conversation. People often mix in a foreign word, "
            f"emoji, or a place name — that is NOT a request to switch "
            f"language, ignore it. Only switch if the guest EXPLICITLY asks "
            f"to continue in a different language; if that happens, switch "
            f"and call save_guest_language with the new one."
        )
    else:
        language_instruction = (
            "You don't know this guest's language yet. Infer it from the "
            "language of their message below and call save_guest_language "
            "with it right away — then keep replying in that same language "
            "for the rest of the conversation, never switching on your own."
        )

    system_prompt = SYSTEM_PROMPT.format(
        phone_instruction=phone_instruction,
        language_instruction=language_instruction,
        today_date=datetime.date.today().isoformat()
    )

    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": message}]
    )

    # As ferramentas de reserva/preco/cama precisam de hostel_id+telefone
    # reais pra saber de qual hospede/hostel se trata - sem isso (ex:
    # endpoint de teste manual sem hostel_id), elas nem aparecem pro modelo.
    tools = [SAVE_GUEST_NAME_TOOL, SAVE_GUEST_LANGUAGE_TOOL]
    if hostel_id and guest_phone:
        tools = tools + RESERVATION_TOOLS

    extracted_name = None
    extracted_language = None
    final_text = None

    for _ in range(MAX_TOOL_ROUNDS):
        kwargs = dict(model="gpt-4.1-mini", temperature=0.6, messages=messages)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = client.chat.completions.create(**kwargs)
        response_message = response.choices[0].message

        if not response_message.tool_calls:
            final_text = response_message.content
            break

        messages.append(response_message)

        for tool_call in response_message.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")
            tool_content = "ok"

            if name == "save_guest_name":
                extracted_name = args.get("name")
            elif name == "save_guest_language":
                extracted_language = args.get("language")
            elif name == "calculate_nights":
                try:
                    nights = (
                        datetime.date.fromisoformat(args.get("checkout_date"))
                        - datetime.date.fromisoformat(args.get("checkin_date"))
                    ).days
                    tool_content = json.dumps({"nights": nights}, ensure_ascii=False)
                except (ValueError, TypeError):
                    tool_content = json.dumps({"error": "Datas invalidas."}, ensure_ascii=False)
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
            elif name == "get_room_options":
                try:
                    result = list_room_categories(hostel_id)
                    tool_content = json.dumps(result, ensure_ascii=False)
                except Exception as error:
                    tool_content = json.dumps({"error": "Erro ao buscar modalidades."}, ensure_ascii=False)
            elif name == "get_available_beds":
                try:
                    result = find_available_beds(
                        hostel_id, args.get("category_name"),
                        args.get("checkin_date"), args.get("checkout_date")
                    )
                    tool_content = json.dumps(result, ensure_ascii=False)
                except Exception as error:
                    tool_content = json.dumps({"error": "Erro ao buscar camas disponíveis."}, ensure_ascii=False)
            elif name == "get_addons":
                try:
                    result = get_offerings_for_chat(hostel_id)
                    tool_content = json.dumps(result, ensure_ascii=False)
                except Exception as error:
                    tool_content = json.dumps({"error": "Erro ao buscar extras."}, ensure_ascii=False)
            elif name == "create_reservation":
                try:
                    result = create_reservation_from_chat(
                        hostel_id, guest_phone,
                        args.get("guest_name"), args.get("category_name"),
                        args.get("checkin_date"), args.get("checkout_date"),
                        bed_id=args.get("bed_id")
                    )
                    tool_content = json.dumps(result, ensure_ascii=False)
                except ValueError as error:
                    tool_content = json.dumps({"error": str(error)}, ensure_ascii=False)
            elif name == "save_guest_date_of_birth":
                save_guest_date_of_birth(hostel_id, guest_phone, args.get("date_of_birth"))
            elif name == "save_guest_nationality":
                save_guest_nationality(hostel_id, guest_phone, args.get("nationality"))

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_content
            })

    if final_text is None:
        fallback_by_language = {
            "pt": "Deixa eu confirmar isso com a equipe e já te retorno, tá bom?",
            "en": "Let me confirm that with the team and I'll get back to you shortly.",
            "es": "Déjame confirmar eso con el equipo y te aviso enseguida.",
            "fr": "Laissez-moi confirmer ça avec l'équipe, je reviens vers vous très vite.",
            "de": "Lassen Sie mich das mit dem Team klären, ich melde mich gleich bei Ihnen.",
        }
        final_text = fallback_by_language.get(
            guest_language or extracted_language, fallback_by_language["pt"]
        )

    return final_text, extracted_name, extracted_language
