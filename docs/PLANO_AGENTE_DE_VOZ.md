# PLANO TÉCNICO — Agente de Voz por IA

**Status:** Não iniciado. Pesquisa de viabilidade concluída em 02/09/2026 (sessão autônoma, item "b" da fila de melhorias inspiradas em concorrência — WeSpeak anuncia agente de voz por telefone como diferencial). Nenhuma linha de código escrita ainda — este documento existe pra deixar o desenho técnico pronto antes de decidir seguir, não pra registrar algo já construído (diferente do padrão normal de `DIARIO_DE_ENGENHARIA.md`, que só registra o que já foi shippado).

**Por que parou na pesquisa e não foi direto pra código**: diferente dos outros itens da fila desta madrugada (BI/Relatórios, kanban, venda cruzada, cancelamento via chat, desconto de estadia longa, cupom — todos sem custo variável novo pro StayFlow), agente de voz envolve dinheiro real por minuto de ligação e a criação de uma conta nova (Twilio) com cartão de crédito — decisão de negócio, não técnica. Ver seção "Decisões pendentes" no fim.

---

## 1. Motivação

Nenhum concorrente pesquisado até agora (WeSpeak, Hoteligy, R2OS/WhatsMinder) confirma ter isso rodando de verdade em produção — WeSpeak apenas *anuncia* atendimento por voz como diferencial de marketing. Vale considerar, antes de investir tempo real nisso, confirmar se é uma feature que os concorrentes de fato entregam ou se é discurso de venda sem produto por trás — mas mesmo que seja só anúncio, "atender por telefone" é uma dor real e universal do setor (hóspede que liga de verdade, não manda WhatsApp) que a StayFlow hoje não cobre de forma nenhuma.

## 2. Arquitetura proposta

```
Ligação telefônica do hóspede
        │
        ▼
Número Twilio (compartilhado ou por hostel — ver seção 6)
        │  (Twilio Media Streams — WebSocket bidirecional de áudio)
        ▼
Servidor-ponte NOVO (processo separado do Flask principal)
        │  (WebSocket, proxy de áudio bruto nos dois sentidos)
        ▼
OpenAI Realtime API (gpt-realtime — entende e fala, com
interrupção/turn-taking nativos, function calling embutido)
        │
        ▼
MESMA camada de tools que o chat de texto já usa
(services/ai_service.py — ver seção 3)
```

Padrão bem documentado publicamente (Twilio tem tutorial oficial pra exatamente esse fluxo — Twilio Voice + OpenAI Realtime Agents SDK). Não é território inexplorado, é integração de duas APIs já maduras.

**Ponto técnico central**: a OpenAI Realtime API já suporta function calling no mesmo formato JSON que a API de Chat Completions que o StayFlow já usa — ou seja, o *schema* de cada tool (`get_room_options`, `create_reservation`, etc.) não precisa ser reescrito do zero, só re-registrado nesse novo canal.

## 3. Reaproveitamento do que já existe

O texto (`services/ai_service.py`) já tem toda a lógica de negócio que um agente de voz precisaria — a única coisa que muda é o CANAL, não o cérebro:

| Tool já existente | Reaproveitável direto? |
|---|---|
| `get_room_options`, `get_available_beds`, `get_stay_total` | Sim, sem mudança de lógica |
| `validate_coupon`, `create_reservation`, `cancel_reservation`, `extend_reservation` | Sim, sem mudança de lógica |
| `get_addons`, `get_offerings` | Sim, sem mudança de lógica |
| `get_menu`, `create_kitchen_order`, `report_maintenance_issue`, `report_security_concern`, `request_valet` | Sim (fase 2, ver seção 7) |
| `save_guest_name`, `save_guest_language`, `save_guest_date_of_birth`, `save_guest_nationality` | Sim, sem mudança de lógica |

O que **precisa** ser adaptado, não reaproveitado 1:1:

- **`SYSTEM_PROMPT`**: o texto atual foi escrito pra ser LIDO (permite formatação, listas, "20.000" por extenso). Voz exige frases mais curtas, sem qualquer marcação, números faláveis de forma natural, e instrução explícita de não competir por turno de fala (deixar o hóspede terminar de falar).
- **Confirmações que hoje são visuais** (ex: foto de documento, link de pagamento) não existem em ligação de voz — precisa de um fallback claro ("vou te mandar um link por WhatsApp pra isso") em vez de tentar fazer tudo só de voz.

## 4. Modelo de custo (estimado, pesquisa de 02/09/2026)

**Twilio** (número + minutos recebidos):
- Número local Argentina: ~US$8/mês + ~US$0,01/minuto recebido.
- Número toll-free Argentina: ~US$25/mês + ~US$0,23/minuto recebido (não vale a pena pro nosso caso).
- Preço varia por país — cada hostel em país diferente precisaria de número próprio daquele país ou aceitar chamada internacional (mais cara).

**OpenAI Realtime API** (cobra por token de áudio, não por minuto fixo):
- Modelo principal (`gpt-realtime`): ~US$0,06–0,11/min com cache de prompt funcionando; sem cache, pode chegar a US$0,18–0,46/min em ligação longa.
- Modelo "mini": cerca de 1/3 do preço (~US$0,02–0,05/min com cache).

**Estimativa de exemplo** (100 ligações/mês, 4 min de média = 400 min/mês, modelo mini com cache):
- Twilio: ~US$8 (número) + US$4 (minutos) = **~US$12/mês**
- OpenAI: 400 × US$0,035 (meio-termo) ≈ **~US$14/mês**
- **Total aproximado: US$25–30/mês por hostel** nesse volume — pode subir bastante em hostel com volume real de ligação ou se usar o modelo principal sem cache.

Isso é a PRIMEIRA feature da StayFlow com custo variável direto por uso (diferente de WhatsApp, que não tem custo por mensagem pro StayFlow hoje) — precisa entrar num modelo de billing que hoje não existe (ver seção 8).

## 5. Diferença de infraestrutura

- **Hoje**: tudo é webhook HTTP stateless (rotas Flask, uma requisição = uma resposta, sem conexão mantida aberta).
- **Voz exige**: um processo mantendo WebSocket aberto durante a ligação inteira (minutos, não milissegundos) — não cabe no modelo request/response atual sem adaptação.
- **Render** (onde a StayFlow já hospeda) suporta WebSocket nativamente em Web Services — confirmado via documentação oficial (`render.com/docs/websocket`), incluindo timeout estendido pra streaming de LLM e conexões que ficam abertas indefinidamente sem cair sozinhas. Viável sem trocar de provedor de hosting.
- Recomendação: serviço **separado** do Flask principal (processo próprio), não encaixar no mesmo `app.py` — motivo: uma ligação de voz mantém estado/conexão por minutos, e não deveria competir por recurso com as requisições HTTP normais do resto do produto.

## 6. Riscos técnicos a validar antes de prometer ao usuário

- **Latência real**: uma ligação de telefone exige resposta natural (idealmente <1s de silêncio antes de responder) — precisa testar de verdade, não só confiar na documentação da OpenAI.
- **Interrupção de fala (barge-in)**: a Realtime API já suporta nativamente, mas a configuração fina (quão sensível, quando cortar a fala da IA) precisa de ajuste empírico, não sai "pronto" na primeira tentativa.
- **Cobertura por país**: Twilio tem número local pra Argentina confirmado; cobertura/qualidade pra outros países onde a StayFlow tem ou vai ter cliente precisa ser checada individualmente antes de prometer a feature pra um piloto fora da Argentina.
- **Qualidade de voz em português/espanhol**: a Realtime API é multilíngue, mas sotaque e naturalidade em pt-BR/es-AR não foram testados de verdade nesta pesquisa — só documentação, não uma ligação real.

## 7. Fases sugeridas, se aprovado

- **Fase 0 (não é código)**: usuário decide o modelo de billing do custo variável (seção 8), cria a conta Twilio, escolhe 1 hostel piloto disposto a testar.
- **Fase 1 (MVP mínimo)**: 1 número, 1 idioma (português), só as tools de reserva (`get_room_options`/`get_stay_total`/`create_reservation`/`get_available_beds`) — sem cardápio, sem manutenção, sem segurança. Testado com ligação real de verdade (não só teste automatizado) antes de qualquer cliente real usar.
- **Fase 2**: `OPERATIONAL_TOOLS` completo (cardápio, manutenção, segurança, manobrista), mais idiomas, métricas de uso/custo visíveis no `admin.html` (quantos minutos cada hostel consumiu, pra cobrança e pra decisão de manter ou não).

## 8. Decisões pendentes — só o usuário resolve, não é técnico

1. **Quem paga o custo variável por minuto?** StayFlow absorve dentro do plano mensal atual (risco: cliente com muita ligação vira prejuízo), ou cobra separado por consumo (precisa de mecanismo de billing por uso, que não existe hoje — o billing atual, v1.59.0, é só assinatura fixa via Mercado Pago)?
2. **Quem cria a conta Twilio e quando?** Precisa de cartão de crédito e verificação de identidade — ação do usuário, não automatizável por mim.
3. **Qual hostel/piloto testa primeiro?** Idealmente um com volume real de ligação (não adianta testar num piloto que nunca recebe telefonema).
4. **Vale a pena mesmo, dado o custo por minuto?** Nenhum concorrente pesquisado confirma ter isso rodando de verdade em produção — vale considerar se é prioridade real ou se o "diferencial" dos concorrentes é só discurso de vendas.
