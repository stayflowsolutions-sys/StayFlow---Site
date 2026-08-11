import json
import os
import re
from openai import OpenAI
from dotenv import load_dotenv

from database import get_connection

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Mensagens so-confirmacao que nao carregam sinal nenhum de venda/
# problema sozinhas ("ok", "obrigado", so emoji) - rodar a IA nelas so
# gerava ruido no Opportunity Center (pedido explicito do usuario pra
# parar) e dobrava o custo de token por mensagem (essa analise roda
# em CIMA da resposta do chat, nao no lugar dela). Lista curta e
# deliberadamente conservadora - qualquer coisa fora dela ainda passa
# pela IA normalmente, inclusive respostas curtas com numero/data
# ("dia 20", "sim, 2 pessoas") que continuam relevantes no contexto.
_FILLER_MESSAGES = {
    "ok", "okay", "okey", "oki", "blz", "beleza", "certo", "entendi",
    "show", "top", "legal", "otimo", "ótimo", "perfeito", "combinado",
    "obrigado", "obrigada", "obg", "vlw", "valeu", "thanks", "thank you",
    "ty", "gracias", "merci", "danke",
    "sim", "s", "yes", "y", "si", "oui", "ja", "já",
    "nao", "não", "no", "n", "non", "nein",
}

_EMOJI_RE = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF]+",
    flags=re.UNICODE,
)


def _is_filler_message(message):
    """True quando a mensagem nao vale a pena mandar pra IA analisar - so
    emoji/pontuacao, ou um agradecimento/confirmacao puro e curto."""
    stripped = _EMOJI_RE.sub("", message or "").strip()
    stripped = re.sub(r"[!?.,;:]+$", "", stripped).strip()

    if not stripped:
        return True

    if len(stripped) <= 25 and stripped.lower() in _FILLER_MESSAGES:
        return True

    return False


def fallback_analysis(message):
    return {
        "intent": "general",
        "score": 0,
        "urgency": "low",
        "estimated_value": 0,
        "description": "Não foi possível analisar a mensagem com segurança.",
        "next_action": "Revisar manualmente a conversa."
    }


def analyze_with_ai(message, history=None, account_kind="lodging"):
    # Analisa a CONVERSA (ultimas mensagens reais, se houver), nao so a
    # mensagem isolada que acabou de chegar - uma mensagem curta tipo
    # "sim" ou "pode ser dia 20" so faz sentido junto do que veio antes.
    # Sem isso, cada mensagem nova era avaliada do zero, sem contexto,
    # e o motor achava uma "oportunidade nova" a cada mensagem da MESMA
    # conversa em vez de entender que e a mesma intencao evoluindo.
    conversation_block = ""
    if history:
        lines = []
        for item in history[-10:]:
            speaker = "Hospede" if item.get("role") == "user" else "Recepcao/IA"
            lines.append(f"{speaker}: {item.get('content', '')}")
        conversation_block = "Conversa ate agora (mais antiga primeiro):\n" + "\n".join(lines) + "\n\n"

    business_context = (
        "a tour/rental agency and its customer"
        if account_kind == "agency"
        else "a hostel/hotel and its guest"
    )
    prompt = f"""
Analyze this conversation between {business_context}, and return ONLY
valid JSON. Judge the opportunity based on the CONVERSATION AS A WHOLE,
not just the single latest message in isolation - a short reply like
"sim" or "pode ser dia 20" only makes sense together with what came
before.

{conversation_block}Latest message just received:
{message}

Return this exact structure:
{{
  "intent": "booking",
  "score": 94,
  "urgency": "high",
  "estimated_value": 420,
  "description": "Cliente demonstrou alta intenção de reservar.",
  "next_action": "Responder em até 10 minutos."
}}

Rules:
- intent must be one of: booking, tour, upsell, human_help, follow_up, general
- score must be a number from 0 to 100
- urgency must be one of: low, medium, high
- set urgency to "high" whenever the guest/customer shows frustration or
  dissatisfaction, reports a problem/complaint about the service they
  received (for a stay: room, cleanliness, staff, noise, etc.; for a
  tour/rental: the vehicle/equipment/guide not showing up or not as
  described, etc.), or asks something you are not confident you can
  resolve on your own - even when intent is "general" (this is what
  triggers a real-time alert to the team, so it must not be missed)
- estimated_value must be a number
- description must be in Portuguese
- next_action must be in Portuguese
- return only JSON, no markdown, no explanation
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.2,
            messages=[
                {
                    "role": "system",
                    "content": "You are StayFlow's decision engine for hospitality operations. Always return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content.strip()

        if content.startswith("```"):
            content = content.replace("```json", "").replace("```", "").strip()

        return json.loads(content)

    except Exception as error:
        print("Decision Engine error:", error)
        return fallback_analysis(message)


def analyze_message(hostel_id, guest_id, message, history=None, account_kind="lodging"):
    """
    guest_id vem ja resolvido pelo chamador (routes/chat.py, via
    get_or_create_guest_by_channel) - antes essa funcao recebia
    telefone e procurava o hospede de novo por
    "WHERE hostel_id = ? AND phone = ?", o que nunca acharia nada pra
    canal sem telefone de verdade (Instagram/Messenger, onde
    guests.phone fica NULL).
    """
    if _is_filler_message(message):
        return None

    analysis = analyze_with_ai(message, history=history, account_kind=account_kind)

    if analysis.get("intent") == "general":
        # "general" nunca vira oportunidade (nao e venda/reserva), mas
        # ainda pode ser um hospede com problema, duvida sem resposta
        # confiavel ou frustracao - isso merece alerta em tempo real pra
        # equipe mesmo sem virar linha no Opportunity Center. Tipo
        # separado de "opportunity" de proposito (pedido do usuario):
        # nao e sobre venda, e sobre atencao humana urgente.
        if analysis.get("urgency") == "high":
            try:
                from database import get_connection as _get_connection
                from services.push_service import send_push_to_hostel

                conn = _get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM guests WHERE id = ?", (guest_id,))
                guest_row = cursor.fetchone()
                conn.close()
                guest_name = guest_row["name"] if guest_row and guest_row["name"] else "Hóspede"

                send_push_to_hostel(
                    hostel_id,
                    title=f"⚠️ {guest_name}",
                    body=analysis.get("description") or "Hóspede pode precisar de atenção.",
                    url="/app",
                    notification_type="guest_needs_attention",
                )
            except Exception as error:
                print(f"AVISO: falha ao notificar hospede precisando de atencao por push: {error}")

        return analysis

    conn = get_connection()
    cursor = conn.cursor()

    # Uma conversa inteira sobre o mesmo assunto (ex: "booking") deve
    # virar UMA oportunidade que evolui, não uma nova a cada mensagem -
    # isso lotava o Opportunity Center e disparava o sino de novo a cada
    # mensagem da MESMA conversa. Se já existe uma oportunidade aberta
    # deste hóspede com o mesmo tipo, atualiza os dados nela em vez de
    # criar outra; um assunto genuinamente diferente (ex: pediu um tour
    # no meio de uma conversa de reserva) ainda vira sua própria linha.
    cursor.execute(
        """
        SELECT id FROM opportunities
        WHERE guest_id = ? AND status = 'open' AND type = ?
        ORDER BY created_at DESC LIMIT 1
        """,
        (guest_id, analysis.get("intent"))
    )
    existing = cursor.fetchone()
    is_new_opportunity = existing is None

    if existing:
        # created_at tambem funciona como "ultima atividade" aqui (nao e
        # exibido como data de criacao em lugar nenhum da interface) -
        # atualizar garante que uma conversa que acabou de responder
        # suba pro topo da lista, em vez de ficar presa na posicao de
        # quando foi detectada pela primeira vez.
        cursor.execute(
            """
            UPDATE opportunities
            SET description = ?, score = ?, urgency = ?, estimated_value = ?, next_action = ?, created_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                analysis.get("description"),
                analysis.get("score", 0),
                analysis.get("urgency", "low"),
                analysis.get("estimated_value", 0),
                analysis.get("next_action"),
                existing["id"]
            )
        )
    else:
        cursor.execute(
            """
            INSERT INTO opportunities
            (
                guest_id,
                type,
                description,
                status,
                score,
                urgency,
                estimated_value,
                next_action
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guest_id,
                analysis.get("intent"),
                analysis.get("description"),
                "open",
                analysis.get("score", 0),
                analysis.get("urgency", "low"),
                analysis.get("estimated_value", 0),
                analysis.get("next_action")
            )
        )

    cursor.execute("SELECT name FROM guests WHERE id = ?", (guest_id,))
    guest_row = cursor.fetchone()
    guest_name = guest_row["name"] if guest_row and guest_row["name"] else "Hóspede"

    conn.commit()
    conn.close()

    # So notifica em oportunidade NOVA (nao em toda mensagem que
    # atualiza uma ja existente) - senao uma conversa longa e urgente
    # manda uma notificacao por mensagem, o que rapidamente vira ruido
    # em vez de alerta util. Best-effort: falha no envio nunca deve
    # quebrar a analise da mensagem em si.
    if is_new_opportunity and analysis.get("urgency") == "high":
        try:
            from services.push_service import send_push_to_hostel
            send_push_to_hostel(
                hostel_id,
                title=f"🔥 {guest_name}",
                body=analysis.get("next_action") or analysis.get("description") or "Nova oportunidade de alta prioridade.",
                url="/app",
                notification_type="opportunity",
            )
        except Exception as error:
            print(f"AVISO: falha ao notificar nova oportunidade por push: {error}")

    return analysis