---

## Perguntas pra amanhã (rascunho — vamos formalizar na audiência)

1. Se um hóspede manda mensagem e o número `to` não bate com nenhum
   `hostels.phone`, o que acontece? Por quê o sistema foi desenhado assim?
2. Por que `guests.phone` não pode mais ser `UNIQUE` sozinho?
3. Onde mora a decisão de "qual hostel é esse"? (duas respostas — uma pra
   rota logada, outra pro webhook)
4. O que o decorator `@require_auth` faz, exatamente, antes da view rodar?
5. Se eu apagar o cookie de sessão do navegador, o que acontece na próxima
   chamada ao `/dashboard`?

---

## SESSÃO 2 — 05/07/2026

### Contexto no início da sessão

Retomando depois de um dia sem trabalhar no projeto (dia 04 foi só descanso).
Objetivo declarado pelo usuário: máximo de progresso possível, incluindo
funcionalidades que faltavam e infraestrutura de produção.

### O que foi construído (funcionalidades novas, todas testadas com sandbox antes de entregar)

1. **Sessão de login real no frontend** — trocou o check baseado só em
   `localStorage` por verificação de verdade via `GET /me`. Adicionado botão
   de logout (não existia).
2. **Módulo de Reservas** — criado do zero: tabela `reservations`,
   `routes/reservations.py` (GET/POST/PATCH), formulário no frontend,
   seletor de mudança de status.
3. **Bug corrigido em `routes/settings.py`** — tabela `settings` antiga não
   tinha as colunas `hostel_name/hostel_type/checkin/checkout` que o código
   novo esperava (mesmo padrão do bug de `guests.phone` do dia 1). Corrigido
   com migração automática (`add_column_if_not_exists`).
4. **`GET /guests`** — rota de listagem que não existia (só existia
   `/guests/<id>` individual).
5. **Módulo Financeiro** (`routes/finance.py`) — reaproveita dados de
   `reservations` + `opportunities`, sem tabela nova.
6. **Módulo Relatórios** (`routes/reports.py`) — receita por canal + funil
   de conversão, também reaproveitando dados existentes.
7. **Módulo Estoque completo** — `suppliers` (fornecedores) +
   `inventory_items` (com categoria, fornecedor, quantidade, mínimo,
   quantidade de reposição sugerida). Alertas de estoque baixo geram
   **mensagem sugerida pronta pra copiar e mandar pro fornecedor**. Editar/
   excluir/marcar vazio.
8. **Padrão de design "+ criar novo na hora"** aplicado em: categoria de
   estoque, unidade de medida, tipo de quarto (reservas), tipo de
   propriedade (configurações) — sempre que fizer sentido, esse é o padrão
   a seguir daqui pra frente.
9. **Módulo Operações** (`routes/operations.py`) — alertas agregados
   (check-in/out pendente, oportunidade urgente sem resposta, estoque
   baixo). Tarefas de limpeza ficam vazias de propósito (dependem do mapa
   de camas, Fase 2).
10. **Módulo Receitas/Upsell** (`routes/revenue.py`) — catálogo de
    experiências/upsells (tabela `offerings`) + oportunidades que a IA já
    classifica como `tour`/`upsell` (reaproveitado do `decision_engine`).

### WhatsApp Business — Cloud API real (a peça mais importante do dia)

- `hostels` ganhou colunas `whatsapp_phone_number_id` e
  `whatsapp_access_token` (credenciais por hostel, multi-tenant).
- `services/whatsapp_service.py` — `send_whatsapp_message()`, chama a
  Graph API da Meta de verdade. Antes disso, o sistema só **gerava** a
  resposta da IA e nunca enviava de volta pro WhatsApp — essa era uma
  lacuna 100% real que foi fechada agora.
- `routes/chat.py` foi refatorado: lógica principal virou
  `process_incoming_message(hostel_id, phone, text, send_to_whatsapp)`,
  reaproveitada tanto pelo `/message` de teste quanto pelo webhook real.
- `routes/whatsapp_webhook.py` (novo) — `GET /webhook/whatsapp` (handshake
  de verificação da Meta) e `POST /webhook/whatsapp` (recebe mensagens no
  formato real da Meta, bem diferente do `{phone, message}` simples usado
  pra teste).
- Frontend: card "📱 WhatsApp Business" em Configurações, com campos pra
  colar Phone Number ID e Access Token, e exibição da Callback URL +
  Verify Token que precisam ser colados no painel da Meta.
- **Pendência:** a configuração final no painel da Meta (colar a URL e o
  token) não foi concluída — paramos no meio pra resolver a hospedagem
  definitiva primeiro (ver abaixo).

### Pesquisa de custos e naming (decisões de negócio, não só código)

- **Domínio:** `stayflow.com` já existia (empresa de válvulas industriais,
  sem relação). `stayflow.io` existe e é uma consultoria de hotelaria no
  Vietnã (risco baixo de confusão real — modelo de negócio e mercado
  diferentes). Decidido: **`stayflowsolutions.com`**, comprado via
  Cloudflare Registrar (~US$ 10,44/ano).
- **Custo mensal estimado total** (Render + domínio + OpenAI, WhatsApp
  gratuito no uso atual): **US$ 35-45/mês** pra manter rodando com 1 hostel
  piloto. Escala bem devagar por hostel adicional.
- OpenAI `gpt-4.1-mini`: US$ 0,40/1M tokens entrada, US$ 1,60/1M saída —
  poucos centavos por conversa real.

### Git — descoberta importante

O backend (`app.py`, `database.py`, `routes/`, `services/`, `utils/`)
**nunca tinha sido versionado no Git antes de hoje** — estavam todos como
"untracked". Criado `.gitignore` (exclui `stayflow.db`, `conversations.json`,
`__pycache__`, backups locais), e feito o primeiro commit de verdade de
todo o backend (30 arquivos) + depois o frontend copiado pra dentro do
mesmo repositório (45 arquivos, necessário pro deploy no Render).

### Deploy em produção — a saga do dia

- Render Pro comprado (workspace). Descoberto que **já existia um serviço
  antigo** chamado `HostelBot`, criado em 18/06, no plano Free, quebrando
  a cada deploy porque o Start Command ainda apontava pro `hostelbot.py`
  (arquivo já apagado há dias).
- Corrigido: Build Command (`pip install -r requirements.txt`, antes
  instalava só 3 libs na mão), Start Command (`gunicorn app:app`, antes
  `python hostelbot.py`).
- `requirements.txt` ganhou `bcrypt`, `gunicorn`, `requests` (faltavam).
- Frontend (`StayFlow---Site/`) copiado pra dentro do repositório do
  backend via `xcopy`, porque o Render só puxa um repositório por serviço.
- Variáveis de ambiente (`STAYFLOW_FRONTEND_DIR`, `SECRET_KEY`,
  `WHATSAPP_VERIFY_TOKEN`, `OPENAI_API_KEY`) precisaram ser configuradas
  **duas vezes** — a primeira vez não salvou de verdade (bug de interface
  ou clique perdido), só percebemos porque conferimos direto no Shell do
  Render (`env | grep`).
- Serviço migrado de Free pra **Starter** ($7/mês) — tira o "dormir após
  15 min" e habilita disco persistente e Shell.
- ⚠️ A chave da OpenAI apareceu em texto puro durante um `env | grep` no
  Shell do Render, colado aqui no chat. **Já foi revogada e trocada** por
  uma nova, tanto na OpenAI quanto no Render.
- **Resultado final: https://hostelbot-9yyg.onrender.com está no ar**,
  testado com um hostel de teste criado direto em produção (cadastro →
  login → dashboard carregando dado real).

### Ferramenta nova aprendida: usar `node --check` pra validar JavaScript

Quando um erro de sintaxe no `dashboard.html` (uma chave `{` faltando)
causava recarregamento de página em vez de salvar formulário via API,
descobrimos que dava pra extrair os blocos `<script>` do HTML e validar
cada um com `node --check arquivo.js` — aponta a linha exata do erro,
muito mais rápido que caçar visualmente num arquivo de 3600+ linhas.

### O que ficou pendente pra próxima sessão

- [ ] Conectar `stayflowsolutions.com` ao serviço no Render
- [ ] Terminar a configuração do webhook no painel da Meta (Callback URL +
      Verify Token) usando a URL de produção estável
- [ ] Confirmar/anexar disco persistente no Render (Starter permite, não
      confirmamos que já está ativo)
- [ ] Testar mensagem real do WhatsApp chegando e sendo respondida
- [ ] Adicionar link "Criar conta" clicável no `Login.html`
- [ ] Separar "trocar de usuário" vs "trocar de hostel" no logout
- [ ] Visual do Login (logo pequena + fundo ondulado) — fica pro
      refinamento visual planejado pra amanhã
- [ ] Faxina de pastas locais (`Archive/`, `Audit/`, `backups/`) — nunca
      confirmada
- [ ] Consolidar as 3 versões do Documento Mestre em `docs/`
- [ ] Decidir destino do `templates/components/` (nunca integrado)
- [ ] Botão de cancelar reserva — **já resolvido nesta sessão** (seletor de
      status na tabela de reservas)

### Checklist rápido pra amanhã (ponto de partida sugerido)

1. Conectar domínio
2. Fechar WhatsApp de verdade (Meta + teste real)
3. Refinamento visual (login, logo, fundo)
4. Faxina de pastas + consolidação de docs