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

---

## SESSÃO 4 - 13/07/2026

### Contexto no início da sessão

Retomando depois do fim de semana (última entrada foi sexta, 11/07). Primeira
tarefa: confirmar se os 6 commits da Sessão 3 realmente completaram — a
conversa anterior tinha encerrado por limite de contexto antes da
confirmação final.

### Confirmação dos 6 commits pendentes + commit 7

`git log --oneline -8` e `git status --short` confirmaram: os 6 commits
completaram com sucesso, na ordem planejada, sem erro. Working tree limpa
(só `_screenshots_revisao/` e `teste-users.html` fora, como esperado).
Feito um 7º commit (`c4e343e`) juntando a atualização de docs (diário +
master context) com o skill `document-audit` que tinha ficado sem commit.

### Descoberta e correção: divergência entre `main` e `arquitetura-v2`

Ao tentar mesclar `arquitetura-v2` → `main` no `StayFlow---Site`, o merge
falhou: `Login.html` no working tree não batia com nenhuma das duas
branches. Investigação revelou a causa raiz: **o mesmo bug de
`login.html`/`Login.html` duplicado no índice do Git (já corrigido na
`arquitetura-v2` na Sessão 3) nunca tinha sido corrigido na `main`** —
o Windows não distingue maiúsculas/minúsculas no disco, mas o Git
rastreava os dois como arquivos separados, e o checkout ficava
sobrescrevendo um pelo outro. Corrigido com `git rm --cached login.html`
na `main`. Depois disso, merge fast-forward limpo, push feito.

Durante a investigação, um arquivo "misterioso" apareceu no meio do
processo — conteúdo de `Login.html` que não batia com nenhuma versão
commitada (CSS inline, login via `localStorage`, incompatível com a
arquitetura de sessão de servidor atual). Salvo em
`Login_MISTERIOSO_BACKUP.html` (não commitado, não identificado pelo
usuário — pode ser um rascunho antigo esquecido em algum editor). Resolvido
descartando o conteúdo não commitado do `Login.html` de verdade e seguindo
com o merge.

### Infraestrutura Render: serviço órfão descoberto e removido

Investigação revelou **dois projetos no Render**: "My project" (contém o
`HostelBot`, Web Service real) e "Stayflowsolutions Site" (continha um
Static Site órfão chamado "StayFlow Site", puxando direto do repositório
`StayFlow---Site`/branch `main`, sem domínio customizado, só acessível via
`stayflow-site.onrender.com`). Confirmado via checagem cruzada (webhook do
WhatsApp na Meta aponta pra `stayflowsolutions.com`; DNS na Cloudflare tem
só 2 registros, ambos apontando pro `HostelBot`) que esse serviço não tinha
nenhuma função real — sobra de uma fase anterior do projeto. **Deletado**
com segurança, após confirmação dupla (Meta + Cloudflare).

**Aprendizado de arquitetura registrado:** o frontend não chega em
produção pelo `StayFlow---Site` sozinho — existe uma cópia física dentro
de `HostelBot/StayFlow---Site/` (via `xcopy`/`robocopy`), e é essa cópia
que o Render de fato builda. Todo commit no frontend precisa ser replicado
manualmente pro `HostelBot` (copiar arquivo → commit → push) pra chegar em
produção. Isso gerou fricção real ao longo do dia (mudanças feitas duas
vezes) — o usuário identificou isso como retrabalho estrutural e pediu um
processo mais direto; decisão de arquitetura de longo prazo (separar
frontend como Static Site próprio + backend como API pura em subdomínio)
registrada no Roadmap como item a resolver quando o operacional estiver
fechado.

### Deploy real dos 8 commits pendentes

Após corrigir a divergência de branches, xcopy completo (`/MIR`) do
`StayFlow---Site` pra dentro do `HostelBot`, removendo arquivos obsoletos
(`dashboard2.html`, `estrutura_projeto.txt`, `test-users.html`, 6 CSS
órfãos, versão antiga de `templates/dashboard.html`) e trazendo a
estrutura de CSS modular completa. Commit e push no `HostelBot`
(`7b5569a`) — **deploy confirmado em produção pela primeira vez desde a
Sessão 3**.

Confirmado visualmente: botão "Teste grátis" no navbar mobile, link
"Criar conta" funcional. **Navbar mobile testado em Safari real no iPhone
do usuário** (pendência da Sessão 3): fica translúcido de forma estável
durante scroll rápido, sem piscar — fix confirmado funcionando.

### Descoberta: arquivos de IA de sessão anterior nunca foram commitados

Durante a sincronização, `git status` no `HostelBot` revelou 3 arquivos
modificados desde antes desta sessão: `routes/chat.py`,
`services/ai_service.py`, `services/memory_service.py` — o ajuste de tom
mais natural e janela de histórico maior, mencionados como já feitos na
introdução da Sessão 3, **na verdade nunca tinham sido commitados nem
testados de ponta a ponta com número real**. Decisão: deixar
`memory_service.py` de fora por enquanto (não testado), mas usar
`ai_service.py`/`chat.py` como base pra construir a próxima feature em
cima.

### Feature nova: captura do nome do hóspede via function calling

Investigação completa (consulta ao banco de produção real via Shell do
Render, leitura de `ai_service.py`/`chat.py`/`guest_service.py`/
`database.py`) confirmou a suspeita registrada desde a Sessão 3: o campo
`guests.name` nunca era preenchido pelo fluxo real — a IA perguntava o
nome (só texto livre no prompt), mas a resposta se perdia no histórico da
conversa sem nenhum ponto de extração.

**Implementado:** `ask_ai()` em `ai_service.py` passou a usar *function
calling* da OpenAI — uma ferramenta `save_guest_name` que o modelo aciona
quando reconhece o nome do hóspede na conversa. `process_incoming_message`
em `chat.py` desempacota a tupla `(resposta, nome_extraído)` e chama a
nova função `update_guest_name()` (`database.py`) quando o nome vem
preenchido. Testado localmente (hóspede de teste) e depois **com número
real de WhatsApp** — o hóspede "Denis Targansky" teve o nome capturado e
gravado corretamente no banco de produção, confirmado via Shell do Render.
Commit `55ab673`, deploy confirmado.

**Efeito colateral identificado e aceito:** como `ai_service.py` já tinha
as mudanças de tom/telefone da sessão anterior, o commit da captura de
nome inclui essas mudanças juntas — testadas pela primeira vez em conjunto
no teste real.

**Frontend conectado em seguida:** `routes/chats.py` passou a incluir
`g.name` no `SELECT` da rota `/chats` (commit `d1648b0`); `chats-live.js`
passou a usar `chat.name || chat.phone` na lista de conversas e
`guest.name || guest.phone` no título da conversa aberta (commit
`b848aef`, sincronizado pro `HostelBot` como `e6cde0a`). Confirmado em
produção: conversas com nome capturado após a feature mostram o nome;
conversas anteriores à feature continuam mostrando telefone (comportamento
aceito pelo usuário, não é retroativo).

### Limpeza de dado: renomeação do hostel de demonstração

Esclarecido pelo usuário: o hostel `id=1` (hoje "StayFlow",
`caiocfacosta@icloud.com`) não é o Hostel Lagares real — é a conta pessoal
de demonstração de vendas do usuário. Confirmado via Shell do Render que
essa renomeação **já tinha sido feita em produção numa sessão anterior não
documentada** (o banco local do PC, desatualizado, ainda mostrava
"Lagares"/e-mail antigo — reforça a lição já registrada de nunca confiar
no banco local pra fatos de dado real). Decisão registrada: o Hostel
Lagares real vai ganhar cadastro, login e número de WhatsApp próprios,
separados, quando o usuário tiver os dados dele prontos.

### Auditoria completa do menu de Configurações

Investigação de código (sem suposição, cruzando backend e frontend linha
por linha) revelou o estado real por trás dos 9 botões de categoria
(Geral, Empresa, IA, Comunicação, Integrações, Equipe, Segurança, Billing,
Developer):

- **Geral e WhatsApp Business:** 100% funcionais, com backend real
  (`routes/settings.py`) e frontend conectado (`hydrateSettingsFromBackend`,
  `saveWhatsappSettings`/`loadWhatsappSettings`).
- **Os 9 botões de categoria são só visuais** — `bindSettingsMenu()` troca
  apenas uma classe `.active`, sem trocar conteúdo. Todos os cards
  (Geral, WhatsApp, IA) sempre aparecem juntos na mesma tela.
- **Card "IA StayFlow" tem bug real:** os checkboxes (`auto_reply`,
  `opportunity_generation`) são enviados pro backend via `POST /settings`,
  mas a rota só grava `hostel_name/hostel_type/checkin/checkout` — os dois
  valores se perdem silenciosamente. Identificado, não corrigido ainda.
- **Painel de Equipe (`#teamOverlay`/`#teamPanel`/`#teamListContainer`)
  nunca teve o HTML criado** — só o JavaScript existe
  (`openTeamPanel`/`closeTeamPanel`/`loadTeamList`, funcional e testado
  contra `/users`). Bug pré-existente (não introduzido hoje), confirmado
  reproduzindo o erro clicando no avatar da sidebar antes de qualquer
  mudança da sessão.
- **"Status do sistema" mostrava texto fixo enganoso** ("Backend:
  aguardando conexão", "WhatsApp não conectado") mesmo com tudo
  funcionando de verdade.

**Corrigido e deployado nesta sessão:**
1. Status pills passaram a refletir o estado real (lido de
   `hydrateSettingsFromBackend`/`loadWhatsappSettings`) — 2 commits
   (um com bug de ordem, corrigido no segundo: `efbb58c`/`f5cceff`).
2. Botão "Equipe" do menu passou a chamar `openTeamPanel()` (commit
   `b9cf00b`/`74c0d4f`) — isso **expôs** (não causou) o bug pré-existente
   do painel sem HTML, confirmado reproduzindo o mesmo erro pelo avatar da
   sidebar.

### Pesquisa de integrações OTA (Booking.com / Airbnb)

Pesquisa web confirmou: **tanto Booking.com quanto Airbnb têm acesso de
API fechado hoje pra desenvolvedores pequenos/independentes** —
Booking.com pausou novas inscrições de Connectivity Partner; Airbnb só
convida parceiros selecionados, sem processo de inscrição aberto. Conexão
direta descartada como caminho viável no curto prazo.

Alternativas mapeadas: iCal (grátis, só sincroniza disponibilidade, não
captura dados completos da reserva); channel manager pago (Beds24
confirmado como parceiro oficial da Booking/Airbnb/VRBO, a partir de
~€15,90/mês + ~€0,55/mês por canal, mas não confirmado se acesso via API
exige plano superior); **e-mail** (ideia do usuário — ler os e-mails de
confirmação que OTAs já mandam pro hostel, extrair dados via IA, mesmo
padrão já usado no WhatsApp — não exige aprovação de parceiro nenhuma).

**Decisão:** priorizar o caminho de e-mail quando essa frente for
atacada, mas **só depois do operacional (Configurações, Equipe) estar
100% fechado** — registrado no roadmap represado.

### Início da Fase 1: sistema de permissões multi-hostel

Ao corrigir o botão "Equipe", o usuário deixou claro que "função de
funcionário" não pode ser um recurso pela metade — precisa ser um sistema
completo de permissões, com: (1) uma pessoa podendo ter login em mais de
um hostel/hotel (estilo troca de conta do Instagram/Facebook, sem
re-logar), e (2) o admin podendo tanto definir permissões por função
quanto sobrescrever individualmente por funcionário (exceções pontuais,
ex: cobrir a falta de alguém).

**Arquitetura desenhada e aprovada** (modelo "workspace", como
Slack/Notion): `users` vira identidade pura (nome, e-mail único global,
senha) — deixa de ter `hostel_id`/`role` própprios. Nova tabela
`hostel_memberships` liga pessoa a hostel com uma função. Nova tabela
`roles` (por hostel, nome + lista de permissões configurável pelo admin,
catálogo de 10 seções: dashboard, chats, opportunities, reservations,
operations, guests, finance, inventory, revenue, settings). Nova tabela
`membership_permission_overrides` pras exceções individuais por cima da
função.

**Fase 1 (schema) implementada e testada nesta sessão:**
- 3 tabelas novas criadas em `create_database()` (`database.py`), no
  mesmo padrão das tabelas existentes.
- `_users_table_needs_migration()`/`_migrate_users_to_memberships()`
  escritas seguindo exatamente o padrão já usado pra migração de `guests`
  (Sessão 3): detecta schema antigo, migra dado preservando tudo, sem
  perda.
- **Bug pego e corrigido antes de qualquer risco:** a primeira versão da
  migração promovia todo mundo pra função "Admin" com acesso total,
  ignorando o `role` original — corrigido pra usuários com `role='admin'`
  virarem "Admin" (tudo liberado) e qualquer outro valor virar "Staff"
  **sem permissão nenhuma por padrão** (admin decide depois, não o
  sistema).
- Testado de ponta a ponta numa cópia isolada do banco (via
  `STAYFLOW_DATA_DIR` apontando pra pasta temporária), nunca contra o
  banco real — confirmado que preserva dados, migra corretamente o
  usuário admin real e os dois usuários de teste "staff" pré-existentes.
- Backup de segurança do banco de produção feito no Shell do Render antes
  de qualquer trabalho de schema (`stayflow_backup_pre_membership_migration.db`,
  em `/var/data/`).

**Não commitado, não deployado.** Fica só local, testado. Fases 2
(backend: reescrever `login()`/`register()` pra suportar múltiplos
hostels + troca de conta sem senha + rotas de `roles`/`memberships`) e 3
(frontend: seletor de conta, painel de Equipe reconstruído do zero,
navegação filtrada por permissão) ficam pra sessão futura.

### Padrões de trabalho estabelecidos nesta sessão

- **Um comando por vez, sempre esperando confirmação** antes de mandar o
  próximo pro Claude Code — regra explícita do usuário, quebrada uma vez
  no meio da sessão e corrigida.
- **Nenhuma funcionalidade pela metade** — corrigir um botão não é só
  ligá-lo a uma tela existente incompleta; o recurso completo (ex:
  cadastro de funcionário + permissões) precisa sair pronto, mesmo que
  isso signifique dividir o trabalho em fases maiores.
- Uso de `conversation_search` (busca em conversas passadas) antes de
  re-investigar código do zero, quando aplicável — evita retrabalho de
  descoberta já feita em sessão anterior.

### O que ficou pendente pra próxima sessão

- [ ] Fase 2 e 3 do sistema de permissões multi-hostel (backend + frontend
      completos, ver seção acima)
- [ ] Corrigir bug do card "IA" em Configurações (checkboxes que o backend
      ignora silenciosamente)
- [ ] `services/memory_service.py` — ainda não commitado, não testado com
      WhatsApp real (`HISTORY_WINDOW=60`, herda da Sessão 3)
- [ ] Reconstruir "assumir conversa" (botão de resposta manual) — mencionado
      pelo usuário, deliberadamente adiado pra depois da captura de nome,
      depois adiado de novo pro final da sessão
- [ ] Cadastrar o Hostel Lagares real (login + número de WhatsApp
      próprios, separados da conta de demonstração)
- [ ] Preencher `hostels.phone` (continua `NULL` em produção — confirmado
      que não bloqueia o roteamento real do webhook, que usa
      `whatsapp_phone_number_id`, mas fica pendente por organização)
- [ ] Corrigir dropdown de idioma cortado no mobile — bug real confirmado,
      deliberadamente adiado pra fase de lapidação visual (evitar
      retrabalho, já que o layout mobile vai ser reorganizado)
- [ ] Visual do Login — decidido seguir o mesmo padrão de fundo com mapa
      mundi já usado no `Register.html` (substitui a ideia antiga de "logo
      pequena + fundo ondulado")
- [ ] Botão "Teste grátis" ainda linka pro WhatsApp — decidir quando trocar
- [ ] Decidir arquitetura definitiva de deploy (frontend como Static Site
      próprio + backend como API em subdomínio) pra eliminar o xcopy manual
- [ ] Integração por e-mail com OTAs (Booking/Airbnb/Hostelworld) — só
      depois do operacional 100% fechado
- [ ] `Login_MISTERIOSO_BACKUP.html`, `_screenshots_revisao/`,
      `teste-users.html` continuam fora do Git, sem resolução
- [ ] Faxina de pastas locais (`Archive_old/`, `Audit_old/`,
      `backups_old/`) — ainda não feita
- [ ] Decidir destino de `templates/components/` — ainda sem decisão

---

## SESSÃO 5 - 14 a 19/07/2026

### Contexto no início da sessão

Continuação direta da Sessão 4, através de várias pausas reais do usuário
(algumas de um dia inteiro). Objetivo único, declarado logo no início:
terminar por completo o sistema de permissões multi-hostel que ficou como
Fase 1 (schema) na sessão anterior — Fases 2 (backend) e 3 (frontend),
sem deixar nada pela metade, do jeito que o usuário passou a exigir
explicitamente a partir de hoje.

### Correção de processo: memória de preferências

Uma ferramenta usada em turnos anteriores para salvar preferências
(`memory_user_edits`) parou de existir/retornou erro. Corrigido migrando
essas preferências para o sistema de memória real (arquivo
`/preferences.md`), preservando tudo que já tinha sido registrado.

### Padrões de trabalho reforçados nesta sessão (o usuário cobrou cada um deles em algum momento)

- **Revisar o próprio código antes de mandar pro Claude Code**, não só
  depois que o usuário perguntar "tem certeza?". Isso pegou bugs reais
  repetidas vezes antes de eles chegarem a existir no código (ver lista
  abaixo).
- **Um comando por vez**, nunca empilhar instruções.
- **Nenhuma funcionalidade pela metade** — levado ao extremo hoje: o que
  começou como "só ligar o botão Equipe" virou a construção completa de
  um sistema de identidade + múltiplos hostels + funções + exceções
  individuais, porque o usuário recusou qualquer atalho parcial.
- **Não repetir investigação já feita** — checar o que já foi confirmado
  na própria conversa antes de pedir novo comando.

### Fase 2 (Backend) — construída e testada peça por peça

**Núcleo de cálculo de permissão** (`database.py`): `get_membership()`,
`get_effective_permissions()` (função + exceções individuais combinadas
em tempo real, nunca cacheado). Testado isoladamente com 4 cenários
(admin com tudo, staff sem nada, staff com exceção pontual, pessoa sem
vínculo) antes de qualquer coisa depender dele.

**Decorator `@require_permission`** (`utils/tenant.py`) — verifica
permissão a cada requisição, sempre recalculada do banco (decisão
explícita do usuário: "fazemos da forma correta, não a mais rápida").
Testado com Flask de verdade (não só função isolada): bloqueio sem
sessão, bloqueio por falta de permissão específica, liberação por
exceção individual, liberação total do admin.

**Identidade e múltiplos hostels** (`database.py`): `get_hostel()`,
`get_user_by_email()`, `get_user_by_id()`, `get_user_hostels()`,
`create_identity_and_hostel()` (transação real, com rollback testado
forçando um e-mail duplicado no meio da criação — confirmado que nada
fica órfão no banco).

**`routes/auth.py` reescrito por completo** — `login()`/`register()`
adaptados ao novo modelo, `select_hostel()` novo (finaliza a escolha de
hostel, serve tanto pro primeiro login com múltiplas contas quanto pra
trocar de hostel depois, sem senha nova), `/me` expandido (devolve
permissões calculadas + lista de outros hostels). **Revisão própria
pegou 3 problemas antes de mandar**: campos que sumiriam da sessão e
quebrariam `utils/tenant.py`; erro de concorrência não tratado no
registro simultâneo; decisão de `must_change_password` que eu tinha
mudado sem avisar. Depois, por pedido do usuário ("vamos terminar tudo
hoje"), a camada de compatibilidade com o frontend antigo foi removida —
simplificação consciente, sabendo que trava tudo até a Fase 3 terminar.
Testado via `app.test_client()` real: registro, logout, `/me` sem
sessão, senha errada, login com 1 hostel, login com múltiplos hostels
(devolve lista), tentar escolher hostel que não é seu (403), escolher
hostel válido, trocar de hostel já logado sem senha nova.

**Conversão das 13 rotas antigas** de `@require_auth` pra
`@require_permission`, uma chave por arquivo. Descoberta no processo:
faltavam 2 permissões no catálogo original de 10 (`reports` e `team`,
esse último criado depois de uma conversa sobre separar "editar
configurações gerais" de "gerenciar equipe") — catálogo final com 12
chaves, centralizado em `utils/permissions.py` (`ALL_PERMISSIONS`,
`PERMISSION_LABELS`), fonte única de verdade reaproveitada por
migração, decorator, rotas e frontend.

**`routes/team.py` (novo, 9 rotas)** — CRUD de funções, listar/convidar/
trocar função/exceção individual/desativar/reativar equipe, mais
catálogo de permissões e detalhe de origem por pessoa
(`/permissions-detail`, separa "vem da função" de "foi ajustado
manualmente" — pedido explícito do usuário, "nível de empresa
multinacional", não a versão simplificada que eu tinha sugerido primeiro
por ser mais rápida).

**Proteções de segurança construídas com o usuário aprovando cada
decisão antes**: nenhuma mudança pode deixar um hostel sem ninguém com
permissão `team` (checado em troca de função, exceção individual e
desativação — `check_team_permission_safety`); função só pode ser
apagada sem nenhum vínculo restante, **ativo ou inativo** (bug pego na
própria revisão antes de mandar: a primeira versão só checava vínculos
ativos, deixaria gente desativada com referência quebrada, sumindo
silenciosamente da listagem).

**Limpeza**: as rotas antigas e quebradas `POST`/`GET /users` em
`routes/settings.py` (usavam colunas que não existem mais desde a
migração da Sessão 4) foram removidas, junto do `import bcrypt`/
`hash_password` que só existiam pra sustentar elas.

### Bugs pegos na revisão própria antes de qualquer código ir pro Claude Code (lista consolidada)

- Import redundante de `ALL_PERMISSIONS_STR` duplicado (topo do arquivo
  + dentro de função).
- Concorrência não tratada em `create_role`/`update_role` (nome
  duplicado gerava erro cru em vez de mensagem clara).
- Nome de função/pessoa injetado direto dentro de atributo `onclick` —
  quebraria com aspas duplas no nome; corrigido buscando o dado por id
  numa lista já carregada, em vez de embutir texto no HTML.
- Duplo escape: `escapeHtml()` aplicado num texto que já ia por
  `.textContent` (que já é seguro por natureza) — mostraria códigos HTML
  literais na tela.
- `ON CONFLICT ... DO UPDATE` (sintaxe SQLite recente, nunca testada no
  ambiente) trocada por `SELECT` + `UPDATE`/`INSERT` manual, garantido
  de funcionar em qualquer versão.
- Especificidade de CSS: `.collapse-menu{display:none}` perdendo pra
  `.menu button{display:flex}` por ser menos específico — corrigido com
  `.menu button.collapse-menu`.

### Fase 3 (Frontend) — construída em cima do backend testado

**`Login.html`** — card novo (`#hostelSelector`) que aparece quando o
login devolve `needs_hostel_selection: true`, listando os hostels como
botões; escolher um chama `/select-hostel` e só então redireciona.

**3 bugs reais encontrados por revisão própria, não por reclamação do
usuário**: `window.STAYFLOW_USER` guardava só o pedaço `user` da
resposta do `/me`, perdendo `hostel_name`/`role_name` que vêm no nível
acima — os 3 campos da sidebar (nome do hostel, e-mail do hostel, função
da pessoa) sempre mostravam texto de fallback fixo, nunca o dado real.
Corrigido introduzindo `window.STAYFLOW_SESSION` (resposta completa do
`/me`), usado por tudo que precisa desses dados daqui pra frente.

**Seletor de conta na sidebar** (`.hostel-selector-wrap`, dropdown) —
corrigido um bug de posicionamento (`position:relative` faltando no
invólucro, o dropdown abriria em lugar errado da tela) antes de mandar.
Testado com 2 hostels reais (vínculo criado direto no banco de teste
pra simular): lista os dois, marca o ativo, troca funciona (recarrega a
página, hostel novo ativo, permissões recalculadas corretas pro novo
contexto).

**Painel de Equipe reconstruído do zero** (o HTML nunca tinha existido,
confirmado na Sessão 4) — 2 abas (Equipe/Funções), modal genérico
reutilizável (`openGenericModal`/`closeGenericModal`, usado por convite,
trocar função, criar/editar função, exceções individuais — evita
duplicar CSS/JS pra cada formulário). Convite gera senha temporária
mostrada uma única vez na tela. Cada card de pessoa tem botões pra
trocar função, editar exceções individuais (com a distinção visual
"herdado da função" vs "ajustado manualmente", vinda da rota
`/permissions-detail`), desativar/reativar. Cada card de função tem
editar (com os 12 checkboxes) e apagar.

**Menu lateral**: reordenado por prioridade de uso real (o usuário pediu
uma lista priorizada antes de aprovar a ordem final), "Equipe" virou
item de primeira classe (antes só existia via clique no avatar), e
passou a esconder itens conforme a permissão real da pessoa logada
(`hideNavItemsWithoutPermission`, lida do `/me`).

### Lição de processo aprendida no meio dos testes: reiniciar o servidor

Mudança em arquivo Python (`database.py`, `routes/`) só é lida pelo
Flask quando o processo reinicia — diferente de HTML/CSS, sempre lido
fresco a cada carregamento de página. Um teste deu "modal vazio" porque
o servidor local ainda estava com o backend de antes das rotas novas
existirem; resolvido matando o processo antigo e subindo de novo.
Registrado como lembrete permanente pro resto da sessão.

### Testes finais confirmados pelo usuário, na interface real (não só backend isolado)

Login com múltiplos hostels mostrando a tela de escolha; editar e
apagar função (incluindo a proteção contra apagar função com gente
vinculada); trocar função de uma pessoa; exceção individual persistindo
corretamente (reaberto depois, a mudança continuava lá); login com
conta sem ser admin mostrando o menu lateral filtrado, só com os itens
permitidos pela função dela.

### Publicação em produção

Dois commits em cada repositório (frontend `StayFlow---Site` e backend
`HostelBot` com xcopy sincronizado), todos com o mesmo cuidado de
sempre (`git status` conferido antes de cada `add`, `services/
memory_service.py` mantido de fora por ser frente não relacionada e
ainda não testada). Deploy confirmado em produção: a migração de banco
rodou pela primeira vez contra dado real (com backup de segurança feito
na Sessão 4, nunca precisou ser usado), a conta real do usuário
continuou funcionando, e a função dela apareceu corretamente como
"Admin" com as 12 permissões.

### Assuntos levantados pelo usuário, registrados mas não atacados nesta sessão

- **Reorganizar o cabeçalho**: mover hostel/usuário da sidebar pro topo
  à direita (onde hoje fica "+ Nova reserva"), e "Nova reserva" virar
  botão flutuante empilhado com o "Ask StayFlow". Adiado de propósito
  pra não misturar com a reordenação do menu (risco de não saber qual
  mudança quebrou o quê, se algo desse errado).
- **Reserva criada via modal flutuante**, reaproveitando o mesmo padrão
  de modal genérico construído hoje, em vez de navegar pra outra tela.
- **"Assumir conversa" (Ask StayFlow) virar agente de verdade** — a
  intenção do usuário é a IA conseguir agir sobre o sistema durante a
  conversa (ex: "chegou uma compra de 50 toalhas" atualizando o estoque
  sozinho), usando o mesmo mecanismo de function calling já validado na
  captura de nome do hóspede. Reconhecido como grande iniciativa nova,
  fora do escopo de hoje — o próprio usuário concordou em adiar depois
  de eu apontar que já estava registrada no caderno dele como "Fase 2"
  represada.
- **Traduções inconsistentes fora da landing page** — usuário percebeu
  que o dashboard não tem o mesmo sistema de tradução central que a
  landing page (`index.html`) já tinha; funciona em alguns lugares,
  falha em outros. Quer adicionar francês, alemão e possivelmente
  japonês depois — decisão registrada de corrigir a arquitetura de
  tradução primeiro (senão os novos idiomas multiplicam o problema em
  vez de resolver).

### O que ficou pendente pra próxima sessão

- [ ] Reorganizar cabeçalho (hostel/usuário pro topo, "Nova reserva" como
      botão flutuante)
- [ ] Criar reserva via modal flutuante, sem navegar pra outra tela
- [ ] Corrigir bug do card "IA" em Configurações (checkboxes que o
      backend ainda ignora silenciosamente — não atacado nesta sessão)
- [ ] Decidir destino das 5 categorias vazias de Configurações (Empresa,
      Comunicação, Segurança, Billing, Developer)
- [ ] Investigar e corrigir a arquitetura de tradução do dashboard antes
      de adicionar francês/alemão/japonês
- [ ] Transformar "Ask StayFlow" num agente real com function calling
      (grande iniciativa nova, represada)
- [ ] `services/memory_service.py` — ainda não commitado, não testado com
      WhatsApp real
- [ ] Cadastrar o Hostel Lagares real (login + número de WhatsApp
      próprios)
- [ ] Preencher `hostels.phone` (organização, não bloqueia nada)
- [ ] Corrigir dropdown de idioma cortado no mobile — adiado pra fase de
      lapidação visual
- [ ] Visual do Login — fundo com mapa mundi (padrão do `Register.html`)
- [ ] Botão "Teste grátis" ainda linka pro WhatsApp
- [ ] Decidir arquitetura definitiva de deploy (eliminar o xcopy manual)
- [ ] Integração por e-mail com OTAs — só depois do operacional 100%
      fechado
- [ ] `Login_MISTERIOSO_BACKUP.html`, `_screenshots_revisao/`,
      `teste-users.html` continuam fora do Git
- [ ] Faxina de pastas locais (`Archive_old/`, `Audit_old/`,
      `backups_old/`)
- [ ] Decidir destino de `templates/components/`

---

## SESSÃO 6 - 21/07/2026

### Contexto no início da sessão

Continuação direta da Sessão 5 (que terminou com o sistema de
permissões multi-hostel publicado em produção). Objetivo: reorganização
visual do cabeçalho do Dashboard (item que já estava planejado como
próximo passo), seguido de correção do bug conhecido do card "IA" em
Configurações.

### Padrão de trabalho ajustado nesta sessão

O usuário pediu explicitamente pra combinar o máximo de trabalho
seguro numa instrução só, em vez de fatiar em muitos ciclos — motivado
por limite de tempo/mensagens no Claude Code. Isso mudou o ritmo: menos
investigação incremental, mais instruções completas de uma vez,
mantendo os mesmos princípios de segurança (checagem prévia de texto
único antes de editar, revisão própria antes de mandar).

### Reorganização dos botões flutuantes

Unificação visual dos dois botões flutuantes ("Ask StayFlow" e "Nova
reserva"), que hoje tinham formatos e tamanhos incompatíveis (140px
transparente vs recém-criado 56px sólido). Processo iterativo, com
vários ajustes visuais em cima do resultado renderizado (não dava pra
acertar de primeira sem ver na tela):

- Ambos padronizados no mesmo tamanho, cantos arredondados com o token
  oficial `var(--radius)`, fundo azul idêntico.
- A logo do "Ask StayFlow" (antes um `<img>` colorido) recolorida via
  `mask-image` do CSS para a cor de fundo escura do dashboard
  (`#06101b`), criando um efeito de "recorte" sobre o azul do botão —
  técnica nova no projeto, nunca usada antes.
- Confirmado por análise real do arquivo (`PIL`/Pillow) que `logo2.png`
  tem transparência real (RGBA) e que a margem transparente ao redor
  do desenho é praticamente simétrica (12px vs 10px, de 1536px de
  largura) — o desalinhamento percebido visualmente era causado por
  distorção de proporção (`mask-size` forçando os dois eixos ao mesmo
  valor numa imagem não-quadrada, 1536×1024), não por deslocamento
  real do arquivo. Corrigido usando `auto` num dos eixos do
  `mask-size`, deixando o CSS calcular a proporção certa.
- Tamanho final do botão centralizado numa variável CSS nova
  (`--floating-btn-size`, em `tokens.css`), pra qualquer ajuste futuro
  ser uma mudança de 1 número, não reescrita de 3 blocos.
- Todo o processo de ajuste fino (tamanho da logo, posição, cor do
  ícone "+") envolveu bastante tentativa-e-erro guiado por
  print/feedback visual direto do usuário — sem tentar resolver por
  cálculo puro depois da primeira rodada.

### Reorganização do cabeçalho: hostel/usuário movidos pro topbar

O card de hostel e o card de usuário, antes empilhados verticalmente
na barra lateral (dentro de `.sidebar-profile`, com o botão "Sair"
solto embaixo), foram movidos para a faixa horizontal do topbar, ao
lado do sino de alertas.

Decisão de design: o avatar do usuário deixou de abrir o painel de
Equipe diretamente e passou a abrir um menu suspenso pequeno, com 2
opções — "Equipe" (escondida automaticamente se a pessoa não tiver a
permissão `team`, reaproveitando `hideNavItemsWithoutPermission`) e
"Sair" (que antes só existia como botão solto na sidebar, agora tem um
lugar definido). O dropdown do hostel continua com a mesma lógica de
antes (trocar de conta), só realocado.

Achado durante a investigação (não corrigido, registrado): o clique no
avatar do usuário sempre abriu o painel de Equipe sem checar
permissão — diferente do item "Equipe" do menu lateral, que já usa
`hideNavItemsWithoutPermission`. Não é falha de segurança (o backend
bloqueia certo com 403), só inconsistência de UX. Resolvido de
propósito nesta sessão ao construir o novo menu suspenso (o item
"Equipe" dentro dele agora sim respeita a permissão).

### Correção do bug do card "IA" em Configurações

Bug já identificado numa auditoria anterior (Sessão 4): os checkboxes
"Resposta automática" e "Geração de oportunidades", dentro do card de
IA em Configurações, pareciam salvar (nenhum erro na tela), mas o
backend nunca gravava esses dois valores — a rota só persistia 4
campos (nome, tipo, checkin, checkout). Investigação nesta sessão
revelou uma camada extra mascarando o problema: `saveSettingsToLocal()`
grava a resposta inteira do formulário no `localStorage` antes mesmo
da chamada ao servidor — então, depois de salvar e recarregar, os
checkboxes apareciam exatamente como deixados, dando falsa sensação de
persistência real.

Separado em dois destinos diferentes, por decisão consciente:

- **"Geração de oportunidades"**: corrigido de ponta a ponta.
  Adicionada coluna `opportunity_generation` em `settings` (padrão
  ligado, preserva comportamento de quem nunca mexeu). `GET`/`POST
  /settings` passam a ler/gravar de verdade. A chamada de
  `analyze_message()` em `routes/chat.py` (que rodava sempre,
  incondicional) passou a checar essa preferência antes de executar.
  Testado com mensagem real simulando reserva urgente, hostel com a
  preferência desligada: a IA respondeu normalmente ao hóspede, mas
  zero oportunidade nova foi criada — confirma que o desligamento tem
  efeito real, não é cosmético.
- **"Resposta automática"**: decidido não fingir uma correção — esse
  checkbox só faria sentido de verdade com um mecanismo de aprovação
  humana antes de enviar (o "assumir conversa"/Ask StayFlow agente,
  ainda não construído). Em vez de salvar um valor sem efeito nenhum,
  o checkbox foi desabilitado visualmente, com texto explicando o
  motivo ("Em breve — depende do recurso de assumir conversa").

### Correção de processo: instruções corrigidas sempre completas

O usuário identificou e corrigiu um hábito ruim: ao revisar e corrigir
uma instrução já enviada, só a parte alterada estava sendo reenviada,
pedindo pro usuário juntar manualmente com a mensagem anterior.
Registrado como regra permanente: toda correção deve vir como bloco
completo e autocontido, nunca como fragmento pra colar em cima de algo
já mandado.

### O que ficou pendente pra próxima sessão

- [ ] Publicar em produção o trabalho desta sessão (cabeçalho
      reorganizado, botões flutuantes unificados, correção do
      checkbox de oportunidades) — commit/push feitos ao final desta
      sessão, deploy a confirmar
- [ ] Decidir destino das 5 categorias vazias de Configurações
      (Empresa, Comunicação, Segurança, Billing, Developer)
- [ ] Corrigir arquitetura de tradução do Dashboard antes de adicionar
      francês/alemão/japonês
- [ ] Transformar "Ask StayFlow" num agente real com function calling
      — pré-requisito também do checkbox "Resposta automática", que
      continua desabilitado até esse recurso existir
- [ ] Cadastrar o Hostel Lagares real (login + WhatsApp próprios)
- [ ] `services/memory_service.py` — ainda não commitado, não testado
      com WhatsApp real
- [ ] Preencher `hostels.phone` (organização, não bloqueia nada)
- [ ] Corrigir dropdown de idioma cortado no mobile
- [ ] Visual do Login — fundo com mapa mundi (padrão do `Register.html`)
- [ ] Botão "Teste grátis" ainda linka pro WhatsApp
- [ ] Decidir arquitetura definitiva de deploy (eliminar o xcopy manual)
- [ ] Integração por e-mail com OTAs
- [ ] `Login_MISTERIOSO_BACKUP.html`, `_screenshots_revisao/`,
      `teste-users.html` continuam fora do Git
- [ ] Faxina de pastas locais (`Archive_old/`, `Audit_old/`,
      `backups_old/`)
- [ ] Decidir destino de `templates/components/`
- [ ] Colunas mortas na tabela `settings` (`checkin_time`,
      `checkout_time`, `breakfast_time`, `languages`, `services`,
      `tours` — existem no schema, nunca lidas nem escritas por
      nenhuma rota) — achado nesta sessão, não investigado a fundo
- [ ] Padronizar formato de resposta da rota `/settings` (hoje devolve
      `{"status": "ok"}`, diferente do padrão `{"success": true, ...}`
      usado em todas as outras rotas construídas nas últimas sessões)
- [ ] `_backfill_security_billing_for_full_access_roles()` roda a cada
      `create_database()` (todo start do app), não só uma vez — hoje é
      inofensivo porque não toca overrides individuais por pessoa, só
      a permissão-base da role. Se no futuro existir edição direta da
      permissão-base de uma role que remova propositalmente `security`/
      `billing` de uma role que ainda tenha as 12 chaves antigas, essa
      função reverteria a remoção a cada restart. Precisa ganhar uma
      guarda de "já rodou uma vez" (registro em alguma tabela de
      controle de migração), igual as outras migrações de schema —
      achado na Sessão 7, não implementado ainda.

## SESSÃO 7 - 22/07/2026

### Contexto no início da sessão

Continuação direta da Sessão 6. Objetivo único, declarado no início:
resolver de ponta a ponta as 5 categorias vazias de Configurações
(Empresa, Comunicação, Segurança, Billing, Developer) identificadas na
sessão anterior, mais qualquer limpeza de base necessária pra isso.

### Decisão de arquitetura (Sessão 7) — interruptor mestre da IA vs. horário de silêncio

Durante a construção de Comunicação (PASSO 6), a primeira versão do
horário de silêncio (`quiet_hours_start`/`quiet_hours_end`) chegou a
suprimir o **envio automático real ao hóspede** via WhatsApp
(`send_whatsapp_message` em `routes/chat.py`), usando o timezone já
validado. Essa versão foi revertida — `is_within_quiet_hours()` continua
existindo em `database.py`, testada e funcional, mas **não é chamada em
lugar nenhum** por enquanto.

No lugar dela, foi criado o interruptor mestre real: coluna
`ai_enabled` em `settings` (aditiva, `INTEGER DEFAULT 1`), função
`is_ai_enabled(hostel_id)`, e checkbox "IA responde automaticamente aos
hóspedes" no card IA StayFlow (visualmente destacado, diferente do
checkbox "Resposta automática para dúvidas simples", que continua
desabilitado — este último é sobre assumir UMA conversa específica no
futuro, não sobre ligar/desligar a IA inteira). Quando desligado, o
hóspede continua tendo a mensagem salva e a oportunidade detectada
(`analyze_message` não depende de resposta da IA), mas nenhuma resposta
é gerada nem enviada — atendimento fica 100% manual a partir daí.

**Regra de arquitetura registrada para o futuro:** `ai_enabled` é o
único mecanismo que pode gatear resposta *direta* a um hóspede.
`quiet_hours_start`/`quiet_hours_end` ficam reservados para mensagem
*proativa*/notificação de equipe (quando o Ask StayFlow com function
calling existir) — nunca devem voltar a gatear resposta direta a
hóspede. O campo continua no contrato de `/settings`, mas a UI o
renderiza desabilitado com aviso, pra não sugerir que já faz algo hoje.

### Mudança estrutural de arquitetura (Sessão 7) — sessão rastreada no servidor

Até este ponto da Sessão 7, a autenticação de todo o sistema era a
sessão **padrão do Flask**: um cookie assinado (`itsdangerous`,
`app.secret_key`) carregando `user_id`/`hostel_id` inteiramente no
navegador. O servidor nunca guardava nenhum registro de quem estava
logado — cada requisição só validava a assinatura do cookie e recalculava
tudo fresco do banco. Isso significava que **não havia nenhuma forma de
ver quantos dispositivos estavam logados, nem de derrubar um específico**
— trocar a senha, por exemplo, não conseguia derrubar uma sessão de
cookie já ativa em outro aparelho.

**Decisão explícita do usuário:** fazer essa migração agora, e não
adiar como "em breve" — ainda não há hóspede real nem o Hostel Lagares
cadastrado, então o efeito colateral inevitável (todo mundo precisa
logar de novo depois do deploy, já que o formato do cookie muda por
completo) custa zero neste momento.

**O que mudou:**
- Nova tabela `sessions` (`id` — token opaco aleatório de 32 bytes via
  `secrets.token_urlsafe`, não sequencial, impossível de adivinhar —
  `user_id`, `hostel_id` opcional, `created_at`, `last_seen_at`,
  `revoked`, `user_agent` cru).
- O cookie do Flask passou a guardar **só** `session["session_id"]`
  (o token opaco) — nunca mais `user_id`/`hostel_id` direto. Toda
  requisição autenticada busca a linha correspondente no banco
  (`get_valid_session`), confirma `revoked=0`, e só então libera acesso
  — com cache por requisição em `flask.g` pra não consultar o banco mais
  de uma vez por requisição.
- **Login com múltiplos hostels vira uma sessão real também**, só com
  `hostel_id = NULL` (estado "pending") até a escolha em
  `/select-hostel` — não existe mais um mecanismo paralelo
  (`session["pending_user_id"]`) por fora da tabela. Uma sessão pending
  fica automaticamente bloqueada de qualquer rota protegida por
  `@require_auth`/`@require_permission`, porque `hostel_id` vem `None`.
- `/select-hostel` **atualiza a mesma linha** (mesmo token, mesmo
  "dispositivo") — nunca cria uma sessão nova, seja completando a
  escolha inicial ou trocando de hostel estando já logado.
- Troca de senha (`/security/change-password`, nova) agora **revoga de
  verdade** todas as outras sessões do usuário, exceto a que está
  fazendo a troca — e a mensagem de sucesso passou a poder dizer isso
  com honestidade, porque agora é real.
- Tela "Sessões ativas" em Segurança lista as sessões do próprio
  usuário (com a atual identificada) e permite revogar uma por uma —
  revogar bloqueia a *próxima* requisição daquela sessão específica,
  testado explicitamente.
- Log básico de login (`login_attempts`): toda tentativa em `/login`
  fica registrada (sucesso/falha, e-mail tentado), visível em Segurança.

**Investigação de segurança feita antes de implementar** (para não
deixar nenhuma rota insegura pela migração): confirmado que **só**
`routes/auth.py` e `utils/tenant.py` tocam o objeto `session` do Flask
em todo o codebase — nenhuma rota lê `session.get(...)` por fora dos
decorators `@require_auth`/`@require_permission`. O webhook do WhatsApp
e o endpoint de teste `/message` não usam sessão de forma alguma
(confirmado). Nenhuma rota órfã encontrada.

**Testado com rigor** (autenticação não admite meio-termo): login cria
linha em `sessions`; dois "dispositivos" (test clients distintos)
geram duas linhas distintas e acessam normalmente; revogar uma sessão
específica bloqueia a *próxima* requisição dela (401) sem afetar a
outra; trocar senha revoga todas as sessões exceto a atual (confirmado
que a antiga falha e a atual continua válida), muda o hash de verdade
e invalida a senha antiga para novo login; fluxo completo de login
multi-hostel (sessão criada com `hostel_id NULL` → rota protegida
bloqueada em pending, incluindo `/me` → `/select-hostel` preenche o
`hostel_id` na mesma linha → rota protegida passa a funcionar) validado
ponta a ponta; log de login confirmado com uma tentativa de sucesso e
uma de falha aparecendo corretamente.

**Correção pós-teste:** a primeira versão restringia a seção Segurança
inteira à permissão `security` (via `applyPermissionVisibility`) — bug
real, pego antes de aprovar o passo: trocar a própria senha, ver as
próprias sessões ativas e o próprio histórico de login são gestão da
**própria conta**, não administração do hostel — restringir isso
bloquearia qualquer Staff sem essa permissão de trocar a própria senha.
Corrigido: `change_password`/`list_sessions`/`revoke_session_route`/
`list_login_attempts` usam `@require_auth` (só exige sessão válida, sem
checar permissão específica) — continuam seguras porque cada uma é
escopada por `get_current_user_id()` internamente (cada pessoa só
vê/mexe na própria conta, nunca na de outra). O card no frontend
também deixou de ter `data-required-permission="security"` — fica
visível pra qualquer usuário autenticado.

A permissão `security` continua existindo em `ALL_PERMISSIONS`, sem uso
por enquanto — **reservada para uma futura tela de política de
segurança do hostel** (ex: forçar 2FA pra toda a equipe, auditoria de
login de todos os funcionários, não só o próprio) — isso sim seria
administração do hostel, diferente de gerenciar a própria conta. Não é
o mesmo caso de `billing`, que continua restrita a admin/dono de
verdade porque é configuração do hostel (plano, fatura), não conta
pessoal.

Testado explicitamente: usuário Staff (sem a permissão `security`)
logou, trocou a própria senha com sucesso, viu as próprias sessões e o
próprio histórico de login — tudo sem precisar de nenhuma permissão
especial. Teste de isolamento entre contas: usuário A tentou revogar um
`session_id` pertencente ao usuário B — `revoke_session_route` rejeitou
corretamente (404, nada foi apagado). Confirmado também que
`last_seen_at` é atualizado a cada requisição autenticada (não só na
criação) — duas requisições separadas, dois timestamps diferentes.

### PASSO 8 — Billing e PASSO 9 — Developer

Ambos honestamente desabilitados, sem dado falso nem formulário
funcional:

- **Billing**: card "Modelo de cobrança em definição" (sem processador
  de pagamento integrado, sem plano ativo). Tabela nova `billing`
  (hostel_id, plan_name, status, created_at) — só estrutura, nenhuma
  rota lê nem escreve nela ainda. Restrita à permissão `billing` (via
  `applyPermissionVisibility`) — essa sim continua config do hostel de
  verdade (plano/fatura), diferente de Segurança (conta pessoal).
- **Developer**: card "Integrações — em breve", com lista curta do que
  está planejado (OTAs — Booking.com, Airbnb, Hostelworld — e channel
  managers como Beds24, reaproveitando a pesquisa já feita na Sessão 4;
  chaves de API próprias). Tabela nova `api_keys` (hostel_id, key_name,
  created_at) — só estrutura, sem geração real de chave. Sem gate de
  permissão por enquanto — nada funcional existe ainda pra proteger;
  decisão a revisitar quando a funcionalidade real for construída.

### Smoke test de regressão (antes do PASSO 8)

A reescrita completa de autenticação (cookie assinado → sessão
rastreada no servidor) toca o mecanismo usado por toda rota protegida
do sistema, não só as de Segurança. Antes de prosseguir, testado login
normal seguido de 8 rotas protegidas de módulos **não tocados** nesta
sessão (`/reservations`, `/team`, `/finance`, `/inventory`, `/revenue`,
`/guests`, `/opportunities`, `/reports`) — todas 200, sem nenhum erro
relacionado à sessão.

### Resumo da Sessão 7

**As 5 categorias de Configurações, todas resolvidas** (nenhuma ficou
pela metade):
- **Empresa**: razão social, CUIT/RUT, endereço, fuso horário (lista
  fechada IANA, validada no backend), moeda (lista fechada ISO 4217),
  check-in/check-out (colunas reaproveitadas, não duplicadas), logo
  (URL de texto, sem upload de arquivo). Testado ponta a ponta,
  escopado por hostel_id.
- **Comunicação**: preferência de canal de alerta (ligada ao sino já
  existente), biblioteca de respostas rápidas (tabela + rotas CRUD +
  integração real no picker do chat, preenchendo o campo de texto sem
  nunca chamar o envio diretamente), interruptor mestre `ai_enabled`
  (ver decisão de arquitetura acima). Horário de silêncio construído,
  testado e depois **revertido** de gatear resposta direta — fica
  reservado pra mensagem proativa futura, campo no contrato mas UI
  desabilitada com aviso.
- **Segurança**: trocar senha, ver/revogar sessões ativas, log de
  login — todos como gestão da própria conta (`@require_auth`, sem
  exigir permissão especial, corrigido depois de um erro de escopo
  pego antes de aprovar o passo). 2FA desabilitado ("em breve"). A
  mudança que sustenta tudo isso — sessão rastreada no servidor — é a
  maior mudança estrutural da sessão (ver seção própria acima).
- **Billing**: honestamente desabilitado, restrito à permissão
  `billing` (config do hostel de verdade).
- **Developer**: honestamente desabilitado, sem gate de permissão
  (nada funcional pra proteger ainda).

**Mudança estrutural**: autenticação migrou de cookie assinado
client-side (Flask padrão, sem registro nenhum no servidor) pra sessão
rastreada em tabela própria (`sessions`), com token opaco de 32 bytes,
revogação individual e por troca de senha. Decisão explícita do usuário
de fazer isso agora (não adiar) porque ainda não há hóspede real nem o
Hostel Lagares cadastrado — o relogin geral forçado pelo deploy custa
zero neste momento. Investigação prévia confirmou zero rotas órfãs;
smoke test de regressão pós-implementação confirmou zero rotas
quebradas fora do que já foi testado diretamente.

**Migração de schema** (PASSO 3): removidas as 6 colunas mortas de
`settings` (`checkin_time`, `checkout_time`, `breakfast_time`,
`languages`, `services`, `tours` — confirmado sem nenhum uso real antes
de remover), testado preservando 100% dos dados existentes numa cópia
isolada (célula por célula, antes vs. depois). **Isso resolve** o item
pendente da Sessão 6 sobre colunas mortas.

**Contrato de `/settings` padronizado** (PASSO 2/5): resposta sempre
`{"success": true, ...}` (troca do `{"status": "ok"}` antigo), upsert
parcial de verdade (testado explicitamente: salvar só Comunicação não
apaga Empresa, e vice-versa). **Isso resolve** o item pendente da
Sessão 6 sobre o formato de resposta inconsistente.

**Duas chaves de permissão novas**: `security` e `billing` adicionadas
a `ALL_PERMISSIONS`, com backfill automático pras roles que já eram
"acesso total" no esquema antigo (testado). `security` acabou sem uso
direto (trocar senha/sessões/login são conta pessoal, não hostel) —
fica reservada pra uma futura tela de política de segurança do hostel
(forçar 2FA pra equipe, auditoria de login de todos os funcionários).

**Achado de ambiente**: Windows não vem com dados IANA por padrão;
`zoneinfo` (usado por `is_within_quiet_hours`, hoje não chamada em
lugar nenhum) precisou do pacote `tzdata`, adicionado a
`requirements.txt` (preservando a codificação UTF-16LE incomum do
arquivo original). Verificar isso via `pip install -r requirements.txt`
real acabou reinstalando pacotes locais (`bcrypt` voltou pra 4.2.1, a
versão já fixada no arquivo) — mais invasivo do que pretendido pra uma
simples verificação, mas resultado inofensivo (mesma versão de
produção).

**`services/memory_service.py` finalmente commitado**: a versão local
(`MEMORY_FILE` via `STAYFLOW_DATA_DIR`, `HISTORY_WINDOW=60`) ficou sem
commit desde a Sessão 3, nunca testada ponta a ponta. Investigado antes
de decidir: só 1 commit já tinha tocado o arquivo (`21a0ca6`, Sessão 2,
05/07), a versão em produção era a antiga (caminho relativo fixo,
janela de 12 mensagens) — confirmado que `21a0ca6` é ancestral do
último commit publicado (`daed695`). Testado nos 5 pontos antes de
aprovar: `conversations.json` criado dentro de `STAYFLOW_DATA_DIR` (não
mais na raiz do projeto — achado colateral: um `conversations.json`
não rastreado, de 11/07, com conversa real desde 25/06, sentado na
pasta de código, prova viva do bug); histórico correto até 60 mensagens
(testado com 40 e com 80, nunca truncou em 12); sobrevive a um "restart"
simulado (`create_database()` chamado de novo, mesmo diretório);
`.gitignore` do HostelBot já protegia `conversations.json`/
`conversations.json.backup` (nenhum ajuste necessário). Entra no
commit de fechamento desta sessão, tal como está localmente.

### O que ficou pendente pra próxima sessão

Itens da Sessão 6 resolvidos nesta sessão (não repetidos aqui):
colunas mortas de `settings`, formato de resposta de `/settings`.

- [ ] Publicar em produção o trabalho da Sessão 6 E da Sessão 7 —
      **nada foi commitado nem deployado ainda**, aguardando aprovação
      final e backup manual do disco do Render antes do commit
- [ ] `_backfill_security_billing_for_full_access_roles()` roda a cada
      `create_database()`, não só uma vez — precisa de guarda "já
      rodou uma vez" se um dia existir edição direta de permissão-base
      de role que remova `security`/`billing` propositalmente (achado
      na Sessão 7, não implementado)
- [ ] Corrigir arquitetura de tradução do Dashboard antes de adicionar
      francês/alemão/japonês
- [ ] Transformar "Ask StayFlow" num agente real com function calling
      — pré-requisito do checkbox "Resposta automática" (assumir Uma
      conversa) E do horário de silêncio de verdade (mensagem proativa)
- [ ] Cadastrar o Hostel Lagares real (login + WhatsApp próprios)
- [ ] Preencher `hostels.phone` (organização, não bloqueia nada)
- [ ] Corrigir dropdown de idioma cortado no mobile
- [ ] Visual do Login — fundo com mapa mundi (padrão do `Register.html`)
- [ ] Botão "Teste grátis" ainda linka pro WhatsApp
- [ ] Decidir arquitetura definitiva de deploy (eliminar o xcopy manual)
- [ ] Integração por e-mail com OTAs — só depois do operacional 100%
      fechado
- [ ] Faxina de pastas locais (`Archive_old/`, `Audit_old/`,
      `backups_old/`)
- [ ] Decidir destino de `templates/components/`
- [ ] `migrate_conversations_json.py` (raiz do HostelBot) ainda usa o
      caminho relativo antigo (`MEMORY_FILE = "conversations.json"`,
      mesmo bug que existia em `memory_service.py`) — script solto de
      execução manual, não importado por `app.py` nem por nenhuma rota,
      não é bug ativo. Corrigir quando for usado de novo, não agora —
      achado na Sessão 7 durante a investigação do memory_service.py.
- [ ] Construir de verdade quando fizer sentido: tela de política de
      segurança do hostel (usa a permissão `security`, já reservada
      pra isso — forçar 2FA pra equipe, auditoria de login de todos os
      funcionários)
- [ ] 2FA de verdade (autenticação em duas etapas) — desabilitado como
      "em breve", integração com SMS/authenticator é escopo maior,
      sem meio-termo possível
- [ ] Billing/Developer funcionais — quando o modelo comercial e as
      integrações de verdade existirem, respectivamente
- [ ] Robocopy de sincronização do fechamento da Sessão 7 usou `/MIR`
      sem excluir `docs/` nem `.claude/` (fugiu do padrão seletivo de
      sync usado nas sessões anteriores, que só copiava os arquivos de
      deploy de verdade). Resultado: `StayFlow---Site/docs/` e
      `StayFlow---Site/.claude/` ficaram untracked dentro do
      `HostelBot` — deliberadamente não commitados nem adicionados ao
      `.gitignore` (só não fazem parte de nenhum commit por enquanto).
      Da próxima vez, rodar com `/XD docs .claude` também, igual já se
      faz com `.git`, pra não repetir isso.
