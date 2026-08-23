import json
import os
import re
from openai import OpenAI
from dotenv import load_dotenv

from database import get_connection, get_enabled_partner_items_for_hostel, dispatch_opportunity_webhook

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


# O que conta como "oportunidade" muda por categoria - um lead quente
# numa imobiliaria (visita agendada) nao e a mesma coisa que um upsell
# numa estetica automotiva (servico extra oferecido). Mesmo espirito
# de AGENCY_CATEGORY_PROMPTS em ai_service.py: contexto proprio por
# categoria, nao um rotulo generico trocado. "servico_generico"/
# categoria ausente cai no fallback generico de sempre.
_AGENCY_CATEGORY_BUSINESS_CONTEXT = {
    "turismo": "a tourism agency and its customer, discussing a tour or travel experience",
    "aluguel_carro": "a car rental company and its customer",
    "aluguel_bike": "a bike rental business and its customer",
    "aluguel_equipamentos": "an equipment rental business and its customer",
    "imobiliaria": "a real estate agency and its customer, discussing a property to buy or rent",
    "automotivo": "an automotive shop (detailing, tinting, mechanic, bodywork, parts, etc.) and its customer, discussing a service for their vehicle",
    "comercio": "a store and its customer, discussing a product",
}


def analyze_with_ai(message, history=None, account_kind="lodging", agency_category=None, partner_items=None):
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

    if account_kind == "agency":
        business_context = _AGENCY_CATEGORY_BUSINESS_CONTEXT.get(
            (agency_category or "").strip().lower(), "a business and its customer"
        )
    else:
        business_context = "a hostel/hotel and its guest"

    # Lista de itens de parceiro que ESSA hospedagem ja ativou
    # (Parceiros) - deixa a mesma chamada de IA tambem escolher qual
    # item combina com o pedido do hospede, em vez de uma segunda
    # chamada separada so pra isso. So entra no prompt quando existe
    # pelo menos um item (custo zero pra quem nao usa Parceiros).
    partner_items_block = ""
    if partner_items:
        items_lines = "\n".join(
            f'- id {item["id"]}: {item["name"]} ({item.get("category") or "sem categoria"})'
            + (f' - {item["description"]}' if item.get("description") else "")
            for item in partner_items
        )
        partner_items_block = f"""
This business also has partner items available to offer when the guest
asks for something the business itself does not sell directly:
{items_lines}

If (and only if) the guest's request genuinely matches one of these
items, include its id as "suggested_partner_item_id". If none of them
are a real match, use null - never force a suggestion.
"""

    prompt = f"""
Analyze this conversation between {business_context}, and return ONLY
valid JSON. Judge the opportunity based on the CONVERSATION AS A WHOLE,
not just the single latest message in isolation - a short reply like
"sim" or "pode ser dia 20" only makes sense together with what came
before.

{conversation_block}Latest message just received:
{message}
{partner_items_block}
Return this exact structure:
{{
  "intent": "booking",
  "score": 94,
  "urgency": "high",
  "estimated_value": 420,
  "description": "Cliente demonstrou alta intenção de reservar.",
  "next_action": "Responder em até 10 minutos.",
  "suggested_partner_item_id": null
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
- suggested_partner_item_id must be one of the ids listed above, or null
  if no partner items were listed or none genuinely match
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


def analyze_message(hostel_id, guest_id, message, history=None, account_kind="lodging", agency_category=None):
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

    # Busca os itens de parceiro ANTES da analise pra IA poder escolher
    # qual combina com o pedido na MESMA chamada, em vez de sempre
    # sugerir "o primeiro item habilitado" depois (dívida tecnica
    # documentada desde a v1.47.0). So pra contas lodging - agencia
    # nao tem "Parceiros" pra oferecer pro proprio cliente.
    partner_items = get_enabled_partner_items_for_hostel(hostel_id) if account_kind == "lodging" else []

    analysis = analyze_with_ai(
        message,
        history=history,
        account_kind=account_kind,
        agency_category=agency_category,
        partner_items=partner_items,
    )

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

    # Quando o hospede pede um passeio/excursao (intent='tour') e a
    # hospedagem ja tem algum item de portfolio de agencia parceira
    # ativado (Parceiros), usa o id que a propria IA escolheu (mesma
    # chamada acima, ja viu a lista de candidatos e o pedido real do
    # hospede) - so pra 'tour' de proposito (o unico intent que mapeia
    # claramente pra categoria de agencia hoje - 'upsell' e generico
    # demais, cobre coisas sem nada a ver, tipo upgrade de quarto).
    # Valida contra os ids realmente oferecidos pra nao aceitar uma
    # alucinacao da IA (id inventado, fora da lista que foi mandada).
    suggested_partner_item_id = None
    if analysis.get("intent") == "tour" and partner_items:
        candidate_ids = {item["id"] for item in partner_items}
        raw_suggestion = analysis.get("suggested_partner_item_id")
        if raw_suggestion in candidate_ids:
            suggested_partner_item_id = raw_suggestion

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
            SET description = ?, score = ?, urgency = ?, estimated_value = ?, next_action = ?,
                suggested_partner_item_id = ?, created_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                analysis.get("description"),
                analysis.get("score", 0),
                analysis.get("urgency", "low"),
                analysis.get("estimated_value", 0),
                analysis.get("next_action"),
                suggested_partner_item_id,
                existing["id"]
            )
        )
        opportunity_id = existing["id"]
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
                next_action,
                suggested_partner_item_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                guest_id,
                analysis.get("intent"),
                analysis.get("description"),
                "open",
                analysis.get("score", 0),
                analysis.get("urgency", "low"),
                analysis.get("estimated_value", 0),
                analysis.get("next_action"),
                suggested_partner_item_id
            )
        )
        opportunity_id = cursor.lastrowid

    cursor.execute("SELECT name FROM guests WHERE id = ?", (guest_id,))
    guest_row = cursor.fetchone()
    guest_name = guest_row["name"] if guest_row and guest_row["name"] else "Hóspede"

    conn.commit()
    conn.close()

    # Contas 'agency' (imobiliaria, estetica automotiva, loja online etc.)
    # nao tem reserva/check-in - a oportunidade E o evento de conversao
    # pra esse tipo de negocio, entao e ela que dispara o webhook de saida
    # genérico (se o cliente tiver um sistema proprio cadastrado em
    # Configuracoes -> Integracoes). Hospedagem continua so avisando via
    # reserva (dispatch_reservation_webhook), pra nao duplicar sinal.
    if account_kind == "agency":
        dispatch_opportunity_webhook(
            hostel_id, guest_id, opportunity_id,
            "opportunity_created" if is_new_opportunity else "opportunity_updated"
        )

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