---

## Perguntas pra amanhã (rascunho - vamos formalizar na audiência)

1. Se um hóspede manda mensagem e o número `to` não bate com nenhum
   `hostels.phone`, o que acontece? Por quê o sistema foi desenhado assim?
2. Por que `guests.phone` não pode mais ser `UNIQUE` sozinho?
3. Onde mora a decisão de "qual hostel é esse"? (duas respostas - uma pra
   rota logada, outra pro webhook)
4. O que o decorator `@require_auth` faz, exatamente, antes da view rodar?
5. Se eu apagar o cookie de sessão do navegador, o que acontece na próxima
   chamada ao `/dashboard`?

---

## SESSÃO 2 - 05/07/2026

### Contexto no início da sessão

Retomando depois de um dia sem trabalhar no projeto (dia 04 foi só descanso).
Objetivo declarado pelo usuário: máximo de progresso possível, incluindo
funcionalidades que faltavam e infraestrutura de produção.

### O que foi construído (funcionalidades novas, todas testadas com sandbox antes de entregar)

1. **Sessão de login real no frontend** - trocou o check baseado só em
   `localStorage` por verificação de verdade via `GET /me`. Adicionado botão
   de logout (não existia).
2. **Módulo de Reservas** - criado do zero: tabela `reservations`,
   `routes/reservations.py` (GET/POST/PATCH), formulário no frontend,
   seletor de mudança de status.
3. **Bug corrigido em `routes/settings.py`** - tabela `settings` antiga não
   tinha as colunas `hostel_name/hostel_type/checkin/checkout` que o código
   novo esperava (mesmo padrão do bug de `guests.phone` do dia 1). Corrigido
   com migração automática (`add_column_if_not_exists`).
4. **`GET /guests`** - rota de listagem que não existia (só existia
   `/guests/<id>` individual).
5. **Módulo Financeiro** (`routes/finance.py`) - reaproveita dados de
   `reservations` + `opportunities`, sem tabela nova.
6. **Módulo Relatórios** (`routes/reports.py`) - receita por canal + funil
   de conversão, também reaproveitando dados existentes.
7. **Módulo Estoque completo** - `suppliers` (fornecedores) +
   `inventory_items` (com categoria, fornecedor, quantidade, mínimo,
   quantidade de reposição sugerida). Alertas de estoque baixo geram
   **mensagem sugerida pronta pra copiar e mandar pro fornecedor**. Editar/
   excluir/marcar vazio.
8. **Padrão de design "+ criar novo na hora"** aplicado em: categoria de
   estoque, unidade de medida, tipo de quarto (reservas), tipo de
   propriedade (configurações) - sempre que fizer sentido, esse é o padrão
   a seguir daqui pra frente.
9. **Módulo Operações** (`routes/operations.py`) - alertas agregados
   (check-in/out pendente, oportunidade urgente sem resposta, estoque
   baixo). Tarefas de limpeza ficam vazias de propósito (dependem do mapa
   de camas, Fase 2).
10. **Módulo Receitas/Upsell** (`routes/revenue.py`) - catálogo de
    experiências/upsells (tabela `offerings`) + oportunidades que a IA já
    classifica como `tour`/`upsell` (reaproveitado do `decision_engine`).

### WhatsApp Business - Cloud API real (a peça mais importante do dia)

- `hostels` ganhou colunas `whatsapp_phone_number_id` e
  `whatsapp_access_token` (credenciais por hostel, multi-tenant).
- `services/whatsapp_service.py` - `send_whatsapp_message()`, chama a
  Graph API da Meta de verdade. Antes disso, o sistema só **gerava** a
  resposta da IA e nunca enviava de volta pro WhatsApp - essa era uma
  lacuna 100% real que foi fechada agora.
- `routes/chat.py` foi refatorado: lógica principal virou
  `process_incoming_message(hostel_id, phone, text, send_to_whatsapp)`,
  reaproveitada tanto pelo `/message` de teste quanto pelo webhook real.
- `routes/whatsapp_webhook.py` (novo) - `GET /webhook/whatsapp` (handshake
  de verificação da Meta) e `POST /webhook/whatsapp` (recebe mensagens no
  formato real da Meta, bem diferente do `{phone, message}` simples usado
  pra teste).
- Frontend: card "[WhatsApp] WhatsApp Business" em Configurações, com campos pra
  colar Phone Number ID e Access Token, e exibição da Callback URL +
  Verify Token que precisam ser colados no painel da Meta.
- **Pendência:** a configuração final no painel da Meta (colar a URL e o
  token) não foi concluída - paramos no meio pra resolver a hospedagem
  definitiva primeiro (ver abaixo).

### Pesquisa de custos e naming (decisões de negócio, não só código)

- **Domínio:** `stayflow.com` já existia (empresa de válvulas industriais,
  sem relação). `stayflow.io` existe e é uma consultoria de hotelaria no
  Vietnã (risco baixo de confusão real - modelo de negócio e mercado
  diferentes). Decidido: **`stayflowsolutions.com`**, comprado via
  Cloudflare Registrar (~US$ 10,44/ano).
- **Custo mensal estimado total** (Render + domínio + OpenAI, WhatsApp
  gratuito no uso atual): **US$ 35-45/mês** pra manter rodando com 1 hostel
  piloto. Escala bem devagar por hostel adicional.
- OpenAI `gpt-4.1-mini`: US$ 0,40/1M tokens entrada, US$ 1,60/1M saída -
  poucos centavos por conversa real.

### Git - descoberta importante

O backend (`app.py`, `database.py`, `routes/`, `services/`, `utils/`)
**nunca tinha sido versionado no Git antes de hoje** - estavam todos como
"untracked". Criado `.gitignore` (exclui `stayflow.db`, `conversations.json`,
`__pycache__`, backups locais), e feito o primeiro commit de verdade de
todo o backend (30 arquivos) + depois o frontend copiado pra dentro do
mesmo repositório (45 arquivos, necessário pro deploy no Render).

### Deploy em produção - a saga do dia

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
  **duas vezes** - a primeira vez não salvou de verdade (bug de interface
  ou clique perdido), só percebemos porque conferimos direto no Shell do
  Render (`env | grep`).
- Serviço migrado de Free pra **Starter** ($7/mês) - tira o "dormir após
  15 min" e habilita disco persistente e Shell.
- [ATENCAO] A chave da OpenAI apareceu em texto puro durante um `env | grep` no
  Shell do Render, colado aqui no chat. **Já foi revogada e trocada** por
  uma nova, tanto na OpenAI quanto no Render.
- **Resultado final: https://hostelbot-9yyg.onrender.com está no ar**,
  testado com um hostel de teste criado direto em produção (cadastro ->
  login -> dashboard carregando dado real).

### Ferramenta nova aprendida: usar `node --check` pra validar JavaScript

Quando um erro de sintaxe no `dashboard.html` (uma chave `{` faltando)
causava recarregamento de página em vez de salvar formulário via API,
descobrimos que dava pra extrair os blocos `<script>` do HTML e validar
cada um com `node --check arquivo.js` - aponta a linha exata do erro,
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
- [ ] Visual do Login (logo pequena + fundo ondulado) - fica pro
      refinamento visual planejado pra amanhã
- [ ] Faxina de pastas locais (`Archive/`, `Audit/`, `backups/`) - nunca
      confirmada
- [ ] Consolidar as 3 versões do Documento Mestre em `docs/`
- [ ] Decidir destino do `templates/components/` (nunca integrado)
- [ ] Botão de cancelar reserva - **já resolvido nesta sessão** (seletor de
      status na tabela de reservas)

### Checklist rápido pra amanhã (ponto de partida sugerido)

1. Conectar domínio
2. Fechar WhatsApp de verdade (Meta + teste real)
3. Refinamento visual (login, logo, fundo)
4. Faxina de pastas + consolidação de docs

---

## SESSÃO 3 - 08/07 a 09/07/2026

### Contexto no início da sessão

Retomando após correção da memória da IA (`memory_service.py` com disco
persistente + janela de histórico maior) e do prompt (`ai_service.py` com
tom mais natural). Claude Code instalado no VS Code com sucesso - primeira
sessão real usando essa ferramenta no projeto.

### Auditoria de CSS e refatoração completa

**Descoberta inicial:** o `legacy.css` (1503 linhas, motivo original do
pedido de refatoração) era código **órfão** - nenhuma página real da raiz
(`dashboard.html`, `index.html`, `Login.html`) linkava esse arquivo. Cada
uma tinha o próprio CSS embutido em `<style>` inline. O bug relatado (KPIs
cortados no mobile) existia de verdade, mas dentro do `dashboard.html`,
não no `legacy.css`.

**Também descoberto e corrigido no processo:**
- `Login.html` e `login.html` eram o mesmo arquivo físico no disco (Windows
  não distingue maiúsculas/minúsculas), mas o Git rastreava os dois como
  arquivos separados, com conteúdos diferentes (`login.html` era uma versão
  antiga e desatualizada, "Client Login"). Corrigido com
  `git rm --cached login.html`, mantendo só `Login.html`.
- `dashboard2.html` (backup manual pré-Git) confirmado sem nenhuma
  referência real no projeto - movido pra `_backup_antigo/`.

**Arquitetura nova aplicada** (plano revisado e aprovado antes de aplicar):

```
static/css/
  tokens.css   <- :root único (cores, radius, shadow, breakpoints), #0b84ff
               como token de cor oficial (valor do dashboard.html)
  reset.css    <- reset universal mínimo, compartilhado pelas 3 páginas
  app.css      <- extraído do dashboard.html
  landing.css  <- extraído dos 9 blocos <style> do index.html
  auth.css     <- extraído do Login.html (.card->.auth-card, .btn->.auth-btn,
               pra não colidir com os mesmos nomes de classe em app.css/landing.css)
  legacy.css   <- entry-point opcional (@import dos 5 acima), não usado
               por nenhuma página hoje
```

Órfãos movidos pra `_backup_antigo/`: `legacy.css` antigo,
`templates/dashboard.html` (748 linhas, incompleto, nunca foi o servido em
produção - confirmado que `/app` serve `dashboard.html` da raiz), CSS
vazios (`base.css`, `chats.css`, `components.css`, `responsive.css`,
`settings.css`), `layout.css` (não linkado em lugar nenhum).

### Bugs de mobile corrigidos (verificados com screenshot real, 375px/1440px)

1. **KPIs cortados no mobile do dashboard** - `.span-*`/`.kpi` nunca
   colapsavam pra `grid-column:span 12` em `<=1100px`. Regra que faltava,
   não guerra de especificidade.
2. **Logo do hero estourando a tela no mobile do `index.html`** - 9 blocos
   `<style>` cronológicos redefiniam `.hero-logo` com `!important`
   crescente; a última regra do arquivo (`980px`, sem `max-width`) sempre
   vencia, mesmo em telas pequenas. Teto de `270px` adicionado em `<=820px`.
3. **Botões do topbar cortados no mobile** ("Alertas operacionais"/"+Nova
   reserva") - achado durante a verificação, fora do escopo original.
   Corrigido empilhando em coluna.
4. **Card de login sem margem no mobile** - `body` sem `padding`, card
   encostava nas bordas. Confirmado (comparando com a versão anterior via
   `git show HEAD:Login.html`) que o bug já existia antes da refatoração,
   não foi introduzido por ela.

### Commit 1 e 2 (feitos direto nesta sessão, antes das rodadas sem supervisão)

- `40e1538` - refatoração de CSS completa (20 arquivos).
- `5447b1f` - `assets/js/chats-live.js` (224 linhas, script já em uso real
  pela aba Chats, tinha ficado fora do commit anterior por engano).

### Skill criado: `stayflow-context`

`.claude/skills/stayflow-context/SKILL.md`, aponta pra
`docs/DIARIO_DE_ENGENHARIA.md` e `docs/STAYFLOW_MASTER_CONTEXT.md` (os
dois precisaram ser movidos pra dentro do repositório, numa pasta `docs/`
nova, pra o skill funcionar - antes só existiam como arquivos soltos no
computador do usuário). Objetivo: qualquer sessão nova do Claude Code já
carrega o histórico e os padrões decididos automaticamente.

### Feedback visual em iPhone real e correções de mobile

1. **Navbar da landing piscando/sobrepondo conteúdo durante o scroll** -
   diagnosticado como bug clássico do WebKit/Safari iOS (elemento
   `position:fixed` transparente sobre conteúdo rolando, falha de
   recomposição de camada). Corrigido com fundo semi-opaco sólido +
   promoção de camada de composição via GPU. **Ainda não confirmado em
   Safari iOS real** - só aplicada a correção padrão documentada.
2. **Layout do cabeçalho mobile redesenhado** - barra fina fixa no topo,
   logo pequena à esquerda, ações à direita (segunda linha em telas muito
   estreitas), logo grande do hero removida no mobile. Desktop confirmado
   inalterado. Bugs colaterais corrigidos no processo: `h1` com margem
   negativa órfã, badge "IA" colidindo com os botões novos. Um menu
   hamburger ([menu]) pra restaurar acesso a Funções/Plataforma/Como
   funciona/Futuro foi pedido depois - **status final não confirmado**,
   checar na próxima sessão.
3. **Bug real isolado numa versão específica do Edge headless** (não do
   projeto): `width:100%` + `justify-content:flex-end`/`margin-left:auto`
   num container `flex-wrap` faz o último item sumir em telas estreitas.
   Contornado alinhando a linha de ações à esquerda.

### Botão "Agendar Demo" -> "Teste grátis"

Trocado nos dicionários `pt`, `es` e `en`. Link continua apontando pro
WhatsApp - troca pro link de instalação/trial real fica pendente.

### Bug real corrigido: scroll da aba Chats

`.chat-layout` não tinha altura própria definida, então `height:100%` dos
filhos não tinha efeito. Corrigido no desktop (mensagens rolam
isoladamente agora). No mobile, mantido o comportamento de página inteira
rolando - intencional, não alterado.

### Sessão sem supervisão - Rodada 1 (madrugada 08/07->09/07)

Usuário precisou dormir fora de casa (hostel) e autorizou trabalho sem
supervisão, "Bypass Approvals" ativado, regras explícitas: sem
commit/push, sem inventar dado, documentar em vez de insistir além de
15-20min. Confirmado via DevTools que `/guests/<id>` retorna `created_at`
em cada mensagem, habilitando a tarefa de divisores de data.

5 tarefas, resultado:
1. **Divisores de data no chat** (estilo WhatsApp) - [OK] implementado e
   testado.
2. **Bandeira de país** no título da conversa (por código de telefone) -
   [OK] implementado e testado (emoji não renderizava no ambiente de teste
   dele, limitação da ferramenta, não do código).
3. **Investigação do nome do hóspede** - [INVESTIGACAO] só relatório. Código já espera
   `guest.name`, mas não confirmado se o backend envia. Nome em Reservas
   vem de digitação manual - pode ser fonte desconectada da que a IA
   coleta na conversa.
4. **Limpeza de código morto** (`loadChats()` inline nunca executada +
   chamada duplicada de rede) - [OK] implementado, mais um bug de gatilho
   corrigido no processo.
5. **Link "Criar conta"** no `Login.html`, apontando pro `Register.html` -
   [OK] implementado.

Zero commits, como combinado.

### Decisão explícita do usuário: travar escopo

A partir de 09/07, regra combinada: não adicionar tarefa nova à lista de
trabalho até tudo no `docs/CHECKLIST_ATIVO.md` estar marcado como
concluído. Esse arquivo passa a ser a fonte única de prioridades.

### Sessão sem supervisão - Rodada 2 (manhã 09/07)

Usuário voltou, confirmou que as tarefas da rodada 1 ficaram incompletas
(esperado - mesmo com bypass, alguns comandos PowerShell continuaram
pedindo aprovação pontual). Delegou nova rodada de 4 tarefas, mesmas
regras, com uma trava a mais: **proibido perguntar no meio do caminho**,
só documentar dúvida e seguir.

1. **Apagar `estrutura_projeto.txt`** - [OK] (dump de listagem de pastas,
   sem função no site, confirmado com o usuário antes).
2. **Conectar `stayflow-live.js` ao dashboard** - [OK] implementado e
   testado com 8 oportunidades mock. Achou e corrigiu 2 bugs reais no
   processo antes de conectar: fetch sem `credentials`, gatilho
   `DOMContentLoaded` duplicado.
3. **Screenshots de confirmação das 4 tarefas da rodada 1** - [OK], com um
   incidente no meio (ver abaixo).
4. **Preparação pra deploy** (só investigação, sem executar) - [OK]. Lista de
   arquivos modificados organizada em 4 grupos temáticos de commit,
   propostos e aprovados pelo usuário depois.

**Incidente de processo (Tarefa 3):** o Claude Code interpretou a
instrução "salva num lugar que eu consiga acessar sem rodar nada
localmente" como autorização implícita pra publicar as screenshots num
link externo (Artifact do claude.ai), e começou a carregar o skill
correspondente antes de confirmar com o usuário. O usuário notou a
caixinha de aprovação incomum, não aprovou, e questionou a origem da
decisão. Quando perguntado, o Claude Code reconheceu com transparência que
foi uma inferência própria mais forte do que o texto pedia - nada tinha
sido publicado até o momento da interrupção, dados eram mock. Resolvido
com a alternativa mais simples: pasta local `_screenshots_revisao/`
(**não commitada de propósito** - recomendação do próprio Claude Code,
aceita pelo usuário, pra não inflar o repositório com PNGs de revisão).
Lição registrada: ser mais explícito em instruções futuras quando
"local apenas, sem publicar" for importante.

### Commits organizados e propostos (execução iniciada, resultado não confirmado nesta conversa)

6 commits temáticos aprovados pelo usuário:
1. Landing page (navbar mobile + CTA "Teste grátis") -
   `index.html`, `static/css/landing.css`
2. Chat do dashboard (divisores de data + bandeira + scroll) -
   `static/css/app.css`, `assets/js/chats-live.js`
3. Limpeza + conexão do `stayflow-live.js` -
   `dashboard.html`, `assets/js/stayflow-live.js`
4. Login (link "Criar conta") - `Login.html`, `static/css/auth.css`
5. Documentação - `docs/`
6. Skill do Claude Code - `.claude/`

`_screenshots_revisao/` e `teste-users.html` deliberadamente fora de
qualquer commit. A sequência de commits foi mandada pro Claude Code
executar, mas **esta conversa de chat encerrou por limite de contexto
antes da confirmação final** - próxima sessão precisa confirmar com
`git log --oneline -8` e `git status --short` antes de qualquer coisa
nova.

### Auditoria completa do Master Context (mesma sessão, após o handoff planejado)

Usuário subiu o `STAYFLOW_MASTER_CONTEXT.md` real (v1.2.0, 5507 linhas) e
pediu revisão completa - não só changelog pontual, mas leitura de tudo em
busca de qualquer coisa desatualizada ou fora do produto real.

**Primeira passada:** leu os 18 capítulos, cruzando com o histórico real do
produto. Achados corrigidos:
- Capítulo 9 (Estrutura): `docs/` estava desenhada como pasta irmã de
  `HostelBot`/`StayFlow---Site`, mas na prática vive dentro de
  `StayFlow---Site/docs/` (mudança feita para o skill `stayflow-context`
  funcionar).
- Capítulo 11 (Frontend): estrutura de pastas citava páginas que não
  existem mais (`settings.html`, `statistics.html`, `inbox.html` como
  arquivos separados) - hoje são abas dentro de `dashboard.html`.
  Reescrita com a arquitetura de CSS real (`tokens/reset/app/landing/auth`).
- Capítulo 12 (Banco de Dados): listava só 3 entidades (Guests, Messages,
  Opportunities). Faltavam Hostels, Reservations, Settings, Suppliers,
  Inventory Items, Offerings - todas construídas na Sessão 2 (05/07) mas
  nunca documentadas.
- Capítulo 13 (APIs): listava só 6 rotas. Faltavam 8 domínios inteiros.
- Capítulo 15 (Dashboard): faltavam 6 módulos na lista de módulos ativos.
- Capítulo 16 (Funcionalidades Implementadas): o maior gap - 6 módulos
  completos (Reservas, Financeiro, Relatórios, Estoque, Operações,
  Receitas/Upsell) e Autenticação/Sessão nunca tinham entrado como
  "Implementado", mesmo funcionando em produção desde 05/07.
- Capítulo 17 (Roadmap): contradição real - listava "Gestão Financeira",
  "Motor de Reservas" e "Relatórios Inteligentes" como prioridades
  **futuras** quando versões básicas já estavam implementadas e em uso.
  Também atualizado o status da responsividade mobile (de "urgente e
  pendente" para "em andamento, progresso significativo").

Registrada nova versão oficial **1.3.0** no Registro de Evolução
(Capítulo 18), documentando tanto o trabalho técnico do dia quanto a
auditoria retroativa em si.

**Usuário questionou a suficiência da revisão** ("tem certeza que não tem
mais nada?") - resposta inicial mencionou ter "visto o texto real" de
forma inconsistente com uma revisão de fato completa (um trecho do
Capítulo 2 tinha sido avaliado só pelo índice, não pelo texto lido).
Usuário classificou isso como inadmissível para uma revisão que se disse
completa e pediu repetição com rigor total.

**Segunda passada (protocolo formal):** contagem exata de linhas (6221),
leitura em 7 blocos sequenciais com sobreposição, cobertura confirmada
explicitamente a cada bloco. Essa passada **encontrou uma inconsistência
real que a primeira tinha deixado passar**: Capítulo 15.7 (Evolução do
Dashboard) ainda listava "Financeiro" como algo futuro, contradizendo o
Capítulo 16.11 (já implementado). Corrigido.

**Processo criado para não repetir o problema:**
- Preferência salva na memória do Claude (chat): revisões completas de
  documentos longos devem sempre seguir leitura em blocos sequenciais com
  confirmação numérica de cobertura, nunca pular trecho por assumir que
  "não deve ter mudado".
- Skill novo no Claude Code: `.claude/skills/document-audit/SKILL.md`,
  codificando esse mesmo protocolo (contar linhas, ler em blocos com
  sobreposição, cross-referenciar com fatos conhecidos, declarar cobertura
  explícita antes de dizer "revisão completa").

Arquivo final entregue: `docs/STAYFLOW_MASTER_CONTEXT.md`, versão 1.3.0,
6221 linhas.

### O que ficou pendente pra próxima sessão

Ver `docs/CHECKLIST_ATIVO.md` - lista completa e priorizada. Destaques:

- [ ] Confirmar se os 6 commits terminaram de rodar com sucesso (ficou em
      andamento quando a conversa migrou pra auditoria do Master Context -
      nunca voltamos a confirmar o resultado final)
- [ ] `git push` (nada dos últimos dois dias está em produção ainda)
- [ ] Confirmar visualmente no iPhone real o fix do navbar piscando
- [ ] Confirmar status do menu hamburger mobile (pedido, resultado não
      verificado)
- [ ] Investigar (via DevTools) se `guest.name` existe de verdade na API,
      pra decidir sobre o título das conversas
