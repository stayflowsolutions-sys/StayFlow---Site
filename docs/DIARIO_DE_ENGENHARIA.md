# DIÁRIO DE ENGENHARIA — StayFlow

Este documento é o registro dia a dia do trabalho na StayFlow. Diferente do
`STAYFLOW_MASTER_CONTEXT.md` (que é a fonte oficial de verdade do produto),
este arquivo é **didático**: existe pra você acompanhar o raciocínio, entender
os caminhos dos arquivos e aprender a arquitetura enquanto ela evolui. Também
serve como "memória de recuperação" — se uma conversa nova precisar retomar
o projeto do zero, colar este arquivo já entrega o contexto inteiro.

## 🟢 RESUMO RÁPIDO — LEIA ISSO PRIMEIRO (última atualização: Sessão 2, 05/07/2026, ~12:30)

**Se você está numa conversa nova comigo (Claude) e colou este arquivo:** aqui está o estado exato do projeto, incluindo o passo exato onde paramos. Não precisa reexplicar nada, só confirma se algo mudou.

- **Produto em produção, rodando de verdade:** https://hostelbot-9yyg.onrender.com
- **Repositório backend:** github.com/stayflowsolutions-sys/HostelBot (contém `HostelBot/` completo E `StayFlow---Site/` copiado pra dentro, porque o Render só puxa 1 repositório)
- **Repositório frontend original (separado, ainda existe mas não é mais o usado em produção):** github.com/stayflowsolutions-sys/StayFlow---Site
- **Hospedagem:** Render, plano **Starter** ($7/mês) no serviço `HostelBot` (Service ID: `srv-d8p483h194ac738tvq6g`), workspace no plano **Pro** ($25/mês)
- **Domínio comprado:** `stayflowsolutions.com` (Cloudflare Registrar)
- **Banco de dados:** SQLite (`stayflow.db`), multi-tenant por `hostel_id`. **O banco em produção é diferente do banco local** — dados de teste, não o Lagares real ainda
- **IA:** OpenAI `gpt-4.1-mini` — chave já foi **rotacionada** (a antiga vazou em texto durante debug, foi revogada e trocada)
- **WhatsApp:** código 100% pronto (webhook real da Meta + envio de resposta), mas a configuração final na Meta (Callback URL + Verify Token) **ainda não foi feita**

### 🔴 PONTO EXATO ONDE PARAMOS (retomar exatamente daqui):

Estávamos conectando o domínio `stayflowsolutions.com` ao serviço do Render. Progresso:

1. ✅ No Render → `HostelBot` → Settings → Custom Domains → cliquei em "+ Add Custom Domain" → digitei `stayflowsolutions.com` → avançou pra etapa "Add DNS records", que pediu 2 registros:
   - `www.stayflowsolutions.com` → CNAME → `hostelbot-9yyg.onrender.com`
   - `stayflowsolutions.com` (raiz) → como CNAME na raiz pode dar problema, o Render sugeriu usar registro **A** apontando pra `216.24.57.1`
2. ✅ Fui na Cloudflare (dash.cloudflare.com → domínio `stayflowsolutions.com` → DNS → Records) e criei os 2 registros:
   - Registro A: Nome `@`, Conteúdo `216.24.57.1`, Proxy status = **"Apenas DNS"** (nuvem cinza, não laranja — importante, o Render precisa disso pra validar e emitir certificado HTTPS)
   - Registro CNAME: Nome `www`, Conteúdo `hostelbot-9yyg.onrender.com`, Proxy status = **"Apenas DNS"** também
3. ⏳ **PRÓXIMO PASSO IMEDIATO:** voltar na aba do Render (Settings → Custom Domains do serviço `HostelBot`), dar F5, e verificar se o domínio já aparece como verificado/ativo. DNS pode levar alguns minutos até 24h pra propagar. Se ainda não verificou, só esperar e tentar de novo.

### Depois de confirmar o domínio, os passos seguintes são:

4. Configurar o webhook na Meta (developers.facebook.com → app "StayFlow AI" → Casos de uso → Conectar en WhatsApp → Paso 2: Configuración de producción → campos "URL de devolución de llamada" e "Token de verificación"):
   - Callback URL: usar `https://stayflowsolutions.com/webhook/whatsapp` (depois de confirmado o domínio) ou `https://hostelbot-9yyg.onrender.com/webhook/whatsapp` (já funciona agora, sem esperar o domínio)
   - Verify Token: `stayflow-verify-token`
5. Confirmar/anexar disco persistente no Render (Starter permite, mas não confirmamos explicitamente que está ativo — sem isso, o `stayflow.db` de produção pode ser apagado em reinícios futuros). Ver em Render → `HostelBot` → menu lateral → "Disk".
6. Testar uma mensagem real de WhatsApp chegando e sendo respondida de ponta a ponta.
7. Depois disso, **parar e fazer o checklist final do dia** (o usuário quer anotar num caderno físico também).

### Dívidas técnicas conhecidas (não travam nada, mas estão anotadas):
- `Login.html` não tem link clicável pra "Criar conta" (só texto sem link)
- Botão de "Sair" deveria separar "trocar de usuário" vs "trocar de hostel" (multi-conta)
- Logo do Login pequena + falta efeito de fundo ondulado (visual, pendente pro dia seguinte)
- Faxina de pastas nunca confirmada (`Archive/`, `Audit/`, `backups/` dentro do projeto local)
- 3 versões do Documento Mestre em `docs/` (nunca consolidadas)
- `templates/components/` (sistema de componentização) nunca foi integrado — decidir se usa ou apaga
- `guest_service.py`/`message_service.py` foram reconstruídos por mim (confirmados compatíveis com os originais que o usuário mostrou)
- Mapa de camas + fluxo da equipe de limpeza + IA contatando fornecedor sozinha + botão flutuante "Ask StayFlow" inteligente → tudo isso é **Fase 2**, grande demais pra ser feito rápido
- O diário e o Documento Mestre ainda **não foram enviados pro GitHub** — combinado de fazer isso só depois de fechar domínio + WhatsApp, junto com o checklist final

---

## SESSÃO 1 — 03/07/2026

### Contexto no início da sessão

O projeto já existia e funcionava: backend Flask modular (`HostelBot/`),
frontend HTML/CSS/JS (`StayFlow---Site/`), banco SQLite, IA via OpenAI.
Mas era um sistema pensado pra **um hostel só** — nada era isolado por
cliente.

### O que foi auditado

Todos os arquivos do backend (`app.py`, `database.py`, as 9 rotas em
`routes/`, os 6 services em `services/`) e boa parte do frontend
(`dashboard.html`, `login.html`, `Register.html`, `settings.html`,
`inbox.html`, `reservations.html`, `statistics.html`, os `.js`).

Também mapeamos a estrutura de pastas real no disco (via os arquivos
`estrutura_stayflow.txt`, `stayflow_tree.txt` etc.) — que é maior e mais
bagunçada do que os arquivos avulsos sugeriam.

### O que foi encontrado (problemas)

1. **`hostelbot.py`** — protótipo antigo, duplicava tudo que já existia de
   forma melhor em `routes/chat.py` + `services/`. **Você já apagou.**
2. **Vazamento de dados entre hostels** — praticamente toda rota
   (`dashboard`, `executive-summary`, `activity`, `chats`, `opportunities`,
   `guests`) buscava dados **sem filtrar por hostel**. Um segundo cliente
   veria os dados do primeiro, e vice-versa.
3. **`settings.py`** tinha `hostel_id = 1` fixo no código (o próprio
   comentário já dizia "depois vamos trocar pelo hostel do usuário logado").
4. **Schema do banco**: `guests.phone` era `UNIQUE` — dois hostels não
   conseguiam ter hóspedes com o mesmo telefone.
5. **Bagunça de pastas**: `Archive/` (site antigo), `Audit/` (cópias soltas
   de uma auditoria anterior), `backups/` dentro do próprio `HostelBot/`
   com `routes/` e `services/` duplicados, 3 versões do Documento Mestre em
   `docs/`, e um sistema de componentização de frontend
   (`templates/components/*.html`) que nunca chegou a ser usado.

### O que foi corrigido (multi-tenant)

**Decisão de arquitetura:** sessão de servidor do Flask. Depois do login,
o servidor guarda `hostel_id`, `user_id` e `role` num cookie assinado.
Toda rota protegida lê o `hostel_id` dali — nunca de algo que o navegador
mande (isso seria falsificável).

**Arquivo novo — a peça central:**
- `utils/tenant.py` → tem o decorator `@require_auth`, que toda rota
  protegida usa. Ele lê a sessão e devolve `401` se não tiver ninguém
  logado.

**Arquivos alterados:**
- `app.py` → ganhou `secret_key` (necessário pra sessão existir) e rota
  genérica pra servir páginas `.html`.
- `database.py` → schema de `guests` corrigido (`UNIQUE(hostel_id, phone)`
  em vez de `UNIQUE(phone)`), `leads` ganhou coluna `hostel_id`, e existe
  **migração automática**: da próxima vez que `create_database()` rodar,
  ele detecta banco antigo e migra sozinho, sem perder dado.
- `routes/auth.py` → login e registro agora criam a sessão de verdade.
  Ganhou também `/logout` e `/me`.
- `routes/dashboard.py`, `executive.py`, `activity.py`, `chats.py`,
  `opportunities.py`, `guests.py` → todas agora recebem `hostel_id` via
  `@require_auth` e filtram TODAS as queries por ele.
- `routes/settings.py` → tirou o `hostel_id = 1` fixo.
- `routes/chat.py` (o webhook do WhatsApp) → esse não tem login, então
  descobre o `hostel_id` pelo número de WhatsApp que recebeu a mensagem
  (campo `to` no payload, casado contra `hostels.phone` no banco).
- `services/memory_service.py`, `services/decision_engine.py`,
  `services/lead_service.py` → todos passaram a receber `hostel_id` e
  escopar os dados por ele.

**Testado (não só escrito):** simulei 2 hostels fictícios, com hóspedes de
telefone **idêntico** nos dois. Confirmado: cada hostel só vê o próprio
dado; tentar acessar hóspede de outro hostel pelo ID retorna `404`; rota
sem login retorna `401`.

### O que ficou pendente (próxima sessão)

- [ ] **Frontend ainda não manda sessão** — o login grava o usuário em
      `localStorage`, mas as chamadas `fetch()` do `dashboard.html` não
      mandam cookie de sessão. Até isso ser ajustado, o frontend vai
      receber `401` das rotas novas.
- [ ] Confirmar `services/guest_service.py` e `services/message_service.py`
      — eu reconstruí esses dois porque não tinha o conteúdo original.
      Vale comparar com os arquivos reais, se ainda existirem em algum
      backup.
- [ ] Limpeza de pastas: `Archive/`, `Audit/`, `backups/` duplicado dentro
      de `HostelBot/`, consolidar `docs/` numa versão só do Documento
      Mestre.
- [ ] Decidir o destino do sistema de componentização de frontend
      (`templates/components/`) que nunca foi usado — integrar ou apagar.
- [ ] Cadastrar `hostels.phone` de cada hostel real (necessário pro
      webhook funcionar).
- [ ] Definir `SECRET_KEY` de produção (hoje só tem um valor de
      desenvolvimento).

### Arquivos entregues nesta sessão

Pasta `HostelBot_atualizado/`: `app.py`, `database.py`,
`migrate_conversations_json.py`, `routes/*.py` (9 arquivos),
`services/*.py` (6 arquivos), `utils/tenant.py`.

---

## Como funciona o fluxo hoje (mapa rápido pra revisar amanhã)

```
Hóspede manda mensagem no WhatsApp
        │
        ▼
routes/chat.py  (POST /message)
    → database.get_hostel_id_by_number()  [descobre de qual hostel é]
    → services/guest_service.py           [acha ou cria o hóspede]
    → services/memory_service.py          [contexto curto pra IA]
    → services/ai_service.py              [pergunta pro GPT o que responder]
    → services/message_service.py         [salva no SQLite]
    → services/lead_service.py            [salva como lead]
    → services/decision_engine.py         [classifica: score, urgência, valor]
        │
        ▼
   banco stayflow.db (tabelas: guests, conversations, messages,
                       leads, opportunities — tudo ligado por hostel_id)
        │
        ▼
Gestor abre o dashboard.html
    → faz login (routes/auth.py)          [cria a sessão de servidor]
    → dashboard.html chama /dashboard, /opportunities, /chats, etc.
    → cada rota usa utils/tenant.py pra saber de qual hostel são os dados
```

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
