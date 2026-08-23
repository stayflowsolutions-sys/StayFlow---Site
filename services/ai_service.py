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
    save_guest_date_of_birth_by_id,
    save_guest_nationality_by_id,
    get_menu_items,
    find_menu_item_by_name,
    create_kitchen_order,
    create_maintenance_ticket,
    create_security_incident,
    get_active_vehicle_for_guest,
    request_valet,
    notify_on_duty_staff_for_ticket,
    list_portfolio_items,
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

You are the virtual assistant of {hostel_name}, a {hostel_type_label}.

You are a warm, attentive receptionist — not a form to fill out. Match your
tone to the property type stated above: relaxed and casual for a hostel,
more polished and professional for a hotel or resort, but always
personable, never robotic.
Write like a real person texting on WhatsApp: short messages, natural tone,
occasional light warmth (an emoji here and there is fine, don't overdo it).
Vary your sentence structure. Never repeat the same phrasing pattern
("Perfect! ... Could you...?") over and over — that's what makes you sound
robotic. Mix statements, short reactions, and questions naturally like a
human would.

{alt_channel_instruction}

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

AFTER THE RESERVATION IS CREATED — GUEST REGISTRATION (IMPORTANT):
The moment create_reservation succeeds, treat that as the trigger to start
the property's legal guest registration — this is a required checklist, not
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
get_room_options to see the real categories this property actually has
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
symbol either; just state the plain number, since the property's actual
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
{name_instruction}

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

DURING-STAY REQUESTS — ROOM SERVICE, MAINTENANCE, SECURITY, VALET:
These are separate from the reservation flow above and can come up any time
in the conversation, from a first-time guest or a returning one:
- Food/drink order (room service or restaurant): call get_menu first to see
  real items and prices, confirm what the guest wants and their room/table,
  then call create_kitchen_order. Runs automatically, no approval needed.
- A problem with the room/property (broken shower, AC, etc.): call
  report_maintenance_issue. Ask how urgent it feels to the guest, but you
  still set base_urgency yourself from the fixed list — see the tool's own
  description for how to judge it.
- Anything safety-related (suspicious activity, feeling unsafe, a lost/
  stolen item): call report_security_concern. If it sounds like an active
  emergency, also tell the guest to contact the front desk or local
  emergency services directly — don't treat chat as the only channel for
  something time-critical.
- Asking for their parked car: call request_valet (no arguments needed, it
  resolves the guest's vehicle automatically). If it errors, tell the guest
  to check with the front desk instead of retrying.
For all four, always tell the guest their request was received and the
right team has been notified — never leave it unacknowledged, and never
invent an ETA you don't actually have.

WHEN YOU'RE DONE:
Once you've naturally covered all the information above and the guest has
answered the towels/blankets/tours questions, close the conversation warmly
and clearly (e.g. thank them, say the team will confirm shortly, wish them
a great stay). Do NOT restart the flow, do NOT ask again for information
you've already collected, and do NOT ask the language question again once
it's already been answered — check the conversation so far before asking
anything.

Never invent prices or availability — always check with the tools above.
{custom_instructions_section}
"""

# Prompt separado pra conta de agencia parceira (turismo/aluguel de
# carro/bike/equipamento) - o SYSTEM_PROMPT acima e inteiro construido
# em torno de reserva de quarto/check-in fisico (quartos, camas,
# cadastro legal de hospede com foto de documento), que nao existe pra
# uma agencia. Reaproveitar aquele prompt pra agencia faria a IA se
# apresentar como "hospitality property" e tentar pedir foto de
# passaporte de um cliente que so quer saber o preco de um passeio -
# por isso um prompt e um conjunto de ferramentas proprios, no mesmo
# tom/estilo do de hospedagem, mas girando em torno do portfolio da
# agencia (ver AGENCY_TOOLS) em vez de quartos.
_AGENCY_PROMPT_SKELETON = """
Today's date is {{today_date}}. Use this as your reference for anything
relative ("tomorrow", "next week", "in 3 days", etc.) — always convert
relative dates to actual YYYY-MM-DD dates based on it, never guess.

LANGUAGE — IMPORTANT, DO NOT SWITCH MID-CONVERSATION:
{{language_instruction}}

{business_description}

You are a warm, attentive salesperson — not a form to fill out. Friendly
and enthusiastic about what {{hostel_name}} offers, but always personable,
never robotic.
Write like a real person texting on WhatsApp: short messages, natural tone,
occasional light warmth (an emoji here and there is fine, don't overdo it).
Vary your sentence structure. Never repeat the same phrasing pattern over
and over — that's what makes you sound robotic. Mix statements, short
reactions, and questions naturally like a human would.

{{alt_channel_instruction}}

Your goal:
Help customers discover what {{hostel_name}} offers and gather their interest
through natural conversation, not a rigid interrogation.

Information you're gathering, in a natural order (not a strict script):
- preferred language
- what they're interested in (see OFFERINGS below)
{gathering_details}
- contact number (see below — usually already known)
- customer's name

OFFERINGS — IMPORTANT:
Never invent an item, price, or description. As soon as the customer asks
what you offer, or about prices, call get_offerings to see the real {offerings_noun}
this business actually has listed (name, description, category, price).
Quote the real price exactly as returned. NEVER rescale or reformat the
number — if price is 20000, say "20.000" (or "20000"), never "200". Don't
guess a currency symbol either; just state the plain number, since the
business's actual currency isn't ARS/BRL/USD-labeled in the data — unless
the customer tells you their currency. If an item has no fixed price
(price_type is "variable"), tell the customer the exact value will be
confirmed by the team — never guess a number for it.
If get_offerings comes back empty, tell the customer nothing is listed
yet and that the team will follow up directly to help them.

WHEN THE CUSTOMER IS INTERESTED — IMPORTANT:
You do not close the sale or take payment yourself. {handoff_instruction}
Never say it's 100% confirmed yet, and never invent an ETA you don't
actually have.

CONTACT NUMBER — IMPORTANT:
{{phone_instruction}}

CUSTOMER NAME — IMPORTANT:
{{name_instruction}}

WHEN YOU'RE DONE:
Once you've naturally covered what the customer is interested in and have
their contact info, close the conversation warmly and clearly (thank them,
say the team will follow up shortly). Do NOT restart the flow, do NOT ask
again for information you've already collected, and do NOT ask the
language question again once it's already been answered — check the
conversation so far before asking anything.

Never invent prices or offerings — always check with get_offerings.
{{custom_instructions_section}}
"""


def _build_agency_prompt(business_description, gathering_details, offerings_noun, handoff_instruction):
    return _AGENCY_PROMPT_SKELETON.format(
        business_description=business_description,
        gathering_details=gathering_details,
        offerings_noun=offerings_noun,
        handoff_instruction=handoff_instruction,
    )


# Um prompt COMPLETO e separado por categoria de agencia, nao um texto
# generico com um rotulo trocado - o "gathering_details" e a descricao
# do negocio sao especificos de cada vertical de verdade (ex: imobiliaria
# fala de imovel/visita/bairro, estetica automotiva fala de veiculo/
# servico/horario). A espinha dorsal (nunca inventar preco, nunca
# fechar a venda sozinho, coletar nome/contato) e deliberadamente
# identica em todas - sao garantias do produto, nao "sabor" de nicho.
AGENCY_CATEGORY_PROMPTS = {
    "turismo": _build_agency_prompt(
        "You are the virtual assistant of {hostel_name}, a tourism agency offering tours and travel experiences.",
        "- which tour/experience they're interested in\n"
        "- dates or timeframe, and number of people\n"
        "- pickup location or meeting point, if relevant",
        "tours/experiences",
        "Once the customer has picked a tour or experience and you have their "
        "name and contact number, tell them warmly that the team will follow "
        "up shortly to confirm availability and payment.",
    ),
    "aluguel_carro": _build_agency_prompt(
        "You are the virtual assistant of {hostel_name}, a car rental company.",
        "- what type/category of vehicle they need\n"
        "- pickup and return dates\n"
        "- pickup location, and driver's age if they mention it",
        "vehicles",
        "Once the customer has picked a vehicle and you have their name and "
        "contact number, tell them warmly that the team will follow up "
        "shortly to confirm availability, documents needed, and payment.",
    ),
    "aluguel_bike": _build_agency_prompt(
        "You are the virtual assistant of {hostel_name}, a bike rental business.",
        "- what type of bike they want\n"
        "- rental period (hours or days)\n"
        "- pickup/return location, and group size if more than one person",
        "bikes",
        "Once the customer has picked a bike and rental period and you have "
        "their name and contact number, tell them warmly that the team will "
        "follow up shortly to confirm availability and payment.",
    ),
    "aluguel_equipamentos": _build_agency_prompt(
        "You are the virtual assistant of {hostel_name}, an equipment rental business.",
        "- what equipment they need\n"
        "- rental period and quantity\n"
        "- whether they need pickup or delivery",
        "equipment items",
        "Once the customer has picked the equipment and you have their name "
        "and contact number, tell them warmly that the team will follow up "
        "shortly to confirm availability and payment.",
    ),
    "imobiliaria": _build_agency_prompt(
        "You are the virtual assistant of {hostel_name}, a real estate agency.",
        "- whether they want to buy or rent\n"
        "- type of property (house, apartment, commercial), neighborhood/region, "
        "and number of bedrooms if relevant\n"
        "- budget range",
        "properties",
        "Once the customer has shown real interest in a property and you have "
        "their name and contact number, tell them warmly that the team will "
        "follow up shortly to schedule a viewing (visita) and share full details.",
    ),
    # "automotivo" e "comercio" sao GRUPOS (a variedade real dentro deles -
    # estetica/pelicula/mecanica/funilaria e pintura/eletrica/borracharia/
    # auto pecas, ou as "muitas" categorias de comercio - e grande demais
    # pra virar prompt separado por tipo). {agency_subcategory_line} entra
    # preenchido dinamicamente em tempo real (nao faz parte do dict
    # estatico) com o hostels.agency_subcategory de verdade daquela conta,
    # mesmo espirito do hostel_type_label usado no SYSTEM_PROMPT normal.
    "automotivo": _build_agency_prompt(
        "You are the virtual assistant of {hostel_name}, an automotive shop{agency_subcategory_line}.",
        "- their vehicle's make and model\n"
        "- which service they want (whatever this business actually lists - "
        "wash, polish, ceramic coating, window tinting, mechanical repair, "
        "bodywork/paint, electrical, tires, parts, etc.)\n"
        "- preferred day/time to bring the vehicle in",
        "services",
        "Once the customer has picked a service and you have their name and "
        "contact number, tell them warmly that the team will follow up "
        "shortly to confirm the appointment time and price.",
    ),
    "comercio": _build_agency_prompt(
        "You are the virtual assistant of {hostel_name}, a store{agency_subcategory_line}.",
        "- which product/item they're interested in, and quantity\n"
        "- whether they need something custom made (design, size, etc.), if "
        "relevant to what this business sells\n"
        "- where they saw it, if they mention a specific channel (Mercado "
        "Livre, Instagram, etc.) — don't ask this directly, just note it if "
        "they bring it up — and their shipping location/city if relevant",
        "products",
        "Once the customer has picked something and you have their name and "
        "contact number, tell them warmly that the team will follow up "
        "shortly to confirm stock/details, price and delivery.",
    ),
    "servico_generico": _build_agency_prompt(
        "You are the virtual assistant of {hostel_name}, a business offering products and/or services.",
        "- relevant details for what they picked (only ask what's actually "
        "relevant, don't force every question on every customer)",
        "items",
        "Once the customer has picked something and you have their name and "
        "contact number, tell them warmly that the team will follow up "
        "shortly to confirm details, availability and payment.",
    ),
}

# Prompt separado pro numero comercial da propria StayFlow (o do botao
# flutuante do site/redes sociais) - usado so quando hostels.ai_persona
# = 'software' pra esse hostel_id (ver database.py). Sem isso, esse
# numero herdaria o SYSTEM_PROMPT normal e responderia como se fosse a
# recepcao de um hotel de verdade pra quem escreve vindo do site — o
# numero real do software precisa se apresentar como o proprio
# vendedor/assistente da StayFlow, nunca fingir ser uma hospedagem.
SOFTWARE_SYSTEM_PROMPT = """
Today's date is {today_date}. Use this as your reference for anything
relative ("this weekend", "next month", etc.) — always convert relative
dates to actual YYYY-MM-DD dates based on it, never guess.

LANGUAGE — IMPORTANT, DO NOT SWITCH MID-CONVERSATION:
{language_instruction}

You are the virtual assistant of StayFlow ITSELF — the software company —
NOT a hotel, hostel, or any lodging property. Whoever is messaging found
this number on the StayFlow website or social media, and is almost always
a hospitality business owner or manager curious about the product. Never
role-play as a hotel receptionist, never pretend to check room
availability or dates, never invent a stay or reservation — that is not
what this number is for.

You are a warm, confident salesperson — knowledgeable about the product,
never pushy, never robotic. Write like a real person texting on WhatsApp:
short messages, natural tone, occasional light warmth (an emoji here and
there is fine, don't overdo it). Vary your sentence structure.

WHAT STAYFLOW IS — use this to answer accurately, never invent features:
StayFlow is an AI-powered management system for hospitality businesses —
hotels, hostels, guesthouses, apart-hotels and similar properties, not
limited to any single type. It:
- Answers guests instantly, 24/7, on WhatsApp, Instagram and Messenger, in
  any language, through an AI assistant.
- Keeps room availability synced across Booking.com, Airbnb, Hostelworld
  and other channels automatically, avoiding overbooking.
- Centralizes the whole operation in one panel: housekeeping,
  maintenance and finance, with tasks assigned to the team and real-time
  tracking.
- Lets a property that already has a system connect its own PMS via
  webhook, or import everything (rooms, guests, reservations) from a
  spreadsheet in minutes.
- The AI also actively sells: it detects opportunities in guest
  conversations and suggests tours, excursions and upgrades — including a
  partner's offering when the property itself doesn't sell what the guest
  wants.

PRICING — IMPORTANT, never invent numbers, use exactly this:
- Starter: US$89/month. Up to 30 rooms, up to 10 team members. AI
  WhatsApp support, centralized chat, reservations, room map, guests,
  Opportunity Center, finance, guest payments via Mercado Pago.
  Operational modules (kitchen, maintenance, front desk, parking) are a
  paid add-on.
- Business (the most chosen plan): US$349/month. Up to 80 rooms, up to
  40 team members. Everything in Starter, plus every operational module
  included (events, kitchen, maintenance, security, parking), plus
  Portfolio and the partner network for agencies.
- Enterprise: US$699/month. Unlimited rooms, unlimited team. Everything
  in Business — meant for chains and multi-property operations.
Every plan includes a 30-day free trial, no credit card required — the
lead can sign up and get straight into the dashboard themselves.

YOUR GOAL:
Understand what kind of property the lead runs (type, roughly how many
rooms) and what's actually slowing them down today (missed messages,
overbooking, scattered spreadsheets, etc.), then show how StayFlow solves
THAT specifically — don't just recite the feature list top to bottom.
Recommend a plan once it's clear which one fits. When they're ready, send
them to sign up themselves at https://stayflowsolutions.com/planos.html —
they can pick a plan and start the free trial immediately, no need to
wait for a human.

If they ask something you're not sure about (custom/negotiated pricing,
deep technical integration details, anything outside what's listed
above), say so honestly and let them know the team will follow up
personally — never invent an answer.

CONTACT NAME — IMPORTANT:
{name_instruction}

WHEN YOU'RE DONE:
Once the lead has a clear picture and either signed up or said they'll
think about it, close warmly — no need to force the sale. Do NOT restart
the pitch from scratch, do NOT repeat the full feature list again once
it's already been covered.

Never invent features, prices, or availability that aren't stated above.
"""

GET_OFFERINGS_TOOL = {
    "type": "function",
    "function": {
        "name": "get_offerings",
        "description": (
            "Returns this business's real portfolio of tours/rentals/services, "
            "with name, description, category and price (or price_type "
            "'variable' when there's no fixed price yet, only 'fixed' has a "
            "usable price). Always call this before quoting a price or "
            "describing what's offered to a customer — never invent an item."
        ),
        "parameters": {"type": "object", "properties": {}}
    }
}

AGENCY_TOOLS = [GET_OFFERINGS_TOOL]

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
                "property team can review it manually. Use this instead of "
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
                "Returns the property's real room categories, with price per "
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
                "(part of guest registration, asked after the reservation "
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
                "(part of guest registration, asked after the reservation "
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

# Ferramentas dos modulos operacionais novos (Sessao 9): cozinha/room
# service, manutencao, seguranca patrimonial e manobrista. Mesmo
# padrao das RESERVATION_TOOLS - ligadas so quando hostel_id+guest_id
# existem (ver `tools = ...` mais abaixo).
OPERATIONAL_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_menu",
            "description": (
                "Returns the property's real food/drink menu items, with "
                "price and category. Always call this before quoting a menu "
                "item or its price to a guest - never invent an item or a "
                "price. If this comes back empty, the property has no menu "
                "configured yet - tell the guest room service isn't "
                "available through chat right now."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_kitchen_order",
            "description": (
                "Places a food/drink order with the kitchen once the guest "
                "has confirmed what they want and their room/table. Only "
                "use item names that came back from get_menu. This is "
                "confirmed automatically - no approval needed - but always "
                "tell the guest their order was received and give a rough "
                "sense that it's being prepared, never promise an exact "
                "delivery time."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Room number or table where the order should be delivered."
                    },
                    "items": {
                        "type": "array",
                        "description": "Items being ordered.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Menu item name, exactly as returned by get_menu."},
                                "quantity": {"type": "integer"},
                                "notes": {"type": "string", "description": "Optional, e.g. 'no onions'."}
                            },
                            "required": ["name", "quantity"]
                        }
                    }
                },
                "required": ["location", "items"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "report_maintenance_issue",
            "description": (
                "Opens a maintenance ticket for a problem the guest reports "
                "(broken shower, AC not working, etc.). Ask the guest how "
                "urgent it feels to them and pass that as guest_reported_urgency "
                "in their own words - but YOU still choose base_urgency from the "
                "fixed list (urgent/high/normal/low) based on the nature of the "
                "problem, weighed against how it compares to what a property "
                "normally deals with (a water leak or no AC in hot weather is "
                "'urgent'/'high' even if the guest downplays it; a burnt-out "
                "lightbulb is 'low' even if the guest calls it urgent). This "
                "runs automatically, no approval needed - always tell the guest "
                "the team has been notified."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Room number or area with the problem."},
                    "description": {"type": "string", "description": "What's wrong, in the guest's own words."},
                    "category": {"type": "string", "description": "Short category, e.g. 'plumbing', 'electrical', 'air conditioning', 'furniture'."},
                    "guest_reported_urgency": {"type": "string", "description": "How urgent the guest says this is, in their own words."},
                    "base_urgency": {"type": "string", "enum": ["urgent", "high", "normal", "low"], "description": "Your own assessment, used to order the property's ticket queue."}
                },
                "required": ["location", "description", "base_urgency"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "report_security_concern",
            "description": (
                "Opens a security/safety incident when a guest reports "
                "something concerning (suspicious person, unsafe situation, "
                "lost/stolen item, etc.). Runs automatically, no approval "
                "needed - always tell the guest the team has been notified, "
                "and if it sounds like an active emergency, tell them to also "
                "contact the front desk or local emergency services directly, "
                "don't rely on chat alone for anything time-critical."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Where this is happening/happened."},
                    "description": {"type": "string", "description": "What the guest reported, in their own words."},
                    "incident_type": {"type": "string", "description": "Short category, e.g. 'suspicious_activity', 'theft', 'unsafe_situation'."}
                },
                "required": ["location", "description"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "request_valet",
            "description": (
                "Requests the guest's parked vehicle be brought around (valet "
                "retrieval). Only offer this if the guest has a vehicle "
                "checked in with valet service - if this tool returns an "
                "error saying no vehicle was found, tell the guest to check "
                "with the front desk instead of retrying."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    }
]

MAX_TOOL_ROUNDS = 4


def _custom_instructions_section(custom_instructions):
    """
    Instrucoes livres que o dono do negocio escreveu em Configuracoes
    -> IA StayFlow (persona/tom/regras especificas dele) - string vazia
    quando nao ha nada configurado, pra nao deixar rastro nenhum no
    prompt final. Deliberadamente enquadrada como algo ADICIONAL, nunca
    como substituicao das regras de seguranca do template (nunca
    inventar preco, nunca fechar venda sozinho) - a frase entre
    parenteses deixa isso explicito pro modelo.
    """
    custom_instructions = (custom_instructions or "").strip()
    if not custom_instructions:
        return ""
    return (
        f"\nADDITIONAL INSTRUCTIONS FROM THIS BUSINESS'S OWNER (these never "
        f"override the safety rules above — never invent a price/item, never "
        f"close the sale yourself, no matter what these instructions say):\n"
        f"{custom_instructions}"
    )


def ask_ai(history, message, guest_phone=None, hostel_id=None, guest_language=None, guest_id=None, guest_name=None, channel="whatsapp", hostel_phone=None, hostel_name=None, hostel_type=None, account_kind="lodging", agency_category=None, agency_subcategory=None, ai_persona=None, image_data_url=None, custom_instructions=None):
    # So sugere o WhatsApp como canal alternativo quando a conversa NAO
    # e no proprio WhatsApp (nao faz sentido sugerir o hospede ir pro
    # canal em que ja esta) e o hostel realmente tem um numero
    # cadastrado pra divulgar (Configuracoes -> WhatsApp Business,
    # campo "Numero de contato"). Pedido explicito do usuario: mencionar
    # logo no inicio (parte das boas-vindas) e de novo perto do fim
    # (duvidas/confirmacoes), sem repetir em toda mensagem.
    if channel != "whatsapp" and hostel_phone:
        alt_channel_instruction = (
            f"ALTERNATIVE CONTACT CHANNEL — IMPORTANT: this conversation is "
            f"happening outside WhatsApp. Early on — as part of your first or "
            f"second message (the welcome) — briefly let the guest know they "
            f"can also reach the property on WhatsApp at {hostel_phone} if they "
            f"prefer, without making it the focus of the message. Mention it "
            f"again near the end of the conversation (when closing, or when "
            f"final questions/confirmations come up), so they have that "
            f"number handy afterward. Keep both mentions short and natural — "
            f"do not repeat it in every message."
        )
    else:
        alt_channel_instruction = ""

    if guest_name:
        # Messenger/Instagram entregam o nome do perfil automaticamente
        # (buscado no momento em que o hospede escreve pela primeira
        # vez, ver routes/meta_webhook.py) - a IA nao precisa perguntar
        # de novo, so usar naturalmente. WhatsApp continua sem isso (o
        # numero de telefone nao revela o nome), pergunta na conversa
        # como sempre - por isso o guest_name so chega aqui preenchido
        # quando ja se sabe de verdade, nunca inventado.
        name_instruction = (
            f"You already know the guest's name: {guest_name}. Do NOT ask "
            f"for it again — just use it naturally in the conversation (e.g. "
            f"greeting them by name). No need to call save_guest_name for a "
            f"name you already have."
        )
    else:
        name_instruction = (
            "As soon as the guest tells you their name, call the "
            "save_guest_name function with it. Do this silently — it's a "
            "background action, never mention it or narrate it to the "
            "guest. Call it only once per conversation, the first time the "
            "name is clearly stated."
        )

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

    is_software = ai_persona == "software"
    is_agency = account_kind == "agency"

    if is_software:
        system_prompt = SOFTWARE_SYSTEM_PROMPT.format(
            language_instruction=language_instruction,
            name_instruction=name_instruction,
            today_date=datetime.date.today().isoformat(),
        )
    elif is_agency:
        # agency_category vem de hostels.agency_category (lista fechada em
        # database.py AGENCY_CATEGORIES) - cada categoria tem seu PROPRIO
        # prompt completo em AGENCY_CATEGORY_PROMPTS (nao um texto generico
        # com um rotulo trocado). Fallback pra servico_generico cobre
        # categoria ausente/nao mapeada.
        template = AGENCY_CATEGORY_PROMPTS.get(
            (agency_category or "").strip().lower(), AGENCY_CATEGORY_PROMPTS["servico_generico"]
        )

        # So "automotivo"/"comercio" usam isso (a variedade dentro deles e
        # grande demais pra virar prompt separado por subtipo) - as outras
        # categorias nao tem {agency_subcategory_line} no texto, entao o
        # kwarg extra e ignorado sem erro (str.format so usa o que existe
        # no template).
        subcategory_clean = (agency_subcategory or "").strip()
        agency_subcategory_line = f" specializing in {subcategory_clean}" if subcategory_clean else ""

        system_prompt = template.format(
            phone_instruction=phone_instruction,
            language_instruction=language_instruction,
            name_instruction=name_instruction,
            alt_channel_instruction=alt_channel_instruction,
            today_date=datetime.date.today().isoformat(),
            hostel_name=hostel_name or "the business",
            agency_subcategory_line=agency_subcategory_line,
            custom_instructions_section=_custom_instructions_section(custom_instructions),
        )
    else:
        # hostel_type e um campo livre (Configuracoes > Empresa aceita "+ Novo
        # tipo..."), entao so usamos os rotulos conhecidos pra deixar o texto
        # natural em ingles ("a hostel", "a hotel") - qualquer tipo customizado
        # cai no generico "hospitality property", que ainda funciona bem na frase.
        _HOSTEL_TYPE_LABELS = {
            "hostel": "hostel",
            "hotel": "hotel",
            "pousada": "guesthouse",
            "resort": "resort",
            "flat": "serviced apartment",
        }
        hostel_type_label = _HOSTEL_TYPE_LABELS.get((hostel_type or "").strip().lower(), "hospitality property")

        system_prompt = SYSTEM_PROMPT.format(
            phone_instruction=phone_instruction,
            language_instruction=language_instruction,
            name_instruction=name_instruction,
            alt_channel_instruction=alt_channel_instruction,
            today_date=datetime.date.today().isoformat(),
            hostel_name=hostel_name or "the property",
            hostel_type_label=hostel_type_label,
            custom_instructions_section=_custom_instructions_section(custom_instructions),
        )

    # image_data_url: quando o hospede manda uma foto no chat (nao um
    # documento de identidade - esse fluxo e separado), a mensagem vira
    # multimodal (visao da OpenAI) em vez de texto puro, pra IA reagir
    # ao CONTEUDO da foto de verdade (ex: reclamacao com foto do quarto)
    # e nao so ver um placeholder tipo "[foto]". So a mensagem ATUAL usa
    # esse formato - o historico (history) continua so texto.
    if image_data_url:
        user_content = [
            {"type": "text", "text": message or "(the guest sent a photo with no caption)"},
            {"type": "image_url", "image_url": {"url": image_data_url}},
        ]
    else:
        user_content = message

    messages = (
        [{"role": "system", "content": system_prompt}]
        + history
        + [{"role": "user", "content": user_content}]
    )

    # As ferramentas de reserva/preco/cama (hospedagem) ou de portfolio
    # (agencia) precisam de um hostel_id real pra saber de qual conta se
    # trata - sem isso (ex: endpoint de teste manual sem hostel_id),
    # elas nem aparecem pro modelo. guest_id (nao guest_phone) porque
    # funciona pra qualquer canal - Messenger/Instagram nunca tem
    # guest_phone de verdade, mas sempre tem guest_id resolvido pelo
    # chamador.
    tools = [SAVE_GUEST_NAME_TOOL, SAVE_GUEST_LANGUAGE_TOOL]
    if is_software:
        pass  # so lead capture (nome/idioma) - nada de reserva/portfolio
    elif is_agency:
        if hostel_id:
            tools = tools + AGENCY_TOOLS
    elif hostel_id and guest_id:
        tools = tools + RESERVATION_TOOLS + OPERATIONAL_TOOLS

    extracted_name = None
    extracted_language = None
    final_text = None

    for round_number in range(MAX_TOOL_ROUNDS):
        kwargs = dict(model="gpt-4.1-mini", temperature=0.6, messages=messages)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = client.chat.completions.create(**kwargs)
        response_message = response.choices[0].message

        if not response_message.tool_calls:
            final_text = response_message.content
            break

        # Ajuda a diagnosticar o fallback "confirmar com a equipe" (linha
        # abaixo, dispara quando o loop de tool-calling esgota
        # MAX_TOOL_ROUNDS sem nunca produzir texto final) - mostra quais
        # ferramentas o modelo tentou chamar em cada rodada.
        print(f"ask_ai rodada {round_number + 1}/{MAX_TOOL_ROUNDS}: tool_calls =", [tc.function.name for tc in response_message.tool_calls])

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
                        hostel_id, guest_id, args.get("new_checkout_date")
                    )
                    tool_content = json.dumps(result, ensure_ascii=False)
                except ValueError as error:
                    tool_content = json.dumps({"error": str(error)}, ensure_ascii=False)
            elif name == "flag_extension_for_approval":
                try:
                    result = flag_extension_for_approval(
                        hostel_id, guest_id, args.get("note", "")
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
            elif name == "get_offerings":
                try:
                    items = list_portfolio_items(hostel_id, include_inactive=False)
                    result = [{
                        "name": item["name"],
                        "description": item["description"],
                        "category": item["category"],
                        "price_type": item["price_type"],
                        "price": item["price"],
                    } for item in items]
                    tool_content = json.dumps(result, ensure_ascii=False)
                except Exception as error:
                    tool_content = json.dumps({"error": "Erro ao buscar portfólio."}, ensure_ascii=False)
            elif name == "create_reservation":
                try:
                    result = create_reservation_from_chat(
                        hostel_id, guest_id,
                        args.get("guest_name"), args.get("category_name"),
                        args.get("checkin_date"), args.get("checkout_date"),
                        bed_id=args.get("bed_id")
                    )
                    tool_content = json.dumps(result, ensure_ascii=False)
                except ValueError as error:
                    tool_content = json.dumps({"error": str(error)}, ensure_ascii=False)
            elif name == "save_guest_date_of_birth":
                save_guest_date_of_birth_by_id(guest_id, args.get("date_of_birth"))
            elif name == "save_guest_nationality":
                save_guest_nationality_by_id(guest_id, args.get("nationality"))
            elif name == "get_menu":
                try:
                    result = get_menu_items(hostel_id)
                    tool_content = json.dumps(result, ensure_ascii=False)
                except Exception as error:
                    tool_content = json.dumps({"error": "Erro ao buscar cardápio."}, ensure_ascii=False)
            elif name == "create_kitchen_order":
                # Resolve nome->menu_item_id ANTES de criar o pedido - so
                # chama create_kitchen_order (que ja da baixa de estoque)
                # se TODOS os itens baterem com exatamente um item do
                # cardapio, pra nunca criar um pedido parcial/errado.
                resolved_items = []
                resolution_errors = []
                for requested_item in args.get("items", []):
                    matches = find_menu_item_by_name(hostel_id, requested_item.get("name", ""))
                    if len(matches) == 1:
                        resolved_items.append({
                            "menu_item_id": matches[0]["id"],
                            "quantity": requested_item.get("quantity", 1),
                            "notes": requested_item.get("notes"),
                        })
                    elif not matches:
                        resolution_errors.append(f"Item não encontrado no cardápio: '{requested_item.get('name')}'.")
                    else:
                        resolution_errors.append(f"Mais de um item do cardápio bate com '{requested_item.get('name')}' - seja mais específico.")

                if resolution_errors:
                    tool_content = json.dumps({"error": " ".join(resolution_errors)}, ensure_ascii=False)
                else:
                    try:
                        ticket_id = create_kitchen_order(
                            hostel_id, args.get("location"), resolved_items,
                            reported_by_guest_id=guest_id, channel=channel,
                        )
                        notify_on_duty_staff_for_ticket(hostel_id, ticket_id, "kitchen", channel=channel)
                        tool_content = json.dumps({"success": True, "ticket_id": ticket_id}, ensure_ascii=False)
                    except ValueError as error:
                        tool_content = json.dumps({"error": str(error)}, ensure_ascii=False)
            elif name == "report_maintenance_issue":
                ticket_id = create_maintenance_ticket(
                    hostel_id, args.get("location"), args.get("description"),
                    category=args.get("category"),
                    guest_reported_urgency=args.get("guest_reported_urgency"),
                    base_urgency=args.get("base_urgency", "normal"),
                    reported_by_guest_id=guest_id, channel=channel,
                )
                notify_on_duty_staff_for_ticket(hostel_id, ticket_id, "maintenance", channel=channel)
                tool_content = json.dumps({"success": True, "ticket_id": ticket_id}, ensure_ascii=False)
            elif name == "report_security_concern":
                ticket_id = create_security_incident(
                    hostel_id, args.get("location"), args.get("description"),
                    incident_type=args.get("incident_type"), reported_via="guest_chat",
                    reported_by_guest_id=guest_id, channel=channel,
                )
                notify_on_duty_staff_for_ticket(hostel_id, ticket_id, "patrimonial_security", channel=channel)
                tool_content = json.dumps({"success": True, "ticket_id": ticket_id}, ensure_ascii=False)
            elif name == "request_valet":
                vehicle = get_active_vehicle_for_guest(hostel_id, guest_id)
                if not vehicle:
                    tool_content = json.dumps({"error": "Nenhum veículo com manobrista encontrado pra esse hóspede."}, ensure_ascii=False)
                else:
                    ticket_id = request_valet(hostel_id, vehicle["id"], reported_by_guest_id=guest_id, channel=channel)
                    notify_on_duty_staff_for_ticket(hostel_id, ticket_id, "parking", channel=channel)
                    tool_content = json.dumps({"success": True, "ticket_id": ticket_id}, ensure_ascii=False)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_content
            })

    if final_text is None:
        print(f"ask_ai: MAX_TOOL_ROUNDS ({MAX_TOOL_ROUNDS}) esgotado sem texto final - hostel_id={hostel_id}, guest_phone={guest_phone!r}, tools_disponiveis={[t['function']['name'] for t in tools]}")
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
