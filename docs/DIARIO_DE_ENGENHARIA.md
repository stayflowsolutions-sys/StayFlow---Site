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

## SESSÃO 8 - 23/07/2026

### Contexto no início da sessão

Continuação direta após o fechamento da Sessão 7 (já publicada em
produção). Objetivo declarado pelo usuário: "fazer o botão Ask
StayFlow funcionar de verdade, e depois começar a preparar as
integrações". Terminou virando duas entregas grandes: o Ask StayFlow
como agente real, e — puxado por um exemplo concreto do usuário
(pedido de reposição a fornecedor) — um sistema completo de Mapa de
Quartos/Camas com ciclo de limpeza e lavanderia.

### Ask StayFlow — de mock pra agente real

Antes desta sessão, o botão "Ask StayFlow" só ecoava uma mensagem fixa
("Mensagem registrada. Quando o backend estiver conectado...") — não
existia rota `/ask`, nem histórico, nem qualquer function calling real
pro painel do operador (o único function calling que já existia era o
`save_guest_name` da IA de atendimento ao hóspede, um "2 rounds fixos",
não um loop de verdade).

**Camada de dados**: extraídas 10 funções de leitura de `database.py`
(dashboard, oportunidades, reservas, estoque, receita, hóspedes,
conversas, financeiro, relatórios) a partir do SQL que já vivia inline
nas rotas manuais — agora rota manual e ferramenta do agente chamam a
mesma função, uma única fonte de verdade. Nova tabela `ask_messages`
(histórico do agente, chave `hostel_id`+`user_id`, separada de
propósito do `memory_service` que é guest-scoped).

**`services/ask_agent_service.py`** (novo): loop real de function
calling (até 6 rodadas por requisição, não fixo), cada ferramenta só
entra na lista oferecida ao modelo se `get_effective_permissions`
incluir a permissão equivalente da rota manual — nunca confia em
`hostel_id`/`user_id` vindo do modelo, sempre vem da sessão.

**Fase de ações reais** (aprovada explicitamente pelo usuário depois
de uma pergunta de escopo — "isso é só pro pão ou é genérico?"):
- Pedido de reposição a fornecedor: `propose_supplier_order` monta a
  mensagem e mostra pro operador, `confirm_and_send_supplier_order` só
  manda de verdade (reusa `send_whatsapp_message`, já existente pra
  hóspede) depois de confirmação explícita numa mensagem separada —
  nunca no mesmo turno da proposta. Nova tabela `inventory_orders`
  rastreia pending_confirmation → sent → received, em vez de depender
  da memória da conversa.
- Aviso proativo a hóspede: mesmo padrão propor→aprovar→enviar,
  `propose_guest_message`/`send_guest_message`. Ao enviar, a mensagem
  é gravada tanto no `memory_service` (JSON, usado pela IA de
  atendimento) quanto no `message_service` (SQL, usado pelas telas) —
  quando o hóspede responder pelo WhatsApp, a IA de atendimento já vê
  esse aviso no histórico normalmente, sem nenhum código novo no
  webhook.
- Extensão de reserva: a IA de atendimento (não o Ask StayFlow) ganhou
  a ferramenta `extend_reservation` — só executa sozinha quando é
  extensão pura (mesmo quarto, mesma diária, calculada pela diária
  atual da reserva); qualquer outra condição (troca de quarto,
  desconto) vira `flag_extension_for_approval`, que cria uma
  oportunidade de alta urgência pra equipe decidir manualmente. Decisão
  confirmada com o usuário via pergunta direta antes de implementar.

**Achados/correções no caminho**:
- `find_inventory_item_by_name`/`find_guest_by_name` usavam `LIKE` puro
  no SQL, sensível a acentuação — "pão" (que o modelo tende a grafar
  corretamente) não batia com um item cadastrado sem acento. Trocado
  por comparação normalizada (remove acento + minúsculas) em Python.
- A IA de atendimento nunca recebia a data de hoje no prompt — não
  conseguia calcular "amanhã" nem validar datas de extensão
  corretamente. Corrigido injetando a data real a cada chamada.
- Confirmação simples ("pode mandar") às vezes fazia o modelo montar a
  proposta de novo em vez de executar o envio — reforçada a instrução
  do prompt pra tratar confirmação subsequente como sinal inequívoco de
  "execute o que já propus". Testado antes e depois, comportamento
  consistente depois do ajuste.

### Mapa de Quartos/Camas (novo módulo completo)

Puxado pelo pedido de reposição a fornecedor, o usuário levou o
raciocínio adiante: "quero fazer o mapa de quartos, com camas
separadas por cor, ocupada vermelho, livre verde, beliche meio a meio,
checkout entra na lista de limpeza, roupa de cama vai pra lavanderia".
Depois ampliado explicitamente pra pensar em hotel/resort grande, não
só hostel pequeno.

**Modelo de dados**: `room_categories` (modalidade de quarto,
configurável por cada propriedade — não é lista fixa), `rooms`
(com `floor` pra organização de propriedade grande), `beds` (tipo
`single`/`bunk_top`/`bunk_bottom`, pareadas por `bunk_group`), status
gravado de verdade (`free`/`occupied`/`needs_cleaning`) — decisão
consciente de NÃO calcular ocupação pelas datas da reserva, porque
check-in/check-out reais nem sempre batem com o planejado.
`inventory_items` ganhou `in_laundry_quantity` (quantidade suja, fora
do estoque limpo disponível) e `reservations` ganhou `bed_id`.

**Ciclo completo testado**: check-in atribui reserva a uma cama livre
específica; check-out libera a cama pra `needs_cleaning` (a "lista de
limpeza do dia" é simplesmente essa consulta, sem tabela própria);
marcar como limpa consulta o "kit de roupa de cama" configurado por
tipo de cama, desconta do estoque limpo e soma em `in_laundry_quantity`;
devolução da lavanderia faz o caminho inverso, com proteção contra
devolver mais do que realmente está lá.

**Pensando em hotel/resort grande** (pedido explícito do usuário):
`create_rooms_bulk` cria vários quartos de uma vez com a mesma
modalidade/andar — testado criando 3 quartos num único comando, tanto
via banco quanto via HTTP real.

**Modalidades padrão por tipo de propriedade**: reaproveitado o campo
`hostel_type` que já existia em Configurações > Empresa (antes sem
nenhum efeito prático) — `apply_default_room_categories_if_needed`
roda quando esse campo é salvo e, **só se o hostel ainda não tem
nenhuma modalidade cadastrada**, cria os padrões do tipo (Hostel →
Privado/Compartilhado; Hotel/Pousada/Resort → Standard/Luxo). Nunca
sobrescreve modalidade manual já existente. Opção "Resort" adicionada
ao seletor, que antes só tinha Hostel/Hotel/Pousada/Flat.

**Frontend**: nova seção "Mapa de Quartos" no menu lateral (logo após
Reservas, posição escolhida pelo usuário entre 3 opções), mapa visual
com legendas de cor, beliche renderizado como um bloco só com metade
de cima/baixo coloridas pelo status real de cada cama, painel de ação
inline ao clicar numa cama (check-in com busca de reserva confirmada
sem cama atribuída, check-out, marcar como limpa).

**Limitação de teste registrada**: sem ferramenta de navegador
disponível nesta sessão (sem Playwright/Puppeteer), a validação da UI
foi feita via HTTP real (login com sessão de verdade, cookies reais,
todas as chamadas que o JS faz) contra um servidor Flask local com
banco isolado — não clique físico na interface. Recomendado ao usuário
testar visualmente antes de considerar 100% fechado. No caminho, dois
processos de teste ficaram escutando a mesma porta ao mesmo tempo
(`pkill` não mata processo Python no Git Bash/Windows do jeito
esperado) e mascararam uma correção por um momento — resolvido matando
os PIDs via `Stop-Process` do PowerShell.

### O que ficou pendente pra próxima sessão

- [ ] Validação visual manual do Mapa de Quartos num navegador de
      verdade (clique físico nas camas, beliche, formulários) — não
      foi possível nesta sessão por falta de ferramenta de navegador
- [ ] Cadastrar de verdade quartos/camas/kits de roupa de cama do
      Hostel Lagares real, hoje só testado com dados sintéticos
- [ ] Decidir se `resort` merece um conjunto de modalidades padrão
      próprio (hoje reaproveita o mesmo Standard/Luxo do Hotel) —
      simplificação deliberada, não formalmente confirmada com o
      usuário
- [ ] Integrações com redes sociais (Facebook/Instagram/TikTok) e
      OTAs/PMS (Booking/Airbnb) — adiadas de propósito até a fundação
      de function calling do Ask StayFlow existir de verdade, que
      passou a existir nesta sessão
- [ ] Itens já pendentes da Sessão 7 continuam pendentes (ver acima),
      não repetidos aqui

### Continuação da Sessão 8 (mesma data) — reserva por WhatsApp, preço, mapa de camas com 5 estados

Depois do fechamento acima, o usuário testou o Ask StayFlow em produção
de verdade e trouxe uma sequência de achados e pedidos novos, todos
tratados na mesma sessão:

**Bug crítico de produção descoberto pelo usuário**: o servidor Flask
rodava sem `threaded=True` — enquanto o Ask StayFlow ou a IA de
atendimento estavam no meio de uma chamada real à OpenAI (vários
segundos), o processo inteiro ficava bloqueado pra qualquer outro
pedido, inclusive mandar mensagem manual pro hóspede. Corrigido com uma
linha (`app.run(..., threaded=True)`). Complementado no frontend: o
painel Ask StayFlow agora usa `AbortController` com timeout de 75s, pra
nunca mais deixar o botão de enviar travado indefinidamente.

**Reserva automática via WhatsApp**: a IA de atendimento ganhou
`create_reservation_from_chat` (database.py) — cria a reserva sozinha
assim que reúne nome/modalidade/datas, sempre `status='pending'`
(equipe confirma depois) e **valor sempre calculado a partir do
`price_per_night` real da modalidade** (nunca aceito como argumento do
modelo — reforço mecânico, não só instrução de prompt). Não duplica se
o hóspede reafirmar a mesma coisa na conversa.

**Preço e seleção de cama pelo hóspede** (pedido explícito, comparado
pelo usuário a escolher janela/corredor num site de passagem de
ônibus): `room_categories` ganhou `price_per_night`/`description`;
`find_available_beds` calcula disponibilidade **futura** por
sobreposição de datas de reserva (diferente do status operacional em
tempo real do mapa) — a IA de atendimento consulta isso, apresenta as
camas livres (cima/baixo do beliche) e usa a escolhida ao criar a
reserva. Achado no caminho: em pelo menos uma conversa de teste real, o
modelo disse que uma cama "tinha acabado de ser reservada" quando na
verdade ainda estava livre — a validação mecânica de disponibilidade
(que bloqueia de verdade um double-booking) funcionou corretamente, mas
a explicação que o modelo deu ao hóspede foi imprecisa. Registrado como
limitação conhecida de confiabilidade do modelo, não um bug de código —
não perseguido além disso por causa do tempo de sessão.

**5 estados de cama no mapa** (pedido explícito do usuário): verde
livre, vermelho ocupada, âmbar precisa de limpeza, azul reservada,
laranja manutenção. "Reservada" é um estado **derivado só pra
exibição** (cama com status real `free` mas com reserva futura
atribuída) — o status operacional de verdade continua sendo só
free/occupied/needs_cleaning/maintenance; nova acao
`set_bed_maintenance` (só permite entrar em manutenção se a cama
estiver fisicamente livre agora).

**Assumir/devolver conversa + envio manual real**: novo campo
`guests.ai_paused` — quando true, a IA para de responder aquele
hóspede específico (mensagem/oportunidade continuam sendo salvas),
diferente de `is_ai_enabled` (interruptor do hostel inteiro). Botão
"Assumir conversa"/"Devolver pra IA" na tela de Chats. A caixa de
envio manual da tela de Chats, que **sempre foi mock** desde o início
do projeto (só ecoava uma resposta fake), agora manda mensagem de
verdade pelo WhatsApp Business (`send_message_to_guest_now`).

**Lista de limpeza espelhada em Operações**: a caixa "Tarefas
operacionais" de Operações, que desde a Sessão 6 tinha um comentário
dizendo "depende do mapa de camas, ainda não construído", agora
consome `get_cleaning_list` (mesma fonte de verdade do Mapa de
Quartos) — sem tabela duplicada.

### Terceira rodada da Sessão 8 (mesma data) — bugs reais achados testando, gunicorn

O usuário continuou testando em produção e achou mais uma série de
bugs reais, todos corrigidos:

- **Beliche renderizava como 2 quadrados separados**, não uma cama só
  dividida ao meio (o CSS já previa a divisão, a função de geração de
  HTML que estava errada — criava dois `.bed-tile` em vez de um com
  dois `.bed-tile-half`). Corrigido, e aproveitado pra deixar o
  formato mais retangular (cama vista de cima), não quadrado.
- **Tecla Enter no chat ainda chamava `mockSend()`** — o botão
  "Enviar" tinha sido trocado pro envio real, mas o atalho de teclado
  (`bindEnterToSend`) foi esquecido, então digitar e apertar Enter
  ainda caía na mensagem simulada antiga. Corrigido.
- **Sino de alertas nunca zerava**: contagem de `/operations` era
  recalculada do zero a cada carregamento e nunca marcada como "vista".
  Agora abrir Operações grava a contagem atual como vista
  (`localStorage`), e o sino só acende de novo se a contagem
  subir acima do que já foi visto.
- **IA de reserva confundia nome de MODALIDADE com nome de QUARTO**
  entre uma chamada e outra de `get_available_beds` (ex: usava "Dorm 1"
  em vez de "Compartilhado") — isso fazia a consulta devolver lista
  vazia, que a IA interpretava como "sem cama disponível" (falso
  negativo real, reproduzido e comprovado com log das chamadas reais
  de function calling). `find_available_beds` agora detecta esse erro
  e devolve uma mensagem explicando o problema com a lista de
  modalidades válidas, e o prompt foi reforçado explicando a diferença.
- **IA às vezes atrasava a criação da reserva** esperando e-mail/toalha
  antes de reservar, mesmo já tendo nome+modalidade+datas — prompt
  ajustado deixando claro que a reserva deve ser criada assim que esses
  3 dados existirem, o resto continua sendo coletado depois.
- **IA reescalava o preço ao falar com o hóspede** (dizia "R$ 200"/
  "R$ 600" quando o valor real configurado era 20.000/60.000) — a
  reserva em si sempre foi gravada com o valor certo (calculado no
  servidor, nunca aceito do modelo), só a fala pro hóspede estava
  errada. Prompt agora instrui a nunca reescalar nem inventar símbolo
  de moeda.
- **Servidor de produção**: `gunicorn` já estava em `requirements.txt`
  mas nunca foi de fato usado — criado `Procfile`
  (`web: gunicorn app:app --workers 3 --threads 4 --timeout 120`).
  Não foi possível testar `gunicorn` localmente (não roda nativamente
  no Windows, depende de `fork`/`fcntl` do POSIX) — o usuário precisa
  atualizar o Start Command no painel do Render manualmente, sem
  acesso direto a isso nesta sessão.

Pendência levantada pelo usuário e ainda não escopada: captura de
documento de identidade (nome completo, data de nascimento, foto do
documento) durante a reserva pelo WhatsApp — requer lidar com
mensagens de mídia no webhook do WhatsApp, que hoje só processa texto;
não implementado ainda, precisa de decisão sobre onde armazenar as
fotos antes de começar.

### Quarta rodada da Sessão 8 (mesma data) — testando em produção de verdade, mais bugs reais

**Descoberta importante sobre o servidor**: o usuário mostrou que o
Start Command do Render já era `gunicorn app:app` (não o servidor de
desenvolvimento do Flask, como eu tinha suposto antes). O diagnóstico
mudou, mas a correção continuou a mesma: `gunicorn app:app` sozinho,
sem `--workers`/`--threads`, usa 1 processo único por padrão — mesmo
efeito prático de travar tudo durante uma chamada lenta à IA. Start
Command atualizado manualmente pelo usuário pra
`gunicorn app:app --workers 3 --threads 4 --timeout 120`.

**Duas camas cadastradas com o mesmo nome "Cama 1"** (uma beliche de
cima, outra de baixo) confundiram a IA numa conversa real — não é bug
de código, é qualidade de dado cadastrado; anotado como lembrete de
usar nomes distintos ao criar beliches.

**Bug real de CSS, achado testando ao vivo**: o painel do Ask StayFlow
ficava com o cabeçalho (seletor de hostel, sino, avatar) renderizado
por cima dele, e depois de acumular mensagens a caixa de digitação
"sumia". Duas causas raiz distintas, ambas corrigidas:
- `.topbar` tinha `z-index:50`, maior que o `.ask-panel` (`z-index:40`)
  — corrigido pra 55/56, entre o topbar e os modais genéricos (60/65).
- `.ask-body` (flex:1 dentro de `.ask-panel`, que é flex-column) não
  tinha `min-height:0` nem `overflow-y` — armadilha clássica de
  flexbox: sem isso, o item flex cresce pra caber todo o conteúdo em
  vez de rolar, empurrando a `.ask-input` pra fora da tela conforme a
  conversa cresce. Corrigido com `min-height:0` + `overflow-y:auto`.

**Mapa de Quartos ganhou editar/excluir cama**: `update_bed_label`
(novo) e `delete_bed` (já existia, agora bloqueia exclusão de cama
ocupada — pede check-out antes) expostos na UI via botões no painel
de ação de qualquer cama, em qualquer status.

### Quinta rodada da Sessão 8 (mesma data) — captura de documento de identidade

Feature nova pedida pelo usuário: hostels em geral precisam registrar
documento de identidade do hóspede (nome completo, data de nascimento,
foto do passaporte/RG). Nada disso existia — o webhook do WhatsApp só
processava mensagens de texto, imagem chegava e era silenciosamente
ignorada.

**Armazenamento**: decisão consciente de guardar os arquivos no mesmo
disco persistente onde já fica o banco (`STAYFLOW_DATA_DIR/documents/
{hostel_id}/{guest_id}/...`), não em nuvem — não há credenciais de um
serviço de storage externo disponíveis nesta sessão. Cada envio vira
uma linha nova em `guest_documents` (nunca sobrescreve), permitindo
reenvio se a foto sair ruim.

**Download de mídia da Meta**: é sempre em 2 passos — primeiro busca a
URL temporária de download pelo media_id, depois baixa o arquivo de
verdade dessa URL, os dois autenticados com o token do hostel
(`download_whatsapp_media`, novo em `whatsapp_service.py`). O webhook
detecta `type == "image"` e processa fora do fluxo normal de texto —
manda confirmação direta ("Recebi seu documento, obrigado!") sem
passar pela IA de conversa, já que ela não analisa o conteúdo da
imagem mesmo.

**IA de atendimento**: pede nome completo, data de nascimento (nova
tool `save_guest_date_of_birth`) e foto do documento logo depois de
criar a reserva.

**Achado no caminho, corrigido**: se `get_available_beds` devolve
lista vazia, isso pode significar "lotado" OU "essa modalidade ainda
não tem camas cadastradas individualmente" (comum em quarto privado)
— a IA estava travando a reserva inteira nesse segundo caso. Prompt
ajustado: lista vazia não bloqueia mais a reserva, ela é criada sem
`bed_id` (atribuição de cama fica pro check-in, como já era o design).
Testado nos dois casos.

Documentos capturados aparecem no perfil do hóspede na tela de Chats,
com link pra abrir o arquivo (`GET /guests/documents/<id>/file`).

### Sexta rodada da Sessão 8 (mesma data) — trava real contra overbooking

O usuário perguntou (sem pedir mudança ainda) se o ajuste da rodada
anterior ("lista de camas vazia não bloqueia mais a reserva") abria
risco de overbooking. Resposta honesta: sim, abria — se uma modalidade
não tem nenhuma cama cadastrada, nada detecta duas reservas
sobrepostas pra ela, já que a checagem de conflito é toda por
`bed_id`. O usuário pediu a correção certa: exigir cama cadastrada
antes de liberar reserva automática.

`create_reservation_from_chat` reescrita com a trava definitiva:
- Modalidade sem NENHUMA cama cadastrada → reserva NÃO é criada.
  Vira oportunidade tipo `booking`, urgência alta, pra equipe cadastrar
  as camas e confirmar manualmente. Não duplica a oportunidade se o
  hóspede repetir o pedido na mesma conversa.
- Modalidade com cama(s) cadastrada(s) → `bed_id` passa a ser
  OBRIGATÓRIO (antes era opcional) e precisa apontar pra uma cama
  realmente livre pras datas pedidas, verificada de novo no momento da
  reserva.

Prompt da IA de atendimento revertido/corrigido: a instrução anterior
("lista vazia não significa lotado, reserve sem cama mesmo assim") foi
removida — o comportamento certo agora é o oposto, e a IA foi
instruída a avisar o hóspede que o pedido foi registrado pra equipe
quando `create_reservation` recusar por falta de cama cadastrada.

Testado com banco isolado (4 cenários: sem cama, repetição não
duplica oportunidade, com cama sem escolher trava, com cama escolhendo
reserva) e com conversa real de IA (confirmou que a reserva não é
criada e o hóspede recebe aviso correto).

### Sétima rodada da Sessão 8 (mesma data) — morador de longa duração

Pedido novo do usuário, com exemplo real (ele mesmo mora no hostel,
pagando conforme consegue): lugares onde alguém mora fixo/indeterminado
(ex: funcionário) precisam ser identificados separado de reserva
normal, contando quantos dias a pessoa deve, com pagamentos parciais
abatendo o saldo — e o usuário fez questão de lembrar que também pode
acontecer o inverso (pagar a mais e ficar com crédito acumulado).

**Modelo**: `reservations` ganhou `stay_type` ('fixed' padrão ou
'indefinite') e `daily_rate`; nova tabela `reservation_payments`
(cada pagamento é uma linha, nunca sobrescreve). Saldo é sempre
calculado sob demanda (nunca um campo estático que poderia
dessincronizar): dias ocupados (checkin até hoje, ou até checkout se
já encerrada) vezes diária, menos soma de tudo que já foi pago. Saldo
positivo significa que deve; saldo negativo significa crédito
acumulado por ter pago a mais — mesma fórmula cobre os dois casos sem
lógica especial.

`create_indefinite_stay`: sempre status='confirmed' (é um arranjo já
decidido pela equipe, não pedido de hóspede aguardando aprovação);
daily_rate pode ser 0 (funcionário que não paga nada, só ocupa a
cama). Se bed_id for passado, ocupa a cama de verdade na hora (mesma
integridade operacional do check-in normal). close_indefinite_stay
libera a cama pra limpeza, igual um check-out normal.

Exposto em 3 lugares, mesma fonte de verdade: formulário próprio na
tela de Reservas (separado do form de reserva normal), tabela de
Reservas mostrando "Deve US$ X" ou "Crédito US$ X" com cor diferente,
e 4 ferramentas novas no Ask StayFlow (criar morador, consultar saldo,
registrar pagamento, encerrar estadia).

Testado: cálculo de dias vezes diária, pagamento parcial, pagamento
que gera crédito (saldo negativo), pagamento inválido (zero/negativo)
recusado, diária zero resulta em saldo zero, cama ocupada na criação e
liberada pra limpeza no encerramento.

### Oitava rodada da Sessão 8 (mesma data) — bugs de edição no Mapa de
### Quartos + tradução completa do Dashboard

Usuário testando reportou, em duas mensagens seguidas: não conseguia
editar nem excluir quarto, e também não tinha como editar cama
(tipo/grupo), adicionar modalidade nova em edição, nem mudar nome de
nada — só existia formulário de criação em cada uma dessas três
coisas (quarto, cama, modalidade), sem nenhum caminho de edição ou
exclusão na interface, mesmo quando o backend já suportava (`DELETE
/rooms/<id>` e `DELETE /room-categories/<id>` já existiam, só sem
botão que os chamasse).

**Correção**: adicionadas rotas `PATCH /rooms/<id>` e `PATCH
/room-categories/<id>` no backend (`update_room`/`update_room_category`
em `database.py`), e `update_bed_label` estendida pra aceitar também
`bed_kind`/`bunk_group` (não só o nome). No frontend, cada card de
quarto no Mapa de Quartos ganhou botões ✎/✕ (editar/excluir), cada
modalidade também, e o painel de ações da cama ganhou "Editar
tipo/grupo" além do que já existia. Testado com banco isolado: editar
nome/modalidade/andar de quarto, limpar modalidade, excluir quarto
(cascateando pras camas), editar capacidade/preço/descrição de
modalidade limpando cada campo, mudar cama de solteiro pra beliche e
voltar (grupo é limpo automaticamente ao virar solteiro), rejeição de
beliche sem grupo.

**Depois disso**, o usuário testou trocar o idioma do painel pra
francês e viu que só o menu lateral e o título/subtítulo do topbar
traduziam — abrir qualquer painel (ex: Equipe) mostrava tudo em
português por dentro. Pediu insistentemente tradução **completa**,
"no contexto de hotelaria, sem tradução literal".

**Arquitetura**: reaproveitado o motor que já existia (mas só na
landing page) — extraído pra `assets/js/i18n-core.js`, compartilhado
agora por `dashboard.html` e `index.html`. Dicionário do Dashboard em
`assets/js/i18n-dashboard-data.js`, ~570 chaves × 5 idiomas
(PT/EN/ES/FR/DE), cobrindo as 13 seções do painel (Dashboard, Chats,
Reservas — incluindo morador de longa duração —, Mapa de Quartos,
Opportunity Center, Hóspedes, Operações, Equipe, Financeiro, Estoque,
Receitas, Relatórios, Configurações com suas 7 sub-abas) mais o painel
Ask StayFlow: texto estático (via atributos `data-i18n` /
`data-i18n-placeholder` / `data-i18n-title`), conteúdo montado em JS
(helper `T(chave, texto_pt_de_fallback)`) e as mensagens de
`alert`/`confirm`/`prompt` escritas no próprio frontend (as que vêm do
backend, tipo `data.message`, ficam de fora — ver "fora de escopo"
abaixo). `chats-live.js` e `stayflow-live.js` também passaram pelo
mesmo tratamento (incluindo nomes de mês e "Hoje"/"Ontem" traduzidos
pro divisor de data do chat).

Um bug real foi achado e corrigido no meio do processo: o card de
status do WhatsApp/Backend em Configurações e a URL do webhook tinham
`data-i18n` colocado errado — como o JS sobrescreve esse texto no
carregamento da página com o status real ("Backend conectado" etc.),
trocar de idioma DEPOIS disso ia reverter o texto pra um placeholder
traduzido, apagando a informação real. Corrigido removendo o
`data-i18n` desses elementos específicos e traduzindo a string dentro
do próprio JS que a define.

Troca de idioma não recarrega tudo de uma vez (evita bater ~15
requisições no backend simultâneas): a página ATIVA no momento da
troca recarrega os dados na hora; as outras ficam marcadas como
"sujas" e recarregam sozinhas na próxima vez que a pessoa realmente
abrir aquela seção.

Landing page (`index.html`) migrada pro mesmo motor compartilhado
(tinha o próprio, duplicado, só com PT/EN/ES) — francês e alemão
adicionados aos ~70 textos existentes, sem mexer no dropdown visual
que já funcionava.

Verificação: balanceamento de chaves/parênteses/colchetes em todo
arquivo tocado, e um script de cobertura cruzada (todo `data-i18n` /
`data-i18n-placeholder` / `data-i18n-title` / `T('chave'` usado no
HTML/JS tem que existir no dicionário, e todo idioma tem que ter
exatamente as mesmas chaves que os outros) — rodado várias vezes ao
longo do trabalho, sempre limpo antes de sincronizar.

**Fora de escopo, decisão explícita**: mensagens de erro que vêm
prontas do backend Flask (`jsonify({"message": "..."})`, espalhadas
por `routes/*.py` e `database.py`) continuam em português. Traduzir
isso direito exigiria o backend devolver códigos de erro em vez de
texto pronto — projeto maior, separado, tocando o outro repositório.
Efeito prático: alguém usando o painel em alemão vê a interface toda
traduzida, mas um erro vindo do servidor ainda aparece em português.

### Nona rodada da Sessão 8 (mesma data) — bugs reais na IA de atendimento
### via WhatsApp (idioma, contagem de diárias, coleta de dados)

Usuário testou a IA de atendimento (WhatsApp) com dois números
diferentes e relatou três problemas reais:
1. Num teste em inglês, a IA trocou de idioma pra português sozinha no
   meio da conversa.
2. Na mesma conversa, pediram reserva de sexta a domingo e a IA disse 5
   diárias em vez do correto — a IA estava calculando datas de cabeça
   (subtração de calendário é exatamente o tipo de conta que um LLM
   erra), sem nenhuma ferramenta garantindo o número certo.
3. Num segundo teste (em espanhol, sem o problema de idioma), a
   conversa não completou a captura de dados depois que o hóspede
   confirmou a reserva — o usuário quer nome completo, telefone, email,
   documento e nacionalidade coletados em ordem, de forma sistemática,
   a partir do momento em que a reserva é confirmada.

**Idioma**: a tabela `guests` já tinha uma coluna `language`, mas
nenhum lugar do código lia ou escrevia nela — o idioma "estabelecido"
não sobrevivia entre mensagens, a IA reconstruía a impressão de idioma
relendo o histórico a cada vez, o que é frágil. Corrigido com o mesmo
padrão já usado pra nome/data de nascimento: nova ferramenta
`save_guest_language`, chamada assim que o idioma é detectado (ou
trocado a pedido explícito do hóspede) e persistida via
`update_guest_language`; o idioma já salvo é lido ANTES de cada chamada
à IA (`get_guest_language`) e reforçado explicitamente no prompt
("o idioma já estabelecido é X, nunca troque sozinho — uma palavra
estrangeira ou emoji ocasional não é pedido de troca").

**Contagem de diárias**: nova ferramenta `calculate_nights`
(check-in/check-out → número exato de noites, calculado em Python, não
pelo modelo) — o prompt agora proíbe explicitamente contar dias de
cabeça e exige chamar essa ferramenta antes de cotar preço ou noites ao
hóspede. Além disso, `create_reservation_from_chat` (que já calculava
`nights` internamente pra saber o valor da reserva) passou a devolver
esse número no resultado da própria reserva, pra IA usar o valor real
salvo ao confirmar com o hóspede em vez de recalcular.

**Captura de dados**: a seção do prompt sobre registro pós-reserva foi
reescrita como checklist explícita e ordenada (nome legal completo,
telefone, email, nacionalidade, data de nascimento, foto do
documento) — o momento-gatilho é a criação da reserva, e a IA é
instruída a não considerar a conversa encerrada até ter passado pelos
seis itens. Nacionalidade é campo novo: coluna `guests.nationality`,
função `save_guest_nationality` e ferramenta correspondente (mesmo
padrão de `save_guest_date_of_birth`, que já existia).

Testado sem gastar chamada real à IA: banco isolado confirmando
persistência de idioma e nacionalidade, cálculo de 2 diárias pra
sexta→domingo (e valor batendo com preço configurado), e uma simulação
completa do loop de tool-calling do `ask_ai()` com respostas falsas do
modelo (`client.chat.completions.create` trocado por uma função de
teste) confirmando que as três ferramentas novas (idioma, noites,
nacionalidade) são chamadas e processadas corretamente de ponta a
ponta antes de qualquer teste real em produção.

### Décima rodada da Sessão 8 (mesma data) — Dashboard (home) sem tradução
### + Resumo Executivo da IA sempre em português

Usuário testou a troca de idioma de novo (francês) e mandou print: o
menu lateral e o título do topbar traduzem certinho, mas a PÁGINA
Dashboard em si (a primeira tela depois do login — cards de KPI,
"Resumo Executivo da IA", "Operação", "Atividades de hoje", "Ações
prioritárias") continuava inteira em português. Essa seção
especificamente tinha ficado de fora de todo o trabalho de tradução da
rodada anterior — um `data-i18n` esquecido em toda a home, não em
seções específicas.

Dois problemas diferentes, corrigidos os dois:

1. **Conteúdo estático da home** (rótulos dos KPIs, títulos dos
   cards, textos padrão de "nenhum dado ainda", cabeçalhos de tabela):
   simplesmente nunca tinham recebido `data-i18n` — corrigido com o
   mesmo padrão usado no resto do Dashboard, ~35 chaves novas × 5
   idiomas.

2. **Texto gerado pela IA** ("O hostel possui X hóspedes..." e as
   "Ações recomendadas"): esse é conteúdo de verdade gerado por uma
   chamada à OpenAI (`routes/executive.py`), com o prompt
   explicitamente mandando "use português", sem nenhuma noção de qual
   idioma o gestor está usando no painel. Corrigido: o endpoint
   `/executive-summary` agora aceita `?lang=` (o frontend manda o
   idioma atual do Dashboard), o prompt pede o resumo no idioma pedido
   em vez de fixo em português, e o fallback (usado se a chamada à IA
   falhar) tem uma versão traduzida pronta pra cada um dos 5 idiomas —
   não depende da IA responder certo pra pelo menos mostrar algo no
   idioma correto.

Esse mesmo problema (texto gerado pela IA sempre em português,
independente do idioma escolhido no painel) provavelmente também
afeta o campo `next_action` das oportunidades (preenchido pela IA de
atendimento/motor de decisão) — não foi mexido nesta rodada, fica
registrado como pendência conhecida pra próxima vez que aparecer.

### Décima primeira rodada da Sessão 8 (25/07) — varredura completa de
### todo texto gerado pelo backend que sempre saía em português

Usuário, já impaciente (com razão — travamos bastante tempo nisso),
pediu pra resolver de vez TODO lugar que sempre sai em português,
não só o que já tinha sido corrigido. Foi feito um mapeamento
sistemático de toda chamada à OpenAI no backend (só existiam 4 no
projeto inteiro) e de todo texto persistido no banco que é exibido no
Dashboard, pra fechar os buracos restantes:

1. **Ask StayFlow** (`/ask`, `ask_agent_service.py`): o prompt tinha
   "Responda em português" fixo. Agora `ask_agent()` recebe `lang` (o
   idioma atual do Dashboard de quem está perguntando, mandado pelo
   frontend em toda chamada) e instrui o modelo a responder nesse
   idioma — sem depender de detecção, já que aqui (diferente do
   hóspede no WhatsApp) o idioma de quem pergunta é sempre conhecido
   de antemão pela própria sessão do painel.

2. **Oportunidades** (`description`/`next_action`, mostrados no
   Opportunity Center, nas "Ações prioritárias" do Dashboard e no
   "Resumo da IA" do perfil do hóspede em Chats): esse texto é gerado
   UMA VEZ, no momento em que a mensagem do hóspede chega (motor de
   decisão `decision_engine.py`, sempre em português, gravado assim no
   banco pra sempre) — diferente do resumo executivo, não dá pra só
   "pedir em outro idioma" achar na hora, o texto já existe gravado.
   Solução: novo `services/translation_service.py` com
   `translate_opportunity_fields()` — na hora de LER as oportunidades
   (`GET /opportunities` e `GET /guests/<id>`), se o idioma pedido não
   for português, os textos são traduzidos em UMA chamada em lote à
   OpenAI (nunca uma chamada por oportunidade, pra não multiplicar
   custo/latência a cada carregamento de tela) antes de devolver pro
   frontend. Pedido em português continua sem nenhum custo extra
   (passthrough direto, sem chamar a IA de tradução). Se a tradução
   falhar por qualquer motivo, devolve o texto original em português
   em vez de quebrar a tela.

Isso também resolve de graça o mesmo problema em qualquer oportunidade
criada sem IA (ex: a trava de overbooking do Mapa de Quartos, que
grava uma frase fixa em português direto no banco) — como a tradução
acontece na leitura, não na escrita, qualquer oportunidade antiga ou
nova passa pelo mesmo filtro.

**Deixado em português de propósito** (não é lacuna, é decisão): a
mensagem sugerida de reposição a fornecedor (Estoque → "Copiar
mensagem"). Essa mensagem é pro FORNECEDOR ler, não pro gestor — trocar
pro idioma do painel do gestor arriscaria mandar uma mensagem no
idioma errado pra alguém que não usa o StayFlow (ex: gestor usando o
painel em francês, fornecedor local que só entende português/espanhol).

Testado sem gastar chamada real: passthrough de português (zero
chamada à API), idioma inválido (mesmo passthrough), tradução em lote
simulada com resposta falsa da API confirmando o mapeamento de volta
pros campos certos, e falha da API caindo de volta pro texto original
sem quebrar.

### Décima segunda rodada da Sessão 8 (28/07) — oportunidade avaliada
### por conversa, não por mensagem

Usuário notou (raciocínio correto, sem ser um "bug" no sentido de algo
quebrado — mais um problema de design) que toda mensagem nova de um
hóspede gerava uma oportunidade nova, mesmo sendo a mesma conversa
continuando. Isso lotava o Opportunity Center com várias linhas do
mesmo assunto e fazia o sino de alertas disparar de novo a cada
mensagem, mesmo sem nada realmente novo ter acontecido.

Causa raiz, em `decision_engine.py`: `analyze_with_ai()` recebia só a
ÚLTIMA mensagem isolada, sem nenhum contexto da conversa — e
`analyze_message()` sempre fazia `INSERT` de uma linha nova em
`opportunities`, nunca verificava se já existia uma aberta pra aquele
hóspede.

**Correção, duas partes:**
1. `analyze_with_ai()` agora recebe o histórico recente da conversa
   (mesmo formato já usado pra IA de atendimento) e monta um bloco
   "Conversa até agora" no prompt — o modelo julga a intenção com
   contexto real, não uma mensagem solta ("sim" ou "pode ser dia 20"
   só fazem sentido junto do que veio antes).
2. `analyze_message()` agora verifica se já existe uma oportunidade
   ABERTA do mesmo hóspede com o mesmo `type` (booking, tour, etc) —
   se existir, faz `UPDATE` nela (description/score/urgency/
   estimated_value/next_action, e `created_at` também é atualizado,
   já que não é exibido como data de criação em lugar nenhum da
   interface — funciona como "última atividade", fazendo a conversa
   ativa subir pro topo da lista). Só cria uma linha nova quando é
   realmente um assunto diferente (ex: pediu um tour no meio de uma
   conversa de reserva).

`routes/chat.py` ajustado pra buscar o histórico uma vez só (antes só
buscava depois, só pra IA de atendimento) e reaproveitar pra análise
de oportunidade e pra IA de atendimento, evitando uma segunda leitura
da mesma conversa.

Efeito prático: uma conversa inteira sobre a mesma reserva agora vira
UMA linha no Opportunity Center que vai se atualizando (fica mais
urgente/mais completa conforme a conversa avança), em vez de várias
linhas duplicadas — e o sino só soa de novo quando a contagem de
alertas abertos realmente aumenta (lógica que já existia no frontend),
o que agora reflete assuntos de verdade, não mensagens.

Testado sem gastar chamada real à IA (respostas simuladas): 3
mensagens de teste (2 sobre reserva + 1 sobre tour) resultaram em
exatamente 2 linhas na tabela (a de reserva foi atualizada com os
dados da segunda mensagem, não duplicada); histórico da conversa
confirmado presente no prompt enviado pro modelo; e teste de
reordenação confirmando que um hóspede que voltou a escrever sobe pro
topo da lista de oportunidades.

### Décima terceira rodada da Sessão 8 (28/07) — caixas de alerta com a
### cara do StayFlow, em vez da caixa branca do sistema operacional

Usuário pediu: os `alert()`/`confirm()`/`prompt()` nativos do
navegador (caixa branca, cara de sistema operacional) deveriam virar
uma caixa azul com a identidade visual do StayFlow. Mapeado: 78
`alert()`, 10 `confirm()` e 8 `prompt()` só no `dashboard.html`, mais 4
`alert()` em `chats-live.js` — 100 pontos ao todo.

**Problema técnico real por trás disso**: `confirm()`/`prompt()`
nativos são SÍNCRONOS (travam a página até a pessoa responder, e o
valor volta na hora) — um modal de verdade, feito com HTML/CSS/JS, não
consegue travar a thread desse jeito. Não dá pra só "trocar a cor" do
`confirm()` nativo; ele precisa virar assíncrono (`Promise`), e todo
lugar que chamava `confirm()`/`prompt()` esperando o valor na hora
precisa passar a usar `await`.

**Solução, duas partes diferentes:**
1. `alert()`: como nenhum lugar do código usa o valor de retorno nem
   depende do bloqueio síncrono de verdade (é sempre "mostra e
   segue"), dava pra simplesmente SOBRESCREVER `window.alert` uma
   única vez com uma versão que abre o modal azul (sem travar nada) —
   os 82 pontos (78 + 4) foram resolvidos de graça, sem tocar em
   nenhum dos call sites.
2. `confirm()`/`prompt()`: como o valor de retorno É usado de verdade
   (`if(!confirm(...)) return;`), esses não dava pra sobrescrever sem
   quebrar o comportamento (um `confirm()` que sempre retorna `true`
   sem perguntar nada seria perigoso — ex: excluiria uma cama sem
   confirmar de verdade). Criadas duas funções novas,
   `stayflowConfirm()`/`stayflowPrompt()`, que devolvem uma Promise, e
   os 18 pontos reais (10 confirm + 8 prompt) foram convertidos um por
   um pra `await stayflowConfirm(...)`/`await stayflowPrompt(...)`,
   dentro de funções `async` (a maioria já era; 3 listeners de
   `change` em `<select>` precisaram virar `async () => {...}`).

Modal novo (`#sfAlertOverlay`/`#sfAlertModal`) usa o mesmo padrão
visual já existente do `.generic-modal` (fundo azul-marinho escuro,
borda sutil), com um ícone circular azul no topo — não reaproveita o
MESMO elemento DOM do modal genérico (usado pelas telas de Equipe) pra
evitar os dois tentarem abrir ao mesmo tempo. Fecha com Esc, com clique
fora, ou com os botões — clique fora/Esc conta como "cancelar"
(resolve `false`/`null`, nunca `true`).

Balanceamento de chaves/parênteses/colchetes conferido no
`dashboard.html` depois da conversão inteira, e checagem de cobertura
cruzada de i18n confirmando que a chave nova (`common.cancel`) existe
nos 5 idiomas.

## Décima quarta rodada: Mapa de Quartos — menu de ações em vez de caixas fixas

Pedido do usuário: a aba "Mapa de Quartos" tinha, além do card do mapa
em si, mais cinco cards fixos sempre visíveis (Modalidades de quarto,
Novo quarto, Nova cama, Lista de limpeza do dia, Devolver da
lavanderia) — cada um ocupando metade da largura da tela. Isso deixava
o mapa visual dos quartos (o conteúdo que a pessoa realmente quer ver
o tempo todo) espremido lá embaixo, depois de uma parede de
formulários. Pedido: juntar tudo isso numa caixa só, tipo um menu
hambúrguer, e abrir um modal central quando a pessoa escolhe o que
quer criar — deixando o espaço da página só para os quartos.

**Mudança de estrutura:** a seção `#roommap` agora tem um único card
(`span-12`) com o mapa (legenda + grid + painel de ação de cama) e,
no cabeçalho do card, um botão "☰ Ações" que abre um dropdown (mesmo
componente visual `.hostel-selector-dropdown` já usado no seletor de
hostel/idioma/usuário no topbar). Cada item do dropdown chama uma
função nova que monta o HTML do formulário correspondente e abre no
modal genérico já existente (`openGenericModal`/`closeGenericModal`,
o mesmo usado pelo painel de Equipe e pelos modais de editar
quarto/cama/modalidade): `openCreateCategoryModal()`,
`openCreateRoomModal()` (quarto único + em lote, no mesmo modal),
`openCreateBedModal()`, `openCleaningListModal()`,
`openLaundryReturnModal()`.

**Detalhe técnico que exigiu cuidado:** os formulários antigos viviam
fixos dentro de `#roommap` e algumas funções JS localizavam os campos
deles via seletor amarrado à seção (ex:
`document.querySelectorAll("#roommap select[name='category_name']")`).
Como agora esses formulários só existem no DOM quando o modal está
aberto (o `innerHTML` é montado na hora), troquei esse seletor por
IDs diretos (`#roomCategorySelect`, `#bulkRoomCategorySelect`) que
funcionam em qualquer lugar do documento, modal aberto ou não. Como
`getElementById`/`querySelectorAll` simplesmente não encontram nada
quando o modal está fechado (sem lançar erro), `loadRoomMap()`
continua rodando normal toda vez que a aba abre — só não escreve nada
nos campos que não existem na hora, e escreve certinho quando o
modal é aberto depois, porque o HTML de cada modal já nasce pré-
preenchido com os dados em cache (`ROOM_CATEGORIES_CACHE`,
`ROOM_MAP_ROOMS_CACHE`, que já são atualizados pelo `loadRoomMap()`
sempre que a aba é aberta).

**Decisão de UX:** os modais de criar categoria/quarto/cama NÃO fecham
sozinhos depois de criar um item — o formulário só é limpo (`.reset()`)
e a lista/seletor dentro do próprio modal se atualiza na hora. Isso é
proposital: montar um hostel do zero envolve criar vários quartos e
várias camas em sequência (ex: um dormitório com 8 camas), e forçar
reabrir o menu ☰ a cada item seria pior do que o modelo antigo. Já o
modal de "Devolver da lavanderia" também não fecha sozinho, pelo
mesmo motivo (entradas repetidas). A lista de limpeza, dentro do seu
próprio modal, continua se atualizando ao vivo quando uma cama é
marcada como limpa (a função existente já escreve nos mesmos IDs,
então funciona sem mudança nenhuma nela).

Chave `roommap.emptyDesc` (texto do estado vazio do mapa) foi
substituída por `roommap.emptyDesc2`, que menciona o novo menu "☰
Ações" em vez de "crie modalidades e quartos abaixo" (não fazia mais
sentido com o formulário fora da tela) — a chave antiga, órfã, foi
removida dos 5 idiomas. Duas chaves novas (`roommap.actionsMenu.label`,
`roommap.actionsMenu.title`) traduzidas nos 5 idiomas; todo o resto do
conteúdo dos modais reaproveita chaves de i18n que já existiam
(`roommap.categories.*`, `roommap.newRoom.*`, `roommap.newBed.*`,
`roommap.cleaning.*`, `roommap.laundry.*`), sem duplicar tradução.

Balanceamento de chaves/parênteses/colchetes conferido no
`dashboard.html` e no `i18n-dashboard-data.js`, e checagem de
cobertura cruzada de i18n confirmando 0 chaves faltando nos 5
idiomas.

## Décima quinta rodada: botão de assumir/devolver chat vira o próprio botão de enviar

O usuário confirmou que o botão "Assumir conversa" (aba Chats, ao lado
do Score) existia e funcionava, mas achou o visual feio — um botão
secundário cinza solto ao lado do título, some/aparece por texto sem
nenhuma pista de cor. Pedido: fazer o próprio botão "Enviar" cumprir
esse papel. Enquanto a IA está no controle da conversa, esse botão
fica **verde** e escrito "Assumir"; ao clicar, assume a conversa (não
envia nada — não faz sentido digitar pra IA responder por você) e o
botão vira o azul normal, escrito "Enviar". Ao lado dele aparece um
botão "Devolver" — só visível quando a conversa está assumida por um
humano — que devolve o controle pra IA; ao devolver, esse botão some
de novo e o de enviar volta a ficar verde/"Assumir".

Removido o antigo `#chatTakeoverBtn` (ficava ao lado do "Score: —").
O botão de enviar (`#chatSendBtn`) ganhou um atributo `data-mode`
("assume" ou "send") que o dispatcher `chatPrimaryBtnClick()` lê pra
decidir se chama `assumeChatUI()` ou o `sendMessageToGuestUI()` já
existente — evita o bug sutil que o código antigo tinha (decidir a
ação comparando o `textContent` do botão com o texto traduzido, que
quebraria se o idioma mudasse no meio do caminho). `toggleChatTakeover`
foi separado em duas funções explícitas,
`assumeChatUI()`/`giveBackChatUI()`, ambas chamando o mesmo helper
interno `setChatAiPaused(paused)` que já existia (só que agora sem
precisar inferir a direção a partir de texto de UI). `loadGuestProfile`
(em `chats-live.js`) passou a alternar classe `.green` e texto do botão
de enviar, e mostrar/esconder o botão "Devolver", a partir do campo
real `guest.ai_paused` vindo do backend — igual já fazia antes, só que
aplicando em dois elementos em vez de um.

Reaproveitada a classe `.btn.green` que já existia no CSS (usada em
outros botões de ação positiva) — nenhum CSS novo foi necessário.
Os textos dos botões foram encurtados nos 5 idiomas pra caber no
espaço apertado ao lado do campo de mensagem (ex.: "Assumir conversa"
→ "Assumir", "Devolver pra IA" → "Devolver"), reaproveitando as
mesmas chaves de tradução que já existiam (`chats.takeoverBtn`,
`chats.giveBackToAiBtn`) — só o valor mudou, sem novas chaves.

Balanceamento de chaves/parênteses/colchetes conferido no
`dashboard.html` e no `chats-live.js`, e checagem de cobertura cruzada
de i18n confirmando 0 chaves faltando nos 5 idiomas.

## Décima sexta rodada: integração com channel manager (Beds24) — Fase 1 (fundação)

Início do maior projeto desta sessão: conectar o StayFlow a Booking.com,
Airbnb e Hostelworld pra receber reserva automaticamente, sem overbooking
entre canais. Depois de pesquisa de mercado (custo de channel managers,
o que cada um duplicaria do StayFlow) e discussão sobre modelo de
negócio, decisão registrada com o usuário:

- **Beds24** como channel manager (API v2 aberta, webhook de reserva em
  tempo real, preço competitivo — ~€15,90/mês base + ~€3/mês por
  propriedade adicional).
- **Modelo agência/white-label**: UMA conta master do StayFlow no Beds24
  (o usuário já criou, tipo "Vários", 1000+ propriedades), onde cada
  cliente StayFlow vira uma sub-propriedade — nunca cria conta própria,
  nunca vê a marca Beds24, nunca paga separado. Custo absorvido pelo
  StayFlow e embutido no próprio preço.
- Também ficou registrado, como Fase 6 futura, um pedido do usuário:
  webhook de saída genérico, pra clientes que já usam sistema próprio e
  querem o StayFlow só como camada de atendimento/IA — toda reserva
  (de qualquer origem) seria replicada pra uma URL configurável do
  cliente. Reaproveita o mesmo gancho de "reserva criada/alterada" já
  planejado pro push de disponibilidade — ainda não implementado.

Plano completo registrado e aprovado (`EnterPlanMode`/`ExitPlanMode`),
com investigação prévia de codebase (2 agentes Explore, backend e
frontend) confirmando: nenhum campo de mapeamento externo existia em
`reservations`/`rooms`/`beds`/`room_categories`; **os 3 caminhos de
criação de reserva não tinham nenhuma trava contra condição de corrida**
(check-then-act sem transação, em produção via gunicorn com múltiplos
workers reais); nenhuma infraestrutura de criptografia no projeto; nenhum
scheduler/cron.

**Fase 1 implementada** (fundação — ativação da sub-propriedade, sem
ainda receber/enviar reserva de verdade, isso fica pras próximas fases):

- `database.py`: tabelas novas `beds24_master_account` (singleton — é
  UMA conta que vale pra todos os clientes, não tem `hostel_id`),
  `channel_room_mapping` (de-para modalidade StayFlow ↔ quarto Beds24,
  usada na Fase 2), `channel_webhook_events` (idempotência de webhook,
  usada na Fase 3); colunas novas `hostels.beds24_property_id` e
  `reservations.external_booking_id`.
- **`reservar_cama_com_trava(hostel_id, bed_id, checkin, checkout,
  insert_fn)`** (novo, em `database.py`): usa `BEGIN IMMEDIATE` do
  SQLite pra fechar a janela de corrida real que existia entre "checar
  disponibilidade" e "inserir a reserva" — a trava de escrita é pega
  na abertura da transação, não só no primeiro INSERT/UPDATE, então
  serializa de verdade chamadas concorrentes (funciona entre threads E
  entre processos gunicorn diferentes, porque é trava de arquivo, não
  de memória). Aplicada imediatamente em `create_reservation_from_chat`
  (fluxo do WhatsApp — reescrito pra reconferir disponibilidade e
  inserir a reserva numa única transação travada, em vez de 3 conexões
  separadas como antes) — é o outro caminho automático de alta
  frequência que vai disputar cama com o webhook do Beds24 nas próximas
  fases. Deliberadamente NÃO aplicada em `create_reservation_record`
  (entrada manual da equipe, campo de cama é texto livre, baixa
  frequência de disputa real — mudar o comportamento ali seria
  regressão de UX pra um problema que quase não acontece na prática).
- `services/beds24_service.py` (novo): autenticação da API v2 (troca de
  invite code por refresh token, cache + renovação sob demanda do access
  token — sem scheduler, já que o projeto não tem nenhum), `create_property`
  (cria a sub-propriedade de um cliente via `POST /properties`),
  `push_availability` (usado só na Fase 4). Refresh token guardado
  **criptografado** (Fernet/`cryptography`, nova dependência) — único
  desvio do padrão do projeto (token de WhatsApp fica em texto puro),
  justificado porque um vazamento aqui expõe a reserva de TODOS os
  clientes StayFlow de uma vez, não de um hostel só. Chave de
  criptografia numa env var nova, `BEDS24_ENCRYPTION_KEY` — **pendente
  de configurar no Render**, sem ela a ativação da integração falha com
  erro claro (`RuntimeError`), não silenciosamente.
- `routes/settings.py`: rotas novas `GET /settings/beds24` (status:
  conta master pronta? sub-propriedade já ativada?) e `POST
  /settings/beds24/activate` (cria a sub-propriedade pro hostel logado),
  seguindo exatamente o padrão de `/settings/whatsapp`.
- `dashboard.html`: botão "Integrações" do menu de Configurações (antes
  apontava pro placeholder "em breve" da seção `developer`) agora abre
  uma tela de verdade (`data-settings-section="integracoes"`) com três
  estados — conta master não configurada ainda, não ativado (botão
  "Ativar"), ativado (status). Chave i18n órfã `settings.developer.*`
  removida dos 5 idiomas, substituída por `settings.beds24.*` novas.
- `requirements.txt`: `cryptography==49.0.0` adicionado (única
  dependência nova).

**Nota de honestidade técnica**: alguns nomes exatos de campo do corpo
de requisição da API do Beds24 (`POST /properties`, `POST
/inventory/rooms/calendar`) vieram de documentação pública, não de teste
contra a API real — marcados com comentário "confirmar contra API real"
no código. Serão ajustados assim que testarmos com a conta master de
verdade nas próximas fases.

**Configuração real, feita com o usuário passo a passo**: conta master
criada no Beds24 (tipo agência, "Vários"/1000+ propriedades — confirmado
que o painel de revendedor com "Subcontas" existe de verdade, útil pra
fase futura de criar conta por cliente). `BEDS24_ENCRYPTION_KEY` gerada e
configurada no Render. Invite code gerado com escopos Reservas-
Financeiro, Inventário, Propriedades e Canais (leitura+escrita) e Contas
(só leitura), acesso "todos pertencem à conta". `setup_beds24_master.py`
rodado com sucesso via Shell do Render, refresh token salvo criptografado
em produção.

**Bug real encontrado no primeiro teste de ponta a ponta**: clicar em
"Ativar integração com canais" devolveu HTTP 401 do Beds24 ao tentar
criar a propriedade. Causa: `create_property`/`push_availability`
mandavam o access token num header `Authorization: Bearer {token}`
(padrão OAuth2 comum, mas não é o que o Beds24 usa) — a documentação
real confirma que a API v2 do Beds24 espera um header próprio chamado
`token` (`token: {access_token}`), sem "Bearer" na frente. Corrigido nos
dois pontos.

**Segundo bug real, mesmo teste**: corrigido o header, veio HTTP 400
"Request body must be an array" — a API do Beds24 espera o corpo de
`POST /properties` como lista, mesmo pra criar uma propriedade só
(padrão em lote deles, igual o endpoint de disponibilidade já esperava
certo desde o início). Corrigido, e a leitura da resposta foi endurecida
pra aceitar formatos diferentes (lista ou objeto, com ou sem wrapper
`"new"`), com log de debug da resposta bruta em caso de sucesso —
evita precisar de mais uma rodada de tentativa e erro se o formato
mudar de novo.

**Confirmado funcionando em produção**: terceiro teste, botão "Ativar
integração com canais" retornou "Status: Ativado" — a sub-propriedade
do hostel foi criada de verdade dentro da conta master do Beds24. Fase
1 encerrada aqui por hoje; Fases 2-6 (mapeamento de quarto, webhook de
entrada/saída, conexão real com as OTAs) ficam pra próxima sessão.

**Verificação**: `ast.parse` em todo `.py` novo/editado; testes isolados
com banco SQLite de scratchpad (`STAYFLOW_DATA_DIR`) e `requests`
mockado, cobrindo: criptografia round-trip do refresh token, troca de
invite code, cache/renovação de access token, criação de propriedade, e
— o mais importante — `reservar_cama_com_trava` bloqueando de verdade
uma segunda reserva com datas sobrepostas na mesma cama, junto com um
teste completo de regressão de `create_reservation_from_chat` (criação
normal, não-duplicação por reafirmação, bloqueio por cama disputada,
bloqueio por modalidade sem cama) confirmando que o retrofit da trava
não mudou nenhum comportamento existente. Balanceamento de chaves/
parênteses/colchetes e cobertura i18n conferidos no frontend.

**Fases seguintes** (não implementadas ainda, checkpoint com o usuário
entre cada uma): mapeamento de quarto (Fase 2), webhook de entrada de
reserva (Fase 3), push de disponibilidade de saída (Fase 4), conectar
OTA de verdade — ponto em aberto sobre como o cliente final autoriza a
própria conta de Booking/Airbnb sem ver o painel geral do Beds24 (Fase
5), webhook de saída genérico pra cliente com sistema próprio (Fase 6).

## Integração com channel manager (Beds24) — Fase 2 (mapeamento de quarto)

Sessão seguinte, continuando a integração. Antes de receber reserva de
verdade (Fase 3), o hostel precisa dizer qual modalidade do StayFlow
corresponde a qual quarto do Beds24 — sem isso, uma reserva de OTA
chegaria sem saber onde encaixar.

Pesquisada a documentação real da API antes de implementar (aprendendo
com os dois bugs da Fase 1): `GET /properties?propertyId=X&includeAllRooms=true`
(header `token`, mesmo já corrigido) devolve os quartos já cadastrados
na sub-propriedade, dentro de um campo `roomTypes` (lista de
`{id, name}`). Novo `beds24_service.get_property_rooms(property_id)`
busca isso, tolerando tanto resposta em lista quanto objeto direto
(mesma cautela da Fase 1, já que o formato exato varia por endpoint).

`database.py` ganhou `get_channel_room_mappings` (junta `room_categories`
do hostel com o mapeamento existente via `LEFT JOIN`, pra sempre mostrar
todas as modalidades mesmo as ainda não mapeadas), `save_channel_room_mapping`
(upsert via `ON CONFLICT`, mesmo padrão já usado na Fase 1) e
`delete_channel_room_mapping`. `routes/settings.py` ganhou
`GET/POST /settings/beds24/room-mapping` e
`DELETE /settings/beds24/room-mapping/<room_category_id>`.

Na tela de Configurações → Integrações, a área que antes só dizia
"Ativado" ganhou a lista de verdade: uma linha por modalidade do
hostel, com um `<select>` das opções vindas do Beds24 e botão Salvar —
escolher "nenhum" e salvar remove o mapeamento. Reaproveita
`list_room_categories` que já existia (mesma função usada pelo Mapa de
Quartos), sem duplicar consulta.

**Verificação**: testes isolados cobrindo criação/atualização (upsert)
de mapeamento, bloqueio ao mapear modalidade que não existe/não é do
hostel, remoção, busca inversa (quarto Beds24 → modalidade StayFlow,
já pronta pro webhook da Fase 3), e `get_property_rooms` com resposta
mockada em lista e em objeto direto. Balanceamento de chaves/parênteses
e cobertura i18n conferidos no frontend.

**Ajuste em produção, testado ao vivo pelo usuário**: primeiro teste real
mostrou o seletor de quarto vazio — esperado, já que a sub-propriedade
criada na Fase 1 nasce sem nenhum quarto cadastrado no Beds24. Em vez de
mandar o usuário criar o quarto manualmente no painel deles (quebraria a
promessa de nunca precisar abrir o Beds24), foi adicionado
`beds24_service.create_room_type(property_id, room_name)` — usa o mesmo
`POST /properties`, mas com `id` da propriedade existente + `roomTypes`
no corpo (`[{"id": ..., "roomTypes": [{"name": ...}]}]`, formato
confirmado na documentação antes de implementar, aprendendo com os bugs
da Fase 1). Nova rota `POST /settings/beds24/create-room` e um segundo
botão "Criar no Beds24" ao lado de cada modalidade sem mapeamento —
cria o quarto lá e já vincula automaticamente, fechando o fluxo sem
sair do StayFlow.

**Faxina**: encontradas (e removidas) duas cópias obsoletas do diário e
do master context — uma commitada há muito tempo direto na raiz do
repositório `HostelBot` (`docs/`, de antes da convenção atual, parada em
07/07), outra solta e nunca commitada dentro de
`HostelBot/StayFlow---Site/docs/` (sobra de antes do robocopy passar a
excluir essa pasta da sincronização, parada em 22/07). Nenhum conteúdo
único perdido — a versão em `StayFlow---Site/docs/` sempre teve tudo
isso e mais.

**Feedback do usuário testando ao vivo, com screenshot real**: o
seletor de quarto apareceu com "Camas24" no lugar de "Beds24" — o
tradutor automático do navegador traduzindo "Beds" literalmente, porque
o nome da plataforma aparecia cru na tela. Aproveitando, o usuário
deixou clara uma diretriz de produto pra esta integração toda: **o
cliente final nunca deve sentir que existe qualquer outra plataforma no
meio** — precisa parecer 100% StayFlow, mesmo sabendo (pelos nomes de
Booking/Airbnb/Hostelworld, que continuam visíveis de propósito) que
existe sincronização com canais de venda reais.

Removida toda menção literal a "Beds24" e a "channel manager" dos
textos visíveis, nos 5 idiomas: "Selecione o quarto no Beds24..." →
"Selecione o quarto sincronizado...", "Criar no Beds24" → "Criar
automaticamente", mensagens de erro reescritas no mesmo espírito.
Nomes de função internos (`loadBeds24Settings`, `createBeds24RoomForCategory`
etc.) e `console.warn` de depuração mantidos como estão — não são
visíveis pro usuário, só pra manutenção do código.

Também corrigidos dois problemas reais expostos pelo mesmo teste: (1)
faltava uma mensagem de sucesso clara depois de criar o quarto
automaticamente — o usuário não conseguia saber se tinha funcionado só
olhando o estado da tela; adicionada `settings.beds24.createRoomSuccess`.
(2) o seletor de quarto podia aparecer vazio/sem opção selecionada logo
depois de criar um quarto novo, se o Beds24 demorasse um instante pra
refletir esse quarto na consulta seguinte (`GET /properties` logo em
seguida ao `POST` de criação, consistência eventual do lado deles) — o
`<select>` agora injeta uma opção extra pro quarto mapeado mesmo que
ele ainda não apareça na lista vinda do Beds24, evitando a aparência de
"não funcionou" quando na verdade só está sincronizando.

**Causa raiz real da confusão (achada testando ao vivo)**: não era bug
do StayFlow nenhum dos dois — "Compartilhado" (nome de modalidade
gravado certinho no banco) virando "Compartmentalhado" na tela era o
mesmo sintoma de "Beds24" virando "Camas24": o **tradutor automático do
próprio navegador** (Edge/Chrome) reprocessando uma página que já está
em português (ou já tem tradução própria via seletor de idioma),
bagunçando texto estático e, possivelmente, interferindo em conteúdo
inserido dinamicamente por JavaScript (explicaria a caixa de aviso
aparecer vazia depois de criar o quarto).

Usuário corretamente apontou que desativar a tradução só no próprio
navegador não resolveria pra nenhum cliente real que tivesse a mesma
configuração ligada. Correção aplicada direto no código, de uma vez pra
sempre: `<meta name="google" content="notranslate">` no `<head>` +
atributo `translate="no"` na tag `<html>` de `dashboard.html`,
`Login.html`, `Register.html` e `index.html` (esse último já tinha o
meta tag de uma sessão anterior, só faltava o atributo `translate`).
Isso é o sinal padrão da web pra qualquer tradutor de navegador (Google
Translate, Microsoft Translator no Edge) não oferecer/aplicar tradução
automática — a tradução do StayFlow continua existindo, só que
exclusivamente pelo seletor de idioma próprio do produto, nunca por
inferência do navegador.

**Bug real encontrado, mesmo teste**: o botão "Salvar" do mapeamento de
quarto não dava nenhum retorno visível quando funcionava — só mostrava
mensagem em caso de erro. Usuário salvou um mapeamento já correto (o
mesmo id que a criação automática já tinha vinculado) e, sem nenhuma
confirmação na tela, concluiu que "não salvou". Corrigido: sucesso
agora mostra `settings.beds24.mappingSaveSuccess` ("Mapeamento salvo
com sucesso!"), mesmo padrão do botão de criar quarto.

Também investigando por que o seletor continuava mostrando
"(sincronizando...)" mesmo depois de recarregar a página — mais do que
o esperado pra uma simples demora de consistência eventual do Beds24.
Adicionado log de depuração em `get_property_rooms` (resposta bruta da
listagem + lista já parseada) pra comparar, nos logs do Render, o id do
quarto capturado na hora de criar contra o id que a listagem realmente
devolve depois — vai apontar se é só demora real ou se há uma
divergência de formato entre os dois pontos que merece correção.

**Causa raiz real, achada nos logs**: existiam dois quartos duplicados
chamados "privado" no Beds24 (ids diferentes) — o usuário, vendo
"sincronizando" persistir, concluiu (razoavelmente) que a primeira
criação tinha falhado e clicou em "Criar automaticamente" de novo pra
mesma modalidade, criando um segundo quarto. Não era perda de dado nem
erro de parsing — era falta eventual de consistência real do lado do
Beds24 (a listagem seguinte ao `POST` de criação nem sempre já reflete
o quarto novo na hora) combinada com uma UI que convidava a repetir a
ação.

**Correção da causa raiz, não só do sintoma**: o botão "Criar
automaticamente" agora só aparece pra modalidade que **ainda não tem
nenhum vínculo** — uma vez mapeada (mesmo que temporariamente mostrando
"sincronizando..."), o botão de criar some, restando só "Salvar" (útil
se quiser trocar pra outro quarto já existente). Frontend também passou
a esperar 3 segundos antes de recarregar a lista depois de criar (dá
tempo real pro Beds24 refletir), e a mensagem de sucesso passou a
avisar explicitamente que pode levar alguns segundos pra aparecer com o
nome certo — a pessoa agora sabe que é uma espera esperada, não uma
falha, sem precisar adivinhar.

**Correção da correção — o diagnóstico acima estava errado.** Depois de
esperar e recarregar várias vezes sem o "sincronizando..." nunca sair
do lugar, ficou claro que não era demora nenhuma. Usuário pediu (com
razão) pra parar de tentar adivinhar e investigar com dado real dos
logs — processo feito passo a passo, isolando cada hipótese: busca por
`Quartos parseados` (o log de sucesso) não trouxe nenhum resultado, nem
`Erro ao listar quartos` (falha HTTP) — sobrou só
`Resposta do Beds24 sem roomTypes`, que trouxe o corpo bruto da
resposta e revelou a causa raiz de verdade: **a suposição de formato
estava errada desde o início**. O código esperava um objeto de
propriedade com uma chave `roomTypes` aninhada contendo a lista de
quartos (é o que a documentação pública do Beds24 dava a entender); a
API real devolve a **lista de quartos direto**, sem esse envelope — os
dois quartos "privado" (ids 712413/712414) estavam lá o tempo todo,
criados com sucesso, só que o parsing nunca os encontrava porque
procurava no lugar errado.

Corrigido `get_property_rooms` pra aceitar os dois formatos (lista
direta de quartos, ou objeto de propriedade com `roomTypes` dentro),
com testes cobrindo especificamente o formato real observado nos logs,
o formato hipotético antigo (mantido por segurança) e propriedade sem
nenhum quarto. `create_room_type` (a função que cria o quarto) não
precisou de correção — a suposição de formato dela pra resposta de
criação se confirmou certa pelos próprios ids extraídos, que bateram
com os dois quartos reais vistos na listagem.

**Lição registrada**: quando um sintoma "quase resolve mas não resolve
de vez" depois de uma correção, vale suspeitar de causa raiz diferente
da hipótese inicial, em vez de só reforçar a mesma explicação (nesse
caso, "só espera mais um pouco"). Isolar por eliminação nos logs (qual
das 3 saídas possíveis da função realmente aconteceu) achou a causa
real em poucos passos, mais rápido do que qualquer tentativa adicional
de ajuste de tempo de espera teria achado.

**Terceira e última correção — a "causa raiz real" acima também estava
incompleta.** Depois de subir a correção anterior, `beds24_rooms`
continuava vindo vazio, mesmo com o deploy confirmado no ar. Usuário
pediu explicitamente pra parar de remendar em cima de suposição e
resolver "direito" — criada uma rota de diagnóstico temporária
(`GET /settings/beds24/debug-raw`, removida depois de usar) que devolve
a resposta da Beds24 **sem nenhuma interpretação**, direto no navegador.
Isso revelou o formato real, de uma vez por todas: um dict com uma
chave `"data"` (lista), e é dentro do primeiro item dessa lista que
mora `"roomTypes"` — ou seja, `resposta["data"][0]["roomTypes"]`.
Nenhuma das duas tentativas anteriores (lista direta de quartos; dict
com `roomTypes` direto no topo) cobria esse caminho. Corrigido de vez,
com teste cobrindo o formato real confirmado + os formatos antigos
mantidos como fallback (não custam nada e protegem contra a Beds24
variar o formato dependendo de parâmetro/conta no futuro).

De brinde, a rota de diagnóstico também expôs que existem vários
quartos duplicados "Compartilhado"/"privado" na propriedade de teste,
resultado dos vários cliques em "Criar automaticamente" durante as
tentativas anteriores — inofensivo (cada um tem um id próprio, o
seletor só fica com mais opções repetidas), mas o usuário pode limpar
manualmente no painel do Beds24 se quiser deixar arrumado.

## Integração com channel manager (Beds24) — exclusão de quarto sem uso

Usuário pediu pra já construir a exclusão de quarto (em vez de só
limpar manual dessa vez), já que vai ser necessária de qualquer forma —
com o pedido explícito de pensar em travas de segurança e não fazer
gambiarra.

**Endpoint não confirmado contra documentação real** (a wiki pública do
Beds24 bloqueou acesso automatizado nas tentativas de pesquisa) —
implementado com a melhor suposição informada, seguindo o padrão já
confirmado de outros endpoints (`DELETE /properties/rooms` com
`propertyId`/`roomId` via query string, header `token`). Diferente das
vezes anteriores, isso **não foi declarado como resolvido sem teste
real** — combinado com o usuário testar uma exclusão de verdade,
olhando a resposta crua, antes de confiar na função.

**Duas travas de segurança implementadas** em `DELETE
/settings/beds24/rooms/<beds24_room_id>`:
1. Bloqueia apagar quarto que ainda está vinculado a uma modalidade —
   usa `get_room_category_id_by_beds24_room_id` (já existia da Fase 2)
   pra checar antes; força desvincular primeiro.
2. Confere contra a lista real de quartos da propriedade
   (`get_property_rooms`) que o quarto pedido realmente pertence a
   **este** hostel antes de tentar apagar — importante porque a conta
   master do Beds24 é compartilhada entre todos os clientes do
   StayFlow; sem essa trava, um cliente poderia (por acidente ou não)
   tentar apagar quarto de outro.

**Frontend**: nova seção "Quartos sem uso" na tela de mapeamento,
listando só os quartos do Beds24 que não estão vinculados a nenhuma
modalidade (`beds24_rooms` menos os que aparecem em `categories`,
calculado no backend), cada um com botão "Remover" atrás de
`stayflowConfirm()` — mesmo padrão de confirmação de exclusão já usado
no resto do sistema.

**Verificação**: testes isolados cobrindo a chamada HTTP (parâmetros
corretos, erro tratado) e as duas travas de segurança (banco já testado
na Fase 2, reaproveitado aqui). A chamada real à API ainda precisa ser
confirmada com o usuário — ver próxima entrada.

**Teste real: `DELETE /properties/rooms` não funciona.** Duas
tentativas, a segunda já com log melhorado pra trazer o corpo da
resposta da Beds24 — ambas HTTP 500, e a segunda confirmou que o corpo
da resposta vem **vazio**, sem nenhum detalhe de erro pra investigar.
Não é erro de parâmetro (esses normalmente vêm com mensagem); tudo
indica que o endpoint tentado nem existe do jeito suposto — só a
documentação oficial ou o suporte da Beds24 resolveriam com certeza
essa dúvida, e ambos ficaram inacessíveis pra mim nesta sessão.

**Decisão, com o usuário de acordo**: parar de tentar adivinhar
endpoint de exclusão às cegas — cada tentativa falha sem dar pista
nova, só custa tempo e frustração sem necessidade real (a funcionalidade
principal, mapeamento, já funciona). Botão "Remover" retirado da UI (um
botão que não funciona é pior que não ter botão) — a seção "Quartos sem
uso" continua existindo, mas só como informativo, mostrando o que
sobrou pra limpeza manual no painel do Beds24. `deleteUnusedBeds24Room`
(frontend) removida por estar morta sem nenhuma chamada; as 4 chaves de
i18n órfãs correspondentes também removidas dos 5 idiomas.
`delete_room_type`/rota `DELETE /settings/beds24/rooms/<id>`
(backend, com as travas de segurança) mantidos como estão — a lógica em
si já está pronta e testada, só falta o endpoint certo confirmado, pra
não precisar refazer esse trabalho quando isso for retomado (via
suporte oficial do Beds24, se virar necessidade recorrente).

## Integração com channel manager (Beds24) — Fase 3 (webhook de entrada)

Usuário confirmou seguir mesma madrugada pra Fase 3: receber reserva de
verdade vinda de Booking.com/Airbnb/Hostelworld via webhook do Beds24.

**Desenho pensado pra nunca perder dado mesmo com formato de payload
desconhecido** (lição direta da Fase 2, onde o formato real só foi
descoberto testando): toda notificação recebida grava o payload cru em
`channel_webhook_events.payload_json` **antes** de qualquer tentativa
de interpretar. Se a extração de campo estiver errada, nada se perde —
dá pra corrigir o parsing depois olhando o payload real guardado, sem
repetir o processo de descoberta às cegas que consumiu boa parte da
Fase 2.

**Novo `routes/beds24_webhook.py`**: `POST
/webhook/beds24/<secret_token>` — autenticação por token secreto no
próprio path (Beds24 não manda assinatura HMAC nativa como o
WhatsApp/Meta manda), configurado como env var `BEDS24_WEBHOOK_SECRET`.
Resolve o hostel dono da reserva por `propertyId` (se vier no payload)
ou por `roomId` (nova função `get_hostel_id_by_beds24_room_id`, busca
inversa que não depende de já saber o hostel de antemão — diferente da
busca de mapeamento de quarto da Fase 2, que exige hostel_id como
filtro). Extração de campo tolerante a variação de nome
(`_first_present`, tenta várias grafias comuns: `bookId`/`id`/
`bookingId`, `arrival`/`checkIn`/`firstNight`, etc.) — outra lição da
Fase 2, onde nomes de campo divergiam do esperado. Sempre responde 200
(mesmo padrão do webhook do WhatsApp), erro interno vira
`status='failed'` no evento salvo, nunca derruba a notificação.

**`database.py`**: `get_hostel_id_by_beds24_room_id`,
`try_claim_webhook_event`/`finalize_webhook_event` (idempotência via
`UNIQUE(beds24_booking_id)` + `INSERT` que falha limpo em reentrega —
mesma ideia de constraint já usada em outras tabelas do projeto, sem
lógica de deduplicação manual), e `create_reservation_from_channel`
— a peça central: diferente do fluxo do WhatsApp (que recusa reservar
sem cama livre), aqui a reserva **já é um compromisso confirmado do
lado da OTA**, então não dá pra simplesmente recusar por falta de cama.
Tenta atribuir uma cama disponível de verdade, com a mesma trava contra
condição de corrida da Fase 1 (`reservar_cama_com_trava`); se não
houver nenhuma livre/cadastrada, cria a reserva mesmo assim sem cama
específica, pra equipe atribuir manualmente depois — perder o registro
da reserva seria bem pior que deixar sem cama atribuída.

**Escopo desta fase, deliberadamente**: só reserva **nova** (criação).
Atualização de data e cancelamento ficam pra próxima rodada, depois de
ver um payload real de teste — tentar adivinhar o formato desses dois
eventos também, sem nenhum dado real pra validar contra, repetiria o
mesmo erro que já custou tempo demais na Fase 2. Por enquanto, um
webhook de cancelamento chega, é reconhecido pelo campo `status`, e
fica marcado como eventos `ignored` no banco (não cria nem cancela
reserva nenhuma) — visível nos logs pra northear a próxima rodada.

**Verificação**: suite de testes cobrindo, com Flask `test_client()`
real (não só função isolada): token secreto errado bloqueado com 403,
resolução de hostel via `roomId`, criação de reserva com cama
disponível e sem cama disponível, idempotência ponta a ponta (reenviar
o mesmo webhook duas vezes não duplica a reserva), e o fluxo completo
HTTP de reserva nova chegando e virando `reservations` de verdade no
banco. Balanceamento/sintaxe conferidos nos arquivos Python novos.

**Configuração real com o usuário**: variável `BEDS24_WEBHOOK_SECRET`
gerada e configurada no Render; URL do webhook cadastrada no painel do
Beds24 (Configurações → Propriedades → Acesso → "Webhook de Reservas"),
versão **"2 - com dados pessoais"** escolhida deliberadamente (a versão
sem dados pessoais não traria nome/telefone do hóspede, que o StayFlow
precisa pra criar a reserva completa).

**Teste real: reserva de teste criada direto no painel do Beds24** —
revelou duas coisas reais de uma vez, como esperado (mesmo padrão de
"só se aprende testando" da Fase 1-2):

1. **Estrutura do payload diferente do suposto**: os dados da reserva
   vêm dentro de uma chave `"booking"` aninhada
   (`{"timeStamp":..., "booking": {...campos aqui...}, "invoiceItems":
   [...]}`), não soltos no nível de cima do payload como o código
   assumia. Sem essa correção, `bookId`/`id` nunca era encontrado e a
   reserva era descartada com "sem id de reserva reconhecido" — mas
   nada foi perdido de verdade, porque o payload cru já tinha sido
   gravado antes da tentativa de interpretar (exatamente o motivo de
   ter desenhado assim desde o início).
2. **A Beds24 manda um webhook novo a cada alteração, não só na
   criação** — a mesma reserva (`booking.id` igual) chegou duas vezes
   em menos de 2 minutos: a primeira com nome/telefone do hóspede
   vazios (reserva recém-criada, dados ainda não preenchidos no
   formulário do painel), a segunda já com "Juliana Souza" e telefone
   preenchidos. O desenho original da Fase 3 (idempotência simples,
   "processa uma vez só, ignora reentrega") trataria a segunda mensagem
   como duplicata e descartaria a atualização de nome — errado. Corrigido
   ainda dentro da mesma rodada: chave de idempotência passou a incluir
   o `modifiedTime` do evento (`"90711959:2026-07-31T04:25:47Z"`, não só
   o id puro), e nova função `update_reservation_from_channel` — se já
   existe uma reserva StayFlow pra aquele `external_booking_id`, o
   evento vira atualização (nome, telefone, datas, status) em vez de
   criar de novo ou ser ignorado. Reentrega EXATA do mesmo evento
   (mesmo id + mesmo modifiedTime) continua sendo ignorada de verdade.

Reteste com o payload real exato capturado nos logs de produção (não
um mock genérico) confirmou: primeiro webhook cria a reserva com
"Hóspede (OTA)" como nome provisório; segundo webhook atualiza pra
"Juliana Souza" sem duplicar; reenvio do segundo evento não muda nada.
Deploy da correção feito, teste real repetido no Beds24 pra confirmar
de ponta a ponta em produção.

**Confirmado funcionando em produção**: reserva de teste ("Juliana
Souza", Compartilhado, 31/07→03/08) apareceu certinha no Mapa de
Quartos (cama corretamente marcada como ocupada/reservada) e na aba
Reservas, com status "CONFIRMED".

**Bug real encontrado no mesmo teste**: reserva chegou com **US$
0,00** de valor. Causa: `create_reservation_from_channel` recebia
`amount` da rota do webhook, mas a rota nunca extraía o campo `price`
do payload da Beds24 pra passar adiante — sem valor recebido, a função
tentava calcular pelo `price_per_night` cadastrado na modalidade do
StayFlow, que ainda não tinha preço configurado (ficou 0). Usuário
apontou o ponto certo: o valor tem que vir **sempre do canal**, nunca
recalculado pelo preço do StayFlow — plataformas como Booking/Airbnb
podem vender com desconto, e o valor real cobrado do hóspede é o que
importa pro financeiro, não o preço de tabela. Corrigido: `amount`
agora extraído do payload (`price`/`totalPrice`/`amount`, tentando os
três nomes) e repassado tanto pra criação quanto pra atualização de
reserva (`update_reservation_from_channel` ganhou o parâmetro
`amount`, opcional — `None` preserva o valor já gravado ao atualizar
outros campos, só sobrescreve quando o payload realmente trouxe um
preço). Retestado com o payload real: `amount: 36.0` correto nos dois
testes (criação e atualização).

**Confirmado em produção**: usuário adicionou mais um dia na reserva de
teste no painel do Beds24 (disparando webhook novo) e o valor apareceu
certo na aba Reservas do StayFlow: US$ 36,00 (não mais US$ 0,00).
Fase 3 encerrada como funcional de ponta a ponta.

## Gap descoberto: check-in/check-out não acessível pela aba Reservas

Usuário reportou que, ao tentar mudar o status de uma reserva confirmada
pra "check-in confirmado" (pedido original: quando confirmar o check-in
no StayFlow, empurrar isso automaticamente pro Beds24 também), o
dropdown "Cambiar estado" da aba Reservas só oferecia pendente/cancelada/
no-show — nenhuma opção de check-in.

Investigação mostrou que o fluxo completo já existia no backend e no
Mapa de Quartos (cama azul=reservada → vermelha=ocupada no check-in →
amarela=precisa limpeza no check-out → verde=livre quando a limpeza é
confirmada), com rotas prontas (`POST /reservations/<id>/checkin`,
`POST /reservations/<id>/checkout`, `POST /beds/<id>/mark-cleaned`) —
só nunca tinha sido ligado na aba Reservas, que só mexe no campo
`reservations.status` (pending/confirmed/cancelled/no_show), um conceito
totalmente separado do status físico da cama (`beds.status`).

Corrigido: `get_reservations_with_stats` (`database.py`) agora faz LEFT
JOIN com `beds` e devolve `bed_status` junto de cada reserva. A aba
Reservas passou a mostrar, junto do dropdown de status:
- **"Confirmar check-in"**, se a reserva está confirmada e ainda sem
  cama (`bed_id` nulo) — abre um seletor com as camas livres no momento
  (via `/bed-map`) e chama a rota de check-in já existente.
- **"Confirmar check-out"**, se a cama da reserva está `occupied` — chama
  a rota de check-out já existente (a cama vai pra `needs_cleaning`,
  some da lista de limpeza só quando alguém confirma a limpeza — mesmo
  fluxo do Mapa de Quartos).
- Aviso "Aguardando limpeza da cama", se `bed_status === needs_cleaning`
  (sem ação aqui — confirmar a limpeza continua sendo tarefa da equipe de
  limpeza, já coberta em outro lugar da interface).

Testado com `ast.parse`, balanceamento de chaves/parênteses, cobertura
i18n (5 idiomas) e um teste end-to-end usando `app.test_client()` real
(sessão de verdade via `create_session`, não sessão forjada) cobrindo
checkin → checkout → mark-cleaned e conferindo que `/reservations`
reflete `bed_status` corretamente em cada etapa.

Push automático do check-in confirmado pro Beds24 (pedido original do
usuário) fica para uma rodada seguinte — depende de confirmar antes se
a API do Beds24 tem algum conceito de status "hóspede chegou"/"arrived"
equivalente, o que ainda não foi verificado.

## Bug real encontrado testando ao vivo: botão de check-in sumindo pra reservas de canal/WhatsApp

Usuário testou em produção e reportou: os botões de check-in/check-out
apareceram certinho pra uma reserva manual, mas duas reservas reais
(uma vinda do WhatsApp, outra do Beds24 — "Júlia Castells" e "Juliana
Souza") não mostravam nenhum botão.

Causa raiz: `bed_id` da reserva estava sendo usado pra duas coisas ao
mesmo tempo — (1) qual cama fica reservada pro período (preenchido
automaticamente na criação, inclusive vindo do Beds24/WhatsApp, via
`find_available_beds`) e (2) se o hóspede já fez check-in físico de
verdade. Como reservas de canal/WhatsApp já nascem com `bed_id`
preenchido, a lógica da rodada anterior (que usava `!r.bed_id` pra
decidir se mostrava "Confirmar check-in") achava que essas reservas já
tinham feito check-in e escondia os dois botões.

Corrigido com dois campos novos e sem ambiguidade: `reservations.checked_in_at`
e `checked_out_at` (timestamp, null até a ação real acontecer),
preenchidos por `checkin_reservation_to_bed`/`checkout_reservation_bed`.
A visibilidade dos botões na aba Reservas (e o filtro de "reservas
aguardando check-in" do Mapa de Quartos) passou a usar esses dois
campos, não mais a presença de `bed_id`.

Aproveitando a correção, endereçado também um pedido explícito do
usuário: já que o Beds24/WhatsApp já informa a categoria (compartilhado/
privado) e o sistema já atribui automaticamente uma cama livre dessa
categoria na criação da reserva, o check-in dessas reservas não deve
pedir pra recepção escolher a cama de novo — `checkinReservationUI` agora
confirma o check-in direto na cama já atribuída com um clique só quando
`bed_id` já existe, e só abre o seletor manual de cama livre quando a
reserva realmente não tem nenhuma atribuída ainda (reserva manual, ou
nenhuma cama livre na categoria no momento da criação). Trocar de cama
depois continua sendo manual (recepção ou via Ask StayFlow), não uma
ação de check-in.

Testado com um cenário que reproduz exatamente o bug real: reserva criada
via `create_reservation_from_channel` (já nasce com `bed_id`, `checked_in_at`
null) e depois check-in confirmado usando essa mesma cama, sem escolha
manual — junto com o fluxo antigo (reserva manual sem cama, escolhida na
hora do check-in). Balanceamento, sintaxe e cobertura i18n conferidos de
novo depois da mudança.

Observação separada, não é bug: apareceram duas reservas idênticas de
"Juan" na aba Reservas (datas de 2024, uma cancelada e uma confirmada) —
é dado de teste antigo de sessões anteriores, não algo criado por essa
mudança. Fica pro usuário cancelar/limpar manualmente pela própria aba
(já dá pra mudar o status pra "Cancelada" no dropdown).

## Atualização automática entre Reservas e Mapa de Quartos

Usuário reparou que, depois de confirmar check-in/check-out, a cor da
cama só mudava depois de dar F5 — pedido explícito: "tudo que for
atualização dinâmica que muda status de algo em algum lugar deveria
entrar automaticamente".

Causa: Reservas e Mapa de Quartos mostram o mesmo estado de dois jeitos
diferentes, mas cada ação só recarregava a própria tela de origem
(`checkinReservationUI`/`checkoutReservationUI`/`updateReservationStatus`
na aba Reservas só chamavam `loadReservations()`; `checkoutBedUI`/
`markBedCleanedUI` no Mapa de Quartos só chamavam `loadRoomMap()`) —
como as duas seções ficam sempre no DOM (só uma fica visível por vez),
dava pra atualizar as duas juntas sem custo real, só ninguém tinha
ligado os dois lados.

Corrigido com uma função central, `refreshOperationalViews()`, que
chama `loadRoomMap()` e `loadReservations()` juntas (cada uma só roda se
a função existir/a seção estiver carregada) - aplicada em toda ação que
muda status de cama ou reserva, nos dois sentidos: check-in/check-out/
mudança de status manual na aba Reservas, e check-in/check-out/marcar
como limpa no Mapa de Quartos, além de abrir/encerrar estadia de longa
duração (que também ocupa/libera cama). Resultado: mudar o status em
qualquer um dos dois lugares reflete no outro na hora, sem F5.

## Cama presa em "Reservada" (azul) depois do ciclo completo de teste

Usuário testou check-in/check-out/limpeza em todas as reservas e uma
cama ficou travada mostrando "Reservada" (azul) mesmo sem nenhuma
reserva ativa.

Causa: o cálculo de `display_status` no Mapa de Quartos (`get_bed_map`)
pinta uma cama livre de azul quando existe alguma reserva não-cancelada
com `checkout_date >= hoje` pra aquele `bed_id` — mas nunca checava se
essa reserva já tinha sido **finalizada de verdade** (check-out
confirmado). Como `bed_id` continua na reserva depois do check-out
(registro histórico, não é limpo), uma reserva já 100% concluída (cuja
data de checkout ainda não passou, ex: teste com datas futuras) continua
"contando" como reserva ativa nesse cálculo, prendendo a cama como
reservada mesmo depois de check-out + limpeza confirmados.

Corrigido: a consulta agora também exige `checked_out_at IS NULL` (campo
novo desta mesma rodada) — só reservas que ainda não passaram por
check-out contam pra pintar a cama de azul. Testado com o ciclo completo
(reserva → check-in → check-out → limpeza) confirmando que a cama volta
pra "free" no fim, não fica presa em "reserved".

## Origem da reserva mostrando "direct" em vez do nome da OTA

Usuário observou que a coluna "Origem" da aba Reservas mostra o valor
cru vindo do Beds24 (ex: "direct") em vez do nome da plataforma
(Airbnb/Booking.com/Hostelworld). O backend já captura o canal real de
cada reserva individualmente (campo `channel` do payload da Beds24,
gravado em `reservations.source`) — "direct" nesse caso específico é o
valor correto, porque a reserva de teste foi criada direto no painel do
Beds24, não simulando vir de uma OTA real. Ainda não testado com uma
reserva sincronizada de verdade de Airbnb/Booking/Hostelworld pra
confirmar os nomes exatos que a Beds24 manda nesse campo.

Melhorada a exibição enquanto isso: `channelDisplayLabel()` no frontend
mapeia slugs conhecidos (`airbnb`, `booking`/`bookingcom`, `hostelworld`,
`expedia`, `agoda`, `vrbo`, `whatsapp`, `manual`, `direct`) pro nome
formatado da plataforma; qualquer valor desconhecido cai num fallback
seguro (primeira letra maiúscula), nunca quebra a tela mesmo se o slug
real de uma OTA vier diferente do esperado.

## Cor roxa pra cama de morador de longa duração

Pedido do usuário: diferenciar visualmente no Mapa de Quartos uma cama
ocupada por morador fixo (estadia indefinida, ex: funcionário) de uma
cama ocupada por hóspede normal de passagem.

`get_bed_map` (`database.py`) ganhou uma consulta extra: entre as camas
com `status = 'occupied'`, identifica quais têm uma reserva vinculada
com `stay_type = 'indefinite' AND checkout_date IS NULL` (estadia
indefinida ainda ativa - `checkout_date` só é preenchido quando a
estadia é encerrada de verdade via `close_indefinite_stay`). Essas camas
recebem `display_status = 'long_term'` em vez de `'occupied'`.

Cor escolhida: roxo (`#9b5de5`), aplicada em `.bed-tile-half.long_term`
e `.bed-map-legend i.long_term` (`static/css/app.css`), com entrada nova
na legenda do mapa e chave i18n `bed.status.long_term` nos 5 idiomas.
Ao encerrar a estadia, a cama volta pro ciclo normal (`needs_cleaning` →
limpeza → `free`), sem precisar de nenhum tratamento especial - testado
com o ciclo completo (morador ocupando → encerrar estadia → cor some).

## Morador de longa duração: sem cama, sem hóspede, sem aviso de limpeza no check-out

Usuário criou um morador fixo pela aba Reservas e reportou três coisas
erradas de uma vez: não entrou em nenhuma cama, não apareceu na aba
Hóspedes, e nenhum check-out (de nenhuma reserva) gerava aviso
operacional de limpeza.

**Cama vazia**: `create_indefinite_stay` só ocupa uma cama de verdade
quando recebe `bed_id` — mas o formulário "Residente de larga duración"
nunca teve um seletor de cama, só um campo de texto livre "Quarto/
observação". Ou seja, o recurso de cor roxa criado na rodada anterior
nunca tinha como funcionar de verdade nesse formulário. Corrigido: select
`indefiniteStayBedSelect`, populado com as camas livres a cada
carregamento do Mapa de Quartos (`fillIndefiniteStayBedSelect`,
reaproveitando o mesmo padrão do seletor de check-in da aba Reservas).

**Sem hóspede na aba Hóspedes**: `create_indefinite_stay` só *procurava*
um hóspede já existente com aquele telefone (`SELECT ... WHERE phone =
?`) — nunca *criava* um novo, diferente do resto do sistema (WhatsApp,
Beds24) que usa `get_or_create_guest`. Um morador novo com telefone novo
nunca virava um registro na tabela `guests`, então nunca podia aparecer
na aba (que lista direto de `guests`). Corrigido pra usar
`get_or_create_guest` + `update_guest_name`, igual todo o resto do
sistema já faz.

**Check-out sem aviso operacional**: nenhuma cama aguardando limpeza
contava como alerta — só aparecia como "tarefa" na página de Operações,
sem nunca incrementar o sininho de notificações (que já dispara
automaticamente no login pra quem tem permissão de Operações, gate já
existente via `@require_permission("operations")`). Corrigido em
`routes/operations.py`: cada cama em `get_cleaning_list` agora também
vira uma linha em `alerts`, não só em `tasks`.

Testado o ciclo completo: criar morador fixo com cama e telefone →
aparece roxo no mapa e na lista de hóspedes com `guest_id` vinculado →
encerrar a estadia → cama vira `needs_cleaning` → aparece em
`/operations` tanto como tarefa quanto como alerta contável no sininho.

## Reserva automática (WhatsApp/qualquer canal) também deve avisar no sininho

Pedido seguinte do usuário: reservas vindas de qualquer canal automático
(WhatsApp, Beds24/qualquer OTA) devem gerar aviso no sininho também, não
só reservas manuais que a equipe já sabe que criou.

Adicionado em `routes/operations.py`: reservas com `source != 'manual'`
criadas nas últimas 24h (janela de tempo pra não acumular alerta de
reserva antiga que a equipe já viu há dias, mesmo padrão dos outros
alertas que são recalculados do zero a cada chamada) viram um alerta
"Nova reserva via {canal}: {hóspede} ({checkin} → {checkout})". Testado
com reserva manual (não gera alerta), via WhatsApp e via canal
(`source='airbnb'`, simulando o que a Beds24 gravaria) — as duas
automáticas geram alerta, a manual não.

## Pedido em aberto: notificação nativa no aparelho (celular/PC)

Usuário pediu, ainda sem escopo detalhado: que essas notificações
(mensagem nova, alerta operacional, problema de IA, necessidade de
intervenção humana etc) cheguem como notificação nativa do sistema
operacional (celular ou PC), no estilo WhatsApp - não só o sininho
dentro do dashboard. Isso é uma peça de infraestrutura nova e maior
(Web Push API: service worker, VAPID keys, tabela de inscrições de
push por dispositivo/usuário, disparo no backend a cada evento
relevante) - ainda não iniciado, fica pra ser desenhado como uma etapa
própria, depois de fechado o que já estava em andamento nesta rodada.

## Perfil completo do hóspede (clicar no nome abre tudo)

Pedido do usuário, retomado de uma rodada anterior desta sessão (tinha
sido explicitamente adiado até terminar a integração Beds24): na aba
Hóspedes, clicar no nome deveria abrir o perfil completo - contato,
endereço, documento (tipo/número + foto), saldo/pagamento em atraso e
histórico de estadias.

Investigação encontrou infraestrutura já pronta e nunca exposta na UI:
- `guest_documents` (tabela) + `save_guest_document`/`list_guest_documents`/
  `get_guest_document_file` já existiam, usados hoje só pelo recebimento
  automático de foto de documento via WhatsApp. Reaproveitados 100% pro
  upload manual também - `save_guest_document` já aceita
  `whatsapp_media_id=None`, então o mesmo caminho de código serve pros
  dois casos.
- `get_guest_profile` já devolvia hóspede + mensagens + oportunidades +
  documentos, só faltava reservas/saldo.
- `get_reservation_balance` (saldo de estadia de longa duração, dias
  ocupados x diária menos pagamentos) já existia pronto, criado numa
  rodada anterior.

**Descoberta importante sobre "pagamento atrasado"**: o modelo de dados
atual só tem controle de pagamento parcial pra estadias de longa duração
(`stay_type='indefinite'`, via `reservation_payments`). Reserva fixa
normal (a maioria) tem só um campo `amount` fechado, sem conceito de
"pago"/"não pago" nem pagamento parcial. Decisão: não inventar um status
de atraso falso pra reserva fixa - o perfil mostra o valor total dela e,
pra estadia de longa duração, mostra o saldo real (deve/crédito/em dia),
igual já é feito na aba Reservas.

**Backend novo**:
- Colunas em `guests`: `address`, `document_type`, `document_number`
  (`date_of_birth`/`nationality` já existiam).
- `get_guest_reservations(hostel_id, guest_id)`: todas as reservas desse
  hóspede, com `balance` calculado só quando `stay_type='indefinite'`.
- `get_guest_profile` passou a incluir `reservations`.
- `update_guest_profile(hostel_id, guest_id, **fields)`: lista branca
  fixa de colunas editáveis (nunca monta SQL com nome de coluna vindo de
  fora), erro claro (`ValueError` → 400) se o telefone novo já pertence
  a outro hóspede do mesmo hostel (`UNIQUE(hostel_id, phone)`).
- Rotas novas: `PATCH /guests/<id>` (edição) e
  `POST /guests/<id>/documents` (upload manual, `multipart/form-data`,
  mesma whitelist de mime type usada no recebimento via WhatsApp:
  jpeg/png/webp/pdf) - essa última confere primeiro que o hóspede
  pertence ao hostel da sessão antes de gravar qualquer arquivo,
  fechando um caminho de escrita cross-tenant que não existia nas rotas
  de leitura (essas já eram escopadas por `hostel_id` desde a criação).

**Frontend novo**:
- Nome na lista de Hóspedes virou link (`onclick="openGuestProfileModal"`).
- `openGenericModal` ganhou um terceiro parâmetro opcional (`wide`) pra
  modal mais largo (760px) só quando precisa - variante nova
  `.generic-modal.wide` no CSS, sem mexer no tamanho padrão usado em
  todo o resto do app.
- Modal do perfil com 4 seções: Contato (editável), Documento
  (tipo/número editáveis + galeria de fotos com miniaturas clicáveis,
  abrindo o arquivo original em nova aba, mais upload de arquivo novo),
  Estadias e pagamento (histórico completo, reaproveitando a mesma
  lógica visual de saldo já usada na aba Reservas pra morador de longa
  duração).

Testado de ponta a ponta via `app.test_client()`: `GET /guests/<id>`
trazendo reservas certas; `PATCH` salvando contato/documento; `PATCH`
com telefone duplicado falhando limpo (400, mensagem clara); upload de
documento via multipart salvando e aparecendo depois no perfil;
`GET /guests/documents/<id>/file` devolvendo o arquivo certo (bytes
batendo exatamente); morador de longa duração aparecendo com saldo
calculado (`balance`) na lista de reservas do perfil.

## Pendência futura anotada: moeda/câmbio automático por país

Usuário pediu, em duas mensagens ao longo desta rodada, pra registrar
como trabalho futuro (explicitamente adiado até a etapa de configurar
formas de pagamento):
- Hostel identificado por país no cadastro; moeda padrão = moeda local
  desse país, com dólar americano SEMPRE disponível como opção em
  qualquer país, além de poder escolher qualquer outra moeda.
- Tabela/mecanismo de câmbio com atualização automática de cotação
  (usuário supõe que existe alguma API/banco de dados externo acessível
  pra isso - nenhuma foi escolhida ainda).
- Regra de negócio explícita: o câmbio usado é sempre 30 pontos abaixo
  do câmbio real de mercado, pra qualquer moeda (exemplo dado: se 1 USD
  = 1500 ARS no mercado, o StayFlow calcula com 1 USD = 1470 ARS). Ponto
  em aberto pra confirmar antes de implementar: se "30 pontos" é sempre
  uma subtração fixa de 30 unidades da moeda local por dólar (como no
  exemplo) ou um ajuste proporcional - não presumir, perguntar/confirmar
  a matemática exata quando for implementar.
- Área de configuração de empresa também deveria se adaptar aos campos
  exigidos por cada país.

Nada disso foi iniciado - é um recurso grande o suficiente (motor de
conversão de moeda + regra de margem + fonte de câmbio ao vivo +
identificação de país por hostel + seletor de moeda na UI + campos de
empresa por país) pra merecer sua própria rodada de design, não pra
encaixar de raspão em outra tarefa.

## Fase 4 da integração Beds24: saída/disponibilidade

Usuário pediu recapitulação de tudo que faltava na integração Beds24 e
escolheu começar pelo item mais importante: hoje, reserva feita manual
ou pelo WhatsApp não avisa o Beds24 - risco real de overbooking (outra
OTA vender a mesma cama enquanto ela já está ocupada no StayFlow).

`push_availability(beds24_room_id, checkin_date, checkout_date,
num_avail)` já existia em `services/beds24_service.py` desde a Fase 1,
mas nunca tinha sido chamada de lugar nenhum - só a peça que faltava era
calcular CORRETAMENTE quantas unidades ainda estão livres e ligar isso
nos pontos certos.

**Decisão de design importante**: contar disponibilidade por `bed_id`
(como o resto do sistema faz pro mapa de quartos) subestimaria a
ocupação real, porque reserva manual/WhatsApp só recebe uma cama
específica atribuída no momento do check-in - antes disso, `bed_id`
fica null mesmo a reserva já estando confirmada e ocupando uma vaga da
modalidade. Por isso `sync_availability_to_channel` conta por
`room_type` (texto, mesma convenção já usada por `find_available_beds`
e `create_reservation_from_chat`): `numAvail` = total de camas da
modalidade menos reservas não-canceladas de QUALQUER origem (inclusive
vindas do próprio Beds24) que se cruzam com o período pedido.

Ligada em três pontos:
1. `create_reservation_record` (reserva manual) - depois do insert.
2. `create_reservation_from_chat` (WhatsApp) - depois de confirmar a
   cama e inserir.
3. `update_reservation_status_record` - depois de QUALQUER mudança de
   status (não só cancelamento) - como a função sempre recalcula do
   zero a partir do banco, chamar de novo em qualquer transição é
   sempre seguro e correto (cobre cancelar E reverter cancelamento).

**Nunca chamada** em `create_reservation_from_channel`/
`update_reservation_from_channel` (as duas funções que processam
reserva vinda DO Beds24) - evita ecoar de volta pra eles uma mudança
que eles mesmos já sabem, mesmo princípio já usado no webhook de
entrada.

Testado com mocks de `services.beds24_service.push_availability` (sem
gastar chamada real de API): sem mapeamento configurado não sincroniza
nada; 3 camas sem reserva nenhuma dá `numAvail=3`; criar reserva manual
sem cama atribuída já reduz pra 2 (prova que a contagem por `room_type`
funciona mesmo sem `bed_id`); cancelar essa reserva volta pra 3;
reserva criada via `create_reservation_from_channel` não dispara
nenhuma chamada (sem eco); reserva via WhatsApp também sincroniza
corretamente.

**Nome exato do campo continua não confirmado contra a API real**
(`numAvail`, por analogia com outros campos documentados do Beds24) -
mesma ressalva de toda essa integração desde a Fase 1: só confirma de
verdade testando ao vivo com a conta master. Próximo passo natural:
usuário testar criando/cancelando uma reserva manual/WhatsApp de
verdade pra uma modalidade já mapeada, e conferir no painel do Beds24
se a disponibilidade mudou.

## Teste real: cancelamento não apareceu no painel do Beds24

Usuário cancelou a reserva da Juliana pela aba Reservas do StayFlow e
foi conferir no Calendário do Beds24 - a reserva dela continuava lá
(`Compartilhado` mostrando "0" disponível nas datas, barra da Juliana
ainda desenhada no calendário).

Duas coisas descobertas:

1. **Não é bug, é limitação esperada da Fase 4 como desenhada**: `push_availability`
   só mexe no CALENDÁRIO/INVENTÁRIO (quantas unidades ainda podem ser
   vendidas), não na reserva específica em si. A reserva da Juliana é um
   registro de booking de verdade dentro do Beds24 (foi criada lá,
   espelhada pro StayFlow via webhook) - cancelar no StayFlow nunca
   tocaria nesse registro, só ajustaria "quantas vagas sobraram pra
   vender". São duas APIs/conceitos diferentes do Beds24. Fica claro que
   o próximo passo real é sincronizar o STATUS DA RESERVA especÍfica de
   volta pro Beds24 (usando `external_booking_id`), não só disponibilidade
   agregada - isso generaliza o pedido antigo de "avisar check-in
   confirmado" pra também cobrir cancelamento.

2. **Bug real de observabilidade**: mesmo se a disponibilidade tivesse
   sido sincronizada corretamente, não daria pra confirmar isso pelos
   logs - `sync_availability_to_channel`/`push_availability` só tinham
   `print()` no caminho de ERRO, nunca no de sucesso ou nos "no-op"
   (sem checkin/checkout, modalidade não encontrada, modalidade não
   mapeada). Conferindo o log real do Render no horário exato do
   `PATCH /reservations/5` (a reserva da Juliana, confirmado pelo id),
   não apareceu rastro nenhum da sincronização - impossível saber se
   rodou, se foi ignorada, ou se falhou.

Corrigido: `print()` adicionado em todo caminho de `sync_availability_to_channel`
(sem data, categoria não encontrada, sem mapeamento, cálculo completo
com os números exatos usados) e em `push_availability` (sucesso além de
erro, com a resposta completa do Beds24). Deploy feito - próximo teste
do usuário já vai mostrar no log exatamente o que está acontecendo.
Construir a sincronização de status de reserva específica (cancelamento
+ check-in) fica pra assim que confirmarmos, com log real, que a Fase 4
básica está funcionando.

## Confirmado: Fase 4 funciona de verdade contra a API real

Usuário testou de novo e mandou o log - achado no meio dele:

```
Sync disponibilidade Beds24: categoria 'privado' ... numAvail=1
Disponibilidade empurrada pro Beds24 com sucesso: 201 [{"success":true}]
```

**Confirmado**: o campo `numAvail` estava certo desde o início (a
ressalva "confirmar contra API real" que vinha desde a Fase 1 pode ser
removida) - o Beds24 aceitou a chamada com HTTP 201 e respondeu
`{"success":true}`. A Fase 4 está funcionando de ponta a ponta em
produção.

No mesmo teste, o usuário reportou mais duas coisas:

1. **Reserva manual (Vinicius, Compartilhado) não apareceu no painel do
   Beds24** - esperado, mesma explicação já registrada na entrada
   anterior: Fase 4 só ajusta quantas vagas sobram pra vender, nunca
   cria um registro de reserva visível lá. Isso já é suficiente pra
   evitar overbooking (a vaga fica bloqueada pra venda), só não cria a
   sensação visual de "a reserva está lá dentro".

2. **Bug real encontrado**: a reserva manual do Vinicius (modalidade
   Compartilhado, com `price_per_night` de US$ 20.000 já configurado)
   nasceu com US$ 0,00 na aba Reservas. Causa: `create_reservation_record`
   (criação manual) nunca calculava o valor pelo preço da modalidade -
   só os outros dois caminhos de criação (`create_reservation_from_chat`
   do WhatsApp e `create_reservation_from_channel` do Beds24) já faziam
   esse cálculo. Reserva manual dependia 100% de alguém digitar o valor
   na mão no formulário.

Corrigido: `create_reservation_record` agora calcula `amount` pelo
`price_per_night` da modalidade × noites quando nenhum valor é
informado explicitamente (mesma lógica dos outros dois caminhos) - só
não sobrescreve se a equipe já digitou um valor de propósito (ex:
desconto negociado). Testado: sem valor informado calcula certo (3
noites × US$ 20.000 = US$ 60.000); valor informado explicitamente é
respeitado sem ser sobrescrito; modalidade sem cadastro continua US$
0,00 sem quebrar nada.

## Fase 5 da integração Beds24: reserva de verdade, "tudo em sincronia"

Pedido direto do usuário depois de ver a Fase 4 funcionando: "quero que
esteja tudo em acordo, trabalhem juntos pra ser perfeito. Quero que
mostre o que foi criado, cancelado, check-in, check-out, tudo que for
possível mostrar em sincronia."

Até aqui, `push_availability` (Fase 4) só ajustava quantas vagas sobram
pra vender - nunca criava a reserva de verdade dentro do Beds24. Por
isso a reserva do Vinicius não apareceu no painel deles no teste
anterior. Esta rodada constrói a peça que faltava: publicar a reserva
em si.

**Vantagem real que baixou o risco dessa rodada**: diferente das Fases
1-3 (onde cada campo precisou de tentativa e erro contra a API real),
já temos um payload REAL completo de reserva vindo do webhook (Claudio
Silva, capturado nos logs) - `propertyId`, `roomId`, `arrival`,
`departure`, `firstName`, `lastName`, `phone`, `email`, `status`,
`price` são todos nomes de campo já confirmados de verdade. `create_booking`
monta o corpo do `POST /bookings` com esses mesmos nomes. O parsing da
resposta reaproveita o formato de lote com wrapper `"new"` já confirmado
em `create_property`/`create_room_type` (`data[0]["new"]["id"]`) -
alta confiança de estar certo mesmo sem ter testado esse endpoint
especificamente ainda ao vivo.

**Design da sincronização** (`sync_booking_to_channel`, `database.py`):
- Só roda pra reserva `source in ('manual', 'whatsapp')` - reserva vinda
  do próprio Beds24 nunca passa por aqui (evita eco, mesmo princípio já
  usado em `sync_availability_to_channel`).
- Reserva ainda `pending` (status padrão de toda reserva vinda do
  WhatsApp, aguardando a equipe confirmar) NÃO publica no Beds24 ainda -
  não faz sentido anunciar numa OTA algo que a equipe pode recusar.
  Publica só quando o status muda pra `confirmed`.
- Estadia de longa duração (sem `checkout_date`) fica de fora - não é
  o tipo de ocupação que se anuncia numa OTA.
- Primeira publicação (`external_booking_id` ainda null): cria a
  reserva no Beds24 via `create_booking`, grava o id retornado na
  própria reserva do StayFlow.
- Publicações seguintes (já tem `external_booking_id`): só
  `update_booking_status` (cancelar, reverter cancelamento) - nunca
  cria de novo, sempre atualiza a mesma reserva lá.

Ligada nos mesmos 3 pontos da Fase 4 (`create_reservation_record`,
`create_reservation_from_chat`, `update_reservation_status_record`).

**Bug relacionado encontrado e corrigido de quebra**: `create_reservation_from_chat`
tinha o MESMO bug já corrigido em `create_indefinite_stay` numa rodada
anterior - só *procurava* um hóspede já existente com aquele telefone,
nunca *criava* um novo. Hóspede novo mandando a primeira mensagem pelo
WhatsApp nunca virava registro em `guests`, então nunca aparecia na aba
Hóspedes E nunca levava telefone/email de verdade pra sincronização com
o Beds24 (ficava `None`/`None` na chamada de criação da reserva -
confirmado no teste antes do fix). Corrigido pra usar `get_or_create_guest`
+ `update_guest_name`, chamado FORA da transação travada de
`reservar_cama_com_trava` (essa função abre sua própria conexão,
não dava pra abrir outra dentro de uma transação já travada).

**Fora do escopo desta rodada, de propósito**: check-in e check-out.
O payload real mostrou que a Beds24 guarda isso como um `infoItem`
separado (`{'code': 'CHECKIN', ...}`), não como o `status` principal da
reserva - mecanismo de escrita (se é que dá pra escrever via API) ainda
não confirmado. Arriscado demais chutar sem testar - fica pra depois de
confirmar que criação/cancelamento estão funcionando ao vivo.

Testado com mocks de `create_booking`/`update_booking_status` (sem
gastar chamada real): reserva pending do WhatsApp não publica ainda;
confirmar publica e grava o `external_booking_id`; cancelar atualiza a
mesma reserva (não cria outra); reserva manual já criada como
`confirmed` publica na hora; reserva vinda do Beds24 nunca aciona nada
daqui (sem eco); telefone/email agora chegam certos na chamada depois
do fix do hóspede.

## Bug real em produção: reserva duplicada (eco da própria Fase 5)

Usuário testou de verdade e mandou print do painel do Beds24: a reserva
do "Silvano" apareceu **duas vezes**, idênticas (mesma modalidade, nome,
datas, valor), ambas via origem "API". Confirmou explicitamente que não
criou duas vezes - já tinha visto duplicação antes (o caso do "Juan",
mas aquilo era dado de teste antigo de sessões passadas, sem relação).
Essa aqui é nova, e é bug de verdade.

**Causa raiz**: a própria Fase 5 recém-construída. Sequência real:
1. StayFlow cria a reserva do Silvano manualmente.
2. `sync_booking_to_channel` dispara, chama `create_booking` - Beds24
   cria a reserva e devolve o id.
3. StayFlow grava esse id em `reservations.external_booking_id` -
   MAS isso é uma segunda operação separada, depois da chamada HTTP já
   ter voltado.
4. A Beds24, ao criar a reserva, manda um webhook de confirmação de
   volta pro StayFlow - **quase instantaneamente**, às vezes chegando
   antes do passo 3 terminar.
5. Quando esse webhook chega, `get_reservation_id_by_external_booking_id`
   ainda não encontra nada (o vínculo do passo 3 ainda não foi salvo) -
   o webhook não tem como saber que essa "reserva nova" é a MESMA que
   acabou de ser criada, e cria uma linha duplicada via
   `create_reservation_from_channel`.

Um eco clássico: a Fase 5 manda uma ação pro Beds24, e o próprio
mecanismo de entrada (Fase 3) que já existia reage a essa ação como se
fosse notícia nova de fora.

**Corrigido** com uma checagem de deduplicação antes de criar qualquer
reserva nova a partir de um webhook: `find_recent_unlinked_stayflow_reservation`
(`database.py`) procura uma reserva `source in ('manual','whatsapp')`,
criada nos últimos 10 minutos, ainda sem `external_booking_id`, com a
MESMA modalidade + nome do hóspede + datas de check-in/check-out do
booking que chegou no webhook. Se achar, `link_external_booking_id`
vincula essa reserva existente em vez de criar outra -
`routes/beds24_webhook.py` foi reordenado pra fazer essa checagem antes
de decidir se cria ou atualiza. Janela de 10 minutos + casamento exato
de 4 campos torna colisão por coincidência real praticamente impossível.

Testado simulando a corrida de verdade: cria reserva → apaga
manualmente o `external_booking_id` que acabou de ser gravado (simula o
webhook chegando ANTES desse gravar) → manda o payload de eco → confirma
que continua existindo só 1 reserva, não 2. Confirmado também que um
booking genuinamente novo vindo de fora (sem nenhuma reserva StayFlow
correspondente) continua sendo criado normalmente, sem ser
"engolido" por engano pela checagem nova.

## Alerta de limpeza não aparecia na hora certa

No mesmo teste, usuário reportou: fez um check-out e não apareceu
nenhum aviso de limpeza em Operações/sininho. O alerta em si já existia
no backend (corrigido numa rodada anterior) - o problema era só que
`refreshOperationalViews()` (a função central que reatualiza as telas
depois de qualquer ação operacional) nunca chamava `loadOperations()`,
só `loadRoomMap()`/`loadReservations()`. O alerta ficava certinho no
banco, só não aparecia até a pessoa recarregar a página ou abrir a aba
Operações manualmente. Corrigido adicionando `loadOperations()` à mesma
função central - agora qualquer ação (check-in, check-out, cancelar,
etc) atualiza as três telas juntas, sininho incluso.

## Bug real: reserva do Otavio não calculou preço nem foi pro Beds24

Usuário testou de novo (reserva "Otavio", modalidade "Privado") e os
dois bugs voltaram: preço US$ 0,00 e nada sincronizado com o Beds24.
Log revelou a causa exata:

```
Sync disponibilidade Beds24: modalidade 'Privado' nao encontrada no hostel 1, ignorado.
```

A modalidade real cadastrada nesse hostel se chama **"privado"**
(minúsculo - confirmado também no mapeamento Beds24 e nas reservas do
Claudio Silva, todas com "privado" minúsculo). O formulário de nova
reserva manual, porém, tem um `<select>` com opções **fixas** no HTML
("Privado"/"Compartilhado", maiúsculo) - nunca foi ligado às modalidades
reais cadastradas no hostel. Como toda comparação no banco usava
`name = ?` (sensível a maiúsculas/minúsculas no SQLite), "Privado" ≠
"privado": nunca achava a modalidade, então nem calculava preço nem
sincronizava disponibilidade/reserva com o Beds24 - uma causa raiz só
explicando os dois sintomas reportados.

Corrigido em TODOS os pontos onde `room_type`/nome de modalidade é
comparado no banco (não só onde o bug apareceu, para fechar a fragilidade
de verdade): `create_reservation_record` (cálculo de preço),
`find_available_beds` (duas consultas), `create_reservation_from_chat`
(cálculo de preço + contagem de camas), `_resolve_category_id`,
`find_recent_unlinked_stayflow_reservation`, `sync_availability_to_channel`
(duas consultas) e `sync_booking_to_channel` - todas passaram a usar
`LOWER(name) = LOWER(?)` em vez de `name = ?`. Testado com o cenário
exato do bug (modalidade cadastrada "privado", reserva criada com
"Privado"): preço calculado corretamente E reserva sincronizada com o
Beds24, mesmo com capitalização diferente. Bateria completa de testes
Beds24 (Fases 3, 4 e 5) rerodada sem regressão.

Ainda não corrigido nesta rodada (fica para reforçar depois): o
`<select>` de "Tipo de quarto" do formulário de nova reserva continua
com opções fixas, não dinâmicas a partir de `room_categories` - o fix
de comparação insensível a maiúsculas resolve o sintoma, mas a causa de
UX (dropdown desconectado das modalidades reais) continua lá.

## Redesign dos botões de check-in/check-out na aba Reservas

Pedido direto do usuário, olhando o resultado visual: o botão de
check-in/check-out ficava "feio", embaixo do dropdown "Mudar status..."
na coluna Ações, ocupando a largura toda. Pedido: tirar de baixo do
status, colocar do lado, botão verde só com "Check-in" e, depois de
feito, um botão vermelho do lado escrito "Check-out".

Movido o botão pra dentro da própria coluna Estado, ao lado da pill de
status (`CONFIRMED`/`PENDING`/etc), como um botão pequeno arredondado
(`pill-btn`) em vez do botão retangular grande de antes. Classes novas
no CSS: `.checkin-pill` (fundo verde sólido `#26e0a0`) e
`.checkout-pill` (fundo vermelho sólido `#ff5d76`), texto escuro pra
contraste, mesmo formato arredondado da pill de status ao lado. Texto
dos botões encurtado de "Confirmar check-in"/"Confirmar check-out" pra
só "Check-in"/"Check-out" nos 5 idiomas (termo já universal no
mercado hoteleiro, sem necessidade de tradução literal). Coluna Ações
ficou só com o dropdown de mudar status, mais limpa.

**Ajuste seguinte**: usuário testou e reportou que os dois ficaram um
embaixo do outro em vez de lado a lado - o `<td>` não tinha nenhum
container flex, então o navegador quebrava linha naturalmente quando o
espaço não alcançava pra tudo em uma linha só. Corrigido envolvendo a
pill de status + botão num `<div style="display:flex;align-items:center;
gap:6px;flex-wrap:nowrap;white-space:nowrap">` - agora ficam sempre lado
a lado na mesma linha.

## F5 sempre voltava pro Dashboard

Pedido do usuário: "se eu tô numa aba de reservas e aperto F5, ela
volta pro Dashboard - quero que continue na mesma página, só que
atualizada."

Causa: `openPage(pageId, trigger)` só troca a classe `.active` entre as
seções - nunca grava em lugar nenhum QUAL página está aberta. Como
`#dashboard` é a única seção com `class="page active"` já no HTML
estático, todo reload (F5, ou até fechar/abrir a aba do navegador)
sempre começa do zero nele.

Corrigido com `localStorage`: `openPage` agora grava
`stayflow_last_page` toda vez que muda de página com sucesso; o
bootstrap da sessão (`hydrateUserUI`, que já roda depois de confirmar
sessão de verdade e aplicar permissões) chama `restoreLastOpenPage()`
logo em seguida - lê o valor salvo e chama `openPage` de novo pra essa
mesma aba, só se ela ainda existir E a pessoa ainda tiver permissão pra
vê-la (confere se o botão do menu correspondente não está escondido por
`hideNavItemsWithoutPermission` - reaproveita o mesmo mecanismo já
existente de permissão por `data-page`, sem duplicar lógica). Se não
tiver mais permissão ou a página não existir mais, fica no Dashboard
(sempre permitido a todo mundo), sem tentar forçar uma tela que a
pessoa não pode ver.

Recurso puramente de frontend (sem chamada de API nova) - verificação
real precisa ser feita manualmente no navegador (abrir uma aba
diferente de Dashboard, dar F5, conferir que continua lá).

## Bug real: preço da reserva chegava US$ 0,00 no painel do Beds24

Usuário criou uma reserva de teste ("ruiter") e reportou: o StayFlow
calculou o preço certo, mas o Beds24 mostrava US$ 0,00 na lista de
"Últimas Reservas". Pedi o log e a resposta real da API mostrou:

```
Resposta do Beds24 ao criar reserva: [{'success': True, 'new': {'id': 90722118, 'price': 350, ...}}]
```

O campo `price` **foi aceito e ecoado de volta** (350) - o que
descartou a hipótese de a API estar rejeitando o valor. Pedi print do
painel de "Últimas Reservas" pra comparar: TODAS as reservas criadas
via API (Vinicius, Silvano x2, Gabriel, Ruiter) mostravam US$ 0,00,
exceto a única criada direto no painel do Beds24 (Claudio Silva,
US$ 36,00, origem "StayFlow" em vez de "API"). Diferença real
encontrada comparando os dois payloads: a reserva do Claudio (criada
por eles) tinha um `invoiceItems` de verdade
(`{'type': 'charge', 'amount': 36, 'lineTotal': 36, ...}`) - as
nossas, criadas via `POST /bookings`, nunca mandavam esse campo.

**Conclusão**: o campo `price` no corpo da criação é só um valor de
referência/eco - o que preenche o valor de verdade nos relatórios e
telas do Beds24 é o item de fatura (`invoiceItems`, `type: 'charge'`).
Corrigido em `create_booking` (`services/beds24_service.py`): agora
manda um `invoiceItems` com `type: 'charge'`, `qty: 1` e `amount` igual
ao preço da reserva, além do campo `price` que já era enviado. Testado
com mock de `requests.post` conferindo o corpo exato enviado - contém
`invoiceItems` com o valor certo.

## Bug real: check-in não refletia no Mapa de Quartos

No mesmo teste, usuário reportou: fez check-in do Claudio Silva pela
aba Reservas e a cama dele não apareceu ocupada (vermelha) no Mapa de
Quartos. Hipótese certa do próprio usuário: como a reserva (vinda do
Beds24) já chega com uma cama atribuída automaticamente, e o check-in
usa essa cama sem mostrar nenhuma caixa de seleção, alguma informação
não está passando direito por aí.

Isso reverte uma decisão de design de uma rodada anterior (check-in de
reserva de canal confirmava direto na cama já atribuída, sem picker,
por pedido explícito do próprio usuário) - mas na prática real revelou
um ponto cego: confiar cegamente na atribuição automática, sem chance
de conferir/corrigir, escondeu o problema até virar um bug visível.

Corrigido: `checkinReservationUI` agora **sempre** mostra o seletor de
cama livre (nunca pula direto pro check-in), com a cama já atribuída
pré-selecionada no dropdown quando existir - a recepção só precisa
clicar "Confirmar" se estiver tudo certo, ou trocar se não estiver.
Pedido extra do usuário atendido: cada opção do seletor mostra
claramente "Beliche - Cima"/"Beliche - Baixo" quando a cama faz parte
de um beliche, não só o nome genérico da cama.

## Redesign do formulário de Nova Reserva / Morador de longa duração

Usuário pediu pra tirar os dois formulários fixos da aba Reservas (que
ficavam sempre ocupando espaço na tela) e virarem botão + modal, além
de repensar os campos. Argumento pra tirar o status "Pendente" da
criação manual: "não entendo o sentido de haver pendente, se quando uma
reserva é feita ela já é confirmada" - faz sentido pra criação manual
(a equipe digitando é um compromisso já certo), diferente da reserva
via WhatsApp (a IA cria automaticamente, `pending` até a equipe
confirmar - esse caso continua existindo, não mudou).

Campos pedidos: nome e sobrenome (separados), telefone, email,
nacionalidade, data, tipo de quarto, cama.

**Frontend**: os dois `<div class="card span-12">` com formulário fixo
viraram um único card com dois botões ("+ Nova reserva" e "🏠 Morador de
longa duração"), cada um chamando `openNewReservationModal()`/
`openNewIndefiniteStayModal()` (`openGenericModal` variante `wide`).
Removido de quebra o handler de "+ Novo tipo..." do antigo select fixo
de tipo de quarto (`reservationRoomTypeSelect`) - código morto, já que
o select novo (`nrRoomType`) lista as modalidades REAIS cadastradas no
hostel (`/room-categories`), não precisa mais de escape hatch pra
"criar tipo novo na hora". Seletor de cama (`nrBedId`) filtra pela
modalidade escolhida (`fillNewReservationBedSelect`, reagindo ao
`onchange` do tipo de quarto) e reaproveita o sufixo "Beliche - Cima/
Baixo" criado na correção anterior. Formulário de morador de longa
duração manteve os mesmos campos de antes, só movido pro modal - o
seletor de cama dele (`indefiniteStayBedSelect`) já existia, só passou
a ser populado na abertura do modal em vez de a cada `loadRoomMap()`
(elemento não existe mais permanentemente no DOM).

**Backend**: `create_reservation_record` ganhou os parâmetros `email`,
`nationality`, `bed_id`. Corrigido de quebra o MESMO bug já corrigido em
`create_indefinite_stay`/`create_reservation_from_chat` nesta sessão:
essa função só *procurava* um hóspede já existente pelo telefone, nunca
*criava* um novo - hóspede novo pela criação manual nunca aparecia na
aba Hóspedes. Agora usa `get_or_create_guest` + `update_guest_profile`
(reaproveitando a função já criada pro perfil do hóspede) pra gravar
email/nacionalidade de verdade. Quando uma cama específica é escolhida
na criação, passa a usar `reservar_cama_com_trava` (mesma trava contra
condição de corrida já usada pra reserva de canal/WhatsApp) - antes a
criação manual nunca escolhia cama nenhuma, então nunca precisou dessa
proteção; agora que oferece essa opção, precisa da mesma segurança.

Testado: hóspede com email/nacionalidade grava certo na tabela `guests`;
escolher uma cama já ocupada no mesmo período é recusado (trava
funcionando); escolher outra cama livre funciona normalmente. Bateria
completa de regressão (preço automático, case-insensitive, Fases 4/5 do
Beds24) rerodada sem quebrar nada.

## Cama "Reservada" com semanas de antecedência, checkout some da lista, status CHECKOUT

Usuário reportou, em duas mensagens seguidas: (1) cama com reserva pro
mês que vem aparecia "Reservada" (azul) no Mapa de Quartos já no dia de
hoje, impedindo perceber que ela está livre pra alugar antes dessa
data - "só tendo a trava pro dia do check-in pra ninguém reservar a
mesma cama" (a trava real de disponibilidade continua intacta em outro
lugar, isso é só sobre a cor exibida); (2) depois do check-out, o
hóspede deveria sair da lista da aba Reservas e só continuar
rastreável pela aba Hóspedes, com status "CHECKOUT".

**Cor "Reservada" só a partir do dia do check-in**: `get_bed_map`
mudou a condição de `checkout_date >= hoje` pra
`checkin_date <= hoje AND checkout_date >= hoje` - ou seja, só entra
"Reservada" quando o período da reserva já INCLUI hoje (chegada já
chegou ou passou, saída ainda não aconteceu), não mais qualquer reserva
futura não-cancelada. A trava de verdade contra dar a mesma cama pra
duas reservas continua em `find_available_beds`/
`reservar_cama_com_trava`/`sync_availability_to_channel`, que sempre
olham o período completo da estadia, não só hoje - só o que muda é a
cor mostrada no mapa.

**Alerta operacional complementar**: como a cama só fica azul a partir
do dia do check-in, adicionado um alerta novo em `/operations` pra
reservas com `checkin_date = hoje` e `checked_in_at` ainda null (mesmo
se já `confirmed`) - "Chegada hoje - atribuir cama e confirmar
check-in: {hóspede}". O alerta antigo ("Check-in de hoje ainda
pendente") só cobre reserva com status != confirmed, o que quase nunca
acontece no dia da chegada (a reserva já foi confirmada bem antes) -
esse novo cobre o caso real: reserva confirmada chegando hoje, ainda
sem check-in físico.

**Check-out sai da lista de Reservas**: `get_reservations_with_stats`
passou a filtrar `checked_out_at IS NULL` na lista retornada - reserva
com check-out já confirmado não aparece mais na aba Reservas. As
estatísticas (KPIs de check-ins/check-outs/receita) continuam
calculadas em cima do conjunto COMPLETO (não filtrado), pra não
subtrair receita já confirmada só porque o hóspede já foi embora.

**Status CHECKOUT na aba Hóspedes**: `get_guests_list` ganhou
`last_checked_out_at` (subquery pegando o `checked_out_at` da reserva
mais recente de cada hóspede). Frontend: coluna Status mostra
"CHECKOUT" (pill vermelha) quando esse campo está preenchido, prioridade
sobre o "Ativo"/"Sem interação" de antes.

Testado o ciclo completo: reserva com check-in daqui 20 dias não deixa
a cama reservada hoje; reserva com check-in hoje deixa a cama reservada
E gera o alerta operacional; depois do ciclo completo (check-in →
check-out → limpeza), a reserva some de `/reservations` e a cama volta
pra `free` (não fica presa em "reserved" por causa de uma reserva futura
na mesma cama); hóspede aparece com `last_checked_out_at` preenchido.

## Seletor de cama filtra por modalidade + camas duplicadas no teste

Usuário testou o formulário novo e reportou duas coisas: (1) o seletor
de camas do modal de check-in mostrou "Compartilhado · Cama 1 (Beliche
- Baixo)" **duas vezes** na lista - pediu pra investigar; (2) o Bruno
tinha reserva numa modalidade específica, mas o seletor de check-in
oferecia camas de QUALQUER modalidade misturadas, o que pode fazer a
recepção atribuir sem querer o hóspede a um quarto diferente do
reservado.

**Item 2 (corrigido)**: `checkinReservationUI` passou a receber também
o `room_type` da reserva (terceiro parâmetro, escapado com o mesmo
padrão já usado em `deleteRoomUI`/`deleteCategoryUI`) e ganhou um
seletor de modalidade próprio, pré-selecionado com a modalidade da
reserva - o seletor de cama (`fillCheckinReservationBedSelect`) agora
filtra por essa modalidade escolhida, com a opção explícita de trocar
se for realmente intencional. Mesmo padrão categoria→cama já usado no
formulário de Nova Reserva.

**Item 1 (investigado, não é bug de código)**: contagem de beds via
`/bed-map` é uma consulta direta na tabela `beds`, sem nenhum JOIN que
pudesse duplicar linhas - se duas camas aparecem com o mesmo rótulo
"Cama 1", são duas linhas de verdade na tabela, criadas em algum
momento (provavelmente um duplo-clique/duplo-envio no formulário "Nova
cama" - `submitNewBed` não tinha nenhuma proteção contra isso, e o
modal de criação de cama fica aberto de propósito depois de criar, pra
permitir criar várias em sequência, o que também facilita clicar
"Criar" duas vezes sem querer pra mesma cama). Não dá pra consertar
dado já duplicado sem acesso ao banco de produção - pedido pro usuário
conferir/excluir a cama duplicada pelo Mapa de Quartos (mesmo fluxo já
usado antes pra limpar quarto duplicado do Beds24).

## Falso positivo no verificador de balanceamento (achado real, não é bug de JS)

Depois de editar `checkinReservationUI`, o `check_dashboard_balance.py`
acusou desbalanceamento (401 chaves abrindo, 400 fechando - antes
841/841). Investigação profunda (scripts de diagnóstico dedicados,
checando cada bloco `<script>` e cada etapa da limpeza de comentário/
string) revelou a causa real: o padrão `.replace(/'/g, "\\'")` (usado
pra escapar aspas simples antes de embutir num atributo `onclick`) já
existia 4 vezes no arquivo (`deleteRoomUI`, `editBedLabelUI`,
`deleteCategoryUI`, `createBeds24RoomForCategory`) - um número PAR.
Cada ocorrência contém um apóstrofo solto dentro de um literal de regex
(`/'/g`), que o verificador (baseado em regex simples, sem entender
sintaxe de regex literal de verdade) trata como se fosse o início de
uma string de aspas simples. Com um número par de ocorrências, elas
acabavam se "auto-parando" aos pares sem quebrar a contagem final. Ao
adicionar uma 5ª ocorrência (em `checkinReservationUI`), o número virou
ímpar, e essa última ficou emparelhada erroneamente com uma aspa simples
bem mais adiante no arquivo, "engolindo" ~45 mil caracteres de código
real como se fosse uma única string gigante.

**Não era um bug de JavaScript de verdade** (o padrão já funciona em
produção nos outros 4 lugares, e o motor real de JS entende regex
literal corretamente) - era uma limitação do script de diagnóstico
(scratchpad, não faz parte do produto). Corrigido trocando a nova
ocorrência por `.split("'").join("\\'")` - mesmo resultado de escape,
sem o apóstrofo solto que confunde o verificador. Balanceamento voltou
a 841/841.

## Não corrigido nesta rodada (fora do escopo, exige acesso a produção)

Cama duplicada mencionada acima - fica pro usuário resolver
manualmente pelo Mapa de Quartos, já que não há como inspecionar/editar
dados de produção diretamente por aqui.

## Fase 6 da integração de canais: webhook de saída genérico (adiantada na frente da Fase 5)

Depois de aprovado um plano completo pra conectar Booking.com/Airbnb/
Hostelworld de verdade (Fase 5, cliente autorizando a própria conta de
OTA na sub-propriedade dele no Beds24), o usuário pediu pra inverter a
ordem: começar pela Fase 6 (webhook de saída genérico) porque ainda não
tem como cadastrar um cliente de verdade pra testar a Fase 5 agora.

Cliente que já tem sistema próprio e usa o StayFlow só pra atendimento/
IA, sem adotar o mapa de quartos do StayFlow como fonte de verdade,
cadastra em Configurações → Integrações uma URL sua. Toda reserva
criada, alterada, cancelada, ou com check-in/check-out feito - de
QUALQUER origem (manual, WhatsApp, ou canal/Beds24, diferente de
`sync_booking_to_channel`/`sync_availability_to_channel` da Fase 4/5,
que só rodam pra origem manual/WhatsApp pra não ecoar de volta pro
Beds24) - dispara um `POST` JSON assinado pra essa URL.

Modelo de dados novo: colunas `hostels.outbound_webhook_url` e
`outbound_webhook_secret` (texto puro - diferente do token master do
Beds24, que é criptografado por expor todos os clientes de uma vez se
vazar; esse aqui, se vazar, só permite forjar evento NO SISTEMA DO
CLIENTE, não expõe nada do StayFlow). O secret é gerado com
`secrets.token_hex(32)` na primeira vez que a URL é salva, e só muda se
o usuário pedir explicitamente ("Gerar nova chave") - trocar só a URL
nunca troca o secret sem avisar.

Backend: `services/outbound_webhook_service.py` (novo) monta o corpo
JSON (`event`, `reservation`, `sent_at`) e assina com HMAC-SHA256
(cabeçalho `X-StayFlow-Signature: sha256=<hex>`), timeout de 5s, nunca
levanta exceção - mesmo princípio de `services/whatsapp_service.py` e
`services/beds24_service.py`. `database.py` ganhou
`dispatch_reservation_webhook(hostel_id, reservation_id, event_type)`,
que busca a URL/secret do hostel (não faz nada se não tiver
configurado), monta o payload da reserva e chama o serviço. Ligado em
9 pontos onde uma reserva nasce/muda/termina:
`create_reservation_record` (created), `create_indefinite_stay`
(created), `close_indefinite_stay` (checked_out),
`create_reservation_from_chat` (created), `update_reservation_status_record`
(cancelled/status_changed), `checkin_reservation_to_bed` (checked_in),
`checkout_reservation_bed` (checked_out), `create_reservation_from_channel`
(created), `update_reservation_from_channel` (cancelled/updated).

Frontend: novo card em Configurações → Integrações, logo abaixo do
card do Beds24 (mesmo `data-settings-section="integracoes"`) - campo
de URL + botão salvar, e depois de ativado mostra a chave secreta
(campo readonly, monoespaçado, com "Copiar"/"Gerar nova chave"/
"Desativar", os dois últimos com `stayflowConfirm`). Rotas novas em
`routes/settings.py`: `GET/POST/DELETE /settings/outbound-webhook` e
`POST /settings/outbound-webhook/regenerate-secret`.

Testado com `STAYFLOW_DATA_DIR` isolado + mocks de
`services.outbound_webhook_service.send_webhook` (sem gastar chamada
real): sem URL configurada não dispara nada; criar/check-in/check-out/
cancelar reserva dispara o evento certo com payload/url/secret
corretos; regenerar chave muda o valor; desativar limpa url e secret;
as 4 rotas via `app.test_client()` real; `send_webhook` de verdade (sem
mock, só o `requests.post` mockado) confirma que a assinatura HMAC
bate byte a byte com o corpo enviado. Regressão de check-in/check-out
já existente (`test_reservations_checkin_checkout.py`) continua
passando sem alteração.

Pendente pra próxima rodada, na ordem que o usuário pediu: (1)
investigar por que o menu do usuário (dropdown no topbar) não mostra o
nome/cargo de quem está logado, mesmo esse usuário aparecendo
corretamente na aba Equipe - investigação começou, ainda sem causa raiz
confirmada; (2) finalizar a frente do "Ver cancelamentos" (backend
pronto: `get_cancelled_reservations`, rota `/reservations/cancelled`,
filtro de `get_reservations_with_stats` já esconde canceladas -
frontend, i18n e testes ainda faltam); (3) Fase 5 de verdade (conectar
uma conta real de Booking.com/Airbnb/Hostelworld), quando houver um
cliente real pra testar; (4) Enter confirma/Esc cancela nas caixas de
cadastro e aviso do dashboard (pedido novo do usuário, ainda não
iniciado).

## Fechamento das três pendências antes de partir pra Instagram/Facebook

Usuário pediu explicitamente pra fechar 100% o que tinha ficado pela
metade antes de começar a integração com Instagram/Facebook. Três
itens da rodada anterior:

### Bug real: menu do usuário nunca mostrava nome/cargo

Causa raiz encontrada (a investigação da rodada anterior tinha
descartado elemento HTML duplicado e função duplicada, mas não tinha
chegado na causa de verdade): `hydrateUserUI` deixava a atribuição de
`.user-name`/`.user-role`/`.user-avatar` por ÚLTIMO na função, depois
de `populateHostelSelector(session)`, `applyPermissionVisibility(...)`,
`hideNavItemsWithoutPermission(...)` e `restoreLastOpenPage()` (essa
última, adicionada numa rodada recente pra persistir a aba aberta no
F5). Qualquer exceção lançada por qualquer uma dessas quatro chamadas
aborta a função no meio, e o menu do usuário nunca chega a ser
preenchido - fica preso em "—" pra sempre, mesmo com a sessão
carregada perfeitamente (explica por que a aba Equipe, que lê a sessão
por outro caminho totalmente separado, sempre mostrou o nome certo).

Corrigido: a atribuição de nome/cargo/avatar agora é a PRIMEIRA coisa
que a função faz (logo depois do guard `if(!u) return`), e as quatro
chamadas seguintes ganharam `try/catch` individual com log no console
- o menu do usuário nunca mais fica órfão, mesmo se alguma dessas
chamadas continuar falhando por outro motivo no futuro. Não foi
possível confirmar ao vivo em navegador (sem acesso a browser neste
ambiente) - validado estaticamente (balanceamento de chaves,
cobertura de i18n, revisão da nova ordem de execução) e testado o
resto do fluxo de reservas que compartilha código adjacente
(regressão de check-in/check-out continua passando). Recomendado
confirmar visualmente no primeiro acesso real depois do deploy.

### Frente de "Ver cancelamentos" finalizada

Backend já estava pronto de uma rodada anterior (`get_cancelled_reservations`,
rota `/reservations/cancelled`). Frontend: botão "🗑️ Ver cancelamentos"
na aba Reservas, ao lado de "+ Nova reserva"/"Morador de longa
duração", abre o `genericModal` compartilhado com uma tabela (hóspede,
quarto/cama, datas, origem, valor, botão "Reativar"). Reativar faz
`PATCH /reservations/<id>` com `status: "confirmed"`, atualiza a tela
principal (`refreshOperationalViews`) e re-renderiza a lista de
canceladas no próprio modal (sem fechar), pra dar pra reativar várias
em sequência. Reaproveitadas as mesmas chaves i18n de coluna já
existentes na tabela principal (`reservations.col.*`) em vez de criar
duplicatas - só 4 chaves novas mesmo (`cancelledBtn`, título/vazio/
botão do modal), nos 5 idiomas. Testado ponta a ponta com
`STAYFLOW_DATA_DIR` isolado: reserva cancelada some da lista principal
e aparece nas canceladas; reativar faz o caminho inverso; rota real
via `app.test_client()`.

### Enter confirma / Esc cancela

Investigação mostrou que quase toda "caixa de cadastro" do dashboard
(convite de equipe, nova função, trocar função, nova reserva, morador
de longa duração, check-in, editar quarto/cama/modalidade, cadastrar
quarto/cama nova, etc - 19 pontos ao todo) já passa pelo MESMO
`genericModal`/`genericModalOverlay` compartilhado, cada um sempre com
exatamente um botão `class="btn"` (nunca "secondary"/"red") como ação
de confirmar - convenção já seguida em todo o código, sem exceção.
Isso tornou a implementação simples: um listener `keydown` global
(estendendo o que já existia só pro `sfAlert`) fecha o `genericModal`
com Esc, e aciona esse botão de confirmar com Enter sempre que o foco
estiver num `<input>`/`<select>` dentro do corpo do modal (nunca numa
`<textarea>`, onde Enter precisa continuar quebrando linha). O sistema
de aviso (`sfAlert`, usado por `alert()`/`stayflowConfirm()`/
`stayflowPrompt()`) já tinha os dois: Esc fecha desde uma rodada
anterior, Enter já confirmava tanto no prompt (listener dedicado) 
quanto no alert/confirm simples (o botão OK recebe foco automático ao
abrir, e Enter num botão focado já aciona o clique nativamente) - nada
precisou mudar ali.

## Início da integração Instagram/Messenger - Fase 1 (fundação de dados)

Duas pesquisas em paralelo antes de planejar: um agente Explore no
backend (padrão exato do WhatsApp - `services/whatsapp_service.py`,
`routes/whatsapp_webhook.py`, `routes/chat.py`, schema do banco) e
outro no frontend (como a aba Chats renderiza hoje, se já existe algum
conceito de canal). Confirmado: zero scaffolding prévio de
Instagram/Facebook em qualquer lugar do código - só links de rodapé no
site e uma `settings.html` estática sem JS nenhum, morta. Também
pesquisei os requisitos reais da Meta (Instagram Messaging API,
Messenger Platform, App Review, Business Verification) pra embasar as
decisões de arquitetura.

Usuário aprovou o plano inicial (conexão manual tipo WhatsApp, um
único par de credencial por Página cobrindo os dois canais) e, na
hora de sair do modo de plano, pediu pra incluir quatro coisas que eu
tinha deixado de fora por padrão de simplicidade: OAuth de verdade (em
vez de colar token à mão), modelo de identidade multi-canal de
verdade (em vez de um atalho com prefixo em cima de `phone`), e
atualização em tempo real da aba Chats - concordando que é o jeito
mais profissional e correto, mesmo dando mais trabalho. No meio da
implementação, pediu mais um ajuste: o WhatsApp (hoje só manual)
também ganha o mesmo tratamento OAuth (via "WhatsApp Embedded
Signup"), e os três canais (WhatsApp, Facebook, Instagram) mantêm um
modo manual como alternativa, lado a lado com o botão de conexão
automática - atualizei o plano registrado antes de continuar
implementando.

Decisões de arquitetura completas estão no plano
(`C:\Users\User\.claude\plans\graceful-pondering-bonbon.md`), resumo
das principais: webhook único `/webhook/meta` pra Messenger e
Instagram (confirmado por pesquisa: os dois entregam no mesmo formato
`entry[].messaging[]`, e o handshake de verificação é idêntico ao que
o WhatsApp já usa - mecanismo genérico de Webhooks da Meta, não
específico de produto); SSE em vez de WebSocket pra tempo real
(WebSocket persistente exigiria trocar o worker do gunicorn de
`threaded=True` pra `eventlet`/`gevent`, mudança de infraestrutura de
produção fora do escopo de uma feature); App Review + Business
Verification da Meta é bloqueio real de produção, não só código -
registrado como ponto explícito que precisa de ação do usuário (criar
o App Meta, submeter pra revisão), com testes rodando normalmente até
lá via contas de teste (limite de 25, sem revisão).

**Fase 1 implementada e testada** (só fundação, nada visível ainda):
- `hostels` ganhou `facebook_page_id`/`facebook_page_access_token`/
  `facebook_oauth_state`, `instagram_business_id`/
  `instagram_access_token`/`instagram_oauth_state`, e
  `whatsapp_oauth_state` (as duas colunas de credencial do WhatsApp já
  existiam - o fluxo OAuth novo grava nas MESMAS colunas que o
  formulário manual já usa, não precisa de coluna extra).
- Tabela nova `guest_channel_identities` (`hostel_id`, `guest_id`,
  `channel`, `external_id`, `UNIQUE(hostel_id, channel, external_id)`)
  - identidade multi-canal de verdade, em vez de forçar IGSID/PSID
  dentro de `guests.phone`.
- Função canônica nova `get_or_create_guest_by_channel(hostel_id,
  channel, external_id, phone=None, name=None)` - resolve/cria hóspede
  pela identidade de canal; `phone` só é gravado de verdade quando
  `channel='whatsapp'` (nos outros canais fica `NULL`, sem valor fake).
  `get_or_create_guest` (por telefone direto) continua existindo pros
  fluxos que não passam por chat (reserva manual). `get_guest_channel`
  resolve o canal de um hóspede pra despacho de envio, com fallback
  `'whatsapp'` pra hóspede antigo sem nenhuma linha em
  `guest_channel_identities` (preserva comportamento de hoje).
- CRUD completo de config/resolver por hostel pro Facebook e pro
  Instagram (espelhando exatamente `get_hostel_whatsapp_config`/
  `save_hostel_whatsapp_config`/`get_hostel_id_by_whatsapp_phone_number_id`),
  e helpers de `oauth_state` (salvar, e consumir - conferir contra o
  valor certo E já limpar, nunca reutilizável, pros três canais).
- Testado isoladamente com `STAYFLOW_DATA_DIR`: 8 cenários (config
  vazia por padrão, salvar/resolver/limpar Facebook e Instagram, state
  OAuth de uso único rejeitando valor errado, identidade multi-canal
  idempotente e isolada por canal, `guests.phone` só preenchido pro
  WhatsApp, fallback de canal pra hóspede antigo, isolamento
  multi-tenant com o mesmo `external_id` em hostels diferentes).
  Regressão dos testes já
  existentes (check-in/check-out, webhook de saída, cancelamentos)
  sem quebra.

**Bloqueado pra Fase 2** (rotas de OAuth de verdade): preciso que o
usuário crie o App Meta do StayFlow e passe `app_id`/`app_secret` -
mesmo tipo de bloqueio externo que a conta master do Beds24 teve na
Fase 1 daquela integração.

## Fase 2 (primeiro pedaço): OAuth real com o Facebook (Messenger)

Usuário já tinha um App Meta criado ("StayFlow AI", mesmo usado pelo
WhatsApp) - não precisou criar um novo, só adicionar os casos de uso
que faltavam (a Meta trocou "Adicionar produto" por "Agregar caso de
uso" nas versões recentes do painel - mesma coisa, nome novo).
Confirmado por App ID/App Secret passados no chat.

Decisão tomada nessa hora: guardar `META_APP_ID`/`META_APP_SECRET`
como variável de ambiente, não numa tabela criptografada como o plano
original previa - é um segredo do StayFlow inteiro (um App só, não um
por hostel), mesmo padrão já usado pro `WHATSAPP_VERIFY_TOKEN`, mais
simples e sem precisar resolver "como faço a credencial chegar no
banco de produção" (pra isso teria que existir alguma rota
administrativa ou script rodado direto contra o banco - desnecessário
quando dá pra só configurar a variável de ambiente no painel do
Render). Removida a tabela `meta_app_credentials` e as duas funções
`save_meta_app_credentials`/`get_meta_app_credentials` que tinham sido
criadas na Fase 1 pra esse fim, antes de qualquer código depender
delas.

Implementado: `services/meta_oauth_service.py` (novo) - troca `code`
por token de usuário, troca por token de longa duração
(`grant_type=fb_exchange_token`), busca a Página conectada via
`/me/accounts` (que já devolve o token PRÓPRIO da Página de graça,
pronto pra mandar mensagem depois) - pega a primeira Página que a
conta administra (a grande maioria dos hostels só tem uma; escolher
entre várias fica pra se algum dia for um problema real). Nunca
levanta exceção, mesmo princípio de `services/beds24_service.py`.

`routes/meta_oauth.py` (novo): `GET /oauth/facebook/connect` (gera um
`state` anti-CSRF, salva no hostel, redireciona pra tela de
consentimento da Meta) e `GET /oauth/facebook/callback` (confere o
`state` - e já limpa, nunca reutilizável -, troca o `code` pela
Página, salva `facebook_page_id`/`facebook_page_access_token` no
hostel, redireciona de volta pro dashboard com o resultado numa query
string simples `?meta_oauth=facebook&status=success|error&message=...`,
já que esse fluxo é redirect de tela cheia, não popup - diferente do
WhatsApp Embedded Signup, que vai precisar de outro mecanismo mais
pra frente).

Frontend: card "Facebook Messenger" em Configurações → Comunicação,
com os dois modos lado a lado pedidos pelo usuário (decisão 1b do
plano) - botão "Conectar Facebook" (manda pro `/oauth/facebook/connect`)
e "Configurar manualmente" (expande um formulário Page ID + Access
Token, mesmo layout do card do WhatsApp) - os dois caminhos gravam nas
mesmas colunas, então o estado "conectado" não precisa saber por qual
deles a credencial chegou. `handleMetaOAuthReturn()` roda no boot da
sessão, detecta a query string do callback, abre Configurações →
Comunicação automaticamente e mostra a mensagem de sucesso/erro, e
limpa a URL depois (evita reprocessar o mesmo resultado se a pessoa
der F5).

Corrigido de quebra um bug real desta sessão: `loadOutboundWebhookSettings`
só tinha sido registrado no `PAGE_LOADERS.settings` (reload por troca
de idioma), nunca no listener principal de `stayflow:session-ready` -
o card do webhook de saída (implementado numa rodada anterior) ficava
sempre vazio no carregamento normal da página, só preenchia depois de
trocar de idioma uma vez. Corrigido registrando nos dois lugares.

Testado com a Graph API mockada (sem gastar chamada real): fluxo
completo connect→callback→Página salva com token certo; `state`
errado ou reutilizado é rejeitado; connect falha educadamente sem
`META_APP_ID`/`META_APP_SECRET` configurado; rotas de configuração
manual (`GET`/`POST`/`DELETE /settings/facebook`) - salvar, manter
token quando o campo vem vazio, desconectar. Balanceamento de
chaves/parênteses e cobertura i18n conferidos, sem regressão nos
testes já existentes.

Pendente pras próximas rodadas, uma de cada vez: pegar a URL de
produção do usuário pra confirmar a Redirect URI exata que precisa
estar cadastrada no App Meta (`https://<domínio>/oauth/facebook/callback`);
Instagram Login (mesmo padrão, App/API diferente); WhatsApp Embedded
Signup (via popup JS, mecanismo de callback diferente dos outros
dois); depois disso, entrada (webhook `/webhook/meta`), saída (envio
de mensagem), migração de identidade, e tempo real (SSE) - todas
detalhadas no plano completo.

## Configuração ao vivo com o usuário - achado real e confirmação

Guiei o usuário passo a passo pelo painel da Meta (achado dele: a
Meta trocou "Adicionar produto" por "Agregar caso de uso" nas versões
recentes). App Meta já existia ("StayFlow AI", mesmo do WhatsApp) -
só precisou adicionar os casos de uso de Messenger e Instagram
("Mensajes comerciales"). App ID (`2039319673644412`) e App Secret
passados no chat - configurados como `META_APP_ID`/`META_APP_SECRET`
no Render.

Achado real na hora de configurar o Facebook Login: esse App usa o
modo "Facebook Login for Business" com Configuration (não o Facebook
Login clássico que o código original assumia) - as permissões
(`pages_show_list`/`pages_messaging`/`pages_manage_metadata`) ficam
empacotadas numa "Configuración" própria, que gera um Configuration
ID (`1632026542144059`), usado na URL de autorização via `config_id`
em vez de `scope` solto. Corrigido `get_facebook_authorize_url`
(`services/meta_oauth_service.py`) e as duas checagens de
"App configurado" (`routes/meta_oauth.py`, `routes/settings.py`) pra
exigir `FACEBOOK_CONFIG_ID` também, não só `META_APP_ID`/`META_APP_SECRET`.
Testes atualizados pra cobrir o `config_id` na URL e o novo requisito
de configuração - todos passando.

Também precisou cadastrar a Redirect URI
(`https://stayflowsolutions.com/oauth/facebook/callback`) na tela
"Configurar" (separada da tela "Configuraciones" com o Configuration
ID) - campo "URI de redireccionamiento de OAuth válidos", dentro de
"Configuración del cliente de OAuth".

**Confirmado funcionando de ponta a ponta em produção**: botão
"Conectar Facebook" no StayFlow → tela de consentimento da Meta →
callback → Página salva no hostel, usuário reportou "conectado com
sucesso". Fecha o ponto que o plano tinha deixado em aberto (mesmo
padrão da integração Beds24 - só confirma o formato exato da API
testando ao vivo).

Próximo passo, um de cada vez: Instagram Login.

## Messenger 100% funcional - Fase 3+4 (entrada e saída)

Perguntado se era melhor conectar os três canais primeiro ou terminar
cada um por completo antes do próximo - recomendei terminar um por
vez (aprende a API de verdade num canal só, resultado testável mais
cedo, risco isolado) e o usuário concordou.

Comecei pelo webhook de entrada (`routes/meta_webhook.py`), copiando o
handshake genérico do WhatsApp. Na hora de ligar no pipeline real
(`process_incoming_message`, `routes/chat.py`), apareceu um problema
estrutural que não tinha ficado óbvio antes: quase toda função do
pipeline resolvia o hóspede buscando de novo por
`WHERE hostel_id = ? AND phone = ?` - `analyze_message`
(`decision_engine.py`), `is_guest_ai_paused`, `get_guest_language`,
`update_guest_name`/`update_guest_language`, e o próprio
`save_message_db` (que decide `conversation_id` a partir de um
`get_or_create_guest(hostel_id, phone)` interno). Pra Messenger, cujo
`guests.phone` fica `NULL` de propósito (decisão da Fase 1 - não forçar
PSID/IGSID como telefone fake), NENHUMA dessas buscas acharia o
hóspede certo. Sem esse achado, o Messenger teria "funcionado" só na
aparência (mensagem chegando, mas IA nunca pausável por hóspede, nunca
sabendo o idioma certo, nunca puxando o histórico certo, oportunidade
nunca gravada).

Resolvido resolvendo `guest_id` UMA VEZ, no topo de
`process_incoming_message`, via `get_or_create_guest_by_channel` (já
existia da Fase 1) - e criando equivalentes por `guest_id` de cada
função afetada: `is_guest_ai_paused_by_id`, `get_guest_language_by_id`,
`update_guest_name_by_id`, `update_guest_language_by_id` (`database.py`,
novas, WHERE id = ? em vez de WHERE phone = ?, as antigas continuam
existindo intactas pra quem ainda as chama). `analyze_message` mudou de
assinatura pra receber `guest_id` já resolvido em vez de buscar de
novo (só um call site, risco baixo). `save_message_db_for_guest`
(nova) espelha `save_message_db`, mas recebe `guest_id` direto -
`save_message_db` original fica intacta, só usada pelos poucos call
sites legados de WhatsApp que não passam pelo pipeline principal
(imagem de documento, mensagem de equipe). De quebra,
`save_message_db_for_guest` é a única que realmente grava o canal
certo em `conversations.channel` (fazia tempo que ficava sempre
`'api'`, achado real de uma rodada anterior nunca de fato corrigido).

Ponto de maior risco desta rodada: um hóspede de WhatsApp que já existia
ANTES desta integração (criado pelo caminho antigo, sem nenhuma linha
em `guest_channel_identities` ainda) não podia simplesmente "criar um
hóspede novo" na primeira mensagem depois do deploy - o telefone já
existe, e `guests` tem `UNIQUE(hostel_id, phone)`, um INSERT duplicado
quebraria com erro de integridade. `get_or_create_guest_by_channel`
ganhou uma checagem extra: se o canal é WhatsApp e já existe um
hóspede com aquele telefone (sem identidade de canal ainda), ADOTA o
`guest_id` existente e só cria a linha de identidade que faltava, em
vez de tentar inserir de novo. Testado explicitamente (Teste 6 do
roteiro) simulando esse cenário exato.

Memória da IA (`services/memory_service.py`, arquivo JSON de
histórico) não precisou de nenhuma mudança de código - só passou a
receber uma chave diferente pra canais sem telefone
(`"messenger:<psid>"` em vez do valor cru), function `_memory_key()`
nova em `chat.py`. A chave do WhatsApp continua idêntica a sempre
(`hostel_id:telefone`), sem risco de invalidar histórico de conversa
já em produção.

Novo `services/messenger_service.py` (`send_messenger_message`), mesmo
contrato "nunca levanta exceção, retorna bool" de
`services/whatsapp_service.py` - usa o token da própria Página (obtido
no OAuth da rodada anterior) via `POST /me/messages`.

Testado (8 cenários com `STAYFLOW_DATA_DIR` isolado, `ask_ai` e
`send_messenger_message`/`send_whatsapp_message` mockados): mensagem
via Messenger cria hóspede sem telefone fake e com identidade de
canal; segunda mensagem do mesmo PSID reaproveita o mesmo hóspede;
mensagens gravadas na ordem certa com `conversations.channel` correto;
IA nunca recebe o PSID como se fosse telefone; WhatsApp continua
gravando telefone de verdade e passando ele pra IA (regressão); hóspede
antigo de WhatsApp adotado sem duplicar; rota real `/webhook/meta`
(handshake + POST) processando mensagem de ponta a ponta; webhook com
`page_id` desconhecido não quebra, só ignora. Regressão completa de
tudo que já existia (reservas, check-in/check-out, webhook de saída,
cancelamentos, OAuth do Facebook, configurações manuais) sem quebra.

Próximo passo: Instagram Login (mesmo padrão OAuth+webhook+envio, App
diferente na Meta).

## Bug real de produção: IA no Messenger caía no fallback "confirmar com a equipe"

Guiei o usuário pelo teste ao vivo (webhook inscrito, mensagem enviada
pra Página conectada) - respondeu, mas com o texto fixo "Deixa eu
confirmar isso com a equipe e já te retorno" em vez de uma resposta de
verdade. Usuário pediu explicitamente: quer que a IA no Messenger
funcione EXATAMENTE igual ao WhatsApp - pergunte idioma, nome, processe
pedido de reserva do mesmo jeito.

Causa raiz: `services/ai_service.py` só liberava as ferramentas de
reserva pro modelo (`get_room_options`, `get_available_beds`,
`create_reservation`, `extend_reservation`, `flag_extension_for_approval`)
quando `hostel_id and guest_phone` - e `guest_phone` só existe de
verdade pro WhatsApp (Messenger passa `None` de propósito, pra IA não
tratar o PSID como se fosse telefone, decisão da rodada anterior). Sem
essas ferramentas, a IA tentava ajudar com o pedido de reserva mas não
tinha como agir - ficava chamando `save_guest_language`/`save_guest_name`
sem nunca "fechar" com texto, esgotava as `MAX_TOOL_ROUNDS` (4) e caía
no fallback.

Corrigido trocando o portão pra `guest_id` (que existe de verdade pra
qualquer canal, resolvido uma vez no topo do pipeline) em vez de
`guest_phone`. Isso expôs, em cascata, o MESMO problema estrutural já
corrigido no pipeline de mensagem (rodada anterior) só que agora nas
ferramentas de reserva: `create_reservation_from_chat`,
`attempt_extend_reservation`, `flag_extension_for_approval`
(`database.py`) resolviam o hóspede buscando de novo por
`guests.phone` internamente - nunca funcionariam pra Messenger. As três
mudaram de assinatura pra receber `guest_id` já resolvido em vez de
`phone` (só um call site cada, em `ai_service.py`, risco baixo).

De quebra, `create_reservation_from_chat` também tinha `source =
'whatsapp'` HARDCODED no INSERT da reserva, não importa de qual canal
ela realmente veio - corrigido pra usar `get_guest_channel(hostel_id,
guest_id)` (já existia da Fase 1) como o `source` real. Isso por sua
vez expôs mais dois lugares que só reconheciam `('manual', 'whatsapp')`
como "essa reserva nasceu dentro do próprio StayFlow" (usado pra
decidir se é seguro sincronizar com o Beds24 sem risco de ecoar de
volta uma reserva que já veio de lá) - criada a constante
`STAYFLOW_NATIVE_SOURCES = ("manual", "whatsapp", "messenger",
"instagram")`, usada nos dois lugares (um deles precisou virar SQL
parametrizado com `IN (?,?,?,?)` em vez do literal fixo antigo).

`_flag_booking_needs_manual_setup` (dispara quando a IA tenta reservar
uma modalidade sem nenhuma cama cadastrada) também mudou pra receber
`guest_id` direto, mesmo motivo.

Testado (6 cenários novos, com `STAYFLOW_DATA_DIR` isolado): reserva
criada via Messenger grava `source='messenger'` e valor calculado
certo; reafirmar o mesmo pedido não duplica (dedupe agora por
`guest_id`+`source`+datas, não mais telefone); WhatsApp continua
gravando `source='whatsapp'` (regressão); modalidade sem cama vira
oportunidade vinculada ao `guest_id` certo mesmo sem telefone; extensão
de estadia (`attempt_extend_reservation`/`flag_extension_for_approval`)
funciona por `guest_id`; e o teste mais direto - chamando `ask_ai` de
verdade (só o client da OpenAI mockado) e confirmando que as
ferramentas de reserva aparecem na lista `tools` mesmo com
`guest_phone=None`, contanto que `guest_id` exista. Regressão completa
de tudo (incluindo o teste de eco do Beds24, que exercita bem as duas
checagens de `STAYFLOW_NATIVE_SOURCES`) sem quebra.

Adicionado log permanente em `ask_ai` (não só pra esse debug -
qualquer ocorrência futura do fallback "confirmar com a equipe" agora
aparece nos logs do Render com as ferramentas que o modelo tentou
chamar em cada rodada, facilitando diagnosticar sem precisar
reproduzir manualmente).

Pendência conhecida, não crítica: `save_guest_date_of_birth`/
`save_guest_nationality` (parte do registro pós-reserva) ainda são
buscadas por telefone - com `guest_phone=None` no Messenger, essas
duas ficam mudas (não travam, só não gravam) até uma próxima rodada
de limpeza. Baixo risco (estágio avançado da conversa, depois da
reserva já criada), registrado pra não esquecer.

## Nome automático do hóspede no Messenger (e Instagram, quando chegar)

Pedido do usuário: diferente do WhatsApp (o número de telefone não
revela quem é a pessoa), Messenger e Instagram já entregam a conversa
identificada de verdade - a IA não deveria perguntar o nome, já deveria
usar ele naturalmente, inclusive na própria mensagem de boas-vindas
("Olá Caio!").

Novo `get_messenger_user_profile(page_access_token, psid)`
(`services/messenger_service.py`) - `GET /{psid}?fields=first_name,last_name`
na Graph API, mesmo contrato nunca-levanta-exceção dos outros serviços.
Chamado em `routes/meta_webhook.py` a cada mensagem recebida (custo
desprezível - só é de fato GRAVADO na primeira vez, já que
`get_or_create_guest_by_channel` só usa o parâmetro `name` na hora de
CRIAR o hóspede, mensagens seguintes acham o hóspede já existente e
ignoram). `process_incoming_message` ganhou um parâmetro `name` pra
receber isso; e passou a buscar o nome já salvo do hóspede
(`get_guest_name_by_id`, nova) pra informar pra IA em toda mensagem,
não só na criação.

`ask_ai` ganhou `guest_name` e um `{name_instruction}` novo no prompt
(mesmo padrão já usado pra idioma/telefone) - quando o nome já é
conhecido, troca a instrução de "pergunte o nome quando ele disser,
chame save_guest_name" pra "você já sabe o nome, use naturalmente,
NÃO pergunte de novo, não precisa chamar save_guest_name". Como a
busca do perfil acontece ANTES de gerar a resposta, isso já funciona
na primeiríssima mensagem da conversa - não precisa de uma segunda
mensagem pra "aprender" o nome.

Testado: nome do perfil buscado e gravado certo no hóspede novo (sem
forçar telefone fake); `ask_ai` recebe `guest_name` já na primeira
mensagem via webhook real; o prompt monta a instrução certa nos dois
casos (nome conhecido vs desconhecido); WhatsApp sem nome ainda salvo
continua pedindo do jeito de sempre (regressão). Regressão completa
de tudo sem quebra.

Mesma lógica se aplica ao Instagram quando o Instagram Login for
implementado (a API do Instagram também expõe nome/username do
perfil pelo IGSID) - só repetir o padrão de `get_messenger_user_profile`.

## Selo de canal na aba Chats/perfil + nome de hóspede clicável na aba Reservas

Dois pedidos do usuário nessa rodada: (1) identificar visualmente de
onde vem cada conversa (WhatsApp/Messenger/Instagram), de forma
discreta, na aba Chats e no perfil do hóspede; (2) nome do hóspede
clicável na aba Reservas, abrindo o mesmo perfil já usado na aba
Hóspedes - motivo explícito: além de facilitar o acesso, garante que
esse perfil "precisa existir" pra qualquer reserva, inclusive morador
de longa duração (usuário reportou não estar achando o perfil do
morador fixo que criou pra testar o saldo devedor - fica pendente
investigar à parte, depois desta rodada).

Backend: `get_chats_list` e `get_guest_profile` (`database.py`) passaram
a devolver `channel` - o primeiro via subquery direta em
`guest_channel_identities` (pega a mais recente), o segundo reaproveitando
`get_guest_channel` (já tinha fallback `'whatsapp'` pro hóspede sem
nenhuma identidade de canal registrada, da Fase 1).

Frontend: `channelBadgeHtml(channel)` (novo, `dashboard.html`) monta um
selo pequeno e discreto (cor por canal - verde WhatsApp, roxo Messenger,
rosa Instagram), usado em três lugares: lista de conversas (`chats-live.js`,
ao lado do nome), título da conversa aberta (mesmo arquivo), e cabeçalho
"Contato" do modal de perfil do hóspede (`openGuestProfileModal`,
`dashboard.html`). `CHANNEL_DISPLAY_LABELS` ganhou entradas pra
`messenger`/`instagram`/`api` (esse último cobre `conversations.channel`
antigo, sempre gravado como `'api'` antes da Fase 3).

`guestNameLink(guestId, guestName)` (novo) - nome de hóspede vira link
clicável (`onclick="openGuestProfileModal(...)"`, mesma função que a
aba Hóspedes já usa) em qualquer lugar que já tinha `guest_id`
disponível na linha: reserva normal, morador de longa duração, e a
lista do modal "Ver cancelamentos" - os três já traziam `guest_id` na
consulta, só faltava usar. Cai pra texto simples se `guest_id` vier
vazio (defesa, não deveria acontecer na prática).

Testado (`get_chats_list`/`get_guest_profile` devolvendo o canal certo
por hóspede, incluindo o fallback pro hóspede pré-integração) e
regressão completa sem quebra. Balanceamento de chaves/parênteses e
cobertura i18n conferidos (nomes de canal são texto fixo/marca, mesmo
padrão já usado pra WhatsApp/Airbnb/Booking.com em `CHANNEL_DISPLAY_LABELS`,
não precisam de tradução).

## Bug real: perfil do morador fixo não existia, crédito sumido do Financeiro

Usuário reportou, logo depois de eu ter implementado os nomes
clicáveis: não achava o perfil do morador de longa duração que criou
pra testar, e o crédito de US$ 100.000 que registrou como pagamento
(pra testar se o saldo ia descontando por dia) não aparecia em
Financeiro. Pediu pra eu continuar o que estava fazendo e investigar
isso depois - investigado nesta rodada.

**Causa raiz do primeiro**: `create_reservation_record` e
`create_indefinite_stay` só criavam a linha em `guests` quando um
TELEFONE era passado (`if phone: guest_id = get_or_create_guest(...)`)
- reserva ou estadia cadastrada só com nome (o caso comum de morador
fixo/funcionário, que muitas vezes nem tem telefone cadastrado) nunca
ganhava `guest_id` nenhum. Não era só "difícil de achar" - o perfil
literalmente não existia, `reservations.guest_id` ficava `NULL`. Meu
`guestNameLink()` da rodada anterior já lidava bem com isso (cai pra
texto simples sem link quando `guest_id` é vazio), mas a causa de
verdade era essa.

Corrigido com `create_guest_without_phone(hostel_id, name)` (novo,
`database.py`) - INSERT direto, sempre cria um hóspede novo (nunca
tenta reaproveitar um existente, já que sem telefone não há nenhuma
chave confiável pra saber que duas reservas "sem telefone" são a
mesma pessoa - diferente de `get_or_create_guest`, que dedupe por
telefone). Usada nos dois pontos que antes só criavam hóspede "se
tinha telefone".

**Causa raiz do segundo**: `get_finance_summary` somava só
`reservations.amount` pra calcular a receita confirmada - mas estadia
de longa duração (`stay_type='indefinite'`) nasce SEMPRE com
`amount=0` (não tem valor fechado, o que existe é uma diária
acumulando saldo devedor, controlado à parte por
`reservation_payments`/`get_reservation_balance`, mecanismo próprio já
existente). Qualquer pagamento registrado contra um morador fixo era
dinheiro de verdade recebido, mas ficava completamente invisível na
receita.

Corrigido: a soma agora usa `SUM(reservation_payments.amount)` no
lugar de `amount` especificamente quando `stay_type='indefinite'`
(`CASE WHEN r.stay_type = 'indefinite' THEN ... ELSE r.amount END`,
via `LEFT JOIN` agregado) - reserva fixa continua somando `amount`
exatamente como antes, zero mudança de comportamento pra ela. De
quebra, adicionada uma terceira linha na `UNION ALL` de movimentações
(`'Pagamento'`, puxando de `reservation_payments` direto) - antes só
existiam `'Reserva'` e `'Oportunidade'` no extrato, um pagamento de
morador fixo nunca aparecia lá nem como R$0 (a linha da reserva em si
já mostrava R$0, mas nenhuma linha separada mostrava o pagamento de
verdade).

Testado (`STAYFLOW_DATA_DIR` isolado): reserva manual sem telefone cria
hóspede de verdade, aparece na lista de Hóspedes e abre perfil
normalmente (`phone=None`, não um telefone fake); estadia de longa
duração sem telefone igual; duas reservas sem telefone (nomes
diferentes) viram hóspedes DIFERENTES, sem colidir no mesmo registro;
receita confirmada passa a incluir o pagamento do morador fixo
(regressão confirmando que reserva fixa continua contando `amount`
normalmente); pagamento aparece na lista de movimentações como
`'Pagamento'`; saldo do perfil reflete o crédito (negativo = a favor
do hóspede). Regressão completa de tudo (incluindo os testes de
reserva/webhook/Beds24, que criam hóspede com e sem telefone em vários
pontos) sem quebra.

## Nome do Messenger ainda não aparecia (hóspede criado antes do fix)

Testando ao vivo de novo: selo de canal funcionando certinho (roxo
"Messenger", verde "WhatsApp"), IA respondendo de verdade (preço,
opções de quarto) - mas o nome continuava "Sem telefone"/"Hóspede" na
aba Chats, mesmo já com o nome automático (rodada anterior) no ar.

Causa: `get_or_create_guest_by_channel` só grava o `name` recebido na
hora de CRIAR o hóspede (branch de `INSERT`). Essa conversa específica
já existia de um teste anterior (de antes do nome automático existir)
- toda mensagem seguinte só encontrava a identidade de canal já
cadastrada e devolvia o `guest_id` direto, sem passar perto do `name`
nenhuma vez.

Corrigido: no branch onde a identidade já existe, se o hóspede ainda
está sem nome salvo E um nome foi passado nessa chamada, preenche
retroativamente (`UPDATE guests SET name = ...`) - nunca sobrescreve um
nome que já existe. Resolve tanto esse caso (hóspede de antes do fix)
quanto qualquer falha transitória futura (ex: a primeira busca de
perfil no Graph API falhar por instabilidade, autocorrige na mensagem
seguinte).

Testado: hóspede sem nome recebe o nome na mensagem seguinte sem
duplicar registro; hóspede que já tem nome não é sobrescrito por um
valor diferente vindo depois. Regressão completa sem quebra.

## IA sugerindo o WhatsApp real como canal alternativo

Pedido do usuário testando a conversa do Messenger: a conversa vai
bem, mas a IA não tem o número real de WhatsApp do hostel
(+5493883154375) - ele quer que, logo no início (boas-vindas) e de
novo perto do fim (dúvidas/confirmações), a IA sugira ao hóspede que,
se preferir, pode falar por WhatsApp também - só quando a conversa
não é já pelo próprio WhatsApp (não faz sentido sugerir o canal em
que já está).

Achado investigando: `hostels.phone` já existia como coluna (usada
internamente só pelo endpoint de teste manual, `get_hostel_id_by_number`),
mas nunca teve rota nem campo de UI pra ser preenchida - o número real
do hostel nunca chegou a ser salvo em lugar nenhum, por isso a IA não
tinha como conhecê-lo.

Corrigido: `save_hostel_phone(hostel_id, phone)` (novo, `database.py`).
Campo novo "Número de WhatsApp visível pro hóspede" no card WhatsApp
Business (Configurações → Comunicação), diferente do "Phone Number ID"
que já existia (esse é o ID interno da Meta pra autenticar chamada de
API, não um número legível) - salvo/lido junto no mesmo
`GET`/`POST /settings/whatsapp`.

`ask_ai` ganhou dois parâmetros novos, `channel` (explícito agora, em
vez de inferido só pela presença de `guest_phone`) e `hostel_phone`.
Novo bloco `{alt_channel_instruction}` no prompt, condicional: só
aparece quando `channel != "whatsapp"` E o hostel tem
`hostel_phone` configurado - pede pra IA mencionar o WhatsApp
brevemente como alternativa na mensagem de boas-vindas (primeira ou
segunda mensagem) e de novo perto do fechamento da conversa
(dúvidas finais/confirmação), sem repetir isso em toda mensagem.
`routes/chat.py` busca `get_hostel(hostel_id)["phone"]` e repassa pra
`ask_ai` junto com o `channel` já resolvido.

Testado: `save_hostel_phone`/`get_hostel` salvam e devolvem o número
certo; rota `/settings/whatsapp` grava e lê `contact_phone` junto com
os outros dois campos; instrução de canal alternativo aparece no
prompt só na combinação certa (Messenger + número configurado),
ausente no próprio WhatsApp e ausente quando o hostel não tem número
cadastrado; `process_incoming_message` repassa o número certo pra
`ask_ai`. Balanceamento de chaves/parênteses, cobertura i18n (2 chaves
novas, 5 idiomas) e regressão completa sem quebra.

## Perfil do hóspede: leitura por padrão, e Reservas leva pra Hóspedes

Usuário mandou um print: clicou no nome do hóspede numa reserva vinda
do Messenger e abriu o modal de perfil com todos os campos vazios,
apesar de ter mandado nome, documento e foto pelo chat. Ele queria
outra coisa nesse clique - não abrir um cadastro em branco ali mesmo,
e sim: clicar no nome na aba Reservas leva pra aba Hóspedes; dentro da
aba Hóspedes, clicar no hóspede mostra um perfil de **leitura** (campo
fixo com o que já existe), não um formulário aberto pra cadastrar -
com um botão explícito "Editar" pra quem quiser mudar algo.

`guestNameLink()` (usada em Reservas, morador de longa duração e no
modal de cancelamentos) trocou `onclick="openGuestProfileModal(...)"`
por `onclick="goToGuestProfile(...)"` (nova) - troca de aba pra
"guests", recarrega a lista (`loadGuests()`) e dá scroll + destaque
visual temporário (`.guest-row-highlight`, 2s, `@keyframes`) na linha
do hóspede certo, usando um `data-guest-row-id` novo que `loadGuests()`
passou a gravar em cada `<tr>`.

`openGuestProfileModal()` foi reescrita: agora guarda o perfil já
buscado em `window._currentGuestProfile` (evita rebuscar ao alternar
entre ler/editar) e delega o desenho pra `renderGuestProfileModal(
profile, editMode)`, que monta o MESMO conteúdo em dois modos -
leitura (`guestReadonlyField()`, caixa fixa estilizada pra parecer um
input desabilitado, mostrando "—" quando vazio) ou edição (o grid de
`<input>` de sempre, com Salvar/Cancelar). Chamada sem `editMode` (uso
direto na aba Hóspedes) abre em leitura; o botão "✏️ Editar" troca pra
edição; "Cancelar" volta pra leitura sem perder o que já tinha; salvar
com sucesso invalida o cache, recarrega a lista de hóspedes em segundo
plano e reabre o modal em leitura já mostrando o valor novo salvo.

Testado: navegação Reservas → Hóspedes chega na aba certa, com scroll
e destaque na linha certa; perfil abre em leitura por padrão; alternar
leitura ↔ edição preserva os dados; salvar atualiza a lista e reabre em
leitura com o valor novo. Regressão completa sem quebra.

## Nacionalidade/data de nascimento não salvavam no Messenger, e documento sem tratamento nenhum

Duas causas raiz diferentes, achadas investigando o mesmo print acima
(perfil vazio apesar do hóspede ter mandado tudo pelo chat):

**Causa 1** - `save_guest_date_of_birth`/`save_guest_nationality`
(`database.py`) faziam `UPDATE guests SET ... WHERE phone = ?`. Como
`guests.phone` é sempre `NULL` de propósito pra Messenger/Instagram
(decisão já tomada na integração de canais - não força um ID de canal
como se fosse telefone), qualquer chamada da IA pra salvar
nacionalidade ou data de nascimento nesses canais afetava
silenciosamente ZERO linhas - sem erro nenhum, só não fazia nada.
Corrigido com `save_guest_date_of_birth_by_id`/`save_guest_nationality_by_id`
(novo, `WHERE id = ?`), usadas pelos handlers de tool-call
correspondentes em `ask_ai` (`services/ai_service.py`).

**Causa 2** - Messenger nunca teve NENHUM tratamento de imagem/
documento, diferente do WhatsApp (que já tinha
`handle_incoming_document_image` desde o começo). A Send API do
Messenger entrega o anexo com uma URL de CDN já pronta pra baixar
direto (`message.attachments[].payload.url`) - mais simples que o
WhatsApp, que exige trocar um `media_id` por URL temporária antes.
Novo `download_messenger_attachment(url)` (`services/messenger_service.py`,
`requests.get` simples, nunca levanta exceção) e
`handle_incoming_document_image(hostel_id, psid, attachment_url,
access_token)` (`routes/meta_webhook.py`, mesmo padrão do equivalente
WhatsApp: resolve/cria o hóspede, salva o documento, grava uma
mensagem placeholder na conversa, confirma o recebimento por texto
direto). O loop principal do webhook (`receive_message`) agora separa
mensagem com anexo de imagem (vai pro tratamento de documento) de
mensagem de texto normal (segue pro pipeline de IA de sempre).

Testado: nacionalidade/data de nascimento salvas certo por `guest_id`
mesmo sem telefone; `ask_ai` chamando as versões `_by_id` certas via
tool-call; documento do Messenger recebido, salvo com o `guest_id`
certo, mensagem placeholder gravada na conversa e confirmação enviada;
falha ao baixar o anexo avisa o hóspede sem derrubar o webhook.
Regressão completa sem quebra.

## Mapa de Quartos: "Novo quarto"/"Nova cama" pareciam sem reação ao clique

Usuário reportou que, no menu "☰ Ações" do Mapa de Quartos, os itens
"Novo quarto" e "Nova cama" não respondiam ao clique. Investigação
inicial (leitura de código) não achou nada óbvio - as duas funções
existiam, o HTML dos botões era idêntico aos outros itens do mesmo
menu que funcionavam, e não havia erro de sintaxe JS (confirmado
isolando as duas funções e validando com um parser JS de verdade).

Como a investigação estática não convergia, subi o servidor local com
um banco de teste e testei o clique de verdade num navegador headless
(Playwright, recém-instalado no ambiente). O teste confirmou o
sintoma - clicar no botão "Novo quarto" não abria o modal - e revelou
a causa exata: no ponto exato do botão, o elemento que realmente
recebia o clique não era o botão, e sim `#roomMapGrid` (a grade de
quartos/camas abaixo do menu), mesmo o dropdown tendo `z-index:20`.

Causa raiz: `.card>*{position:relative;z-index:1}` - regra genérica que
existe pra por o conteúdo de qualquer `.card` acima dos gradientes
decorativos de fundo (`.card::before`/`.card::after`) - dá o MESMO
`z-index:1` a TODOS os filhos diretos de um `.card`, sem distinção.
No card do Mapa de Quartos, a linha do cabeçalho (que contém o
dropdown "Ações") e `#roomMapGrid` são ambos filhos diretos do mesmo
`.card` - empatam em `z-index:1`, e o desempate entre elementos com
z-index igual é por ordem no DOM: `#roomMapGrid` vem depois, então
pinta por cima. O `z-index:20` do dropdown nunca chegava a ser
comparado com o do grid, porque só vale DENTRO do próprio contexto de
empilhamento que a linha do cabeçalho criou (o dropdown é filho da
linha do cabeçalho, não do `.card` diretamente) - a comparação real que
decide quem fica por cima acontece um nível acima, entre a linha do
cabeçalho inteira e o grid, e aí os dois estão empatados em 1.

Corrigido dando à `<div>` da linha do cabeçalho um `z-index:2` inline -
suficiente pra vencer o empate contra o `1` do grid no nível do
`.card`, sem mexer na regra genérica `.card>*` (que existe por um
motivo válido e é usada em toda a aplicação).

Testado: clique de verdade (sem `force`) nos dois botões agora abre o
modal certo, confirmado via Playwright; sem erros de console;
balanceamento de chaves/parênteses do `dashboard.html` inalterado.

## Caixas de "cadastro" clicáveis em Comunicação e Integrações

Retomada a feature que tinha sido iniciada e revertida numa rodada
anterior (ficou num estado inconsistente - cards duplicados/ocultos -
quando um bug mais urgente interrompeu o trabalho). Pedido original do
usuário: em Configurações → Comunicação, "transforme tudo que for
cadastro em caixa também, assim fica só a caixa clicável de cada meio,
e suas configurações ocultas na caixa" - e replicar "em toda StayFlow
onde faça sentido".

Desta vez, os quatro cards que são claramente "cadastro de um canal/
integração" (WhatsApp Business e Facebook Messenger em Comunicação;
integração com canais/Beds24 e Webhook de saída em Integrações)
viraram caixas resumidas (`.settings-summary-card`, CSS que já tinha
sido criado na tentativa anterior e ficou sem uso até agora): título +
uma linha de status ("✅ Conectado", "Não configurado ainda - clique
pra conectar", etc.) + um chevron. O card "Comunicação" geral (sininho
de alertas, horário de silêncio, respostas rápidas) ficou de fora de
propósito - não é um cadastro de canal, é configuração de uso comum.

Diferente da tentativa anterior (que tentou reescrever a estrutura
inteira de uma vez e acabou deixando IDs duplicados pra trás), a
abordagem desta vez foi a mais segura possível: cada card clicável
chama uma função nova (`openWhatsappSettingsModal()`,
`openFacebookSettingsModal()`, `openBeds24SettingsModal()`,
`openOutboundWebhookSettingsModal()`) que monta o EXATO mesmo HTML que
o card tinha antes (mesmos IDs de campo, mesmos `onclick` pras funções
de salvar/conectar/desconectar de sempre) dentro do `genericModal` já
usado em toda a aplicação, e então chama a função de carregamento
correspondente (`loadWhatsappSettings()` etc.) pra preencher os campos
com os dados já salvos. Nenhuma função de salvar/carregar precisou ser
reescrita - só passaram a rodar contra elementos que existem enquanto o
modal está aberto, em vez de sempre.

Isso expôs um bug de ordem em `loadFacebookSettings`/
`loadBeds24Settings`/`loadOutboundWebhookSettings`: as três tinham um
guard no topo (`if(!elX || !elY) return`) que saía ANTES de chegar em
qualquer lógica - como esses elementos agora só existem com o modal
aberto, essa saída antecipada aconteceria sempre que a função rodasse
em segundo plano (ex: no carregamento da sessão), e o texto de status
da caixa resumida (que devia aparecer mesmo com o modal fechado) nunca
seria atualizado. Corrigido movendo a atualização do texto de status
pra ANTES do guard nas três funções (WhatsApp já não tinha esse guard
logo no início, só precisou do texto de status adicionado).

Testado com clique de verdade num navegador (Playwright): as quatro
caixas abrem o modal certo com os campos certos, sem erro de console;
preencher e salvar dados do WhatsApp pelo modal, fechar e reabrir
mostra o valor persistido; o texto de status de cada caixa aparece
correto (inclusive o estado "não conectado"/"ainda não disponível")
assim que a página carrega, sem precisar abrir o modal nenhuma vez.
Balanceamento de chaves/parênteses e cobertura i18n (14 chaves novas,
5 idiomas) sem quebra.

## Hóspede avisado de volta no chat quando a reserva é confirmada/cancelada

Pedido do usuário: "as reservas que vem do messenger vem como
pendentes, quero que quando ela seja confirmada ou cancelada, seja
comunicado de volta ao hospede no chat também, já passando pra ele
horário de check in, endereço, etc". Reserva vinda de um canal de chat
(Messenger, e também WhatsApp) fica com `status='pending'` até a
equipe confirmar manualmente na aba Reservas - até agora, esse
resultado nunca voltava pro hóspede, que ficava sem saber se a reserva
tinha sido aceita ou não a menos que perguntasse de novo.

Novo `notify_guest_reservation_status(hostel_id, reservation_id,
status)` (`database.py`), chamado no fim de
`update_reservation_status_record` - o único ponto por onde uma
mudança de status passa hoje (`PATCH /reservations/<id>`, usado pela
aba Reservas). Só age quando o novo status é `confirmed` ou
`cancelled` (ex: reverter pra `pending` não dispara nada). A chamada
fica dentro de um `try/except` que só imprime o erro - importante
porque o `UPDATE`/commit do status já aconteceu ANTES dessa chamada, e
uma falha de rede ao mandar WhatsApp/Messenger não pode fazer parecer
que a reserva não foi confirmada de verdade.

Resolução do canal de volta: busca a linha mais recente do hóspede em
`guest_channel_identities` (mesma fonte que já alimenta o badge de
canal na aba Chats) - se existir, usa `channel`+`external_id` direto
(o `external_id` do WhatsApp já É o telefone, então não precisa buscar
`guests.phone` separado); se não existir nenhuma linha (hóspede antigo,
de antes da integração multi-canal), cai no fallback de telefone puro
como WhatsApp - mesmo padrão de fallback que `get_guest_channel` já
usa em outros lugares. Reserva sem `guest_id` vinculado (cadastro
manual só com nome, sem telefone/canal) ou sem telefone/PSID
resolvível sai em silêncio - não tem pra onde mandar. Instagram fica de
fora por enquanto (não tem função de envio implementada ainda).

Mensagem de confirmação inclui check-in (com o horário padrão
configurado em Configurações → Empresa, se o hostel tiver preenchido)
check-out e endereço do hostel (idem, se preenchido) - mensagem de
cancelamento é mais simples, sem esses detalhes, convidando a
reagendar ou tirar dúvida por ali mesmo. Texto varia por idioma
(`get_guest_language_by_id`, mesmos pt/en/es/fr/de que o resto da IA
usa), com fallback pt se o idioma do hóspede ainda não foi detectado
ou não é um dos suportados. Mensagem enviada é gravada tanto na
memória da IA (`memory_service.save_message`, role "assistant" - pra
não confundir a IA numa conversa futura) quanto no histórico visível
na aba Chats (`save_message_db_for_guest`, sender "staff" - mesmo
padrão que `send_message_to_guest_now`, o envio manual, já usa pra
distinguir de mensagem gerada pela IA).

Testado (5 cenários): reserva confirmada via Messenger manda a
mensagem certa pro PSID certo, com data de check-in/check-out, horário
e endereço do hostel embutidos, e a mensagem fica gravada na conversa;
reserva cancelada via WhatsApp manda a mensagem de cancelamento pro
telefone certo; reserva sem hóspede vinculado (só nome, sem telefone)
não tenta enviar nada e não quebra; mudar status pra "pending" não
dispara notificação nenhuma; falha simulada no envio (exceção forçada)
não impede o status de ser salvo normalmente. Regressão completa (12
scripts cobrindo Messenger, WhatsApp, Beds24, Financeiro, perfil de
hóspede, canal, reservas canceladas e alertas de nova reserva) sem
quebra.

## Instagram Direct conectado - terceiro canal

Pedido do usuário: "vamos conectar o instagram". Antes de codar,
entrei em modo de planejamento (WhatsApp e Messenger já funcionam
100%, faltava só o Instagram). Investigação de código (agente Explore)
confirmou uma coisa boa: a base de dados já estava pronta desde a
integração do Facebook - colunas `instagram_business_id`/
`instagram_access_token`/`instagram_oauth_state` em `hostels`, e as 6
funções de CRUD/oauth-state em `database.py`, espelhando exatamente o
padrão do Facebook - só nunca tinham sido ligadas a rota nenhuma,
porque na época ficou combinado que Instagram usaria um metodo de
login diferente ("Instagram API with Instagram Login", sem depender de
Página do Facebook) e isso ficou pra rodada seguinte.

**Achado que mudou a suposição inicial**: uma pesquisa dedicada
(agente Plan, com busca na documentação atual da Meta) confirmou que
esse método NÃO é uma variação do fluxo Facebook já implementado - é
uma stack praticamente paralela, com host/credencial/formato
diferentes em quase todo passo:

- **App ID/Secret próprios** (`INSTAGRAM_APP_ID`/`INSTAGRAM_APP_SECRET`,
  variáveis novas) - não dá pra reaproveitar `META_APP_ID`/
  `META_APP_SECRET` que o Facebook já usa.
- **Autorização**: `www.instagram.com/oauth/authorize` com `scope`
  direto na URL (`instagram_business_basic,instagram_business_manage_messages`
  - atenção: a Meta descontinuou os nomes de escopo antigos sem o
  prefixo `instagram_` em 27/01/2025), sem `config_id` (isso é
  específico do Facebook Login for Business).
- **Troca do `code` por token**: **POST** em `api.instagram.com/oauth/access_token`
  (o Facebook usa GET em `graph.facebook.com`).
- **Token de longa duração**: GET em `graph.instagram.com/access_token?grant_type=ig_exchange_token`
  (host ainda diferente do passo anterior - terceiro host na mesma
  sequência).
- **Envio de mensagem**: POST `graph.instagram.com/v20.0/<IG_BUSINESS_ID>/messages`,
  token no **header** `Authorization: Bearer` - diferente do Messenger,
  que manda o token como query param em `/me/messages`.
- **Vantagem real do método**: não exige Página do Facebook vinculada.

Dava pra reaproveitar a FORMA dos arquivos já existentes
(`meta_oauth_service.py`, `messenger_service.py`, `meta_oauth.py`,
`meta_webhook.py`) como molde de organização, mas o conteúdo de cada
chamada HTTP precisou ser escrito do zero, não copiado.

**Implementação** (fases com checkpoint, plano salvo e seguido):

- `services/meta_oauth_service.py`: `get_instagram_authorize_url`/
  `exchange_code_for_instagram_account` (as 3 chamadas certas: code→
  token curto via POST, token curto→longa duração, tentativa best-effort
  de buscar o username - se falhar, segue só com o ID, sem bloquear a
  conexão).
- `routes/meta_oauth.py`: `/oauth/instagram/connect`/`/callback`,
  espelhando exatamente o padrão do Facebook (`_back_to_settings`,
  `save_hostel_instagram_oauth_state`/`consume_...`/`save_hostel_instagram_config`
  já existiam).
- `routes/settings.py`: `GET/POST/DELETE /settings/instagram`, mesmo
  contrato do `/settings/facebook` (form manual como alternativa ao
  OAuth, pra quem já tem as credenciais prontas).
- `services/instagram_service.py` (novo): `send_instagram_message`,
  `get_instagram_user_profile` (best-effort - a documentação da Meta
  não confirma um endpoint de perfil pra esse fluxo especificamente;
  se falhar, devolve `None` e a IA pergunta o nome, igual já faz no
  WhatsApp, sem quebrar nada), `download_instagram_attachment`.
- `routes/meta_webhook.py`: generalizado pra um dicionário de
  adaptadores por canal (`_CHANNEL_ADAPTERS`), evitando duplicar o loop
  inteiro de eventos (texto/imagem/perfil) uma vez por canal - resolve
  o canal do evento pelo campo `object` do payload da Meta (`"page"` →
  Messenger, `"instagram"` → Instagram), com fallback tentando os dois
  lookups de hostel se o campo vier ausente ou inesperado (não
  confirmado com 100% de certeza na doc primária da Meta, só em fontes
  secundárias consistentes - mesma ressalva de sempre, só um teste ao
  vivo confirma).

  **Detalhe de implementação que rendeu um bug real, achado só ao
  rodar os testes**: a primeira versão guardava a referência direta
  das funções de envio/download (`download_messenger_attachment` etc)
  como valor no dicionário `_CHANNEL_ADAPTERS`, criado uma vez no
  carregamento do módulo. Isso captura o OBJETO da função no momento em
  que o dict é montado - um teste que faz `patch("routes.meta_webhook.
  download_messenger_attachment")` depois disso rebate o NOME no
  módulo, mas o dict já guardou o objeto antigo, então o mock nunca era
  chamado (o teste falhava silenciosamente tentando uma requisição de
  rede de verdade). Corrigido envolvendo cada entrada do dict numa
  função-wrapper pequena que chama o nome pelo módulo (mesmo padrão que
  as funções de envio/perfil já usavam sem querer, por acidente de
  escrita) - aí o mock funciona porque a busca do nome acontece em
  tempo de chamada, não em tempo de importação.

- `database.py`: `_dispatch_reservation_status_message` (da notificação
  de reserva confirmada/cancelada, v1.36.0) ganhou um branch pro
  Instagram, e o gate de canais permitidos passou a incluir
  `"instagram"`.
- Frontend: terceiro card clicável em Comunicação (mesmo padrão dos
  outros), modal espelhando o do Facebook (Conectar/manual).
  **Corrigido de brinde, achado nesta rodada**: `handleMetaOAuthReturn`
  sempre mostrava a mensagem de retorno rotulada "Facebook" (chaves
  `settings.facebook.connectSuccess`/`connectFailed` fixas), não
  importava o canal que realmente tinha voltado do OAuth - trocado pra
  chaves genéricas `settings.metaOauth.connectSuccess`/`connectFailed`,
  compartilhadas entre os canais (e prontas pro WhatsApp Embedded
  Signup, quando existir).

Testado: 18 scripts de regressão completa (incluindo os já existentes
de Messenger/WhatsApp/Beds24/Facebook, pra garantir que a
generalização do webhook não quebrou nada que já funcionava), mais 4
cenários novos específicos de Instagram (mensagem de texto roteada
certo pelo `object`, documento recebido/salvo/confirmado no canal
certo, fallback sem `object`, reserva confirmada notificando pelo
Direct com endereço/horário). Teste real de clique em navegador
(Playwright): os três cards de Comunicação (WhatsApp/Facebook/
Instagram) abrem os modais certos, salvar configuração manual do
Instagram funciona e persiste, sem erro de console.

**Bloqueio de negócio, não de código** (mesmo padrão já visto com
Beds24 e Facebook App Review nesta sessão): falta o usuário criar o
produto "Instagram" no App Meta existente, pegar o Instagram App
ID/Secret em "API setup with Instagram login" e conectar uma conta de
teste - até lá, o botão "Conectar Instagram" redireciona com uma
mensagem de erro educada, sem quebrar nada. Pontos que a pesquisa não
conseguiu confirmar com certeza absoluta na documentação oficial da
Meta ficam marcados como "a confirmar no primeiro teste ao vivo":
disponibilidade de nome/username do remetente nesse fluxo específico,
formato exato do payload do webhook, se a assinatura do webhook no
painel é uma seção separada da do Messenger, e exigência de Business
Verification pra esse escopo de permissão.

## Depuração ao vivo do Instagram Direct: quatro causas reais de configuração, uma de cada vez

Usuário tentou conectar a conta real logo depois da fundação da rodada
anterior. Nenhuma delas era bug de código - cada uma só apareceu
testando ao vivo com a Meta de verdade, na mesma linha das descobertas
já registradas nas integrações do Beds24 e do Facebook:

1. **Redirect URI truncada** ao colar no painel da Meta - erro de
   cópia, não bug de código, mas custou uma rodada de diagnóstico até
   ficar claro que a URL cadastrada estava incompleta.
2. **Instagram App Secret truncado** (19-20 caracteres em vez dos 32
   esperados) - também erro de cópia do painel da Meta, causando a
   troca de código falhar sempre com a mesma mensagem
   (`exchange_code_for_instagram_account` devolvendo "A Meta recusou o
   código de autorização do Instagram.").
3. **Faltava adicionar a conta como "Instagram tester" no App Meta** -
   e especificamente com o papel **"Evaluador de Instagram"**, não o
   "Evaluador" genérico (que só aceita identidade resolvível via
   Facebook, sem servir pra uma conta puramente Instagram). Aceito pelo
   lado do Instagram em Configuración → Centro de cuentas → Tu
   información y permisos → Conexiones de apps → "Apps y sitios web" →
   aba "Invitaciones de prueba".
4. **Conta de teste precisou virar pública + profissional** - estava
   privada, o que bloqueava a geração de token mesmo com o convite de
   tester já aceito.
5. **Assinatura do webhook não registrava de verdade via toggle do
   painel** - corrigido chamando `POST
   /{ig_id}/subscribed_apps?subscribed_fields=messages` diretamente via
   API, através de uma rota de diagnóstico temporária criada só pra
   isso (commits `4042298`, `5c576af`, `de4b175`, `6b609fa`, `093bdbd` -
   ver limpeza dessas rotas mais abaixo).

De quebra, o próprio fluxo de "Publicar" do painel da Meta passou a
exigir uma página de política de privacidade publicada **antes mesmo**
de exigir App Review completo - `privacy.html` criado (referenciando
LGPD), servido automaticamente pela rota genérica `/<page_name>.html`
já existente, sem precisar de rota nova (commit `19f69c0`, espelhando
o que já tinha sido adicionado no frontend).

## Bug raiz encontrado e corrigido: mismatch de esquema de ID do Instagram

Depois das cinco causas de configuração acima resolvidas, a conexão
completava mas as mensagens reais nunca chegavam no webhook do jeito
esperado. Investigação encontrou a causa raiz de verdade, mais
profunda que qualquer ajuste de painel: a troca OAuth
(`exchange_code_for_instagram_account`, `services/meta_oauth_service.py`)
devolvia um **"ID com escopo de app"** (ex: `28000058579630962`) no
campo `user_id` da resposta de troca de token - só que o `entry.id`
real que chega no payload do webhook, e o ID que a Send API
(`/{IG_ID}/messages`) espera na URL, usam um **"ID clássico"**
completamente diferente (ex: `17841416924089707`). Confirmado via
pesquisa citando a documentação oficial da Meta ("This ID is [the]
value of the `id` field received in webhook notifications for this
account") e o fórum da comunidade Meta, com múltiplos desenvolvedores
relatando o mesmo sintoma.

Corrigido chamando `GET
https://graph.instagram.com/{INSTAGRAM_API_VERSION}/me?fields=user_id,username`
logo após a troca de token, e usando ESSE `user_id` (o clássico) como
`instagram_business_id` salvo em `hostels`, em vez do `user_id` que já
vinha na resposta da troca de token em si. Enquanto a causa raiz não
estava confirmada, um mapeamento temporário (`4c0f8cb`, "mapeia ID de
teste do dev pro hostel real") serviu de ponte pra continuar testando
o resto do fluxo - removido assim que o fix de verdade
(`a0d04ef`/`a383f48`) entrou, com o mapeamento temporário corrigido
pro ID já correto em `136d297`.

## Instagram manda `message_edit` em vez de `message` entre contas de teste

Descoberta no meio da mesma rodada de depuração: mensagens novas de
verdade, trocadas entre duas contas testadoras do mesmo App em
Development Mode, às vezes chegavam no webhook como um evento
`message_edit` (`{"mid": ..., "num_edit": 0}`) em vez de `message` com
texto - e, pior, sem nenhum campo `sender`, o que quebraria a
resolução normal de quem mandou a mensagem.

Implementado `_fetch_instagram_message_text(mid, access_token)`
(`routes/meta_webhook.py`) como fallback: quando o evento chega assim,
busca o texto (e o remetente) da mensagem por `mid` direto na API, em
vez de depender do payload do webhook trazer tudo pronto. Corrigido em
duas rodadas (`e3462f0` implementou o fallback inicial pro texto;
`f368171` corrigiu o fato de que esse evento também não traz `sender`,
então o remetente também precisa ser buscado pelo `mid`, não só o
texto).

## Decisão de produto: StayFlow não é (e nunca foi) um SaaS de nicho hostel

Por instrução explícita do usuário, `index.html` (hero e CTA final da
landing page) e `privacy.html` foram reescritos pra parar de descrever
a StayFlow como "SaaS para hostels, hotels and pousadas" e passar a
usar linguagem de hospedagens de todo tipo e porte (hospitality
businesses of every kind), com hostel citado só como exemplo, nunca
como definição ou teto do produto. Commits `89286f6` (HostelBot,
espelho do frontend) e `d300d6e` (StayFlow---Site, origem).

Isso não é só um ajuste de texto de marketing - é registrado aqui como
**decisão de produto/filosofia** porque vale pra qualquer descrição
futura da StayFlow (marketing, texto de App Review, documentação
técnica), não só essas duas páginas: hostel é apenas a primeira
categoria de hospedagens atacada, por ser a que o usuário tem acesso
direto agora pra validar a operação de verdade - a ambição real do
produto é ser o maior e mais completo software de hotelaria que
existe, mirando hotéis e resorts de todo porte, não uma ferramenta de
nicho. O texto do pacote de submissão do App Review (ver mais abaixo)
já foi escrito respeitando essa mesma diretriz.

## Limpeza de segurança e atualização de versão de API do Instagram

**Limpeza de rotas de diagnóstico**: as duas rotas temporárias criadas
pra depurar a conexão do Instagram (`/settings/instagram/debug`,
`/settings/instagram/subscribe`) foram criadas e removidas de
`routes/settings.py` várias vezes ao longo dos dois dias de depuração
- reabertas cada vez que surgia mais um teste necessário, e removidas
de novo logo em seguida, antes de dar acesso total a uma conta de
revisor externo (o revisor do App Review da Meta, que precisaria de
permissão de equipe pra acompanhar a configuração). Verificado nesse
processo, como checagem de segurança explícita: **nenhuma rota de
Configurações** (WhatsApp/Facebook/Instagram/Beds24) jamais devolve o
token de acesso bruto pro frontend - todas seguem o mesmo padrão
`"has_access_token": bool(access_token)` já usado desde a primeira
integração (WhatsApp), confirmado revisando as quatro rotas de
`GET /settings/<canal>` uma por uma. Ao final da sessão de depuração
(02-03/08), nenhuma rota de diagnóstico do Instagram permanece no
código - removidas definitivamente no commit `f24fb4a`, depois de a
causa raiz real (ver próxima entrada) já estar confirmada e não
precisar mais delas.

**Atualização de versão de API**: chamadas do Instagram migradas de
v20.0 pra v25.0 em `services/instagram_service.py` (`API_BASE`),
`services/meta_oauth_service.py` (`INSTAGRAM_API_VERSION`) e
`routes/meta_webhook.py` (`_fetch_instagram_message_text`) - commit
`820841f`, suspeita de que a versão antiga (lançada em 05/2024)
pudesse ter comportamento defasado em endpoints mais novos. As
chamadas do Facebook/Messenger/WhatsApp (`API_BASE` de
`meta_oauth_service.py`, ainda v20.0) **não foram tocadas** de
propósito, já que esses canais já funcionam de ponta a ponta.

**Inscrição do webhook não é permanente**: descoberto em 02/08 que a
inscrição feita manualmente dias antes (via a rota de diagnóstico) já
tinha se perdido - precisou ser refeita do zero pela mesma rota
temporária, que devolveu `{"success": true}` da própria Meta de novo
(commit `9810935`, "Reinclui rota temporaria de reinscricao do webhook
do Instagram").

## Causa raiz confirmada: restrição de Standard Access da Meta bloqueia o Instagram

Com todas as causas dependentes de código já corrigidas (mapeamento de
ID, versão de API, inscrição de webhook, fallback de `message_edit`) e
o sintoma ainda persistindo (mensagens reais não apareciam de forma
consistente), foi criada mais uma rota de diagnóstico temporária
(commit `2c4fe0e`) pra chamar o endpoint oficial da **Conversations
API** do Instagram (`GET /{instagram_business_id}/conversations`)
direto, com o token salvo de verdade, sem nenhuma camada do StayFlow
no meio.

**Resultado, com prova técnica definitiva**: a resposta veio `HTTP
200` com `"data": []` - zero conversas retornadas, mesmo com mensagens
reais acontecendo naquela conta no exato mesmo momento (visíveis
direto na caixa de entrada do Instagram/Meta). Isso é prova direta de
que o problema é uma restrição de **"Standard Access"** da própria
Meta (confirmado também por pesquisa: "Standard Access only covers
accounts you own... some features may not work properly until
Advanced Access"), e não um bug de código - só o **App Review**
(Advanced Access) resolve isso de verdade. Todas as causas que
dependiam de código foram testadas e corrigidas ao longo da sessão sem
resolver o sintoma; só uma restrição de plataforma explica o resultado
observado.

Com a causa raiz confirmada, a rota de diagnóstico que a revelou (e as
demais criadas ao longo da depuração) foram removidas em definitivo -
commit `f24fb4a`, fechando a limpeza de segurança mencionada na
entrada anterior.

## Pacote de submissão do App Review preparado (Instagram) - ainda não submetido

Com a causa raiz confirmada como uma restrição de plataforma, o
próximo passo real deixa de ser depuração de código e passa a ser a
submissão formal do App Review da Meta - preparada nesta sessão, mas
**ainda não submetida** (ação do usuário, pendente pra 04/08 em
diante):

- Descrição do caso de uso e justificativas específicas pras duas
  permissões necessárias (`instagram_business_basic`,
  `instagram_business_manage_messages`).
- Passo a passo pro revisor da Meta usando uma **conta de teste
  dedicada** (`review_meta@gmail.com`), criada via convite de equipe
  com permissão total - especificamente pra o revisor nunca precisar
  ter acesso à conta pessoal do usuário.
- Roteiro de vídeo **honesto**: mostra o fluxo equivalente já
  funcionando de ponta a ponta no WhatsApp/Messenger, em vez de fingir
  uma resposta via Instagram que hoje é tecnicamente impossível por
  causa da restrição de Standard Access confirmada acima.
- Texto inteiro escrito respeitando a decisão de posicionamento
  registrada mais acima (nunca descrever a StayFlow como "SaaS de
  hostel").
- Um parágrafo explica que a IA já reúne toda a informação necessária
  pra confirmar uma reserva sozinha, e é tecnicamente capaz disso, mas
  por escolha deliberada de produto
  (`create_reservation_from_chat`, `database.py`, sempre cria a
  reserva com `status='pending'`) a confirmação final fica com a
  equipe humana, como proteção contra overbooking - configurável por
  hospedagem, e não uma limitação técnica da IA.

## Primeira validação de mercado fora do nicho hostel: Diplomatic Hotel (Mendoza)

Marco de negócio, não de código: o usuário conectou com uma pessoa que
trabalha no **Diplomatic Hotel** (Mendoza, Argentina) - um hotel de
grande porte, não um hostel - que quer apresentar a StayFlow pro hotel
como piloto. Reunião direta com quem decide está sendo marcada a
partir de 04/08/2026. Primeira validação concreta de mercado fora do
nicho hostel, reforçando na prática a decisão de posicionamento
registrada mais acima (a StayFlow foi desenhada desde o início pra
hospedagem de qualquer porte, não só pequenos hostels - hostel foi só
o ponto de partida operacional).

## SESSÃO 9 - 04 a 05/08/2026

### Contexto no início da sessão

Sessão longa, com o usuário explicitamente pedindo "máximo de
progresso possível" antes da apresentação ao Diplomatic Hotel. Cobriu
sete frentes distintas, cada uma puxada por um pedido direto do
usuário, várias delas descobertas via auditoria proativa de código em
vez de bug reportado. Todas publicadas em produção e confirmadas no ar
antes de passar pra próxima.

### Auditoria de segurança completa

Pedido direto do usuário: "qual a facilidade pra alguém hackear meu
site? Tenho que proteger o máximo possível" - auditoria de segurança
real (defensiva, sobre o próprio site do usuário, dentro do escopo
permitido).

Achados e correções:

1. **XSS armazenado real** - dados controlados pelo hóspede (nome,
   telefone, prévia de mensagem) e dados derivados da IA (descrição/
   próxima ação de oportunidade) eram inseridos via `.innerHTML` sem
   escape em `assets/js/chats-live.js` (lista de chats, histórico de
   IA) e `assets/js/stayflow-live.js` (Opportunity Center, Ações
   Prioritárias). Qualquer hóspede mandando mensagem por WhatsApp podia
   injetar HTML/JS que executava no navegador da EQUIPE assim que
   alguém abrisse Chats, Opportunity Center ou o próprio Dashboard.
   Corrigido envolvendo todos os pontos identificados com
   `escapeHtml()` (já existente, usado em outros lugares corretamente -
   o problema era só nesses dois arquivos). Confirmado via varredura
   que mensagens de bolha de chat e campos do perfil do hóspede já
   usavam `.textContent` (seguro por natureza), não precisaram de
   mudança.
2. **Sem proteção contra força bruta no login** - a tabela
   `login_attempts` já existia e já era populada (usada só pra exibir
   histórico), mas nunca era LIDA pra bloquear nada. Nova
   `count_recent_failed_logins(email, minutes=15)`; `/login` passou a
   checar ANTES de validar a senha - 5 tentativas erradas pro mesmo
   e-mail nos últimos 15 minutos bloqueia com 429. Casa por e-mail (não
   por IP) de propósito: `login_attempts` já grava o e-mail tentado
   mesmo pra conta inexistente, cobrindo também enumeração de contas.
   Testado localmente: 5 senhas erradas seguidas de a senha CERTA ainda
   devolve 429 (bloqueio vale mesmo acertando depois).
3. **Sem cabeçalhos de segurança nenhum** - confirmado via `curl -sI`
   direto em produção que faltavam `X-Content-Type-Options`,
   `X-Frame-Options`, `Strict-Transport-Security`, `Referrer-Policy`.
   Adicionados via `@app.after_request` em `app.py`.
4. **Senha de cadastro aceitava 1 caractere** - `/register` não tinha o
   mesmo mínimo de 8 caracteres que `/security/change-password` já
   exigia. Alinhado.
5. **Webhooks da Meta sem verificação de assinatura nenhuma** -
   `/webhook/meta` e `/webhook/whatsapp` processavam qualquer POST com
   payload plausível como se fosse legítimo da Meta. Esse item foi
   REPORTADO primeiro (não corrigido de cara) porque não dava pra
   testar contra tráfego real da Meta sem risco de quebrar mensageria
   de hóspede de verdade antes de uma demo comercial - pedido
   explicitamente autorização do usuário antes de mexer ("faça o").
   Novo `utils/webhook_security.py`
   (`verify_meta_signature`, HMAC-SHA256 sobre o corpo CRU da
   requisição via `X-Hub-Signature-256`, comparação em tempo constante,
   falha aberta só quando `META_APP_SECRET` não está configurado -
   fallback de desenvolvimento). Testado localmente contra assinaturas
   sintéticas (válida/inválida/ausente/sem secret configurado, os 4
   cenários corretos), publicado, confirmado que a rota real passou a
   devolver 403 pra requisição sem assinatura (prova que o secret
   realmente está configurado em produção), e por fim confirmado pelo
   usuário mandando uma mensagem real: "sim sim, chegou e a IA
   respondeu normal".

Na sequência, implementado Content-Security-Policy completo (`app.py`,
`_CSP_DIRECTIVES`) - mantendo `unsafe-inline` em `script-src`/
`style-src` deliberadamente: o dashboard inteiro usa `onclick=`/
`onchange=`/`onsubmit=` inline e `<script>` embutido (não é um app com
build step separando JS/HTML) - reescrever isso pra remover
`unsafe-inline` de verdade significaria trocar ~169 `onclick` + 10
`onchange` + 7 `onsubmit` por `addEventListener`, refatoração grande
demais pra fazer de uma vez sem capacidade de teste visual real (sem
ferramenta de automação de navegador neste ambiente). O valor real da
CSP está nas outras diretivas, que fecham vetores sem risco de
regressão - `connect-src 'self'` em particular impede que uma injeção
de XSS (se algum dia acontecer de novo, apesar do fix acima) consiga
exfiltrar dados pra um servidor externo.

**Decisão permanente registrada nesta sessão**: sessão nunca deve
expirar automaticamente por tempo (nem absoluta, nem por inatividade).
Pedido explícito do usuário ao ser perguntado sobre isso: "a coisa de
expiração automática não gosto muito, porque é incômodo você ter que
ficar entrando e saindo toda vez que for usar o site". Revogação
continua existindo normalmente (logout, troca de senha derruba outras
sessões, revogação individual).

### Direito ao esquecimento (exclusão de dados do hóspede) + documentação de hospedagem de dados

Pedido do usuário ao considerar como responder se o Diplomatic Hotel
perguntar sobre proteção de dados durante a venda: "e se eles me
perguntarem sobre proteção de dados". Depois de uma avaliação honesta
do que já podia/não podia ser afirmado, o usuário aprovou dois itens
concretos de uma vez ("pode fazer os 2").

**Exclusão de dados**: novo `erase_guest_data(hostel_id, guest_id)`
(`database.py`) e `POST /guests/<id>/erase-data` - apaga de verdade
documentos (inclusive o arquivo em disco, não só a linha no banco) e
todas as conversas/mensagens do hóspede, anonimiza nome (vira "Hóspede
removido"), telefone, e-mail, data de nascimento, nacionalidade e
documento, e atualiza `guest_name` em reservas e veículos já
existentes pra manter o registro financeiro sem identificar a pessoa
(reserva em si não é apagada, só deixa de apontar pro nome real).
Botão "🗑️ Excluir dados do hóspede" no perfil, com confirmação forte
via `stayflowConfirm()` antes de executar (ação irreversível de
propósito, sem lixeira). Testado localmente de ponta a ponta: hóspede
com documento real em disco + conversa + mensagens + reserva +
veículo - depois da exclusão, documento sumiu do disco de verdade,
conversas/mensagens/identidades de canal foram apagadas, nome virou
"Hóspede removido" com encoding UTF-8 correto (confirmado via
`unicode_escape`, não só aparência no terminal), reserva/veículo
mantidos com o nome anonimizado. Casos de erro (hóspede inexistente,
`hostel_id` errado) devolvem `ValueError` corretamente, sem vazar dado
de outra hospedagem.

**Local de hospedagem dos dados**: usuário confirmou direto no painel
do Render que a região é Oregon (US West) - não dava pra descobrir por
código (sem `render.yaml` no repositório, serviço configurado
manualmente pelo painel). Adicionado à política de privacidade
(`privacy.html`), na mesma seção que já falava da Meta/OpenAI como
transferência internacional, e a seção de direitos do titular passou a
mencionar o botão de autoatendimento pra exclusão.

### Câmbio evolui pra casa de câmbio de verdade

Trabalho em várias rodadas curtas, cada uma puxada por um pedido/
observação direta do usuário testando a funcionalidade:

1. **Cotação atual não se preenchia sozinha** - causa raiz: o seletor
   de "moeda recebida" abria com a primeira moeda da lista selecionada
   por padrão (ARS), e a busca automática de cotação só disparava pra
   USD - então a pessoa precisava trocar manualmente pra USD pra ver
   qualquer coisa. Corrigido colocando USD primeiro na lista
   (`FINANCE_EXCHANGE_CURRENCIES`).
2. **"Você que teria que sincronizar o câmbio de todas as moedas
   cadastradas"** - pedido pra cobrir ARS/CLP/BRL/PEN/BOB/COP, não só
   USD. Novo `get_reference_rate(foreign_currency, home_currency)`
   (`services/exchange_rate_service.py`): quando a moeda da hospedagem
   é ARS, ancora no dólar blue (Bluelytics - a cotação que hospedagens
   argentinas realmente usam no dia a dia, bem diferente da oficial) e
   cruza via USD pra qualquer outra moeda recebida; fora desse caso,
   taxa oficial direta via `open.er-api.com` (gratuita, sem chave).
   Limitação documentada: Bolívia também tem uma distorção real entre
   câmbio oficial e paralelo desde 2023, mas não há fonte pública/
   gratuita equivalente ao Bluelytics pra isso - fica sem resolver,
   documentado. Testado contra as APIs reais (USD→ARS via blue,
   BRL→ARS e CLP→ARS cruzados via blue, USD→BRL e ARS→USD via taxa
   oficial), todos os valores bateram com o esperado. A própria moeda
   da hospedagem saiu da lista de "moeda recebida" (não faz sentido
   cambiar ela por ela mesma).
3. **Caixa de lucro dedicada** - antes o lucro aparecia junto do valor
   creditado numa linha de texto pequena. Virou um espaço próprio
   destacado, valor grande, verde/vermelho conforme o sinal, atualizado
   em tempo real conforme a pessoa digita.

### Correção de posicionamento "hostel" (terceira vez)

Usuário reagiu com bem mais ênfase que das duas vezes anteriores:
"de uma vez por todas entenda, NÃO ESTAMOS MAIS LIDANDO COM UM
HOSTEL" - motivado por eu ter usado "hostel" tanto na conversa quanto
em comentários de código recém-escritos (`database.py`,
`routes/finance.py`, `services/exchange_rate_service.py`,
`dashboard.html`) e, mais grave, em texto VISÍVEL na interface
(`finance.exchange.modalDesc`, "gera lucro pro hostel", nos 5
idiomas). Corrigido em todos os pontos encontrados. Memória de feedback
atualizada com uma regra mais rígida: a exceção de "texto técnico
interno não precisa desse cuidado" NÃO cobre comentários que descrevem
lógica de negócio (só nomes de tabela/coluna/função que seguem a
convenção `hostel_id`/`hostels` por motivo estrutural, e o valor
literal "Hostel" como opção real de tipo de propriedade).

### Revisão de UX mobile em Configurações/Operações/Equipe

Usuário reportou, testando no celular: clicar numa categoria de
Configurações só empurrava o conteúdo pra baixo do menu, em vez de
abrir a categoria escolhida. Causa raiz: `switchSettingsSection()` (e
o equivalente em Operações e Equipe) trocava o conteúdo visível mas
nunca resetava a posição de rolagem - se a pessoa estava rolada pra
baixo na seção anterior, a troca mantinha esse mesmo scroll, dando a
impressão de ter "pulado" pro meio da seção nova. Corrigido nos três
lugares (mesmo padrão que `openPage()` já usava certo). Configurações
no mobile (≤1100px) ganhou também o mesmo padrão de duas telas já
usado nos Chats (lista de categorias OU conteúdo, nunca as duas
empilhadas), com botão "Voltar".

Na mesma leva, consolidado Notificações (push) e Horário de silêncio
numa única caixa/modal - horário de silêncio só existe pra gatear
quando o push deve notificar, não fazia sentido ser configuração
separada ("se já existe uma configuração que faça, não repita" - pedido
direto do usuário). Sininho de alertas (`alert_channels`) movido pra
dentro da mesma caixa. Respostas Rápidas virou caixa clicável + modal,
removendo o último formulário solto que restava na tela de
Comunicação.

**Bug real achado de brinde durante essa investigação**: `saveSettings()`
buscava campos `data-setting` só dentro da seção `#settings` do DOM,
mas o modal genérico (`#genericModal`) é renderizado FORA dela na
árvore (elemento irmão, definido depois de `#settings`/`#team`
fecharem no HTML). Isso significa que o modal "Geral" (nome/tipo da
hospedagem), que reusa `saveSettings()` pro botão Salvar, muito
provavelmente NUNCA salvava esses dois campos de verdade desde que
virou modal - o clique parecia funcionar (fechava o modal, mostrava
"Configurações salvas") mas o valor digitado nunca chegava no banco.
Corrigido ampliando a busca de `#settings` pro `document` inteiro -
seguro, porque cada nome de `data-setting` só aparece uma única vez em
todo o arquivo (conferido antes de aplicar). Confirmado por teste
local: POST simulando exatamente o que o modal manda agora persiste
`hostel_name`/`hostel_type` corretamente.

### Sistema completo de notificações push nativas (Web Push API)

Item que já constava no Roadmap como "deliberadamente adiado". Usuário
pediu pra retomar agora ("agora quero que isso seja exibido... quero
bem completo" foi dito mais tarde, sobre Eventos, mas o espírito valeu
pra essa frente toda). Construído em várias rodadas dentro da mesma
sessão:

**Base**: chaves VAPID via variável de ambiente (nunca no repositório -
recurso fica desligado em silêncio sem elas, mesmo padrão do
`META_APP_SECRET`), gerado par de chaves real com `py_vapid`/
`cryptography`. Service worker (`sw.js`) servido na RAIZ do site
(`/sw.js`, não `/assets/js/sw.js`) pra que o escopo padrão cubra o
site inteiro. Nova tabela `push_subscriptions` (uma linha por
pessoa+dispositivo - PC e celular contam separado). `services/
push_service.py` (`send_push_to_hostel`) manda a notificação de
verdade via `pywebpush`, respeitando horário de silêncio e limpando
sozinho qualquer inscrição que o navegador já invalidou (404/410 real
do serviço de push). Testado repetidamente contra o FCM real do
Google (não simulado) - inscrição fake sempre recebia 404 real e era
limpa do banco, confirmando que o envio realmente saiu pra rede.

**Tipos de evento**, adicionados em rodadas sucessivas conforme o
usuário ia pedindo mais cobertura: nova oportunidade de alta
prioridade e nova reserva pendente (os dois primeiros); depois "quero
que notifique mensagens do chat" (chat_message, único desligado por
padrão - risco de virar ruído); depois "quando o chat detectar
problema, frustração do cliente, ou dúvida, quero que notifique como
urgência" (guest_needs_attention - ajuste no prompt do Decision Engine
pra marcar urgência alta mesmo quando `intent="general"`, que antes só
retornava sem nenhum efeito colateral, sem notificar nada); depois
"notificações para conversas assumidas" (assumed_conversation - dispara
exatamente no ponto em que o código já pulava a resposta da IA por
causa de `ai_paused`, só quando é a conversa individual assumida, não
o interruptor geral do hostel); depois "adiciona pra chamado de
manutenção, manobrista, pedido de cozinha, tudo que faça sentido"
(kitchen_order/maintenance_ticket/security_incident/valet_request -
hook único em `notify_on_duty_staff_for_ticket`, já chamado tanto
pelas rotas HTTP quanto pela criação de chamado feita pela própria IA
via chat, cobrindo os dois caminhos sem duplicar lógica); por fim
new_event, junto com o módulo de Eventos.

**Filtro por permissão**: "quero que isso seja exibido
proporcionalmente a cada função... a limpeza só recebe opção de
ativar notificação de limpeza, manutenção o mesmo, manobrista, etc" -
cada checkbox "o que deve notificar" ganhou `data-required-permission`
e passou a usar o mesmo `applyPermissionVisibility()` já usado no menu
lateral e nas categorias de Configurações, reaproveitado dentro do
modal.

### Autenticação em duas etapas (2FA/TOTP)

Pedido direto do usuário ("faça-o", referindo-se ao 2FA sinalizado
como "Em breve" desde a Sessão 7). `pyotp` (geração/verificação de
código TOTP) e `qrcode` (QR em SVG via `qrcode.image.svg`, sem Pillow,
sem CDN externo - gerado no servidor como data URI). Ativação em
Configurações → Segurança: QR code + chave manual, confirmação com o
primeiro código antes de habilitar de verdade, 8 códigos de backup de
uso único mostrados uma única vez (hash bcrypt do código normalizado -
maiúsculo, sem traço - aceito de volta com ou sem formatação). Login
refatorado: `_complete_login()` isola a lógica de escolha de hostel
que antes vivia só dentro de `/login`; senha certa numa conta com 2FA
ativo agora devolve um `challenge_token` (5 minutos, 5 tentativas) em
vez de completar a sessão - só `POST /login/2fa`, depois do código
TOTP ou um código de backup confirmado, cria a sessão de verdade.

**Bug real de migração encontrado durante o teste local**: banco de
teste recém-criado não tinha as colunas `totp_secret`/`totp_enabled`
mesmo com `add_column_if_not_exists` chamado antes no código. Causa
raiz: `_migrate_users_to_memberships()` (migração antiga, Sessão 7)
reconstrói a tabela `users` inteira com uma lista FIXA de colunas
sempre que detecta o schema antigo - e a detecção (`"hostel_id" in
table_sql`) dispara até em banco novo, porque a própria `CREATE TABLE
IF NOT EXISTS` inicial ainda cita `hostel_id` no texto da definição.
Isso descartava silenciosamente qualquer coluna nova adicionada ANTES
desse ponto do arquivo, em qualquer banco criado do zero - não afetava
produção (já migrada há muito tempo, a condição não dispara mais lá),
mas teria quebrado o próximo deploy realmente novo, e já estava
quebrando os testes locais. Corrigido preservando `totp_secret`/
`totp_enabled` na reconstrução, mesmo padrão já usado pra
`must_change_password`. Testado de ponta a ponta contra um servidor
real: setup + confirmação com código TOTP real, login completo
(código certo completa, errado rejeita), código de backup funciona
normalizado, código de backup reusado falha (uso único), desativar
com senha errada rejeita/senha certa funciona, login volta ao normal
sem pedir 2FA depois de desativado.

### Módulo de Eventos

Usuário perguntou "criamos uma sessão de eventos? o Diplomatic faz
eventos também, importante ter essa parte não?" - discussão rápida de
escopo antes de implementar (Eventos dentro de Operações? Dentro de
Reservas/Receitas? Item próprio?) resolvida com o usuário concordando
em manter item próprio na barra lateral: Operações reúne "chamados"
rápidos resolvidos por quem está de plantão, um conceito diferente de
reserva planejada com peso financeiro próprio; Reservas/Receitas são
sobre hospedagem e upsell pro hóspede já hospedado, não aluguel de
espaço com cliente e calendário próprios.

Construído "bem completo" como pedido: `event_spaces` (salões/jardins/
auditórios, capacidade sentados/em pé, preço), `events` (agenda com
`check_event_space_conflict` - sobreposição de horário no mesmo espaço,
considerando só pendente/confirmado, nunca cancelado - cliente que não
precisa ser hóspede, tipo, status pendente→confirmado→concluído ou
cancelado), `event_addons`/`event_addon_selections` (catálogo de
serviços extras com preço CONGELADO no momento em que são anexados a
um evento - reajustar o catálogo depois não muda retroativamente um
evento já fechado). Nova permissão `events` (décima quinta do
catálogo, aparece automaticamente na tela de Funções sem mudança de
frontend, já que o catálogo é gerado dinamicamente de
`utils/permissions.py`). Receita de eventos confirmados entra no
Financeiro, mesmo critério já usado pra reservas.

**Bug de comparação de data evitado por normalização**: `datetime('now')`/
`CURRENT_TIMESTAMP` do SQLite usam espaço como separador
("2026-08-05 06:38:52"), enquanto `<input type="datetime-local">`
devolve "T" ("2026-08-05T18:00") - comparação textual direta entre os
dois formatos dá errado especificamente em eventos no MESMO DIA
("T" > espaço em ASCII, sempre, independente da hora real). Resolvido
normalizando no Frontend antes de enviar (`eventsToBackendDatetime`,
troca "T" por espaço + adiciona segundos) - testado com evento futuro
aparecendo corretamente em `upcoming_only=1` e evento no passado sendo
corretamente excluído.

### Atualização completa do Documento Mestre e do Diário de Engenharia

Ao final da sessão, usuário pediu explicitamente os dois documentos
"100% atualizados de ponta a ponta, sem falhas" antes de encerrar.
Seguido o protocolo de auditoria integral no Documento Mestre: leitura
completa dos capítulos 9 e 12 a 18 (a maior parte do conteúdo técnico/
específico do documento), mais varredura por palavras-chave
("não implementado", "planejado", "em breve", "adiada" etc.) no
restante do arquivo pra achar qualquer outra menção desatualizada -
achados dois pontos fora dos capítulos originalmente previstos
(catálogo de permissões em 12.3, e notificações push listadas como
"deliberadamente adiadas" na seção 15.7, que o Capítulo 17 já
mencionava mas o 15.7 não tinha sido corrigido junto). Versão do
Documento Mestre avançada de 1.38.0 pra 1.45.0, com sete novas linhas
na tabela de Controle de Versões e um registro narrativo completo no
Capítulo 18 cobrindo a sessão inteira.

### Segunda auditoria, pedida na hora: "por que não fez o que eu pedi exatamente?"

Usuário rejeitou a auditoria acima como insuficiente, direto: pediu
"revisão completa", comparação com o produto atual, diagnóstico do que
falta e um relatório do estado real - a cobertura declarada (capítulos
9 e 12-18 mais varredura por palavra-chave) não é o protocolo formal
de revisão integral que este documento já exige desde a versão 1.3.0
(leitura sequencial de 100% das linhas, sem pular trecho nenhum).
Repetida do zero, com rigor total: leitura sequencial confirmada das
8190 linhas do Documento Mestre e das 5397 linhas deste Diário, mais
verificação cruzada de afirmações técnicas contra o código real
(`utils/permissions.py`, `dashboard.html`, estrutura de pastas do
backend) - passo que nenhuma auditoria anterior deste documento tinha
feito.

**Achados reais que a primeira passada (mais rasa) não pegou:**

1. **Catálogo de permissões estava documentado como 15 chaves, o
   código real já tinha 20.** Faltavam `kitchen`, `maintenance`,
   `patrimonial_security`, `parking` e `scheduling` - adicionadas em
   04/08/2026 (commit `75f37e7`, "Adiciona 5 modulos operacionais
   (cozinha, manutencao, seguranca patrimonial, estacionamento,
   escala) com IA integrada") junto com um módulo operacional inteiro
   que **nunca chegou a ser registrado em nenhum dos dois documentos**,
   apesar de já estar em produção. Cozinha/Manutenção/Segurança
   Patrimonial/Estacionamento até tinham uma menção genérica na seção
   16.14 (sem versão/data atribuída), mas o módulo de **Escala**
   (`routes/scheduling.py` - setores por departamento, grade semanal de
   turnos, consulta de quem está de plantão, pedido/aceite de cobertura
   de turno, aba própria dentro de Equipe) não tinha nenhum registro em
   lugar nenhum.
2. Dentro da própria seção 16.22, duas menções residuais a "14
   permissões" sobreviveram a duas rodadas de correção anteriores
   (12→14→15) sem nunca chegar no número certo, inconsistentes com o
   "15" (agora corrigido pra 20) escrito algumas linhas acima na mesma
   seção.
3. Lista de abas do Frontend (Capítulo 11.3) sem menção à aba Eventos,
   existente desde a v1.45.0 (poucas horas antes desta auditoria).
4. `docs/CHECKLIST_ATIVO.md`, citado em três pontos do Documento Mestre
   e dois pontos deste Diário (inclusive a regra "não iniciar escopo
   novo antes de concluir o que já está no checklist", estabelecida na
   Sessão 3) como arquivo em uso ativo, **confirmado inexistente no
   repositório** - `find` não achou o arquivo em lugar nenhum do
   projeto. Sem registro de quando ou por que foi removido; nenhuma
   sessão documentada aqui registra sua exclusão.

**Corrigido**: as três seções de permissões (12.3, 16.21, 16.22) agora
dizem 20, com a história completa de como chegou nesse número; nova
seção 16.32 documenta o módulo de Escala; 16.14 passou a atribuir
versão/data e "IA integrada" aos quatro módulos que já tinha; 11.3
ganhou "eventos" na lista de abas; as três menções ao
`CHECKLIST_ATIVO.md` como arquivo atual foram substituídas por uma
nota explicando que ele não existe mais (a menção histórica na entrada
da Sessão 3, sobre a criação do arquivo em 09/07/2026, foi mantida
intacta - era verdade no momento em que foi escrita). Versão do
Documento Mestre avançada pra 1.46.0, com uma nova linha na tabela de
Controle de Versões e um segundo registro narrativo no Capítulo 18.

**Resolvido de quebra**: a pendência da Sessão 7 sobre
`HostelBot/StayFlow---Site/docs/` estar fora do controle de versão
desde 23/07/2026 (robocopy `/MIR` sem excluir `docs/`) - os dois
documentos agora são commitados de verdade também no repositório do
backend, não só no do frontend.

**Lição registrada**: uma auditoria "completa" que só lê os capítulos
que parecem mais prováveis de conter mudança recente, sem ler o
documento inteiro nem comparar contra o código, pode passar despercebida
mesmo quando encontra e corrige problemas reais no caminho - o
problema não é o que ela acha, é o que ela erroneamente declara não
existir. O protocolo formal (leitura sequencial de 100%, sem atalho)
já estava registrado desde a versão 1.3.0 exatamente por causa de um
episódio parecido; não seguir esse protocolo de novo, mesmo sem má
intenção, repete o mesmo erro que ele foi criado pra evitar.

## SESSÃO 10 - 13/08/2026

### Contexto no início da sessão

Sessão de documentação pura, pedida explicitamente pelo usuário depois
de uma rodada real de desenvolvimento que aconteceu entre a v1.46.0 e
agora, sem que nenhum dos dois documentos tivesse sido atualizado no
processo. Nove funcionalidades novas já em produção (confirmadas pelo
histórico de commits do repositório `HostelBot`, HEAD em `88d7f45`)
mais uma contradição real encontrada no próprio Documento Mestre sobre
o estado do Billing. O pedido foi explícito: os dois documentos
"100% atualizados agora", editando de verdade (não só relatando o que
falta). Antes de escrever qualquer coisa, cada um dos nove itens foi
verificado direto no código-fonte (`routes/*.py`, `database.py`,
`services/*.py`, `dashboard.html`, `Register.html`, `planos.html`) -
nomes de rota, tabela e função só entraram nos documentos depois de
confirmados, não presumidos a partir do resumo do commit.

### StayFlow Hub: painel interno da StayFlow + impersonation

Até aqui o acesso interno da própria StayFlow (não do cliente) só
existia como proteção de endpoint, sem nenhuma tela. Dois commits
seguidos mudaram isso: primeiro uma visão geral de todas as hospedagens
e agências clientes com receita/comissão (`GET
/stayflow-admin/overview`, `admin.html`/`admin-list.html`/
`admin-hostel.html`), depois o Hub propriamente dito com a capacidade
de entrar direto no dashboard de qualquer conta cliente
(`stayflow-hub.html`).

Dois números são mostrados separados de propósito: MRR estimado (a
partir de `PLAN_PRICES`, só uma estimativa de tabela - a cobrança real
da assinatura StayFlow ainda não está automatizada, ver mais abaixo) e
comissão de fato coletada via Mercado Pago Split (soma real sobre
`guest_charges`). Misturar os dois teria dado a impressão de receita
que não existe de verdade.

A autorização não usa uma role "superadmin" no banco - é allowlist de
e-mail (`STAYFLOW_ADMIN_EMAILS`, checada por
`utils.tenant.is_stayflow_admin_email`), a mesma filosofia de "recurso
desligado em silêncio sem a variável de ambiente" já usada pra
`META_APP_SECRET` e as chaves VAPID. A impersonation em si
(`POST /stayflow-admin/impersonate`) não cria vínculo nenhum em
`hostel_memberships` - só reaponta `sessions.hostel_id` pra conta
visitada, guardando o hostel de origem em
`sessions.impersonating_from_hostel_id` (coluna nova) pra saber voltar
depois (`POST /stayflow-admin/stop-impersonating`). Cada visita fica
registrada em `impersonation_log` (início/fim), embora ainda não exista
nenhuma tela que leia esse histórico - fica registrado como limitação
conhecida, não como faltando. `utils/tenant.py` documenta no próprio
código essa liberação de acesso como uma exceção deliberada à regra de
ouro de que `hostel_id` nunca deveria vir de fora da sessão - segunda
exceção desse tipo no sistema.

### Contas de agência parceira (Portfólio/Parceiros) e IA agency-aware

Item que já constava no roadmap informal do usuário ("Portfólio/
Parceiros") ganhou schema e comportamento reais. `hostels` passou a
carregar `account_kind` (`lodging` ou `agency`) e `agency_category`
(turismo, aluguel de carro, bike ou equipamento) - reaproveitando a
mesma linha, sem criar uma entidade de agência separada. Uma agência
cadastra seu catálogo em `portfolio_items`; qualquer hospedagem pode
optar por vender um item desse catálogo via `partner_offers`
(`UNIQUE(hostel_id, portfolio_item_id)`); quando isso acontece e o
hóspede paga pela agência via Mercado Pago Split, a comissão devida à
hospedagem que indicou fica registrada em `partner_referral_ledger`
(`guest_charges` ganhou `referring_hostel_id` e
`referring_hostel_commission_pct`) - pago "por fora" hoje, sem
processador de payout automático, e conferível pelo StayFlow Hub
(`GET /stayflow-admin/partner-ledger`).

O lado de IA foi construído num ramo separado de propósito, pra não
arriscar o fluxo de reserva de hospedagem que já funciona: `ask_ai`
(`services/ai_service.py`) e `analyze_message`/`analyze_with_ai`
(`services/decision_engine.py`) passaram a receber `account_kind`, e
quando é `agency` usam um prompt de sistema e um conjunto de
ferramentas próprios (`AGENCY_SYSTEM_PROMPT`/`AGENCY_TOOLS`, com
`get_offerings` consultando o portfólio) - sem tentar reservar quarto
ou fazer check-in, conceito que simplesmente não existe pra esse tipo
de conta. O Dashboard também esconde Estoque/Operações/Eventos/KPIs de
hospedagem quando a conta é agência, e troca "hóspede" por "PAX" nesse
contexto.

### Opportunity Center sugerindo item de parceiro

Consequência direta do item anterior: quando o Decision Engine
identifica intent `tour` numa conversa e a própria hospedagem não
vende esse tipo de experiência, mas existe algum item habilitado em
`partner_offers`, a oportunidade criada grava
`suggested_partner_item_id` apontando pro primeiro item disponível.
Deliberadamente simples por enquanto - não há matching semântico entre
o que o hóspede pediu e o item sugerido, só a checagem de que existe
algo disponível pro intent `tour`. Registrado como dívida técnica
conhecida, não como bug. No Frontend, `stayflow-live.js` mostra a
sugestão com botão "Oferecer parceiro", que abre o mesmo modal de
cobrança já usado pra qualquer cobrança via Mercado Pago Split, só que
pré-preenchido - nenhuma lógica de cobrança nova foi criada pra isso.

### Cadastro self-serve com página pública de planos

A Fase 1 do Billing (tabela `billing`, planos, trial de 30 dias, comp
accounts) já estava em produção fazia tempo, mas só era ativável pelo
StayFlow Hub, manualmente, por um administrador. Isso mudou: `planos.html`
é a página pública nova (3 planos reais - Starter US$89, Business
US$349, Enterprise US$699+ negociado, valores em `PLAN_PRICES`), com
cada botão linkando pra `Register.html?plan=starter` (ou `business`/
`enterprise`). `Register.html` lê esse parâmetro da URL, mostra o plano
escolhido antes de completar o cadastro, e manda `plan_name` no corpo
de `POST /register`.

Verificado direto no código pra não registrar isso errado: `/register`
chama `set_billing_plan(hostel_id, plan_name)` quando o plano não é
Starter, mas quem realmente cria a linha de trial de 30 dias é
`get_billing_info` (chamada internamente por `set_billing_plan` antes
de fazer o UPDATE) - função que já existia desde a Fase 1 e cria
`status='trialing'` com `trial_ends_at` 30 dias à frente pra qualquer
hostel novo, plano Starter por padrão. Ou seja: o trial automático
nunca foi novo nesta sessão, o que é novo é (a) a página pública de
preços e (b) `/register` aceitar o plano escolhido e ativá-lo sozinho,
sem passar pelo Hub. Essa descoberta foi o gatilho direto pra revisar a
seção de Billing do Documento Mestre (ver fechamento desta sessão mais
abaixo).

### Importador de dados via CSV

Construído em cinco commits incrementais, um tipo de dado por vez:
Quartos, Hóspedes, Reservas, Equipe e Portfólio. Fica em Configurações,
com modelo de CSV pronto pra baixar por tipo. O parsing é feito
inteiramente no Frontend, com um parser próprio em JavaScript
(`parseImportCSV`, sem biblioteca externa - mesma filosofia de não
depender de CDN externo já usada no resto do projeto) que já lida com
campo entre aspas com vírgula interna; o backend só recebe
`{"rows": [...]}` já estruturado (`POST /rooms/import`,
`/guests/import`, `/reservations/import`, `/team/import`,
`/portfolio/items/import`).

Alguns detalhes valem registro porque não são óbvios: importar
reservas usa `source="import"` e `notify=False` - de propósito, pra
não tentar sincronizar cada linha importada com o Beds24 nem disparar
o webhook de saída durante uma carga em massa (o que faria sentido pra
uma reserva nova de verdade, não pra migração de dados históricos).
Importar equipe cria a função (role) citada na planilha com zero
permissões se ela ainda não existir, em vez de rejeitar a linha -
começa fechada, o administrador libera depois. Os dois já respeitam os
limites do plano contratado (`check_room_limit`/`check_seat_limit`),
então uma importação grande não contorna o teto do Billing.

### Tour de introdução (onboarding)

Slide explicando os blocos do Dashboard no primeiro acesso de cada
pessoa, mais uma dica curta por item de menu na primeira vez que é
clicado. Implementação própria, sem biblioteca de tour externa
(intro.js, shepherd.js) - mesmo padrão de não depender de dependência
de terceiro pra algo que dá pra construir direto. A decisão mais
relevante foi onde guardar a preferência: em banco (`users
.onboarding_dismissed` pra desligar tudo, `user_feature_intros` -
`UNIQUE(user_id, feature_key)` - pra cada item já visto), não em
`localStorage`, porque a mesma pessoa loga em mais de um dispositivo
(o sistema de identidade única de pessoa da Sessão 5 já cobre isso) e
o tour reaparecendo num celular novo depois de já ter sido dispensado
no PC seria uma regressão de experiência.

De brinde nesse mesmo commit, corrigida uma armadilha real de migração:
`_migrate_users_to_memberships` reconstrói a tabela `users` com uma
lista fixa de colunas sempre que roda num banco novo, e
`onboarding_dismissed` estava sendo descartado silenciosamente por não
constar nessa lista - mesma classe de bug já corrigida antes pra
`totp_secret`/`totp_enabled` (Sessão 9) e `must_change_password`.
Corrigido preservando a coluna, com comentário no código pra não
repetir com a próxima coluna nova em `users`.

### Botões de chamado manual + aba "Tarefas" em Operações

As rotas de Cozinha, Manutenção e Segurança Patrimonial (`POST
/kitchen/orders`, `/maintenance/tickets`,
`/patrimonial-security/incidents`) já existiam desde 04/08/2026 e já
notificavam quem está de plantão via `notify_on_duty_staff_for_ticket`
- só que sem nenhum botão no Dashboard ligado a elas. A equipe só
conseguia abrir um chamado indiretamente, pedindo pra IA pelo Ask
StayFlow ou esperando um hóspede reportar. Corrigido só no Frontend,
sem tocar em nenhuma rota: cada aba ganhou seu botão de abrir chamado
manual. Estacionamento, que já tinha um conceito ligeiramente diferente
(chamado sempre associado a um veículo específico), ganhou um botão
dedicado que abre um seletor de veículo antes de reusar a mesma rota
`POST /parking/vehicles/<id>/valet-request`.

A aba "Tarefas" resolve um problema diferente: chamado que não se
encaixa em nenhuma das quatro categorias fixas (o exemplo usado no
próprio código é "trocar lâmpada do corredor"). Em vez de criar uma
tabela nova, `POST /operations/tasks` reaproveita `tickets` com
`type='task'` - decisão consciente de não duplicar o sistema de
urgência/fila que os outros quatro tipos já usam. A diferença real é
que tarefa avulsa não tem setor de plantão fixo, então não dispara
notificação automática nenhuma; conclui com `POST
/operations/tasks/<id>/resolve` e aparece com botão "concluir" próprio
na mesma lista de alertas que já mostrava limpeza pendente (que resolve
sozinha, ao marcar a cama como limpa, sem esse botão).

### Ask StayFlow ganha visão de imagem

`POST /ask` passou a aceitar `multipart/form-data` com um arquivo
opcional, além do JSON puro que já existia. Restrito a
`image/jpeg`/`image/png`/`image/webp` - decisão explícita registrada no
próprio código: é o formato que a câmera do celular gera na hora, e é
o único que o modelo consegue realmente "ver" via `image_url` (PDF
ficou de fora). A imagem vira data URI em base64 e é passada pra
`ask_agent(..., image_data_url=...)`
(`services/ask_agent_service.py`) - vale registrar que esse módulo
específico usa o modelo `gpt-4.1-mini` da OpenAI, não Claude/Anthropic
(diferente da suposição inicial de investigação desta sessão, corrigida
depois de ler o código de verdade).

A partir da foto, a IA decide sozinha o que fazer: reposição de
estoque, pedido de cozinha (`_create_kitchen_order_by_name`), chamado
de manutenção (`_create_maintenance_ticket`) ou incidente de segurança
(`_create_security_incident`) - as três novas ferramentas terminam
chamando `notify_on_duty_staff_for_ticket`, o mesmo mecanismo dos
botões manuais descritos acima, sem duplicar lógica de notificação.
Diferente do fluxo de reposição a fornecedor (que sempre pede
confirmação explícita antes de mandar algo pra fora do sistema), esses
três não exigem aprovação prévia - mas o prompt de sistema instrui a IA
a perguntar em vez de adivinhar quando a foto for ambígua ou faltar
informação essencial, e isso foi confirmado na descrição do próprio
commit como testado na prática.

### Correção da contradição de Billing no Documento Mestre

Ao revisar o Capítulo 17 pra registrar o cadastro self-serve, ficou
claro que a seção 17.2 estava desatualizada de um jeito que não era só
"faltando uma linha nova" - ela descrevia Billing como "modelo de
cobrança em definição, sem processador nem plano ativo", o que
contradizia diretamente a Fase 1 (planos/trial/comp accounts) que já
estava em produção há mais tempo do que essa frase sugeria, e agora
contradizia ainda mais com o cadastro self-serve recém-registrado.
Reescrito com cuidado pra não trocar um exagero por outro: Billing Fase
1 está de fato em produção (planos reais, trial automático de 30 dias,
página pública, ativação sem aprovação manual), mas a cobrança
recorrente automática da PRÓPRIA assinatura StayFlow (cobrar o cliente
StayFlow depois que o trial acaba, Fase 2-3 com Stripe/Mercado Pago)
continua sendo só schema stub, sem processador ligado - hoje é
100% manual/honra, sem trava de bloqueio por inadimplência. Repetido
explicitamente no texto pra não confundir: isso não tem nada a ver com
o Mercado Pago Split guest-facing (cobrança do hóspede pelo hostel),
que já é real e está em produção desde bem antes desta sessão.

### Atualização do Documento Mestre e do Diário de Engenharia

Os nove itens acima, mais a correção de Billing, foram escritos nos
capítulos correspondentes do Documento Mestre: 11.3 (lista de
arquivos - `planos.html`, `Register.html`, `admin.html`/
`admin-list.html`/`admin-hostel.html`/`stayflow-hub.html`, aba Tarefas
e Portfólio/Parceiros na descrição do `dashboard.html`), 12.3 (schema -
`portfolio_items`/`partner_offers`/`partner_referral_ledger`,
`impersonation_log`, `user_feature_intros`, colunas novas em
`hostels`/`sessions`/`opportunities`/`guest_charges`/`users`, e
correção da descrição de `billing`), 14.3 (Decision Engine
agency-aware), 15.4 (módulo Portfólio/Parceiros na lista do Dashboard),
16.4 (Opportunity Center sugerindo parceiro), 16.14 (botões de chamado
manual + aba Tarefas), 16.27 (Ask StayFlow com visão de imagem) e uma
seção nova, 16.33 ("StayFlow Hub, Importador de Dados (CSV) e Tour de
Onboarding"), pra agrupar os três itens sem capítulo óbvio de destino.
Versão do Documento Mestre avançada de 1.46.0 pra 1.47.0, com uma nova
linha na tabela de Controle de Versões, e corrigido de brinde um
resíduo real esquecido em revisões anteriores: a última linha do
arquivo ainda dizia "Fim da Versão Oficial 1.6.0", desatualizada desde
muito antes desta sessão.

Mirror do backend (`HostelBot/StayFlow---Site/docs/`) sincronizado com
as mesmas duas versões finais, mantendo a prática estabelecida desde a
Sessão 9 de versionar os documentos também no repositório do backend.

## SESSÃO 11 - 20/08/2026

### Suporte real a fotos no chat

Antes desta sessão, qualquer imagem recebida de um hóspede pelo
WhatsApp/Instagram/Messenger era arquivada automaticamente como "foto
de documento de identidade", mesmo quando não tinha nada a ver com
isso, e a IA nunca via a imagem de verdade — só sabia que "um arquivo
chegou". Implementado suporte de verdade: `messages.media_path`/
`media_mime_type`/`media_token` (colunas novas) guardam a mídia real;
os webhooks (`routes/whatsapp_webhook.py`, `routes/meta_webhook.py`)
passam a encaminhar a foto pelo pipeline normal de atendimento
(`process_incoming_message`, agora aceitando `media_bytes`/
`media_mime_type`) em vez do fluxo antigo "sempre é documento";
`ask_ai()` (`services/ai_service.py`) ganhou um parâmetro
`image_data_url` que monta o conteúdo multimodal (`image_url`) quando
existe foto, então a IA reage de verdade ao que está na imagem.
Equipe também pode mandar foto pro hóspede (`POST
/guests/<id>/send-photo` e o equivalente em "Meu chat",
`routes/guests.py`/`routes/stayflow_admin.py`), despachada pelo canal
real do hóspede via `send_whatsapp_image`/`send_messenger_image`/
`send_instagram_image` (`services/*_service.py`) — corrigido de brinde
um bug real encontrado no processo: `send_message_to_guest_now` só
mandava mensagem por WhatsApp antes, não importava qual fosse o canal
de origem do hóspede. Nova rota pública `GET /media/chat/<token>`
(`app.py`, token de 16 caracteres hex validado por regex, sem sessão)
existe porque as próprias APIs da Meta baixam a imagem que a StayFlow
manda de volta, e não têm como autenticar com cookie de sessão.
Testado com três scripts próprios contra banco SQLite temporário antes
de sincronizar pros três locais de código (`StayFlow---Site`,
`HostelBot` raiz, `HostelBot/StayFlow---Site`) e publicar. Documentado
no Documento Mestre, seção 16.2.

### Nova regra: documentar ao terminar, não quando lembrado

No meio da sessão, ao planejar a feature de Prospecção (abaixo), o
assistente presumiu — sem checar — que a feature de StayFlow Hub/
impersonation (Sessão 10) ainda não estava documentada, e chegou a
escrever isso num plano. O usuário corrigiu na hora: "confere direito
no código, já arrumamos isso" — checado de novo, a Sessão 10 já tinha
documentado tudo (Documento Mestre 16.33, Diário acima). O erro real
não foi a mensagem errada em si, foi o hábito: documentação vinha
sendo tratada como passo à parte, pedido depois, em vez de parte do
fechamento de cada tarefa — o que já tinha acontecido de verdade uma
vez antes (a rodada inteira de nove funcionalidades da Sessão 10, só
documentada quando cobrada). Regra registrada de forma permanente
(memória do assistente, `feedback_update_docs_after_task`): toda
tarefa de código só conta como terminada depois do Documento Mestre e
deste Diário atualizados, não como um pedido separado.

### Nova aba "Prospecção" no painel interno

Contexto: o usuário está começando a prospectar hospedagens piloto
para a StayFlow, por duas vias — abordagem presencial (sem hora
marcada, começando pelo hostel Dale) e abordagem digital (WhatsApp,
e-mail, Instagram), reaproveitando contatos de quando trabalhava com
pacotes de viagem numa agência em Bariloche, enquanto aguarda resposta
do Diplomatic Hotel (já em prospecção havia mais tempo, ver v1.40.0).
Para organizar isso, uma planilha (Google Sheets) foi montada fora do
sistema com as colunas Nome, Hospedagem, Prioridade, Canal, Status,
Último contato, Próxima ação, Data da próxima ação e Observações. O
usuário pediu pra essa lista morar dentro do próprio painel interno da
StayFlow em vez de numa aba de navegador separada.

Implementado reaproveitando ponta a ponta o padrão já existente da aba
Despesas (`admin.html` + `routes/stayflow_admin.py` + `database.py`),
por ser estruturalmente idêntico ao que se precisava: tabela não-tenant
(sem `hostel_id`, dado da própria StayFlow), form inline de criar/
editar, filtro por status, badge de pendência no menu. Tabela nova
`stayflow_leads`, CRUD completo (`create_stayflow_lead`,
`list_stayflow_leads` com filtro opcional por status/prioridade,
`get_stayflow_lead`, `update_stayflow_lead` por allowlist dinâmica de
campos, `delete_stayflow_lead`), rotas `GET/POST /stayflow-admin/leads`
e `PATCH/DELETE /stayflow-admin/leads/<id>` protegidas por
`@require_stayflow_admin`. Diferente do resto do painel, o conteúdo da
aba (formulário, cabeçalhos de tabela) ficou só em português, sem
`data-i18n` completo — é ferramenta de uso exclusivo do usuário, não
faz sentido i18n aqui; só o item de menu e o título/subtítulo do
topbar ganharam chave de tradução nos 5 idiomas, pro mecanismo de
troca de aba não quebrar. Testado com dois scripts próprios: um contra
o banco direto (create/list/get/update/delete/filtros/ordenação por
data de próxima ação), outro contra as rotas Flask de verdade (cliente
de teste com autenticação simulada, cobrindo os casos de validação —
nome vazio, prioridade/status inválidos — e o caso de sessão ausente,
401). Documentado no Documento Mestre, seção 16.34, e na tabela de
Controle de Versões (v1.48.0 fotos no chat, v1.49.0 Prospecção).

Mirror do backend (`HostelBot/StayFlow---Site/docs/`) sincronizado com
as mesmas versões finais, mesma prática das sessões anteriores.

### Contexto de IA separado por categoria de negócio (não mais rótulo trocado)

Ainda na mesma sessão, o usuário — animado com a resposta que teve de
conhecidos interessados em pilotar a StayFlow (mãe e amigos numa
imobiliária, um amigo com estética automotiva, outro com película
automotiva, outro com estamparia e loja online no Mercado Livre) —
pediu pra generalizar de vez o suporte a "lojas e prestadores de
serviço, com catálogo e tudo". Antes de qualquer código, ele apontou
um problema real na arquitetura: `account_kind = "agency"` já existe
desde a rodada anterior (turismo, aluguel de carro/bike/equipamento),
mas TODAS essas categorias compartilhavam o mesmo
`AGENCY_SYSTEM_PROMPT`, só trocando um rótulo (`agency_category_label`)
dentro do texto — não era um contexto de verdade separado por tipo de
negócio, era um prompt genérico com um substantivo diferente. Frase
literal do usuário: "cada um deve ter o seu próprio contexto,
separadamente".

Decisão de arquitetura (registrada em plano antes de codar): não criar
um `account_kind` novo por vertical — isso quebraria a premissa de
duas categorias exatas que `applyAccountKindVisibility`/
`hideNavItemsWithoutPermission` (`dashboard.html`) assumem hoje
(comparação `===` estrita contra uma única string). `account_kind =
"agency"` já significa estruturalmente "negócio com catálogo, sem
quartos/reservas", o que já serve bem pra imobiliária/estética
automotiva/etc. O que mudou foi `agency_category` deixar de ser só um
rótulo cosmético e passar a selecionar um prompt de sistema INTEIRO e
separado.

Implementado (primeira passada, corrigida logo abaixo):
`database.AGENCY_CATEGORIES` ampliada de 4 pra 10 valores (as 4
antigas + `imobiliaria`, `estetica_automotiva`, `pelicula_automotiva`,
`estamparia`, `loja_online`, `servico_generico` como catch-all/fallback).
Em `services/ai_service.py`, o
`AGENCY_SYSTEM_PROMPT` único virou `AGENCY_CATEGORY_PROMPTS` — uma
função `_build_agency_prompt` monta um prompt completo por categoria a
partir de um esqueleto comum (`_AGENCY_PROMPT_SKELETON`), preenchendo
a descrição do negócio, as perguntas específicas ("Informação que você
está reunindo"), o substantivo usado pra falar do catálogo, e a frase
de handoff pro time — mas a espinha dorsal que garante o produto
(nunca inventar preço/item, sempre checar `get_offerings`, nunca
fechar venda sozinho) é deliberadamente idêntica em todas, por serem
garantias do produto, não "sabor" de nicho. `services/decision_engine.py`
ganhou o mesmo tratamento pro `business_context` usado na análise de
oportunidade (`_AGENCY_CATEGORY_BUSINESS_CONTEXT`). `routes/chat.py`
passou a extrair `agency_category` mais cedo (antes só existia perto
do `ask_ai`) pra alimentar também o `analyze_message`.

No meio da implementação, o usuário adicionou mais um requisito real:
"eles também devem ter integração com PMS do local caso já tenham
sistema" — o mesmo webhook de saída que hospedagem já tem
(`dispatch_reservation_webhook`, v1.27.0) devia existir pras contas
`agency` novas. Como esse tipo de conta não tem reserva/check-in,
investigado o pipeline de oportunidades (`analyze_message`,
`services/decision_engine.py`) pra achar o evento equivalente: o
momento em que uma oportunidade é criada (ou atualizada, se a mesma
conversa evolui) É o evento de conversão real desse tipo de negócio.
Criado `dispatch_opportunity_webhook` (`database.py`, mesmo formato de
`dispatch_reservation_webhook` — nunca levanta exceção, busca
hóspede/oportunidade e manda `POST` assinado), chamado direto de
`analyze_message` logo após o commit, só quando `account_kind ==
"agency"` (hospedagem continua só na reserva, sem duplicar sinal).
Texto do modal de Configurações → Integrações (`settings.outboundWebhook.intro`)
passou a variar por `account_kind` nos 5 idiomas, pra não falar de
"reserva" com quem não tem esse conceito.

Também corrigido de brinde, no mesmo pacote: `Register.html` (as
categorias no seletor, copy do tipo de conta deixou de dizer só
"Agência parceira"), e o relabel "Hóspedes" → "PAX"/"Clientes" em
`dashboard.html` (3 pontos no código) — antes qualquer conta `agency`
virava "PAX", termo que não faz sentido pra estética automotiva ou
estamparia; agora só turismo/aluguel mantêm "PAX" (termo do setor),
as categorias novas usam "Clientes". Precisou adicionar
`agency_category` na resposta de sessão (`routes/auth.py`
`build_session_payload`), que antes só expunha `account_kind`.

Antes de testar, o usuário revisou a lista de 10 categorias e apontou
uma inconsistência de modelagem: "estética automotiva e películas
podem estar juntos... assim como hospedagem que tem as categorias
hostel, pousada etc, a parte automotiva pode ter suas categorias como
estética, películas, mecânica, funilaria e pintura, elétrica,
borracharia, auto peças, etc, assim como o comércio também deve ter
suas categorias que são muitas". Ou seja: `estetica_automotiva`/
`pelicula_automotiva`/`estamparia`/`loja_online` como 4 categorias
"top-level" separadas era o MESMO erro de modelagem que a sessão tinha
acabado de corrigir num nível diferente — só que ao contrário: turismo/
locação eram genéricas demais compartilhando um prompt, e automotivo/
comércio ficariam granulares demais como 4 categorias fixas quando a
variedade real (mecânica, funilaria e pintura, elétrica, borracharia,
auto peças, e "muitas" no comércio) é grande demais pra virar prompt
próprio por subtipo. Correção: as 4 viraram 2 GRUPOS
(`automotivo`/`comercio`), com o detalhe específico guardado numa
coluna nova, `hostels.agency_subcategory` — campo livre com presets,
mesmo padrão exato que `hostel_type` já usa pra hospedagem (hostel/
pousada/hotel/resort/flat + "+ Novo tipo..."). O prompt de IA
(`AGENCY_CATEGORY_PROMPTS["automotivo"]`/`["comercio"]`) interpola a
subcategoria dinamicamente via `{agency_subcategory_line}` ("...an
automotive shop specializing in Funilaria e pintura." — ou frase limpa,
sem esse trecho, quando a conta não preencheu subcategoria nenhuma).
`Register.html` ganhou um terceiro seletor em cascata, só visível pra
automotivo/comércio, com os presets de `database.AGENCY_SUBCATEGORY_PRESETS`
e a mesma opção "+ Outro (digite abaixo)". `database.AGENCY_CATEGORIES`
final: 8 grupos, não 10 categorias.

Testado com quatro scripts próprios contra banco SQLite temporário: os
8 prompts formatam sem erro e são todos distintos entre si (nenhum
texto duplicado); a interpolação de subcategoria funciona com e sem
valor (frase limpa, sem "specializing in" pendurado, quando vazia) e é
ignorada sem erro pelas categorias que não usam esse placeholder; o
fallback pra categoria desconhecida cai em `servico_generico`; o
`business_context` do Decision Engine tem uma frase própria por grupo
com o mesmo fallback; e o webhook de oportunidade — testado via
`analyze_message` de ponta a ponta, com `analyze_with_ai` mockado pra
não bater na OpenAI de verdade — dispara `opportunity_created` na
primeira mensagem, `opportunity_updated` numa segunda mensagem da
mesma conversa, e confirmadamente NÃO dispara pra conta `lodging` (que
segue exclusiva no webhook de reserva). Documentado no Documento
Mestre, seção 14.3 (contexto por categoria/grupo) e seção 16.25
(webhook de oportunidade), mais a tabela de Controle de Versões
(v1.50.0).

Ainda no mesmo pacote, o usuário revisou os presets de "automotivo" e
apontou que "auto peças" sozinho ficou vago demais: "em autopeças deve
haver uma subcategoria mais depois de criado que é carro/moto/
caminhao/maquinas". Em vez de adicionar um quarto nível de cascata na
UI só pra esse caso, o preset único "Auto peças" foi desdobrado
diretamente em 4 presets mais específicos na mesma lista plana
(`database.AGENCY_SUBCATEGORY_PRESETS["automotivo"]`): "Peças de
carro", "Peças de moto", "Peças de caminhão", "Peças de máquinas" —
como `agency_subcategory` já é texto livre (não um enum fechado), isso
captura a mesma informação que um terceiro nível de seletor daria, sem
precisar construir mais uma camada de cascata JS pra um único caso.

Mirror do backend sincronizado com as mesmas versões finais.

### Marcar contas candidatas a treinamento pago na Prospecção

Ainda na mesma sessão, a conversa virou estratégia comercial, em três
partes: (1) quanto tempo oferecer de piloto — decidido 30-45 dias
padrão, 60-90 pra imobiliária, sempre com checkpoint marcado, não um
ano fixo, pra não sufocar o caixa nem perder urgência; (2) o usuário
esclareceu que o piloto não é totalmente de graça — StayFlow ganha
comissão por venda de upgrade e a comissão real do split do Mercado
Pago já durante o piloto, sem mensalidade fixa nesse período. Isso
muda a conta de risco de caixa do item (1): comissão que já entra
proporcional ao uso reduz a pressão de prazo pra converter, MAS só
funciona de verdade nas verticais onde o pagamento passa pela
plataforma (hospedagem, e dá pra estender pra estética automotiva/
película/estamparia) — pra imobiliária o negócio comum fecha fora do
chat (contrato tradicional), então a comissão pode nunca aparecer, e
o checkpoint continua sendo o critério prático: "a comissão já paga a
conta desse piloto?" decide se estica, cobra mensalidade, ou os dois;
(3) se caberia cobrar treinamento presencial pra operações grandes
tipo o Diplomatic Hotel (equipe numerosa, mudança de fluxo de trabalho
é mais drástica que num hostel pequeno) — recomendado como serviço
pago à parte, com preço por faixa de tamanho de equipe (não negociado
caso a caso) e primeiro treinamento gratuito/barato especificamente
durante o piloto, pra não arriscar o piloto fracassar por adoção fraca
da equipe. O usuário topou a sugestão de já deixar a aba Prospecção
preparada pra marcar quais contas são candidatas a treinamento,
conforme forem entrando.

Implementado como flag simples, não um sistema de tags genérico (fora
de escopo pro que foi pedido): `stayflow_leads.training_candidate`
(nova coluna, `add_column_if_not_exists`), checkbox no formulário de
criar/editar contato, selo 🎓 direto no nome na linha da tabela, e um
filtro "Só candidatos a treinamento" na toolbar (client-side, mesmo
padrão dos filtros de status/prioridade que já existiam). Testado com
`database.py` isoladamente (marcar na criação, marcar/desmarcar depois
via update) e — o teste que mais importava aqui — simulando uma tabela
`stayflow_leads` de PRODUÇÃO sem essa coluna, com um registro real já
cadastrado (o próprio Diplomatic Hotel como exemplo), confirmando que
rodar a migração não apaga nem corrompe nenhum contato já cadastrado
antes desta versão. Documentado no Documento Mestre, seção 16.34, e na
tabela de Controle de Versões (v1.51.0).

Mirror do backend sincronizado com as mesmas versões finais.

## SESSÃO 12 - 22/08/2026

### Correções pontuais de UI: selo de canal no Meu chat e botão Ask StayFlow

Usuário reportou que uma mensagem antiga no "Meu chat" (painel interno)
respondeu se identificando como "Hostel Lagares" — investigado a fundo
(rotina do webhook, resolução de `hostel_id` por `whatsapp_phone_number_id`,
lista completa de contas em produção) e confirmado que NÃO é bug de
isolamento entre contas: o hostel `id=1` já se chamou "Hostel Lagares"
antes de virar a conta de demonstração "StayFlow" (renomeação feita e
já documentada numa sessão anterior) — a mensagem antiga só carregava o
nome antigo. Nenhuma mistura de dado entre contas encontrada.

O que era bug real: `get_guests_inbox` (usado só pelo "Meu chat") não
devolvia o canal (`whatsapp`/`instagram`/`messenger`) de cada contato,
diferente da aba Chats normal das hospedagens, que já mostra isso via
`get_guest_channel`. Corrigido chamando `get_guest_channel` por guest
dentro de `get_guests_inbox`, e adicionado o mesmo selo colorido
(`chatChannelBadgeHtml`, cores iguais ao `channelBadgeHtml` de
`dashboard.html`) na lista do admin.

Também corrigido: o botão flutuante "Ask StayFlow" sobrepunha o botão
"Assumir" da barra de envio em duas telas diferentes — `dashboard.html`
(aba Chats das hospedagens, via `body.chats-page-active`) e, separado,
`admin.html` (aba "Meu chat" do painel interno, que usa outro fluxo de
troca de aba e nunca herdava a classe do dashboard). Resolvido com uma
classe própria pro painel interno (`admin-chat-tab-active`, setada em
`switchAdminTab`) e uma regra CSS `@media(min-width:641px)` (só
desktop) pra cada uma das duas telas — a primeira tentativa subiu
demais (281px, foi parar no meio da tela), ajustado pra 100px depois do
usuário reportar visualmente.

De quebra, corrigida também: a conta "Estamparia Exemplo" (demo real
criada numa sessão anterior pro amigo do usuário) não aparecia no
seletor rápido de "Propriedades" no topo do painel interno — esse
seletor só lista contas marcadas como `is_own_test_account`, então
bastou chamar `POST /stayflow-admin/hostel/6/test-account` pra marcar.

### Alarme real de compromisso na Prospecção (v1.52.0)

Usuário já tinha dois compromissos reais cadastrados na Prospecção
(Hotel Camelo, segunda 10h; Miguel Seda, segunda 14h) e pediu um
alarme antes de cada um. Primeira tentativa foi uma rotina agendada do
próprio Claude Code (`RemoteTrigger` + `PushNotification`) — rejeitada
explicitamente pelo usuário: "to falando pro Stayflow me notificar,
não o Claude. Quero que o app esteja ligado pra me avisar", depois
refinado pra 30 e 10 minutos antes, com opção de configurar/selecionar
o alarme por compromisso. Planejado via Plan Mode antes de implementar.

Investigação encontrou toda a infraestrutura de Web Push já pronta e
funcionando desde a v1.43.0 (`services/push_service.py`, `sw.js`,
`routes/push.py` com `/push/status`/`/push/subscribe`, todos genéricos
por `hostel_id`/`user_id`) — só nunca tinha sido ligada ao painel
interno (`admin.html`, que não registrava service worker nem assinava
push nenhuma vez). Como o login do painel interno é dono do
`hostel_id=1` ("StayFlow", conta de teste do próprio usuário), bastou
copiar o MESMO fluxo cliente já usado em `dashboard.html` pro
`admin.html` — zero rota nova de subscribe/unsubscribe.

Não existia nenhum scheduler/cron no projeto (confirmado: sem
APScheduler, sem rota de cron, `Procfile` roda `gunicorn --workers 3`).
Resolvido com uma thread daemon simples em `app.py`, acordando a cada
60s. Como os 3 workers rodam esse laço em paralelo, a deduplicação usa
uma tabela de "claim" nova (`stayflow_lead_alarms_fired`, `INSERT OR
IGNORE` com `UNIQUE(lead_id, offset_minutes)`) — só quem ganha a
inserção manda a notificação de verdade, sem precisar de lock
distribuído nem fila.

`stayflow_leads` ganhou `next_action_time` (hora do compromisso, o
campo antigo só tinha data) e `alarm_offsets_minutes` (minutos antes,
ex. `"30,10"`). Formulário da Prospecção ganhou campo de horário +
checkboxes de 30/10 min + campo livre pra outros minutos. Nova função
`send_push_to_admin` (`services/push_service.py`) — diferente de
`send_push_to_hostel`, não respeita horário de silêncio nem preferência
de tipo de notificação, porque é um alarme pessoal explicitamente
configurado, não um aviso de hóspede que pode esperar. Fuso horário
fixo em `America/Argentina/Mendoza` (`services/lead_alarm_service.py`)
— decisão deliberada, é ferramenta de uso pessoal do usuário, não
multi-tenant. Selo 🔔 na tabela indica compromisso com alarme ativo.
Os dois compromissos já cadastrados (Hotel Camelo, Miguel Seda) foram
atualizados via API com horário e alarme 30/10 min. Documentado no
Documento Mestre, seção 16.34 (v1.52.0).

### Pendências levantadas nesta sessão, ainda não resolvidas

Registradas pelo usuário durante revisão ao vivo do painel, todas
adicionadas à lista de trabalho pra retomar:

- Cadastro de item do Portfólio (`Meu Portfólio` → "Novo item") parece
  reaproveitar a lista de `AGENCY_CATEGORIES` (Turismo/Aluguel de
  carro/Imobiliária/Automotivo/Comércio/...) como "Categoria" do
  produto — isso é a categoria do NEGÓCIO, não do item/produto
  individual (ex: uma estamparia não deveria escolher "Comércio" como
  categoria de uma camiseta). Formulário de criação também parece
  limitado demais de forma geral — revisar todos os campos.
- Reservas com data de check-out já vencida continuam com status
  `CONFIRMED` indefinidamente — sem marcação de atraso, sem aviso, sem
  geração de oportunidade/alerta de checkout. Sistema não avisa
  check-in feito nem check-in pendente vencido.
- Vários hóspedes na aba Reservas aparecem com o nome em texto simples
  (não clicável), enquanto outros são link pro perfil (`guestNameLink`,
  v1.34.0) — suspeita: reservas manuais sem `guest_id` vinculado (só
  nome digitado) não geram o link. Precisa confirmar e corrigir.

Nenhum desses foi corrigido ainda nesta sessão — ficaram na fila
depois do alarme de compromisso, por pedido explícito do usuário de
"enfileirar, não abandonar o que já estava em andamento".

### Auditoria completa por pendências (Master Context + Diário) e rodada de correções

Usuário pediu uma checagem final: "tem mais alguma coisa parada ou
pendente que vamos terminar tudo". Duas investigações completas em
paralelo (protocolo de leitura sequencial 100%, sem pular trecho) nos
dois documentos — 6.116 linhas do Diário, 9.038 do Master Context —
levantaram uma lista grande de pendências reais, algumas de meses
(Hostel Lagares real nunca cadastrado, arquitetura de deploy manual,
japonês nunca adicionado, App Review do Instagram nunca confirmado
como enviado, WhatsApp Embedded Signup só como intenção registrada).
De brinde, a auditoria achou duas inconsistências no próprio Master
Context: cabeçalho de versão desatualizado (dizia 1.47.0/13-08 com o
conteúdo já em 1.52.0) e uma contradição real sobre envio de
notificação de reserva via Instagram (seção 16.10 dizia que não
funcionava, seção 16.26 dizia que funcionava — conferido no código:
funciona, 16.10 estava desatualizada). Ambas corrigidas.

Usuário decidiu: esquecer de vez o Hostel Lagares como piloto (não é
mais candidato) e adiar a segunda conta de WhatsApp Brasil — os dois
saíram da lista. Do resto, pediu pra eu mesmo ordenar por relevância e
já ir corrigindo, avisando o que fosse fazendo, sem perguntar de novo
a cada item.

Executado nesta rodada (pequenos e médios primeiro): botão "Teste
grátis" já apontava certo (falso alarme do diário antigo); dropdown de
idioma/usuário cortado no mobile corrigido (bug de meses — `left:0`
fazia o dropdown nascer fora da tela nos dois últimos botões da barra,
resolvido ancorando pela direita só no mobile); limpeza de
`templates/components/` (7 arquivos vazios, nunca usados),
`teste-users.html` e `_screenshots_revisao/`; tela de histórico de
visitas do Hub (o log já existia desde a v1.47.0, só faltava UI);
upload real de foto no Portfólio (antes só aceitava URL colada — nova
tabela `portfolio_photos`, rota pública `/media/portfolio/<token>`,
mesmo padrão do chat). De brinde nessa última, achada e corrigida uma
regressão real: a correção de categoria do Portfólio da sessão
anterior tinha deixado o *backend* (`routes/portfolio.py`) ainda
validando contra `AGENCY_CATEGORIES` — qualquer categoria de produto
digitada que não fosse um dos 8 códigos de negócio dava 400 "Categoria
inválida". Corrigido antes de qualquer cliente real esbarrar nisso.

Idiomas novos (japonês + italiano) foram reclassificados de "correção
rápida" pra "precisa planejar": o dicionário de i18n do dashboard tem
mais de 1.000 chaves por idioma (5.275 linhas pra 5 idiomas hoje) —
traduzir isso às cegas, sem forma de testar visualmente quebra de
layout em script CJK, é tarefa grande demais pra encaixar como item
pequeno.

Pedido explícito de processo, registrado como regra permanente: quando
uma instrução nova chega enquanto outra tarefa está em andamento,
enfileirar e avisar quando começar a próxima — nunca abandonar o que
já estava sendo feito, a menos que interfira diretamente (nesse caso,
ponderar com o usuário antes).

Ordem de prioridade escolhida pros itens grandes restantes (a pedido
do usuário, "escolha você"): WhatsApp Embedded Signup → Nuvemshop/
Tiendanube → Agente de IA (persona/tom/escalonamento) → resposta
automática em conversa assumida → matching semântico do Opportunity
Center → arquitetura de deploy → cobrança automática (Billing Fase
2-3) → CSP sem unsafe-inline → idiomas novos. Critério: impacto nos
pilotos ativos agora (Hotel Camelo, rede de 3 hotéis via Miguel Seda)
pesou mais que dívida técnica sem efeito visível pro cliente.

### WhatsApp Embedded Signup (v1.53.0)

Primeiro item grande da lista. Investigação prévia (background agent)
mapeou o padrão existente de Facebook/Instagram OAuth
(`services/meta_oauth_service.py`, `routes/meta_oauth.py`) e confirmou
um achado importante: o WhatsApp Embedded Signup da Meta **não segue
o mesmo desenho de redirect de página inteira** — é SDK JavaScript
(`FB.login()` com um `config_id` próprio), aberto num popup dentro da
própria página do dashboard, sem nunca sair da StayFlow. O resultado
chega em dois canais ao mesmo tempo: o `code` no callback do
`FB.login()`, e `phone_number_id`/`waba_id` via evento `postMessage`
(`WA_EMBEDDED_SIGNUP`) disparado pelo próprio popup da Meta. Como isso
roda todo dentro da página já autenticada (nunca existe uma rota
pública de callback), o `state` anti-CSRF que Facebook/Instagram
precisam não faz falta aqui — a coluna `hostels.whatsapp_oauth_state`,
criada preventivamente havia sessões pra esse fluxo, acabou ficando
sem uso real (desenho mais simples do que se esperava, não é problema).

Implementado: helper comum de troca "code → token de longa duração"
extraído de `exchange_code_for_page` (agora reaproveitado também pelo
WhatsApp, evitando duplicar a lógica); `exchange_whatsapp_embedded_signup`
troca o token, registra o número na Cloud API (`POST
/<phone_number_id>/register`, com um PIN de 6 dígitos gerado na hora —
só exigência técnica da API, nunca visto/reutilizado pelo usuário) e
inscreve o app da StayFlow nos webhooks da WABA (`POST
/<waba_id>/subscribed_apps`), pra mensagem já cair no
`/webhook/whatsapp` que já existia. Nova env var `WHATSAPP_CONFIG_ID`
— diferente de `FACEBOOK_CONFIG_ID` (só server-side), essa precisa ser
exposta pro frontend, já que o `FB.login()` do navegador a usa
diretamente; não é segredo, é um identificador público de
configuração. `GET /settings/whatsapp` passou a expor
`oauth_available`/`app_id`/`config_id`.

Frontend: botão "Conectar via WhatsApp" ao lado do formulário manual
existente (só aparece com `oauth_available`), SDK da Meta carregado
sob demanda (só quando o botão é clicado, não em toda carga do
dashboard), listener de `message` pra capturar o evento
`WA_EMBEDDED_SIGNUP`, e um POST final juntando `code` +
`phone_number_id` + `waba_id`. A CSP (`app.py`) precisou de uma
exceção nova — `connect.facebook.net` liberado em `script-src` e
`connect-src`/`graph.facebook.com` em `connect-src` — único host
externo aberto na CSP até agora, necessário pro SDK JS funcionar.

Mesma limitação do App Review do Instagram: só funciona de ponta a
ponta depois que existir, de verdade, uma "WhatsApp Embedded Signup
configuration" criada no painel de developers da Meta pro App da
StayFlow (gera o `config_id` real) — até lá, o botão fica escondido,
mesmo comportamento que Facebook/Instagram já têm sem suas respectivas
configurações. Bloqueio de configuração externa, não de código.

### Integração Nuvemshop/Tiendanube (v1.54.0)

Segundo item grande da lista de prioridades. Pesquisa na documentação
oficial (`tiendanube.github.io/api-documentation`) confirmou: OAuth
2.0 restrito (só `authorization_code`, token não expira — só invalida
se o lojista desinstalar o app), autorização em
`www.tiendanube.com/apps/{client_id}/authorize`, troca de código em
`POST .../apps/authorize/token` já devolvendo o `user_id` (ID da loja)
junto com o token, sem precisar de uma chamada separada tipo
`/me/accounts` do Facebook. Um detalhe pego só na segunda busca (a
primeira deu um header errado): a API usa `Authorization: Bearer
{token}` de verdade (não `Authentication: bearer` como uma fonte menos
precisa sugeriu), exige um header `User-Agent` identificando o app em
toda chamada, e o caminho é versionado por data
(`api.tiendanube.com/2025-03/`, não `/v1/`) — mesmo domínio serve
Argentina e Brasil, resolvendo de graça a dúvida que o plano tinha
registrado sobre domínio diferente por país.

Decisão de arquitetura que valeu a pena conferir antes de implementar:
em vez de criar uma tabela nova pro catálogo sincronizado, `portfolio_items`
(a mesma que já alimenta `get_offerings`/a IA desde a criação do
Portfólio) ganhou `external_id`/`source` — vocabulário emprestado de
`guest_channel_identities` (único precedente real de "isso veio de
fora" no schema, achado numa investigação dedicada antes de inventar
um nome novo). Idempotência via índice único PARCIAL (`WHERE
external_id IS NOT NULL`), não uma constraint normal — assim item
cadastrado à mão (que fica com `external_id` `NULL`) nunca esbarra na
regra de unicidade, já que o SQLite trata cada `NULL` como distinto.
Sincronização inicial roda completa assim que a loja conecta (sem
esperar o primeiro webhook), e os eventos `product/created`,
`product/updated`, `product/deleted`, `order/paid` mantêm tudo
atualizado depois — o último dispara um push novo (`nuvemshop_order`)
avisando o pedido pago.

Webhook validado com uma função de assinatura própria
(`verify_nuvemshop_signature`, `utils/webhook_security.py`) em vez de
generalizar a da Meta — o header (`x-linkedstore-hmac-sha256`, hash
puro sem prefixo `sha256=`) e o secret são diferentes o suficiente pra
não valer a pena forçar reaproveitamento. Fora de escopo desta rodada,
registrado explicitamente: sincronizar estoque/variantes, mandar dado
de volta pra Nuvemshop (só leitura por enquanto), e Mercado Livre
(plataforma própria separada, self-contida, seguirá como pendência à
parte quando o usuário decidir priorizar).

### Agente de IA — persona/tom customizados (v1.55.0)

Terceiro item grande da lista. Investigação prévia confirmou que o
card "Agente de IA (persona, tom, regras de escalonamento)" era um
placeholder morto desde sempre — a condição citada ("disponível quando
o Ask StayFlow tiver function calling") nunca teve relação real com
essa feature (Ask StayFlow é o copiloto interno do dashboard, sistema
separado do `ask_ai()` de atendimento) e já estava cumprida há tempo;
a feature em si nunca foi construída.

Decisão que valeu a pena confirmar antes de implementar: um campo de
texto livre (`settings.ai_custom_instructions`), não três campos
estruturados — o parênteses do título descreve o TIPO de coisa que
cabe ali, não exige inputs separados. Interpolado como uma seção
ADICIONAL no fim dos templates de prompt (`{custom_instructions_section}`,
mesmo padrão de placeholder dinâmico já usado por
`{agency_subcategory_line}`), com uma frase deixando explícito que as
instruções do dono nunca substituem a espinha dorsal de segurança
(nunca inventar preço, nunca fechar venda sozinha) — testado
renderizando os 9 templates reais (hospedagem + 8 categorias de
agência) com e sem instrução customizada antes de subir, sem erro de
`.format()`. Deliberadamente fora de `SOFTWARE_SYSTEM_PROMPT` (número
comercial da própria StayFlow). Reaproveitou 100% o mecanismo genérico
de Configurações já existente (`_SETTINGS_TEXT_FIELDS`) — só a
validação de tamanho (2000 caracteres) precisou de um `if` a mais no
handler.

### Resposta automática pra dúvidas simples em conversa assumida (v1.56.0)

Quarto item grande, mesmo padrão de placeholder morto do anterior
(checkbox `checked disabled`, sem `data-setting` nenhum, texto
"depende do recurso de assumir conversa" — recurso que já funciona
desde sessões bem anteriores). Meio-termo pedido: hoje "assumir
conversa" é tudo ou nada, a IA some completamente até alguém devolver;
o pedido era deixar a IA ainda responder sozinha PERGUNTAS SIMPLES
mesmo com a conversa assumida, ficando calada em qualquer coisa mais
complexa.

Achado que evitou construir um classificador do zero: `services/decision_engine.py::analyze_message()`
já roda ANTES do gate de `ai_paused` em `routes/chat.py`, e já devolve
`intent` (`booking/tour/upsell/human_help/follow_up/general`) e
`urgency` (`low/medium/high`) — a própria regra do decision engine já
sobe a urgência quando o hóspede parece frustrado ou pede algo que a
IA não teria confiança de resolver sozinha, que é basicamente o
inverso de "pergunta simples". Critério adotado: `intent in ("general", "follow_up")`
E `urgency == "low"` — qualquer `human_help` ou urgência acima de
`low` mantém o silêncio de sempre. Isso significou reestruturar um
`if` só (routes/chat.py, bloco de `conversation_assumed`) em vez de
inventar uma segunda chamada de IA pra classificar.

Trade-off aceito conscientemente e documentado na própria UI: essa
classificação só existe quando "Geração de oportunidades" está ligada
— em vez de pagar o custo/latência de uma chamada de IA extra só pra
classificar quando essa opção estiver desligada, o recurso novo
simplesmente exige que ela esteja ativa (já vem ligada por padrão, não
é uma limitação real na prática). Efeito colateral corrigido de
propósito: o push `assumed_conversation` (que antes disparava sempre
que chegava mensagem numa conversa assumida) passou a ser suprimido
quando a IA já respondeu a dúvida sozinha — sem isso a equipe seria
alarmada com "hóspede esperando" mesmo com o problema já resolvido.

### Matching semântico na sugestão de item de parceiro (v1.57.0)

Quinto item grande da lista pós-auditoria. Dívida técnica registrada
desde a v1.47.0: quando o Opportunity Center detecta `intent == "tour"`
e a hospedagem tem algum item de Parceiros habilitado, ele sempre
sugeria o PRIMEIRO item da lista, sem nenhuma relação com o que o
hóspede realmente pediu — na prática, provavelmente a equipe já
ignorava a sugestão por saber que era aleatória.

Investigação (`services/decision_engine.py::analyze_message()`)
confirmou o código exato da dívida: `partner_items[0]["id"]` sem
qualquer comparação com o pedido do hóspede. E confirmou que o
universo de candidatos é sempre pequeno — são só os itens que a
PRÓPRIA hospedagem já ativou manualmente na tela Parceiros, sem
paginação em lugar nenhum do fluxo — então dava pra resolver isso sem
embeddings/busca vetorial, só injetando a lista direto no prompt que
já existe.

Decisão de arquitetura: em vez de uma segunda chamada de IA só pra
escolher o item, a MESMA chamada que já classifica a conversa
(`analyze_with_ai`) passou a receber a lista de candidatos (id, nome,
categoria, descrição) e a devolver `suggested_partner_item_id` dentro
do mesmo JSON que já pedia `intent`/`urgency`/etc. — zero round-trip
extra, zero custo adicional pra quem não usa Parceiros (o bloco só
entra no prompt quando existem itens habilitados). `get_enabled_partner_items_for_hostel`
(`database.py`) ganhou `pi.description` no `SELECT` (só tinha
name/category/price) pra dar mais contexto de matching.

Mantido de propósito o gate `intent == "tour"` que já existia (decisão
de produto antiga: `upsell` é genérico demais, cobre coisas sem
relação nenhuma, tipo upgrade de quarto) — a mudança é só em COMO
escolher entre os candidatos, não em QUANDO sugerir. Validação
defensiva adicionada: o id que a IA devolve só é aceito se realmente
está entre os ids que foram oferecidos no prompt (`set` de
`partner_items` já buscados), protegendo contra a IA "inventar" um id
fora da lista. Testado via checagem de sintaxe, assinatura da função
(`inspect.signature`) e import completo do app sem erro.

### Consolidação da arquitetura de deploy do frontend (v1.58.0)

Sexto item grande da lista pós-auditoria, e o mais antigo dos seis —
dívida registrada desde a v1.4.0 (13/07/2026): o Render builda só um
repositório por serviço, então o conteúdo de `StayFlow---Site/` (repo
canônico do frontend) precisa existir fisicamente dentro do
`HostelBot` (`HostelBot/StayFlow---Site/`) pra chegar em produção. Até
agora isso era mantido copiando arquivo por arquivo à mão
(`cp`/`xcopy`/`robocopy`) e commitando duas vezes, uma em cada repo —
processo que já causou divergência e retrabalho real ao longo da
história do projeto, inclusive dentro desta própria sessão (a
documentação teve que ser copiada manualmente a cada versão nova).

Investigação antes de mexer em qualquer coisa: confirmado que
`HostelBot/StayFlow---Site/` é uma pasta comum (sem `.git` próprio,
sem submodule) rastreada como parte normal do repositório do backend;
que não existe nenhum script versionado de sincronização (tudo
manual até hoje); e que existia uma **terceira cópia**, órfã, na raiz
do próprio `HostelBot`: um `admin.html` desatualizado (sem
Prospecção, sem foto no chat, sem push do painel interno) que não
correspondia a nenhuma rota ativa — todas as rotas de página HTML do
Flask servem via `FRONTEND_DIR`, nunca da raiz do backend. Resíduo
morto de uma estrutura anterior, removido com segurança.

Decisão de arquitetura tomada explicitamente: NÃO fazer a separação
"definitiva" já cogitada no Roadmap (frontend como Static Site próprio
do Render, backend virando API pura num subdomínio) — isso implicaria
reconfigurar cookies de sessão entre domínios, CORS e o escopo do
Service Worker (push/PWA), com corte de DNS, risco real demais pra uma
base com pilotos reais ativos (Hotel Camelo, rede do Miguel Seda,
estamparia) agora. Em vez disso, atacada a causa concreta do
retrabalho — a cópia manual em si — sem mexer em domínio/topologia de
produção: `HostelBot/StayFlow---Site/` virou um **git subtree** do
repositório `StayFlow---Site` (`git subtree add --prefix=StayFlow---Site
<url> main --squash`). Migração feita com cautela: `diff -r` completo
entre canônico e cópia aninhada ANTES de mexer (zero diferenças,
baseline confirmado), `git rm -r` da pasta antiga + commit, depois
`git subtree add`, e `diff -r` de novo depois pra confirmar que o
conteúdo continuava equivalente.

Achado no meio do caminho: o `git subtree add` fez um checkout de
verdade (fetch + read-tree), e como `core.autocrlf=true` está ligado
nos dois repos, isso converteu quebra de linha LF→CRLF em vários
arquivos — divergência que a cópia manual antiga nunca expunha
(`cp` não mexe em quebra de linha, só preservava os bytes como
estavam). Confirmado com checksum ignorando quebra de linha que o
conteúdo continuava 100% idêntico (zero diferença real), e resolvido
de forma permanente com `.gitattributes` (`eol=lf`) no `HostelBot`,
pra eliminar esse ruído em todo `git subtree pull` futuro.

Resultado prático: sincronizar frontend → backend deixou de ser
"copiar arquivo por arquivo e torcer pra não esquecer nenhum" e virou
um comando único — `bash sync_frontend.sh` (novo, wrapper de
`git subtree pull --squash` com a URL já embutida), seguido de
`git push` manual depois de revisar (nenhuma automação de push —
mesma disciplina de sempre confirmar antes de publicar). Continuam
sendo dois repositórios de verdade (não virou monorepo), e nada mudou
do lado do Render — mesmo caminho, mesma variável `STAYFLOW_FRONTEND_DIR`,
zero reconfiguração necessária. Verificado ao final: `python -c "import
app"` continua funcionando, `FRONTEND_DIR` resolve normalmente, e o
script de sync roda sem erro (testado logo após a migração, quando não
havia nada novo pra puxar — confirmou "already at commit" sem
quebrar).

### Comparação competitiva com a Aoki e fila de melhorias

Usuário pediu pesquisa sobre a Aoki (ia.aoki), concorrente argentina de
Mar del Plata (chatbot de IA pra WhatsApp/Instagram, ~21 pessoas,
Meta Business Partner, prêmio de inovação industrial 2022, contrato
com a Municipalidade de General Pueyrredón, programa de revenda "Plan
Partner" com comissão recorrente 25/30/35%). Avaliação honesta: em
marketing/equipe/validação externa a Aoki está muito à frente (438
posts, 34,3 mil seguidores, +300 clientes claimados) - fato, sem
disfarçar. Mas o produto deles é raso pra hotelaria especificamente
(sem reserva, mapa de quartos, PMS, financeiro) - é essencialmente um
chatbot de vendas genérico multi-vertical (gastronomia, saúde,
cooperativas) com CRM básico por cima, não uma plataforma de operação.

Do lado do produto, identificado um gap real (confirmado no código,
não só inferido da concorrência): `routes/executive.py` só tem
contagem agregada total (`total_messages`/`total_guests`/`open_opportunities`),
sem série temporal por período; `statistics.html` existe mas é página
órfã sem nenhum dado real ligado. A Aoki mostra métricas por
dia/semana/mês. Adicionado à fila: dashboard de métricas de chat por
período. Do lado de GTM (não é código): formalizar um programa de
parceiro/indicação com comissão recorrente, inspirado no "Plan
Partner" deles - literalmente o que o Miguel Seda já faz informalmente
trazendo a rede de 3 hotéis dele.

Usuário instruiu: terminar a fila já em andamento primeiro (Billing
Fase 2-3, CSP, idiomas), depois entrar nesses itens novos. Adicionado
ao final da fila de prioridades.

### Billing Fase 2 — cobrança recorrente automática (v1.59.0)

Sétimo item grande da lista pós-auditoria, e a última frente de
Billing ainda 100% manual/honra: a tabela `billing` já tinha
`payment_processor`/`processor_customer_id`/`processor_subscription_id`
como colunas vazias desde a Fase 1, e `set_billing_plan()` já aceitava
esses parâmetros, mas nenhum chamador os usava. Trial de 30 dias era
criado automático, mas nada verificava se tinha vencido - `status`
nunca mudava sozinho.

Investigação (`routes/billing.py`, schema de `billing`,
`services/mercadopago_service.py` inteiro) confirmou: zero decisão
anterior registrada sobre Stripe vs Mercado Pago pra essa cobrança
específica (sempre apareciam juntos, entre parênteses, como opção em
aberto); zero uso de `preapproval` (API de assinatura recorrente do
MP) em qualquer lugar do código; zero linha de Stripe (nem SDK
instalado, nem variável de ambiente lida).

Decisão de arquitetura tomada nesta sessão: Mercado Pago, não Stripe -
motivo prático, não só técnico. Stripe não abre conta padrão pra
recebedor domiciliado na Argentina (o monotributo do usuário) - sem
conta capaz de receber o dinheiro, a integração ficaria bloqueada
igual outras pendências já registradas (App Review do Instagram,
credencial MP). Decisão explicitamente registrada no plano e nos docs
pra poder ser revertida se o usuário algum dia tiver como receber via
Stripe (entidade no exterior, por exemplo).

Achado importante que mudou a arquitetura: essa cobrança é o INVERSO
do Split guest-facing que já existe. No Split, cada HOSTEL conecta a
própria conta MP via OAuth e recebe o dinheiro do hóspede. Aqui é a
StayFlow que precisa RECEBER a mensalidade do hostel - não dá pra
reaproveitar o token OAuth por-hostel, precisa de uma credencial nova
e única da conta MP da própria StayFlow
(`MERCADOPAGO_PLATFORM_ACCESS_TOKEN`). Reaproveitado do Split: só o
PADRÃO (webhook idempotente via tabela dedicada, nunca lança exceção,
sempre responde 200), não o fluxo em si - por isso
`mp_billing_webhook_events` é uma tabela separada de `mp_webhook_events`.

Moeda: ARS, não USD. `PLAN_PRICES` (89/349/699) sempre foi só
estimativa de MRR pro painel interno, nunca dinheiro cobrado de
verdade - uma conta MP argentina cobra em ARS. Em vez de construir o
motor de câmbio/FX (dívida já conhecida e deliberadamente adiada),
criado `PLAN_PRICES_ARS` separado, mantido manualmente (mesmo espírito
de preço fixo ajustado de vez em quando).

Decisão de escopo mais importante: bloqueio de acesso por
inadimplência ficou de fora desta rodada, de propósito. O laço novo em
`app.py` (`_billing_trial_expiration_loop`, roda a cada hora,
reaproveitando o mesmo padrão de daemon thread do alarme de
compromisso) só atualiza `status` pra `past_due` quando o trial vence
sem assinatura - puro bookkeeping, aparece certo na tela, mas não
trava rota nenhuma. Motivo: um bug numa trava de acesso bloquearia um
piloto real ativo (Hotel Camelo, rede do Miguel Seda) por engano -
risco alto demais pra shippar junto com a primeira versão da cobrança
em si. Fica registrado como decisão separada pra quando a cobrança já
estiver validada em produção.

Peça que faltava resolver no meio do caminho: a notificação
`subscription_authorized_payment` (cobrança mensal individual) só traz
o id do PAGAMENTO, não o id da assinatura - foi preciso adicionar
`get_authorized_payment` (consulta a `/authorized_payments/{id}`) só
pra descobrir a qual `preapproval_id` (e portanto qual hostel) aquele
pagamento pertence, antes de decidir se marca `active` ou `past_due`.

Testado: `python -c "import app"` sem erro, todas as rotas novas
(`/billing/subscribe`, `/billing/subscribe/return`, `/billing/cancel`,
`/webhook/mercadopago-billing`) aparecem em `url_map.iter_rules()`,
símbolos novos de `database.py` e `services/mercadopago_billing_service.py`
importam corretamente. Pré-requisito externo pra funcionar em produção
(mesmo padrão de bloqueio já visto no WhatsApp Embedded Signup e no
App Review do Instagram): usuário precisa gerar um Access Token de
produção na própria conta Mercado Pago dele.

### Remoção do unsafe-inline do CSP — reavaliado e confirmado (v1.60.0)

Oitavo item da fila. Investigado o tamanho real antes de propor
qualquer mudança: já existia uma decisão registrada desde a v1.39.0
(04/08/2026) tratando isso como "refatoração grande demais pra fazer
sem capacidade de teste visual real" — a investigação desta sessão
confirmou essa avaliação com números atualizados, não a contradisse.

Números: ~341 atributos de evento inline (`onclick`/`onchange`/
`onsubmit`/`oninput`/`onkeydown`), 81% concentrados em `dashboard.html`
(10.881 linhas) e 17% em `admin.html` — crescido de ~186 desde a
v1.39.0, confirmando que esperar só piora o problema, nunca melhora.
Mais ~990 atributos `style=` inline, 82% também em `dashboard.html`.
Zero infraestrutura de nonce existente pra reaproveitar.

Achado técnico novo, que fecha de vez a ideia de "fazer aos poucos":
por especificação CSP nível 2+, um navegador que entende
`'nonce-...'`/hash numa diretiva **ignora `'unsafe-inline'` na mesma
diretiva**, mesmo que ainda esteja listado (existe só como fallback
pra navegador antigo que nem entende nonce). Ou seja, adicionar nonce
só nos ~14 blocos `<script>` inline (que seria barato) quebraria os
~341 `onclick` em QUALQUER navegador atualizado no mesmo instante —
não existe meio-termo, é tudo ou nada. Pra `style-src`, `'unsafe-hashes'`
(CSP3) exigiria valor estático, e boa parte dos 990 `style=` é gerada
dinamicamente via JS (template string com valor interpolado),
invalidando hash fixo.

Usuário perguntou, antes de eu confirmar a decisão de não mexer, se
isso algum dia vira obrigatório (nesse caso seria mais barato fazer
agora, com o número menor, do que depois). Resposta dada: não existe
prazo técnico dos navegadores — `unsafe-inline` continua sendo aceito
indefinidamente, não é uma API sendo descontinuada. O único cenário
onde isso vira bloqueio de verdade é comercial, não técnico: um
cliente enterprise pedindo auditoria de segurança formal como
condição de contrato. Decisão final do usuário: não mexer agora,
documentar a decisão revisada. Registrado na seção "Decisão permanente
registrada" do Documento Mestre com os números atuais, pra quem
reabrir essa dívida no futuro já ter a resposta pronta.

### Idiomas novos: japonês e italiano nos 3 dicionários i18n (v1.61.0, primeira leva)

Nono item da lista de prioridades pós-auditoria — usuário pediu
originalmente japonês e italiano, depois lembrou que já tinha pedido
"encher de idiomas" numa sessão anterior (não só esses 2) e pediu mais
4: chinês, russo, coreano e holandês, adicionados na sequência desta
mesma sessão (ver entrada seguinte quando concluído). Árabe/hebraico
ficaram de fora de propósito — são RTL (direita pra esquerda), exigem
trabalho de CSS de layout espelhado antes mesmo de traduzir, tratado
como pendência separada, não junto com "adicionar idioma" simples.

Japonês adicionado primeiro (agente anterior), italiano adicionado
nesta rodada — ambos completando os 3 dicionários de tradução do
produto:
`assets/js/i18n-landing-data.js` (90 chaves), `assets/js/i18n-dashboard-data.js`
(1.028 chaves) e o objeto `ADMIN_I18N` dentro de `admin.html` (223
chaves), que tinham só pt/en/es/fr/de desde a v1.12.0.

Estratégia usada pra garantir paridade de chave num arquivo de mais de
1.000 chaves sem esquecer nenhuma: extração programática (regex) da
lista completa de chaves do bloco `en` de cada arquivo, tradução
conferida contra essa lista, e só então inserção do bloco novo.
Terminologia de hotelaria revisada por comparação direta com os blocos
`en`/`pt` já existentes (não tradução literal palavra por palavra) -
ex.: "Modalidade de quarto" vira "Categoria camera" em italiano e
"客室カテゴリー" em japonês; "Beliche" vira "Letto a castello"/"二段ベッド".
Placeholders (`{price}`, `{days}`, `{count}`) e tags HTML (`<strong>`,
`<br>`) preservados exatamente iguais em todo idioma. Japonês usa
aspas nativas (「」) onde o original tem aspas escapadas; italiano
segue o mesmo padrão das línguas latinas já existentes (aspas retas
escapadas), por consistência com o resto do arquivo. Diferente do que
uma nota anterior desta mesma sessão registrou por engano: o seletor
de idioma NÃO é genérico - `assets/js/i18n-core.js` tem
`SUPPORTED_LANGS` hardcoded, e os 3 dropdowns visíveis
(`index.html`/`dashboard.html`/`admin.html`) são blocos HTML fixos,
sem nenhum vindo de array JS. Cada idioma novo exige editar os 4
pontos manualmente, além de traduzir - corrigido nesta entrada e no
Documento Mestre.

Criada `tools/check_i18n_parity.py` - não existia nenhuma rede de
segurança automática garantindo que todo idioma tivesse exatamente o
mesmo conjunto de chaves nos 3 dicionários (era só disciplina manual
até aqui, arriscado num arquivo desse tamanho). O script faz parsing
dos blocos de cada idioma com balanceamento de chaves `{}` que ignora
chaves dentro de literais de string (pra não confundir `"ARS
{price}/mês"` com uma chave de bloco de idioma), extrai o conjunto de
chaves de cada um e falha se qualquer idioma tiver chave faltando ou
sobrando em qualquer um dos 3 arquivos. Rodado ao final desta rodada
com os 7 idiomas (pt/en/es/fr/de/ja/it) nos 3 arquivos: paridade
confirmada, sem chave faltando em nenhum. Documentado no Documento
Mestre, seção 16.35 (v1.61.0).

Nota de correção: essa não era a última pendência da lista — o
usuário lembrou de um pedido anterior ("encher de idiomas") e pediu
mais 4 idiomas na sequência (ver próxima entrada).

## SESSÃO 13 - 24/08/2026

### Conclusão dos idiomas novos: zh/ru/ko/nl (v1.62.0)

Usuário confirmou que "encher de idiomas" era o pedido original, não
só japonês/italiano. Recomendei chinês mandarim simplificado, russo,
coreano e holandês (mercados de turismo relevantes pra Argentina/
LATAM) e deixei explícito que árabe/hebraico ficam de fora dessa
rodada por serem RTL - exigem CSS de layout espelhado, não é só
tradução de texto. Usuário aprovou.

Traduzido via um agente em background por idioma, EM SEQUÊNCIA (não
em paralelo) - decisão deliberada pra evitar dois agentes escrevendo
no mesmo arquivo ao mesmo tempo (os 3 dicionários são compartilhados
entre todos os idiomas). Dois agentes (russo e holandês) esbarraram no
limite de sessão no meio do trabalho e precisaram ser retomados -
`tools/check_i18n_parity.py` foi essencial aqui: antes de retomar cada
agente, rodei o script eu mesmo pra confirmar exatamente quais dos 3
arquivos já estavam prontos e quais ainda faltavam, e passei esse
status preciso no prompt de retomada (em vez de assumir que o agente
lembraria sozinho onde parou).

Achado real: o agente do italiano (rodada anterior) tinha escrito
documentação por conta própria, sem eu ter pedido - e essa
documentação continha uma alegação falsa ("seletor de idioma não
precisou de mudança de código, já era genérico"). Isso é objetivamente
errado: `assets/js/i18n-core.js` tem `SUPPORTED_LANGS` hardcoded, e os
3 dropdowns visíveis (`index.html`/`dashboard.html`/`admin.html`) são
blocos HTML fixos - cada idioma novo exigiu 4 edições manuais (motor +
3 dropdowns) além da tradução. Corrigido no Documento Mestre (seção
16.35 reescrita) e nesta entrada. Lição registrada: instruir
explicitamente os próximos agentes de tradução a NÃO editar
documentação (só os 3 arquivos de dicionário) - aplicado a partir do
agente do chinês em diante, sem repetir o problema.

De brinde, usando o painel ao vivo: 3 pedidos reais de ajuste no
`admin.html` (painel interno, virou o painel principal do usuário) -
(1) status novos de lead na Prospecção (`no_show`/`adiado`/`cancelado`,
faltavam - só existia "call agendada" ou pular direto pra "perdido/sem
interesse", sem meio-termo pra reunião marcada que não aconteceu, ver
próxima seção); (2) dropdowns de idioma do `admin.html` atualizados
com os 6 idiomas novos (feito num intervalo livre entre agentes de
tradução, editando só a parte HTML fora do objeto `ADMIN_I18N` pra não
conflitar); (3) mais 3 pedidos de UI ainda pendentes (Despesas dentro
de Financeiro, bug do F5 resetando pra Visão Geral, reorganização de
Configurações) - na fila, aguardando os agentes de tradução liberarem
o arquivo de vez.

### Status novos de lead na Prospecção: no_show/adiado/cancelado

Usuário relatou ao vivo: reunião marcada com o Hotel Camelo (24/08,
10h) - o contato não compareceu, sem nova data definida. Tentei
registrar isso e descobri que `_LEAD_STATUSES` (`routes/stayflow_admin.py`)
não tinha opção pra isso - só "call agendada" ou pular direto pra um
status de encerramento. Usuário confirmou o gap. Adicionados 3 status
novos (`no_show`, `adiado`, `cancelado`) ao enum do backend, deploy
publicado, e só depois disso consegui atualizar o lead do Hotel Camelo
pro status certo (a primeira tentativa, antes do deploy propagar,
precisou de retry em loop até o Render terminar de subir a versão
nova - 502 esperado durante o rollout). UI (dropdown/labels/estilo em
`admin.html`) implementada no mesmo intervalo livre acima.

### Dashboard de métricas de chat por período (v1.63.0)

Décimo item grande da sessão, motivado pela comparação competitiva com
a Aoki (mensagens/conversas/conversões com filtro de período, algo que
a StayFlow não tinha). Investigação confirmou o gap real:
`routes/executive.py` e o módulo de Relatórios (`get_reports_summary`)
só tinham totais acumulados desde sempre, sem nenhuma agregação por
tempo - a documentação descrevia o funil/receita por canal como "já
implementado", o que é verdade, mas sem quebra temporal nenhuma.

Achados que moldaram a solução: `messages` não tem `hostel_id`/`guest_id`
direto (sempre precisa `JOIN conversations → guests`), mas tem
`created_at` pra agrupar por bucket; `messages.sender` tem exatamente 3
valores reais em uso (`'user'`/`'assistant'`/`'staff'`, confirmado lendo
os 2 únicos pontos de `INSERT INTO messages` e seus chamadores, não
suposição) - "mensagens recebidas" = `sender='user'`;
`opportunities.status` nunca muda de `'open'` em lugar nenhum do código
hoje, não é sinal de conversão utilizável - a conversão real já usada
no funil existente é `reservations.status='confirmed'`, reaproveitado
como o mesmo proxy aqui, não um conceito novo. Nenhuma biblioteca de
gráfico carregada em lugar nenhum do frontend - único precedente é
`admin.html::renderGrowthChart` (painel interno, Canvas API nativa,
sem lib) - seguido o mesmo estilo de casa em vez de introduzir uma
dependência nova.

Extensão aditiva de `/reports` (`?period=daily|weekly|monthly`, chave
nova `chat_activity` na resposta) em vez de rota/página nova - a aba
Relatórios já existia com rota/permissão prontas. Testado com dado
real num hostel de teste isolado (banco temporário,
`STAYFLOW_DATA_DIR` apontado pra pasta separada): contagem de
mensagens por dia, conversas distintas e conversões batendo exatamente
com o esperado, mensagem de 20 dias atrás corretamente excluída da
janela diária de 14 dias. `statistics.html` (página órfã confirmada -
só ela mesma se referenciava, dado 100% fake, fora do design system)
removida de brinde, mesmo perfil das órfãs já limpas na v1.53.0.

### 3 ajustes no painel interno: F5, Despesas/Financeiro, Comunicação (v1.64.0)

`admin.html` virou o painel principal do usuário no dia a dia, e 3
pedidos nasceram de uso ao vivo hoje. Durante o planejamento, usuário
pediu de quebra que o WhatsApp tivesse clique único pra conectar
"igual Facebook e Instagram" - achado real: o WhatsApp já TINHA isso
(Embedded Signup, v1.53.0), só nunca tinha sido ligado no painel
interno.

**F5**: investigação confirmou `switchAdminTab()` sem nenhuma
persistência - `currentAdminTab` só variável JS em memória,
`page-overview` hardcoded como `active` no HTML estático. Corrigido
com `localStorage`, mesmo padrão já usado pelo idioma
(`stayflow_lang`).

**Despesas → sub-aba de Financeiro**: achado que mudou a expectativa
antes de mexer - o botão "+ Nova despesa" JÁ usava a classe CSS padrão
do sistema (`class="btn"`, idêntica à de Prospecção/Equipe). A
sensação de "fora do padrão" que o usuário reportou não vinha de CSS
divergente nenhum - vinha de estar num item de menu separado, fora do
contexto financeiro. Resolvido só com reorganização estrutural (pill
switcher dentro de Financeiro, mesmo padrão `.ops-tabs`/`.ops-tab` já
usado em Operações/Eventos/Equipe no dashboard normal), sem tocar no
CSS do botão em si.

**Comunicação em Configurações**: aqui apareceu a parte mais
interessante da investigação. Configurações do painel interno só
tinha status agregado READ-ONLY de credenciais de PLATAFORMA (App
Meta, Beds24 master, etc) - zero conectividade por conta, mesmo "Meu
chat" já rodando em cima de uma hospedagem real marcada como
"assistente comercial" (`hostels.ai_persona='software'`). Pra
conectar o WhatsApp dessa conta hoje, o usuário precisava ir em
`dashboard.html` de outra tela - sem link nem atalho dentro do próprio
painel interno.

Solução com dois mecanismos DIFERENTES, por uma limitação técnica real
descoberta na investigação: o login do `admin.html` não carrega
`hostel_id` de tenant nenhum na sessão (`@require_stayflow_admin`,
diferente de `@require_permission` que dashboard.html usa) - não dá
pra chamar `/settings/*` direto de lá. Resolvido criando rotas NOVAS
e FINAS em `routes/stayflow_admin.py`
(`/stayflow-admin/software-persona/*`) que resolvem o hostel fixo
internamente (`get_hostel_id_by_ai_persona("software")`) e chamam as
MESMAS funções que `routes/settings.py` já usa - zero lógica de
negócio duplicada, só a camada de autorização muda.

Mas WhatsApp e Facebook/Instagram não puderam usar exatamente o mesmo
mecanismo: WhatsApp Embedded Signup roda via `FB.login()` direto no
navegador (SDK JS), sem precisar de nenhum `redirect_uri` registrado
na Meta - dá pra reproduzir 100% dentro do `admin.html`, sem sair da
tela, nova rota espelhando `/settings/whatsapp/embedded-signup`.
Facebook/Instagram usam OAuth com redirect DE VERDADE pra Meta, e o
callback é uma URL fixa já registrada no painel de developer (não dá
pra duplicar sem reconfigurar o app lá, mudança externa fora do que dá
pra fazer só por código). Solução: o botão "Conectar" chama
`/stayflow-admin/impersonate` (mecanismo do Hub que já existia) pra
"entrar" na conta persona, e navega pro fluxo OAuth normal - ao
terminar, o usuário cai no dashboard da conta impersonada, com o
banner "Sair da visualização" já existente pra voltar. Não é tão
direto quanto o WhatsApp, mas ainda resolve o pedido de "clique em vez
de colar token manualmente", reaproveitando um mecanismo de navegação
que o usuário já conhece do Hub.

De quebra, corrigido: o badge de despesa vencida/vencendo
(`expensesDueBadge`) migrou do antigo botão de menu "Despesas" (que
deixou de existir) pro botão "Financeiro".

Testado: `python -c "import app"` sem erro após as rotas novas;
funções de banco por trás das rotas testadas com banco isolado
(marcar/ler/limpar persona, WhatsApp, Facebook - todos batendo
exatamente com o esperado); `tools/check_i18n_parity.py` confirmando
paridade das 16 chaves novas de Comunicação + 1 de Financeiro nos 11
idiomas do `ADMIN_I18N`; checagem de balanceamento de chaves `{}` no
arquivo inteiro (HTML+JS misturado) sem erro.

### Programa de parceiro/indicação com comissão recorrente (v1.65.0)

Item 12 da fila, o primeiro item "novo" (não pós-auditoria) desta
leva - inspirado no "Plan Partner" da Aoki (comissão em faixa
25/30/35%), motivado por formalizar o que o Miguel Seda já faz na
prática trazendo uma rede de 3 hotéis pra conhecer a StayFlow.

Investigação inicial (agente Explore) confirmou que não existia nada
disso no sistema - o único conceito de "parceiro" já presente
(`partner_referral_ledger`/`/stayflow-admin/partner-ledger`) é sobre
comissão de venda de item de portfólio de agência pro HÓSPEDE, não
sobre assinatura de um hotel indicado. Mesma palavra, dois conceitos
completamente diferentes - risco real de confundir/misturar no
código se não prestasse atenção.

Achado que mudou o desenho no meio do caminho: ao revisar o card real
do Miguel Seda na Prospecção pra confirmar o cenário, o
`property_name` dele é "Promotor StayFlow Brasil (MG, contatos em
todo o país)" - ele não é dono de hotel, não tem conta StayFlow, é um
promotor externo. Se o programa fosse modelado só como "hostel indica
hostel" (preso a `hostels.id`), o próprio caso de uso que motivou o
pedido não caberia sem gambiarra (criar uma conta hostel falsa só pra
guardar o código dele). Resolvido com uma entidade nova e desacoplada,
`referral_partners` (`linked_hostel_id` NULL pra promotor externo
cadastrado à mão via `admin.html`, preenchido pra hostel cliente
indicando outro - linha criada sob demanda na primeira vez que ele
abre o card no dashboard, sem nenhum setup manual pro caso comum).

Mecânica: `subscription_referral_ledger` acumula
`SUBSCRIPTION_REFERRAL_COMMISSION_PCT = 0.20` (fixo por enquanto, não
em faixas por volume como a Aoki - MVP simples, sinalizado como
decisão ajustável, não definitiva) sobre cada cobrança de assinatura
APROVADA de um hostel que foi indicado - gatilho direto dentro de
`mercadopago_billing_webhook.py::_process_authorized_payment_notification`,
o único ponto do sistema que já sabe "esse hostel pagou a mensalidade
agora" (mesmo lugar que confirma `billing.status='active'`).
Idempotente via `UNIQUE(mp_payment_id)` na tabela nova, mesma técnica
já usada em `mp_webhook_events` - reprocessar a mesma notificação do
Mercado Pago não duplica o acúmulo. `get_authorized_payment`
(`mercadopago_billing_service.py`) precisou ganhar `transaction_amount`
no retorno (antes só devolvia id da assinatura + status), único jeito
de saber QUANTO cobrar de comissão. `hostels.referred_by_partner_id`
é setado uma única vez em `/register` (novo campo opcional
`referral_code`, resolvido via `get_referral_partner_by_code`) - sem
retroatividade, hostels já existentes ficam de fora pra sempre.

UI em 3 pontas: `Register.html` lê `?ref=CODE` da URL e manda junto no
cadastro; `dashboard.html` ganha o card "Programa de indicação" dentro
de Configurações (mesma seção de Billing) - link com botão copiar,
lista de hotéis indicados com status, totais acumulado/pago;
`admin.html` ganha uma 3ª pill "Indicações" dentro de Financeiro (mesmo
padrão visual da tabela "Repasses" já existente, reaproveitado, não
reinventado), com botão de payout manual e um formulário pra cadastrar
parceiro externo tipo o Miguel Seda, devolvendo o código gerado pra
repassar por fora (WhatsApp).

Testado com rigor maior que o de costume, dado que envolve dinheiro:
script isolado (banco `STAYFLOW_DATA_DIR` temporário) cobrindo
ponta a ponta - criação de dois hostels de teste, geração lazy de
código de indicação, lookup case-insensitive por código, vínculo de
indicação, criação de parceiro manual, acúmulo de comissão, DUPLA
tentativa de acúmulo com o mesmo `mp_payment_id` confirmando que a
segunda é ignorada (idempotência), resumo agregado batendo com o
valor esperado, stats do hostel indicador, e payout zerando o saldo
`accrued` - script apagado depois, não é dívida deixada no repo.
`tools/check_i18n_parity.py` confirmando as 10 chaves novas do
dashboard (1.037→1.047) e as 11 chaves novas do admin (240→251) nos
11 idiomas.

Fora de escopo, deliberado: payout automático de verdade (PIX/
transferência) continua manual, mesma decisão já tomada pro
partner-ledger antigo e pro Billing; comissão em faixas por volume
(como a Aoki) fica pra depois, só se o percentual fixo não for
incentivo suficiente na prática.

### Fix de layout mobile em "Meu chat" e "Suporte" (v1.66.0)

Reportado ao vivo pelo usuário via print do celular: no `admin.html`,
tanto "Meu chat" quanto "Suporte" usam `.chat-layout` de 2 colunas
(lista de conversas + janela de mensagens lado a lado) - o mesmo
layout do desktop, sem adaptação nenhuma pro celular. Resultado: no
mobile a lista ocupava a tela toda e a conversa em si ficava
espremida/escondida, exigindo rolar pra ver alguma coisa.

O mecanismo certo pra isso já existia no projeto - só nunca tinha sido
estendido pro painel interno. O dashboard normal do cliente
(`dashboard.html`, aba Chats) já resolve exatamente esse problema
desde antes: `chats-live.js::setChatMobileView()` troca um atributo
`data-mobile-view` (`list`/`chat`/`profile`) num único `.chat-layout`,
e regras CSS em `static/css/app.css` (dentro de
`@media(max-width:1100px)`) escondem/mostram cada painel como tela
cheia - só que todas essas regras eram escopadas explicitamente com
`#chats` no seletor, então não valiam pra nenhum outro `.chat-layout`
da aplicação.

`admin.html` tem DOIS `.chat-layout` na mesma página (`#chatShell` pra
"Meu chat", `#supportShell` pra "Suporte") - reaproveitar
`setChatMobileView()` como está (que usa `document.querySelector` sem
escopo) pegaria sempre o primeiro da página, quebrando o segundo.
Resolvido com uma função irmã, `window.setAdminChatMobileView(layoutId, view)`,
que recebe o ID explícito de qual dos dois `.chat-layout` mexer -
mesma ideia, adaptada pra ter mais de uma instância na tela. As
regras de CSS foram estendidas (não duplicadas) pra também cobrir
`#chatShell`/`#supportShell` nos mesmos seletores que já existiam pra
`#chats`. `openMyChatGuest`/`openSupportThread` chamam a troca pra
`"chat"` quando `window.innerWidth <= 1100`; um botão "←"
(`.chat-mobile-back`, classe que já existia e já ficava escondida
fora do mobile por CSS, só nunca tinha sido usada aqui) chama a volta
pra `"list"`. `switchAdminTab()` ganhou o mesmo toggle de
`.chat-fullscreen` no `.main` que o dashboard já usa nas abas de chat,
pra rolar só a área de mensagens em vez da página inteira.

De quebra, achado no meio do caminho: o botão de voltar usava
`data-i18n-title="common.back"`, mas essa chave nunca tinha existido
no `ADMIN_I18N` (só existia em `i18n-dashboard-data.js`) - o
`applyTranslations` simplesmente não define `title` quando a chave não
existe (falha silenciosa, não quebra nada, só fica sem traduzir), mas
seria "Voltar" fixo em qualquer idioma. Adicionada a chave nos 11
idiomas do admin, reaproveitando as MESMAS traduções que o dashboard
já tinha (não traduzido de novo do zero).

Testado: checagem de balanceamento de chaves `{}` nos blocos
`<script>` do arquivo inteiro antes e depois das edições (701/701,
sem diferença por edição quebrada); `tools/check_i18n_parity.py`
confirmando as 252 chaves em paridade nos 11 idiomas do admin após a
chave nova.

### Pesquisa competitiva ampla + tags/notas/origem do lead (v1.67.0)

Usuário mandou, ao longo da sessão, uma sequência de prints de
anúncios do Instagram pedindo comparação: Chatty (letschatty.com),
Hubtype, respond.io, Darwin AI e Cloudbeds - cada um pesquisado na
hora (WebSearch + WebFetch direto nos sites/páginas de preço, não só
o que a busca resume) e comparado honestamente com a StayFlow, sem
disfarçar onde o concorrente é mais forte.

Achados por concorrente:
- **Chatty**: CRM de WhatsApp genérico (fundador Axel Gualda, captação
  de US$50 mil), sem vertical de hotelaria, mais caro que a StayFlow
  (US$150-250/mês + US$100/mês de IA à parte + custo por mensagem da
  Meta, contra US$89/mês tudo incluído). Diferencial real deles:
  rastreamento de origem do lead (de qual anúncio veio a conversa).
- **Hubtype**: fora de liga - fundada 2016 em Barcelona, 15M+
  interações/mês, clientes tipo Decathlon/Mango/VW/EasyJet, modelo
  enterprise sem preço público. Sem vertical de hotelaria, não é
  ameaça direta no mercado atual da StayFlow.
- **respond.io**: o mais robusto dos genéricos - omnichannel de
  verdade (WhatsApp/Instagram/Facebook/TikTok/Telegram/voz/e-mail),
  10 mil+ marcas clientes, sincroniza com Salesforce/HubSpot,
  US$79-279+/mês por contato ativo. O próprio anúncio que o usuário
  mandou destacava "Tag Contacts Buyer Intent using Lifecycle" como
  feature de marca - validação de mercado extra de que tags é padrão
  consolidado, não capricho de UX.
- **Darwin AI**: startup argentina (sede em São Paulo), fundada 2023,
  já captou ~US$7 milhões (US$4,5M da Base10 Partners), opera em 20+
  países da América Latina, "funcionários de IA" com nome próprio
  (Alba/Sofía/Bruno/Eva/Lucas). Mais capitalizado que os outros, mas
  mesmo padrão: genérico multi-vertical, zero hotelaria.
- **Cloudbeds**: o único concorrente de verdade pesquisado nessa
  rodada - PMS líder de mercado pra hospedagem independente/pequena-
  média, dezenas de milhares de propriedades em 150 países, IA própria
  (Signals, modelo fundação treinado especificamente pra hotelaria,
  95% de acurácia de previsão de demanda) e mensageria via WhatsApp
  através do Whistle (empresa que compraram e integraram). Diferença
  estrutural: Cloudbeds nasceu PMS e colou IA/WhatsApp por cima; a
  StayFlow nasceu IA conversacional e conecta com PMS por baixo
  (Beds24) - arquiteturas opostas pro mesmo problema. Preço: piso de
  US$180-220/mês (mesmo pra propriedade de 15 quartos), escalando
  US$15-25+/quarto - mais que o dobro do piso da StayFlow (US$89),
  deixando de fora exatamente o segmento que a StayFlow ataca primeiro
  (hostel/pousada pequena). Signals não é replicável agora - não por
  limitação de código, mas porque exige anos de dado histórico real
  acumulado de dezenas de milhares de propriedades pra treinar um
  modelo preditivo com confiança; StayFlow ainda não tem essa escala
  de base de dados.

Nenhum dos 5 concorrentes tem vertical de hotelaria com reserva/PMS de
verdade (nem Hubtype nem respond.io nem Darwin AI) - só o Cloudbeds,
que é PMS puro com IA/mensageria colada depois. Reforça que a StayFlow
continua sendo a única fazendo IA conversacional NATIVAMENTE
verticalizada em hotelaria, não um detalhe de posicionamento.

Do lado de produto (não GTM), confirmado por grep amplo no backend:
zero tabela de tag, nota interna ou rastreamento UTM/anúncio existia
antes dessa rodada. Implementado:

**Tags** - `guest_tags` (`UNIQUE(guest_id, tag)`, texto livre, sem
lista pré-definida). **Notas internas** - `guest_notes`, log
append-only (sem edição/exclusão nesta rodada, escopo mínimo
deliberado), autoria via `get_current_user_id()` +
`get_user_by_id()`. **Origem do lead** - `guests.lead_referral_json`,
gravada por `set_guest_lead_referral()` a partir do payload `referral`
que a Meta já manda em mensagens vindas de anúncio "Click to
WhatsApp" (`routes/whatsapp_webhook.py::receive_message()` lia o
payload inteiro mas descartava esse campo até agora) - idempotente
(só grava se `lead_referral_json IS NULL`), pra nunca sobrescrever a
origem original do hóspede com o que vier em mensagens seguintes.
`process_incoming_message()` (`routes/chat.py`) ganhou o parâmetro
`referral=None` pra propagar isso desde o webhook até a criação do
hóspede, sem duplicar lógica entre os pontos de entrada.

UI só no painel `.guest-profile` da aba Chats (`dashboard.html` +
`chats-live.js::loadGuestProfile()`) - 2 novas `.smart-profile-section`
(Tags com pills removíveis + input; Notas internas com autor/data +
textarea), e um `.smart-tag` extra na hero ("📢 Veio de anúncio")
quando `lead_referral` existe. Deliberadamente fora de escopo: o modal
de edição de perfil da lista de Hóspedes (`renderGuestProfileModal`) -
os mesmos dados já saem no `GET /guests/<id>`, só falta desenhar a UI
lá se for pedido depois.

Testado com banco isolado antes do commit: tag duplicada vira no-op
(via `INSERT OR IGNORE` + `UNIQUE`), remover tag funciona, nota vazia
levanta `ValueError`, duas notas aparecem na ordem certa (mais
recente primeiro) com autor correto, e o teste mais importante -
chamar `set_guest_lead_referral` DUAS vezes com payloads diferentes
confirma que só o primeiro é gravado (idempotência de origem).
`tools/check_i18n_parity.py` confirmando as 10 chaves novas em
paridade nos 11 idiomas (1.047→1.057).

### Maturidade de PMS: tarifa por temporada (v1.68.0)

Depois de comparar a StayFlow com o Cloudbeds (PMS líder de mercado,
dezenas de milhares de propriedades, IA própria "Signals"), usuário
perguntou o que fazer pra "ficar mais adulto" naquilo que o Cloudbeds
faz bem - operação hoteleira clássica. Levantei 3 gaps reais
(confirmados no código, não achismo): tarifa por temporada, reserva
de grupo, multi-propriedade. Usuário pediu os 3; feature 1 desta
leva é tarifa por temporada.

Investigação (`database.py` completo em torno de `room_categories`/
`reservations`) confirmou: `price_per_night` é um único REAL fixo por
modalidade, sem qualquer conceito de calendário. Achado extra
relevante: o cálculo `price_per_night * nights` estava DUPLICADO em
3 lugares diferentes (`create_reservation_record` - fluxo manual/
dashboard, `create_reservation_from_chat` - fluxo IA/WhatsApp,
`create_reservation_from_channel` - fluxo Beds24/OTA) - qualquer
mudança de regra de preço precisaria ser replicada nos 3 lugares à
mão, risco real de esquecer um.

Resolvido com uma função central nova, `calculate_reservation_amount()`,
que soma o preço NOITE A NOITE (não mais uma multiplicação única) -
pra cada noite da estadia, verifica se alguma `rate_rules` cobre
aquela data especificamente; sem regra, usa o `price_per_night` fixo
de sempre. As 3 funções de criação de reserva foram atualizadas pra
chamar essa função central em vez de repetir a conta - elimina a
triplicação em vez de criar uma quarta cópia.

Decisão de arquitetura da tabela nova (`rate_rules`): ancorada em
`room_category_id` (FK de verdade pra `room_categories.id`) em vez de
seguir o mesmo padrão frágil de `reservations.room_type` (string,
`LOWER(name) = LOWER(?)`) - já que é uma tabela nova, não hereda a
fragilidade antiga só por "consistência" com um padrão que já era
conhecido como problema. Resolução de sobreposição entre regras
(ex: duas regras cobrindo a mesma data): a criada mais recentemente
vence - simples e determinístico, documentado no código. Decisão
consciente de ESCOPO: sem variação por dia da semana nesta rodada
(só intervalo de data) - foi o que literalmente foi pedido
("tarifa por temporada"), variação por dia da semana fica pra depois
se pedida.

UI: em vez de criar uma tela nova, a seção "Tarifas por período"
entrou dentro do modal que já existe pra editar uma modalidade de
quarto (`editCategoryUI` em `dashboard.html`) - lista de regras da
categoria + formulário simples (nome, data início, data fim, preço),
carregado via `GET /room-categories/<id>/rates` assim que o modal
abre.

Testado com rigor - banco isolado antes do commit: estadia de 3
noites sem regra nenhuma bate com o preço base; regra cobrindo só 2
das 3 noites soma corretamente (1 noite preço base + 2 noites preço
de temporada); duas regras sobrepondo a MESMA noite confirmam que a
mais recente vence; validação rejeita data de fim antes da data de
início e categoria inexistente; e o teste mais importante -
`create_reservation_record` chamado sem informar valor manual usa o
cálculo novo automaticamente, provando que a integração nos 3 pontos
de criação funciona de verdade, não só a função isolada.
`tools/check_i18n_parity.py` confirmando as 9 chaves novas nos 11
idiomas (1.057→1.066).

### Maturidade de PMS: reserva de grupo (v1.69.0)

Segundo item da leva de maturidade de PMS (Cloudbeds), depois da
tarifa por temporada. Investigação (`reservations` completo em
`database.py`) confirmou o gap: cada reserva é 1 linha = 1 cama/
quarto (`bed_id` singular) - zero tabela de junção ou campo de
agrupamento existia. Reserva de grupo (ex: excursão/evento cobrindo
vários quartos) hoje só dava pra fazer como N reservas soltas, sem
nenhum vínculo visual entre elas.

Resolvido com o mínimo necessário: `reservation_groups` é só uma
"capa" (`guest_name` + `created_at`, nada além disso) e
`reservations` ganhou `group_id` nullable - quando preenchida, várias
linhas pertencem ao mesmo grupo. A parte importante da decisão foi
NÃO reimplementar a lógica de criação de reserva: `create_group_reservation()`
só cria a capa e depois chama `create_reservation_record()` (a mesma
função de sempre) uma vez por quarto da lista, passando `group_id`
a mais - isso significa que a reserva de grupo herda de graça a MESMA
trava de cama (`reservar_cama_com_trava`), o mesmo cálculo de preço
noite-a-noite (`calculate_reservation_amount`, da v1.68.0 - inclusive
tarifa por temporada se aplicável) e o mesmo webhook de saída, sem
nenhuma cópia paralela de validação que pudesse divergir com o tempo.

Decisão de escopo deliberada: sem motor de desconto de grupo - cada
quarto continua cobrando seu preço normal. "Grupo" aqui é só
organização/vínculo visual, não uma feature de precificação; se
descontos de grupo forem pedidos depois, é uma decisão de produto
separada (like desconto tem impacto de margem/comissão que não deveria
ser decidido implicitamente numa feature de agrupamento).

UI: em vez de uma tela nova, um toggle "Reserva de grupo (vários
quartos de uma vez)" foi adicionado no modal de "Nova reserva" que já
existia (`openNewReservationModal`) - marcar o toggle troca o bloco de
1 quarto por uma lista expansível de blocos (tipo de quarto + cama +
valor, um por linha), com botão "+ Adicionar quarto". Ao salvar, o
JS decide sozinho pra qual endpoint mandar (`/reservations` normal ou
`/reservations/group`) dependendo do estado do toggle - sem duplicar
o modal inteiro só por causa do modo grupo. Reservas com `group_id`
ganham um selo "👥 Parte de um grupo" na listagem principal.

Testado com atenção especial na trava de cama compartilhada - depois
de criar um grupo de 2 quartos, uma tentativa de criar uma reserva
NORMAL (fora do grupo) pra uma das mesmas camas no mesmo período foi
propositalmente testada e falhou como esperado ("Essa cama não está
mais disponível") - prova de que a reserva de grupo não criou um
caminho alternativo mais fraco de validação, é literalmente a mesma
trava contra corrida de sempre. Também testado: grupo vazio (lista de
quartos vazia) rejeitado, grupo inexistente devolve `None`.

### Maturidade de PMS: multi-propriedade (v1.70.0)

Terceiro e último item da leva de maturidade de PMS (Cloudbeds).
Diferente dos dois anteriores, a investigação nesse aqui (agente
Explore, leitura completa de `routes/auth.py`/`database.py`/
`dashboard.html`) trouxe uma virada real: o mecanismo de multi-
propriedade praticamente JÁ EXISTIA, ponta a ponta, publicado em
produção, e nunca tinha sido usado de verdade.

O que já estava lá: `hostel_memberships` já é uma tabela N:N
(usuário↔hostel, não 1:1); `_complete_login()` (`routes/auth.py`) já
trata login de gente com múltiplos hostels de forma diferente de
quem tem só um - cria uma sessão "pending" (`hostel_id=None`) e
devolve `needs_hostel_selection: true` com a lista; `POST /select-hostel`
já existe e já troca o `hostel_id` de uma sessão EXISTENTE (nunca cria
sessão nova) - dá pra "trocar de conta" sem logout; e o `dashboard.html`
já tem a UI inteira pronta: botão `.hostel-mini` na topbar
(`toggleHostelSelector`), dropdown populado por `populateHostelSelector()`
a partir de `session.hostels`, cada opção chamando `switchHostel(hostelId)`.
Consultei o `stayflow.db` direto pra confirmar: zero usuário real (nem
da própria equipe StayFlow) tinha mais de 1 `hostel_membership` ativo
hoje - o mecanismo estava published mas dormindo.

O motivo de nunca ter sido usado: o ÚNICO jeito de uma pessoa ganhar
uma segunda `hostel_membership` era ser CONVIDADA por outro hostel via
Equipe (`routes/team.py`) - não existia nenhum caminho pra alguém, já
logado na própria conta, criar uma propriedade nova pra SI MESMO. Esse
foi o gap real fechado nesta versão - não o mecanismo de troca (que
já estava correto), só a falta de um "criar mais uma".

Decisão de arquitetura: nova função `create_hostel_and_membership_for_user(user_id, ...)`
em vez de tentar reaproveitar/fatiar `create_identity_and_hostel()`
(a função que o `/register` já usa) - ela faz os mesmos 3 `INSERT`s
(hostel, role Admin, `hostel_membership`), só que sem a parte de criar
usuário (reaproveita o `user_id` da sessão já autenticada). Decisão
consciente: `create_identity_and_hostel` já está em produção
protegendo o fluxo de cadastro público - fatiar ela pra "compartilhar"
metade da lógica seria risco desnecessário pra economizar ~15 linhas
de SQL direto, que é basicamente o que a função nova tem.

Nova rota `POST /account/add-hostel` seguiu o MESMO estilo de
checagem manual de sessão que `/select-hostel` já usa (`session.get("session_id")`
+ `get_valid_session`), em vez do decorator `@require_auth` de
`utils/tenant.py` - motivo: esse decorator já EXIGE um `hostel_id` de
tenant resolvido na sessão (401 se não tiver), e `routes/auth.py`
como um todo (register/login/select-hostel/logout/me) já tem seu
próprio jeito manual de lidar com sessão, sem usar aquele decorator
em lugar nenhum - misturar os dois estilos no mesmo arquivo criaria
inconsistência sem ganho real.

UI: em vez de uma tela nova, um botão "+ Adicionar hospedagem" foi
colocado dentro do MESMO dropdown que já existia pra trocar de
hospedagem (abaixo do link de Configurações) - abre um modal simples
(só nome; tipo fica fixo em "lodging" nesta rodada, sem replicar a
cascata completa de categoria de agência do `Register.html` só pra
esse caso secundário) e, ao salvar, já redireciona pra `/app` com a
propriedade nova ativa.

Testado com rigor extra, incluindo o fluxo via Flask test client (não
só função de banco isolada) - simulei o cenário real ponta a ponta:
criar usuário com senha de verdade (`bcrypt`, não texto puro),
logar via `POST /login`, cair no estado `needs_hostel_selection`
(porque o teste já tinha 2 hostels de uma etapa anterior), escolher um
via `/select-hostel`, chamar `/account/add-hostel` e confirmar que a
resposta já vem com a sessão apontando pra hospedagem nova E a lista
`hostels` com 3 itens, e por fim confirmar que `/select-hostel`
continua funcionando pra voltar pro hostel original sem logout -
prova de que a feature nova não quebrou o mecanismo de troca já
existente. Também testado: nome vazio rejeitado tanto na função de
banco quanto na rota (400).

Com essa versão, encerra a leva de 3 itens de maturidade de PMS
iniciada na v1.68.0 (tarifa por temporada, reserva de grupo, multi-
propriedade) - todos os 3 nasceram da mesma pergunta do usuário
("o que fazer pra ficar mais adulto como o Cloudbeds") depois de uma
rodada de pesquisa competitiva ampla que também cobriu Chatty,
Hubtype, respond.io, Darwin AI, Whaticket, Asksuite, HiJiffy e
Runnr.ai - nenhum desses, além do Cloudbeds, tem vertical de
hotelaria de verdade.

### Ponto de funcionário e histórico de ação rastreável (v1.71.0)

Depois da rodada de PMS, usuário mandou mais prints de anúncios pra
pesquisar (Zapia, Cloocker, HighLevel, PXSOL, Prometheo - Whaticket/
Chatty repetidos, ignorados). Ao discutir o que aproveitar dessa
pesquisa, perguntei se o Cloocker (app de controle de ponto/fichaje)
não serviria pra StayFlow - usuário confirmou que sim, e isso puxou
um pedido antigo dele que nunca tinha sido atendido: rastreabilidade
de ação por funcionário. Explicou com um exemplo concreto - camareira
arruma uma cama malfeita, hóspede reclama, o dono quer ter autonomia
de saber exatamente QUEM arrumou aquela cama e A QUE HORAS, sem
desculpa possível.

Antes de desenhar qualquer coisa, investigação (agente Explore,
leitura completa de `staff_shifts`/`tickets`/`beds` em `database.py`)
confirmou os dois gaps eram reais, não achismo:

- **Ponto**: zero infraestrutura. "Escala" (`staff_shifts`) é 100%
  planejamento futuro - o campo `status` nunca sai de `'scheduled'`
  em lugar nenhum do código, não existe nenhum registro de
  comparecimento de verdade.
- **Rastreabilidade**: `mark_bed_cleaned(hostel_id, bed_id)` e
  `set_bed_maintenance(hostel_id, bed_id, under_maintenance)` não
  recebiam nenhum identificador de quem executou a ação - só mudavam
  o status da cama. O sistema de chamados (`tickets`, compartilhado
  por 5 blueprints - cozinha/manutenção/segurança/operações/
  estacionamento) tinha rastreabilidade PARCIAL: sabia quem relatou e
  quem foi DESIGNADO, mas não quem de fato EXECUTOU a resolução (podem
  ser pessoas diferentes) nem guardava histórico de mudanças de status
  intermediárias.

Achado que definiu a arquitetura toda: `routes/scheduling.py::create_shift_route`
já resolvia "quem é o funcionário logado agora" com um padrão pronto -
`get_membership(get_current_user_id(), hostel_id)["membership_id"]`,
usado quando o corpo da requisição não trazia o `membership_id`
explícito (caso de uso "criar turno pra mim mesmo"). Em vez de inventar
um mecanismo novo de identificar o autor de uma ação, esse MESMO padrão
foi replicado em todo lugar novo que precisava saber "quem clicou isso".

**Ponto** (`staff_attendance`): um registro por turno realmente
trabalhado, diferente de `staff_shifts` (que é só o planejado).
`clock_in()` bloqueia bater ponto de novo se já existir um registro
aberto (`clock_out_at IS NULL`) daquele funcionário - evita duas
entradas sem saída no meio. `clock_out()` fecha o registro aberto mais
recente. Sem geolocalização nem biometria - escopo mínimo do que foi
pedido (registro de horário, não vigilância de local).

**Rastreabilidade** (`staff_activity_log`): uma tabela GENÉRICA única
(`entity_type`, `entity_id`, `action`, `detail`) em vez de uma tabela
de log por feature - qualquer módulo novo que precisar de auditoria no
futuro reaproveita a mesma, sem duplicar estrutura. Função central
`log_staff_activity()` - se `membership_id` vier `None` (caminho sem
ator identificado), simplesmente não loga nada, sem quebrar a função
chamadora (log sem autor não serve pro propósito de auditoria mesmo).
Ligada em `mark_bed_cleaned`/`set_bed_maintenance` (ganharam parâmetro
`membership_id`) e nas 3 funções de ticket - `assign_ticket`/
`update_ticket_status`/`resolve_ticket` ganharam `actor_membership_id`
(quem CLICOU a ação, conceito novo e diferente de
`assigned_to_membership_id`, que é pra QUEM foi designado). `tickets`
ganhou coluna `resolved_by_membership_id` como FATO de primeira
classe, não só entrada de log - é o dado que resolve o caso concreto
do usuário (quem de fato resolveu, não só quem foi designado).

Maior superfície de mudança em rotas desta sessão até agora: os 5
blueprints de chamado (`kitchen.py`, `maintenance.py`, `operations.py`,
`parking.py`, `patrimonial_security.py`) tiveram suas rotas de
assign/in-progress/resolve atualizadas pra resolver o
`actor_membership_id` da sessão e repassar adiante - mesma linha de
código (`get_membership(get_current_user_id(), hostel_id)`) replicada
nos 5 arquivos, cada um com uma função auxiliar `_actor_membership_id`
local (não virou helper compartilhado entre arquivos pra não criar
acoplamento entre blueprints de módulos operacionais distintos, que
hoje são deliberadamente independentes uns dos outros).

Nova rota `GET /team/<membership_id>/activity-log` (reaproveitando a
guarda `_membership_in_hostel` que `routes/team.py` já tinha) devolve
ponto + ações combinados - é literalmente o "histórico de cada
funcionário" pedido. UI: botão "Bater ponto" na aba Escala (mostra
status atual: dentro desde HH:MM, ou botão de entrada); botão
"Histórico" em cada card de membro da Equipe, abrindo modal com as
duas listas.

Testado com rigor: banco isolado cobrindo o ciclo completo de ponto
(entrada bloqueando segunda entrada sem saída, saída sem entrada
aberta falhando, histórico correto) e o fluxo completo de ticket
(create → assign → in_progress → resolve, cada etapa gravando o autor
certo em `staff_activity_log` E `resolved_by_membership_id` gravado
corretamente, com o nome do resolvedor vindo via JOIN em `get_ticket`).
Também testado via Flask test client (não só função de banco isolada)
- login real, bater ponto pela ROTA, checar status, bater saída,
consultar o histórico combinado pela rota real e confirmar que reflete
exatamente os eventos esperados.

Fora de escopo, deliberado: geolocalização/biometria no ponto, alertas
automáticos de atraso/falta, edição de um registro de ponto já feito
(esqueceu de bater saída, por exemplo), e uma tela dedicada de
"chamados resolvidos" dentro dos 5 módulos de ticket - o dado já
existe e já aparece no histórico do funcionário; uma tela dedicada por
módulo fica pra depois, só se pedida de verdade (nenhum desses 5
módulos tem hoje nem uma listagem de chamados JÁ resolvidos, só os
abertos - construir isso seria escopo novo, não parte do pedido atual).

### Integração Tokko Broker - etapa 1 de 2 (v1.72.0)

Depois de mais uma rodada de pesquisa competitiva (Bitrix24, ClickUp,
entre outros), usuário pediu explicitamente pra retomar a fila de
features e apontou pra começar pelos itens mais antigos ainda
pendentes: matching de imóvel por preferência do comprador e
integração com o Tokko Broker (item 13 e 14, inspirados na Waichatt,
concorrente vertical em imobiliária). Escopo restrito o tempo todo a
`account_kind='agency'` + `agency_category='imobiliaria'` - nunca
aparece pra hospedagem nem pra outras categorias de agência.

Investigação (agente Explore + pesquisa da API pública real do Tokko
Broker, developers.tokkobroker.com) confirmou terreno greenfield -
zero menção a "tokko"/imóvel/"real estate" em código antes desta
versão - e revelou que a arquitetura certa é mais simples do que a da
Nuvemshop: o Tokko não usa OAuth, usa uma API KEY única por
imobiliária, gerada em "Mi Empresa → Permisos" no painel deles e
colada manualmente nas Configurações - sem redirect, sem state
anti-CSRF, sem token que expira. Fluxo é só leitura (GET) - StayFlow
puxa o catálogo sob demanda, nunca recebe webhook nesse fluxo básico.

Decisão de reaproveitamento: `portfolio_items` já é genérica e já tem
sync externo pronto (usado até agora só pela Nuvemshop) - índice único
PARCIAL `(hostel_id, source, external_id)` (`WHERE external_id IS NOT
NULL`) + `upsert_portfolio_item_from_external()`. Reaproveitado 100%
sem duplicar lógica, agora também chamado com `source='tokko'`. Como a
tabela genérica não tem campo nenhum específico de imóvel (operação,
localização, quartos, m²), criada tabela companheira nova
`real_estate_details` (1:1 via `portfolio_item_id`) - mantém
`portfolio_items` limpa pra outros tipos de item (passeio, aluguel de
bike) que não têm esses campos.

**Bug real encontrado e corrigido de brinde, fora do pedido original**:
ao escrever o teste isolado do sync do Tokko (mock da resposta da API,
sem chamada de rede real), o insert em `upsert_portfolio_item_from_
external()` falhava com `sqlite3.OperationalError: ON CONFLICT clause
does not match any PRIMARY KEY or UNIQUE constraint`. Investigação (
reprodução isolada via `python3 -c "..."` direto no `sqlite3`, versão
3.50.4) confirmou: quando o índice único é PARCIAL (tem `WHERE`), o
SQLite exige que a cláusula `ON CONFLICT(...)` repita EXATAMENTE o
mesmo `WHERE` pra ser reconhecida como alvo de conflito válido - só
declarar as colunas não basta. A função, em produção desde a
integração Nuvemshop, tinha `ON CONFLICT(hostel_id, source,
external_id) DO UPDATE` sem o `WHERE external_id IS NOT NULL` - ou
seja, TODO insert por essa função (não só quando havia conflito de
verdade) quebrava em tempo de PARSE da declaração SQL, não em tempo de
execução condicional. Isso nunca tinha sido detectado porque nenhum
teste isolado tinha exercitado esse caminho de código antes - a
Nuvemshop está em produção, então ou os merchants reais nunca bateram
esse caminho de forma a expor o erro visivelmente, ou o erro estava
sendo engolido silenciosamente em algum ponto acima. Corrigido
adicionando o `WHERE external_id IS NOT NULL` na cláusula `ON
CONFLICT`, replicando o índice; suite de teste isolado do Tokko
re-executada do zero depois da correção, confirmando sucesso.

Novo `services/tokko_service.py`: `list_properties(api_key)` (GET puro
na API real do Tokko, nunca levanta exceção - mesmo princípio
defensivo dos outros services de integração externa) e
`sync_tokko_properties(hostel_id, api_key)` (itera o catálogo, chama o
upsert genérico pra base + `upsert_real_estate_details()` novo pros
campos estruturados). Nota registrada em comentário no próprio arquivo:
os nomes de campo usados na resposta da API (`operations`,
`room_amount`, `total_surface` etc.) seguem a documentação pública mas
nunca foram testados contra uma resposta real, porque nenhuma
imobiliária conectou uma chave de verdade ainda - mesma categoria de
pendência já registrada pra outras integrações externas (WhatsApp
Embedded Signup, Mercado Pago produção).

Novas rotas em `routes/settings.py` (mesmo arquivo da Nuvemshop):
`GET/POST/DELETE /settings/tokko` (ler/salvar/remover a chave) e `POST
/settings/tokko/sync` (sincronização manual sob demanda - sem cron
nesta rodada). Nova guarda `_require_real_estate_agency(hostel_id)`,
espelhando `_require_agency()` de `routes/portfolio.py` mais a
checagem extra de `agency_category == 'imobiliaria'`.

UI: novo card "Tokko Broker" em Configurações, com chave de API,
status de conexão, "Sincronizar agora" e desconectar - mesmo padrão
visual e de `fetch` já usado pelo card da Nuvemshop logo acima dele.
Esse card é o primeiro precedente real de gating por `agency_category`
no frontend: `applyAccountKindVisibility()`, que antes só olhava
`account_kind`, ganhou um segundo parâmetro (`agencyCategory`) e um
novo atributo `data-required-agency-category` no HTML - documentado
aqui pra ser reaproveitado se surgir uma próxima categoria de agência
com feature própria. Descoberta lateral durante a inserção de i18n:
várias chaves de configuração de integração da Nuvemshop/Mercado Pago
(`settings.nuvemshop.title`, `.disconnectConfirm`,
`settings.mercadopago.title`) nunca tinham sido adicionadas ao
dicionário - sempre mostraram o fallback em português pra qualquer
idioma selecionado. Gap pré-existente, não catálogo desta versão,
deliberadamente não corrigido aqui pra não misturar escopo.

17 chaves i18n novas (`settings.tokko.*`) nos 11 idiomas, ancoradas em
`settings.facebook.connectBtn` (única chave confirmada presente nas 11
línguas antes da inserção) - `tools/check_i18n_parity.py` confirmando
1.093→1.110 chaves.

Etapa 2 (matching de imóvel por preferência do comprador, reaproveitando
`opportunities.suggested_partner_item_id` - já calculado desde a
v1.57.0 mas nunca renderizado em lugar nenhum do `dashboard.html`, dado
morto até agora mesmo pro caso antigo de tour) fica pra versão
seguinte, já com o desenho definido no plano aprovado.

### Matching de imóvel por preferência do comprador - etapa 2 de 2 (v1.73.0)

Fechamento dos itens 13/14 da fila, iniciados na v1.72.0 com a
integração Tokko Broker. Novo branch em `services/decision_engine.py`:
quando `account_kind == "agency"` e `agency_category == "imobiliaria"`,
os candidatos de matching vêm de `get_own_active_portfolio_items()` (o
PRÓPRIO catálogo da imobiliária, já criado na v1.72.0) - caso inverso
do matching de tour que já existia desde a v1.57.0 (hospedagem
oferecendo catálogo de uma agência PARCEIRA terceira pro próprio
hóspede). O prompt novo (`own_items_block`) inclui preço, localização,
quartos e tipo de operação (venda/aluguel) na lista de candidatos - o
bloco de tour deliberadamente omite preço, mas pra imóvel esses dados
são o cerne do match. Reaproveitado 100% o mesmo campo
`suggested_partner_item_id` e a MESMA validação anti-alucinação (o id
que a IA sugere só é aceito se estiver de verdade no set de candidatos
que foi mandado no prompt) - dispara quando `intent == "booking"`, a
classificação mais próxima que a IA já tem pra "esse lead quer fechar
negócio nisso", já que o motor de intents é genérico entre verticais
(booking/tour/upsell/human_help/follow_up/general).

**Achado que corrigiu uma premissa errada do plano original**: antes de
escrever qualquer UI nova, fui conferir onde ficava a renderização de
`suggested_partner_item_id` no Opportunity Center - o plano (escrito na
sessão anterior, antes da compactação) afirmava que esse campo "nunca
era renderizado em lugar nenhum do `dashboard.html`", calculado desde a
v1.57.0 mas invisível. Investigação nova mostrou que isso é falso: a
renderização SEMPRE existiu, só que em `assets/js/stayflow-live.js`
(`opportunityRowHtml()` pra tabela, `updateOpportunitiesPrioritySidebar()`
pra caixa "Mais importantes") - um arquivo carregado normalmente pelo
`dashboard.html` (`<script src="assets/js/stayflow-live.js">`), mas que
a investigação de planejamento anterior não tinha aberto (só vasculhou
`dashboard.html` de verdade). Antes de construir de novo uma feature
que já existia, confirmei via `git log` que o commit original
(`bf3cbce`) já trazia a renderização completa desde a v1.57.0. Lição
registrada: uma alegação herdada de um plano anterior é uma hipótese
congelada no tempo, não um fato verificado - vale re-conferir contra o
código atual antes de agir em cima dela, mesmo quando o plano já foi
aprovado.

Com a renderização confirmada como já pronta, o trabalho de UI ficou
restrito a ajustar a COPY pro caso novo: a mesma função genérica
mostrava sempre "Sugestão: {item} via {agency}" com botão "Oferecer
parceiro" - correto pro caso de tour (o vendedor É um parceiro
terceiro de verdade), mas sem sentido pro caso de imóvel (o vendedor é
a PRÓPRIA imobiliária, "via Imobiliaria X" ficaria redundante/confuso
chamando a própria conta de parceiro dela mesma). Nova função
`isOwnCatalogSuggestion()` (verifica `window.STAYFLOW_SESSION.account_kind
=== "agency" && agency_category === "imobiliaria"` - suficiente porque
a arquitetura já garante que os dois casos são mutuamente exclusivos)
ramifica a copy: vira "Sugestão: {item}" + botão "Oferecer imóvel" só
pro caso de catálogo próprio.

**Segundo bug real encontrado e corrigido, só percebido ao testar o
fluxo de cobrança ponta a ponta pro caso novo**: `routes/guest_charges.py`,
na criação de uma cobrança `charge_type='partner_item'`, sempre setava
`referring_hostel_id = hostel_id` (a hospedagem/agência que chamou a
rota) incondicionalmente - correto quando o vendedor real é uma agência
DIFERENTE (caso de tour, onde isso vira uma linha em
`partner_referral_ledger` registrando o que a StayFlow deve pra
hospedagem que indicou a venda). Mas no caso novo de imobiliária
oferecendo o PRÓPRIO catálogo, vendedor (`item["hostel_id"]`) e chamador
(`hostel_id` da sessão) são a MESMA conta - gravar `referring_hostel_id`
nesse caso criaria uma "comissão de indicação" da imobiliária pra ela
mesma, poluindo o razão de repasses com lançamentos sem sentido
econômico (e potencialmente pagáveis via `mark_partner_referral_paid_out`,
"pagando" a conta pra ela mesma). Corrigido: `referring_hostel_id` só é
setado quando `seller_hostel_id != hostel_id` de verdade. Testado em
banco isolado confirmando os dois comportamentos lado a lado (cobrança
self-catalog não grava `referring_hostel_id`/comissão; cobrança de
parceiro terceiro genuíno continua gravando exatamente como antes,
sem regressão).

De brinde, ao inserir as chaves i18n novas, descoberto que 2 chaves já
usadas no código desde a v1.57.0 (`opportunities.partnerSuggestion`,
`opportunities.offerPartnerBtn`) nunca tinham entrado em nenhum dos 11
dicionários - sempre mostraram só o fallback em português via `T(key,
fallback)`, independente do idioma selecionado pelo usuário. Corrigido
junto com as 2 chaves novas (`opportunities.ownItemSuggestion`,
`opportunities.offerOwnItemBtn`) - `tools/check_i18n_parity.py`
confirmando 1.110→1.114 chaves.

Testado em banco isolado (banco isolado + mock de `analyze_with_ai`,
sem chamar a API de verdade): sugestão válida (id dentro do set de
candidatos enviado) aceita e salva; id "alucinado" pela IA (fora do
set) rejeitado, salva `null`; conta `lodging` nunca aciona o branch de
imóvel mesmo que a IA "sugira" um id válido de outro contexto; intent
diferente de `booking` (ex: `upsell`) não aciona o matching de imóvel
mesmo com candidatos disponíveis. Encerra a leva Tokko Broker + matching
de imóvel iniciada na v1.72.0.

### Tela de chamados resolvidos nos 5 módulos operacionais (v1.74.0)

Com a fila numerada zerada (itens 1-19 todos shippados), usuário
perguntou "que nos falta?" - resposta organizada em 4 grupos (gaps de
produto não atacados, decisões deliberadamente adiadas, bloqueadores
externos, pendências de negócio/GTM). Na sequência, pediu pra atacar
em ordem de prioridade. Ordem definida por mim, do menor risco/maior
valor pro maior esforço - primeiro item: a tela de "chamados
resolvidos" nos 5 módulos operacionais (Cozinha/Manutenção/Segurança
patrimonial/Estacionamento/Tarefas), porque o dado já existia desde a
v1.71.0 (`resolved_by_membership_id`/`resolved_at`) e na época ficou
registrado como "fora de escopo deliberado, fica pra se for pedida" -
ninguém tinha pedido até agora.

Investigação (agente Explore) confirmou a arquitetura: `tickets` é UMA
tabela genérica compartilhada pelos 5 módulos, distinguida por `type`
(`kitchen_order`/`maintenance`/`security_incident`/`valet_request`/
`task`). Já existia `get_open_tickets(hostel_id, ticket_type=None)`
(status IN open/assigned/in_progress) mas nenhuma função equivalente
pra resolvidos. `get_ticket(hostel_id, ticket_id)` já fazia o JOIN
certo pra trazer `resolved_by_name` (LEFT JOIN `hostel_memberships` →
`users`) - reaproveitado exatamente esse JOIN na função nova. Os 5
blueprints são deliberadamente independentes uns dos outros desde a
v1.71.0 (cada um duplica seu próprio `_actor_membership_id` "pra não
criar acoplamento entre módulos operacionais distintos") - mas essa é
uma convenção de BACKEND; no FRONTEND já existem helpers genéricos
compartilhados entre os 5 módulos (`urgencyPillClass`,
`ticketStatusLabel`), então uma função JS genérica pros 5 é consistente
com o padrão existente - só o backend ficou com uma rota fina por
blueprint, sem função/serviço compartilhado entre eles.

Nova `get_resolved_tickets(hostel_id, ticket_type=None, limit=20,
offset=0)` em `database.py`, paginada como `get_opportunities_list`
(retorna `{items, total}`) - decisão consciente de NÃO copiar o padrão
sem paginação de `/team/<id>/activity-log` (histórico pessoal de um
funcionário, naturalmente limitado): chamados resolvidos acumulam sem
limite ao longo da vida inteira da hospedagem, pedem paginação de
verdade. 5 rotas novas (`GET .../resolved`, uma por blueprint), cada
uma thin, reaproveitando os mesmos decorators (`require_permission`/
`require_plan_feature`) e o mesmo parsing de `limit`/`offset` com
clamp que `routes/opportunities.py` já usava.

UI: pill switcher "Abertos"/"Resolvidos" em cada um dos 5 painéis,
reaproveitando o componente visual `.ops-tabs`/`.ops-tab` que já existe
pra alternar entre os próprios módulos (Tarefas/Cozinha/Manutenção/
Segurança/Estacionamento) - não foi criado CSS novo. Cada painel de
histórico tem 4 colunas fixas (local, descrição, resolvido por,
resolvido em) iguais pros 5 módulos, sem coluna de ação (é consulta,
não tem o que fazer com um chamado já resolvido) + botão "Mostrar
mais" no mesmo padrão do Opportunity Center. Em vez de 5 pares de
funções JS quase idênticas, uma função genérica só
(`switchTicketView(moduleKey, view)` + `loadResolvedTickets(moduleKey)`),
configurada por um dict `TICKET_MODULE_CONFIG` com o endpoint e os ids
de DOM de cada módulo - reaproveita `escapeHtml` (já existe desde o
começo do dashboard) e `opportunityDateLabel` (já existe em
`stayflow-live.js`) pra formatação, sem duplicar helper nenhum.

Testado em banco isolado: 2 hospedagens (uma delas só pra provar
isolamento de tenant), chamados dos 5 tipos criados e resolvidos
(menos um de manutenção, deixado aberto de propósito) - confirmado que
`get_resolved_tickets` só traz os resolvidos, nunca o aberto;
`resolved_by_name` populado certo via JOIN; filtro por `ticket_type`
funcionando; paginação com `limit`/`offset` sem sobreposição entre
páginas; e isolamento de tenant nos dois sentidos (hostel B nunca vê
chamado do hostel A e vice-versa). Also testado via Flask test client
- login real, as 5 rotas novas respondendo 200 com sessão de conta
"comp" (billing cortesia, libera `hostel_has_plan_feature` sem precisar
reconstruir a configuração real de planos/add-ons só pro teste) e o
formato `{items, total}` batendo com o total esperado em cada uma.

6 chaves i18n novas (`tickets.tabOpen`, `tickets.tabResolved`,
`tickets.resolvedByLabel`, `tickets.resolvedAtLabel`,
`tickets.resolvedEmptyTitle`, `tickets.resolvedEmptyDesc`) nos 11
idiomas - `tools/check_i18n_parity.py` confirmando 1.114→1.120. Erro
próprio corrigido antes de publicar: a primeira tradução em espanhol
saiu com a palavra errada ("chamados", português, em vez de
"solicitudes") - pego na revisão manual antes do commit.

### Diária de fim de semana (sexta/sábado) por modalidade (v1.75.0)

Segundo item da leva pós-fila-zerada, na mesma ordem de prioridade
definida na v1.74.0. Estende a tarifa por temporada (`rate_rules`,
v1.68.0) - que já resolve "preço diferente num intervalo de DATAS"
(ex: alta temporada de verão) mas não tinha nenhuma noção de dia da
semana. Caso de uso real e bem comum em hotelaria: cobrar mais nas
noites de sexta/sábado (pico de demanda de lazer) o ano inteiro, sem
precisar cadastrar uma regra de temporada pra cada final de semana.

Investigação (agente Explore) confirmou o ponto de inserção ideal:
`calculate_reservation_amount(hostel_id, room_type_name, checkin_date, checkout_date)`
já soma o preço NOITE A NOITE com um `while` que anda dia a dia como
objeto `date` (`current`) ANTES de virar string pra comparar contra
`rate_rules` - `current.weekday()` já estava ali disponível de graça,
sem precisar reestruturar nada. Confirmado também, via grep de
`weekday|dia_semana|strftime|%w` em `database.py`/`routes/rooms.py`,
que não existia ABSOLUTAMENTE NENHUM conceito de dia da semana em
lugar nenhum do motor de preço até agora - terreno greenfield de
verdade dentro de uma função já madura.

Decisão de arquitetura: nova coluna `room_categories.weekend_price_per_night`
(REAL, nullable), não uma tabela nova - mesma filosofia opt-in que
`price_per_night` já usa (`NULL` = recurso desligado, comportamento
idêntico a antes da coluna existir). "Fim de semana" definido como
sexta+sábado, fixo nesta rodada (convenção padrão de lazer/hotelaria) -
não configurável, mesmo espírito minimalista de "ponto de partida
simples" já usado em outras decisões do produto (comissão de indicação
fixa em 20%, regra de temporada sem variação por dia quando foi criada
na v1.68.0).

Regra de precedência por noite, do mais específico pro mais genérico:
1) `rate_rule` de temporada que cobre a data (inalterado - uma regra
tipo "Réveillon" cadastrada como temporada continua podendo sobrepor
um sábado específico) → 2) diária de sexta/sábado, se configurada e a
noite cair nesses dois dias → 3) diária normal (`price_per_night`),
fallback de sempre. Implementado calculando o preço-base da noite
(`weekend_price_per_night` ou `price_per_night`, conforme o dia) ANTES
do loop existente de `rate_rules`, que continua rodando por cima
exatamente como já rodava - o loop de temporada nunca precisou saber
que dia da semana é, só continua podendo sobrescrever o que quer que
tenha sido calculado antes dele.

Zero mudança nos 3 pontos de chamada de `calculate_reservation_amount`
(`create_reservation_record`/`create_reservation_from_chat`/
`create_reservation_from_channel`) - a data de check-in/check-out já
chegava neles do jeito de sempre, o dia da semana é derivado
internamente na função, não precisa de parâmetro novo em lugar nenhum.

UI: campo novo "Diária de sexta/sábado (opcional)" no modal de edição
de modalidade (`editCategoryUI`), logo abaixo do campo de diária
normal - MESMA rota `PATCH /room-categories/<id>` já existente, sem
rota nova (é um atributo da categoria, diferente de `rate_rules` que é
uma lista separada com suas próprias rotas). `list_room_categories` e
`update_room_category` estendidas pra incluir a coluna nova, replicando
com cuidado o MESMO padrão de coerção que `price_per_night` já usava:
campo vazio/ausente no PATCH vira `NULL` (desliga o recurso), não
"mantém o valor anterior" - achado importante ao escrever o teste
isolado: minha primeira tentativa de teste chamou `update_room_category`
passando só `weekend_price_per_night`, sem repassar `price_per_night`,
e isso zerou a diária normal da categoria (mesmo comportamento que o
código já tinha pra `price_per_night` antes desta mudança) - não é um
bug introduzido agora, é o padrão pré-existente da função, e o
frontend real (`submitEditCategory`) já sempre reenvia TODOS os campos
juntos a cada salvamento, então nunca dispara esse caso na prática;
só precisei corrigir o teste pra refletir isso.

Testado em banco isolado: categoria sem `weekend_price_per_night`
configurado se comporta EXATAMENTE como antes desta versão
(retrocompatibilidade); uma estadia terça→domingo soma corretamente
noite a noite (3 noites normais + 2 de fim de semana, sexta E sábado
contam); uma `rate_rule` de temporada cadastrada sobre o mesmo sábado
vence a diária de fim de semana (precedência respeitada); domingo
explicitamente NÃO entra na regra (só sexta/sábado); desligar o campo
(vazio) volta a `NULL`. Testado também via Flask test client: `PATCH
/room-categories/<id>` grava o valor e `list_room_categories` lê de
volta certinho. 1 chave i18n nova nos 11 idiomas (`tools/check_i18n_parity.py`
confirmando 1.120→1.121).

### Desconto automático em reserva de grupo (v1.76.0)

Terceiro item da leva pós-fila-zerada, mesma ordem de prioridade. A
reserva de grupo (v1.69.0) nasceu com uma decisão explícita registrada
no próprio código: "Sem motor de desconto - cada quarto mantém seu
preço normal". Era um gap conhecido desde a criação, fica pra "depois,
se o percentual fixo não bastar como incentivo" - ficou sem incentivo
nenhum até agora. Caso de uso real: excursão/evento fechando vários
quartos de uma vez normalmente justifica um desconto pro grupo todo, e
a única forma de simular isso hoje era a equipe digitar manualmente um
valor menor em cada quarto, um por um, sem nenhum registro de que
aquilo era um desconto de verdade (nem quanto).

Investigação (agente Explore) mapeou o gancho certo:
`create_group_reservation` já chama `create_reservation_record` uma
vez por quarto, e essa função já aceita um `amount` pronto que, quando
informado, pula o próprio `calculate_reservation_amount` - o mesmo
mecanismo que já existia pra permitir digitar um valor manual serve
perfeitamente pra aplicar um desconto por cima do valor (calculado OU
manual) antes de repassar adiante. Confirmado também que
`reservations.amount` sempre foi o valor FINAL cobrado em qualquer
cenário do sistema - nunca existiu um conceito de "preço de tabela vs.
preço cobrado" separado em lugar nenhum das reservas - então gravar o
valor já descontado ali é consistente com a convenção existente, não
introduz uma ideia nova. E confirmado via grep (`discount|desconto|
coupon|cupom` em `database.py`/`routes/`) que o único resultado eram
os comentários documentando a AUSÊNCIA do recurso - terreno greenfield
de verdade.

Decisão de arquitetura: desconto PERCENTUAL, digitado pelo staff na
hora de criar o grupo (não uma regra automática por tamanho de grupo,
tipo "3+ quartos ganham 5% sozinho") - mesmo espírito minimalista já
usado noutras decisões do produto (comissão de indicação fixa em 20%,
tarifa por temporada sem variação por dia quando foi criada). Nova
coluna `reservation_groups.discount_pct` (nullable) guarda só o
REGISTRO de qual desconto foi usado, pra auditoria/exibição - não
participa de cálculo nenhum na leitura, porque o valor já sai
descontado e gravado em cada `reservations.amount`. `create_group_reservation`
valida o percentual (0 a 100, senão `ValueError`) e aplica sobre CADA
quarto: primeiro resolve o valor do jeito que já resolvia (manual OU
`calculate_reservation_amount`), depois multiplica por
`(1 - discount_pct / 100)` - o desconto vale igual pros dois casos,
sem tratamento especial pra quando o valor veio digitado à mão.

Achado que virou trabalho extra necessário, não escopo por conta
própria: a investigação revelou que NADA no sistema soma os quartos de
um grupo em lugar nenhum hoje - nem `get_reservation_group` (devolve a
lista crua), nem o modal de criação (nunca mostra total nenhum antes
de enviar), nem a listagem de reservas (cada linha mostra só o valor
daquele quarto, o badge "👥 Parte de um grupo" é puramente visual, sem
nenhum total agregado em lugar nenhum). Sem fechar esse gap mínimo, o
desconto teria o mesmo destino do `suggested_partner_item_id` da
v1.57.0: calculado certinho por baixo dos panos, mas invisível pra
quem realmente usa o produto - lição da v1.73.0 reaplicada aqui de
propósito. Fechado com o menor esforço possível: `get_reservation_group`
ganhou um `group_total` computado (soma em Python dos valores já
retornados, sem SQL novo) e o modal de Nova Reserva passou a buscar
esse resumo logo depois de criar um grupo com sucesso, mostrando o
total (com o desconto já aplicado) numa confirmação simples antes de
fechar - em vez de só fechar e atualizar a tela sem feedback nenhum,
como acontecia até agora.

Testado em banco isolado: grupo sem `discount_pct` continua idêntico a
antes desta versão (retrocompatibilidade); grupo com desconto sobre
valor calculado automaticamente (200 → 180 por quarto com 10%); grupo
com desconto sobre valor digitado manualmente (500 → 400 com 20%,
provando que o desconto não faz distinção entre as duas origens);
percentual inválido (negativo, acima de 100, não numérico) sempre
levanta `ValueError`. Testado também via Flask test client: `POST
/reservations/group` com desconto seguido de `GET /reservations/group/<id>`
confirmando que o `group_total` bate com a conta esperada. 4 chaves
i18n novas nos 11 idiomas (`tools/check_i18n_parity.py` confirmando
1.121→1.125).

### Alertas automáticos de atraso/no-show (v1.77.0)

Quarto item da leva pós-fila-zerada. Hoje, quando um hóspede não
aparece no dia da chegada, ninguém é avisado - a equipe só descobre se
alguém lembrar de olhar o Mapa de Quartos ou a lista de Reservas.

Investigação (agente Explore) trouxe 3 achados que mudaram
completamente a expectativa de escopo do que ia ser construído:

1. **`no_show` já era um status válido de `reservations`, com UI/i18n
   completos** - dropdown de status, pill vermelho, até um KPI
   (`kpiNoShow`) já contando quantos. A equipe já consegue marcar
   manualmente hoje. Isso mudou o objetivo real: não era "criar o
   conceito de no-show", era "avisar proativamente que uma reserva
   está atrasada", deixando a decisão de marcar (ou não) com quem
   trabalha no balcão - eles podem saber de algo que o sistema não sabe
   (hóspede ligou avisando que ia atrasar, por exemplo).
2. **A condição de detecção já existia e já era usada** - o bloco
   "arrival" de `GET /operations` (`routes/operations.py`) já filtra
   exatamente `checkin_date = hoje AND status != 'cancelled' AND
   checked_in_at IS NULL` pra mostrar um alerta na tela. Só que é
   PASSIVO: só aparece se alguém abrir a página naquele momento. Não
   tem hora de chegada esperada guardada em lugar nenhum, só a data.
3. **A StayFlow já tem um scheduler funcionando em produção** - achado
   mais importante pra moldar a arquitetura. Não existe nada de
   APScheduler, cron, ou um serviço de worker separado no Render (sem
   `render.yaml`, deploy é um único Web Service via `Procfile`, 3
   workers do gunicorn). Mas `app.py` já registra DOIS laços em
   background há tempo - `threading.Thread` simples com `while True` +
   `time.sleep`, um pros alarmes de compromisso da Prospecção (a cada
   60s) e outro pra expirar trial de billing vencido (a cada hora).
   Como os 3 workers do gunicorn rodam esse código em paralelo (cada
   worker é um processo Python separado, cada um importa `app.py` e
   registra as próprias threads), a deduplicação é resolvida no banco:
   uma tabela de "quem já disparou isso" com `INSERT OR IGNORE` +
   checar `cursor.rowcount` - só quem ganha a inserção manda a
   notificação de verdade, os outros desistem sem precisar de lock
   nenhum. Esse padrão já testado e rodando em produção foi clonado
   diretamente, sem inventar nada novo.

Decisão de arquitetura mais importante: **só alerta, nunca marca
`no_show` sozinho** - mesmo espírito conservador já usado no Billing
("bloqueio de acesso por inadimplência... só bookkeeping, status muda
mas nenhuma rota trava"). Automação que muda dado do hóspede sem
supervisão humana é um risco desnecessário aqui - o pior cenário de só
alertar é a equipe ignorar uma notificação; o pior cenário de
auto-marcar seria um hóspede chegando tarde à noite já rotulado
"no-show" por engano.

Horário de corte fixo em 18h (fuso `America/Argentina/Mendoza`, mesmo
fuso único hardcoded que `services/lead_alarm_service.py` já usa - sem
conceito de fuso por hospedagem em lugar nenhum do sistema hoje) - não
configurável por hospedagem nesta rodada, mesmo espírito minimalista
já repetido em outras decisões do produto (tarifa de fim de semana
fixa em sexta/sábado, comissão de indicação fixa em 20%). Novo
`services/no_show_alert_service.py::check_late_arrivals(now=None)` -
só roda a query de verdade quando a hora local for >= 18h; busca
reservas pendentes de TODAS as hospedagens de uma vez (mesmo espírito
de `get_due_lead_alarms`, que também não itera hostel por hostel);
pra cada uma, tenta reivindicar via `claim_late_arrival_alert`
(nova tabela `late_arrival_alerts_fired`, UNIQUE em `reservation_id`)
e só manda o push se ganhar a corrida. O parâmetro `now` é injetável
de propósito - sem isso, testar a borda exata do horário de corte
dependeria do relógio real da máquina rodando o teste, uma fragilidade
desnecessária.

Novo laço `_late_arrival_alert_loop()` registrado em `app.py`, mesmo
padrão dos outros dois, mas com intervalo de 15 minutos (900s) - mais
espaçado que os 60s dos alarmes de compromisso de propósito, porque
esse alerta não precisa de precisão de minuto, é um lembrete de "hoje
ainda não chegou", não um horário exato disparando na hora certa.

Novo tipo de notificação push `late_arrival`, default LIGADO (mesmo
grupo de `reservation`/`opportunity` - não é ruidoso tipo
`chat_message`, que dispara por mensagem). Registrar um tipo de
notificação novo direito exige tocar em 5 lugares pra manter
consistência com os que já existem: lista default do backend
(`_DEFAULT_PUSH_NOTIFICATION_TYPES`), checkbox nova em Configurações →
Notificações, o array `defaultPushTypes` e o mapa
`pushTypeCheckboxIds` no JS, e a chave i18n do rótulo do checkbox nos
11 idiomas - nenhum atalho tomado, os 5 lugares foram atualizados.

Testado em banco isolado com `now` injetado (sem depender do relógio
real): antes das 18h, a função não dispara nada e nem tenta reivindicar
nenhuma reserva (confirma que o horário de corte é respeitado antes de
qualquer efeito colateral); depois das 18h, dispara exatamente pras
reservas realmente pendentes, uma por hospedagem, testado com 2
hospedagens diferentes recebendo cada uma seu próprio push; reserva já
com `checked_in_at` preenchido ou `status` `cancelled`/`no_show` nunca
entra na lista, confirmado nos dois casos; rodar a função de novo
depois de já ter disparado não manda push nenhum de novo (dedup via
claim funcionando). `python -c "import app"` confirmando que o novo
laço em background não quebra o startup. 1 chave i18n nova nos 11
idiomas (`tools/check_i18n_parity.py` confirmando 1.125→1.126).

Fora de escopo deliberado: marcar `no_show` automaticamente (decisão
continua manual, de propósito), horário de corte configurável por
hospedagem, mais de um alerta por reserva ao longo do dia, e alerta de
check-out atrasado (hóspede que não saiu na data esperada) - "no-show"
é especificamente sobre não ter chegado, checkout atrasado é um
problema diferente, fica pra outra rodada se pedido.

### Comissão em faixas pro programa de indicação (v1.78.0)

Quinto item da leva pós-fila-zerada. Antes de programar qualquer
coisa, o usuário fez uma pergunta de negócio ("você acha que 20 é um
bom número?"), o que puxou uma conversa maior: expliquei que 20%
recorrente é generoso pro padrão de programas de afiliado SaaS
(15-30% é a faixa normal), mas que sendo FIXO não recompensa quem traz
mais volume, diferente do modelo em faixas da Aoki que inspirou o
programa originalmente. Sugeri uma estrutura de 3 faixas
(1-2/3-5/6+ indicações ativas = 20/25/30%), recalculada pra frente
(nunca retroativa) - o usuário perguntou detalhes de como a comissão
já funciona hoje (só sobre mensalidade, nunca sobre comissão de
passeio; recorrente vitalício, sem prazo) antes de aprovar.

No meio do planejamento, o usuário pediu uma conta hipotética de custo
vs. receita por hotel (quanto custa de IA/Mercado Pago vs. quanto
sobra de margem) - respondida à parte, sem mexer em código, deixando
claro que os números de IA/API eram estimativa, não confirmados nos
extratos reais dele.

Investigação (agente Explore) confirmou que a arquitetura já favorecia
a mudança sem migração nenhuma: `subscription_referral_ledger.commission_pct`
sempre foi gravado POR LINHA (não uma referência a uma constante
global) - cada lançamento já era auto-descritivo, só precisava mudar o
que se CALCULA na hora do lançamento. O ponto exato já resolvia
`referring_partner_id` antes de montar a comissão
(`_process_authorized_payment_notification`, `mercadopago_billing_webhook.py`) -
só trocar a constante fixa por uma função ali. `billing.status == 'active'`
já era o único status que significa "pagando de verdade agora" -
exatamente o status que o próprio webhook acabou de setar pro hostel
que pagou, então contar "quantos hostels esse parceiro tem ativos
agora" inclui coerentemente quem acabou de pagar.

Nova `SUBSCRIPTION_REFERRAL_COMMISSION_TIERS` (lista ordenada de
limiar/percentual) + `resolve_subscription_referral_commission_pct()`
+ `count_active_referrals_for_partner()` (mesmo JOIN de
`get_hostel_referral_stats`, só filtrado e contado em vez de listado)
em `database.py`. `get_subscription_referral_summary()` ganhou
`active_referral_count`/`current_tier_pct` por parceiro (calculado em
Python, poucas dezenas de parceiros no máximo) - sem isso ninguém
conseguiria explicar por que um lançamento saiu numa % e outro noutra.
Painel "Indicações" (`admin.html`, Financeiro) ganhou 2 colunas novas
mostrando isso.

Testado em banco isolado: fronteiras exatas das 3 faixas (0-2→20%,
3-5→25%, 6+→30%). Testado também ponta a ponta pelo webhook de
verdade, com `mercadopago_billing_service.get_authorized_payment`
mockado (mesmo padrão já usado pro Tokko, sem chamada de rede real):
2 pagamentos em sequência pro mesmo parceiro - primeiro com o parceiro
tendo poucas indicações ativas (20%), depois sobe pra 6 indicações
ativas antes do segundo pagamento (30%) - confirmando que o SEGUNDO
lançamento reflete a faixa nova, mas o PRIMEIRO continua intocado em
20% no razão, provando que a mudança de faixa nunca é retroativa.
2 chaves i18n novas no `ADMIN_I18N` (252→254).

### Auto-cadastro público de parceiro de indicação externo (v1.79.0)

Surgiu direto da criação de um post de Instagram sobre o programa de
indicação (o próprio usuário pediu pra fazer o post, discutimos vários
ângulos possíveis - decidiu pela "chamada pra virar indicador" em vez
de mostrar feature de produto). No meio da criação do post, o usuário
perguntou como um indicador de fato se conecta à StayFlow hoje -
expliquei que existem dois caminhos: quem já é cliente tem link pronto
no próprio dashboard, mas quem NÃO é cliente (o público real do post)
depende do Caio cadastrar manualmente pelo `admin.html` toda vez. Ele
percebeu na hora que isso não escalava se o post desse volume, e pediu
pra construir o auto-cadastro ali mesmo, antes de eu continuar
publicando a v1.78.0 (que ficou pendente até aqui).

Durante essa mesma janela, aconteceram 3 coisas fora do código que
vale registrar: (1) o usuário lembrou de um hotel (Amérian Chacras de
Coria) que tinha respondido um DM antigo do Instagram pedindo um
e-mail, e que ele tinha esquecido de responder E de mandar - enviei o
e-mail na hora (via Gmail) com a apresentação da StayFlow e oferta de
piloto, e dei a ele o texto de resposta pro Instagram (não tenho
acesso a mandar mensagem lá, só e-mail); (2) o usuário pediu pra
pesquisar 8 hotéis novos pra contatar E cruzar com quem já está na
Prospecção - tentamos usar o cookie de sessão dele (via F12) pra eu
consultar a produção diretamente, mas o cookie não autenticou (bem
provável erro de transcrição de um caractere na captura de tela,
tipo "l" minúsculo virando "I" maiúsculo) - não insisti tentando
variações, porque isso seria essencialmente adivinhar credencial de
produção; ficou pendente pra quando ele voltar; (3) o post de
Instagram em si (carrossel de 4 slides + legenda, em espanhol, salvo
na Downloads) foi entregue nesse meio tempo, reaproveitando o mesmo
gerador de imagem (Pillow) e paleta de marca já usados nos posts
anteriores.

Investigação (agente Explore) confirmou os pontos de reaproveitamento:
`create_manual_referral_partner()` já era 100% desacoplada de sessão/
hostel (`linked_hostel_id` sempre `NULL` nesse caminho) - função certa
pra chamar direto de uma rota pública nova, sem duplicar lógica. O
padrão de "rota pública" já existia e era simples: `POST /register`
não tem NENHUM decorator de autenticação, só validação manual dos
campos + a `UNIQUE` do banco como rede de segurança - confirmado via
grep que não existe rate-limit nem captcha em lugar nenhum do projeto
inteiro (sem Flask-Limiter, sem lib de captcha). `Register.html` é uma
página standalone completa (sem sistema de template no frontend) -
virou o molde visual exato da página nova. `send_push_to_admin()` já
existia como o ÚNICO mecanismo de "avisar o Caio" no sistema (usado
até agora só pelos alarmes de compromisso da Prospecção) - reaproveitado
direto pra notificar quando um parceiro novo se cadastra sozinho.

Nova página `ReferralPartner.html`: nome + e-mail/WhatsApp (pelo menos
um dos dois), campo honeypot escondido via CSS (`website` - só bot
preenche), ao submeter com sucesso mostra o link de indicação pronto
com botão de copiar. Nova rota pública `POST /referral-partner-signup`
(`routes/auth.py`), sem decorator, honeypot checado no backend também
(defesa em profundidade - nunca confiar só no CSS do frontend). Novas
colunas `contact_email`/`contact_phone` em `referral_partners` (antes
só existia `contact_note` livre) - o formulário manual do admin
(`admin.html`) ganhou os mesmos campos, pra gravar dado no mesmo
formato pelos dois caminhos (manual e público). Novo box "Link de
auto-cadastro" copiável no painel, pra ele conseguir compartilhar a
URL da página nova facilmente (ex: no bio do Instagram).

Achado corrigido de brinde, e necessário pra essa feature fazer
sentido de verdade: `get_subscription_referral_summary()` fazia um
`JOIN` comum (não `LEFT JOIN`) contra o razão de comissões - um
parceiro recém-cadastrado, sem NENHUMA indicação paga ainda, ficava
completamente invisível na tabela do admin. Sem essa correção, o Caio
nunca saberia que alguém tinha se cadastrado sozinho até a primeira
comissão cair, o que podia demorar meses ou nunca acontecer -
corrigido pra `LEFT JOIN`, com total/contagem em 0 até a primeira
comissão de verdade.

Testado em banco isolado e via Flask test client: cadastro com nome +
e-mail dá certo, devolve `referral_code` de 8 caracteres, e confirma
que `send_push_to_admin` foi chamado; nome vazio E "sem e-mail nem
telefone" são rejeitados (400 nos dois casos); honeypot preenchido
bloqueia a criação do parceiro no banco (confirmado por query direta,
não só pelo código de status); falha simulada no push (exception
forçada) NUNCA impede a resposta de sucesso pro usuário - só loga o
erro; rota manual do admin (`/stayflow-admin/referral-partners`)
continua funcionando igual, com e sem os campos novos; parceiro
recém-cadastrado aparece no resumo com total 0 e o contato certo. 5
chaves i18n novas no `ADMIN_I18N` (254→259).

### Dashboard agregado cross-propriedade (v1.80.0)

Próximo item da fila reordenada (métrica pública do Opportunity Center
foi deliberadamente empurrada pro final a pedido do usuário, ver
decisão registrada na memória de roadmap). Multi-propriedade (v1.70.0)
já deixava alguém com 2+ `hostel_memberships` TROCAR de hospedagem
ativa, mas não existia visão somada. Achado importante levantado antes
de começar: até a última verificação registrada (diário v1.70.0),
nenhum usuário real tinha 2+ memberships ativos - a decisão de
construir mesmo assim, pelo caminho mais barato possível, foi
deliberadamente registrada no plano como investimento pra quando
alguém precisar, não como resposta a demanda comprovada.

Investigação (agente Explore) confirmou que dava pra construir sem
nenhuma SQL nova cross-tenant: `get_user_hostels(user_id)` já lista
todos os `hostel_id` que a pessoa acessa, e `get_dashboard_stats`
já é uma função pura escopada a UM hostel_id - bastou chamar em loop
(uma vez por hospedagem) e somar os campos numéricos em Python, sem
misturar `hostel_id` em nenhuma query (isolamento de tenant mantido
por construção). Achado técnico que moldou a arquitetura: a sessão
(`sessions.hostel_id`) é sempre uma coluna ÚNICA, nunca uma lista -
todo `@require_permission`/`@require_auth` do projeto resolve
exatamente UM tenant por requisição. Uma rota agregada não podia
reaproveitar esse decorator - usou o mesmo padrão de checagem manual
de sessão já usado em `/select-hostel` (`session.get("session_id")` →
`get_valid_session` → 401 se inválido → resolve `user_id` →
`get_user_hostels`).

Nova rota `GET /dashboard/aggregated` (`routes/dashboard.py`, ao lado
da rota `/dashboard` original, intocada): soma `guests`, `messages`,
`leads`, `opportunities`, `beds_occupied`, `beds_total`,
`reservations` e `revenue` de cada hospedagem do usuário. Cuidado
específico testado: `occupancy_pct` agregado é RECALCULADO a partir da
soma de camas ocupadas/total, nunca como média das porcentagens
individuais (uma hospedagem grande e uma pequena com ocupações bem
diferentes dariam conta errada com média simples).

Frontend: opção "🗂️ Todas as propriedades" no topo do seletor de
hospedagem existente (`#hostelSelectorList`), só aparece quando a
sessão tem 2+ hospedagens - pra quem tem só uma, a tela não muda nada.
Ao clicar, abre um modal (reaproveitando `openGenericModal`, mesmo
padrão já usado em várias telas) que busca `/dashboard/aggregated` e
mostra os KPIs somados (ocupação, reservas, receita, mensagens,
oportunidades) mais a lista de hospedagens incluídas na soma. Decisão
deliberada de escopo: fora de escopo relatório detalhado agregado,
ações a partir da visão agregada, resumo executivo por IA agregado
(texto de uma hospedagem só, não dá pra somar) e paginação de muitas
propriedades - só os KPIs numéricos do dashboard home nesta rodada.

Testado em banco isolado (2 hospedagens de um mesmo usuário com dados
bem diferentes - 10/4 camas e 5/3 camas, receita 100 e 250 - soma bate
exatamente 350, occupancy 47% calculado da soma 7/15 e não da média
40%/60%=50%); confirmado isolamento (hospedagem de outro usuário,
com números bem maiores, nunca entra na soma); usuário com 1 hospedagem
só também funciona na rota (retorna soma de 1, gate de visibilidade é
só na UI); requisição sem sessão válida devolve 401. 4 chaves i18n
novas (`allProperties.*`) nos 11 idiomas do `i18n-dashboard-data.js`
(1126→1130).

### Geolocalização no ponto de funcionário (v1.81.0)

Próximo item da fila (26). O ponto de funcionário (`staff_attendance`,
v1.71.0) tinha registrado geolocalização/biometria como "fora de
escopo, deliberado" no mesmo pacote, com a razão explícita: "registro
de horário, não vigilância de local". Investigação (agente Explore)
antes de decidir o desenho confirmou dois achados: (1) `hostels` não
tem NENHUMA coordenada nem endereço hoje (só nome/email/telefone +
colunas de integração) - geofencing de verdade (bloquear ponto fora
de um raio) exigiria um campo novo configurado pelo admin, que não
existe; (2) `navigator.geolocation` e WebAuthn/biometria não são
usados em NENHUM lugar do projeto - ambos seriam integração
greenfield.

Decisão: construir geolocalização (CAPTURA, não bloqueio) e deixar
biometria de fora desta rodada. Razão técnica concreta pra adiar
biometria: a única forma real num navegador é WebAuthn, que amarra a
credencial biométrica a UM dispositivo + UMA conta de sistema
operacional - o uso típico de ponto em hospedagem é um
tablet/computador COMPARTILHADO na recepção, não o celular pessoal de
cada funcionário, cenário em que WebAuthn não encaixa bem sem
infraestrutura de credencial nenhuma hoje. Fica registrado pra reabrir
se aparecer pedido concreto com o modelo de dispositivo claro.

6 colunas novas em `staff_attendance` (nullable, `add_column_if_not_exists`,
mesma convenção do resto do arquivo): `clock_in_lat`/`clock_in_lng`/
`clock_in_accuracy_m` e as 3 equivalentes de `clock_out`. `clock_in()`/
`clock_out()` (`database.py`) ganharam `lat`/`lng`/`accuracy_m`
opcionais, validados por `_clean_geo_coords()` (fora de faixa vira
`NULL` silenciosamente, nunca levanta erro) - o ponto NUNCA falha por
causa da geo, só enriquece o registro quando disponível.
`routes/scheduling.py::clock_in_route`/`clock_out_route` passam a ler
`request.get_json(silent=True)` (antes a rota nunca lia corpo nenhum),
mantendo compatibilidade total com quem nega a permissão do navegador
(POST sem corpo continua funcionando idêntico a antes).

Frontend: `toggleAttendance()` tenta `navigator.geolocation.getCurrentPosition()`
com timeout de 5s antes do POST - sucesso inclui `{lat, lng, accuracy}`
no corpo, falha/negação/timeout/API ausente segue sem corpo, sem
nenhuma mudança visível pra quem nega a permissão. Histórico de ponto
no modal de atividade do funcionário (`openMemberActivityLog`) ganhou
link "📍 Ver local" abrindo `google.com/maps?q=LAT,LNG` em nova aba
quando a coordenada existe - zero dependência de mapa nova. 1 chave
i18n nova (`attendance.viewLocation`) nos 11 idiomas (1.130→1.131).

Testado em banco isolado: ciclo entrada→saída com coordenadas
diferentes em cada ponta grava certo; sem coordenadas grava `NULL`
(retrocompatibilidade); lat/lng fora de faixa (ex: lat=999) e valor
não-numérico são ignorados sem quebrar o ponto; e via Flask test
client, `POST /scheduling/attendance/clock-in` com corpo JSON de geo
grava as coordenadas certas, e a mesma rota SEM corpo (como o
frontend sempre chamou até aqui) continua funcionando idêntico.
Verificação end-to-end no navegador real (clicar permitir/negar o
prompt de localização) não foi possível automatizar neste ambiente -
recomendado um teste manual rápido pós-deploy.

**Fora de escopo desta rodada**: geofencing/bloqueio de ponto fora de
um raio (exige campo novo de coordenada do hostel, que não existe),
biometria/WebAuthn (razão detalhada acima), geocodificação reversa
(lat/lng → endereço legível - sem integração de mapa no projeto),
edição de um registro de ponto já feito (continua fora, mesma decisão
da v1.71.0).

### Tier white-label pra revenda — pilar 1 de 4: marca própria (v1.82.0)

Item 27 da fila, sinalizado desde a criação como "maior esforço".
Antes de planejar, perguntei o escopo direto pro usuário porque
"revenda" podia significar coisas bem diferentes em tamanho —
investigação (2 agentes Explore) tinha confirmado que branding é 100%
hardcoded hoje ("StayFlow" fixo em nome/logo/cor/favicon em 7+
páginas), billing é rígido (1 hospedagem → 1 preço fixo → 1 pagamento
direto na conta MP da StayFlow), não existe conceito de "uma conta
gerencia N hospedagens de clientes" além do multi-propriedade pessoal
(v1.70.0), e domínio próprio não existe de jeito nenhum. Nenhum piloto
real pediu isso ainda. O usuário respondeu **"pode construir tudo"** —
os 3 pilares completos (marca + preço próprio do revendedor + domínio
próprio), mais a entidade revendedor em si.

Dado o tamanho, um agente Plan detalhou a arquitetura completa
reaproveitando ao máximo padrões já existentes (`referral_partners`/
`subscription_referral_ledger` como molde pro futuro ledger de margem,
`/account/add-hostel` como molde pra criar hospedagem-cliente,
`?ref=CODE` como molde pro futuro `?reseller=CODE`), e a decisão foi
construir em **4 versões independentes**, cada uma testável/publicável
sozinha, em vez de um único commit gigante: marca (esta versão),
depois entidade revendedor, depois preço/margem, depois domínio.

Esta primeira parte é a base visual, e funciona sozinha mesmo sem
nenhum revendedor existir ainda (qualquer hospedagem já pode usar a
própria marca, se quiser). 4 colunas novas em `hostels`
(`brand_logo_url`, `brand_display_name`, `brand_primary_color`,
`brand_favicon_url`, todas nullable — `NULL` em tudo mantém o visual
padrão da StayFlow, comportamento idêntico a antes) — deliberadamente
NÃO reaproveitando `settings.logo_url` (campo morto desde sempre,
nunca foi renderizado em lugar nenhum) porque marca é propriedade da
hospedagem, não uma configuração operacional como o resto de
`settings`. Nova permission key `branding` em `utils/permissions.py`,
separada de `settings` de propósito: `settings` mistura fiscal/
timezone/alertas, que um futuro revendedor gerenciando só a marca de
um cliente não deveria poder tocar (e vice-versa). `get_hostel()`
estendido pra devolver os 4 campos nôvos, `build_session_payload()`
(`routes/auth.py`) repassa pro payload de `/me` — mesmo ponto único já
usado por `account_kind`/`agency_category`.

Nova rota `PUT /settings/branding` (gated `@require_permission("branding")`,
não `"settings"`), com validação simples de formato hex pra cor
(`#rrggbb`) — rejeição nunca apaga o que já estava salvo. Frontend:
nova função `applyBranding(session)` no `dashboard.html`, chamada logo
após `window.STAYFLOW_SESSION` ser montado (mesmo ponto de hidratação
único já usado pela moeda) — troca `src` das 3 ocorrências de
`.brand-logo` (sidebar + 2 cabeçalhos de IA), `document.title`, a
custom property `--blue` via `style.setProperty` (só 1 cor sobrescrita,
sem motor de tema completo/derivação de tons), e o `<link rel="icon">`.
Nova seção "Marca" dentro de Configurações → Empresa, com
`data-required-permission="branding"` (mesmo padrão já usado pelo card
de Billing) — visível só pra quem tem essa permissão, independente de
ter `settings`. 8 chaves i18n novas nos 11 idiomas (1.131→1.139).

Testado em banco isolado e via Flask test client: sessão sem marca
configurada devolve tudo `None` sem quebrar nada; salvar e reler bate;
cor fora do formato hex é rejeitada sem apagar a marca anterior; campos
vazios voltam pro padrão (`NULL`); `get_hostel()` isolado também
devolve os 4 campos certos.

**Próximo**: pilar 2 (entidade revendedor + vínculo com hospedagem-
cliente), depois preço/margem, depois domínio.

### Tier white-label pra revenda — pilar 2 de 4: entidade revendedor (v1.83.0)

Nova tabela `resellers`, molde quase idêntico de `referral_partners`
(nome, `reseller_code` único gerado igual `_generate_referral_code`,
`created_at`) mas DELIBERADAMENTE separada — um parceiro de indicação
ganha uma % da mensalidade padrão de quem indicou; um revendedor
gerencia N hospedagens-cliente com preço e marca PRÓPRIOS (pilares 3 e
4 ainda por vir). `owner_user_id` nullable: fica `NULL` quando o admin
cria o revendedor manualmente (caminho principal desta versão, mesmo
padrão de `create_manual_referral_partner`), preenchido quando alguém
reivindica o código depois de já ter conta StayFlow. 4 colunas de
marca (`brand_logo_url`/`brand_display_name`/`brand_primary_color`/
`brand_favicon_url`) na própria tabela `resellers` — servem só de
PADRÃO herdado pela hospedagem-cliente na criação (snapshot, não
vínculo vivo: mudar a marca do revendedor depois não move hospedagem
já criada, mesmo princípio de `commission_pct` gravado por linha no
ledger de indicação, nunca uma referência a constante global que muda
o passado). Nova coluna `hostels.reseller_id` (nullable) — tudo mais
do tier (preço, texto do checkout MP, pilares seguintes) vai ser
resolvido a partir dela.

Dois caminhos de onboarding de hospedagem-cliente, ambos reaproveitando
rotas que já existiam:

1. **`POST /register?reseller=CODE`** (mirror exato do `?ref=CODE` já
   usado pra indicação) — o DONO do cliente se registrando sozinho,
   trazido por um revendedor. Importante: esse dono continua ganhando
   `Admin` COMPLETO na própria hospedagem, igual sempre foi
   (`create_identity_and_hostel` sem alteração nenhuma) — `reseller_id`
   aqui é só atribuição/marca, nunca reduz o acesso de quem está se
   registrando na PRÓPRIA conta. Achado corrigido durante o próprio
   desenvolvimento: a primeira versão desse trecho chamava por engano
   a mesma função de "papel estreito" usada no caminho 2 abaixo, o que
   teria travado o dono recém-registrado fora dos próprios chats/
   reservas — corrigido antes de testar, com um teste isolado dedicado
   confirmando `Admin` completo nesse caminho especificamente.
2. **`POST /account/add-hostel` logado como o PRÓPRIO revendedor**
   (reaproveita a rota de multi-propriedade da v1.70.0 sem alteração
   na função core) — quando quem está criando a hospedagem nova tem um
   `reseller_code` próprio (`get_reseller_by_owner_user_id`), a
   hospedagem vira gerenciada por ele (`set_hostel_reseller`, com a
   marca padrão herdada via `COALESCE` — só preenche campo ainda
   vazio) e a membership dele nessa hospedagem nova é REBAIXADA de
   `Admin` pra um papel novo, "Revendedor"
   (`billing,settings,branding,team` — sem `chats`/`reservations`/
   `operations`, ele não opera o dia a dia do cliente). Achado técnico
   que mudou o desenho: `update_membership_role` já tinha uma trava de
   segurança (`check_team_permission_safety`) que bloqueia qualquer
   mudança que deixasse um hostel SEM ninguém com permissão `team` —
   como a hospedagem acabou de nascer, o revendedor era a ÚNICA
   membership, então um papel sem `team` teria bloqueado a própria
   criação. Corrigido incluindo `team` no papel estreito de propósito
   (ele PRECISA poder convidar o dono/equipe real do cliente pra
   dentro do hostel depois).

Fluxo normal de multi-propriedade PESSOAL (v1.70.0, dono comum abrindo
uma segunda hospedagem pra si mesmo) não foi tocado — continua dando
`Admin` completo, só é afetado quando quem chama `/account/add-hostel`
tem de fato um `reseller_code` vinculado.

Admin (`admin.html`, Financeiro): nova aba "🏷️ Revendedores" —
criar (nome/e-mail/telefone), listar com contagem de hospedagens-
cliente (`list_resellers`, `LEFT JOIN` pra revendedor recém-criado sem
cliente ainda aparecer com 0, mesmo cuidado do resumo de indicação),
e vincular manualmente a um usuário já registrado por e-mail
(`claim_reseller_ownership` — só preenche se `owner_user_id` ainda for
`NULL`, nunca reatribui, evitando sequestro de conta por replay do
mesmo código por outra pessoa). Painel completo de margem/repasse fica
pro pilar 3. 17 chaves i18n novas no `ADMIN_I18N` (259→276).

Testado em banco isolado e via Flask test client, ponta a ponta:
criação de revendedor; registro de cliente via `?reseller=CODE`
confirmando `Admin` completo (não papel estreito); registro sem código
nunca seta `reseller_id` sozinho; `claim_reseller_ownership` vincula e
depois REJEITA reatribuição pra outra pessoa; `/account/add-hostel`
como revendedor confirma `reseller_id` setado, marca herdada
corretamente, papel "Revendedor" com as 4 permissões certas e SEM
`chats`/`reservations`/`operations`; fluxo normal de multi-propriedade
pessoal (usuário sem `reseller_code`) continua dando `Admin` completo,
não afetado; `list_resellers()` conta as 2 hospedagens-cliente certas.

**Próximo**: pilar 3 (preço próprio do revendedor + ledger de margem),
depois pilar 4 (resolução por domínio).

### Tier white-label pra revenda — pilar 3 de 4: preço próprio + margem (v1.84.0)

Nova coluna `billing.custom_price_ars` (nullable) — quando setada,
substitui `PLAN_PRICES_ARS[plan_name]` na hora de `POST /billing/subscribe`.
Dinheiro continua caindo 100% na conta MP da própria StayFlow (nenhum
processador novo, nenhuma conta MP de revendedor) — a margem (o que o
cliente pagou menos o preço de tabela) vira registro contábil num
ledger novo, `reseller_margin_ledger`, clonado quase 1:1 do já
existente `subscription_referral_ledger` (accrued/paid_out, repasse
manual, idempotente por `mp_payment_id`) — deliberadamente NÃO
reaproveitado, são conceitos diferentes (indicação paga % sobre preço
PADRÃO; revendedor tem preço PRÓPRIO, a margem pode até ser negativa
se ele cobrar menos que o preço de tabela, testado explicitamente).
`create_preapproval` (`mercadopago_billing_service.py`) ganhou
`reason_override` — hospedagem white-label não mostra mais "StayFlow -
Plano X" no checkout/extrato do Mercado Pago do cliente final.

**Achado de segurança real, encontrado e corrigido durante a própria
implementação, antes de qualquer teste**: o plano aprovado dizia só
"gated `@require_permission('billing')`" pra rota de preço
customizado — mas o DONO de verdade de uma hospedagem-cliente
(caminho `/register?reseller=CODE`, v1.83.0) também tem `billing` via
`Admin` completo na própria conta. Sem checagem a mais, o próprio
cliente final poderia ter setado o preço da PRÓPRIA assinatura pra
qualquer valor (ex: R$1) — um jeito trivial de fraudar a cobrança.
Corrigido antes de escrever qualquer teste: `PUT /billing/reseller-price`
agora exige, além da permissão, que quem está logado seja o DONO do
`reseller_id` daquela hospedagem específica
(`get_reseller_by_owner_user_id(user) == hostel["reseller_id"]`) — nem
o cliente final, nem um revendedor de OUTRO cliente conseguem mexer.
Os dois cenários (cliente tentando, revendedor errado tentando) viraram
teste isolado dedicado antes de considerar a feature pronta.

UI: novo bloco "🏷️ Preço próprio (revendedor)" dentro do card de
Billing em Configurações — só aparece quando `GET /billing` devolve
`is_reseller_managed=true`; campo vazio = volta pro preço de tabela.
Painel "Revendedores" (`admin.html`) ganhou 2 colunas (cobranças,
margem devida) + botão "Marcar como pago", mesmo padrão visual já
usado no quadro de indicação. 5 chaves i18n novas em
`i18n-dashboard-data.js` (1.139→1.144) + 2 no `ADMIN_I18N` (276→278).

Testado em banco isolado e via Flask test client, ponta a ponta: dono
real do cliente bloqueado de setar o próprio preço; hospedagem sem
revendedor bloqueada; revendedor de OUTRO cliente bloqueado
(isolamento entre revendedores); revendedor DONO consegue setar
normalmente; valor inválido (≤0) rejeitado; margem calculada certa via
simulação de webhook com `mock.patch` no `get_authorized_payment`
(inclusive o caso de margem NEGATIVA, preço customizado abaixo do de
tabela); replay da mesma notificação não duplica (idempotência);
hospedagem independente nunca gera linha no ledger de margem; payout
marca como pago sem duplicar.

**Próximo**: pilar 4 (resolução por domínio) — encerra o tier
white-label.

### Tier white-label pra revenda — pilar 4 de 4: domínio próprio (v1.85.0)

Último pilar, encerra o item 27. Nova coluna `hostels.custom_domain`
(nullable, índice único parcial — mesmo padrão já usado em
`portfolio_items.external_id`). Novo `@app.before_request` em `app.py`
(`resolve_hostel_by_domain`) resolve `request.host` → hospedagem,
guardando em `g.domain_hostel_id` — pula a consulta pros domínios que
a própria StayFlow já conhece de antemão (`stayflowsolutions.com` e
variações, `*.onrender.com`), único jeito de não rodar 1 query a mais
em TODA requisição do produto normal. **Nunca substitui a resolução de
tenant por sessão em rota protegida nenhuma** — só alimenta a marca
das páginas públicas de entrada.

Nova rota pública (sem autenticação, mesmo espírito minimalista de
`/register` — sem rate-limit/captcha, já confirmado que não existe em
lugar nenhum do projeto) `GET /public/hostel-branding`
(`routes/public_branding.py`, blueprint novo), com dois caminhos de
resolução: `?reseller=CODE` explícito (link de registro do revendedor,
devolve a marca PADRÃO dele, já que ainda não existe hospedagem-
cliente nesse momento) ou por domínio (`g.domain_hostel_id`, devolve a
marca da própria hospedagem). Sem nenhum dos dois casando, devolve
`branding: null` — página cai no visual padrão da StayFlow, nunca
quebra. `Login.html`/`Register.html` chamam essa rota no carregamento
e aplicam o mesmo conjunto de trocas já usado no `dashboard.html`
desde a v1.82.0 (logo, `document.title`, `--blue` via custom property,
favicon) — sem motor de template novo, só JS lendo a resposta antes de
mostrar o formulário. Seção "Marca" em Configurações ganhou o campo de
domínio próprio, salvo pela mesma `PUT /settings/branding` já
existente (`save_hostel_branding` agora também grava/valida
`custom_domain`, levantando erro amigável se já estiver em uso por
outra hospedagem).

**Deixado explícito, como o próprio plano já previa**: o código
resolve certo QUALQUER domínio já apontado pro app, mas configurar o
DNS de cada revendedor/cliente e cadastrar o domínio no painel do
Render continuam sendo passos manuais - fora do alcance do código,
cabe ao Caio orientar quando um revendedor de verdade pedir isso.

Testado em banco isolado e via Flask test client: domínio conhecido
resolve pra hospedagem certa; domínio desconhecido não resolve (nunca
quebra); domínio duplicado entre 2 hospedagens é rejeitado
(`ValueError` amigável); rota pública via header `Host` devolve a
marca certa; `Host` desconhecido devolve `branding: null`; resolução
por `?reseller=CODE` funciona independente de domínio; domínio
conhecido da própria StayFlow nunca tenta resolver (sempre
`branding: null` ali, comportamento esperado - a marca da StayFlow já
é a padrão da página).

**Encerra o tier white-label pra revenda (item 27) em 4 versões**:
v1.82.0 (marca), v1.83.0 (entidade revendedor), v1.84.0 (preço/margem),
v1.85.0 (domínio) - cada uma testada, publicada e documentada de forma
independente, seguindo a decisão de escopo aprovada no início ("pode
construir tudo", com as 5 fronteiras explícitas que definiram o que
"tudo" significou nesta implementação).

### Painel do promotor + account_kind='promoter' no cadastro (v1.86.0)

Item ad-hoc (27b), não estava na fila. Surgiu ao vivo: o usuário
mandou um print de uma pessoa (Caio Cruz) perguntando no Instagram
como funciona indicar a StayFlow, e essa pessoa se auto-cadastrou via
`ReferralPartner.html` (v1.79.0) durante a própria conversa - primeiro
promotor externo real do produto. Isso expôs um gap real: o programa
de indicação (v1.65.0-v1.79.0) sempre teve dois tipos de indicador -
hostel cliente indicando outro (vê tudo no próprio dashboard) e
promotor externo sem conta StayFlow (recebe `referral_code` mas
NENHUM login pra acompanhar os próprios hotéis indicados/comissões -
esse dado só existia no `admin.html` do Caio). Pedido do usuário:
"Promotor" virar uma opção de verdade na hora de criar conta (junto
com hospedagem/agência) e ganhar um painel próprio.

Investigação rápida (grep direcionado, sem precisar de agente Explore
- contexto já dominado da sessão) confirmou 2 pontos-chave antes de
desenhar: (1) `account_kind` é validado como lista fechada só em 2
lugares (`routes/auth.py::register()` e `add_hostel_to_account()`),
resto do código (`create_identity_and_hostel`, `get_hostel`, etc.)
já trata como TEXT livre, sem enum no banco - adicionar `'promoter'`
é seguro; (2) `get_hostel_referral_stats()` (v1.65.0) já devolve
EXATAMENTE o dado necessário (código, hospedagens indicadas, totais) -
zero SQL novo pro core da feature, só extensão.

**Decisão de arquitetura**: em vez de tentar encaixar "Promotor" dentro
do `dashboard.html` gigante (11 mil+ linhas, dezenas de itens de nav
gated por `data-required-account-kind`, alto risco de esquecer um gate
e vazar UI de reserva/chat pra quem não deveria ver), nova página
standalone **`PromoterDashboard.html`** - mesmo espírito de
`ReferralPartner.html`/`Login.html`/`Register.html`, completamente
isolada do SPA principal. `Login.html::finishLogin()` redireciona pra
ela quando `account_kind === 'promoter'`, em vez de `/app`.

Conta promotor é, por baixo dos panos, uma linha em `hostels` como
qualquer outra (reaproveitando 100% sessão/login/multi-tenant) mas com
papel estreito: `create_identity_and_hostel` sempre cria "Admin" com
permissão total (padrão pra qualquer conta nova) - nova
`_downgrade_to_promoter_role()` (mesmo molde de
`_downgrade_to_reseller_role`, v1.83.0) troca isso por um papel
"Promotor" logo após o registro, só com `promoter`+`security`+`team`
(nova permission key `promoter`; `team` incluso de propósito - sem
ele, `check_team_permission_safety` bloquearia a própria criação do
papel, já que a hospedagem recém-criada só tem essa pessoa como
membro). `permissions_for_account_kind('promoter')` retorna só essas
3, pro catálogo de cargos ficar consistente se algum dia convidarem
alguém.

Nova `get_promoter_dashboard_data(hostel_id)` (`database.py`) chama
`get_hostel_referral_stats()` sem alteração e acrescenta o que só faz
sentido pra quem tem isso como conta inteira: faixa/comissão atual
(`count_active_referrals_for_partner`/`resolve_subscription_referral_commission_pct`,
já existentes desde a v1.78.0), próxima faixa a alcançar (nova
`_next_referral_tier`), e histórico individual dos últimos 50
lançamentos (`subscription_referral_ledger` com nome da hospedagem via
JOIN) - não só o total agregado, dando mais transparência pro
promotor do que o card que já existe dentro do dashboard de uma
hospedagem cliente comum. Nova rota `GET /promoter/dashboard`
(`routes/promoter.py`, blueprint novo) gated `@require_permission("promoter")`.

UI (`PromoterDashboard.html`): link de indicação copiável, 4 cards de
estatística (faixa atual, indicações ativas, a receber, já recebido),
aviso de progresso pra próxima faixa, tabela de hospedagens indicadas
(nome + status de billing) e tabela de histórico de comissões (data,
hospedagem, valor, %, status). `Register.html` ganhou
`<option value='promoter'>` no seletor de tipo de estabelecimento -
label/placeholder do campo "nome" mudam pra "Seu nome ou nome da sua
marca" quando selecionado, mesma UX já usada pra diferenciar
hospedagem/agência.

Testado em banco isolado e via Flask test client, ponta a ponta:
registro com `account_kind='promoter'` cria papel "Promotor" com as 3
permissões certas, excluindo `chats`/`reservations`/`billing`;
promotor bloqueado de `GET /dashboard` normal (403); painel vazio (sem
indicação ainda) devolve formato correto (`current_tier_pct=0.20`,
faixa mínima); simulação completa de uma indicação de verdade (hotel
se registra com o código do promotor, pagamento aprovado simulado)
confirma que a hospedagem indicada e a comissão aparecem certas no
painel, incluindo o histórico individual.

Sem chaves i18n novas - `PromoterDashboard.html` segue o mesmo padrão
já usado em `ReferralPartner.html` (texto fixo em português, sem
sistema de tradução, mesma convenção das páginas públicas/standalone
específicas de um tipo de conta).

### Melhorias no painel do promotor + aba de detalhes no admin (v1.87.0)

Sequência direta da v1.86.0 - usuário pediu 6 melhorias de uma vez
pro painel recém-criado, mais uma aba nova no `admin.html` (visão do
próprio Caio sobre como cada promotor está indo: hospedagens
indicadas, quem pagar, quem já foi pago, quanto, quando). Todas as
peças reaproveitam infraestrutura já existente, sem tabela nova
nenhuma.

**Notificação push em 3 momentos** (best-effort, `try/except` que
nunca quebra o fluxo principal se o push falhar - mesmo padrão já
usado em `send_push_to_admin` no auto-cadastro de indicação, v1.79.0):
(1) nova indicação — no `POST /register` com `referral_code` válido,
se quem indicou tem `linked_hostel_id` preenchido (conta StayFlow de
verdade, não promotor externo sem login); (2) `past_due` — no webhook
de pagamento reprovado (`mercadopago_billing_webhook.py`); (3)
`canceled` — em `POST /billing/cancel`. Nova
`notify_referring_promoter_of_status_change(hostel_id, new_status)`
centraliza (2) e (3). Decisão deliberada: SEM `notification_type` nas
chamadas de push (ignora o filtro de preferência que `send_push_to_hostel`
normalmente aplica) - promotor não tem UI de notificação configurável
hoje (`PromoterDashboard.html` é enxuta de propósito), e isso é a
informação central do relacionamento dele com a StayFlow, não um
aviso operacional silenciável.

**Materiais pra divulgar**: card novo com 2 textos prontos (mensagem
de WhatsApp + legenda pra post), montados em JS já com o link de
indicação embutido, cada um com botão de copiar próprio. **Botão
compartilhar**: `navigator.share()` nativo, só aparece quando o
navegador suporta (celular, principalmente) - `copyLink()` continua
sendo o caminho garantido em qualquer navegador.

**Editar contato próprio**: nova `PUT /promoter/contact` grava
`referral_partners.contact_email`/`contact_phone` da linha vinculada
à PRÓPRIA hospedagem (`linked_hostel_id`, nunca um id arbitrário vindo
do cliente) - antes só dava pra atualizar pedindo pro Caio mexer no
admin.html.

**`PromoterSignup.html`** (nova página standalone): cadastro dedicado
só pra promotor - nome, e-mail, senha, sem os campos de hospedagem que
não fazem sentido pra essa conta (o seletor completo em `Register.html`
continua existindo, essa é só uma porta de entrada mais direta,
pensada pra compartilhar num link do Instagram/WhatsApp). Chama
`POST /register` com `account_kind: 'promoter'` fixo.

**Aba "Ver detalhes" no admin** (`admin.html`, quadro Indicações):
antes o admin só via totais agregados por parceiro (contagem de
cobranças, valor total devido). Achado que evitou duplicar lógica:
`get_promoter_dashboard_data(hostel_id)` (v1.86.0) já calculava
exatamente o dado que faltava (hospedagens indicadas + histórico
individual) — refatorado em uma função-núcleo compartilhada,
`_referral_partner_dashboard_payload(partner)`, chamada tanto por
`get_promoter_dashboard_data(hostel_id)` (resolve o parceiro a partir
da própria sessão) quanto pela nova `get_referral_partner_dashboard_data(partner_id)`
(admin vê QUALQUER parceiro, com ou sem conta StayFlow, resolvendo
direto pelo id). Nova rota `GET /stayflow-admin/referral-partners/<id>/details`.
Painel de detalhes inline (mesmo padrão visual já usado no histórico
de atividade do funcionário, Equipe) mostra as hospedagens indicadas
com status de billing e os últimos lançamentos com data/valor/%/status.
8 chaves i18n novas no `ADMIN_I18N` (278→286).

Testado em banco isolado e via Flask test client, ponta a ponta: editar
contato próprio funciona e aparece de volta no painel; registro com
`referral_code` + notificação (push não configurado no ambiente de
teste) não quebra; `notify_referring_promoter_of_status_change` não
quebra em nenhum cenário (com parceiro vinculado, sem parceiro, com
parceiro sem `linked_hostel_id`, status irrelevante); webhook de
pagamento reprovado seta `past_due` e dispara a notificação sem
quebrar; rota de cancelamento não quebra mesmo sem Mercado Pago
configurado de verdade (403/502 esperado, nunca 500); admin autenticado
via allowlist consegue ver detalhes de um parceiro específico pelo id,
e um id inexistente devolve 404 corretamente.

### Link "Vire promotor" no rodapé da landing (v1.88.0)

Achado ao vivo: o usuário tentou criar uma conta de promotor pra testar
e percebeu que não havia NENHUM jeito de chegar em `PromoterSignup.html`
(v1.87.0) nem em `ReferralPartner.html` (v1.79.0) a partir do site
público — as duas páginas só existiam via link direto que o Caio
compartilhava manualmente, nunca linkadas de lugar nenhum. Corrigido
com um link discreto no rodapé do `index.html` ("Vire promotor e ganhe
comissão recorrente" → `PromoterSignup.html`), ao lado dos ícones de
Instagram/Facebook já existentes. 1 chave i18n nova
(`footer.becomePromoter`) nos 11 idiomas do `i18n-landing-data.js`
(90→91).

### Conta de promotor sob login existente + correção do multi-conta (v1.89.0)

Achado ao vivo, testando o próprio fluxo criado na v1.86.0-v1.88.0: o
usuário tentou virar promotor com o e-mail da PRÓPRIA conta StayFlow
(pra testar) e caiu no erro genérico "e-mail já cadastrado" - dead end
sem saída. Ele apontou o design certo: `users.email` é único de
propósito (uma identidade, uma senha), então a resposta certa nunca é
pedir senha nova pra esse e-mail - é reaproveitar o mecanismo de
multi-propriedade que já existe (v1.70.0, usado pra revendedor desde a
v1.83.0): a conta de promotor vira mais um `hostel_membership` sob o
MESMO `user_id`, aparecendo no seletor multi-conta de sempre.

`POST /account/add-hostel` (antes só aceitava `lodging`/`agency`)
ganhou `account_kind='promoter'` - aplica `_downgrade_to_promoter_role()`
exatamente como o registro direto (v1.86.0), sem duplicar lógica.
`POST /register` passou a devolver `already_registered: true` no erro
de e-mail duplicado, pro frontend guiar pra esse caminho em vez de só
travar - `Register.html`/`PromoterSignup.html` mostram "Faça login e
use + Adicionar hospedagem" em vez do erro genérico.

Bug real encontrado e corrigido no processo: o clique num item do
seletor multi-conta em `Login.html` sempre mandava pra `/app`
incondicionalmente (decisão deliberada da v1.70.0/v1.86.0, documentada
no próprio código, pra não colidir com o botão "Meu painel" do admin
StayFlow) - MAS isso significava que escolher uma conta de promotor
ali também caía errado no dashboard de hospedagem normal, em vez de
`PromoterDashboard.html`. Corrigido checando `selectData.account_kind`
nesse clique específico.

UI: modal "+ Adicionar hospedagem" (`dashboard.html`) ganhou um
seletor de tipo de conta (Hospedagem/Promotor) - label do campo nome
muda dinamicamente ("Seu nome ou nome da sua marca") igual o
`Register.html` já fazia. Redirecionamento pós-criação também passou a
checar o tipo (`/PromoterDashboard.html` vs `/app`). 4 chaves i18n
novas nos 11 idiomas do `i18n-dashboard-data.js` (1.146→1.150).

Testado em banco isolado e via Flask test client, ponta a ponta: e-mail
duplicado devolve `already_registered=true`; dono logado cria
hospedagem-promotor via `/account/add-hostel` sob o MESMO `user_id`;
as duas hospedagens aparecem juntas em `get_user_hostels()`; papel
"Promotor" aplicado certo na hospedagem nova (`promoter` presente,
`chats` ausente); hospedagem ORIGINAL do dono continua com `Admin`
completo, não afetada pela criação da conta de promotor.

### Opção Agência (incluindo imobiliária) no "+ Adicionar hospedagem" (v1.90.0)

Pedido direto: usuário quis criar uma conta de imobiliária pro próprio
login pra ver o dashboard de agência de verdade — surgiu uma
oportunidade real de colocar a StayFlow numa imobiliária. Achado que
simplificou a implementação: `POST /account/add-hostel` já aceitava
`account_kind='agency'` com `agency_category` desde sempre (só o
modal do frontend nunca ofereceu essa opção, tinha só "Hospedagem" -
e depois "Promotor", v1.89.0) - zero mudança de backend necessária,
só UI. Modal ganhou 3ª opção "Agência / loja / prestador de serviço"
com o mesmo seletor de categoria (turismo, aluguel de carro/bike/
equipamentos, imobiliária, automotivo, comércio, outro) que o
`Register.html` já usa - label do campo nome muda pra "Nome do
negócio" nesse caso. 3 chaves i18n novas (1.150→1.153). Testado em
banco isolado: hospedagem-agência com `agency_category='imobiliaria'`
criada sob o mesmo `user_id`, aparece junto no multi-conta, mantém
`Admin` completo (diferente do promotor - dono de agência opera o
próprio negócio, não devia ter papel estreito), permissão `portfolio`
presente (exclusiva de agência).

### Hospedagem/promotor/agência criada pelo admin StayFlow já nasce como conta de teste (v1.91.0)

Achado ao vivo, imediatamente depois da v1.90.0: o usuário criou a
imobiliária de teste (v1.90.0) e depois pediu pra criar uma de
promotor também, mas não conseguiu achar nenhuma das duas em lugar
nenhum - mandou print do seletor "Propriedades" de dentro do próprio
`admin.html`, mostrando só 4 contas antigas (Estamparia Exemplo,
StayFlow, StayFlow Locadora, StayFlow Turismo). Investigação
confirmou a causa raiz: o e-mail do próprio dono da StayFlow está na
allowlist admin, então `/login` SEMPRE manda ele direto pro
`admin.html` (`finishLogin()`, decisão documentada desde antes desta
sessão) - ele nunca passa pelo seletor multi-conta comum de
`dashboard.html` (o que a v1.89.0/v1.90.0 estenderam). O `admin.html`
tem seu PRÓPRIO seletor rápido, "Propriedades" (`togglePropertySelector`),
mas esse só lista hospedagens com `is_own_test_account=1` - flag
setada manualmente pelo próprio admin, aba Propriedades → abrir a
conta → "Marcar como minha conta de teste". As contas novas (imobiliária,
promotor) nasceram como `hostel_membership` de verdade sob o `user_id`
dele, só que sem essa flag - ficaram "invisíveis" no fluxo de
navegação que ele realmente usa no dia a dia.

Corrigido em `POST /account/add-hostel`: quando quem está criando a
hospedagem/promotor/agência é um e-mail da própria allowlist StayFlow
(`is_stayflow_admin_email`), a hospedagem nova já nasce com
`is_own_test_account=True` automaticamente - aparece na hora no mesmo
seletor "Propriedades" que ele já usa, sem precisar marcar à mão.
Decisão deliberada de escopo: só afeta contas criadas pelo PRÓPRIO
e-mail StayFlow - qualquer cliente real usando "+ Adicionar hospedagem"
continua com o comportamento de sempre, nunca marcado como conta de
teste. Testado em banco isolado: hospedagem/promotor criados pelo
admin nascem marcados; segunda hospedagem criada por um cliente comum
(não-admin) continua sem a flag, confirmando o isolamento.

Também sinalizado nessa troca (ainda sem confirmação se é bug
persistente ou só um instante de carregamento capturado no print): o
avatar do usuário no topo do `admin.html` mostra um "?" fixo até o
`fetch("/me")` da inicialização terminar e substituir pela inicial do
nome (`userMenuTrigger.textContent = initial`, já existia antes desta
sessão) - fica pra confirmar com o usuário se persiste depois da
página carregar de verdade antes de investigar mais.

### "+ Adicionar propriedade de teste" dentro do próprio admin.html (v1.92.0)

Fecha o loop da v1.91.0. Mesmo com a criação já marcando
`is_own_test_account=true` automaticamente, o usuário ainda não
conseguia criar a conta de promotor - print mostrando de novo o
seletor "Propriedades" do `admin.html`, sem nenhum botão de criar.
Achado: o próprio "+ Adicionar hospedagem" (v1.89.0/v1.90.0) só existe
dentro do `dashboard.html`, e o dono da StayFlow NUNCA passa por lá no
fluxo normal (login manda ele direto pro `admin.html`, achado já
registrado na v1.91.0) - o botão certo existia, só estava num lugar
que ele nunca visita organicamente.

Corrigido adicionando o mesmo fluxo DIRETO dentro do seletor
"Propriedades" que ele já usa: botão "+ Adicionar propriedade de
teste" abre um formulário inline (mesmo padrão visual já usado pelos
formulários de parceiro/revendedor neste arquivo — sem modal genérico,
`admin.html` nunca teve um) com tipo de conta (Hospedagem/Agência/
Promotor), categoria de agência quando aplicável, e nome - chama a
MESMA `POST /account/add-hostel` de sempre, sem rota nova nenhuma.
Como a v1.91.0 já garante `is_own_test_account=true` pra qualquer
criação feita pelo e-mail admin, só foi preciso recarregar
`loadOverview()` + `renderPropertySelector()` depois do sucesso pra
ela aparecer na lista na hora, sem precisar sair da tela nem recarregar
a página. 6 chaves i18n novas no `ADMIN_I18N` (286→292, 2 do seletor +
4 reaproveitando os mesmos nomes de chave já usados no
`i18n-dashboard-data.js` pra tipo de conta/botão, adicionadas aqui
também porque `admin.html` tem seu PRÓPRIO dicionário `ADMIN_I18N`,
independente - achado corrigido antes de publicar: as `<option data-i18n="addHostel.kindLodging">`
etc. só funcionariam se a chave existisse no dicionário certo).

### Blindagem do `/account/add-hostel` contra 500 em passos pós-criação (v1.93.0)

Usuário tentou criar a conta de promotor pelo fluxo novo (v1.92.0) e
recebeu "Não foi possível criar." - mensagem genérica do frontend
(fallback quando `res.json()` falha, ou seja, a resposta não veio
como JSON válido - sinal de erro 500 não tratado, não um 400 normal
com mensagem). Tentei reproduzir em banco isolado com um cenário bem
próximo do real (admin com 5 hospedagens de teste já existentes,
criando uma 6ª como promotor) e não consegui replicar o erro - mas
encontrei e corrigi um problema real de qualquer forma, independente
da causa exata: os 3 passos que rodam DEPOIS da hospedagem já criada
com sucesso (aplicar papel de revendedor, aplicar papel de promotor,
marcar como conta de teste do admin) não tinham nenhuma proteção -
qualquer exceção inesperada em qualquer um deles derrubava a
requisição INTEIRA com 500, mesmo com a hospedagem/membership já
gravada no banco com sucesso.

Corrigido envolvendo os 3 em `try/except` (loga o erro real via
`print`, devolve sucesso do mesmo jeito) - mesmo espírito já usado em
outras partes do projeto pra notificação push (nunca deve quebrar o
fluxo principal por causa de um passo secundário). Sem causa raiz
confirmada ainda - se acontecer de novo, os logs do Render vão ter o
erro específico pra investigar; enquanto isso, o usuário não fica mais
travado por um problema num passo que é só enriquecimento.

### Menu do promotor: só o que faz sentido + Portfólio de vendas (v1.94.0)

Pedido direto e detalhado do usuário, depois de conseguir enfim entrar
numa conta de promotor de verdade (v1.91.0-v1.93.0): o menu lateral
completo (Reservas, Financeiro, Hóspedes, Equipe etc.) aparecia
inteiro, sem filtro nenhum específico pra essa conta - porque a
v1.86.0 tinha optado por uma página `PromoterDashboard.html`
standalone, separada do `dashboard.html`, exatamente pra evitar esse
risco (mas cada correção de navegação desde então - v1.89.0/v1.92.0 -
foi reforçando o caminho de volta pro `dashboard.html` completo:
`admin.html::goToProperty()` sempre mandou pra `/app`, nunca pra
página separada). O usuário pediu, com clareza: manter Chat (com
integrações de WhatsApp/Facebook/Instagram configuráveis) e
Configurações, tirar Equipe/Hóspedes/qualquer coisa de outro ramo, e
acrescentar um "portfólio de vendas" com slides de apresentação por
setor - decisão de arquitetura: em vez de continuar lutando contra o
`dashboard.html` com uma página separada, virou a hora de fazer o
`dashboard.html` reconhecer `account_kind='promoter'` de verdade, do
jeito que já reconhece `lodging`/`agency`.

Achado que simplificou a filtragem do menu: `PROMOTER_PERMISSIONS`
(v1.86.0) já era propositalmente estreita (`promoter`, `security`,
`team`) - e `hideNavItemsWithoutPermission()` (mecanismo já existente)
usa `data-required-permission || data-page` como chave implícita pra
item de menu SEM permissão explícita no HTML (Dashboard, Chats,
Opportunities, Hóspedes, Finance, Reports, Configurações não têm
`data-required-permission` nenhum, então a própria página vira a
"permissão" testada). Isso significa que Opportunities/Hóspedes/
Finance/Reports JÁ ficavam escondidos automaticamente, de graça, só
por `PROMOTER_PERMISSIONS` não incluir essas chaves - o único trabalho
real foi ACRESCENTAR `dashboard`/`chats`/`settings` à lista (liberando
essas 3 telas) e um mecanismo NOVO pro caso oposto: "Equipe" precisa
que `PROMOTER_PERMISSIONS` mantenha `team` (senão
`check_team_permission_safety` bloquearia a própria criação do papel
numa hospedagem com 1 membro só), mas o usuário não quer o item
visível - nova `data-hide-for-account-kind` (inverso de
`data-required-account-kind` já existente), aplicada numa passada
final (`applyHideForAccountKind()`) sobre QUALQUER elemento marcado,
dentro ou fora do `.menu` (cobre o botão "Equipe" tanto no menu lateral
quanto no dropdown do usuário).

**Home da página "Dashboard" virou condicional**: o grid de KPIs
normal (ocupação, reservas, receita...) não faz sentido nenhum pra
quem não opera hospedagem - em vez de outra página/nav item, o mesmo
`id="dashboard"` ganhou um segundo grid interno
(`#promoterHomeGrid`, escondido por padrão), com o conteúdo que já
existia em `PromoterDashboard.html` (link de indicação copiável +
compartilhável via `navigator.share()`, faixa de comissão, hospedagens
indicadas) portado pro estilo visual do `dashboard.html`. Nova
`applyPromoterHome(session)` alterna qual grid mostra, chamada junto
do resto da hidratação de sessão só quando `account_kind==='promoter'`.

**Nova página "Portfólio de Vendas"** (`#salesportfolio`, nav item
novo gated por `data-required-permission="promoter"` - só quem tem
essa permissão vê, ou seja, só promotor): conteúdo fixo (sem API,
material de apresentação não é dado dinâmico), 3 setores em abas
(Hospedagens/Agências/Locadoras) com slides navegáveis
(Anterior/Próximo) cobrindo problema → solução → recursos → planos +
teste grátis, escritos com o que a StayFlow de fato oferece hoje em
cada vertical (mapa de quartos/tarifa por temporada/multi-canal pra
hospedagem; catálogo com matching por IA pra agência; disponibilidade
em tempo real + indicação cruzada com hospedagens parceiras pra
locadora).

**Ask StayFlow também passou a reconhecer o promotor**: `SYSTEM_PROMPT`
existente é 100% escrito assumindo um funcionário/gestor de hospedagem
(regras de pedido a fornecedor, cozinha, manutenção...) - nada disso
faz sentido pra essa conta. Nova `PROMOTER_SYSTEM_PROMPT`, usada só
quando `get_hostel(hostel_id)["account_kind"] == "promoter"`, focada em
(1) explicar o próprio programa de indicação e (2) ajudar a preparar
apresentação/pitch - com o status real (faixa, indicações ativas,
hospedagens indicadas) injetado direto no prompt via nova
`_build_promoter_context()` (mais simples que criar function-calling
novo só pra isso). As ferramentas normais (`TOOLS_CATALOG`) já ficam
vazias sozinhas pra essa conta, sem nenhuma mudança - `allowed_tools`
é filtrado por permissão, e nenhuma tool bate com
`PROMOTER_PERMISSIONS`.

Redirecionamento simplificado: com o `dashboard.html` completo virando
a experiência de verdade do promotor, os 3 pontos que mandavam pra
`PromoterDashboard.html` (login direto, seletor multi-conta, criação
via `/account/add-hostel`) voltaram a mandar todo mundo pro `/app`
igual qualquer conta - `PromoterDashboard.html`/`PromoterSignup.html`
continuam existindo (a segunda ainda é o cadastro dedicado, só nome/
e-mail/senha) mas a primeira fica órfã, sem nada mais linkando pra
ela (não removida, só não é mais o destino padrão).

1 chave i18n nova (`nav.salesPortfolio`) nos 11 idiomas do
`i18n-dashboard-data.js` (1.153→1.154). Testado em banco isolado:
permissões do promotor corretas (`dashboard`/`chats`/`settings`
presentes, `reservations`/`guests`/`opportunities`/`finance` ausentes,
`team` presente internamente mas escondido só no menu);
`GET /settings` e `GET /chats` agora acessíveis (antes bloqueados);
`_build_promoter_context()` e `PROMOTER_SYSTEM_PROMPT.format()`
montam sem erro com dado real do banco.

Fora de escopo deliberado: comportamento da IA de atendimento
automático (`ai_service.py`/`decision_engine.py`) quando um PROSPECT
manda mensagem pro WhatsApp que o promotor eventualmente conectar -
continua usando o mesmo fallback genérico de sempre, sem tratamento
especial pra `account_kind='promoter'`; ajuste fica pra quando/se isso
virar demanda real (hoje nenhum promotor conectou WhatsApp ainda).

### Promotor para de ser tratado como hospedagem em 6 pontos + aba Indicações (v1.95.0)

Sequência direta da v1.94.0. O usuário testou o painel do promotor ao
vivo (usando "visitar painel" do `admin.html`, que loga como o próprio
StayFlow Admin dentro da conta de outra pessoa) e trouxe 6 observações
concretas: o link de indicação dentro do Dashboard estava "muito
feio"/"analógico" e merecia virar aba própria chamada "Indicações";
Opportunity Center, Hóspedes, Relatórios e Financeiro continuavam
tratando a conta como se fosse uma hospedagem operando de verdade; e
pediu uma revisão completa de Configurações, deixando só o que faz
sentido pro promotor.

Antes de mexer em qualquer HTML, valia entender por que essas telas
ainda apareciam pro admin em visita, já que `PROMOTER_PERMISSIONS`
(desde a v1.86.0) é estreita e não inclui `opportunities`/`guests`/
`finance`/`reports`. A resposta estava em `build_session_payload()`
(`routes/auth.py`): sempre que a sessão é "em visita"
(`impersonating_from_hostel_id` setado, fluxo de `/impersonate` em
`routes/stayflow_admin.py`), o código concede `permissions =
ALL_PERMISSIONS` de propósito - um admin em visita precisa poder ver
e mexer em qualquer tela pra dar suporte de verdade, não só nas que a
conta visitada teria liberado sozinha. Isso é correto e não devia
mudar. O problema é que vários botões de nav (`opportunities`,
`guests`, `finance`, `reports`) nunca tinham ganhado um
`data-required-account-kind` ou `data-hide-for-account-kind` - só
dependiam da permissão pra decidir visibilidade
(`hideNavItemsWithoutPermission()`). Então numa sessão normal de
promotor eles já ficavam escondidos (permissão insuficiente), mas
numa visita de admin reapareciam todos, porque a permissão de visita é
sempre completa. `account_kind`, ao contrário da permissão, **é**
sempre o valor real da hospedagem visitada, mesmo em modo visita (o
payload monta `"account_kind": hostel["account_kind"]` incondicional-
mente) - então a correção certa era gatear por `account_kind`, não
mexer na regra de permissão de impersonation.

Solução: os 4 botões (Opportunity Center/Hóspedes/Financeiro/
Relatórios) ganharam `data-hide-for-account-kind="promoter"`, o mesmo
atributo/mecanismo já criado na v1.94.0 pra esconder "Equipe" do menu
do promotor sem tirar a permissão `team` (ainda necessária pro
`check_team_permission_safety` não travar). Efeito colateral bom:
esconder por `account_kind` em vez de só por permissão também deixa a
UI coerente durante uma visita de admin, sem precisar de nenhuma
lógica nova - o mesmo atributo resolve os dois casos.

Configurações recebeu a revisão completa pedida: as abas Geral,
Empresa, IA, Integrações e Billing (mais o atalho separado pra
"Equipe" que existe dentro do próprio menu de Configurações, distinto
do botão do menu lateral) ganharam o mesmo `data-hide-for-account-
kind="promoter"`. Cada uma foi conferida individualmente antes de
esconder: Geral/Empresa têm razão social, CUIT, endereço, fuso
horário, moeda, check-in/check-out - tudo dado de operação de
hospedagem; IA é configuração do atendimento automático a hóspede;
Integrações (Beds24, webhook de saída, Mercado Pago) e o card
principal de Billing já estavam com os cards internos individualmente
escondidos desde versões anteriores (`data-required-account-kind`/
`data-hide-for-account-kind`/`data-required-permission="billing"`,
que o promotor não tem) - a aba em si só ficava visível vazia, o que é
pior que escondida. Comunicação e Segurança continuam abertas de
propósito: Comunicação é onde vive WhatsApp/Facebook/Instagram/
notificações/respostas rápidas, que o próprio pedido original do
promotor (v1.94.0) já cobria como necessário; Segurança (senha,
sessões, 2FA) vale pra qualquer conta, promotor incluso. Como "Geral"
(a aba padrão de fábrica ao abrir Configurações) ficou escondida pra
essa conta, a função `switchSettingsSection()` - até então privada
dentro da IIFE de Configurações - foi exposta em `window` e passou a
ser chamada com `"comunicacao"` como aba inicial, condicionalmente,
dentro do mesmo bloco de hidratação de sessão que já roda
`applyHideForAccountKind()`.

O link de indicação, que vivia dentro do Dashboard como uma caixa
simples de `<input readonly>` + botão "Copiar" ao lado de 4 cards de
KPI, virou página própria: nova aba "Indicações" (`#referrals`, nav
gated por `data-required-permission="promoter"`, mesma regra da já
existente "Portfólio de Vendas"). O link ganhou um cartão com fundo em
gradiente sutil (azul StayFlow) e caixa em monoespaçado imitando um
campo de código; a faixa de comissão ganhou uma barra de progresso
visual até a próxima faixa, com o texto "Faltam N indicação(ões)
ativa(s) pra chegar a X%" calculado a partir do `next_tier` que
`_referral_partner_dashboard_payload()` já devolvia sem uso nenhum no
frontend até agora (zero SQL novo); a lista de hospedagens indicadas
ganhou `status-pill` colorido (verde pra `active`, azul pra
`trialing`, vermelho pra `canceled`/`past_due`) reaproveitando as
mesmas classes CSS já usadas no Opportunity Center, em vez do texto
cinza simples de antes. O Dashboard do promotor ficou reduzido aos 4
KPIs (faixa atual, indicações ativas, a receber, já recebido) + 3
botões de atalho (Indicações/Chats/Portfólio de Vendas) - menos
redundante com a nova aba, sem duplicar a lista de hospedagens em dois
lugares com o mesmo id de elemento.

2 chaves i18n novas (`nav.referrals`, `topbar.subtitle.referrals`) nos
11 idiomas do `i18n-dashboard-data.js` (1.154→1.156), inseridas com o
mesmo script Python descartável de sempre (âncora num texto vizinho já
existente, indentação copiada, apagado depois de rodar
`tools/check_i18n_parity.py` com sucesso). Testado sem precisar de
banco isolado nem Flask test client - mudança 100% de frontend (HTML/
JS/i18n), nenhuma rota nem tabela nova: balanceamento de chaves/
parênteses/colchetes do `dashboard.html` conferido a cada edição;
contagem de `<section>`/`<div>` comparada contra o HEAD anterior à
sessão, confirmando que o delta de 1 tag já existente (não introduzido
agora, provavelmente uma correspondência falsa de regex dentro de uma
string/comentário JS em algum lugar do arquivo de 11 mil+ linhas)
permaneceu exatamente igual antes e depois; `openPage()`/`updateTopbar()`
conferidos como genéricos (sem lista fixa de ids de página), então a
aba nova não precisou de nenhum código extra pra funcionar.

Fora de escopo: não foi criada nenhuma lógica nova pra `account_kind`
em `PAGE_LABELS`/`switchSettingsSection()` além do necessário pro
promotor - outras contas (`lodging`/`agency`) continuam exatamente
como estavam, sem nenhum comportamento alterado.

### Lapidação final do painel do promotor (v1.96.0)

Usuário testou a v1.95.0 ao vivo (via "visitar painel" do admin) e
mandou uma lista de 9 observações numa tacada só, sem esperar eu
implementar uma de cada vez - a mesma disciplina de agrupar pedidos já
estabelecida nesta sessão. Antes de tocar em qualquer HTML, valia
entender por que um problema específico estava acontecendo: o card
"Marca (White-label)" (gated só por `data-required-permission="branding"`)
aparecia pro admin em visita mesmo o promotor não tendo essa permissão.
Investigação confirmou a MESMA causa raiz já documentada na v1.95.0 -
`build_session_payload()` concede `permissions=ALL_PERMISSIONS` de
propósito durante impersonation, então qualquer elemento gated só por
permissão (sem `data-hide-for-account-kind` de reforço) vaza durante
visita do admin. Corrigido acrescentando o atributo faltante no card de
Marca e no card principal de Billing (dois que tinham escapado da
blindagem da v1.95.0), e generalizado: o modal de Notificações
(`openNotificationsModal()`) tinha o mesmo problema por um motivo
diferente - seu conteúdo é injetado via `openGenericModal()` DEPOIS da
hidratação inicial da página, então `applyPermissionVisibility()`
(chamada manualmente logo após a injeção, desde antes desta sessão)
nunca era acompanhada de `applyHideForAccountKind()` - corrigido
chamando as duas juntas. Esse padrão (permissão sozinha não é
suficiente pra decidir visibilidade quando existe impersonation) fica
registrado aqui porque é bem provável que apareça de novo em qualquer
card/modal futuro gated só por `data-required-permission`.

**Dashboard**: os 3 botões de atalho (Ver link/Chats/Portfólio,
adicionados na v1.95.0) saíram - usuário achou redundante ter atalho
pra abas que já estão logo ali no menu. Entrou um gráfico "Seu
desempenho" em Canvas nativo, reaproveitando o MESMO padrão de
`renderChatActivityChart()` de Relatórios (linha/área em gradiente,
sem biblioteca externa, já que nenhuma página do dashboard carrega
chart lib) - só que em barras, uma por mês, com a comissão total
gerada. O dado já existia: `history` (últimos 50 lançamentos do
`subscription_referral_ledger`) já vinha dentro do payload de
`/promoter/dashboard` desde a v1.86.0, mas o frontend nunca tinha
usado esse campo pra nada. Bucketing por mês feito 100% client-side
(`bucketPromoterHistoryByMonth()`), zero SQL novo.

**Nova aba "Carteira"** (pedido que chegou separado, no meio da
implementação: "também criar uma aba 'carteira' ou 'financeiro'"): usa
o MESMO payload do gráfico (zero fetch novo) pra mostrar a receber/já
recebido, um relatório mensal (mesmo bucketing por mês, reaproveitado)
e o extrato linha a linha - qual hospedagem gerou qual comissão, a
%, o status (`accrued`/`paid_out`) e as duas datas. `renderPromoterWallet()`
e `renderPromoterPerformanceChart()` rodam juntas dentro de
`loadPromoterHomeData()`, que já era chamada uma vez só na hidratação
da home do promotor - as duas abas (Dashboard e Carteira) ficam
sempre atualizadas ao mesmo tempo, sem re-fetch ao trocar de página.

**Botão flutuante "+"** (`.reserva-floating`, "Nova reserva") ganhou
`data-hide-for-account-kind="promoter"` - óbvio em retrospecto (conta
sem hospedagem não tem reserva pra criar), mas só apareceu porque
nunca tinha um usuário promotor testando ao vivo antes.

**Ask StayFlow** voltou ao tratamento visual do `index.html`: o botão
flutuante usava uma máscara CSS (`-webkit-mask-image` aplicando
`background-color:#06101b` sólido por cima do logo, dentro de um
círculo com gradiente azul) - o efeito real era uma silhueta escura
numa bolha azul, perdendo o gradiente de verdade das ondas do logo.
Trocado por `<img src="logo2.png">` direto, sem fundo, só um
`drop-shadow` leve pra manter a sensação de flutuar - exatamente como
a landing page já fazia. O reposicionamento na aba Chats
(`body.chats-page-active .ask-floating{bottom:...}`, pra não tampar o
botão "Assumir" da barra de envio) já existia de uma versão anterior e
não precisou de nenhuma mudança - só troquei o conteúdo interno do
botão, as regras de posição continuam batendo no mesmo seletor CSS.
Boas-vindas e as 3 sugestões-atalho do painel (`Quais oportunidades
existem hoje?`/`Quem precisa de resposta humana?`/`Onde posso aumentar
receita?`) também eram 100% hospedagem - ganharam
`data-hide-for-account-kind="promoter"` e 3 sugestões próprias
(`data-required-permission="promoter"`) ao lado; texto de boas-vindas
trocado via JS (`#askSubtitle`/`#askWelcomeMsg`, novos ids só pra isso)
na mesma função de hidratação que já troca a aba padrão de
Configurações pro promotor.

**Configurações > Segurança**: "Trocar senha" era um formulário fixo
direto na tela (3 campos + botão sempre visíveis) - virou o mesmo
padrão "card-resumo → clique → modal" já usado em WhatsApp/Facebook/
Instagram/Nuvemshop/etc (`openChangePasswordModal()` chamando
`openGenericModal()`). Como os 3 `<input>` mantiveram os MESMOS ids
(`currentPasswordInput`/`newPasswordInput`/`confirmPasswordInput`),
`submitChangePassword()` (que já lia por `getElementById`) não
precisou de nenhuma alteração - só migraram de morada, o comportamento
é idêntico.

**Onboarding**: dois mecanismos de "primeiro acesso" ainda falavam
100% linguagem de hospedagem pro promotor - o tour inicial de 5 slides
do Dashboard (`dashboardIntroSlides()`, que já tinha uma ramificação
pra `isAgency` mas nada pra promotor, caindo no texto padrão de
"ocupação, reservas") e as dicas rápidas por página
(`FEATURE_COACH_MARKS`, ex: a de "settings" dizia "Dados da
hospedagem, integrações, segurança e mais"). Resolvido com uma
ramificação própria em cada um: `dashboardIntroSlides()` ganhou um
`if(accountKind === "promoter")` retornando 4 slides falando dos KPIs/
gráfico/menu de verdade dessa conta; novo `FEATURE_COACH_MARKS_PROMOTER`
com overrides pra "settings" e dicas exclusivas pras páginas que só
essa conta vê (`referrals`/`wallet`/`chats`/`salesportfolio`, nenhuma
dessas existia no dicionário genérico antes). `stayflowMaybeShowFeatureIntro()`
e `showFeatureCoachMark()` ganharam um segundo parâmetro opcional
(`infoOverride`) pra aceitar o dicionário certo sem duplicar a lógica
de exibição/dispensa (que continua uma só, compartilhada).

**Portfólio de Vendas reconstruído** - de longe a parte mais trabalhosa
desta versão. Pedido do usuário foi explícito: não é só um deck de
venda, é "uma carta de estudo" também, precisa ter "imagens, explicação
de como funciona" e o promotor tem que poder perguntar pro Ask
StayFlow se tiver dúvida. Decisões tomadas:
- **4º setor novo, "Imobiliárias"** (antes só Hospedagens/Agências/
  Locadoras) - conteúdo escrito do zero cobrindo o problema real desse
  setor (leads que chegam fora do expediente, corretor cruzando
  manualmente pedido × estoque), como a StayFlow resolve (sincronização
  com Tokko Broker + matching por IA, mesma integração documentada nas
  auditorias anteriores da imobiliária, ainda pendente de outros
  ajustes fora do escopo desta versão) e recursos principais.
- **Slide novo em TODOS os 4 setores: "Como apresentar isso"** - antes
  o deck só tinha problema/solução/recursos/planos, puro material de
  marketing. Esse slide novo é a parte de "estudo" de verdade: uma
  dica concreta de que pergunta abrir a conversa, qual objeção mais
  comum e como quebrar, específica de cada setor - transforma o
  material de "o que é o produto" pra "como eu vendo isso na prática".
- **Ícone por slide** (SVG inline, cor variando por tipo: vermelho pra
  problema, azul pra solução, ciano pra recursos, amarelo pra "como
  apresentar", verde pra planos) - a pedido explícito de ter "imagens"
  no material; sem nenhum asset de foto real disponível pros 4 setores,
  ícone vetorial foi a escolha mais honesta (nada de hotlink de imagem
  genérica de banco de imagens).
- **Botão "Perguntar ao Ask StayFlow sobre isso" em cada slide**
  (`askAboutPortfolioSlide()`): abre o painel e manda uma pergunta já
  montada com o título + corpo + bullets do slide atual embutidos como
  contexto direto na mensagem. Decisão consciente de NÃO ensinar o
  backend a rastrear "em qual slide a pessoa estava" (função nova,
  campo de sessão novo, mais uma camada de estado pra manter
  sincronizada) - embutir o próprio conteúdo do slide na pergunta é
  mais simples e não menos confiável: a IA recebe o fato concreto que
  precisa pra responder, e `PROMOTER_SYSTEM_PROMPT` (v1.94.0) já era
  genérico o bastante sobre "o que é a StayFlow" pra completar bem a
  resposta sem nenhuma mudança de backend.

**i18n** - motivado por duas mensagens separadas do usuário no meio da
sessão ("a introdução de explicação... estão pra hotéis, tem que
ajeitar pra promotor" e, ainda mais direto, "percebi também que não
traduz direito, traduz os menus mas o conteúdo continua em português
sempre"). Auditoria rápida (script comparando todo `data-i18n="..."`
usado no HTML contra as chaves existentes no dicionário pt) confirmou:
quase tudo que eu tinha construído nesta rodada E na v1.95.0 (Carteira,
Indicações, gráfico do Dashboard, sugestões do Ask StayFlow, cabeçalho/
abas do Portfólio de Vendas) tinha sido escrito como texto Português
puro direto no HTML/JS, sem passar pelo sistema de tradução - exatamente
a reclamação do usuário, e o motivo real por trás dela (não é que a
tradução "falhe", é que esse conteúdo específico nunca tinha `data-i18n`
nem `T()` nenhum). Corrigido convertendo todo o texto ESTRUTURAL (
rótulos de KPI, cabeçalhos de card, texto de botão, cabeçalho de coluna
de tabela, mensagens de estado vazio, mensagens de JS como "Link
copiado!") pra `data-i18n`/`T()`, com 43 chaves novas inseridas nos 11
idiomas via o mesmo script Python descartável de sempre (âncora num
texto vizinho, indentação copiada, `tools/check_i18n_parity.py` rodado
com sucesso antes de apagar o script). Decisão de escopo explícita, não
silenciosa: o corpo/bullets de cada um dos ~20 slides do Portfólio de
Vendas e os parágrafos do tour inicial do Dashboard continuam só em
português - mesmo precedente já aceito na v1.94.0 ("sem chaves i18n
novas, mesma convenção de texto fixo do `ReferralPartner.html`"),
traduzir prosa extensa de vendas pra 11 idiomas com qualidade de
verdade é uma ordem de grandeza de esforço diferente de rótulo curto
de interface, e sinalizei isso direto pro usuário em vez de fingir que
cobri 100%.

Nenhuma mudança de backend/banco nesta versão - tudo dashboard.html +
i18n-dashboard-data.js + app.css. Testado com balanceamento de chaves/
parênteses/colchetes do `dashboard.html` conferido a cada edição
(inclusive checando que o delta pré-existente de 1 tag `<section>`/
`<div>` já documentado na v1.95.0 continuou exatamente igual) e
`tools/check_i18n_parity.py` confirmando as mesmas 1199 chaves nos 11
idiomas.

### Tradução completa do Portfólio de Vendas e do onboarding (v1.97.0)

A v1.96.0 tinha feito uma escolha deliberada de escopo, documentada
explicitamente: traduzir todo o texto ESTRUTURAL (rótulos, botões,
cabeçalhos) mas deixar o conteúdo longo do Portfólio de Vendas e os
parágrafos do tour inicial só em português, pelo mesmo precedente já
usado na v1.94.0. O usuário rejeitou essa escolha sem meio-termo:
"quero que esteja tudo traduzido, tem que funcionar direito isso". Não
é uma reclamação pra negociar escopo de novo - é uma instrução direta.
Então esta versão existe pra reverter completamente aquela decisão e
traduzir de verdade tudo que tinha ficado de fora.

O volume aqui é bem maior que qualquer rodada anterior de i18n desta
sessão: 20 slides do Portfólio de Vendas (4 setores × 5 slides, cada
um com título + corpo + às vezes 4-5 bullets) e as 3 variantes do tour
inicial do Dashboard (padrão/hospedagem, agência, promotor), mais as
14 dicas de primeiro-acesso genéricas e as 5 do promotor. Pra manter
isso gerenciável, o trabalho foi dividido em 5 scripts Python
descartáveis sequenciais (um por setor do Portfólio + um pro
onboarding inteiro), cada um rodado e verificado (`check_i18n_parity.py`)
antes do próximo, em vez de um script gigante único mais arriscado de
revisar. Ao todo, 104 chaves novas em 11 idiomas - a maior inserção de
i18n numa versão só desde o início da disciplina de i18n nesta sessão.

Decisão de arquitetura que valeu a pena documentar: em vez de
acrescentar um campo `key` extra em cada um dos 20 objetos de slide
(seria só mais um lugar pra errar/esquecer de manter sincronizado), a
chave é montada na hora a partir do que JÁ existe -
`"salesPortfolio." + portfolioCurrentSector + "." + slide.kind` - já
que setor + tipo de slide (problem/solution/features/pitch/plans) já
formam um caminho único por definição (cada setor tem exatamente um
slide de cada kind). Isso ficou centralizado numa função só,
`portfolioSlideText(slide)`, que devolve `{title, body, bullets}` já
resolvidos via `T()` com o fallback em português original - tanto
`renderPortfolioSlide()` (o que aparece na tela) quanto
`askAboutPortfolioSlide()` (o que é mandado pro Ask StayFlow) chamam
essa mesma função, então a pergunta enviada pra IA agora usa o texto
JÁ traduzido pro idioma ativo, não mais o fallback em português fixo -
inclusive o próprio template da pergunta ("Sobre \"{title}\": {context}
- pode me explicar melhor...") virou uma chave traduzida
(`salesPortfolio.askQuestionTemplate`) com placeholders.

Pro onboarding, cada slide de `dashboardIntroSlides()` ganhou
`titleKey`/`bodyKey` ao lado do `title`/`body` (fallback) já existente
- mesma convenção `T(chave, fallback)` usada em todo o resto do
arquivo. Um detalhe que economizou uma chave inteira: o slide
"Opportunity Center" (mesmo nome em hospedagem e agência) reaproveita
a chave `nav.opportunities` que já existe e já está traduzida nos 11
idiomas pro menu lateral - zero motivo pra duplicar essa tradução só
porque o texto aparece em outro lugar da tela. A mesma lógica se
aplicou a `FEATURE_COACH_MARKS`/`FEATURE_COACH_MARKS_PROMOTER`: o
título de cada dica (ex.: "Chats", "Financeiro", "Configurações") já é
literalmente o mesmo texto do item de menu correspondente, então
reaproveitou `nav.chats`, `nav.finance`, `nav.settings` etc direto -
só o texto explicativo de cada dica precisou de chave nova
(`onboarding.coach.<página>.text`). Isso quase cortou pela metade o
número de chaves que esse bloco exigiria se cada dica tivesse ganho
título E texto novos. Único cuidado necessário: "chats" e "settings"
existem tanto na versão genérica quanto na do promotor com textos
DIFERENTES - resolvido com um namespace separado
(`onboarding.coach.promoter.chats.text` vs `onboarding.coach.chats.text`)
pra essas duas chaves especificamente, evitando colisão.

Verificação final em 3 camadas: `tools/check_i18n_parity.py` (as
mesmas 1303 chaves nos 11 idiomas, contra as 1199 antes desta
versão); balanceamento de chaves/parênteses/colchetes do
`dashboard.html` depois de cada uma das 5 rodadas de edição; e um
script de auditoria feito especificamente pra esta versão, que extrai
TODO argumento de `T(...)` usado no arquivo inteiro (não só o que eu
mexi) e compara contra o dicionário em português - confirmando que
nenhuma chave nova desta versão OU da v1.96.0 ficou sem tradução.

Esse último script revelou um achado que não é meu de resolver agora,
mas que precisa ficar registrado e comunicado: sobraram cerca de 70
chaves de `T(...)` usadas no `dashboard.html` que não existem no
dicionário - todas de módulos que esta sessão nunca tocou (modais de
"novo pedido" de Cozinha/Manutenção/Estacionamento/Segurança
Patrimonial, cadastro de item do Portfólio de agência, conexão de
Mercado Pago/Nuvemshop/WhatsApp). São textos que já rodavam há muito
tempo com o fallback em português sempre ativo (a chave nunca existiu
em idioma nenhum, nem no próprio português) - um gap de i18n real e
pré-existente do sistema, não um efeito colateral de nada feito no
painel do promotor. Sinalizado ao usuário explicitamente em vez de
deixar escondido; fica como candidato claro pra uma rodada de i18n
dedicada, separada do trabalho do promotor.

Nenhuma mudança de backend/banco nesta versão - tudo
`dashboard.html` + `i18n-dashboard-data.js`.

### Vazamento entre contas, payout do promotor e dados do cliente (v1.98.0)

Usuário testou ao vivo de novo, dessa vez numa hospedagem comum
("Swing", `account_kind='lodging'`, plano Starter em trial) visitada
via impersonation, e achou um bug real: "Indicações", "Carteira" e
"Portfólio de Vendas" apareciam no menu dela, coisa que só devia
existir pra conta de promotor. Antes de corrigir, valia entender por
que - resposta era a MESMA causa raiz já documentada duas vezes nesta
sessão (v1.95.0 pro card de Marca/Billing, v1.96.0 pros checkboxes de
notificação): esses 3 itens de nav (mais as 3 sugestões correspondentes
do Ask StayFlow) eram gated só por `data-required-permission="promoter"`,
e `build_session_payload()` concede `permissions=ALL_PERMISSIONS` de
propósito durante impersonation - então qualquer hospedagem visitada
pelo admin "ganha" a permissão `promoter` de graça, mesmo sendo lodging.
Corrigido acrescentando `data-required-account-kind="promoter"` nos 6
elementos - `account_kind`, diferente de permissão, é sempre o valor
real da hospedagem visitada, nunca inflado.

Dado que essa é a TERCEIRA vez que o mesmo padrão de bug aparece nesta
sessão (Marca/Billing → checkboxes de notificação → agora nav items
inteiros vazando pra hospedagem errada), virou memória de feedback
permanente (`feedback_permission_vs_accountkind_isolation.md`,
salva fora do repositório, no sistema de memória entre sessões) em vez
de só mais uma correção pontual - a regra fica registrada pra qualquer
sessão futura: nunca gatear UI exclusiva de `account_kind` só por
permissão, sempre parear com `data-required-account-kind`/
`data-hide-for-account-kind`, exatamente porque impersonation quebra
esse gate sozinho.

**Correção de escopo em cima de correção** - episódio educativo à
parte: o usuário tinha pedido que o botão flutuante do Ask StayFlow
voltasse a ter "o mesmo tamanho e posição do index" (sem círculo, logo
grande de 160px). Implementei isso como mudança GLOBAL em `app.css`
(`.ask-floating`), já que a frase não mencionava escopo nenhum. Só
depois, testando numa hospedagem normal, o usuário esclareceu que a
intenção real era só pro promotor - o resto das contas devia continuar
com o círculo azul de sempre. Isso é diferente dos vazamentos reais
acima (aqueles eram bug não-intencional; esse foi eu interpretando
escopo errado numa instrução ambígua) mas o resultado prático pro
usuário foi o mesmo tipo de sintoma ("mudou onde não devia"), e ele
próprio conectou os dois como parte do mesmo problema de isolamento -
por isso a correção entrou junto nesta versão. Solução: revertido o
`.ask-floating` de base pro circulo original (`<span
class="brand-logo-mask">` com mask-image, `var(--floating-btn-size)`,
gradiente azul), e a variante nova isolada atrás de
`[data-account-kind="promoter"]` no PRÓPRIO botão (atributo setado via
JS na mesma função de hidratação que já troca outros textos só pro
promotor) - o span ganhou `data-hide-for-account-kind="promoter"`, o
`<img>` ganhou `data-required-account-kind="promoter"` com
`style="display:none"` de segurança antes da hidratação rodar. Duas
lições double-checked na mesma correção: reaproveitar o MESMO mecanismo
genérico de sempre (não inventar uma solução ad-hoc), e o CSS troca o
container inteiro via atributo no próprio elemento, não só o conteúdo
interno - importante porque a versão do promotor muda `width`/`height`/
`background` do botão inteiro, não só o ícone.

**Dados de recebimento do promotor** - pedido direto: "pode colocar
uma conectividade de conta também pro promotor receber pagamentos".
Decisão de escopo consciente: NÃO construir OAuth/API de pagamento de
verdade (Mercado Pago Connect ou similar) - o programa de indicação
inteiro já funciona com repasse 100% MANUAL desde a v1.65.0
(`subscription_referral_ledger.status`, marcado `paid_out` a mão pelo
admin), então automatizar o RECEBIMENTO sem automatizar o PAGAMENTO
seria meia solução arriscada (superfície de integração financeira nova
pra um fluxo que continua manual do outro lado). Em vez disso: 2
colunas novas em `referral_partners` (`payout_method` - só rótulo
`mercadopago`/`pix`/`bank`, nunca validado contra processador nenhum -
e `payout_details`, texto livre), nova `PUT /promoter/payout-info`
(mesmo molde de `PUT /promoter/contact`, já existente desde a v1.87.0),
card "💳 Como você quer receber" na aba Carteira (mesmo padrão
"card-resumo → clique → modal" de sempre) e o mesmo dado surfaced pro
admin no painel "Ver detalhes" de `admin.html` (`_referral_partner_dashboard_payload()`
já compartilhado entre o painel do próprio promotor e o do admin,
zero rota nova pro lado do admin - só os 2 campos passaram a vir
junto no payload que já existia).

**Dados completos do cliente** - achado ao vivo revisando o
`admin-hostel.html` de "Swing": só mostrava o e-mail da HOSPEDAGEM
(`hostels.email`, que às vezes nem é o e-mail de quem se cadastrou, é
só copiado do e-mail de login no `/register`), nunca o nome de
verdade da pessoa, telefone ou endereço - "eu deveria conseguir ver os
dados do cliente [...] tem que ter tudo isso do cliente registrado
também pra que eu tenha a informação completa". Investigação encontrou
duas coisas boas antes de escrever qualquer código novo: (1) o nome
real da pessoa JÁ era capturado desde sempre (`admin_name` no
`/register`, salvo em `users.name`) - só nunca tinha sido
surfaced pro admin, um gap de exibição, não de coleta; (2) endereço
também já existia como campo opcional em Configurações > Empresa
(`settings.address`, usado pra confirmação de reserva por WhatsApp) -
adicionar uma coluna `hostels.address` duplicada teria sido o
caminho errado (dado duplicado, duas fontes de verdade pra mesma
informação); revertido antes de commitar depois de perceber isso.
Nova `get_hostel_owner_and_address()` busca o nome/e-mail de quem tem
o `hostel_membership` mais antigo daquela hospedagem (o Admin original
criado por `create_identity_and_hostel`) + o endereço de `settings`,
num JOIN só. O único dado genuinamente NUNCA coletado era telefone -
a coluna `hostels.phone` já existia no schema desde sempre (usada em
`get_hostel()`/`hostel_profile()`), mas nada em nenhum fluxo de
registro escrevia nela. Adicionado como campo obrigatório em AMBOS os
2 pontos de entrada públicos de `/register` (`Register.html` e
`PromoterSignup.html` - confirmado que são os únicos 2 arquivos que
chamam essa rota, `/account/add-hostel` usa uma função de banco
diferente e não precisou de mudança). `create_identity_and_hostel()`
ganhou o parâmetro `phone` opcional (só usado pelo `/register`,
`/account/add-hostel` continua sem telefone de propósito - é uma ação
de quem já está logado, não um cadastro novo de pessoa desconhecida).

Testado em banco isolado com Flask test client de ponta a ponta:
registro sem telefone rejeitado com 400; registro com telefone grava
`hostels.phone` corretamente; `get_hostel_owner_and_address()` devolve
nome/e-mail reais da pessoa que se cadastrou; fluxo completo de
promotor (registro → login → `PUT /promoter/payout-info` → `GET
/promoter/dashboard` confirmando os 2 campos novos no payload); método
de payout inválido rejeitado com 400. Também: balanceamento de chaves/
parênteses/colchetes do `dashboard.html` e `admin.html` conferido após
cada rodada de edição, `tools/check_i18n_parity.py` confirmando as
mesmas chaves em todos os 11 idiomas (3 chaves novas no `ADMIN_I18N`
pro rótulo de payout no "Ver detalhes", 7 chaves novas no dicionário
do dashboard pro card de Carteira).

### Sessão de admin presa ao trocar de propriedade em visita (v1.99.0)

Achado ao vivo, no meio de uma investigação de "o app tá travando" -
usuário estava impersonando "Swing" (hospedagem normal), usou o
seletor de propriedades do topo (que durante visita sempre lista as
PRÓPRIAS hospedagens do admin, já que `user_id` nunca muda em
impersonation) pra ir direto pra "Imobiliária Teste", e a partir daí
não conseguia mais voltar pro próprio painel - o painel interno chegou
a mostrar "Não foi possível carregar o painel".

Antes de mexer em qualquer coisa, precisava confirmar se isso era
regressão de algo feito hoje ou um bug pré-existente. Checagem
estrutural primeiro (contagem de `<script>`/`<section>`/`<div>` no
`dashboard.html`, comparando com a mesma contagem no commit de
v1.94.0, ANTES de qualquer trabalho desta sessão) - os dois pequenos
desbalanços que já apareciam (`<script>` 14/12, `<section>`/`<div>`
com delta de 1) já existiam identicamente em v1.94.0, então não eram
a causa. Isso descartou hipótese de HTML quebrado por uma das minhas
edições e apontou pra procurar no fluxo de sessão/impersonation em si.

Achado real, em `routes/auth.py::select_hostel()`: a rota atualiza
`sessions.hostel_id` via `update_session_hostel()` mas nunca toca
`sessions.impersonating_from_hostel_id` (coluna separada, gravada por
`/stayflow-admin/impersonate` como "endereço de volta"). A resposta
dessa chamada específica não denuncia o problema (`build_session_payload()`
é chamado sem passar o flag, então o JSON de resposta sempre diz
`impersonating:false`), mas o banco continua com o valor antigo -
`GET /me` (usado em qualquer F5 ou navegação nova) LÊ esse flag do
banco via `session_data.get("impersonating_from_hostel_id")` e reabre
a "visita" com o destino ERRADO (o hostel de origem de ANTES de visitar
Swing, não Swing nem Imobiliária Teste). Resultado: a pessoa fica
girando entre contas sem nunca conseguir fechar de vez o ciclo, porque
toda vez que ela pensa que saiu, o próximo carregamento reabre a visita
fantasma.

O raciocínio que fechou a correção: usar o seletor NORMAL de
propriedades (que só lista as próprias hospedagens do usuário logado)
enquanto "em visita" só pode significar uma coisa - a pessoa quer
abandonar a visita e ir pra uma conta de verdade dela. Não existe
cenário legítimo de querer continuar "visitando" depois de escolher
explicitamente uma das próprias contas por esse caminho. Fix de uma
linha: `select_hostel()` chama `set_session_impersonation(session_id, None)`
antes de trocar o hostel - função que já existia (usada por
`stop_impersonating()`), só nunca tinha sido chamada daqui.

Confirmado que é bug pré-existente (mecanismo de impersonation é da
v1.47.0, muito antes desta sessão) - só nunca tinha sido testado nessa
combinação específica (impersonation ativa + troca de propriedade
PRÓPRIA pelo seletor normal, não pelo botão "Sair da visualização").
Reproduzido em banco isolado com Flask test client (2 hospedagens
próprias do admin + 1 cliente real registrado num client HTTP
separado, pra não contaminar o cookie de sessão do admin - achado
lateral do próprio processo de teste: `/register` faz auto-login de
quem acabou de se cadastrar, então registrar um cliente de teste no
MESMO client HTTP do admin sobrescreve a sessão ativa) - confirmado
que o bug reproduzia exatamente como descrito antes do fix, e que
`/me` permanece `impersonating:false` de forma estável em trocas
sucessivas depois.

Publicado com urgência, fora do ciclo normal de "testar tudo e só
então documentar com calma" - usuário estava ativamente travado em
produção no momento do achado. Órientação dada a ele em paralelo à
correção: fazer logout/login pra limpar a sessão já corrompida, já
que o fix impede o problema de acontecer de novo mas não conserta
retroativamente uma sessão que já ficou gravada com o flag preso no
banco.

### Auditoria de 7 achados no produto imobiliária (v1.100.0)

Com o painel do promotor "lapidado" (v1.95.0-v1.99.0) e o nome da
indicadora do setor imobiliário confirmado (Julia de Luna, Bauru-SP,
pra apresentação de parceria comercial), usuário aprovou seguir direto
pra uma lista de 7 achados de uma auditoria anterior do lado
imobiliária do produto - nenhum deles crítico isoladamente, mas juntos
formavam uma experiência capenga pra quem realmente vende imóvel pela
plataforma.

O mais revelador dos 7 foi o quarto: `real_estate_details` (operação,
localização, quartos, banheiros, m²) existia desde a v1.72.0 (sync do
Tokko Broker), mas era uma tabela alimentada só numa direção. O sync
automático escrevia nela via `upsert_real_estate_details()`, só que
`list_portfolio_items()` e `get_portfolio_item()` nunca faziam o JOIN
de volta - os dados existiam no banco mas eram invisíveis pro
frontend mesmo pra quem tinha sincronizado corretamente. E o
formulário manual de "Novo item" nunca soube que essa tabela existia,
então uma imobiliária cadastrando um imóvel à mão (sem usar o Tokko)
perdia justamente os campos que mais importam pra esse tipo de
negócio. Dois lados da mesma lacuna, corrigidos juntos: JOIN nos dois
SELECTs de leitura, e `_save_real_estate_fields()` novo gravando o que
o formulário manual manda - com uma decisão deliberada de só gravar
quando pelo menos 1 dos 5 campos vier na requisição, pra não criar uma
linha real_estate_details vazia (só NULLs) pendurada em item que não é
imóvel nenhum (ex: um city tour cadastrado por uma agência de
turismo).

Os outros achados eram mais diretos, mas cada um carregava uma causa
raiz do tipo "generalização que esqueceu de checar a categoria
específica": o ícone ✈️ de agência genérica aparecendo pra imobiliária
em 7 pontos do admin (todos alimentados pela mesma
`get_stayflow_admin_overview()`, resolvido estendendo o SELECT uma vez
só com `agency_category` e criando `kindIcon()` como ponto único de
decisão do ícone certo); o Tokko Broker sempre pedindo texto em
espanhol (`lang=es_ar` hardcoded) mesmo pra imobiliária brasileira -
bug latente que nunca deu problema porque nenhuma imobiliária real
tinha conectado uma API key ainda, mas que ia gerar operação/tipo em
espanhol na cara de qualquer sync real; "Hóspede" hardcoded em 3
lugares que deveriam dizer "Cliente" pra imobiliária (resolvido
reaproveitando `agencyGuestNoun()`, que já existia e já sabia
diferenciar PAX de Clientes por categoria - só faltava esses 3 pontos
chamarem a função); e o botão "Oferecer imóvel" que abria um modal de
"Gerar cobrança" do Mercado Pago (fluxo herdado do "Oferecer item"
genérico) quando o que faz sentido pra imóvel é mandar uma mensagem
pro cliente com os detalhes, não cobrar na hora - resolvido com um
modal de mensagem editável reaproveitando `POST /guests/<id>/send-message`,
endpoint que já existia pro chat manual e não precisou de nenhuma
alteração.

Padrão que se repetiu nos 7: nenhum exigiu rota nova, tabela nova ou
mecanismo novo - cada um era uma generalização (ícone de agência,
idioma da API, nome de "hóspede", ação de "oferecer item") que nunca
tinha sido especializada pro caso da imobiliária desde que a categoria
foi introduzida. Testado em banco SQLite isolado com Flask test client:
criar item de imóvel manualmente grava e devolve os 5 campos; PATCH
mandando só descrição não apaga os campos de imóvel já existentes
(só sobrescreve quando o campo vem de novo na requisição); item comum
(sem nenhum campo de imóvel) continua com tudo `NULL` sem quebrar
leitura nem criar linha vazia; `sync_tokko_properties()` com
`requests.get` mockado confirma que `lang=pt_br` é o valor realmente
enviado e que os campos de imóvel do Tokko chegam certos no portfolio
depois do sync. 20 chaves i18n novas em 11 idiomas (1.303→1.335) mais
3 no `ADMIN_I18N` (292→295, painel de payout do parceiro de indicação).

### Refinamento profundo da imobiliária + bug universal do Suporte (v1.101.0)

Usuário pediu sugestões pra "deixar mais completo" o produto do lado
imobiliária, já com a apresentação da Julia de Luna se aproximando.
Listei 7 pontos (galeria de fotos, preço formatado por operação,
código de referência, filtros estruturados no matching, sync
automático do Tokko, amenidades/condomínio/IPTU, área útil vs. total)
e o usuário aprovou fazer todos de uma vez: "pode fazer todas essas
atualizações na imobiliária".

No meio do levantamento técnico, uma mensagem à parte mudou a
prioridade: "uma coisa que senti falta em todos os menus foi a aba de
suporte... entra na lista". Investigando antes de tocar em qualquer
coisa da imobiliária, achei um bug bem mais sério do que uma lacuna de
UI: a aba "Suporte" nunca aparecia pra NINGUÉM, em NENHUM tipo de
conta - não era um problema específico de promotor ou agência.
`hideNavItemsWithoutPermission()` usa `data-page` como chave de
permissão implícita quando o botão não tem `data-required-permission`
explícito (mesmo mecanismo documentado nas sessões anteriores sobre o
menu do promotor) - e `"support"` nunca foi cadastrado em
`ALL_PERMISSIONS` (`utils/permissions.py`). Resultado:
`hasAnyPermission("support", permissions)` sempre devolvia `false`,
pra qualquer permissão que a conta tivesse, desde que essa lógica de
menu existe. O backend do Suporte (`support_bp`, `list_support_threads()`,
`loadSupportThread()`) sempre esteve funcional - só a porta de entrada
no menu é que nunca funcionou. Corrigido excluindo `"support"` do
check de permissão dentro de `hideNavItemsWithoutPermission()`: o
canal de contato direto com a equipe StayFlow não é uma área de dado
sensível por permissão, então não faz sentido estar sujeito ao mesmo
gate de "dashboard"/"finance"/etc.

Dos 7 itens da imobiliária, o mais revelador tecnicamente foi o de
sync automático do Tokko. O escopo original pedido era "webhook do
Tokko" - mas o próprio arquivo já carregava uma nota honesta desde a
v1.72.0 dizendo que os nomes de campo da API nunca foram testados
contra uma resposta real, porque nenhuma imobiliária tinha conectado
uma chave de verdade ainda. Escrever um receptor de webhook
especulativo, sem contrato verificado, corria o risco real de nunca
bater com o payload de verdade quando o primeiro cliente conectasse -
e ficaria pior que não ter nada, porque pareceria funcionar até o dia
em que alguém dependesse dele. Troquei por resync automático
periódico (a cada 6h, `_tokko_resync_loop` em `app.py`, no mesmo
padrão dos outros 3 laços em background que já existem desde a v1.59.0/
v1.60.0-era) - reaproveita o caminho de sync que já é testado e
funcional, resolve o mesmo problema prático (catálogo desatualizado
entre cliques manuais em "Sincronizar agora"), e não inventa contrato
nenhum. Decisão comunicada ao usuário como uma troca deliberada de
escopo, não escondida.

Implementar os campos novos (`reference_code`, `useful_area_m2`,
`condo_fee`, `iptu_fee`, `amenities`) expôs um bug real que eu mesmo
quase reintroduzi: `upsert_real_estate_details()` sempre sobrescrevia
TODOS os campos recebidos, inclusive com `None` quando um campo
simplesmente não vinha na chamada. Isso já era um risco arquitetural
desde a v1.72.0 (só não dava problema porque o formulário manual
sempre mandava os 5 campos originais juntos), mas com os 5 campos
novos ficou concreto: um resync automático do Tokko (que só conhece
os 5 originais, nunca amenidades/código/condomínio) apagaria qualquer
enriquecimento manual a cada rodada de 6h. Resolvido tornando a função
um upsert parcial de verdade - todos os 10 campos usam um sentinela
`_UNSET` como valor default, e só entram na query quando o chamador
realmente passa o argumento. Achei isso rodando o teste isolado que
simula exatamente esse cenário (enriquecer manualmente um item vindo
do Tokko, depois rodar o resync de novo) - sem esse teste específico,
o bug só apareceria em produção depois de uma imobiliária real usar os
dois fluxos juntos.

Um segundo achado saiu do mesmo teste: o mapeamento do Tokko guardava
o rótulo de operação exatamente como a API devolve ("Venta"/"Alquiler"
em espanhol, dependendo do idioma pedido) sem normalizar pro enum fixo
(`rent`/`sale`) que o resto do sistema usa - o formulário manual, a
formatação de preço nova ("/mês" só aparece quando `operation_type ===
'rent'`) e o guard-rail de matching novo dependiam todos desse valor
bater exatamente. Um imóvel sincronizado do Tokko ficaria com o preço
formatado errado e imune ao guard-rail, silenciosamente, sem erro
nenhum aparecer em lugar algum. Corrigido com `_normalize_operation_type()`,
tolerante a variantes em espanhol e português (a mesma dupla de idiomas
que a integração realmente atende hoje), preservando o texto original
quando não reconhece nenhuma variante - nunca descarta o dado, só não
consegue mapear pro enum quando isso acontece.

O guard-rail de matching em si (`decision_engine.py`) foi desenhado
como uma segunda camada por cima da sugestão semântica que já existia,
não uma substituição dela: a mesma chamada de IA que escolhe qual
imóvel sugerir agora também extrai `property_filters` - só as
exigências que o cliente disse EXPLICITAMENTE na conversa (operação,
quartos mínimos, teto de preço), nunca inferidas. Uma função pura nova,
`_property_violates_filters()`, invalida a sugestão (`suggested_partner_item_id
= None`) se o imóvel escolhido pela IA violar algum desses filtros
explícitos - existe justamente pro caso em que o modelo "quase acerta"
por similaridade textual (ex: sugere um imóvel de 2 quartos quando o
cliente pediu literalmente "pelo menos 3"). Testável isoladamente sem
nenhuma chamada real de IA, já que é só lógica de comparação sobre um
dicionário.

Testado por completo em banco SQLite isolado com Flask test client:
os 10 campos novos gravam e retornam certo numa criação completa
(amenidade inválida enviada de propósito é filtrada); PATCH parcial
(só descrição, ou só um campo novo isolado) não apaga nada dos dois
grupos de campos, nos dois sentidos; item sem nenhum dado de imóvel
continua limpo; galeria de fotos - 1ª foto vira capa automaticamente,
2ª não sobrescreve, excluir a capa promove a próxima foto restante,
excluir a última limpa a capa pra `None`; resync automático do Tokko
mockado atualiza só os 5 campos que ele realmente manda, preservando
os 5 que só o cadastro manual conhece; guard-rail testado nos 4
cenários de violação (operação, quartos mínimos, preço máximo, e a
combinação sem filtro nenhum) mais 2 de não-violação.

### Agência tratada como hospedagem em toda a "camada de instrução" (v1.102.0)

Usuário testou o painel logado como imobiliária e notou algo que ia
além do Portfólio (já corrigido nas duas versões anteriores): "as
instruções de quando acessa pela primeira vez... também tá tratando
ainda como hospedagem" - citando especificamente Ask StayFlow, resumo
e Opportunity Center, e pedindo pra verificar TUDO que fizesse
sentido. Antes de sair corrigindo, mandei um agente de exploração
dedicado auditar o produto inteiro em busca de todo lugar que ainda
falava de "hóspede"/"reserva"/"check-in" pra uma conta agência - achado
central do relatório: existiam 3 mecanismos já maduros de diferenciação
por tipo de conta (`data-required-account-kind`, `agencyGuestNoun()`,
`applyImobiliariaPortfolioCopy()`), mas praticamente nenhum deles tinha
sido estendido pra além do Portfólio. Pra praticamente todo o resto do
produto, "agência de turismo" e "imobiliária" continuavam sendo
tratadas como a mesma coisa, e ambas continuavam meio hospedagem.

O achado mais sério não estava nem na lista original do usuário: o
prompt de sistema do Ask StayFlow (`SYSTEM_PROMPT` em
`ask_agent_service.py`) é escrito do início ao fim assumindo que quem
está do outro lado da conversa é "um funcionário/gestor do hostel" -
e esse MESMO prompt, sem nenhuma variação, era usado pra qualquer
`account_kind='agency'`. Ou seja: o assistente que fala diretamente
com o DONO do negócio (diferente da IA que atende o hóspede/lead no
WhatsApp, essa sim já bem tratada por categoria desde antes) se
apresentava pra quem administra uma imobiliária como se ela fosse uma
pousada. Enquanto corrigia isso, achei um segundo problema mais sutil,
nunca reportado: o dono/Admin de qualquer conta nova recebe permissão
TOTAL por padrão (mesmo critério de sempre, review de segurança já fez
essa checagem antes) - então o catálogo de ferramentas do Ask StayFlow
oferecia "criar reserva", "abrir chamado de manutenção",
"cadastrar pedido de cozinha" pra quem administra uma imobiliária,
mesmo essas telas já estando corretamente escondidas do menu lateral.
O prompt sozinho não bastava; era preciso também filtrar
`allowed_tools` contra `LODGING_ONLY_PERMISSIONS` quando a conta é
agência, senão a ferramenta continuava existindo por baixo de um
prompt bonito.

Padrão que se repetiu nos outros 6 achados: cada um era um mecanismo
que JÁ sabia diferenciar `account_kind='promoter'` (o painel do
promotor recebeu bastante atenção nas versões anteriores desta sessão)
mas nunca tinha sido estendido pra `account_kind='agency'` - os
textos fixos do próprio Ask StayFlow (subtítulo/boas-vindas, só
trocavam pra promotor), os coach marks de primeiro acesso por página
(só tinham variante pro promotor), e um card inteiro da home do
Dashboard ("Operação", sobre check-in/check-out) que só ficava
escondido pra hospedagem via um raciocínio já feito - só nunca
replicado pra agência. Reaproveitei o padrão de nomenclatura já
validado (PAX pra turismo/locação, Clientes pro resto) criando uma
versão em Python dele (`agency_guest_noun()` em `database.py`, espelho
exato de `agencyGuestNoun()` do frontend) - útil o bastante que também
corrigiu de quebra um bug pré-existente sem relação direta com o
pedido: `/permissions/catalog` (catálogo de cargos em Equipe) trocava
"Hóspedes" por "PAX" pra QUALQUER agência, inclusive imobiliária, que
deveria ver "Clientes".

O Opportunity Center escondia um problema pequeno mas visível: o
campo `intent` da oportunidade (booking/tour/upsell/human_help/
follow_up/general, do `decision_engine.py`) tinha um mapa de tradução
em NENHUM lugar do frontend - vazava cru em inglês na tela ("Intenção:
booking") sempre que a `description` gerada pela IA não estava
disponível. Resolvido com `intentLabel()` nova em `chats-live.js`, que
também precisou de uma ramificação própria: "booking" significa
"reserva de quarto" pra hospedagem mas "fechar negócio" pra agência -
mesmo enum, dois sentidos bem diferentes, não dava pra usar o mesmo
rótulo pros dois casos.

Testado por completo em banco SQLite isolado com Flask test client,
com a chamada real à OpenAI mockada em todos os pontos (sem custo nem
dependência de rede): `agency_guest_noun()` e
`AGENCY_CATEGORY_BUSINESS_CONTEXT_PT` corretos pra cada categoria;
`/permissions/catalog` devolve "Clientes" pra imobiliária e "PAX" pra
turismo; `/executive-summary` manda o `business_label` certo dentro do
prompt (capturado via mock da chamada) e cai no fallback certo por
`account_kind` quando a chamada falha; Ask StayFlow - prompt de
sistema mockado confirma "imobiliária"/"AGÊNCIA" no texto, e a lista
de tools realmente enviada pra API exclui `create_reservation`/
`create_kitchen_order` pra agência, com o teste espelho confirmando
que hospedagem continua com o catálogo completo (sem regressão).
