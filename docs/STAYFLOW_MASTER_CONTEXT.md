\# STAYFLOW MASTER CONTEXT

\## Documento Mestre Oficial



\*\*Documento:\*\* STAYFLOW\_MASTER\_CONTEXT.md



\*\*Versão:\*\* 1.64.0



\*\*Status:\*\* Oficial



\*\*Projeto:\*\* StayFlow



\*\*Classificação:\*\* Confidencial – Uso Interno



\*\*Última atualização:\*\* 24/08/2026



\---



\# CONTROLE DE VERSÕES



| Versão | Data | Status | Descrição |

|---------|------|--------|-----------|

| 1.0.0 | 28/06/2026 | Oficial | Primeira publicação oficial do Documento Mestre da StayFlow. |

| 1.1.0 | 01/07/2026 | Oficial | Consolidação do posicionamento do produto, atualização da arquitetura do frontend, refinamento do Dashboard Inteligente, atualização do roadmap e registro das decisões permanentes. |

| 1.2.0 | 05/07/2026 | Oficial | Publicação em produção com domínio oficial e disco persistente; conclusão e validação de ponta a ponta da integração com WhatsApp Business; registro de limitação de plataforma (restrição de mensagens cross-country Brasil/Indonésia); atualização do roadmap com dívidas técnicas de UX identificadas. |

| 1.3.0 | 09/07/2026 | Oficial | Refatoração completa da arquitetura de CSS do Frontend (tokens/reset/app/landing/auth); correção de múltiplas dívidas técnicas de UX em mobile identificadas na versão anterior; adoção do Claude Code como ferramenta de desenvolvimento assistido, incluindo criação de skill de contexto automático; novas funcionalidades no módulo de Chats (divisores de data, identificação de país por telefone); criação do processo formal de Checklist Ativo para controle de escopo. |

| 1.4.0 | 13/07/2026 | Oficial | Correção de divergência crítica de repositório Git (branch `main` desatualizada em relação a `arquitetura-v2`); publicação em produção de todos os commits pendentes desde a versão anterior; implementação e validação em produção da captura do nome do hóspede via function calling da IA; correção de múltiplos bugs reais no menu de Configurações (indicadores de status falsos, painel de Equipe desconectado); início da Fase 1 (schema) de um sistema de permissões multi-hostel; pesquisa e decisão de estratégia para integrações com OTAs (Booking.com/Airbnb); remoção de infraestrutura órfã no ambiente de hospedagem. |

| 1.5.0 | 19/07/2026 | Oficial | Conclusão e publicação em produção do sistema de permissões multi-hostel (Fases 2 e 3): identidade única de pessoa com suporte a múltiplos hostels e troca de conta sem novo login, funções configuráveis por hostel, exceções de permissão individuais com distinção visual entre herdado e ajustado manualmente. Reconstrução completa do painel de Equipe (nunca teve marcação visual antes). Menu lateral reordenado por prioridade de uso e filtrado pela permissão real de cada pessoa. Catálogo de permissões expandido de 10 para 12 chaves. |

| 1.6.0 | 21/07/2026 | Oficial | Reorganização do cabeçalho do Dashboard: card de hostel/usuário movidos da barra lateral para o topbar, menu suspenso no avatar do usuário (Equipe/Sair, filtrado por permissão). Unificação visual dos botões flutuantes (Ask StayFlow e Nova reserva). Correção do bug de persistência do card "IA" em Configurações — geração de oportunidades agora efetivamente controlável pelo administrador, validada de ponta a ponta; resposta automática desabilitada honestamente até seu pré-requisito (agente de conversa) existir. |

| 1.7.0 | 23/07/2026 | Oficial | Ask StayFlow deixou de ser mockado: agente real com function calling multi-rodada, autenticado, 34 ferramentas escopadas por permissão, endpoint `/ask` com histórico próprio em SQL. Fase de ações reais: pedido de reposição a fornecedor e aviso proativo a hóspede, ambos com fluxo propor→aprovar→enviar via WhatsApp Business; extensão automática de reserva pela IA de atendimento dentro de limite seguro (mesma diária/quarto), fora disso vira oportunidade pra equipe decidir. Novo sistema de Mapa de Quartos: modalidades de quarto configuráveis por propriedade (com padrão automático por tipo — hostel ganha Privado/Compartilhado, hotel/pousada/resort ganham Standard/Luxo), cadastro de quartos em lote, camas normais e beliches pareados, status real (livre/ocupada/precisa de limpeza) refletido em mapa visual colorido. Ciclo completo de lavanderia: check-out move cama pra lista de limpeza automaticamente, marcar como limpa desconta roupa de cama limpa do estoque e move pra "na lavanderia", com ação de devolução ao estoque quando a lavanderia retorna. |

| 1.8.0 | 23/07/2026 | Oficial | Correção de bug crítico de produção: servidor Flask sem `threaded=True` travava o site inteiro durante qualquer chamada real à IA (descoberto pelo usuário testando em produção). Reserva automática via WhatsApp: a IA de atendimento cria a reserva sozinha (status pending) com valor sempre calculado a partir do preço real configurado, nunca inventado. Hóspede agora pode ver preço real e escolher cama específica (cima/baixo do beliche) pelo WhatsApp antes de reservar, com disponibilidade futura calculada por sobreposição de datas. Mapa de Quartos expandido de 3 para 5 estados visuais (livre/ocupada/limpeza/reservada/manutenção). Equipe pode assumir uma conversa específica (pausando a resposta automática só daquele hóspede) e devolver depois; caixa de envio manual do Chat, que sempre foi simulada, agora envia mensagem real pelo WhatsApp Business. Lista de limpeza do Mapa de Quartos espelhada na caixa de tarefas de Operações. |

| 1.9.0 | 23/07/2026 | Oficial | Correção de série de bugs reais encontrados pelo usuário testando em produção: renderização do beliche (era 2 quadrados, virou 1 cama dividida ao meio, formato retangular), tecla Enter do chat ainda chamando o envio simulado antigo, sino de alertas nunca zerando, IA de reserva confundindo nome de modalidade com nome de quarto (causava falso "sem disponibilidade"), IA atrasando a criação da reserva esperando dados extras, IA reescalando o preço ao falar com o hóspede (a reserva em si sempre foi gravada com valor correto). Preparação de servidor de produção: `Procfile` com `gunicorn` (já estava nas dependências, nunca ativado) — pendente o usuário atualizar o Start Command no painel do Render. |

| 1.9.1 | 23/07/2026 | Oficial | Confirmado que o Render já usava `gunicorn app:app` (sem workers/threads configurados, mesmo efeito prático do problema de travamento); Start Command atualizado pelo usuário. Corrigido bug real de CSS achado testando ao vivo: painel do Ask StayFlow sendo sobreposto pelo cabeçalho (z-index) e caixa de digitação "sumindo" conforme a conversa crescia (armadilha de flexbox sem `min-height:0`/`overflow-y`). Mapa de Quartos ganhou edição de nome e exclusão de cama (bloqueada se a cama estiver ocupada). |

| 1.10.0 | 23/07/2026 | Oficial | Captura de documento de identidade via WhatsApp: webhook passou a processar mensagens de imagem (antes só texto), baixando o arquivo real da API da Meta e guardando no disco persistente, associado ao hóspede. IA de atendimento passa a pedir nome completo, data de nascimento e foto do documento após criar a reserva. Documentos recebidos aparecem no perfil do hóspede na tela de Chats. Corrigido também: lista vazia de camas disponíveis não bloqueia mais a reserva quando a modalidade simplesmente não tem camas cadastradas individualmente (comum em quarto privado) — a reserva é criada sem cama especifica, atribuída depois no check-in. |

| 1.10.1 | 23/07/2026 | Oficial | Trava real contra overbooking: modalidade sem nenhuma cama cadastrada não permite mais reserva automática (vira oportunidade de alta prioridade pra equipe confirmar manualmente, sem duplicar se o hóspede repetir o pedido); modalidade com cama cadastrada passa a exigir escolha de uma cama específica e realmente disponível antes de reservar. Revisão do próprio usuário sobre um risco que a correção anterior (1.10.0) tinha introduzido. |

| 1.11.0 | 23/07/2026 | Oficial | Novo tipo de estadia "morador de longa duração" (ex: funcionário que mora no hostel, pagando conforme consegue) — sem data de saída definida, saldo calculado sob demanda (dias ocupados vezes diária configurável, menos pagamentos registrados), suportando tanto saldo devedor quanto crédito acumulado quando a pessoa paga mais do que deve. Exposto na tela de Reservas (formulário próprio, tabela com saldo colorido) e no Ask StayFlow (criar morador, consultar saldo, registrar pagamento, encerrar estadia). |

| 1.12.0 | 23/07/2026 | Oficial | Correção de bugs reais no Mapa de Quartos: não era possível editar ou excluir quarto, editar tipo/grupo de cama, nem editar ou excluir modalidade — só existia criação. Adicionados botões de editar/excluir em quartos e modalidades (rotas `PATCH /rooms/<id>` e `PATCH /room-categories/<id>` novas no backend) e edição de tipo/grupo de cama. Tradução completa do Dashboard (motor compartilhado `i18n-core.js` + dicionário `i18n-dashboard-data.js` com ~570 chaves): todas as 13 seções (Dashboard, Chats, Reservas, Mapa de Quartos, Opportunity Center, Hóspedes, Operações, Equipe, Financeiro, Estoque, Receitas, Relatórios, Configurações com 7 sub-abas) mais o painel Ask StayFlow, incluindo texto estático, conteúdo dinâmico gerado por JS e mensagens de alert/confirm/prompt — em português, inglês, espanhol, francês e alemão, com terminologia real de hotelaria (não tradução literal). Seletor de idioma novo no topbar ao lado do sino de notificações. Landing page (`index.html`) migrada para o mesmo motor compartilhado, com francês e alemão adicionados aos 3 idiomas existentes. Escopo definido como fora desta fase: mensagens de erro geradas pelo backend (Flask), que continuam em português — exigiria o backend passar a devolver códigos de erro em vez de texto pronto, projeto maior e separado. |

| 1.13.0 | 23/07/2026 | Oficial | Correção de três bugs reais na IA de atendimento via WhatsApp, encontrados pelo usuário testando com números diferentes: (1) a IA trocava de idioma sozinha no meio da conversa — corrigido persistindo o idioma estabelecido na coluna `guests.language` (já existia no schema, nunca era usada) e reforçando no prompt a cada mensagem; (2) contagem errada de diárias (5 em vez do correto para sexta→domingo) — a IA calculava datas de cabeça; corrigido com nova ferramenta `calculate_nights` (cálculo determinístico em Python, nunca pelo modelo) e `create_reservation_from_chat` passou a devolver o número real de noites no resultado da reserva; (3) captura de dados pós-confirmação incompleta — reescrita como checklist explícito e ordenado (nome legal, telefone, email, nacionalidade — campo novo — data de nascimento, foto do documento), com gatilho claro no momento da criação da reserva. |

| 1.13.1 | 23/07/2026 | Oficial | Correção de lacuna na tradução do Dashboard: a página inicial (KPIs, Resumo Executivo da IA, Operação, Atividades de hoje, Ações prioritárias) tinha ficado inteira fora do trabalho de tradução anterior. Adicionado `data-i18n` em todo o conteúdo estático dessa seção. Corrigido também o texto gerado pela IA (`/executive-summary`), que sempre respondia em português independente do idioma escolhido no painel — endpoint agora aceita `?lang=`, o prompt pede a resposta no idioma certo, e o fallback (usado se a IA falhar) tem versão traduzida pronta em cada um dos 5 idiomas. |

| 1.14.0 | 25/07/2026 | Oficial | Varredura completa de todo texto gerado pelo backend que sempre saía em português, independente do idioma do painel: Ask StayFlow (`/ask`) passa a receber o idioma atual e responder nele; description/next_action das oportunidades (Opportunity Center, Ações prioritárias do Dashboard, Resumo da IA no perfil do hóspede em Chats) passam por tradução em lote (`services/translation_service.py`) na hora da leitura, já que esse texto é gravado uma única vez em português no momento em que a mensagem do hóspede chega. Português continua sem nenhum custo extra (passthrough). Decisão deliberada de manter em português a mensagem sugerida de reposição a fornecedor (Estoque), por ser dirigida a um terceiro que não usa o painel. |

| 1.15.0 | 28/07/2026 | Oficial | Motor de detecção de oportunidades (`decision_engine.py`) passa a avaliar a CONVERSA inteira (histórico recente incluído no prompt), não mais cada mensagem isolada sem contexto. Oportunidades deixam de ser criadas em duplicidade a cada mensagem: se já existe uma aberta do mesmo hóspede com o mesmo tipo, é atualizada (evolução do mesmo assunto) em vez de gerar uma linha nova — reduz ruído real no Opportunity Center e no sino de alertas, que antes disparava a cada mensagem da mesma conversa. |

| 1.16.0 | 28/07/2026 | Oficial | Substituídos os `alert()`/`confirm()`/`prompt()` nativos do navegador (caixa branca do sistema operacional) por um modal com a identidade visual do StayFlow (caixa azul-marinho, ícone azul). `alert()` foi sobrescrito globalmente sem tocar em nenhum call site (nenhum lugar dependia do valor de retorno); `confirm()`/`prompt()` viraram `stayflowConfirm()`/`stayflowPrompt()` (baseados em Promise, já que um modal HTML não trava a thread como os nativos travam) — os 18 pontos reais que usavam o valor de retorno foram convertidos individualmente para `await`. |

| 1.17.0 | 28/07/2026 | Oficial | Redesign do Mapa de Quartos: os cinco cards fixos de criação (Modalidades, Novo quarto, Nova cama, Lista de limpeza, Devolver da lavanderia) que ocupavam metade da tela cada um foram substituídos por um único botão "☰ Ações" no card do mapa, que abre um menu com cada uma dessas opções — cada item abre seu formulário num modal central (reaproveitando o modal genérico já usado pelo painel de Equipe), deixando o mapa visual de quartos como único conteúdo permanente da página. Modais de criação não fecham sozinhos após criar um item (formulário só limpa e a lista/seletor se atualiza na hora), pensado para o fluxo real de montar um hostel do zero criando vários quartos/camas em sequência. |

| 1.17.1 | 28/07/2026 | Oficial | Botão de assumir/devolver conversa (aba Chats) redesenhado: em vez de um botão secundário cinza solto ao lado do "Score", agora é o próprio botão de enviar mensagem que troca de papel — verde e "Assumir" enquanto a IA está no controle (clicar assume a conversa em vez de enviar), voltando ao azul normal "Enviar" depois de assumido; um botão "Devolver" aparece ao lado só quando a conversa está com um humano, devolvendo o controle pra IA ao ser clicado. |

| 1.18.0 | 28/07/2026 | Oficial | Início da integração com channel manager (Beds24) pra receber reservas de Booking.com/Airbnb/Hostelworld automaticamente — modelo agência/white-label, uma conta master do StayFlow com cada cliente virando sub-propriedade, sem custo nem conta separada pro cliente final. Fase 1 (fundação): tabelas novas de credencial mestra (criptografada) e mapeamento de quarto, serviço de autenticação da API v2 do Beds24, tela de ativação em Configurações → Integrações, e uma trava real contra condição de corrida (`reservar_cama_com_trava`, via `BEGIN IMMEDIATE` do SQLite) aplicada no fluxo de reserva do WhatsApp — fecha um risco de overbooking que já existia antes desta integração, sem trava nenhuma entre checar disponibilidade e inserir a reserva. Fases seguintes (mapeamento de quarto, webhook de entrada, push de disponibilidade, conexão real com as OTAs, webhook de saída genérico pra cliente com sistema próprio) ainda pendentes. Configuração real feita com o usuário (conta master no Beds24, chave de criptografia, invite code) e confirmada funcionando em produção, incluindo dois bugs reais corrigidos no processo (header de autenticação `token`, não `Authorization: Bearer`; corpo do `POST /properties` precisa ser array). |

| 1.19.0 | 30/07/2026 | Oficial | Fase 2 da integração Beds24: mapeamento de quarto. Tela de Configurações → Integrações ganha, pra cada modalidade de quarto do hostel, um seletor com os quartos já cadastrados na sub-propriedade do Beds24 (`GET /properties?includeAllRooms=true`) — escolher e salvar cria o vínculo; escolher "nenhum" remove. Sem esse mapeamento, uma reserva futura vinda de OTA (Fase 3) não saberia em qual modalidade cair. |

| 1.19.1 | 30/07/2026 | Oficial | Ajuste real, testado ao vivo: sub-propriedade nova no Beds24 nasce sem nenhum quarto, deixando o seletor de mapeamento vazio. Adicionado botão "Criar no Beds24" que cria o quarto lá direto (`POST /properties` com `id` da propriedade + `roomTypes`) e já vincula automaticamente — fecha o fluxo sem o usuário precisar abrir o painel do Beds24 manualmente. Faxina: removidas duas cópias obsoletas do diário/master context (uma na raiz do repositório `HostelBot`, outra solta em `HostelBot/StayFlow---Site/docs/`) — só a versão em `StayFlow---Site/docs/` é a fonte de verdade. |

| 1.19.2 | 30/07/2026 | Oficial | Diretriz de produto explícita do usuário, aplicada em toda a integração de canais: o cliente final nunca deve sentir que existe qualquer plataforma externa no meio, só StayFlow. Removida toda menção literal a "Beds24"/"channel manager" dos textos visíveis nos 5 idiomas (achado testando ao vivo: o tradutor automático do navegador traduzia "Beds24" cru na tela pra "Camas24"). Adicionada mensagem de sucesso clara ao criar quarto automaticamente, e o seletor de quarto passou a tolerar o quarto recém-criado ainda não aparecer na consulta seguinte ao Beds24 (consistência eventual do lado deles), evitando a aparência de falha quando na verdade só está sincronizando. |

| 1.19.3 | 30/07/2026 | Oficial | Causa raiz real encontrada: o tradutor automático do navegador (não um bug do StayFlow) estava reescrevendo texto já em português na tela ("Compartilhado" → "Compartmentalhado", "Beds24" → "Camas24"), e possivelmente interferindo em conteúdo inserido por JavaScript. Corrigido de vez, em nível de código (não depende de configuração do navegador de cada pessoa): `<meta name="google" content="notranslate">` + atributo `translate="no"` em `dashboard.html`, `Login.html`, `Register.html` e `index.html` — sinal padrão da web pra nenhum tradutor de navegador atuar na página. Tradução do StayFlow continua existindo, só que exclusivamente pelo seletor de idioma próprio do produto. |

| 1.20.0 | 31/07/2026 | Oficial | Fase 3 da integração Beds24: webhook de entrada. Novo `POST /webhook/beds24/<token secreto>` recebe reserva nova vinda de Booking.com/Airbnb/Hostelworld em tempo real e cria a reserva de verdade no StayFlow — com trava contra condição de corrida (Fase 1) e, diferente do fluxo do WhatsApp, sem recusar a reserva por falta de cama livre (é um compromisso já confirmado do lado da OTA; sem cama disponível, cria mesmo assim pra atribuição manual). Payload sempre gravado cru antes de qualquer interpretação, pra nunca perder reserva mesmo se o formato de campo específico estiver errado — lição direta da Fase 2. Escopo desta fase: só reserva nova; atualização de data e cancelamento ficam pra próxima rodada, após confirmar formato real com teste ao vivo. |

| 1.20.1 | 31/07/2026 | Oficial | Bug real encontrado no primeiro teste ao vivo do webhook: reserva vinda do Beds24 chegava com valor US$ 0,00, porque a rota nunca extraía o campo `price` do payload — a função de criação caía pro `price_per_night` (ainda sem preço configurado) da modalidade no StayFlow. Usuário apontou a regra correta: o valor tem que vir sempre do canal/OTA, nunca recalculado pelo preço do StayFlow, já que plataformas como Booking/Airbnb podem vender com desconto. Corrigido: `amount` extraído do payload (`price`/`totalPrice`/`amount`) e repassado pra criação e atualização de reserva; `update_reservation_from_channel` ganhou parâmetro `amount` opcional (`None` preserva o valor já gravado). Confirmado em produção com reteste real: US$ 36,00 correto. |

| 1.21.0 | 31/07/2026 | Oficial | Corrigido gap na aba Reservas: não havia como confirmar check-in/check-out de uma reserva por ali — só o dropdown de status (pendente/confirmada/cancelada/no-show), um conceito separado do status físico da cama. O fluxo completo (cama azul→reservada, vermelha→ocupada no check-in, amarela→limpeza no check-out, verde→livre quando a limpeza é confirmada) já existia no backend e no Mapa de Quartos, só nunca tinha sido ligado na aba Reservas. `get_reservations_with_stats` passou a fazer LEFT JOIN com `beds` e devolver `bed_status`; a aba Reservas ganhou botão "Confirmar check-in" (abre seletor de cama livre via `/bed-map`, reserva confirmada sem cama) e "Confirmar check-out" (cama ocupada), reaproveitando as rotas `/reservations/<id>/checkin` e `/checkout` já existentes do Mapa de Quartos. Push automático do check-in confirmado pro Beds24 (pedido original do usuário) fica pra próxima rodada, pendente de verificar se a API do Beds24 tem um conceito equivalente a "hóspede chegou". |

| 1.21.1 | 31/07/2026 | Oficial | Bug real encontrado testando em produção: reservas vindas do Beds24/WhatsApp (que já nascem com `bed_id` preenchido, atribuído automaticamente na criação) não mostravam nenhum botão de check-in/check-out, porque a versão anterior usava a presença de `bed_id` como sinal de "já fez check-in" — ambíguo, já que `bed_id` também significa "cama reservada pro período", preenchido bem antes da chegada real. Corrigido com dois campos sem ambiguidade: `reservations.checked_in_at`/`checked_out_at` (timestamp, null até a ação física acontecer de verdade), usados agora tanto na aba Reservas quanto no filtro de "aguardando check-in" do Mapa de Quartos. Aproveitado pra resolver um pedido do usuário: já que a categoria (compartilhado/privado) e a cama já vêm decididas automaticamente na criação da reserva de canal, o check-in dessas reservas não pede mais escolha manual de cama — confirma direto na cama já atribuída; o seletor manual só aparece quando realmente não há cama nenhuma atribuída ainda. |

| 1.21.2 | 31/07/2026 | Oficial | Aba Reservas e Mapa de Quartos passaram a se atualizar automaticamente uma à outra depois de qualquer ação que muda status de cama/reserva (check-in, check-out, marcar como limpa, mudar status manual, abrir/encerrar estadia de longa duração) — antes precisava de F5 pra ver a cor da cama mudar depois de uma ação feita na aba Reservas (e vice-versa). Função central `refreshOperationalViews()` chama as duas telas juntas em todo ponto de mudança de status. |

| 1.21.3 | 31/07/2026 | Oficial | Dois ajustes reportados testando o ciclo completo em produção: (1) bug real corrigido — cama ficava presa mostrando "Reservada" (azul) mesmo depois de check-out e limpeza confirmados, porque o cálculo de cor do Mapa de Quartos não considerava se a reserva vinculada já tinha sido finalizada; corrigido exigindo `checked_out_at IS NULL` na consulta. (2) Coluna "Origem" da aba Reservas ganhou `channelDisplayLabel()` no frontend, mapeando slugs conhecidos de canal (Airbnb, Booking.com, Hostelworld, Expedia, Agoda, Vrbo, WhatsApp, Direto) pro nome formatado da plataforma, com fallback seguro pra qualquer valor não mapeado — o backend já capturava o canal real de cada reserva vinda do Beds24, só faltava a formatação de exibição. |

| 1.21.4 | 31/07/2026 | Oficial | Novo status visual no Mapa de Quartos: cama ocupada por morador de longa duração (estadia indefinida ainda ativa, sem checkout registrado) aparece roxa (`long_term`) em vez de vermelha (`occupied`) — diferencia visualmente de um hóspede normal de passagem. `get_bed_map` identifica essas camas verificando `stay_type = 'indefinite' AND checkout_date IS NULL`; some da cor roxa automaticamente ao encerrar a estadia (`close_indefinite_stay`), voltando pro ciclo normal de limpeza. Legenda do mapa e i18n (5 idiomas) atualizados. |

| 1.21.5 | 31/07/2026 | Oficial | Dois bugs reais corrigidos no formulário de morador de longa duração: (1) não existia seletor de cama no formulário — `create_indefinite_stay` só ocupa uma cama de verdade quando recebe `bed_id`, mas o formulário nunca mandava esse campo, então o morador nunca aparecia no Mapa de Quartos. Adicionado seletor de cama livre (`indefiniteStayBedSelect`, populado a partir do `/bed-map`). (2) morador com telefone não aparecia na aba Hóspedes — a função só *procurava* um hóspede já existente com aquele telefone, nunca *criava* um novo (diferente do resto do sistema, que usa `get_or_create_guest`); corrigido pra criar/vincular o hóspede de verdade. Aproveitado pra fechar outro gap: check-out (inclusive de estadia de longa duração) agora gera um alerta operacional de verdade em `/operations` pra cada cama aguardando limpeza — antes só virava "tarefa" na lista, sem contar no sininho de notificações nem aparecer resumido pra quem tem acesso à área de Operações (que já é avisado automaticamente no login, gate por permissão já existente). |

| 1.21.6 | 31/07/2026 | Oficial | Reservas criadas por qualquer canal automático (WhatsApp, Beds24/qualquer OTA — `source != 'manual'`) nas últimas 24h agora também geram alerta no sininho de Operações ("Nova reserva via {canal}: {hóspede}..."), não só reservas manuais. Pedido em aberto do usuário, ainda não iniciado: notificação nativa no aparelho (celular/PC), estilo WhatsApp, pra mensagem nova/alerta operacional/problema de IA/intervenção humana — requer infraestrutura nova (Web Push API, service worker, VAPID, inscrições por dispositivo), fica pra ser desenhado como etapa própria. |

| 1.22.0 | 31/07/2026 | Oficial | Perfil completo do hóspede na aba Hóspedes: clicar no nome (antes era texto solto, sem ação) abre um modal com contato editável (nome, telefone, email, endereço, data de nascimento, nacionalidade), documento (tipo + número, editáveis, mais galeria de fotos do documento com upload manual — reaproveita o `guest_documents` já usado pelo recebimento automático via WhatsApp) e histórico completo de estadias com status/valor, incluindo saldo devedor/crédito calculado ao vivo pra estadias de longa duração (reservas fixas não têm conceito de pagamento parcial no modelo atual, mostram só o valor total). Novo `get_guest_reservations`, `update_guest_profile`, rotas `PATCH /guests/<id>` e `POST /guests/<id>/documents`; colunas novas em `guests` (`address`, `document_type`, `document_number`). Moeda/câmbio automático por país (pedido do usuário, com regra de margem de 30 pontos abaixo do câmbio real) registrado como pendência futura, a ser feito junto da configuração de formas de pagamento — não iniciado. |

| 1.23.0 | 31/07/2026 | Oficial | Fase 4 da integração Beds24: saída/disponibilidade. Nova `sync_availability_to_channel(hostel_id, category_name, checkin_date, checkout_date)` calcula quantas camas de uma modalidade continuam livres pro período (total de camas menos reservas não-canceladas de qualquer origem que se cruzam com as datas, contadas por `room_type` em texto, não por `bed_id`, porque reserva manual/WhatsApp só ganha cama específica no check-in) e empurra pro Beds24 via `push_availability` (já existia, nunca tinha sido chamada). Ligada em três pontos: criação de reserva manual, criação via WhatsApp, e qualquer mudança de status (cancelar/reverter cancelamento — a função sempre recalcula do zero, então é seguro chamar em qualquer transição). Nunca chamada pra reserva vinda do próprio Beds24 (evita eco). Fecha o risco de overbooking entre canais que ainda existia (reserva feita no StayFlow não avisava as OTAs). Testado com mocks de `push_availability` (sem gastar chamada real): sem mapeamento não sincroniza, contagem correta com/sem reserva, cancelamento libera de volta, reserva de canal não ecoa. Nome exato do campo `numAvail` na API real do Beds24 ainda não confirmado contra uma resposta real — mesma ressalva de sempre nesta integração, ajustar no primeiro teste ao vivo. |

| 1.23.1 | 31/07/2026 | Oficial | Fase 4 confirmada funcionando contra a API real em produção (HTTP 201, `{"success":true}`) - campo `numAvail` estava correto desde o início, ressalva removida. Bug real corrigido: `create_reservation_record` (criação manual) nunca calculava o valor pelo preço da modalidade, diferente dos outros dois caminhos de criação (WhatsApp e Beds24) que já faziam isso - reserva manual em modalidade com preço configurado nascia sempre em US$ 0,00, dependendo de alguém digitar o valor na mão. Agora calcula `price_per_night × noites` automaticamente quando nenhum valor é informado, sem sobrescrever valor digitado explicitamente (ex: desconto negociado). |

| 1.24.0 | 31/07/2026 | Oficial | Fase 5 da integração Beds24: reserva de verdade, não só disponibilidade agregada. Pedido do usuário: "quero que esteja tudo em acordo... mostre o que foi criado, cancelado, check-in, check-out, tudo em sincronia". `create_booking`/`update_booking_status` (novo, `services/beds24_service.py`) usam `POST /bookings` com os mesmos nomes de campo já confirmados reais (vieram do payload real do webhook da Fase 3) e o mesmo formato de resposta em lote (`data[0]["new"]`) já confirmado em `create_property`/`create_room_type`. `sync_booking_to_channel` (novo, `database.py`) cria a reserva no Beds24 na primeira vez (grava o `external_booking_id` retornado) e só atualiza status nas vezes seguintes (cancelar/reverter) - nunca roda pra reserva vinda do próprio Beds24 (evita eco), nunca publica reserva ainda `pending` (só quando a equipe confirma), nunca roda pra estadia de longa duração (não se anuncia numa OTA). Ligada nos mesmos 3 pontos da Fase 4. De quebra, corrigido outro caso do bug "só procura, nunca cria hóspede" (já corrigido em morador de longa duração numa rodada anterior): `create_reservation_from_chat` também passou a usar `get_or_create_guest`, então hóspede novo pelo WhatsApp agora aparece na aba Hóspedes e leva telefone/email de verdade pro Beds24. Check-in/check-out ficam fora do escopo por enquanto - o payload real mostra que a Beds24 guarda isso como um `infoItem` separado (`code='CHECKIN'`), não como o status principal da reserva, mecanismo de escrita ainda não confirmado. |

| 1.24.1 | 31/07/2026 | Oficial | Bug real de produção corrigido: reserva do "Silvano" apareceu duplicada no Beds24 - causa era um eco da própria Fase 5 (StayFlow cria a reserva no Beds24, que manda um webhook de volta quase na hora, às vezes antes da gente terminar de gravar o `external_booking_id` na reserva original; sem saber que era a mesma reserva, o webhook criava uma segunda linha). Corrigido com `find_recent_unlinked_stayflow_reservation`/`link_external_booking_id`: antes de criar uma reserva nova a partir de um webhook, procura uma reserva StayFlow-origin recente (10 min), sem vínculo ainda, com mesma modalidade/hóspede/datas - se achar, vincula em vez de duplicar. Também corrigido: check-out (e qualquer ação operacional) agora atualiza a tela de Operações/sininho na hora (`refreshOperationalViews` ganhou `loadOperations()`) - antes só atualizava depois de recarregar a página ou abrir a aba manualmente, alerta de limpeza existia no backend mas não aparecia na hora certa. |

| 1.24.2 | 31/07/2026 | Oficial | Bug real de produção corrigido: reserva do "Otavio" (modalidade "Privado") não calculou preço nem sincronizou com o Beds24. Causa: a modalidade real do hostel se chama "privado" (minúsculo) - o formulário de nova reserva manual tem opções fixas "Privado"/"Compartilhado" (maiúsculo), e a comparação no banco (`name = ?`) é sensível a maiúsculas/minúsculas, então nunca achava a modalidade. Corrigido em todos os pontos que comparam `room_type`/nome de modalidade (cálculo de preço, `find_available_beds`, sincronização de disponibilidade e de reserva com o Beds24, dedup do eco) para usar `LOWER(name) = LOWER(?)`, resiliente a qualquer diferença de caixa. |

| 1.24.3 | 31/07/2026 | Oficial | Redesign visual dos botões de check-in/check-out na aba Reservas: saíram de baixo do dropdown "Mudar status..." (botão retangular largo) e foram pra dentro da coluna Estado, ao lado da pill de status, como botão pequeno arredondado - verde sólido "Check-in", vermelho sólido "Check-out" depois de feito o check-in. Texto encurtado de "Confirmar check-in"/"Confirmar check-out" pra só "Check-in"/"Check-out" nos 5 idiomas. |

| 1.24.4 | 31/07/2026 | Oficial | Dois ajustes: (1) botão de check-in/check-out da aba Reservas estava quebrando linha (ficava embaixo da pill de status em vez de do lado) - envolvidos os dois num `<div style="display:flex">` sem quebra de linha. (2) F5/reload sempre voltava pro Dashboard, não importa em qual aba a pessoa estivesse - `openPage` agora grava a aba atual no `localStorage`, e o bootstrap da sessão restaura essa aba automaticamente (só se a pessoa ainda tiver permissão pra vê-la; senão fica no Dashboard). |

| 1.24.5 | 31/07/2026 | Oficial | Dois bugs reais de produção corrigidos: (1) reserva criada no StayFlow aparecia com valor US$ 0,00 no painel do Beds24 mesmo a API confirmando o `price` enviado - causa: o campo `price` sozinho é só ecoado na resposta, o valor de verdade vem de um `invoiceItems` (item de fatura) separado, confirmado comparando com o payload real de uma reserva criada direto no painel deles. `create_booking` agora manda `invoiceItems` junto. (2) check-in de uma reserva não refletia no Mapa de Quartos - `checkinReservationUI` confiava cegamente na cama atribuída automaticamente (canal/WhatsApp) sem mostrar seletor; agora sempre mostra o seletor de cama livre (pré-selecionando a já atribuída, se houver), com sufixo claro "Beliche - Cima"/"Beliche - Baixo" quando aplicável. |

| 1.25.0 | 31/07/2026 | Oficial | Redesign do formulário de nova reserva/morador de longa duração na aba Reservas: os dois formulários fixos (ocupando espaço permanente na tela) viraram botões que abrem modal, mesmo padrão já usado no Mapa de Quartos. Campos novos na criação manual: nome/sobrenome separados, email, nacionalidade (gravados de verdade no hóspede via `get_or_create_guest` - mesmo bug "só procura, nunca cria" já corrigido em outros pontos, corrigido aqui também) e seletor de cama de verdade (dependente da modalidade escolhida, com trava contra condição de corrida igual reserva de canal/WhatsApp, sufixo "Beliche - Cima"/"Beliche - Baixo" quando aplicável). Tipo de quarto deixou de ser lista fixa "Privado"/"Compartilhado" e passou a listar as modalidades reais cadastradas no hostel. Status "Pendente" removido da criação manual - toda reserva criada manualmente já nasce confirmada (WhatsApp continua nascendo pending, aguardando confirmação da equipe - isso não mudou). |

| 1.26.0 | 31/07/2026 | Oficial | Quatro ajustes reais de operação diária: (1) cama com reserva futura só aparece "Reservada" (azul) no Mapa de Quartos a partir do dia do check-in, não semanas antes - reserva pro mês que vem não trava mais a percepção de disponibilidade da cama antes da hora (a trava real contra double-booking continua intacta em outro lugar, isso é só a cor exibida). (2) Alerta operacional novo: chegada de hoje sem check-in físico ainda confirmado avisa a recepção a atribuir cama, mesmo pra reserva já confirmada. (3) Reserva com check-out já confirmado sai da lista da aba Reservas (fica só o que está em andamento ou por vir) - histórico continua rastreável pelo perfil do hóspede. (4) Aba Hóspedes mostra status "CHECKOUT" pra quem já teve a estadia mais recente encerrada. Seletor de cama no check-in (aba Reservas) agora filtra por padrão só a modalidade da própria reserva, com opção de trocar modalidade explicitamente - evita atribuir sem querer o hóspede a um quarto diferente do que ele reservou. |

| 1.27.0 | 31/07/2026 | Oficial | Fase 6 da integração de canais: webhook de saída genérico, adiantada na frente da Fase 5 (conexão real com uma OTA) a pedido do usuário, por ainda não ter como cadastrar um cliente de verdade pra testar a Fase 5. Cliente que já tem sistema próprio e usa o StayFlow só pra atendimento/IA cadastra, em Configurações → Integrações, uma URL sua — toda reserva criada, alterada, cancelada, com check-in ou check-out feito (de qualquer origem: manual, WhatsApp ou canal/Beds24) dispara um `POST` JSON assinado (`X-StayFlow-Signature`, HMAC-SHA256 com uma chave gerada por hostel na primeira vez que a URL é salva, mostrada na tela pra copiar) pra essa URL. Novo `dispatch_reservation_webhook` (`database.py`) ligado nos 9 pontos onde uma reserva é criada/alterada/finalizada (diferente de `sync_booking_to_channel`, que só roda pra origem manual/WhatsApp — aqui roda sempre, o cliente quer saber de tudo, inclusive reserva vinda de OTA); nunca levanta exceção, mesmo princípio dos outros serviços de integração. Chave de assinatura guardada em texto puro (diferente do token master do Beds24): se vazar, só permite forjar evento no sistema do próprio cliente, não expõe nada do StayFlow. |

| 1.28.0 | 31/07/2026 | Oficial | Fechamento de três pendências antes de iniciar a integração com Instagram/Facebook. (1) Bug real corrigido: o menu do usuário (dropdown do topbar) nunca mostrava nome/cargo de quem estava logado, mesmo a sessão carregando certinho (a aba Equipe, que lê a sessão por outro caminho, sempre mostrou certo) — causa: `hydrateUserUI` deixava a atribuição de nome/cargo/avatar por ÚLTIMO, depois de `restoreLastOpenPage()`/`populateHostelSelector()`/etc.; qualquer exceção nessas chamadas abortava a função no meio e nunca chegava a preencher o menu. Corrigido colocando essa atribuição PRIMEIRO na função, com as chamadas seguintes protegidas por `try/catch` individual — o menu do usuário nunca mais fica órfão, mesmo se algo mais abaixo falhar. (2) Frente de "Ver cancelamentos" finalizada: botão na aba Reservas abre modal (`/reservations/cancelled`) com lista de reservas canceladas e opção de reativar (`PATCH status=confirmed`) sem sair da tela. (3) Enter confirma / Esc cancela em todas as caixas de cadastro (convite de equipe, nova reserva, morador de longa duração, check-in, editar quarto/cama/modalidade, etc, que já compartilhavam o mesmo `genericModal`) e nos avisos (`sfAlert`, Esc já funcionava, Enter no botão OK também já funcionava por foco nativo) — Enter aciona o primeiro `button.btn` (nunca "secondary"/"red") do corpo do modal quando o foco está num campo de uma linha só, Esc fecha o modal aberto no momento. |

| 1.29.0 | 31/07/2026 | Oficial | Fase 1 da integração com Instagram Direct e Messenger (Facebook): fundação de dados, sem nada visível ainda. Investigação de código (dois agentes Explore) confirmou zero resquício de integração prévia com Instagram/Facebook — greenfield total, com o WhatsApp servindo de modelo. Decisões de arquitetura (registradas no plano completo): conexão via OAuth de verdade (não colar token à mão, nem pro WhatsApp que ganha o mesmo tratamento agora — todos os três com fallback manual também), modelo de identidade multi-canal de verdade (tabela `guest_channel_identities` em vez de forçar IGSID/PSID dentro de `guests.phone`), webhook único `/webhook/meta` pros dois canais novos, e atualização em tempo real da aba Chats via SSE (Server-Sent Events, sem precisar trocar o worker do gunicorn como WebSocket exigiria). Nesta rodada: colunas novas em `hostels` (`facebook_page_id`/`facebook_page_access_token`/`facebook_oauth_state`, `instagram_business_id`/`instagram_access_token`/`instagram_oauth_state`, `whatsapp_oauth_state`), tabela `guest_channel_identities` (`UNIQUE(hostel_id, channel, external_id)`), e a função canônica nova `get_or_create_guest_by_channel` (WhatsApp também vai passar a usar ela nas próximas fases, pra não manter dois caminhos de código divergentes). App ID/Secret do App Meta do StayFlow guardado em variável de ambiente (`META_APP_ID`/`META_APP_SECRET`), não em tabela — mesmo padrão já usado pro `WHATSAPP_VERIFY_TOKEN`, mais simples que a criptografia em banco cogitada inicialmente no plano. Testado isoladamente (8 cenários: config Facebook/Instagram, states OAuth de uso único, idempotência multi-canal, isolamento multi-tenant) e sem regressão nos testes já existentes (check-in/check-out, webhook de saída, cancelamentos). Bloqueado pra Fase 2 (rotas de OAuth): precisa do usuário criar o App Meta do StayFlow (produtos Facebook Login for Business + Instagram Login + WhatsApp Embedded Signup) e passar `app_id`/`app_secret` — mesmo tipo de bloqueio externo que a conta master do Beds24 teve na Fase 1 daquela integração. |

| 1.30.0 | 31/07/2026 | Oficial | Fase 2 da integração de canais (Instagram/Messenger), primeiro pedaço: conexão real via OAuth com o Facebook (Messenger) — usuário já tinha um App Meta criado (mesmo usado pelo WhatsApp), passou App ID/Secret. `services/meta_oauth_service.py` (novo): troca `code` por token de usuário, troca por token de longa duração, busca a Página conectada e o token já pronto dela via `/me/accounts` — mesmo princípio de nunca levantar exceção dos outros serviços de integração. `routes/meta_oauth.py` (novo): `GET /oauth/facebook/connect` (redireciona pra tela de consentimento da Meta, gera `state` anti-CSRF) e `GET /oauth/facebook/callback` (troca code pela Página, salva no hostel, redireciona de volta pro dashboard com o resultado na query string). Card de Configurações → Comunicação para o Facebook Messenger, com os dois modos lado a lado pedidos pelo usuário: botão "Conectar Facebook" (OAuth) e "Configurar manualmente" (Page ID + Access Token direto, mesmo padrão do card do WhatsApp) — qualquer um dos dois grava nas mesmas colunas. Corrigido de quebra um bug real desta sessão: `loadOutboundWebhookSettings` só estava ligado no reload por troca de idioma, nunca no carregamento normal da página — o card do webhook de saída ficava sempre vazio até a pessoa trocar de idioma uma vez. Testado com Graph API mockada (sem gastar chamada real): fluxo completo connect→callback→Página salva, state rejeitado quando errado ou reutilizado, connect falha educadamente sem App configurado, rotas de configuração manual (salvar/manter token/desconectar). Instagram Login e WhatsApp Embedded Signup ficam para as próximas rodadas, um de cada vez. |

| 1.30.1 | 31/07/2026 | Oficial | Ajuste real encontrado configurando ao vivo com o usuário: o App Meta do StayFlow usa "Facebook Login for Business" no modo com Configuration (permissões empacotadas numa "Configuración" criada no painel da Meta, com um Configuration ID próprio — não mandadas soltas via `scope` na URL, como no Facebook Login clássico que o código original assumia). `get_facebook_authorize_url` corrigida pra usar `config_id` (variável de ambiente nova `FACEBOOK_CONFIG_ID`) em vez de `scope`. Confirmado funcionando de ponta a ponta em produção: botão "Conectar Facebook" → tela de consentimento da Meta → callback → Página salva no hostel, com sucesso. Fecha o ponto que o plano tinha deixado em aberto (mesmo padrão da integração Beds24: só confirma o formato exato testando ao vivo). |

| 1.31.0 | 31/07/2026 | Oficial | Fase 3+4 da integração de canais: Messenger 100% funcional (entrada e saída), decisão consciente de terminar um canal por completo antes de começar o Instagram, em vez de só conectar os três primeiro. Novo `routes/meta_webhook.py` (`GET/POST /webhook/meta`, mesmo handshake genérico do `/webhook/whatsapp`) recebe mensagem real do Messenger, resolve o hostel pelo `page_id`, processa pelo MESMO pipeline de IA do WhatsApp. Isso expôs uma dependência estrutural real: várias funções do pipeline (`analyze_message`, `is_guest_ai_paused`, `get_guest_language`, `update_guest_name`/`update_guest_language`, `save_message_db`) resolviam o hóspede buscando por `guests.phone` de novo internamente — nunca funcionariam pra Messenger, cujo `guests.phone` fica `NULL` de propósito (decisão da Fase 1, pra não forçar PSID/IGSID como telefone fake). Corrigido resolvendo `guest_id` UMA VEZ no topo de `process_incoming_message` (via `get_or_create_guest_by_channel`) e criando equivalentes por `guest_id` dessas funções (`is_guest_ai_paused_by_id`, `get_guest_language_by_id`, etc.) e de `save_message_db` (`save_message_db_for_guest`, que também passou a gravar o canal real em `conversations.channel` — antes sempre `'api'`); `analyze_message` também passou a receber `guest_id` já resolvido em vez de buscar por telefone. `get_or_create_guest_by_channel` ganhou lógica de adoção: hóspede de WhatsApp criado ANTES desta integração (sem linha em `guest_channel_identities` ainda) é reconhecido pelo telefone já existente em vez de tentar criar um duplicado (violaria a constraint única). Memória da IA (`memory_service.py`, arquivo JSON) não precisou mudar — só passou a receber uma chave prefixada por canal (`"messenger:<psid>"`) pros canais sem telefone, chave do WhatsApp continua idêntica à de sempre. Novo `services/messenger_service.py` (`send_messenger_message`, mesmo contrato nunca-levanta-exceção dos outros serviços). Testado (8 cenários incluindo o de maior risco: hóspede antigo do WhatsApp sendo adotado sem duplicar) e regressão completa de tudo que já existia sem quebra. Instagram Login fica pra próxima rodada. |

| 1.31.1 | 31/07/2026 | Oficial | Bug real de produção corrigido: primeiro teste ao vivo do Messenger (mensagem real na Página conectada) respondeu com o texto fixo de fallback "Deixa eu confirmar isso com a equipe..." em vez de uma resposta de verdade — usuário pediu explicitamente que a IA no Messenger funcione igual ao WhatsApp (pergunte idioma, nome, processe pedido de reserva). Causa raiz: o portão que libera as ferramentas de reserva pra IA (`get_room_options`, `get_available_beds`, `create_reservation`, `extend_reservation`) exigia `guest_phone` (`services/ai_service.py`), que só existe de verdade pro WhatsApp — no Messenger a IA nunca tinha essas ferramentas disponíveis, tentava ajudar com um pedido de reserva sem conseguir, e esgotava as rodadas de tool-calling sem nunca produzir uma resposta de texto. Corrigido trocando o portão pra `guest_id` (resolvido pelo chamador pra qualquer canal, não só WhatsApp) — expôs, em cascata, que `create_reservation_from_chat`/`attempt_extend_reservation`/`flag_extension_for_approval` (`database.py`) também resolviam o hóspede buscando de novo por `guests.phone`, mesmo problema estrutural já corrigido no pipeline de mensagem na rodada anterior. As três agora recebem `guest_id` já resolvido; `create_reservation_from_chat` também parou de hardcodar `source='whatsapp'` na reserva criada, usando o canal real do hóspede (`get_guest_channel`) — nova constante `STAYFLOW_NATIVE_SOURCES` (`manual`, `whatsapp`, `messenger`, `instagram`) substitui as duas checagens que só reconheciam `('manual', 'whatsapp')` como "reserva nasceu dentro do StayFlow" (usadas pra decidir se é seguro sincronizar com o Beds24 sem risco de eco). Testado (6 cenários novos: reserva criada com `source` correto por canal, dedupe por `guest_id`, oportunidade de "sem cama cadastrada" vinculada ao hóspede certo, extensão de estadia por `guest_id`, e confirmação de que as ferramentas de reserva agora aparecem pro modelo mesmo sem telefone) e regressão completa sem quebra. Adicionado log de diagnóstico permanente em `ask_ai` (rodada a rodada de tool-calling) pra facilitar identificar qualquer caso futuro do mesmo fallback. |

| 1.31.2 | 31/07/2026 | Oficial | Pedido do usuário: diferente do WhatsApp (número de telefone não revela identidade), Messenger/Instagram já entregam a conversa identificada — a IA não deve perguntar o nome, deve simplesmente já usar (ex: "Olá Caio!" na própria mensagem de boas-vindas). Novo `get_messenger_user_profile` (`services/messenger_service.py`, `GET /{psid}?fields=first_name,last_name`) busca o nome do perfil a cada mensagem recebida; `get_or_create_guest_by_channel` só grava esse nome de verdade na criação do hóspede (mensagens seguintes não sobrescrevem). `process_incoming_message`/`ask_ai` ganharam um `guest_name` — quando já conhecido (Messenger desde a primeira mensagem, ou WhatsApp depois que o hóspede disse o nome numa conversa anterior), o prompt troca de "pergunte o nome" para "você já sabe o nome, use naturalmente, não pergunte de novo" (novo `{name_instruction}`, mesmo padrão já usado pra idioma/telefone). Testado (nome do perfil buscado e gravado corretamente sem telefone fake, `ask_ai` recebendo `guest_name` já na primeira mensagem, prompt variando certo com/sem nome conhecido, WhatsApp sem nome ainda salvo continua pedindo normalmente) e regressão completa sem quebra. |

| 1.32.0 | 31/07/2026 | Oficial | Pedido do usuário: identificar de onde vem cada conversa (WhatsApp/Messenger/Instagram) de forma discreta na aba Chats e no perfil do hóspede, e tornar o nome do hóspede clicável na aba Reservas (abrindo o mesmo perfil da aba Hóspedes) — motivação dupla: acesso mais rápido, e forçar que esse perfil exista/seja alcançável pra toda reserva, inclusive morador de longa duração. `get_chats_list`/`get_guest_profile` (`database.py`) passaram a devolver `channel` (via `guest_channel_identities`, com fallback pro hóspede antigo sem canal registrado). Novo `channelBadgeHtml()` (dashboard.html) — selo pequeno colorido (verde WhatsApp, roxo Messenger, rosa Instagram), usado na lista de Chats, no título da conversa aberta e no cabeçalho "Contato" do perfil do hóspede. Novo `guestNameLink()` — nome de hóspede clicável em qualquer lugar que já tinha `guest_id` disponível (linha de reserva normal, linha de morador de longa duração, e a lista do modal "Ver cancelamentos"), chamando o `openGuestProfileModal()` que a aba Hóspedes já usava. Testado (canal certo devolvido por conversa e por perfil, com fallback pro hóspede pré-integração) e regressão completa sem quebra. |

| 1.32.1 | 31/07/2026 | Oficial | Dois bugs reais de produção corrigidos, achados testando o clicável da rodada anterior: usuário reportou não encontrar o perfil do morador de longa duração que criou pra testar, e o crédito de US$ 100.000 registrado como pagamento não aparecia em Financeiro. Causa raiz do primeiro: `create_reservation_record` e `create_indefinite_stay` só criavam um registro em `guests` quando um TELEFONE era informado — reserva/estadia cadastrada só com nome (comum pra morador fixo/funcionário) nunca ganhava `guest_id`, então nunca existia perfil nenhum pra abrir (o clicável simplesmente não tinha link pra fazer). Corrigido com `create_guest_without_phone` (novo) — cria o hóspede mesmo sem telefone (cada reserva "sem telefone" vira um hóspede próprio, já que sem número não há chave nenhuma pra saber que duas são a mesma pessoa). Causa raiz do segundo: `get_finance_summary` somava só `reservations.amount` — que pra estadia de longa duração é SEMPRE 0 (o valor de verdade é a diária acumulando saldo, controlado à parte via `reservation_payments`); qualquer pagamento registrado pra morador fixo ficava invisível na receita. Corrigido somando `reservation_payments` no lugar de `amount` especificamente pra `stay_type='indefinite'` (reserva fixa continua exatamente como antes), e adicionada uma terceira linha na lista de movimentações (`'Pagamento'`) pra esses pagamentos aparecerem no extrato. Testado (9 cenários novos: reserva/estadia sem telefone cria hóspede de verdade e aparece na lista/perfil, hóspedes sem telefone diferentes não colidem no mesmo registro, receita confirmada inclui pagamento de morador fixo, pagamento aparece no extrato, saldo do perfil reflete o crédito) e regressão completa sem quebra. |

| 1.32.2 | 31/07/2026 | Oficial | Bug real encontrado testando o Messenger ao vivo: mesmo com o nome automático (v1.31.2) já no ar, o hóspede continuava aparecendo como "Sem telefone"/"Hóspede" na aba Chats. Causa: `get_or_create_guest_by_channel` só grava o `name` recebido na hora de CRIAR o hóspede — essa conversa específica já existia de um teste anterior (antes do nome automático existir), então toda mensagem seguinte só reaproveitava o `guest_id` já existente, sem nunca tocar no nome. Corrigido: quando a identidade de canal já existe mas o hóspede ainda está sem nome salvo, a próxima mensagem preenche retroativamente (nunca sobrescreve um nome que já foi salvo). Testado (nome preenchido numa mensagem seguinte sem criar hóspede duplicado; nome já salvo não é sobrescrito por um valor diferente vindo depois) e regressão completa sem quebra. |

| 1.33.0 | 31/07/2026 | Oficial | Pedido do usuário testando o Messenger: a IA não tinha o número real de WhatsApp do hostel (+5493883154375), e ele quer que ela sugira esse número como alternativa de contato — logo no início (nas boas-vindas) e de novo perto do fim (dúvidas/confirmações) — quando a conversa é por um canal que não é o próprio WhatsApp. Achado: `hostels.phone` (coluna já existia, usada só internamente pelo endpoint de teste manual) nunca tinha UI nem rota pra ser preenchida — o número real do hostel nunca chegou a ser salvo em lugar nenhum. Novo `save_hostel_phone` (`database.py`); campo "Número de WhatsApp visível pro hóspede" adicionado ao card do WhatsApp em Configurações → Comunicação, salvo/lido junto com `phone_number_id`/`access_token` (`/settings/whatsapp`). `ask_ai` ganhou `channel`/`hostel_phone` — quando o canal não é WhatsApp e o hostel tem número cadastrado, um novo bloco de instrução (`{alt_channel_instruction}`) pede pra IA mencionar o WhatsApp brevemente na mensagem de boas-vindas e de novo perto do fechamento da conversa, sem repetir a cada mensagem; ausente (nenhuma menção) quando já é WhatsApp ou quando o hostel não tem número configurado. Testado (state salvo/lido certo pela rota, instrução presente só na combinação certa de canal+número configurado, `process_incoming_message` repassando o número certo pra IA) e regressão completa sem quebra. |
| 1.34.0 | 31/07/2026 | Oficial | Pedido do usuário, junto com um print mostrando o modal de perfil do hóspede aberto com campos vazios apesar do hóspede ter mandado nome, documento e foto pelo Messenger: clicar no nome na aba Reservas deve levar pra aba Hóspedes (não abrir o modal direto de lá), e dentro da aba Hóspedes o clique deve mostrar um perfil de LEITURA (campos fixos com o que já existe), não um formulário aberto de cadastro — com um botão explícito "Editar" pra trocar de modo. `guestNameLink()` (Reservas) agora chama `goToGuestProfile()` (nova) em vez de abrir o modal direto: navega pra aba Hóspedes, recarrega a lista e dá scroll+destaque visual (`.guest-row-highlight`, 2s) na linha do hóspede clicado. `openGuestProfileModal()` reescrita: cacheia o perfil já buscado (`window._currentGuestProfile`) e delega a um `renderGuestProfileModal(profile, editMode)` que desenha o mesmo conteúdo em dois modos — leitura (`guestReadonlyField()`, caixas fixas com "—" quando vazio) ou edição (grid de `<input>` de sempre, com Salvar/Cancelar); usado tanto direto (clique na aba Hóspedes, abre em leitura) quanto após salvar edição (recarrega e reabre em leitura mostrando o valor novo). Testado (navegação Reservas→Hóspedes com scroll+destaque na linha certa, perfil abre em leitura por padrão, alternância leitura↔edição preserva os dados, salvar edição atualiza a lista e reabre em leitura com o valor novo) e regressão completa sem quebra. |
| 1.34.1 | 31/07/2026 | Oficial | Duas causas raiz distintas, achadas junto com o pedido acima, pra explicar por que o perfil do hóspede do Messenger aparecia vazio mesmo depois dele informar os dados pelo chat: (1) `save_guest_date_of_birth`/`save_guest_nationality` (`database.py`) faziam `UPDATE ... WHERE phone = ?` — como `guests.phone` é sempre `NULL` de propósito pra Messenger/Instagram (decisão da integração de canais), qualquer chamada da IA pra salvar nacionalidade/data de nascimento nesses canais afetava silenciosamente ZERO linhas, sem erro nenhum. Corrigido com `save_guest_date_of_birth_by_id`/`save_guest_nationality_by_id` (novo, `WHERE id = ?`), usadas pelos handlers de tool-call correspondentes em `ask_ai`. (2) Messenger nunca teve tratamento de imagem/documento — diferente do WhatsApp (que troca `media_id` por URL temporária antes de baixar), a Send API do Messenger já entrega uma URL de CDN pronta pra baixar direto nos anexos da mensagem. Novo `download_messenger_attachment` (`services/messenger_service.py`) e `handle_incoming_document_image` (`routes/meta_webhook.py`, mesmo padrão do equivalente WhatsApp) — o loop principal do webhook agora distingue mensagem com anexo de imagem (baixa, salva como documento do hóspede, confirma por texto direto) de mensagem de texto normal (segue pro pipeline de IA de sempre). Testado (4 cenários: nacionalidade/data salvas por `guest_id` mesmo sem telefone, `ask_ai` chamando as versões certas via tool-call, documento recebido e salvo com o `guest_id` certo e confirmação enviada, falha ao baixar o anexo avisa o hóspede sem derrubar o webhook) e regressão completa sem quebra. |
| 1.34.2 | 31/07/2026 | Oficial | Bug real reportado pelo usuário: no menu "☰ Ações" do Mapa de Quartos, os itens "Novo quarto" e "Nova cama" pareciam sem reação ao clique. Investigação confirmou com um clique de verdade num navegador (Playwright) que o clique era fisicamente interceptado por `#roomMapGrid` (a grade de quartos/camas), não pelos botões do menu — apesar do dropdown ter `z-index:20` só localmente. Causa raiz: `.card>*{position:relative;z-index:1}` (regra genérica que põe o conteúdo de qualquer `.card` acima dos gradientes decorativos de fundo) dá o MESMO `z-index:1` a todos os filhos diretos do card — a linha do cabeçalho (que contém o dropdown) e `#roomMapGrid` são ambos filhos diretos, empatam em `z-index:1`, e o desempate por ordem no DOM favorece `#roomMapGrid` (vem depois), fazendo a grade renderizar por cima do menu sempre que o dropdown aberto visualmente sobrepõe a grade — o `z-index:20` do dropdown nunca chegava a ser comparado, porque só vale dentro do próprio contexto de empilhamento do cabeçalho. Corrigido dando à linha do cabeçalho um `z-index:2` explícito (maior que o `1` do grid), o suficiente pra vencer o empate no nível do `.card`. Confirmado com teste real de clique (sem `force`) nos dois botões, sem erros de console, e balanceamento de chaves/parênteses do `dashboard.html` inalterado. |
| 1.35.0 | 31/07/2026 | Oficial | Retomada a feature pedida pelo usuário (iniciada e revertida numa rodada anterior por falta de tempo): em Configurações → Comunicação e Integrações, os cards de WhatsApp Business, Facebook Messenger, integração com canais (Beds24) e Webhook de saída viraram caixas resumidas e clicáveis (título + status, ex. "✅ Conectado" ou "Não configurado ainda — clique pra conectar"), em vez de formulários sempre abertos na tela. Clicar na caixa abre o formulário completo de sempre dentro do `genericModal` já usado em toda a StayFlow, com os MESMOS IDs de campo e as MESMAS funções de sempre (`saveWhatsappSettings`, `connectFacebook`, `activateBeds24Channel`, etc.) — só passam a existir no DOM enquanto o modal está aberto, em vez de sempre. As quatro funções `loadWhatsappSettings`/`loadFacebookSettings`/`loadBeds24Settings`/`loadOutboundWebhookSettings` (chamadas globalmente ao carregar a sessão) ganharam um trecho novo que atualiza o texto de status da caixa resumida (`whatsappSummaryDesc` etc.) ANTES do guard que existia (`if(!elX) return`) — sem esse reordenamento, o texto de status nunca apareceria fora do modal, já que os elementos do formulário só existem quando ele está aberto. Testado com clique de verdade (Playwright): as 4 caixas abrem o modal certo com os campos certos; salvar dados no modal, fechar e reabrir mostra o valor persistido; texto de status aparece correto (inclusive "não conectado") sem precisar abrir o modal, logo ao carregar a página. Balanceamento de chaves/parênteses e cobertura i18n (14 chaves novas × 5 idiomas) sem quebra. |
| 1.36.0 | 31/07/2026 | Oficial | Pedido do usuário: reservas vindas do chat (Messenger/WhatsApp) ficam pendentes até a equipe confirmar manualmente — quando confirmada ou cancelada, o hóspede precisa ser avisado de volta no mesmo chat, já com horário de check-in e endereço na confirmação. Novo `notify_guest_reservation_status(hostel_id, reservation_id, status)` (`database.py`), chamado no fim de `update_reservation_status_record` (dentro de `try/except` — falha no envio nunca derruba a mudança de status, que já foi commitada antes). Resolve o canal de volta do hóspede pela linha mais recente em `guest_channel_identities` (com fallback pro telefone em `guests.phone`, pra hóspede antigo sem identidade de canal registrada); só dispara pra WhatsApp e Messenger (Instagram ainda não tem envio implementado). Mensagem de confirmação inclui check-in (com o horário padrão configurado em Configurações → Empresa, se houver), check-out e endereço do hostel (idem); mensagem de cancelamento é mais simples, convidando a reagendar. Texto varia por idioma (`get_guest_language_by_id`, mesmos 5 idiomas do resto da IA), com fallback pt. Reserva sem hóspede vinculado (cadastro manual só com nome) ou sem telefone/PSID resolvível sai em silêncio, sem tentar enviar. Testado (5 cenários: confirmação via Messenger com endereço/horário na mensagem certa e gravada na conversa; cancelamento via WhatsApp; reserva sem canal resolvível não tenta enviar; mudar pra "pending" não notifica; falha simulada no envio não impede o status de ser atualizado) e regressão completa (12 scripts) sem quebra. |
| 1.37.0 | 31/07/2026 | Oficial | Terceiro canal conectado: Instagram Direct. A base de dados já estava pronta (colunas em `hostels` e 6 funções de CRUD/oauth-state em `database.py`, deixadas prontas quando o Facebook foi feito, mas nunca ligadas a nada). Pesquisa dedicada (documentação atual da Meta) confirmou que o "Instagram API with Instagram Login" é uma stack praticamente paralela ao "Facebook Login for Business" já usado pro Messenger — não uma variação dele: App ID/Secret próprios (`INSTAGRAM_APP_ID`/`INSTAGRAM_APP_SECRET`, variáveis novas, não reaproveitam `META_APP_ID`/`META_APP_SECRET`), autorização em `www.instagram.com/oauth/authorize` com `scope` direto (sem `config_id`), troca de código por token via **POST** em `api.instagram.com` (não GET como o Facebook), token de longa duração e envio de mensagem em `graph.instagram.com` — este último com o token no **header** `Authorization: Bearer` em vez de query param, e endpoint `/<IG_BUSINESS_ID>/messages` em vez de `/me/messages`. Não exige Página do Facebook vinculada (vantagem real do método novo). Novo `services/instagram_service.py` (`send_instagram_message`, `get_instagram_user_profile` — busca de nome é best-effort, sem confirmação oficial de que o endpoint existe pra esse fluxo, cai pra `None` sem quebrar nada — e `download_instagram_attachment`); `services/meta_oauth_service.py` ganhou `get_instagram_authorize_url`/`exchange_code_for_instagram_account`; `routes/meta_oauth.py` ganhou `/oauth/instagram/connect`/`callback`; `routes/settings.py` ganhou `GET/POST/DELETE /settings/instagram` (mesmo contrato do Facebook: form manual como alternativa ao OAuth). `routes/meta_webhook.py` foi generalizado pra um dicionário de adaptadores por canal (`_CHANNEL_ADAPTERS`, com wrappers de indireção pra continuar mockável em teste — capturar a função direto no dict quebraria o patch do nome no módulo) — resolve o canal pelo campo `object` do payload (`"page"` → Messenger, `"instagram"` → Instagram), com fallback tentando os dois lookups de hostel se o campo vier ausente/inesperado; o loop de eventos (texto, imagem, perfil) passou a ser o mesmo código pros dois canais. `database.py`: gate de canais permitidos na notificação automática de reserva confirmada/cancelada (`notify_guest_reservation_status`, v1.36.0) ganhou `"instagram"`. Frontend: terceiro card clicável em Comunicação (mesmo padrão dos outros), modal com os dois modos (Conectar/manual) espelhando o do Facebook; corrigido de brinde um bug real no retorno do OAuth (`handleMetaOAuthReturn` mostrava sempre a mensagem rotulada "Facebook", não importa o canal — trocado pra chaves genéricas `settings.metaOauth.*`). Testado (18 scripts de regressão incluindo 4 novos cenários específicos de Instagram: mensagem de texto roteada certo por `object`, documento salvo e confirmado no canal certo, fallback sem `object`, e reserva confirmada notificando pelo Direct) e teste real de clique em navegador (Playwright) nos três cards de Comunicação juntos, sem erro de console. Pontos que a pesquisa não confirmou com certeza na documentação oficial da Meta (marcados como "a confirmar no primeiro teste ao vivo", mesmo padrão já usado nesta sessão pro Beds24/`config_id` do Facebook): disponibilidade de nome/username do remetente pra esse fluxo específico; formato exato literal do payload do webhook (`object`/`entry.id`); se a assinatura do webhook no painel da Meta é uma seção separada da do Messenger; exigência de Business Verification pra esse escopo. Bloqueio de negócio (não é código): usuário precisa criar o produto "Instagram" no App Meta existente, pegar Instagram App ID/Secret em "API setup with Instagram login", e conectar uma conta de teste — sem isso, o botão "Conectar Instagram" redireciona com erro educado, sem quebrar nada. |
| 1.38.0 | 03/08/2026 | Oficial | Auditoria completa e correção do Documento Mestre (protocolo de revisão integral, linha a linha, mesmo padrão já aplicado na versão 1.3.0), motivada por uma sessão anterior de Claude não conseguir identificar funcionalidades reais do produto a partir deste documento. Achados e correções principais: (1) catálogo de permissões estava documentado em 12 chaves em três pontos (Capítulo 12, 16.21, 16.22) — `utils/permissions.py` já tinha 14 há algumas versões (`security` e `billing` adicionadas junto com a construção das telas de Segurança e Billing em Configurações, nunca refletidas aqui); (2) Capítulo 16 (Funcionalidades) e Capítulo 17 (Roadmap) ainda descreviam como "não implementado"/"planejado" um conjunto de capacidades já construídas e em produção há várias versões: Mapa de Quartos (housekeeping completo), Ask StayFlow como agente real (34 ferramentas, function calling multi-rodada — o Roadmap ainda dizia "simulação de conversa, sem conexão real com o Backend"), integração com Channel Manager (Beds24, 6 fases completas) e módulo de Segurança (troca de senha, sessões ativas, tentativas de login); (3) módulos inteiros sem nenhum registro no documento: integração com Messenger e Instagram Direct (identidade multi-canal, `guest_channel_identities`), Respostas Rápidas (Quick Replies) na aba Chats, hóspede de Longa Duração, perfil de hóspede com modo leitura/edição e documentos. Confirmado por testes reais: a Conversations API do Instagram (`GET /{instagram_business_id}/conversations`) devolve lista vazia mesmo com mensagens reais acontecendo — restrição de "Standard Access" da própria Meta (contas sem "Advanced Access" em `instagram_business_basic`/`instagram_business_manage_messages` não veem conteúdo de mensagem por essa API até passar por App Review), não um bug do StayFlow; conexão de conta e envio de mensagem continuam funcionando normalmente. Registrado como padrão de segurança estabelecido: nenhuma rota `GET /settings/*` (WhatsApp, Facebook, Instagram, Beds24) devolve o valor bruto de um token de acesso ao Frontend, sempre um booleano (`has_access_token`). Registrada a decisão permanente de posicionamento (já aplicada em `index.html`/`privacy.html`): a StayFlow nunca deve ser descrita como produto nichado em hostel — hostel é a primeira categoria de hospedagem atacada para validar a operação, não o mercado-alvo final, que é hospedagens de todo porte. |
| 1.39.0 | 04/08/2026 | Oficial | Auditoria de segurança completa pedida pelo usuário ("qual a facilidade pra alguém hackear meu site?"). Achados corrigidos: XSS armazenado real (nome/mensagem de hóspede e dados derivados da IA inseridos via `innerHTML` sem escape em `chats-live.js`/`stayflow-live.js` — qualquer hóspede podia injetar HTML/JS que executava no navegador da equipe); ausência de proteção contra força bruta no login (`count_recent_failed_logins`, bloqueio de 5 tentativas/15 minutos por e-mail); ausência de cabeçalhos de segurança (`X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Strict-Transport-Security`); senha de cadastro aceitava 1 caractere (`/register` alinhado ao mínimo de 8 já usado em `/security/change-password`); webhooks da Meta (`/webhook/meta`, `/webhook/whatsapp`) sem verificação de assinatura (`utils/webhook_security.py`, HMAC-SHA256 sobre o corpo cru via `X-Hub-Signature-256`, confirmado funcionando contra tráfego real da Meta em produção). Na sequência, implementado Content-Security-Policy (mantendo `unsafe-inline` em script/style de propósito — reescrever ~169 `onclick`/10 `onchange`/7 `onsubmit` inline pra remover essa exceção foi avaliado como refatoração grande demais pra fazer sem capacidade de teste visual real, adiada; `connect-src 'self'` já fecha exfiltração de dados via XSS, que é o vetor mais grave). Decisão permanente registrada: sessão nunca deve expirar automaticamente por tempo (nem absoluta, nem por inatividade) — usuário considera reentrar recorrentemente incômodo; revogação continua existindo (logout, troca de senha, revogar sessão específica). |
| 1.40.0 | 04/08/2026 | Oficial | Direito ao esquecimento (LGPD/Ley 25.326) pedido pelo usuário ao considerar como responder se o cliente em prospecção (Diplomatic Hotel) perguntar sobre proteção de dados. Novo `erase_guest_data(hostel_id, guest_id)` (`database.py`) e `POST /guests/<id>/erase-data`: apaga de verdade documentos (inclusive arquivo em disco) e conversas/mensagens do hóspede, anonimiza nome/telefone/email/data de nascimento/nacionalidade/documento, e atualiza `guest_name` em reservas e veículos já existentes sem apagar o registro financeiro (ação irreversível, com confirmação forte no Frontend via `stayflowConfirm`). Documentado também onde os dados ficam fisicamente hospedados (Render, região Oregon — US West) na política de privacidade, junto com menção ao novo botão de exclusão como mecanismo de autoatendimento pro direito ao esquecimento. |
| 1.41.0 a 1.41.2 | 04 a 05/08/2026 | Oficial | Câmbio evolui de cálculo simples pra uma operação de casa de câmbio de verdade: cotação atual (mercado) separada da cotação usada (com o hóspede), lucro calculado automaticamente na diferença, operador e horário registrados, vínculo opcional com hóspede. Cotação de referência passou a cobrir TODAS as moedas cadastradas (USD/ARS/CLP/BRL/PEN/BOB/COP), não só USD — quando a moeda da hospedagem é ARS, ancora no dólar blue (Bluelytics, a cotação que hospedagens argentinas usam de verdade no dia a dia) e cruza via USD pra qualquer outra moeda recebida; fora desse caso, usa taxa oficial direta (`open.er-api.com`, gratuita, sem chave). Corrigido bug real: o seletor de "moeda recebida" abria com a própria moeda da hospedagem selecionada por padrão, então a cotação nunca se preenchia sozinha sem troca manual — moeda da hospedagem agora nem aparece como opção (não faz sentido cambiar ela por ela mesma). Nova caixa dedicada de "Lucro estimado" no modal, com valor destacado (verde/vermelho conforme sinal), separada do valor creditado. Registrada terceira correção da decisão de posicionamento (ver v1.38.0): "hostel" usado como termo genérico de negócio em texto visível (`finance.exchange.modalDesc`, nos 5 idiomas) e em comentários de código escritos nesta sessão — corrigido pra "hospedagem"/"property"; regra de aplicação ampliada para cobrir também comentários de código que descrevem lógica de negócio, não só copy externa. |
| 1.42.0 | 05/08/2026 | Oficial | Rodada de correções de UX no mobile e em Configurações, a partir de feedback direto do usuário testando ao vivo. Corrigido bug real presente em três lugares (Configurações, Operações, Equipe): trocar de seção/aba mantinha a posição de rolagem anterior, dando a impressão de "pular" pro meio da seção nova em vez de abrir do topo — `switchSettingsSection`/`switchOperationsTab`/`switchTeamTab` passaram a resetar o scroll, mesmo padrão que `openPage()` já usava. Configurações no mobile (≤1100px) ganhou o mesmo padrão de duas telas já usado nos Chats (lista de categorias OU conteúdo da categoria escolhida, nunca as duas empilhadas), com botão "Voltar". Notificações (push) e Horário de silêncio consolidados numa única caixa/modal (horário de silêncio só existe pra gatear quando o push notifica, não fazia sentido ser configuração própria); sininho de alertas movido pra dentro da mesma caixa; Respostas Rápidas virou caixa clicável + modal, removendo o último formulário solto da tela de Comunicação. Corrigido de brinde um bug real encontrado na investigação: `saveSettings()` só buscava campos `data-setting` dentro da seção `#settings`, mas o modal genérico (`#genericModal`) é renderizado fora dela na árvore do DOM — o modal "Geral" (nome/tipo da hospedagem) provavelmente nunca salvava de verdade desde que virou modal; corrigido ampliando a busca pro `document` inteiro (seguro, cada nome de `data-setting` só aparece uma vez no código). |
| 1.43.0 | 05/08/2026 | Oficial | Notificações push nativas (Web Push API) — item que constava no Roadmap como deliberadamente adiado, retomado a pedido do usuário. Infraestrutura completa: chaves VAPID (variáveis de ambiente, nunca no repositório — recurso fica desligado em silêncio sem elas, mesmo padrão já usado pro `META_APP_SECRET`), service worker (`sw.js`, servido na raiz do site pra cobrir o site inteiro) e inscrição por dispositivo/pessoa (`push_subscriptions` — PC e celular contam como inscrições separadas). Nove tipos de evento configuráveis (`push_notification_types`, JSON por hospedagem, mesmo padrão de `alert_channels`): oportunidade de alta prioridade, reserva pendente, hóspede com problema/dúvida/frustração detectado pela IA mesmo fora da taxonomia de oportunidade de venda, mensagem nova numa conversa assumida manualmente pela equipe, pedido de cozinha, chamado de manutenção, ocorrência de segurança, chamado de manobrista, novo evento — mais "toda mensagem do chat" (única desligada por padrão, potencial de ruído). Hook operacional único (`notify_on_duty_staff_for_ticket`, `database.py`) cobre tanto chamado criado pela equipe via rota HTTP quanto chamado criado pela própria IA a partir de uma conversa, sem duplicar lógica. Cada checkbox "o que deve notificar" só aparece pra quem tem a permissão daquela área (`data-required-permission` + `applyPermissionVisibility`, mecanismo já existente reaproveitado) — manutenção só vê/liga a notificação de manutenção, manobrista só a de estacionamento, e assim por diante. Horário de silêncio (`quiet_hours_start`/`quiet_hours_end`, campo que já existia reservado exatamente pra esse uso desde a Sessão 7) passou a valer de verdade. Testado repetidamente contra o FCM real do Google (não só localmente simulado): tipo habilitado tenta enviar de verdade, tipo desabilitado nem tenta rede, inscrição expirada é limpa automaticamente após 404/410 real. |
| 1.44.0 | 05/08/2026 | Oficial | Autenticação em duas etapas (2FA/TOTP) — item que constava no Roadmap como "Em breve" desde a Sessão 7, implementado a pedido do usuário. `pyotp` (geração/verificação de código) e `qrcode` (QR em SVG, gerado no servidor como data URI, sem Pillow nem CDN externo). Ativação em Configurações → Segurança: QR code + chave manual pra escanear no Google Authenticator (ou similar), confirmação com o primeiro código, 8 códigos de backup de uso único mostrados uma única vez (hash bcrypt, normalizados na comparação — aceitos com ou sem traço, maiúsculo ou minúsculo). Login refatorado: senha certa numa conta com 2FA ativo devolve um `challenge_token` de curta duração (5 minutos, 5 tentativas) em vez de completar a sessão — só `POST /login/2fa`, depois de validar o código TOTP ou um código de backup, cria a sessão de verdade. Corrigido de brinde um bug real de migração encontrado durante o teste local: `_migrate_users_to_memberships` reconstrói a tabela `users` com uma lista fixa de colunas sempre que o banco é novo (a própria `CREATE TABLE` ainda cita `hostel_id` no texto, então a migração dispara até em banco recém-criado) — isso descartava silenciosamente qualquer coluna nova adicionada antes desse ponto do código, em qualquer banco novo; não afetava produção (já migrada há muito), mas quebraria o próximo deploy do zero. Corrigido preservando `totp_secret`/`totp_enabled` na reconstrução, mesmo padrão já usado pra `must_change_password`. |
| 1.45.0 | 05/08/2026 | Oficial | Módulo de Eventos — pedido do usuário ao lembrar que hospedagens de grande porte, como o Diplomatic Hotel em prospecção, também vendem espaço para eventos (casamentos, corporativo, conferências) como receita própria, algo que a StayFlow ainda não cobria (o Mapa de Quartos é só pra hospedagem). Item novo na barra lateral (permissão própria `events`, adicionada ao catálogo), com três abas: Espaços (salões/jardins/auditórios, capacidade sentados/em pé, preço de aluguel), Eventos (agenda com checagem de disponibilidade em tempo real — conflito de horário no mesmo espaço é rejeitado na criação — ficha de cliente que não precisa ser hóspede, tipo de evento, status pendente→confirmado→concluído ou cancelado) e Adicionais (catálogo de serviços extras com preço congelado no momento em que são anexados a um evento, pra reajuste futuro do catálogo não alterar retroativamente um evento já fechado). Receita de eventos confirmados entra automaticamente no Financeiro, mesmo padrão já usado pra reserva/pagamento/câmbio. Decisão de escopo registrada: Eventos ficou como item próprio na barra lateral, não dentro de Operações (que reúne "chamados" rápidos resolvidos por quem está de plantão) nem dentro de Reservas/Receitas (que são sobre hospedagem e upsell pro hóspede já hospedado, não aluguel de espaço com cliente e calendário próprios) — avaliação feita explicitamente com o usuário antes de implementar. |

| 1.46.0 | 05/08/2026 | Oficial | Auditoria completa e correção do Documento Mestre e do Diário de Engenharia, motivada por cobrança explícita do usuário depois de uma auditoria anterior (nesta mesma sessão) ter sido apresentada como "revisão completa" sem seguir o protocolo formal de leitura sequencial de 100% do conteúdo. Repetida com rigor total: leitura sequencial confirmada das 8190 linhas do Documento Mestre e das 5397 linhas do Diário, mais verificação cruzada contra o código real (`utils/permissions.py`, `dashboard.html`, estrutura de pastas). Achados reais, não presentes em nenhuma auditoria anterior: (1) o catálogo de permissões estava documentado como 15 chaves em três pontos (12.3, 16.21, 16.22) quando `ALL_PERMISSIONS` já tinha 20 — faltavam 5 chaves (`kitchen`, `maintenance`, `patrimonial_security`, `parking`, `scheduling`) adicionadas em 04/08/2026 junto com um módulo operacional inteiro (5 áreas novas com IA integrada) que nunca chegou a ser registrado nem no Documento Mestre nem no Diário, apesar de já estar em produção; (2) dentro da própria seção 16.22, duas menções residuais a "14 permissões" sobreviveram à correção anterior (12→14→15) sem nunca chegar a 15, inconsistentes com o "15" corrigido na mesma seção; (3) o módulo de Escala (`routes/scheduling.py` — setores, grade de turnos, consulta de quem está de plantão, pedido/aceite de cobertura de turno, aba própria dentro de Equipe) não tinha nenhum registro em lugar nenhum do documento; (4) a lista de abas do Frontend no Capítulo 11.3 não mencionava a aba Eventos (existente desde a v1.45.0); (5) `docs/CHECKLIST_ATIVO.md`, citado em três pontos do Documento Mestre e dois do Diário como "fonte única de prioridades de trabalho" ainda em uso, não existe mais no repositório — sem registro de quando ou por que foi removido. Corrigidos todos os pontos acima; nova seção 16.32 documenta o módulo de Escala; nova nota na seção 9.1 documenta o desaparecimento do `CHECKLIST_ATIVO.md`. De quebra, resolvida uma dívida antiga registrada no próprio Diário (Sessão 7): `HostelBot/StayFlow---Site/docs/` estava sem rastreamento no Git desde 23/07/2026 (robocopy `/MIR` sem excluir `docs/`) — os dois documentos passaram a ser versionados de verdade também no repositório do backend. |

| 1.47.0 | 13/08/2026 | Oficial | Rodada grande de funcionalidades construídas desde a v1.46.0 e nunca registradas neste documento até esta auditoria: (1) StayFlow Hub — painel interno da própria StayFlow (não do cliente), acesso por allowlist de e-mail (`STAYFLOW_ADMIN_EMAILS`, sem role "superadmin" no banco), listando todas as hospedagens/agências clientes com MRR estimado (tabela de preço, `PLAN_PRICES`) separado de propósito da comissão real de fato coletada (Mercado Pago Split, via `guest_charges`); ganhou impersonation real (`POST /stayflow-admin/impersonate`, reaponta `sessions.hostel_id` preservando o hostel de origem em `sessions.impersonating_from_hostel_id`, com registro em `impersonation_log`) — ver nova seção 16.33; (2) contas de agência parceira (Portfólio/Parceiros): `hostels.account_kind` (`lodging`/`agency`) e `agency_category`, catálogo `portfolio_items`, opt-in de outra hospedagem em `partner_offers`, comissão a pagar em `partner_referral_ledger`; Ask StayFlow e IA de atendimento (`services/ai_service.py`/`services/decision_engine.py`) passam a receber `account_kind` e trocam de prompt/ferramentas quando é agência (não tenta fluxo de reserva de quarto/check-in) — ver 14.3; (3) corrigido bug real de i18n: condição de corrida entre `assets/js/i18n-core.js` e `assets/js/i18n-dashboard-data.js` (o segundo carrega depois, perto do fim do `<body>`) matava silenciosamente `T()` e a atualização do título do topbar com `ReferenceError` quando chamados na janela entre os dois scripts — afetava de forma intermitente o modal de Câmbio, Escala, Equipe e Chats; (4) Opportunity Center passa a sugerir item de parceiro (`opportunities.suggested_partner_item_id`) quando a hospedagem não vende o que o hóspede pediu e existe algum item habilitado em `partner_offers` — hoje restrito ao intent `tour` do Decision Engine e sem matching semântico (sempre o primeiro item habilitado) — ver 16.4; (5) cadastro self-serve com plano escolhido: `planos.html` novo (página pública de preços, 3 planos reais — `PLAN_PRICES`: Starter US$89, Business US$349, Enterprise US$699+ negociado), `Register.html` lê `?plan=` da URL e envia `plan_name` para `POST /register`, que ativa o hostel automaticamente nesse plano via `set_billing_plan` sem aprovação manual — ver correção da seção 17.2/17.3 mais abaixo; (6) importador de dados via CSV (parser próprio em JavaScript, sem biblioteca externa) para Quartos, Hóspedes, Reservas, Equipe e Portfólio (`POST /rooms/import`, `/guests/import`, `/reservations/import`, `/team/import`, `/portfolio/items/import`) — ver nova seção 16.33; (7) tour de introdução no primeiro acesso (slides explicando os blocos do Dashboard, mais dica pontual por item de menu na primeira vez que é clicado), preferência gravada por pessoa em `users.onboarding_dismissed`/`user_feature_intros` (banco, não localStorage — funciona em qualquer dispositivo) — ver nova seção 16.33; (8) módulo de Operações ganhou botões de abrir chamado manual nas abas Cozinha/Manutenção/Segurança Patrimonial (reaproveitando rotas que já existiam sem nenhum botão ligado a elas) mais um botão dedicado de Estacionamento, e aba própria "Tarefas" para chamado avulso sem setor fixo (`POST /operations/tasks`, reaproveita a tabela `tickets` já existente com `type='task'`, sem notificação automática de plantão, diferente dos outros quatro tipos) — ver 16.14; (9) Ask StayFlow ganhou visão de imagem: `POST /ask` passa a aceitar `multipart/form-data` com foto (JPEG/PNG/WebP, convertida em data URI base64), e a IA (modelo `gpt-4.1-mini`, não Claude/Anthropic) decide sozinha se a foto é caso de reposição de estoque, pedido de cozinha, chamado de manutenção ou incidente de segurança, perguntando em vez de adivinhar quando a foto é ambígua — ver 16.27. De quebra, corrigida contradição real nas seções 17.2/17.3: o texto descrevia Billing como "modelo de cobrança em definição, sem processador nem plano ativo", desatualizado desde a Fase 1 (planos/trial/comp accounts, já em produção há mais tempo que este documento registrava) — reescrito refletindo o que de fato existe hoje e o que ainda não existe (cobrança recorrente automática da própria assinatura StayFlow, via Stripe/Mercado Pago Fase 2-3, continua só schema stub — não confundir com o Mercado Pago Split guest-facing, que já é real desde antes). |
| 1.48.0 | 19/08/2026 | Oficial | Suporte real a fotos no chat (WhatsApp/Instagram/Messenger). Antes, qualquer imagem recebida de um hóspede era arquivada automaticamente como "documento de identidade" e a IA nunca via a imagem. `messages.media_path`/`media_mime_type`/`media_token` (novo) guardam a mídia de verdade; webhooks (`routes/whatsapp_webhook.py`, `routes/meta_webhook.py`) passam a encaminhar a foto pro pipeline normal (`process_incoming_message`, aceitando `media_bytes`/`media_mime_type`); `ask_ai()` (`services/ai_service.py`) ganhou suporte a visão (conteúdo multimodal `image_url`, modelo com visão). Equipe também pode enviar foto pro hóspede (`POST /guests/<id>/send-photo` e equivalente em "Meu chat"), despachada pelo canal real do hóspede via `send_whatsapp_image`/`send_messenger_image`/`send_instagram_image` — corrigido de brinde um bug real: `send_message_to_guest_now` só mandava por WhatsApp antes, independente do canal de origem do hóspede. Rota pública `GET /media/chat/<token>` (token de 16 caracteres hex, sem sessão) existe porque as APIs da Meta baixam a imagem enviada e não conseguem autenticar com cookie de sessão. Testado via scripts próprios contra banco temporário antes de sincronizar pros três locais e publicar — ver 16.2. |
| 1.49.0 | 20/08/2026 | Oficial | Nova aba "Prospecção" no painel interno da StayFlow (`admin.html`) — CRM leve de outreach comercial, uso exclusivo da própria StayFlow (não é feature client-facing de hospedagem nenhuma). Motivada pelo usuário começar a prospectar hospedagens piloto (abordagem presencial e digital via WhatsApp/e-mail/Instagram) e querer controlar a lista de contatos dentro do próprio painel em vez de planilha externa. Tabela nova `stayflow_leads` (sem `hostel_id`, mesma categoria não-tenant de `stayflow_expenses`/`stayflow_team`): nome, hospedagem, prioridade (alta/média/baixa), canal (WhatsApp/e-mail/Instagram/presencial/outro), status (a contatar → mensagem enviada → respondeu → call agendada → call feita → piloto ativo, ou sem interesse/perdido), datas de último contato e próxima ação, observações. CRUD completo via `POST`/`PATCH`/`DELETE /stayflow-admin/leads`, protegido por `@require_stayflow_admin`, mesmo padrão de rotas/validação de `stayflow_admin.py` já usado pra despesas. Badge no menu e destaque visual em vermelho quando a data da próxima ação já venceu. Conteúdo da aba (formulário/tabela) fica só em português, sem i18n completo — ferramenta de uso pessoal do usuário, diferente do resto do painel — ver seção 16.34. |
| 1.50.0 | 20/08/2026 | Oficial | Contexto de IA separado por categoria de negócio, não mais um prompt genérico com rótulo trocado — motivada pelo usuário ter vários pilotos reais interessados em verticais bem diferentes entre si (imobiliária, estética/película automotiva, estamparia, loja online) e apontar que "cada um deve ter o seu próprio contexto, separadamente". `database.AGENCY_CATEGORIES` reorganizada em 8 grupos: `turismo`, `aluguel_carro`, `aluguel_bike`, `aluguel_equipamentos`, `imobiliaria`, `automotivo`, `comercio`, `servico_generico` (catch-all/fallback) — "automotivo"/"comercio" são GRUPOS (mesmo espírito de `hostel_type` livre pra hospedagem: a variedade real dentro deles, ex. estética/película/mecânica/funilaria e pintura/elétrica/borracharia/auto peças, é grande demais pra prompt por subtipo), com detalhe livre na coluna nova `hostels.agency_subcategory` (presets + "+ Novo tipo...", mesmo padrão de `hostel_type`). `services/ai_service.py`: `AGENCY_SYSTEM_PROMPT` único vira `AGENCY_CATEGORY_PROMPTS`, um prompt COMPLETO por grupo (vocabulário e perguntas específicas do negócio real, ex.: imobiliária fala de "imóvel"/"visita"), com `agency_subcategory` interpolado dinamicamente via `{agency_subcategory_line}` nos grupos automotivo/comércio. Espinha dorsal de garantias do produto (nunca inventar preço/item, sempre checar `get_offerings`, nunca fechar venda sozinho) idêntica em todas. `services/decision_engine.py` ganha o mesmo tratamento pro `business_context` usado na análise de oportunidade (em nível de grupo, sem subcategoria). De quebra, o usuário pediu que essas contas também tivessem a mesma integração com sistema próprio (PMS) que hospedagem já tinha (`dispatch_reservation_webhook`, v1.27.0) — como conta `agency` não tem reserva/check-in, criado `dispatch_opportunity_webhook` (`database.py`), disparado pelo Decision Engine (`opportunity_created`/`opportunity_updated`) toda vez que uma oportunidade é criada ou atualizada pra uma conta `agency` com webhook configurado; texto do modal de Configurações → Integrações passa a variar por `account_kind` (5 idiomas) pra não falar de "reserva" com quem não tem esse conceito. `Register.html` ganhou seletor em cascata (grupo → subcategoria livre, só pra automotivo/comércio) e o rótulo "PAX"/"Clientes" em `dashboard.html` foi atualizado — "PAX" continua só pra turismo/aluguel (termo do setor), demais grupos usam "Clientes". Testado com scripts próprios: os 8 prompts formatam sem erro e são todos distintos, subcategoria interpola certo (com e sem valor) só nos grupos automotivo/comércio, fallback pra categoria desconhecida cai em `servico_generico` sem quebrar, e o webhook de oportunidade dispara corretamente pra conta `agency` (criação e atualização) e NÃO dispara pra `lodging` (que continua só na reserva). |
| 1.51.0 | 20/08/2026 | Oficial | Nova flag `stayflow_leads.training_candidate` na aba Prospecção (`admin.html`) — pedido do usuário ao refletir sobre o caso do Diplomatic Hotel (equipe numerosa): operações grandes podem precisar de treinamento presencial/remoto pago pra adoção da equipe inteira, separado da mensalidade/comissão do piloto, e ele queria marcar quais contas são candidatas a isso sem perder o fio conforme os pilotos forem entrando. Flag simples (checkbox no formulário, selo 🎓 na linha da tabela, filtro "Só candidatos a treinamento"), não um sistema de tags genérico — escopo mínimo pro que foi pedido. Testado com três cenários: criar já marcado, marcar/desmarcar depois via `PATCH`, e — mais importante — migração seguindo o padrão `add_column_if_not_exists` num banco simulando produção (tabela já existia sem a coluna, com um registro real) confirmando que nenhum contato cadastrado antes desta versão se perde. |
| 1.52.0 | 22/08/2026 | Oficial | Alarme real de compromisso na Prospecção — usuário rejeitou explicitamente uma primeira tentativa (rotina agendada do próprio Claude Code) pedindo que fosse "a StayFlow" avisando, não uma ferramenta externa. `stayflow_leads` ganha `next_action_time` (hora do compromisso, o campo antigo só tinha data) e `alarm_offsets_minutes` (minutos antes, ex. `"30,10"`, editável via checkboxes + campo livre no formulário). Reaproveita 100% a infraestrutura de Web Push já existente desde a v1.43.0 (`services/push_service.py`, `sw.js`, `/push/subscribe`) — só nunca tinha sido ligada ao painel interno (`admin.html`); como o login do painel é dono do `hostel_id=1` ("StayFlow", conta de teste do próprio usuário), o mesmo endpoint funciona sem rota nova. Checagem via thread daemon em `app.py` (acorda a cada 60s, sem dependência nova tipo APScheduler); como o `Procfile` roda 3 workers do gunicorn em paralelo, a deduplicação usa uma tabela de "claim" (`stayflow_lead_alarms_fired`, `INSERT OR IGNORE` com `UNIQUE(lead_id, offset_minutes)`) em vez de lock distribuído. Fuso horário fixo em `America/Argentina/Mendoza` — decisão deliberada, ferramenta de uso pessoal do usuário, não multi-tenant. `send_push_to_admin` (diferente de `send_push_to_hostel`) não respeita horário de silêncio, porque é alarme pessoal explicitamente configurado. |
| 1.53.0 | 22/08/2026 | Oficial | Rodada de correções e melhorias encontradas em revisão ao vivo do painel pelo usuário, mais o primeiro item grande da lista de prioridades pós-auditoria: (1) selo de canal (WhatsApp/Instagram/Messenger) que faltava na lista do "Meu chat" do painel interno (`get_guests_inbox` não devolvia `channel`, diferente do Chats normal); (2) botão flutuante "Ask StayFlow" corrigido em duas telas que o sobrepunham ao botão "Assumir" (`dashboard.html` via `chats-page-active`, `admin.html` via nova classe `admin-chat-tab-active` — são fluxos de troca de aba independentes); (3) categoria do item do Portfólio corrigida: usava por engano `AGENCY_CATEGORIES` (classificação do NEGÓCIO, usada em Parceiros) como se fosse categoria do PRODUTO — virou texto livre com sugestão via `<datalist>`, e a validação equivalente no backend (`routes/portfolio.py`) foi removida (regressão pega e corrigida na mesma sessão, antes de qualquer cliente real usar); (4) upload real de foto no item do Portfólio (antes só aceitava URL colada) — nova tabela `portfolio_photos` + rota pública `/media/portfolio/<token>`, mesmo padrão de token opaco do `save_chat_media_file` (chat); (5) tela de histórico de visitas do Hub (`impersonation_log` já era gravado desde a v1.47.0, nunca tinha UI pra ler — nova seção em Configurações); (6) dropdown de idioma/usuário cortado no mobile corrigido (bug de meses, `left:0` fazia o dropdown nascer fora da tela nos dois botões mais à direita da barra); (7) limpeza de arquivos órfãos (`templates/components/` vazio, `teste-users.html`, `_screenshots_revisao/`) pendente desde julho; (8) **WhatsApp Embedded Signup** — conectar o WhatsApp Business sem colar `phone_number_id`/token manualmente, via SDK JS da Meta (`FB.login()` + evento `postMessage` `WA_EMBEDDED_SIGNUP`, mecanismo diferente do redirect usado por Facebook/Instagram porque roda embutido na própria página, sem state anti-CSRF necessário). Nova env var `WHATSAPP_CONFIG_ID` (pública, exposta ao frontend); CSP (`app.py`) ganhou a única exceção de host externo (`connect.facebook.net`) pro SDK funcionar. Depende de configuração externa (criar a "WhatsApp Embedded Signup configuration" no painel de developers da Meta) pra funcionar de ponta a ponta — mesmo tipo de bloqueio já registrado pro App Review do Instagram. |
| 1.54.0 | 23/08/2026 | Oficial | Integração Nuvemshop/Tiendanube (mesma empresa, nome diferente por país — Tiendanube na Argentina, Nuvemshop no Brasil), segundo item grande da lista de prioridades pós-auditoria. Contas `agency` de loja online ganham um card em Configurações → Comunicação pra conectar a loja via OAuth 2.0 (redirect com `state` anti-CSRF, mesmo padrão de Facebook/Instagram — pesquisa confirmou API versionada `api.tiendanube.com/2025-03`, header `Authorization: Bearer` + `User-Agent` obrigatório, domínio único servindo os dois países). Ao conectar: sincroniza todo o catálogo existente de uma vez e registra webhooks (`product/created`, `product/updated`, `product/deleted`, `order/paid`). Decisão de arquitetura: em vez de criar tabela nova pro catálogo, `portfolio_items` (a MESMA que já alimenta `get_offerings`/a IA) ganhou `external_id`/`source` — mesmo vocabulário já usado em `guest_channel_identities`, único precedente real de "dado veio de fonte externa" no schema — com índice único PARCIAL (`WHERE external_id IS NOT NULL`) garantindo sincronização idempotente sem nunca afetar item cadastrado manualmente (que fica com `external_id` `NULL`, e SQLite trata cada `NULL` como distinto). `order/paid` dispara push (novo tipo `nuvemshop_order`) com o resumo do pedido. Assinatura do webhook validada por `verify_nuvemshop_signature` (`utils/webhook_security.py`) — função própria, não reaproveita `verify_meta_signature`, já que o header (`x-linkedstore-hmac-sha256`, sem prefixo `sha256=`) e o secret (`NUVEMSHOP_CLIENT_SECRET`) são diferentes. Fora de escopo desta rodada: sincronizar estoque/variantes, mandar dado de volta pra Nuvemshop (só leitura), e Mercado Livre (plataforma própria separada, pendência à parte). |
| 1.55.0 | 23/08/2026 | Oficial | Card "Agente de IA" em Configurações → IA StayFlow ativado — era um placeholder morto desde sempre (`opacity:.5`, sem nenhum campo real, condição de liberação citando o Ask StayFlow que nunca teve relação de verdade com essa feature). Terceiro item grande da lista pós-auditoria. Novo `settings.ai_custom_instructions` (texto livre, até 2000 caracteres, validado no backend) — cada hospedagem/agência pode escrever instruções de persona/tom/regras específicas do próprio negócio. `services/ai_service.py::ask_ai()` ganha `custom_instructions=None`, interpolado como uma seção ADICIONAL (`{custom_instructions_section}`) no fim de `SYSTEM_PROMPT` (hospedagem) e `_AGENCY_PROMPT_SKELETON` (agência) — deliberadamente fora de `SOFTWARE_SYSTEM_PROMPT` (número comercial da própria StayFlow, não configurável por cliente). A seção deixa explícito que as instruções do dono NUNCA substituem a espinha dorsal de segurança (nunca inventar preço, nunca fechar venda sozinha) — testado renderizando os 9 templates (SYSTEM_PROMPT + 8 categorias de agência) com e sem instrução customizada, sem erro de formatação. Reaproveita 100% o mecanismo genérico de Configurações (`_SETTINGS_TEXT_FIELDS`) pra leitura/escrita, sem endpoint novo. |
| 1.56.0 | 23/08/2026 | Oficial | "Resposta automática para dúvidas simples" ativada — quarto item grande da lista, mesmo padrão de placeholder morto do item anterior (checkbox `checked disabled`, texto "depende do recurso de assumir conversa" — recurso que já funciona há tempo). Hoje "assumir conversa" (`guests.ai_paused`) é tudo ou nada: equipe assume, IA para de responder 100% até alguém devolver. Novo comportamento opcional (`settings.simple_auto_reply_enabled`, desligado por padrão): mesmo com a conversa assumida, se a mensagem classificar como baixo risco, a IA ainda responde essa mensagem pontual — `ai_paused` continua `true`, a equipe segue dona da conversa. Decisão de arquitetura: reaproveita a classificação que `services/decision_engine.py::analyze_message()` já calcula ANTES do gate de `ai_paused` em `routes/chat.py` (campos `intent`/`urgency`, sem chamada de IA extra só pra isso) — critério de "dúvida simples" é `intent in ("general", "follow_up")` E `urgency == "low"`; `intent == "human_help"` ou qualquer urgência acima de `low` mantêm o silêncio de sempre. Consequência aceita conscientemente: como essa classificação só existe quando "Geração de oportunidades" está ligada, o recurso novo depende dela (documentado na própria UI) em vez de rodar uma segunda chamada de IA só pra classificar. De quebra: o push `assumed_conversation` (que antes disparava sempre que chegava mensagem numa conversa assumida) passa a ser suprimido especificamente quando a IA já respondeu a dúvida sozinha — sem isso, a equipe seria alarmada com "hóspede esperando" mesmo depois do problema já ter sido resolvido. |
| 1.57.0 | 23/08/2026 | Oficial | Matching semântico na sugestão de item de parceiro do Opportunity Center, quinto item grande da lista pós-auditoria — resolve a dívida técnica registrada desde a v1.47.0 ("sempre o primeiro item habilitado, sem matching semântico"). A sugestão (`opportunities.suggested_partner_item_id`) usa a MESMA chamada de IA que já classifica a conversa (`services/decision_engine.py::analyze_with_ai()`), sem round-trip extra: quando a conta é `lodging` e existe algum item habilitado em Parceiros (`get_enabled_partner_items_for_hostel`, que ganhou `description` no `SELECT` pra dar mais contexto), a lista de candidatos (id/nome/categoria/descrição) entra no mesmo prompt e o schema JSON de resposta ganha `suggested_partner_item_id`. Continua restrito a `intent == "tour"` (mesma decisão de produto da v1.47.0 — `upsell` é genérico demais); a mudança é só em COMO escolher entre os candidatos, não em QUANDO sugerir. Validação defensiva: o id devolvido pela IA só é aceito se realmente está entre os ids oferecidos no prompt, protegendo contra alucinação. Contas sem nenhum item de Parceiro habilitado não ganham o bloco novo no prompt — custo de token idêntico a antes. |
| 1.58.0 | 23/08/2026 | Oficial | Consolidação da arquitetura de deploy do frontend, sexto item grande da lista pós-auditoria — resolve a dívida técnica registrada desde a v1.4.0 (cópia manual do frontend pra dentro do repositório do backend). `HostelBot/StayFlow---Site/` (a cópia que o Render de fato publica, já que ele builda um repositório só por serviço) deixou de ser uma pasta com arquivos copiados à mão (`cp`/`xcopy`/`robocopy`) e virou um `git subtree` do repositório `StayFlow---Site` — sincronizar passa a ser um comando único (`bash sync_frontend.sh`, novo, wrapper de `git subtree pull --squash`), sem risco de esquecer de copiar algum arquivo. Também removida uma terceira cópia órfã (`HostelBot/admin.html`, na raiz do repositório do backend, fora de `StayFlow---Site/`) — versão antiga, não referenciada por nenhuma rota do Flask (que serve tudo via `FRONTEND_DIR`), resíduo de uma estrutura anterior. `HostelBot` ganhou `.gitattributes` (`eol=lf`) pra eliminar ruído de diff causado pela normalização de quebra de linha que o `git checkout` aplica ao trazer o subtree (CRLF), diferente do que a cópia manual antiga preservava por acidente. Verificado com `diff` recursivo (ignorando só quebra de linha) que o conteúdo do subtree é byte-idêntico ao canônico, e que o Flask continua importando e servindo `FRONTEND_DIR` normalmente — nenhuma configuração do Render precisou mudar, o caminho servido continua o mesmo de sempre. Fora de escopo, deliberadamente: separar o frontend como Static Site próprio do Render (a solução "definitiva" do Roadmap) — envolveria cookies de sessão cross-domain, CORS e reconfiguração do escopo do Service Worker, risco real demais pra pilotos reais ativos agora, pra um ganho que o subtree já entrega sem mexer em topologia de produção. |
| 1.59.0 | 23/08/2026 | Oficial | Billing Fase 2 — cobrança recorrente automática da própria assinatura StayFlow, sétimo item grande da lista pós-auditoria, resolvendo a única frente de Billing que ainda era 100% manual/honra (`payment_processor`/`processor_customer_id`/`processor_subscription_id` existiam como schema stub desde a Fase 1, nunca escritos por ninguém). Decisão de processador: Mercado Pago (API `preapproval`, assinatura recorrente nativa), não Stripe — motivo prático, não só técnico: Stripe não abre conta padrão pra recebedor domiciliado na Argentina (o monotributo do usuário), o que inviabilizaria receber o dinheiro de verdade. Usa uma credencial NOVA e separada (`MERCADOPAGO_PLATFORM_ACCESS_TOKEN`, a conta MP da própria StayFlow) — diferente da credencial OAuth do Split guest-facing (`MERCADOPAGO_CLIENT_ID`/`SECRET`, por-hostel), já que aqui é a StayFlow recebendo do hostel, direção de dinheiro oposta à do Split. Novo `services/mercadopago_billing_service.py` (`create_preapproval`/`get_preapproval`/`cancel_preapproval`/`get_authorized_payment`), novas rotas `POST /billing/subscribe` (gera o link de checkout), `GET /billing/subscribe/return` (retorno pós-checkout) e `POST /billing/cancel`; novo webhook `POST /webhook/mercadopago-billing` (idempotência própria via `mp_billing_webhook_events`, separada de `mp_webhook_events` do Split) tratando tanto `subscription_preapproval` (autorização/cancelamento) quanto `subscription_authorized_payment` (cobrança mensal individual, exige uma consulta a mais em `/authorized_payments/{id}` pra resolver a qual assinatura pertence). Preço cobrado em ARS (`PLAN_PRICES_ARS`, mantido manualmente — motor de câmbio automático continua fora de escopo, dívida separada e já conhecida). Novo laço em `app.py` (`_billing_trial_expiration_loop`, roda a cada hora) marca `past_due` quem terminou o trial de 30 dias sem nunca ter assinado (`database.expire_stale_trials()`) — decisão explícita de escopo: isso é só bookkeeping, NÃO bloqueia nenhuma rota/feature por inadimplência nesta rodada, risco considerado alto demais de derrubar um piloto real (Hotel Camelo, rede do Miguel Seda) por engano numa primeira versão; trava de acesso fica pra uma decisão separada e explícita depois que a cobrança em si estiver validada em produção. UI nova em Configurações → Billing: botão "Assinar agora" (quando sem assinatura ativa) ou "Cancelar assinatura" (quando ativa), tratamento de retorno via `?billing_return=1` (mesmo padrão genérico já usado pelas integrações OAuth). Pré-requisito externo pra funcionar em produção (mesmo tipo de bloqueio já registrado pro WhatsApp Embedded Signup e pro App Review do Instagram): usuário precisa gerar um Access Token de produção na própria conta Mercado Pago dele. |
| 1.60.0 | 23/08/2026 | Oficial | Oitavo item da lista pós-auditoria (remoção do `unsafe-inline` do CSP) reavaliado com números concretos e a decisão de v1.39.0 CONFIRMADA, não esquecida — sem mudança de código. Contagem atual: ~341 atributos de evento inline (`onclick`/`onchange`/`onsubmit`/`oninput`/`onkeydown`, 81% em `dashboard.html` com 10.881 linhas, 17% em `admin.html`), crescido de ~186 desde a v1.39.0 (confirma que o custo só aumenta com o tempo); ~990 atributos `style=` inline (82% em `dashboard.html`). Achado técnico novo (não estava registrado antes): por especificação CSP nível 2+, um navegador que entende `'nonce-...'` em `script-src` IGNORA `'unsafe-inline'` na mesma diretiva — não existe migração incremental possível (nonce só nos poucos `<script>` inline quebraria todos os `onclick` de uma vez em navegador moderno); `'unsafe-hashes'` (CSP3) não resolve `style-src` porque boa parte dos 990 atributos é gerada dinamicamente via JS, invalidando hash estático. Decisão: continua sendo defesa em profundidade sobre um vetor que `connect-src 'self'` já fecha (o mais grave, exfiltração via XSS) — não vale o risco de regressão espalhada num arquivo de quase 11 mil linhas sem capacidade de teste visual, sem demanda real (ex: cliente enterprise exigindo auditoria formal) pra justificar agora. Ver seção "Decisão permanente registrada" (Capítulo 16) pra o registro completo. |
| 1.61.0 | 23/08/2026 | Oficial | Nono item da lista pós-auditoria (idiomas novos) — primeira leva: japonês e italiano adicionados aos 3 dicionários i18n (landing pública, Dashboard, painel interno `ADMIN_I18N`) — 1.341 chaves por idioma (90 + 1.028 + 223), terminologia de hotelaria revisada por comparação com os blocos `en`/`pt` existentes, placeholders e tags HTML preservados. `assets/js/i18n-core.js` (`SUPPORTED_LANGS`, detecção por `navigator.language`) e os 3 seletores de idioma hardcoded (`index.html`, `dashboard.html`, `admin.html`) atualizados manualmente — não é genérico a partir do dicionário, cada idioma novo exige essas 4 edições pontuais além da tradução em si. Criado `tools/check_i18n_parity.py`, rede de segurança automática que confere paridade de chaves entre todos os idiomas nos 3 dicionários (antes era só disciplina manual) — ver seção 16.35. Usuário pediu, na sequência, mais 4 idiomas (chinês, russo, coreano, holandês) — em andamento, registrado quando concluído. |
| 1.62.0 | 24/08/2026 | Oficial | Conclusão do item "idiomas novos" — chinês (`zh`), russo (`ru`), coreano (`ko`) e holandês (`nl`) adicionados aos mesmos 3 dicionários (1.341 chaves cada), completando um total de 6 idiomas novos nesta rodada (ja/it/zh/ru/ko/nl), 11 idiomas suportados ao todo. Traduzido via agentes em background, um por idioma, em sequência (não em paralelo, pra evitar conflito de edição concorrente nos mesmos 3 arquivos) — dois agentes esbarraram em limite de sessão no meio do trabalho e precisaram ser retomados, sem perda de progresso (`tools/check_i18n_parity.py` confirmou exatamente onde cada um tinha parado antes de retomar). Corrigida nesta versão uma alegação falsa que tinha entrado na documentação da v1.61.0 por um dos agentes de tradução (escreveu documentação por conta própria, fora do escopo pedido): dizia que o seletor de idioma "não precisou de mudança de código" — falso, `SUPPORTED_LANGS` e os 3 dropdowns HTML são hardcoded e foram editados manualmente pra cada idioma novo. Árabe/hebraico permanecem deliberadamente fora (RTL, exigem CSS de layout espelhado). Ver seção 16.35 (reescrita, consolidada). |
| 1.63.0 | 24/08/2026 | Oficial | Dashboard de métricas de chat por período — décimo item da lista pós-auditoria, resolvendo o gap confirmado entre `routes/executive.py`/módulo de Relatórios (só totais acumulados, sem série temporal) e o que a documentação descrevia. Novo parâmetro `?period=daily\|weekly\|monthly` em `/reports`, nova chave `chat_activity` na resposta (mensagens recebidas do hóspede, conversas distintas, conversões — reaproveitando o mesmo proxy de conversão já usado no funil existente, `reservations.status='confirmed'`, já que `opportunities.status` nunca muda de `'open'` no código atual). Gráfico em Canvas nativo na aba Relatórios, mesmo estilo já usado no painel interno (`admin.html::renderGrowthChart`) — sem introduzir biblioteca de gráfico nova. `statistics.html` (página órfã, dado fake) removida de brinde. Ver seção 16.36. |
| 1.64.0 | 24/08/2026 | Oficial | 3 ajustes no painel interno da StayFlow (`admin.html`, virou o painel principal do usuário), motivados por uso ao vivo: (1) F5 sempre resetava pra Visão Geral — `switchAdminTab()` não tinha nenhuma persistência (variável JS em memória só); corrigido com `localStorage` (mesmo padrão já usado por `stayflow_lang`), restaurando a aba certa no bootstrap; (2) Despesas virou sub-aba dentro de Financeiro (pill switcher "Visão geral"/"Despesas", mesmo padrão `.ops-tabs`/`.ops-tab` já usado em Operações/Eventos/Equipe no dashboard normal) em vez de item de menu próprio — investigação confirmou que o botão "+ Nova despesa" já usava a classe CSS padrão (`class="btn"`, idêntica à de outros cadastros), a percepção de "fora do padrão" vinha da posição no menu, não do CSS; (3) Configurações ganhou uma seção "Comunicação" com WhatsApp/Facebook/Instagram da conta "assistente comercial" ("persona software", a mesma que "Meu chat" já usa) — antes só existia status agregado read-only de credenciais de plataforma, zero conectividade por conta. Novas rotas `/stayflow-admin/software-persona/{whatsapp,facebook,instagram}` (GET/POST/DELETE conforme o canal) em `routes/stayflow_admin.py`, reaproveitando as MESMAS funções que `routes/settings.py` já usa (zero duplicação de lógica) — só troca a autorização (`@require_stayflow_admin`, sem `hostel_id` de tenant na sessão) por uma resolução fixa via `get_hostel_id_by_ai_persona("software")`. WhatsApp usa o MESMO fluxo de Embedded Signup já construído (v1.53.0, `FB.login()` + evento `WA_EMBEDDED_SIGNUP`) — clique único, sem redirect. Facebook/Instagram usam OAuth com redirect e callback fixo registrado na Meta — como não dá pra duplicar esse callback sem reconfigurar o app na Meta, o botão "Conectar" chama `/stayflow-admin/impersonate` (já existia) pra essa conta e navega pro fluxo OAuth normal; ao terminar, o usuário vê o banner de impersonation ("Sair da visualização") pra voltar ao painel — trade-off aceito conscientemente, não é 100% "sem sair da tela" como o WhatsApp, mas ainda é clique-e-conecta, sem colar token manualmente. Ver seção 16.37. |
| 1.65.0 | 24/08/2026 | Oficial | Programa de parceiro/indicação com comissão recorrente — item 12 da fila, inspirado no "Plan Partner" da Aoki (25/30/35% em faixa), formalizando o que o Miguel Seda já faz informalmente trazendo uma rede de 3 hotéis. Investigação inicial mostrou que o único conceito de "parceiro" já existente (`partner_referral_ledger`) é sobre venda de item de portfólio de agência pro hóspede — sistema irmão, não reaproveitado, não mexido. Achado que mudou o desenho: o `property_name` real do Miguel Seda na Prospecção é "Promotor StayFlow Brasil" — ele não tem conta StayFlow, então o programa não podia ser modelado só como "hostel indica hostel" (não caberia o próprio caso de uso que motivou o pedido). Solução: nova entidade `referral_partners`, desacoplada de `hostels` (`linked_hostel_id` NULL quando é promotor externo cadastrado à mão via `admin.html`, preenchido quando é hostel cliente indicando outro — linha criada sob demanda na primeira vez que ele abre o card no dashboard, zero setup). Nova `subscription_referral_ledger` acumula `SUBSCRIPTION_REFERRAL_COMMISSION_PCT = 0.20` (fixo, não em faixas — ponto de partida simples, sinalizado como ajustável) sobre cada cobrança de assinatura APROVADA de um hostel indicado, direto dentro de `mercadopago_billing_webhook.py::_process_authorized_payment_notification` — único ponto do sistema que confirma "esse hostel pagou agora"; idempotente via `UNIQUE(mp_payment_id)`, mesma técnica do `mp_webhook_events`. `get_authorized_payment` (`mercadopago_billing_service.py`) ganhou `transaction_amount` no retorno pra alimentar o cálculo. `hostels.referred_by_partner_id` setado uma única vez em `/register` (novo campo opcional `referral_code`), sem retroatividade. UI: `Register.html` lê `?ref=CODE` da URL; `dashboard.html` ganha card "Programa de indicação" em Configurações/Billing (link com copiar, lista de indicados, totais); `admin.html` ganha pill "Indicações" dentro de Financeiro (mesmo padrão visual de "Repasses" já existente) com payout manual e formulário de cadastro de parceiro externo. Testado ponta a ponta em banco isolado antes do commit (lazy-creation, idempotência de dupla notificação, payout, stats) — não só `import app`. Payout continua manual/bookkeeping, mesma decisão já tomada pro partner-ledger e pro Billing; faixas por volume (como a Aoki) ficam pra depois, se o percentual fixo não bastar como incentivo. |
| 1.66.0 | 25/08/2026 | Oficial | Fix de layout mobile em "Meu chat" e "Suporte" (`admin.html`) — reportado ao vivo pelo usuário via print: no celular, os dois usam `.chat-layout` de 2 colunas (lista + conversa) igual o desktop, e a conversa ficava escondida/espremida em vez de abrir em tela cheia. O mecanismo certo já existia — `chats-live.js::setChatMobileView()` + CSS `[data-mobile-view]` — mas era escopado só pra `#chats` (a aba de Chats do dashboard normal do cliente); nunca tinha sido estendido pro `admin.html`. Reaproveitado o mesmo padrão (não recriado): `#chatShell`/`#supportShell` (os dois `.chat-layout` do painel interno) ganharam `data-mobile-view="list"` por padrão + `window.setAdminChatMobileView(layoutId, view)` novo (escopado por ID explícito, diferente do `chats-live.js` que usa `querySelector` genérico — necessário porque o admin.html tem DOIS `.chat-layout` na mesma página, não um só). Botão "←" (`.chat-mobile-back`, classe já existente, reaproveitada) chama a troca de volta pra lista; abrir uma conversa (`openMyChatGuest`/`openSupportThread`) muda pra tela de chat quando `window.innerWidth <= 1100`. `switchAdminTab()` ganhou o mesmo toggle de `.chat-fullscreen` no `.main` que o dashboard já usa, pra rolar só a área de mensagens em vez da página inteira. CSS (`static/css/app.css`) estendido pra cobrir `#chatShell`/`#supportShell` nas mesmas regras que já existiam pra `#chats`, sem duplicar lógica nova. Nova chave `common.back` no `ADMIN_I18N` (faltava, reaproveitando a tradução já existente em `i18n-dashboard-data.js`) — `tools/check_i18n_parity.py` confirmou paridade nos 11 idiomas (252 chaves). |
| 1.67.0 | 25/08/2026 | Oficial | Tags, notas internas e origem do lead no perfil do hóspede — pesquisa competitiva ampla (Chatty, Hubtype, respond.io, Darwin AI, Cloudbeds, todos pesquisados a pedido do usuário a partir de anúncios reais do Instagram) confirmou 3 recursos que concorrentes de CRM/mensageria têm e a StayFlow não tinha, verificado direto no código (nenhuma tabela de tag/nota/UTM existia). O anúncio do respond.io destacava "Tag Contacts Buyer Intent" como feature própria — validação de mercado extra pras tags. Achado técnico: o webhook do WhatsApp (`routes/whatsapp_webhook.py::receive_message()`) já recebe o payload `referral` da Meta (quando a mensagem vem de um anúncio "Click to WhatsApp": `source_type`, `source_url`, `headline`, `body`, `ctwa_clid`) mas descartava sem ler. Novas tabelas `guest_tags` (`UNIQUE(guest_id, tag)`, texto livre) e `guest_notes` (log append-only, com autoria via `get_current_user_id()`); nova coluna `guests.lead_referral_json` gravada por `set_guest_lead_referral()` — idempotente, só escreve se ainda `NULL`, nunca sobrescreve a origem original do lead. Novas rotas `POST/DELETE /guests/<id>/tags`, `POST /guests/<id>/notes`, reaproveitando `GET /guests/<id>` (`get_guest_profile` estendido) pra devolver tudo junto. UI no painel `.guest-profile` da aba Chats (`dashboard.html`/`chats-live.js`): 2 novas seções (Tags com pills removíveis, Notas internas com autor/data) + badge "📢 Veio de anúncio" na hero quando `lead_referral` existe — escopo desta rodada só a aba Chats (fluxo real de atendimento), modal de edição de perfil da lista de Hóspedes fica de fora, mesmos dados já disponíveis no backend pra estender depois. Pesquisa também cobriu Hubtype (enterprise, 15M+ interações/mês, sem vertical de hotelaria) e Cloudbeds (PMS líder de mercado, IA própria "Signals" — não replicável agora por exigir anos de dado histórico acumulado, não é limitação de código; preço US$180-220+/mês de piso vs US$89 da StayFlow) — nenhuma feature nova além das 3 já citadas foi considerada necessária a partir dessas duas. Testado ponta a ponta em banco isolado antes do commit (tag duplicada vira no-op, nota vazia levanta erro, dupla tentativa de `set_guest_lead_referral` confirmando idempotência). `tools/check_i18n_parity.py` confirmando as 10 chaves novas nos 11 idiomas (1.047→1.057). |
| 1.68.0 | 25/08/2026 | Oficial | Tarifa por temporada nas modalidades de quarto — primeiro de 3 itens de "maturidade de PMS" levantados na comparação com o Cloudbeds (PMS líder de mercado, IA própria Signals). `room_categories.price_per_night` era um único REAL fixo, sem calendário; o cálculo `price_per_night * nights` estava DUPLICADO em 3 funções (`create_reservation_record`, `create_reservation_from_chat`, `create_reservation_from_channel`). Nova tabela `rate_rules` (`hostel_id, room_category_id, name, start_date, end_date, price_per_night`), ancorada em `room_categories.id` (FK de verdade — decisão deliberada de não repetir a fragilidade do `room_type` por string usada em `reservations`). Nova função central `calculate_reservation_amount()` soma o preço NOITE A NOITE consultando `rate_rules`, substituindo a lógica triplicada nos 3 pontos de criação de reserva — elimina a duplicação em vez de criar uma quarta cópia. Sobreposição de regras: a criada mais recentemente vence (determinístico). Sem variação por dia da semana nesta rodada — escopo mínimo do que foi pedido. UI: nova seção "Tarifas por período" dentro do modal de edição de modalidade já existente (`editCategoryUI`) — lista de regras + formulário simples. Testado ponta a ponta em banco isolado (regra cobrindo parte da estadia, sobreposição entre duas regras, validação de data invertida e categoria inexistente, e confirmação de que `create_reservation_record` usa o cálculo novo automaticamente). `tools/check_i18n_parity.py` confirmando as 9 chaves novas nos 11 idiomas (1.057→1.066). |
| 1.69.0 | 25/08/2026 | Oficial | Reserva de grupo — segundo dos 3 itens de "maturidade de PMS" (comparação com Cloudbeds). Antes, `reservations` era sempre 1 linha = 1 cama/quarto (`bed_id` singular), sem nenhum mecanismo de agrupar N quartos numa mesma reserva (ex: excursão/evento). Nova tabela `reservation_groups` (só uma "capa" com `guest_name`) + coluna nullable `reservations.group_id` — quando preenchida, várias linhas de `reservations` pertencem ao mesmo grupo. Nova função `create_group_reservation(hostel_id, guest_name, bookings, ...)` reaproveita 100% de `create_reservation_record()` (chamada uma vez por quarto da lista, só passando `group_id` a mais) — mesma trava de cama (`reservar_cama_com_trava`) e mesmo webhook de saída de sempre, sem duplicar validação. Sem motor de desconto — cada quarto mantém seu preço normal, incluindo tarifa por temporada se aplicável (v1.68.0). Novas rotas `POST /reservations/group` e `GET /reservations/group/<id>`; `GET /reservations` (já existente) passou a incluir `group_id` em cada linha. UI: toggle "Reserva de grupo" no modal de Nova reserva já existente, permitindo adicionar N blocos de quarto antes de salvar tudo de uma vez; selo "👥 Parte de um grupo" na listagem quando `group_id` está preenchido. Testado ponta a ponta em banco isolado: grupo de 2 quartos criado corretamente, trava de cama confirmada funcionando contra uma reserva FORA do grupo tentando a mesma cama (prova que a validação é a mesma, não uma cópia mais fraca), validação de grupo vazio e grupo inexistente. |
| 1.70.0 | 25/08/2026 | Oficial | Multi-propriedade (habilitar o que já existia) — terceiro e último item de "maturidade de PMS" (comparação com Cloudbeds). Achado que mudou o escopo: investigação (`routes/auth.py`/`database.py`/`dashboard.html` completos) confirmou que o mecanismo de multi-propriedade JÁ EXISTIA ponta a ponta e nunca tinha sido usado de verdade — `hostel_memberships` já é N:N (usuário↔hostel), `_complete_login` já lida com múltiplos hostels, `POST /select-hostel` já troca de hospedagem sem logout, e `dashboard.html` já tem o seletor visual completo (`toggleHostelSelector`/`switchHostel`/`populateHostelSelector`). Confirmado por query direta no banco: nenhum usuário real tinha mais de 1 `hostel_membership` ativo, porque o único jeito de ganhar uma segunda era ser CONVIDADO por outro hostel via Equipe — não existia fluxo de "eu, já logado, quero abrir uma propriedade nova sob minha própria conta". Fechado esse gap real (não o mecanismo de troca, que já funcionava): nova função `create_hostel_and_membership_for_user()` (mesmo padrão de 3 `INSERT`s — hostel, role Admin, `hostel_membership` — que `create_identity_and_hostel()` já usa, só sem criar usuário novo; função separada de propósito em vez de fatiar a existente, que já está em produção via `/register`). Nova rota `POST /account/add-hostel`, mesmo estilo de checagem manual de sessão já usado em `/select-hostel` (não usa `@require_permission`, ainda não há tenant resolvido pra essa ação). UI: botão "+ Adicionar hospedagem" dentro do mesmo dropdown seletor de hostel que já existia na topbar — nome da hospedagem + `POST /account/add-hostel`, já troca a sessão pra propriedade nova ao final. Deliberadamente fora de escopo: qualquer visão agregada cross-propriedade (dashboard combinado, relatório somando várias hospedagens) — ninguém pediu isso de verdade ainda, o gap real era só "criar a segunda propriedade". Testado em banco isolado E via Flask test client simulando o fluxo real (login com múltiplos hostels → seleção pending → `/account/add-hostel` → sessão já aponta pra hospedagem nova → `/select-hostel` continua alternando de volta pra hospedagem original sem logout). Encerra a leva de 3 itens de maturidade de PMS iniciada com a v1.68.0. |
| 1.71.0 | 25/08/2026 | Oficial | Ponto de funcionário e histórico de ação rastreável — surgiu da pesquisa competitiva (Cloocker, app de controle de ponto/fichaje): usuário perguntou se isso não serviria pra StayFlow e lembrou de um pedido antigo nunca atendido — saber quem fez o quê e quando (ex: camareira arruma uma cama, hóspede reclama, dono quer saber QUEM e A QUE HORAS, sem desculpa possível). Investigação (agente Explore) confirmou os dois gaps reais: "Escala" (`staff_shifts`) é só planejamento futuro, `status` nunca sai de `'scheduled'`, zero prova de comparecimento real; `mark_bed_cleaned`/`set_bed_maintenance` não recebiam nenhum `membership_id`, só mudavam o status da cama sem autor nem horário; o sistema de `tickets` (5 blueprints — cozinha/manutenção/segurança/operações/estacionamento) tinha rastreabilidade parcial (quem relatou, quem foi designado) mas não quem de fato RESOLVEU (só quem foi designado, que pode ser outra pessoa) nem histórico de mudanças de status. Nova tabela `staff_attendance` (`clock_in_at`/`clock_out_at`, um registro por turno realmente trabalhado — `clock_in()` bloqueia duplicata se já houver ponto aberto, `clock_out()` fecha o mais recente). Nova tabela genérica `staff_activity_log` (`entity_type`/`entity_id`/`action`/`detail`) reaproveitável por qualquer módulo em vez de uma tabela de log por feature — ligada em `mark_bed_cleaned`/`set_bed_maintenance` (ganharam `membership_id`) e nas 3 funções de ticket (`assign_ticket`/`update_ticket_status`/`resolve_ticket`, ganharam `actor_membership_id`, resolvido nas rotas via o mesmo padrão que `routes/scheduling.py::create_shift_route` já usava: `get_membership(get_current_user_id(), hostel_id)`). `tickets` ganhou `resolved_by_membership_id` como fato de primeira classe (não só log) — resolve o caso concreto de auditoria. Nova rota `GET /team/<id>/activity-log` combina ponto + ações num histórico só, exposto na Equipe via botão "Histórico" por membro; aba Escala ganhou botão "Bater ponto". Testado em banco isolado E via Flask test client (ciclo de ponto duplo bloqueado, fluxo completo de ticket assign→in_progress→resolve gravando o autor certo em cada etapa, histórico combinado correto via rota real). Fora de escopo deliberado: geolocalização/biometria no ponto, alertas automáticos de atraso, edição de ponto já registrado, e uma tela dedicada de "chamados resolvidos" nos 5 módulos de ticket (o dado já existe e aparece no histórico do funcionário; tela dedicada fica pra se for pedida). |
| 1.72.0 | 26/08/2026 | Oficial | Integração Tokko Broker (etapa 1 de 2 dos itens 13/14 da fila, inspirados na Waichatt — concorrente vertical em imobiliária) — sincroniza o catálogo de imóveis de uma imobiliária pra dentro da StayFlow, restrito a `account_kind='agency'` + `agency_category='imobiliaria'`. Investigação confirmou terreno greenfield (zero menção a "tokko"/imóvel em código) e que a API real do Tokko é bem mais simples que a Nuvemshop: chave de API única por imobiliária (gerada em "Mi Empresa → Permisos" no painel deles), colada manualmente — sem OAuth, sem redirect, sem token que expira. Reaproveitado 100% o mecanismo de sync externo que já existia só pra Nuvemshop: `portfolio_items` (índice único parcial `hostel_id+source+external_id`) e `upsert_portfolio_item_from_external()`, agora também chamado com `source='tokko'`. Nova tabela companheira `real_estate_details` (1:1 via `portfolio_item_id`) guarda os campos estruturados que só fazem sentido pra imóvel (operação, localização, quartos, banheiros, m²) sem poluir a tabela genérica usada por passeio/aluguel de bike. Novo `services/tokko_service.py` (`list_properties`/`sync_tokko_properties`) e rotas `GET/POST/DELETE /settings/tokko` + `POST /settings/tokko/sync` em `routes/settings.py`, atrás de `_require_real_estate_agency()` (mesmo espírito de `_require_agency`, mais a checagem de `agency_category`). Bug real encontrado e corrigido de brinde: `upsert_portfolio_item_from_external()` — em produção desde a integração Nuvemshop — tinha `ON CONFLICT(hostel_id, source, external_id)` sem repetir o `WHERE external_id IS NOT NULL` da unique index parcial; SQLite exige a cláusula idêntica pra reconhecer o alvo de conflito num índice parcial, então TODO insert (não só em conflito) quebrava em tempo de parse — nunca detectado porque nenhum teste isolado tinha exercitado esse caminho antes. UI: novo card "Tokko Broker" em Configurações, primeiro precedente de gating por `agency_category` no frontend (`data-required-agency-category`, estendendo `applyAccountKindVisibility()` que antes só olhava `account_kind`) — chave de API, status, "Sincronizar agora", desconectar. Testado em banco isolado com mock da API do Tokko (sem chamada de rede real) confirmando upsert idempotente em `portfolio_items`+`real_estate_details`. 17 chaves i18n novas nos 11 idiomas (1.093→1.110). Etapa 2 (matching de imóvel por preferência do comprador, reaproveitando `opportunities.suggested_partner_item_id`) fica pra versão seguinte. |
| 1.73.0 | 26/08/2026 | Oficial | Matching de imóvel por preferência do comprador (etapa 2 de 2 dos itens 13/14) — novo branch em `decision_engine.py` pra `account_kind='agency'` + `agency_category='imobiliaria'`: candidatos vêm do PRÓPRIO catálogo (`get_own_active_portfolio_items`, já criado na v1.72.0), caso inverso do matching de tour existente desde a v1.57.0 (hospedagem oferecendo catálogo de um PARCEIRO terceiro). Prompt inclui preço/localização/quartos/operação (venda ou aluguel) — o caso de tour deliberadamente omite preço. Reaproveita 100% o mesmo campo `suggested_partner_item_id` e a MESMA validação anti-alucinação (id só aceito se estiver no set de candidatos realmente enviado à IA); dispara quando `intent=='booking'`, o mais próximo que a classificação genérica de intent já tem de "quer fechar negócio nisso". Achado que corrigiu uma premissa errada do plano original: a investigação de planejamento tinha concluído que `suggested_partner_item_id` "nunca era renderizado em lugar nenhum" (por ter revisado só `dashboard.html`), mas a renderização já existia desde sempre em `assets/js/stayflow-live.js` (`opportunityRowHtml`/`updateOpportunitiesPrioritySidebar`) — arquivo separado carregado pela página, fora do escopo da investigação anterior. Verificado antes de construir de novo o que já existia; UI nova ficou restrita a diferenciar a COPY (`isOwnCatalogSuggestion()`): "Sugestão: {item} via {agency}" + botão "Oferecer parceiro" continuam pro caso de tour (parceiro terceiro de verdade), mas viram "Sugestão: {item}" + "Oferecer imóvel" quando o vendedor é a própria conta — evita chamar a própria imobiliária de "parceiro" dela mesma. Bug real encontrado e corrigido só ao testar esse fluxo ponta a ponta: `routes/guest_charges.py` gravava `referring_hostel_id` (e uma linha em `partner_referral_ledger`) pra QUALQUER cobrança `charge_type='partner_item'`, mesmo quando vendedor e chamador são a MESMA hospedagem — exatamente o caso novo de imobiliária oferecendo o próprio catálogo, que geraria uma "comissão de indicação" da conta pra ela mesma. Corrigido pra só gravar `referring_hostel_id` quando o vendedor é de fato OUTRA agência; testado em banco isolado confirmando os dois comportamentos (self-catalog não grava indicação, indicação real de parceiro terceiro continua gravando normalmente). De brinde, 2 chaves i18n (`opportunities.partnerSuggestion`/`offerPartnerBtn`) que já eram usadas no código desde a v1.57.0 mas nunca tinham entrado no dicionário — sempre mostraram só o fallback em português, independente do idioma selecionado. 4 chaves i18n novas nos 11 idiomas (1.110→1.114). Testado em banco isolado: sugestão válida aceita, id alucinado (fora do set de candidatos) rejeitado, conta `lodging` nunca aciona o branch de imóvel, intent diferente de `booking` não aciona matching. Encerra os itens 13/14 da fila, iniciados com a Tokko Broker na v1.72.0. |
| 1.74.0 | 27/08/2026 | Oficial | Tela de "chamados resolvidos" nos 5 módulos operacionais (Cozinha/Manutenção/Segurança patrimonial/Estacionamento/Tarefas) — primeiro item da leva pós-fila-zerada, priorizado por ser o de menor risco (dado já existia desde a v1.71.0 — `tickets.resolved_by_membership_id`/`resolved_at` — só faltava uma tela pra consultar; era "fora de escopo deliberado, fica pra se for pedida" na v1.71.0, foi pedido agora). Nova `get_resolved_tickets(hostel_id, ticket_type=None, limit=20, offset=0)` em `database.py`, ao lado de `get_open_tickets` — mesmo JOIN de `get_ticket` pra trazer `resolved_by_name`, paginada como `get_opportunities_list` (`{items, total}` — decisão deliberada de NÃO seguir o padrão sem paginação do `/team/<id>/activity-log`, já que chamados resolvidos acumulam sem limite natural ao longo da vida da hospedagem, diferente do histórico pessoal de um funcionário). 5 rotas novas, uma por blueprint (`GET /kitchen/orders/resolved`, `/maintenance/tickets/resolved`, `/patrimonial-security/incidents/resolved`, `/parking/valet-requests/resolved`, `/operations/tasks/resolved`), thin, mesmos decorators que a rota de abertos irmã já usa — mantendo a independência deliberada entre os 5 blueprints já registrada na v1.71.0. UI: pill switcher "Abertos/Resolvidos" (reaproveita `.ops-tabs`/`.ops-tab`, mesmo componente visual já usado pra alternar entre os módulos) dentro de cada um dos 5 painéis, com um novo painel de histórico (4 colunas: local, descrição, resolvido por, resolvido em — sem coluna de ação, é só consulta) + botão "Mostrar mais" no mesmo padrão do Opportunity Center. Lógica de toggle/carregamento é UMA função genérica compartilhada pelos 5 módulos (`switchTicketView`/`loadResolvedTickets`, config por módulo num dict), não 5 cópias quase idênticas — reaproveita `escapeHtml`/`opportunityDateLabel` já existentes. 6 chaves i18n novas nos 11 idiomas (1.114→1.120). Testado em banco isolado (2 hospedagens, 5 tipos de chamado, confirma que só os resolvidos aparecem, chamado aberto nunca vaza, `resolved_by_name` correto via JOIN, filtro por tipo, paginação sem sobreposição, isolamento de tenant nos dois sentidos) e via Flask test client (as 5 rotas novas respondendo 200 com o formato `{items, total}` correto). |
| 1.75.0 | 27/08/2026 | Oficial | Diária de fim de semana (sexta/sábado) por modalidade de quarto — segundo item da leva pós-fila-zerada, estende a tarifa por temporada (`rate_rules`, v1.68.0) que cobria "preço diferente num intervalo de DATAS" mas não tinha nenhum conceito de dia da semana. Nova coluna `room_categories.weekend_price_per_night` (REAL, nullable — mesmo padrão opt-in de `price_per_night`; `NULL` = recurso desligado, comportamento idêntico a antes desta versão). Precedência por noite calculada em `calculate_reservation_amount`, do mais específico pro mais genérico: 1) `rate_rule` de temporada que cobre aquela data (inalterado — ex: Réveillon continua podendo sobrepor um sábado específico) → 2) diária de sexta/sábado, se configurada e a noite cair num desses dois dias (`current.weekday() in (4, 5)`, calculado no mesmo loop noite-a-noite que já existia, antes de virar string) → 3) diária normal, fallback de sempre. "Fim de semana" fica fixo em sexta+sábado nesta rodada (convenção padrão de hotelaria/lazer) — não configurável, mesmo espírito minimalista das demais features do produto. Nenhuma mudança nos 3 pontos de chamada de `calculate_reservation_amount` (`create_reservation_record`/`create_reservation_from_chat`/`create_reservation_from_channel`) — a data já chegava neles do jeito de sempre, o dia da semana é derivado internamente. UI: novo campo "Diária de sexta/sábado (opcional)" no modal de edição de modalidade (`editCategoryUI`), logo abaixo da diária normal, usando a MESMA rota `PATCH /room-categories/<id>` já existente (sem rota nova) — `list_room_categories` e `update_room_category` estendidos pra incluir a coluna nova, seguindo exatamente o mesmo padrão de coerção que `price_per_night` já usava (campo vazio/ausente vira `NULL`, desliga o recurso). 1 chave i18n nova nos 11 idiomas (1.120→1.121). Testado em banco isolado: retrocompatibilidade total sem a coluna configurada, terça normal vs. sábado com preço de fim de semana, estadia mista somando noite a noite corretamente, precedência de `rate_rule` de temporada vencendo sobre a diária de fim de semana no mesmo sábado, domingo explicitamente fora da regra (só sexta/sábado), e desligamento do recurso voltando a `NULL`; e via Flask test client confirmando que o `PATCH` grava e `list_room_categories` lê de volta o valor salvo. |
| 1.76.0 | 27/08/2026 | Oficial | Desconto automático em reserva de grupo — terceiro item da leva pós-fila-zerada, estende a reserva de grupo (`reservation_groups`, v1.69.0) que até esta versão não tinha nenhum motor de desconto ("Sem motor de desconto - cada quarto mantém seu preço normal", documentado no próprio comentário do código desde a criação). Nova coluna `reservation_groups.discount_pct` (REAL, nullable — registro do desconto aplicado, pra auditoria/exibição; não afeta cálculo na leitura, já que o valor final descontado fica gravado em `reservations.amount` de cada quarto, mesma convenção de sempre — nunca existiu "preço de tabela vs. cobrado" separado no sistema de reservas). `create_group_reservation` ganha `discount_pct` opcional (0-100, validado — negativo/acima de 100/não numérico levanta `ValueError`), digitado pelo staff na criação do grupo e aplicado automaticamente sobre o valor de CADA quarto — tanto o calculado via `calculate_reservation_amount` (considerando temporada/fim de semana) quanto um valor digitado manualmente pra aquele quarto, mesma regra pros dois casos. Decisão deliberada: desconto é sempre digitado pelo staff nesta rodada, não uma regra automática por tamanho de grupo (ex: "3+ quartos = 5% sozinho") — mesmo espírito minimalista de outras decisões do produto (comissão de indicação fixa, tarifa sem variação por dia quando criada). `get_reservation_group` passou a devolver um `group_total` computado (soma em Python dos valores por quarto, sem SQL novo) — fecha um gap identificado na investigação: nem a criação do grupo nem a listagem de reservas mostravam nenhum total em lugar nenhum antes desta versão, só o valor de cada quarto isoladamente. UI: campo "Desconto do grupo (%) — opcional" no bloco de reserva de grupo do modal de Nova Reserva; após criar com sucesso, busca o resumo do grupo e mostra o total (com o desconto já aplicado) numa confirmação, em vez de só fechar o modal sem feedback nenhum como acontecia antes — lição da v1.73.0 reaplicada aqui (feature sem UI visível é feature que não existe na prática). 4 chaves i18n novas nos 11 idiomas (1.121→1.125). Testado em banco isolado: retrocompatibilidade sem desconto, desconto aplicado sobre valor calculado automaticamente, desconto aplicado sobre valor digitado manualmente, validação rejeitando valores inválidos; e via Flask test client confirmando que `POST /reservations/group` com desconto e o `GET` de detalhe do grupo batem no `group_total` esperado. |
| 1.77.0 | 27/08/2026 | Oficial | Alertas automáticos de atraso/no-show — quarto item da leva pós-fila-zerada. Investigação confirmou 3 achados que mudaram o escopo esperado: (1) `no_show` já era um status válido de `reservations`, com dropdown/pill/KPI completos — o gap real não era "criar o status", era avisar proativamente, deixando a decisão com a equipe; (2) a condição de detecção já existia em `GET /operations` (bloco "arrival": `checkin_date = hoje AND status != 'cancelled' AND checked_in_at IS NULL`), só que passiva (só aparecia se alguém carregasse a página); (3) a StayFlow já tem um scheduler funcionando em produção — nada de APScheduler/cron/worker separado no Render, `app.py` já registra threads em background (`threading.Thread` + `while True` + `sleep`) pros alarmes de compromisso da Prospecção e expiração de trial, com deduplicação entre os 3 workers do gunicorn via tabela de "claim" (`INSERT OR IGNORE` + `cursor.rowcount`). Clonado exatamente esse padrão em vez de inventar infraestrutura nova: novo `services/no_show_alert_service.py::check_late_arrivals(now=None)` (parâmetro `now` injetável, pra testar a borda do horário de corte sem depender do relógio real), novo laço `_late_arrival_alert_loop()` em `app.py` rodando a cada 15min, nova tabela `late_arrival_alerts_fired` + `claim_late_arrival_alert()`/`get_pending_late_arrivals()` em `database.py`. Depois das 18h (horário fixo, fuso `America/Argentina/Mendoza` — mesmo fuso único já hardcoded pros alarmes de lead, sem conceito de fuso por hospedagem hoje; não configurável nesta rodada), avisa a equipe de cada hospedagem sobre reservas do dia ainda sem check-in físico, via `send_push_to_hostel(..., notification_type="late_arrival")` — decisão deliberadamente conservadora: só ALERTA, nunca marca `no_show` sozinho, mesmo espírito já usado no billing ("só bookkeeping, nenhuma rota trava sozinha"). Um alerta por reserva, nunca repete. Novo tipo de notificação push `late_arrival` (default ligado, mesmo grupo de `reservation`/`opportunity`) registrado nos 5 lugares necessários pra consistência: lista default do backend, checkbox nova em Configurações → Notificações, `defaultPushTypes` e `pushTypeCheckboxIds` no JS, 1 chave i18n nos 11 idiomas (1.125→1.126). Testado em banco isolado com `now` injetado: antes do horário de corte nada dispara nem reivindica nada; depois das 18h dispara exatamente pras reservas pendentes certas (excluindo `checked_in_at` preenchido e status `cancelled`/`no_show`), cada push indo pro `hostel_id` certo entre múltiplas hospedagens; rodar de novo não dispara segunda vez (dedup via claim). Fora de escopo deliberado: marcar `no_show` automaticamente, horário de corte configurável por hospedagem, múltiplos alertas por dia, e alerta de check-out atrasado (só atraso de check-in, que é o conceito de "no-show"). |
| 1.78.0 | 01/09/2026 | Oficial | Comissão em faixas pro programa de indicação — quinto item da leva pós-fila-zerada. O programa (v1.65.0) pagava 20% recorrente fixo sobre cada mensalidade aprovada de hostel indicado; o próprio comentário do código já antecipava isso desde a criação ("fixo por enquanto, não em faixas por volume como o [Plan Partner] da Aoki"). Decisão confirmada com o usuário antes de implementar: mantém 20% recorrente vitalício como já era (sem prazo de expiração, comissão só sobre a MENSALIDADE — nunca sobre comissão de passeio/upsell, sistemas totalmente separados), só introduzindo faixas por volume de indicações **ativas** (`billing.status='active'`): 1-2 = 20%, 3-5 = 25%, 6+ = 30%, recalculado PRA FRENTE a cada novo pagamento — nunca retroativo em linhas já lançadas no razão, já que `subscription_referral_ledger.commission_pct` sempre foi gravado POR LINHA (não uma referência a constante global), então a mudança não exigiu migração nenhuma. Nova `SUBSCRIPTION_REFERRAL_COMMISSION_TIERS` (lista ordenada) + `resolve_subscription_referral_commission_pct()` + `count_active_referrals_for_partner()` (mesmo JOIN de `get_hostel_referral_stats`, só filtrado e contado) em `database.py`; `_process_authorized_payment_notification` (`mercadopago_billing_webhook.py`) calcula a faixa na hora do lançamento em vez de usar a constante fixa. `get_subscription_referral_summary()` estendida com `active_referral_count`/`current_tier_pct` por parceiro — painel "Indicações" (`admin.html`, Financeiro) ganhou 2 colunas novas mostrando isso, porque sem visibilidade ninguém consegue explicar por que um lançamento saiu numa % e outro noutra. Testado em banco isolado (fronteiras exatas das 3 faixas) e via webhook ponta a ponta com mock de `get_authorized_payment` (2 pagamentos em sequência pro mesmo parceiro — primeiro a 20%, parceiro sobe pra 6 indicações ativas, segundo pagamento a 30%, e o lançamento antigo confirmado intocado em 20%). 2 chaves i18n novas no `ADMIN_I18N` (252→254). |
| 1.79.0 | 01/09/2026 | Oficial | Auto-cadastro público de parceiro de indicação externo — surgiu direto da criação de um post de Instagram sobre o programa de indicação: até esta versão, um indicador que não é cliente StayFlow só virava parceiro se o Caio cadastrasse manualmente pelo `admin.html` ("+ Parceiro manual") — sem isso, o post traria volume que não escalava (cada resposta exigindo cadastro manual). Nova página pública `ReferralPartner.html`, clone do estilo visual de `Register.html` (mesma paleta, mesmo card, sem sistema de template — página standalone), onde a pessoa se cadastra sozinha (nome + e-mail ou WhatsApp) e recebe o link de indicação (`Register.html?ref=CODIGO`) na hora, com botão de copiar. Nova rota pública `POST /referral-partner-signup` (`routes/auth.py`) seguindo o MESMO padrão de rota pública que `/register` já usava (sem NENHUM decorator de autenticação, só validação manual + a `UNIQUE` do banco como rede de segurança — confirmado que não existe rate-limit nem captcha em lugar nenhum do projeto) — reaproveita `create_manual_referral_partner()` sem duplicar lógica, só com um honeypot simples (campo escondido `website`) como única proteção antispam. Após o cadastro, dispara `send_push_to_admin()` (mesmo mecanismo já usado pelos alarmes de compromisso da Prospecção, best-effort — uma falha no push nunca impede a resposta de sucesso pro usuário) pra avisar o Caio. Nova coluna estruturada `contact_email`/`contact_phone` em `referral_partners` (antes só existia `contact_note` livre) — `admin.html` ganhou os mesmos campos no formulário manual existente, contato exibido na tabela, e um box com o link de auto-cadastro pronto pra compartilhar (ex: no bio do Instagram). Achado corrigido de brinde, necessário pra essa feature fazer sentido: `get_subscription_referral_summary()` fazia `JOIN` (não `LEFT JOIN`) com o razão, então um parceiro recém-cadastrado sem NENHUMA indicação paga ainda ficava completamente invisível no painel admin — corrigido pra `LEFT JOIN`, com total/contagem em 0 até a primeira comissão. Testado em banco isolado e via Flask test client: cadastro com sucesso devolve `referral_code` e notifica o admin; nome vazio e "sem e-mail nem telefone" rejeitados (400); honeypot preenchido bloqueia a criação no banco; falha simulada no push nunca quebra a resposta de sucesso; rota manual do admin continua funcionando com e sem os campos novos; parceiro recém-cadastrado aparece no resumo com total 0. 5 chaves i18n novas no `ADMIN_I18N` (254→259). |
| 1.80.0 | 01/09/2026 | Oficial | Dashboard agregado cross-propriedade — próximo item da fila reordenada (métrica pública do Opportunity Center foi empurrada pro final a pedido do usuário). Multi-propriedade (v1.70.0) já deixava trocar entre hospedagens, mas não existia visão somada. Achado registrado antes de construir: até a última verificação (diário v1.70.0), nenhum usuário real tinha 2+ `hostel_memberships` ativos — decisão deliberada de construir mesmo assim, pelo caminho mais barato (reaproveitar `get_user_hostels`/`get_dashboard_stats` já existentes num loop, somando em Python, sem SQL cross-tenant nova), como investimento pra quando alguém precisar. Nova rota `GET /dashboard/aggregated` (`routes/dashboard.py`), com checagem manual de sessão (mesmo padrão de `/select-hostel`, já que a sessão só resolve UM `hostel_id` por vez — não dá pra usar `@require_permission` aqui). `occupancy_pct` agregado é recalculado a partir da SOMA de camas ocupadas/total, nunca como média das porcentagens individuais. UI: opção "🗂️ Todas as propriedades" no seletor de hospedagem (`#hostelSelectorList`), só visível com 2+ hospedagens na sessão, abrindo modal (`openGenericModal`) com os KPIs somados + lista das hospedagens incluídas. Fora de escopo: relatório detalhado agregado, ações a partir da visão agregada, resumo executivo por IA agregado, paginação de muitas propriedades. Testado em banco isolado: soma exata entre 2 hospedagens com dados bem diferentes (100+250=350), occupancy calculado da soma (7/15=47%, não da média 40%/60%=50%), isolamento confirmado (hospedagem de outro usuário nunca entra na soma), usuário com 1 hospedagem só também funciona (gate é só de UI), 401 sem sessão válida. 4 chaves i18n novas (`allProperties.*`) nos 11 idiomas (1.126→1.130). |
| 1.81.0 | 01/09/2026 | Oficial | Geolocalização no ponto de funcionário — próximo item da fila (26). O ponto (`staff_attendance`, v1.71.0) tinha geolocalização/biometria registradas como "fora de escopo, deliberado" no mesmo pacote ("registro de horário, não vigilância de local"). Investigação confirmou: `hostels` não tem NENHUMA coordenada/endereço hoje (geofencing exigiria campo novo configurado pelo admin, que não existe); `navigator.geolocation` e WebAuthn/biometria não são usados em nenhum lugar do projeto — ambos seriam greenfield. Decisão: construir geolocalização como CAPTURA (não bloqueio) e deixar biometria de fora — razão técnica: WebAuthn amarra credencial biométrica a UM dispositivo+conta de SO, mas o uso típico de ponto em hospedagem é um tablet/computador COMPARTILHADO na recepção, não celular pessoal por funcionário, cenário onde WebAuthn não encaixa sem infraestrutura nenhuma hoje. 6 colunas novas nullable em `staff_attendance` (`clock_in_lat`/`lng`/`accuracy_m` + equivalentes de `clock_out`). `clock_in()`/`clock_out()` (`database.py`) ganharam `lat`/`lng`/`accuracy_m` opcionais, validados por `_clean_geo_coords()` (fora de faixa vira `NULL` silenciosamente, nunca quebra o ponto). `routes/scheduling.py` passou a ler `request.get_json(silent=True)` nas rotas de clock-in/out (antes nunca liam corpo), mantendo compatibilidade total com POST sem corpo (quem nega a permissão do navegador). Frontend: `toggleAttendance()` tenta `navigator.geolocation.getCurrentPosition()` com timeout de 5s antes do POST, best-effort; histórico do funcionário (`openMemberActivityLog`) ganhou link "📍 Ver local" pro Google Maps quando a coordenada existe — zero dependência de mapa nova. 1 chave i18n nova (`attendance.viewLocation`) nos 11 idiomas (1.130→1.131). Testado em banco isolado (ciclo completo com coordenadas, retrocompatibilidade sem coordenadas, valores fora de faixa/não-numéricos ignorados sem quebrar o ponto) e via Flask test client (`POST` com e sem corpo JSON). Verificação end-to-end no navegador real (permitir/negar o prompt) não foi automatizável neste ambiente — recomendado teste manual pós-deploy. Fora de escopo: geofencing/bloqueio, biometria/WebAuthn, geocodificação reversa, edição de ponto já registrado. |
| 1.82.0 | 01/09/2026 | Oficial | Tier white-label pra revenda — pilar 1 de 4: marca própria. Item 27, "maior esforço" desde a criação da fila. Investigação confirmou branding 100% hardcoded, billing rígido (1 preço fixo, 1 pagamento direto pra StayFlow), nenhum conceito de "1 conta gerencia N hospedagens", zero suporte a domínio próprio. Usuário confirmou escopo completo ("pode construir tudo") — decisão: 4 versões independentes (marca → revendedor → preço/margem → domínio), cada uma testável/publicável sozinha. Esta é a base visual, funciona mesmo sem revendedor existir. 4 colunas nullable em `hostels` (`brand_logo_url`/`brand_display_name`/`brand_primary_color`/`brand_favicon_url` — `NULL`=visual padrão StayFlow); NÃO reaproveita `settings.logo_url` (campo morto, nunca renderizado). Nova permission key `branding`, separada de `settings` (que mistura fiscal/timezone/alertas — indevido pra um futuro revendedor que só deveria mexer em marca). `PUT /settings/branding` com validação de cor hex; `build_session_payload()`/`/me` repassam os 4 campos. Frontend: `applyBranding(session)` no `dashboard.html`, chamada no ponto único de hidratação de sessão — troca logo (3 ocorrências de `.brand-logo`), título da aba, `--blue` via CSS custom property (1 cor só, sem motor de tema), favicon. Seção "Marca" em Configurações → Empresa, gated `data-required-permission="branding"` (mesmo padrão do card de Billing). 8 chaves i18n nos 11 idiomas (1.131→1.139). Testado em banco isolado e Flask test client. Próximo: entidade revendedor (v1.83.0). |
| 1.83.0 | 01/09/2026 | Oficial | Tier white-label pra revenda — pilar 2 de 4: entidade revendedor. Nova tabela `resellers` (molde de `referral_partners`, mas separada de propósito — indicação paga % sobre preço padrão, revendedor gerencia N clientes com preço/marca PRÓPRIOS). `owner_user_id` nullable (NULL até alguém reivindicar); 4 colunas de marca em `resellers` como PADRÃO herdado (snapshot na criação, não vínculo vivo) pela hospedagem-cliente nova. Nova coluna `hostels.reseller_id`. Dois caminhos de onboarding, ambos reaproveitando rotas existentes: (1) `POST /register?reseller=CODE` (mirror do `?ref=` de indicação) — dono do cliente se registrando sozinho continua com `Admin` COMPLETO na própria hospedagem, `reseller_id` é só atribuição (achado corrigido durante o dev: versão inicial chamava por engano o rebaixamento de papel nesse caminho, seria bug grave — travaria o dono fora dos próprios chats/reservas — corrigido antes de testar); (2) `POST /account/add-hostel` logado como o PRÓPRIO revendedor — hospedagem vira gerenciada por ele, e a membership dele é REBAIXADA pra papel novo "Revendedor" (`billing,settings,branding,team` — sem `chats`/`reservations`/`operations`). Achado técnico: `update_membership_role` já tinha trava (`check_team_permission_safety`) contra hostel ficar sem ninguém com `team` — hospedagem recém-criada só tem o revendedor como membro, então o papel estreito PRECISA incluir `team` (ele tem que poder convidar o dono/equipe real do cliente depois) ou a própria criação travaria. Multi-propriedade pessoal (v1.70.0) não afetada — só muda quando quem chama `/account/add-hostel` tem `reseller_code` de verdade. Admin: nova aba "🏷️ Revendedores" em Financeiro (criar, listar com `LEFT JOIN` de contagem de clientes, vincular a usuário por e-mail via `claim_reseller_ownership` — protegido contra reatribuição/sequestro). 17 chaves i18n no `ADMIN_I18N` (259→276). Testado em banco isolado e Flask test client ponta a ponta: os dois caminhos de onboarding, proteção contra reatribuição, papel estreito com as permissões certas, multi-propriedade pessoal não afetada, contagem de clientes. Próximo: preço/margem (v1.84.0), depois domínio. |
| 1.84.0 | 01/09/2026 | Oficial | Tier white-label pra revenda — pilar 3 de 4: preço próprio + margem. Nova coluna `billing.custom_price_ars` (nullable) substitui `PLAN_PRICES_ARS[plan_name]` no `POST /billing/subscribe` quando setada. Dinheiro continua 100% na conta MP da StayFlow — margem (cobrado - preço de tabela, pode ser negativa) vira registro contábil em `reseller_margin_ledger`, clone de `subscription_referral_ledger` mas deliberadamente não reaproveitado (conceitos diferentes: indicação = % sobre preço padrão; revendedor = preço próprio). `create_preapproval` ganhou `reason_override` — checkout MP não mostra mais "StayFlow" pra hospedagem white-label. **Achado de segurança real corrigido antes de qualquer teste**: o plano original só previa gate por `@require_permission("billing")`, mas o DONO real de uma hospedagem-cliente (`/register?reseller=CODE`) também tem `billing` via `Admin` completo — sem checagem extra, o próprio cliente poderia ter setado o preço da própria assinatura pra qualquer valor. Corrigido: `PUT /billing/reseller-price` exige que o usuário logado seja o DONO do `reseller_id` daquela hospedagem específica, nunca o cliente final nem um revendedor de outro cliente. UI: bloco "Preço próprio" no card de Billing (só quando `is_reseller_managed=true`); painel "Revendedores" ganhou colunas de cobranças/margem + "Marcar como pago". 5+2 chaves i18n (1.139→1.144 dashboard, 276→278 admin). Testado em banco isolado e Flask test client: cliente bloqueado, hospedagem sem revendedor bloqueada, revendedor de outro cliente bloqueado, revendedor dono funciona, valor inválido rejeitado, margem calculada certa (inclusive negativa) via `mock.patch` no webhook, idempotência confirmada, hospedagem independente nunca gera margem, payout sem duplicar. Próximo: pilar 4 (domínio) — encerra o tier white-label. |
| 1.85.0 | 01/09/2026 | Oficial | Tier white-label pra revenda — pilar 4 de 4: domínio próprio, encerra o item 27. Nova coluna `hostels.custom_domain` (nullable, índice único parcial). Novo `@app.before_request` (`resolve_hostel_by_domain`) resolve `request.host` → `g.domain_hostel_id`, pulando a consulta pros domínios já conhecidos da StayFlow (`stayflowsolutions.com`, `*.onrender.com`) — nunca substitui a resolução de tenant por sessão em rota protegida nenhuma, só alimenta a marca das páginas públicas de entrada. Nova rota pública `GET /public/hostel-branding` (`routes/public_branding.py`, sem autenticação, mesmo espírito minimalista de `/register`) resolve por `?reseller=CODE` (marca padrão do revendedor) ou por domínio (marca da própria hospedagem) — sem nenhum dos dois, devolve `branding: null`, nunca quebra a página. `Login.html`/`Register.html` chamam essa rota no carregamento e aplicam o mesmo conjunto de trocas já usado no `dashboard.html` (logo/título/cor/favicon), sem motor de template novo. Campo de domínio próprio na seção Marca de Configurações, salvo pela mesma `PUT /settings/branding` (rejeita domínio duplicado com erro amigável). Deixado explícito: código resolve qualquer domínio já apontado, mas DNS + cadastro no Render continuam manuais, fora do alcance do código. Testado em banco isolado e Flask test client: resolução por domínio, domínio desconhecido não quebra, domínio duplicado rejeitado, rota pública via header `Host` e via `?reseller=`, domínio da própria StayFlow nunca tenta resolver. **Encerra o tier white-label pra revenda (item 27) em 4 versões independentes** (v1.82.0 marca, v1.83.0 revendedor, v1.84.0 preço/margem, v1.85.0 domínio), cada uma testada/publicada/documentada sozinha, seguindo a decisão de escopo "pode construir tudo" com as 5 fronteiras explícitas acordadas no plano. |
| 1.86.0 | 01/09/2026 | Oficial | Painel do promotor + `account_kind='promoter'` no cadastro — item ad-hoc (27b), surgiu ao vivo: usuário mandou print de alguém perguntando no Instagram como indicar a StayFlow, a pessoa se auto-cadastrou via `ReferralPartner.html` (v1.79.0) durante a conversa (primeiro promotor externo real), e isso expôs um gap: promotor externo tinha `referral_code` mas NENHUM login pra ver os próprios hotéis indicados/comissões — esse dado só existia no `admin.html` do Caio. Investigação rápida confirmou 2 pontos: `account_kind` é validado como lista fechada só em 2 lugares (`register()`/`add_hostel_to_account()`, resto trata como TEXT livre — seguro adicionar `'promoter'`); `get_hostel_referral_stats()` (v1.65.0) já devolve exatamente o dado necessário, zero SQL novo pro core. Decisão de arquitetura: em vez de encaixar "Promotor" dentro do `dashboard.html` (11mil+ linhas, alto risco de vazar UI de reserva/chat por um gate esquecido), nova página standalone `PromoterDashboard.html` (mesmo espírito de `ReferralPartner.html`), com `Login.html::finishLogin()` redirecionando pra ela quando `account_kind==='promoter'`. Conta promotor é uma linha em `hostels` normal (reaproveita sessão/login 100%) mas com papel estreito: `_downgrade_to_promoter_role()` (mesmo molde do revendedor, v1.83.0) troca o "Admin" padrão por um papel só com `promoter`+`security`+`team` (nova permission key `promoter`; `team` incluso porque sem ele `check_team_permission_safety` bloquearia a própria criação do papel numa hospedagem com 1 membro só). Nova `get_promoter_dashboard_data()` estende `get_hostel_referral_stats()` com faixa/comissão atual, próxima faixa a alcançar, e histórico individual dos últimos 50 lançamentos (não só o total). Nova rota `GET /promoter/dashboard`. UI: link copiável, 4 cards de estatística, progresso pra próxima faixa, tabela de hospedagens indicadas + histórico de comissões. `Register.html` ganhou a opção "Promotor / Indicador" no seletor de tipo de conta. Testado em banco isolado e Flask test client ponta a ponta: papel estreito correto, bloqueio de rotas de hospedagem normal (403), painel vazio com formato certo, simulação completa de indicação real (hotel se registra pelo código, pagamento aprovado, comissão e histórico aparecem certos). Sem chaves i18n novas (mesma convenção de texto fixo do `ReferralPartner.html`). |
| 1.87.0 | 01/09/2026 | Oficial | Melhorias no painel do promotor + aba de detalhes no admin — sequência direta da v1.86.0, usuário pediu 6 melhorias de uma vez mais visão do lado do admin (quem pagar, quem já foi pago, quanto, quando, por parceiro). Notificação push best-effort em 3 momentos (nunca quebra o fluxo principal): nova indicação no `/register`, `past_due` no webhook de pagamento reprovado, `canceled` no `/billing/cancel` — nova `notify_referring_promoter_of_status_change()` centraliza os 2 últimos, só dispara quando o parceiro tem `linked_hostel_id` (conta StayFlow de verdade). Deliberadamente sem `notification_type` nas chamadas (ignora filtro de preferência — promotor não tem UI de notificação configurável, e essa é a informação central do relacionamento, não um aviso silenciável). Card "Materiais pra divulgar" (mensagem WhatsApp + legenda pra post, já com o link embutido) e botão "Compartilhar" (`navigator.share()`, só aparece quando o navegador suporta) na `PromoterDashboard.html`. Nova `PUT /promoter/contact` (contact_email/phone da própria linha em `referral_partners`, nunca id arbitrário). Nova `PromoterSignup.html` — cadastro dedicado só pra promotor (nome/e-mail/senha, sem campos de hospedagem), porta de entrada mais direta que o seletor completo do `Register.html`. Admin: refatorado `get_promoter_dashboard_data()` em torno de `_referral_partner_dashboard_payload()` compartilhada, permitindo nova `GET /stayflow-admin/referral-partners/<id>/details` (mesmo dado do painel do promotor, mas sobre QUALQUER parceiro, com ou sem conta) — painel "Ver detalhes" inline no quadro Indicações mostrando hospedagens indicadas + histórico individual. 8 chaves i18n no `ADMIN_I18N` (278→286). Testado em banco isolado e Flask test client: editar contato funciona, notificações não quebram em nenhum cenário (com/sem parceiro vinculado, com/sem conta), webhook de pagamento reprovado seta `past_due` e notifica, cancelamento não quebra (nunca 500) mesmo sem MP configurado, admin vê detalhes de parceiro específico por id (404 pra id inexistente). |
| 1.88.0 | 01/09/2026 | Oficial | Link "Vire promotor" no rodapé da landing — achado ao vivo: usuário tentou criar conta de promotor pra testar e percebeu que `PromoterSignup.html`/`ReferralPartner.html` nunca foram linkadas de lugar nenhum do site público, só compartilhadas manualmente. Link discreto no rodapé do `index.html`, ao lado dos ícones de Instagram/Facebook. 1 chave i18n nova (`footer.becomePromoter`) nos 11 idiomas do `i18n-landing-data.js` (90→91). |
| 1.89.0 | 01/09/2026 | Oficial | Conta de promotor sob login existente + correção do multi-conta — achado ao vivo testando o próprio fluxo: usuário tentou virar promotor com o e-mail da PRÓPRIA conta e caiu num dead-end ("e-mail já cadastrado"). Resposta certa: `users.email` é único de propósito, então a conta de promotor devia virar mais um `hostel_membership` sob o MESMO `user_id` (reaproveitando multi-propriedade, v1.70.0, já usado pra revendedor desde a v1.83.0), não pedir senha nova. `POST /account/add-hostel` ganhou `account_kind='promoter'` (aplicando `_downgrade_to_promoter_role()`, mesma lógica do registro direto). `POST /register` devolve `already_registered: true` no erro de e-mail duplicado — `Register.html`/`PromoterSignup.html` guiam pra "faça login e use + Adicionar hospedagem" em vez de só travar. Bug real corrigido no processo: o clique num item do seletor multi-conta em `Login.html` sempre mandava pra `/app` incondicionalmente (decisão deliberada anterior, documentada no código, pra não colidir com o botão "Meu painel" do admin StayFlow) — mas isso fazia escolher uma conta de promotor cair errado no dashboard normal; corrigido checando `account_kind` nesse clique específico. UI: modal "+ Adicionar hospedagem" ganhou seletor de tipo de conta (Hospedagem/Promotor), label do nome muda dinamicamente. 4 chaves i18n novas (1.146→1.150). Testado em banco isolado e Flask test client: `already_registered=true` no e-mail duplicado, conta de promotor criada sob o mesmo `user_id` via `/account/add-hostel`, as 2 hospedagens aparecem juntas em `get_user_hostels()`, papel "Promotor" correto na nova, hospedagem original do dono não afetada. |
| 1.90.0 | 01/09/2026 | Oficial | Opção Agência (incluindo imobiliária) no "+ Adicionar hospedagem" — pedido direto do usuário, testar o dashboard de agência/imobiliária pra uma oportunidade real. Achado que simplificou tudo: `POST /account/add-hostel` já aceitava `account_kind='agency'` com `agency_category` desde sempre, só o modal do frontend nunca ofereceu essa opção — zero mudança de backend, só UI. Modal ganhou 3ª opção com o mesmo seletor de categoria do `Register.html` (turismo, aluguel de carro/bike/equipamentos, imobiliária, automotivo, comércio, outro). 3 chaves i18n novas (1.150→1.153). Testado em banco isolado: hospedagem-agência criada sob o mesmo `user_id`, aparece no multi-conta, mantém `Admin` completo (diferente do promotor — dono de agência opera o próprio negócio), permissão `portfolio` presente. |
| 1.91.0 | 01/09/2026 | Oficial | Hospedagem/promotor/agência criada pelo admin StayFlow já nasce como conta de teste — achado ao vivo imediatamente depois da v1.90.0: usuário criou a imobiliária de teste mas não conseguiu achá-la em lugar nenhum. Causa raiz: o e-mail do dono da StayFlow está na allowlist admin, então `/login` sempre manda ele direto pro `admin.html` — nunca passa pelo seletor multi-conta comum de `dashboard.html` (o que a v1.89.0/v1.90.0 estenderam). `admin.html` tem seu PRÓPRIO seletor rápido "Propriedades", que só lista hospedagens com `is_own_test_account=1` (flag setada manualmente). As contas novas nasciam como `hostel_membership` de verdade, só que sem essa flag — invisíveis no fluxo que ele realmente usa. Corrigido em `POST /account/add-hostel`: quando quem cria é um e-mail da allowlist StayFlow, a hospedagem nova já nasce com `is_own_test_account=True` automaticamente — cliente real nunca é afetado (só aplica quando o CRIADOR é o próprio admin). Testado em banco isolado: hospedagem/promotor criados pelo admin nascem marcados; hospedagem criada por cliente comum continua sem a flag. Sinalizado mas não confirmado ainda: avatar do usuário no `admin.html` mostrando "?" fixo — pode ser só o instante antes do `fetch("/me")` da inicialização terminar, fica pra confirmar se persiste. |
| 1.92.0 | 01/09/2026 | Oficial | "+ Adicionar propriedade de teste" dentro do próprio admin.html — fecha o loop da v1.91.0. Mesmo com a criação já marcando `is_own_test_account=true` automaticamente, o usuário ainda não conseguia criar a conta de promotor: o botão "+ Adicionar hospedagem" (v1.89.0/v1.90.0) só existe dentro do `dashboard.html`, e o dono da StayFlow nunca passa por lá (login manda direto pro `admin.html`). Corrigido adicionando o mesmo fluxo direto dentro do seletor "Propriedades" que ele já usa — formulário inline (mesmo padrão visual dos formulários de parceiro/revendedor já existentes no arquivo, sem modal genérico) com tipo de conta/categoria de agência/nome, chamando a MESMA `POST /account/add-hostel` de sempre, zero rota nova. Recarrega `loadOverview()`+`renderPropertySelector()` após o sucesso, aparece na lista na hora. 6 chaves i18n novas no `ADMIN_I18N` (286→292) — achado corrigido antes de publicar: `admin.html` tem seu PRÓPRIO dicionário (`ADMIN_I18N`), independente do `i18n-dashboard-data.js` usado por `dashboard.html`, então as chaves `addHostel.kind*` reaproveitadas nos `<option data-i18n>` precisaram ser adicionadas nos dois dicionários separadamente. |
| 1.93.0 | 01/09/2026 | Oficial | Blindagem do `/account/add-hostel` contra 500 em passos pós-criação — usuário tentou criar a conta de promotor pelo fluxo novo (v1.92.0) e recebeu "Não foi possível criar." (mensagem genérica de fallback do frontend, sinal de resposta não-JSON = 500 não tratado). Tentativa de reprodução em banco isolado com cenário próximo do real (admin com 5 hospedagens de teste, criando a 6ª como promotor) não reproduziu o erro, mas revelou um problema real de qualquer forma: os 3 passos que rodam DEPOIS da hospedagem já criada com sucesso (papel de revendedor, papel de promotor, flag de conta de teste) não tinham proteção nenhuma — qualquer exceção inesperada em qualquer um derrubava a requisição INTEIRA com 500, mesmo com o registro já salvo no banco. Corrigido envolvendo os 3 em `try/except` (loga o erro real, devolve sucesso do mesmo jeito) — mesmo espírito já usado pra notificação push em outras rotas (passo secundário nunca derruba o fluxo principal). Causa raiz ainda não confirmada — fica pros logs do Render se acontecer de novo. |
| 1.94.0 | 01/09/2026 | Oficial | Menu do promotor: só o que faz sentido + Portfólio de vendas — pedido direto do usuário após conseguir enfim acessar uma conta de promotor de verdade (v1.91.0-v1.93.0): o menu lateral completo aparecia inteiro, sem filtro (a v1.86.0 tinha optado por página standalone `PromoterDashboard.html` exatamente pra evitar isso, mas correções de navegação subsequentes foram reforçando o caminho de volta pro `dashboard.html` completo). Decisão: em vez de continuar com página separada, fazer `dashboard.html` reconhecer `account_kind='promoter'` de verdade. Achado que simplificou tudo: `PROMOTER_PERMISSIONS` já era estreita, e `hideNavItemsWithoutPermission()` usa `data-required-permission || data-page` como chave implícita — Opportunities/Hóspedes/Finance/Reports já ficavam escondidos de graça, só faltou acrescentar `dashboard`/`chats`/`settings` (liberando essas 3 telas) e criar `data-hide-for-account-kind` (inverso do já existente `data-required-account-kind`) pro caso de "Equipe" (`team` precisa continuar NA permissão, senão `check_team_permission_safety` bloqueia a criação do papel, mas o item não deve aparecer no menu). Página "Dashboard" ganhou um segundo grid interno (`#promoterHomeGrid`) com o conteúdo que já existia em `PromoterDashboard.html` (link de indicação, faixa de comissão, hospedagens indicadas), alternado por `applyPromoterHome()`. Nova página "Portfólio de Vendas" (nav gated `data-required-permission="promoter"`) com slides fixos em 3 abas (Hospedagens/Agências/Locadoras) cobrindo problema→solução→recursos→planos. Ask StayFlow ganhou `PROMOTER_SYSTEM_PROMPT` separado (só ativa quando `account_kind==='promoter'`), injetando o status real do programa de indicação como contexto — ferramentas normais já ficam vazias sozinhas por filtro de permissão. Redirecionamentos simplificados: os 3 pontos que mandavam pra `PromoterDashboard.html` voltaram a mandar pro `/app` normal — a página fica órfã, não removida. 1 chave i18n nova (1.153→1.154). Testado em banco isolado: permissões corretas, `/settings` e `/chats` acessíveis, prompt do promotor monta sem erro. Fora de escopo: comportamento da IA de atendimento automático se um prospect mandar mensagem pro WhatsApp do promotor — sem tratamento especial ainda, fica pra quando virar demanda real. |
| 1.95.0 | 01/09/2026 | Oficial | Promotor deixa de ser tratado como hospedagem em Opportunity Center/Hóspedes/Financeiro/Relatórios/Configurações + nova aba "Indicações" — sequência direta da v1.94.0, usuário testou ao vivo (via "visitar painel" do admin) e reportou 6 pontos onde a conta ainda era tratada como se operasse uma hospedagem de verdade. Achado que explica por que o admin via a tela errada mesmo com `PROMOTER_PERMISSIONS` já estreita: `build_session_payload()` concede `permissions=ALL_PERMISSIONS` toda vez que a sessão está "em visita" (`impersonating_from_hostel_id` setado, ver `routes/stayflow_admin.py::/impersonate`) — intencional pra suporte (admin precisa poder ver/mexer em qualquer tela ao investigar um problema), mas isso reabria pro admin qualquer item de nav sem `data-required-account-kind`/`data-hide-for-account-kind` explícito, mesmo com o `account_kind` real da hospedagem visitada (esse sim correto no payload, sempre) sendo `'promoter'`. Correção: em vez de mexer na regra de impersonation, os botões de nav Opportunity Center/Hóspedes/Financeiro/Relatórios ganharam `data-hide-for-account-kind="promoter"` (mesmo mecanismo já usado em "Equipe" desde a v1.94.0) — esconde por `account_kind`, não por permissão, funcionando tanto na sessão real do promotor quanto na visita do admin. Configurações: abas Geral/Empresa/IA/Integrações/Billing e o atalho pra "Equipe" ganharam o mesmo atributo (todo o conteúdo dessas abas já dependia de dado de hospedagem/agência — razão social, CUIT, fuso horário, check-in/check-out, IA de atendimento, Beds24, Mercado Pago, webhook de saída — nada disso existe pra quem não opera hospedagem/agência); aba padrão ao entrar em Configurações passou a ser "Comunicação" pra essa conta (`switchSettingsSection` exposta em `window`, chamada condicionalmente na hidratação de sessão), já que "Geral" (padrão de fábrica) ficou escondida. Nova aba de nav "Indicações" (`#referrals`, gated `data-required-permission="promoter"`): o link de indicação + faixa de comissão + hospedagens indicadas saiu de dentro do Dashboard — onde vivia como uma caixinha simples de input+botão, criticada como "muito feia"/"analógica" — e virou página própria com hero card, barra de progresso visual até a próxima faixa de comissão (hint "faltam N indicações pra chegar a X%", usando `next_tier` já devolvido por `/promoter/dashboard`, sem SQL novo) e cards de hospedagem indicada com `status-pill` colorido conforme `billing_status` (ok/ai/hot). Dashboard do promotor ficou só com os 4 KPIs + atalhos pra Indicações/Chats/Portfólio de Vendas. 2 chaves i18n novas (1.154→1.156). Testado: balanceamento de chaves/parênteses/colchetes do `dashboard.html` após cada edição, contagem de `<section>`/`<div>` confirmando que o delta pré-existente de 1 tag (já presente no HEAD antes desta sessão, não introduzido agora) permaneceu igual, paridade de chaves i18n confirmada nos 11 idiomas via `tools/check_i18n_parity.py`. |
| 1.96.0 | 01/09/2026 | Oficial | Lapidação final do painel do promotor — 9 pedidos numa lista só, testados ao vivo pelo usuário logo após a v1.95.0. **Bug real corrigido primeiro**: card "Marca (White-label)" e card principal de Billing, ambos gated só por `data-required-permission`, reapareciam pro admin em visita (mesma causa raiz documentada na v1.95.0 — impersonation concede `ALL_PERMISSIONS` de propósito) — corrigido acrescentando `data-hide-for-account-kind="promoter"` nos dois, e generalizado pro modal de Notificações (`openNotificationsModal()` passou a chamar `applyHideForAccountKind()` além de `applyPermissionVisibility()`, já que conteúdo injetado via `openGenericModal()` não é coberto pela hidratação inicial da página). **Dashboard**: os 3 botões de atalho (Ver link/Chats/Portfólio) saíram, entrou gráfico "Seu desempenho" — barra em Canvas nativo (mesmo estilo do `renderChatActivityChart` de Relatórios, sem lib externa) com a comissão gerada por mês, últimos 6 meses, lendo o campo `history` que `/promoter/dashboard` já devolvia (últimos 50 lançamentos do `subscription_referral_ledger`) sem uso nenhum no frontend até agora. **Nova aba "Carteira"** (`#wallet`): a receber/já recebido, relatório mensal (agrupamento client-side do `history` por mês) e extrato linha a linha (hospedagem, valor, comissão, status, datas) — mesmo dado do gráfico, sem rota nova. **Botão flutuante "+"** (`reserva-floating`, nova reserva) ganhou `data-hide-for-account-kind="promoter"` — não fazia sentido pra quem não tem hospedagem. **Ask StayFlow** voltou ao tratamento visual do `index.html`: trocou o `<span>` com máscara CSS (silhueta escura numa bolha azul solida) por `<img>` direto de `logo2.png` sem fundo, só um drop-shadow leve — reposicionamento na aba Chats (`body.chats-page-active`) já existia e não precisou de nada novo; boas-vindas/sugestões do painel ganharam variante pro promotor (`data-hide-for-account-kind`/`data-required-permission` nos botões existentes, textos de boas-vindas trocados via JS). **Configurações > Segurança**: "Trocar senha" deixou de ser formulário fixo na tela e virou card-resumo → modal (`openChangePasswordModal()`, mesmo padrão já usado em WhatsApp/Facebook/Instagram/etc — os ids dos inputs não mudaram, `submitChangePassword()` não precisou de nenhuma alteração). **Onboarding**: tour inicial (`dashboardIntroSlides()`) e dicas de primeiro-acesso por página (`FEATURE_COACH_MARKS`) ganharam ramificação própria pra `account_kind==='promoter'` (novo `FEATURE_COACH_MARKS_PROMOTER`) — antes usavam texto de hospedagem mesmo pra essa conta. **Portfólio de Vendas reconstruído**: de 3 setores com texto corrido virou 4 setores (novo "Imobiliárias", cobrindo sincronização com Tokko Broker + matching por IA) × 5 slides cada (problema → solução → recursos → como apresentar → planos), cada slide com ícone SVG inline colorido por tipo (sem imagem externa, nenhum asset de foto real disponível) e um botão "Perguntar ao Ask StayFlow sobre isso" que abre o painel e manda o próprio conteúdo do slide como contexto da pergunta — mais simples e confiável que ensinar o backend a saber em qual slide a pessoa estava; `PROMOTER_SYSTEM_PROMPT` (v1.94.0) já era genérico o bastante pra responder bem, não precisou de mudança nenhuma no backend. Slide "como apresentar" é novo em todos os 4 setores (antes só tinha problema/solução/recursos/planos) — dá ao promotor uma dica concreta de abertura de conversa por setor, não só marketing. **i18n**: 43 chaves novas (nav/topbar/promoterHome/referrals/wallet/salesPortfolio/ask) em 11 idiomas (1.156→1.199), cobrindo todo o texto estrutural (rótulos, cabeçalhos, botões, colunas de tabela, mensagens de UI) do que foi construído nesta rodada e na v1.95.0 que tinha ficado hardcoded em português — usuário reportou em duas mensagens separadas ("a introdução... estão pra hotéis" e "não traduz direito... conteúdo continua em português") que motivaram essa revisão. **Fora de escopo, decisão deliberada**: o conteúdo longo do Portfólio de Vendas (corpo/bullets de cada slide, ~20 blocos de texto) e os parágrafos do tour inicial ficam só em português — mesmo precedente já aceito na v1.94.0 ("mesma convenção de texto fixo do ReferralPartner.html"), traduzir prosa extensa de vendas pra 11 idiomas com qualidade é uma ordem de grandeza de esforço diferente de rótulo de UI; sinalizado ao usuário, não fica escondido. Nenhuma mudança de backend/banco nesta versão — testado via balanceamento de chaves/parênteses/colchetes do `dashboard.html` a cada edição e `tools/check_i18n_parity.py`. |
| 1.97.0 | 01/09/2026 | Oficial | Tradução completa do conteúdo do Portfólio de Vendas e do onboarding — usuário rejeitou explicitamente a decisão de escopo da v1.96.0 ("quero que esteja tudo traduzido, tem que funcionar direito isso"). Revertida a decisão anterior: os ~20 blocos de texto do Portfólio de Vendas (título/corpo/bullets de cada um dos 5 slides × 4 setores) e os parágrafos do tour inicial do Dashboard passaram de texto fixo em português pra chaves de verdade, resolvidas via `T(chave, fallbackPT)` no momento da renderização. Arquitetura: em vez de acrescentar um campo `key` a cada slide, a chave é montada na hora (`"salesPortfolio." + setor + "." + slide.kind`, ex.: `salesPortfolio.realestate.pitch.body`) já que setor+kind já formam um caminho único por slide — `portfolioSlideText()` centraliza essa resolução (título, corpo, bullets) e é usada tanto por `renderPortfolioSlide()` quanto por `askAboutPortfolioSlide()` (a pergunta mandada pro Ask StayFlow agora usa o texto JÁ traduzido, não o fallback em português, incluindo o próprio template da pergunta, também traduzido). `dashboardIntroSlides()` ganhou `titleKey`/`bodyKey` em cada slide das 3 variantes (padrão/agência compartilhando a maioria, promotor totalmente à parte); o slide "Opportunity Center" reaproveita a chave `nav.opportunities` já existente pro título, sem duplicar tradução. `FEATURE_COACH_MARKS`/`FEATURE_COACH_MARKS_PROMOTER` também pararam de guardar texto fixo: título de cada dica agora reaproveita a mesma chave `nav.*` já usada no menu lateral (zero chaves novas só pra isso), e só o texto explicativo ganhou chave própria (`onboarding.coach.<página>.text`, com namespace separado `onboarding.coach.promoter.*` pras 2 páginas que colidem de nome com a versão genérica — chats/settings). Chrome dos modais de onboarding (botões Voltar/Próximo/Explorar o menu, checkbox "Não mostrar novamente"/"Não mostrar mais dicas", botão "Entendi", título "Introdução") também traduzido. 104 chaves novas em 11 idiomas (1.199→1.303): 57 do Portfólio de Vendas (4 setores × ~14 unidades cada), 47 de onboarding+coach marks+template de pergunta do Ask StayFlow. Testado: `tools/check_i18n_parity.py` confirmando as mesmas 1303 chaves em todos os 11 idiomas; balanceamento de chaves/parênteses/colchetes do `dashboard.html` após cada edição; script de auditoria (grep de todo `T(...)` usado no arquivo comparado contra o dicionário) confirmando que nenhuma chave nova desta ou da v1.96.0 ficou sem entrada — sobrou uma lista de ~70 chaves faltando, mas TODAS pré-existentes e de módulos nunca tocados nesta sessão (cozinha, manutenção, estacionamento, segurança patrimonial, portfólio de agência, integrações Mercado Pago/Nuvemshop/WhatsApp) — sinalizado ao usuário como gap real do sistema, porém fora do escopo do painel do promotor, não escondido nem resolvido silenciosamente aqui. Nenhuma mudança de backend/banco. |
| 1.98.0 | 01/09/2026 | Oficial | Bug real de vazamento entre contas + dados de recebimento do promotor + dados completos do cliente — 4 achados ao vivo numa sessão só de teste do usuário. **Bug de vazamento corrigido**: as abas "Indicações"/"Carteira"/"Portfólio de Vendas" (e as 3 sugestões correspondentes do Ask StayFlow) apareciam pra uma hospedagem NORMAL ("Swing", lodging comum) enquanto o admin a visitava — mesma causa raiz já documentada duas vezes nesta sessão (v1.95.0, v1.96.0): gated só por `data-required-permission="promoter"`, e impersonation sempre concede `ALL_PERMISSIONS`. Corrigido acrescentando `data-required-account-kind="promoter"` nos 6 elementos (3 nav + 3 ask-suggestion) — `account_kind`, ao contrário de permissão, nunca é inflado durante visita. Registrada memória de feedback nova (`feedback_permission_vs_accountkind_isolation`) formalizando a regra geral: nunca gatear UI exclusiva de account_kind só por permissão, sempre parear com `data-required-account-kind`/`data-hide-for-account-kind`. **Botão Ask StayFlow, correção de escopo em cima de correção**: a mudança visual da v1.96.0 (sem círculo, logo de 160px igual ao `index.html`) tinha sido aplicada GLOBALMENTE por engano — usuário esclareceu que era só pro promotor, resto devia continuar com o círculo azul original. Revertido o padrão (`​.ask-floating` volta a ser o círculo com `<span class="brand-logo-mask">`) e isolada a variante nova atrás de `data-account-kind="promoter"` no próprio botão (setado via JS na hidratação de sessão) + `data-required-account-kind`/`data-hide-for-account-kind` nos dois elementos internos (span vs img) — mesmo mecanismo genérico de sempre, sem CSS solto sem escopo. **Dados de recebimento do promotor** (`referral_partners.payout_method`/`payout_details`, novo `PUT /promoter/payout-info`): card "💳 Como você quer receber" na Carteira (Mercado Pago/PIX/transferência bancária + campo livre de detalhes), visível também pro admin no painel "Ver detalhes" de `admin.html` — sem processador de payout automático nenhum, só o dado estruturado que faltava pro admin saber pra onde mandar o repasse manual. **Dados completos do cliente**: `admin-hostel.html` só mostrava e-mail da hospedagem, nada da pessoa de verdade — corrigido com `get_hostel_owner_and_address()` (nome/e-mail do primeiro `hostel_membership`, endereço já existente em `settings.address` desde sempre mas nunca surfaceado pro admin) + telefone (`hostels.phone`, coluna que já existia mas nunca era preenchida). Telefone virou campo obrigatório no cadastro público (`Register.html` e `PromoterSignup.html`, ambos os únicos 2 pontos de entrada de `/register`) — endereço deliberadamente NÃO virou campo novo de cadastro (já existe opcional em Configurações > Empresa, reaproveitado em vez de duplicado). Testado em banco isolado com Flask test client: registro sem telefone rejeitado (400), registro com telefone grava `hostels.phone` e é lido corretamente por `get_hostel_owner_and_address()`, `PUT /promoter/payout-info` aceita método válido e rejeita inválido (400), `GET /promoter/dashboard` devolve os campos novos. |
| 1.99.0 | 01/09/2026 | Oficial | **Bug crítico corrigido**: sessão de admin ficava "presa" ao trocar de propriedade durante uma visita — usuário travou ao vivo (impersonando "Swing", trocou pra "Imobiliária Teste" pelo seletor normal do topo e não conseguiu mais voltar pro próprio painel; painel interno chegou a mostrar "Não foi possível carregar o painel"). Causa raiz: `POST /select-hostel` (usado pelo seletor de propriedades, que durante impersonation sempre lista as hospedagens do PRÓPRIO admin — `get_user_hostels(user_id)`, `user_id` nunca muda em visita) atualizava `sessions.hostel_id` via `update_session_hostel()` mas nunca tocava a coluna separada `sessions.impersonating_from_hostel_id` — a resposta daquela chamada específica parecia normal (`build_session_payload()` sem o flag = `impersonating:false`), mas o banco continuava com o "endereço de volta" antigo gravado; o próximo `GET /me` (que LÊ esse flag do banco, diferente de `/select-hostel`) reabria a visita com o destino errado, deixando a pessoa girando em círculo sem conseguir sair de vez. Corrigido com uma linha: `/select-hostel` agora chama `set_session_impersonation(session_id, None)` antes de trocar de hostel — usar o seletor normal das PRÓPRIAS propriedades durante uma visita só pode significar "quero encerrar a visita e ir pra uma conta minha", nunca faz sentido permanecer "em visita" depois disso. Bug pré-existente, não introduzido nesta sessão (mecanismo de impersonation é da v1.47.0) — só apareceu porque ninguém tinha testado essa combinação específica (trocar de propriedade PRÓPRIA no meio de uma visita a cliente) até agora. Testado em banco isolado com Flask test client, reproduzindo o cenário exato (2 hospedagens próprias do admin + 1 cliente real, visita → troca → `/me` subsequente): antes do fix o `/me` reabria `impersonating:true` com destino errado; depois do fix permanece `impersonating:false` de forma estável em trocas sucessivas. Publicado com urgência — usuário estava ativamente travado em produção no momento do achado; orientado a fazer logout/login pra limpar a sessão já corrompida (o fix por si só não retroage sobre uma sessão já gravada com o flag preso). |

| 1.100.0 | 02/09/2026 | Oficial | Auditoria de 7 achados no produto do lado imobiliária — corrigidos numa leva só antes de seguir pra apresentação com indicadora do setor (Julia de Luna, Bauru-SP). **Ícone errado**: `admin.html` mostrava ✈️ (ícone de agência de turismo) pra QUALQUER `account_kind='agency'`, incluindo imobiliária — corrigido com `kindIcon(h, agencyCategory)`, nova função que checa `agency_category==='imobiliaria'` antes de cair no `KIND_ICONS` genérico (🏠 pra imobiliária), aplicada nos 7 pontos do admin que renderizavam esse ícone (quick-switcher, tabela de propriedades, ranking, alertas, transações, threads de suporte — todos alimentados pela mesma `get_stayflow_admin_overview()`, estendida com `h.agency_category` uma vez só). **Locale hardcoded do Tokko Broker**: `tokko_service.list_properties()`/`sync_tokko_properties()` sempre pediam `lang=es_ar` pra API do Tokko, mesmo pra imobiliária brasileira — parametrizado com default `pt_br`, espanhol continua disponível pra quem precisar (Argentina). **"Hóspede" hardcoded**: rótulo de coluna do Opportunity Center, label do modal de cobrança e empty-state de Hóspedes mostravam "Hóspede" mesmo pra imobiliária (que trata "cliente", não hóspede) — resolvido reaproveitando `agencyGuestNoun()` (já existia, decidia PAX/Clientes por categoria) através de nova função central `applyAgencyGuestNounLabels(session)`, chamada nos 2 pontos de hidratação (inicial + troca de idioma, já que `applyTranslations()` sobrescreve `data-i18n` na troca). **Copy de "Meu Portfólio" genérica demais**: subtítulo e empty-state falavam de "produtos e serviços" sem nada específico de imóvel — nova `applyImobiliariaPortfolioCopy(session)` troca por copy própria quando `agency_category==='imobiliaria'` (3 chaves i18n). **Sem campos de imóvel no cadastro manual**: `real_estate_details` (operação/localização/quartos/banheiros/m²) existia desde a v1.72.0 mas só era preenchida pelo sync automático do Tokko — o formulário manual "Novo item" nunca escrevia nela, e `list_portfolio_items()`/`get_portfolio_item()` nem faziam o JOIN pra devolver os campos mesmo quando existiam. Corrigido nos dois lados: backend com `_save_real_estate_fields()` (grava só quando pelo menos 1 dos 5 campos vem na requisição, pra não criar linha vazia em item que não é imóvel) chamado em `POST`/`PATCH /portfolio/items`, e os dois SELECTs de leitura ganharam `LEFT JOIN real_estate_details`; frontend com os 5 campos aparecendo condicionalmente dentro do MESMO modal já existente de "Novo item" (`portfolioRealEstateFieldsHtml()`, honrando a regra de formulário sempre em modal) e um resumo compacto nos cards da lista (`portfolioRealEstateSummaryHtml()`, ex: "🏠 Aluguel · 2 quartos · 1 banheiro · 65m² · Bairro X"). **Botão "Oferecer imóvel" abria cobrança do Mercado Pago**: fluxo herdado do "Oferecer item" genérico de outras agências, mas pra imóvel não faz sentido gerar link de pagamento — trocado por `openOfferPropertyModal()`/`submitOfferProperty()`, que manda uma mensagem editável (com sugestão pré-preenchida via `T()`) direto pro cliente reaproveitando o `POST /guests/<id>/send-message` já existente (usado pelo chat manual), zero rota nova no backend. 20 chaves i18n novas em 11 idiomas (1.303→1.335): `guests.emptyTitleAgency`/`emptyDescAgency` (2), `portfolio.subtitleImobiliaria`/`emptyTitleImobiliaria`/`emptyDescImobiliaria` (3), `portfolio.realEstate.*` (12), `portfolio.offerProperty.*` (8, com sobreposição descontada) — mais 3 chaves novas no `ADMIN_I18N` (292→295, seção de payout do parceiro de indicação, complementando a v1.98.0). Testado em banco SQLite isolado com Flask test client: criação de item de imóvel grava e devolve os 5 campos; PATCH sem campos de imóvel não apaga os já existentes (só sobrescreve quando o campo vem de novo); item sem nenhum campo de imóvel continua com tudo `NULL`, sem erro; `sync_tokko_properties()` mockado confirma `lang=pt_br` sendo enviado e os campos de imóvel do Tokko chegando certos no portfolio. Balanceamento de chaves/parênteses/colchetes de `dashboard.html`/`admin.html`/`stayflow-live.js` e `ast.parse()` dos 5 arquivos Python tocados, sem regressão. |

| 1.101.0 | 02/09/2026 | Oficial | Refinamento profundo do produto imobiliária (7 itens pedidos pelo usuário) + bug crítico universal corrigido de quebra. **Bug universal corrigido**: a aba "Suporte" (falar direto com a StayFlow — feedback/reclamação/pedido de ajuda) estava invisível em TODOS os menus, de TODAS as contas, sempre — achado ao vivo pelo usuário. Causa raiz: `hideNavItemsWithoutPermission()` usa `data-page` como chave de permissão implícita quando não há `data-required-permission`, e `"support"` nunca existiu em `ALL_PERMISSIONS` (`utils/permissions.py`) — `hasAnyPermission("support", permissions)` sempre devolvia `false` pra qualquer conta/cargo. Corrigido excluindo essa página do check de permissão (é um canal de contato, não uma área de dado sensível). **Galeria de fotos**: `portfolio_photos` já aceitava N fotos por item desde sempre (token é a PK, não item_id), mas a rota de upload sempre sobrescrevia a capa a cada envio novo e não existia consulta que listasse todas — novo `GET/DELETE /portfolio/items/<id>/photos[/<token>]`, upload só define capa automaticamente na 1ª foto, exclusão promove a próxima foto restante a capa (ou limpa se não sobrar nenhuma). **Preço por tipo de operação**: aluguel ganha sufixo "/mês" no card (`formatRealEstatePrice()`), venda continua só o valor. **Código de referência**: campo livre opcional (`reference_code`), toda imobiliária de verdade cataloga por código curto, não pelo nome do imóvel. **Amenidades + custos recorrentes**: checklist fechado de 8 chaves (`REAL_ESTATE_AMENITIES` — garagem/mobiliado/aceita_pet/piscina/elevador/churrasqueira/ar_condicionado/area_servico, filtrado contra chave inventada na gravação) + `condo_fee`/`iptu_fee` numéricos, exibidos lado a lado do preço nos cards. **Área útil vs. total**: `surface_m2` (já existente) agora significa especificamente "área total", nova `useful_area_m2` complementa. **Filtros estruturados no matching**: guard-rail em cima da sugestão semântica da IA (`decision_engine.py`) — o modelo agora também extrai `property_filters` (operação/quartos mínimos/preço máximo) EXPLICITAMENTE dito pelo cliente na conversa, e uma nova `_property_violates_filters()` invalida a sugestão se ela violar algum desses filtros (evita "quase acerto" semântico, ex: sugerir imóvel de 2 quartos quando o cliente pediu "pelo menos 3"). **Sync automático do Tokko**: item de escopo original era "webhook do Tokko", mas a API pública deles nunca foi testada contra uma resposta real (mesma pendência honesta já registrada no arquivo) — implementar um receptor de payload especulativo tinha risco real de nunca bater com o formato de verdade. Trocado por resync periódico a cada 6h (`_tokko_resync_loop` em `app.py`, mesmo padrão dos outros 3 loops em background já existentes), reaproveitando o caminho já testado (`resync_all_tokko_properties()`). **Achado crítico durante os testes, corrigido antes de publicar**: `upsert_real_estate_details()` sempre sobrescrevia TODOS os campos que recebia, incluindo com `None` quando um campo simplesmente não era passado — um resync automático do Tokko (que nunca conhece amenidades/código/condomínio) apagaria esse enriquecimento manual a cada rodada, e uma edição manual parcial apagaria o que o Tokko tinha preenchido. Corrigido tornando a função um upsert parcial de verdade: os 10 campos usam sentinela `_UNSET` como default, só grava/atualiza a coluna quando o chamador realmente passa o argumento — `_save_real_estate_fields()` (`routes/portfolio.py`) espelha o mesmo cuidado nos 2 lados. **Segundo achado nos testes**: o mapeamento do Tokko guardava o rótulo de operação como texto livre no idioma da API ("Venta"/"Alquiler" em espanhol) sem normalizar pro enum fixo (`rent`/`sale`) usado no formulário manual, na formatação de preço e no guard-rail novo — corrigido com `_normalize_operation_type()`, tolerante a variantes em espanhol/português, preserva o texto original se não reconhecer. 20 chaves i18n novas em 11 idiomas (1.335→1.355) + valor de `portfolio.realEstate.surfaceLabel` atualizado em todos pra refletir "área total". Testado em banco SQLite isolado com Flask test client: item com os 10 campos novos grava e devolve tudo certo (amenidade inválida filtrada); PATCH parcial (só descrição, ou só um campo novo) não apaga nenhum campo de imóvel já existente, nos dois sentidos; item sem nenhum campo de imóvel continua limpo; galeria — 1ª foto vira capa automática, 2ª não sobrescreve, exclusão da capa promove a próxima, exclusão da última limpa pra `None`; resync automático do Tokko (mockado) atualiza os 5 campos que ele realmente manda sem apagar os 5 que só o cadastro manual conhece; `get_hostels_with_tokko_configured()` retorna certo; guard-rail de matching testado isoladamente (função pura, sem chamada de IA) nos 4 cenários de violação + 2 de não-violação. |

| 1.102.0 | 02/09/2026 | Oficial | Agência/imobiliária tratada como hospedagem em quase toda a "camada de instrução" do produto — usuário percebeu ao vivo que Ask StayFlow, resumo executivo, onboarding e Opportunity Center continuavam falando de "hóspede"/"reserva"/"check-in" pra quem administra uma agência, apesar do Portfólio já ser 100% ciente de `agency_category` desde a v1.100.0/v1.101.0. Auditoria completa (agente de exploração dedicado) mapeou 7 áreas afetadas, todas corrigidas nesta versão. **Ask StayFlow (o maior gap)**: o prompt de sistema (`services/ask_agent_service.py::SYSTEM_PROMPT`) é escrito 100% pensando em hospedagem ("funcionário/gestor do hostel", "reservas, hóspedes... estoque") e era usado sem nenhuma diferença pra `account_kind='agency'` — novo `AGENCY_SYSTEM_PROMPT`, category-aware via `AGENCY_CATEGORY_BUSINESS_CONTEXT_PT` (nova constante em `database.py`, compartilhada com o resumo executivo) e `agency_guest_noun()` (mesma lógica de `PAX_STYLE_CATEGORIES`/`agencyGuestNoun()` do frontend, agora também no backend). Achado extra ao construir o fix: o dono de uma agência recebe permissão total por padrão, então o Ask StayFlow oferecia ferramentas de reserva/cozinha/manutenção/segurança patrimonial pra quem administra uma imobiliária — `allowed_tools` agora filtra também por `LODGING_ONLY_PERMISSIONS` quando `account_kind='agency'`, então a lista de ferramentas realmente some, não só o prompt muda de tom. **Resumo executivo** (`routes/executive.py`): `business_label` era binário lodging/"agência parceira (turismo/locação)" — corrigido pra usar `AGENCY_CATEGORY_BUSINESS_CONTEXT_PT` (mesma constante do Ask StayFlow), e o fallback usado quando a chamada à IA falha (`FALLBACK_SUMMARIES`) ganhou uma variante `FALLBACK_SUMMARIES_AGENCY` (5 idiomas, mesmo escopo do original) trocando "hóspedes"/"reserva" por "clientes"/"negócio". **Ask StayFlow, textos fixos da UI**: subtítulo e mensagem de boas-vindas do painel (`ask.subtitle`/`ask.welcomeMsg`) só tinham override pra promotor (`data-i18n` sendo reescrito por `applyTranslations()` a cada troca de idioma) — centralizado em `applyAskStayFlowAccountKindText()`, chamada nos 2 pontos de hidratação de sempre, estendida pra agência com o nome do negócio e o substantivo certo (PAX/Clientes) interpolados. **Coach marks** (dicas de primeiro acesso por página): `FEATURE_COACH_MARKS` genérico ("hóspede", "passeio", "hospedagens parceiras oferecerem") era usado igual pra imobiliária — nova `FEATURE_COACH_MARKS_IMOBILIARIA` cobrindo as 5 páginas que essa conta realmente vê (chats/opportunities/portfolio/guests/settings), mesmo padrão/namespace de `FEATURE_COACH_MARKS_PROMOTER`. **Home do Dashboard**: card "Operação" (conceito de check-in/check-out) escondido pra não-lodging via `data-required-account-kind="lodging"` (mesmo padrão já usado em Ocupação/Reservas); 4 textos fixos ("Reservas quase fechadas", empty-states de Atividades/Ações prioritárias/Resumo Executivo) ganharam variante de agência via nova `applyAgencyHomeCopy(session)`. **Opportunity Center**: o enum cru de `intent` (`booking`/`tour`/`upsell`/...) vazava sem tradução na tela ("Intenção: booking") — nova `intentLabel()` em `chats-live.js`, com `booking` virando "Negociação" pra agência (pra hospedagem continua "Reserva", sentido bem diferente); empty-state da tabela também ganhou variante de agência. **Fixes rápidos**: fallback de nome do hóspede/lead ("Hóspede" → "Cliente"/"PAX" via `guestFallbackName()`), botão flutuante "+" de nova reserva vazava pra agência (só tinha `data-hide-for-account-kind="promoter"`, faltava `data-required-account-kind="lodging"` — ficava fora do menu mas acessível pelo atalho), campo "Nome" do formulário de Configurações > Geral reaproveitando o rótulo "Nome do negócio" que a criação de conta já usava (a variável `isAgency` já existia ali, só não era usada nesse ponto). Bônus de consistência: `/permissions/catalog` (catálogo de cargos em Equipe) trocava "Hóspedes" por "PAX" pra QUALQUER agência — agora usa `agency_guest_noun()`, então imobiliária/automotivo/comércio corretamente veem "Clientes". 24 chaves i18n novas em 11 idiomas (1.355→1.379). Testado em banco SQLite isolado com Flask test client, IA mockada (sem custo/rede real): `agency_guest_noun()`/`AGENCY_CATEGORY_BUSINESS_CONTEXT_PT` corretos; `/permissions/catalog` devolve "Clientes" pra imobiliária e "PAX" pra turismo; `/executive-summary` manda o `business_label` certo no prompt pra IA (confirmado capturando a chamada mockada) e cai no fallback certo por `account_kind` quando a IA falha; Ask StayFlow — prompt de sistema mockado confirma texto "imobiliária"/"AGÊNCIA" presente, e a lista de tools enviada à API exclui `create_reservation`/`create_kitchen_order` pra agência (sem regressão: hospedagem continua com o catálogo completo de ferramentas). |

| 1.103.0 | 02/09/2026 | Oficial | Fechamento dos 2 achados que sobraram da auditoria de agência da v1.102.0. **"Importar dados" (card + modal de Configurações)**: card-resumo dizia "Já tem quartos e hóspedes numa planilha?" pra qualquer conta — o modal por trás já era bem estruturado por `account_kind` (seções de Quartos/Reservas escondidas pra agência, seção de Portfólio só pra agência, achado ao investigar antes de mexer), só faltava (a) o texto do card-resumo e (b) o título/rótulos da seção "Hóspedes" dentro do modal reconhecerem PAX/Clientes — resolvido com `agencyGuestNoun()` interpolado no card (nova `applyAgencyHomeCopy` estendida) e dentro de `openImportDataModal()`/`submitImportRows()` (título da seção, texto do botão, contagem final "N cliente(s)/PAX importado(s)"). **Coach marks das demais categorias de agência** (turismo, aluguel de carro/bike/equipamentos, automotivo, comércio): a v1.102.0 só tinha corrigido as dicas de primeiro acesso pra imobiliária (`FEATURE_COACH_MARKS_IMOBILIARIA`) — as outras categorias continuavam vendo o texto genérico de hospedagem ("hóspede", "hospedagem"). Diferente da imobiliária, o CONTEÚDO das dicas genéricas já fazia sentido pra essas categorias (Portfólio realmente é "o que você vende pras hospedagens parceiras oferecerem" pra turismo/locação, Opportunity Center realmente detecta "passeio, aluguel") — só a palavra precisava trocar, não a dica inteira. Nova `FEATURE_COACH_MARKS_AGENCY` com placeholders `{noun}`/`{nounSingular}` resolvidos dinamicamente em `showFeatureCoachMark()` via `agencyGuestNoun()` (um dict só cobre turismo com "PAX" e automotivo/comércio com "Clientes" ao mesmo tempo, sem duplicar por categoria). Ordem de precedência final na seleção do coach mark: promotor → imobiliária → agência genérica → hospedagem (fallback). 8 chaves i18n novas em 11 idiomas (1.379→1.387). Testado: balanceamento de chaves/parênteses/colchetes de `dashboard.html`/`i18n-dashboard-data.js`, paridade de chaves nos 11 idiomas via `tools/check_i18n_parity.py`, revisão manual da lógica de interpolação de placeholder (sem mudança de backend nesta versão — só frontend). |

| 1.104.0 | 02/09/2026 | Oficial | Coach mark (dica de primeiro acesso por página) deixa de ser uma caixinha no canto inferior direito — usuário reportou "em algumas sessões" ela passava despercebida, exatamente por ser pequena (320px) e ficar fora do centro de atenção (`right:24px;bottom:100px`). `showFeatureCoachMark()` reescrita pra reaproveitar o MESMO `#genericModal` centralizado que o tour de boas-vindas já usa — grande, no meio da tela, com fundo escurecido — em vez de criar um `<div>` flutuante próprio. Ajuste vale pra **qualquer tipo de conta** (não é um fix de categoria), pedido explícito do usuário. Comportamento de "não mostrar mais dicas" preservado (só marca como visto ao clicar "Entendi", mesmo critério já usado pelo tour — fechar pelo X/fundo não marca como visto, dica reaparece na próxima visita à página). **Tour de boas-vindas afiado pra imobiliária**: até aqui o tour (`dashboardIntroSlides()`) só distinguia hospedagem vs. agência genérica — usuário pediu pra deixar o conteúdo realmente específico pra imobiliária, não só "não errado". Novo branch `isImobiliaria` nos 4 slides que fazem sentido diferenciar (boas-vindas, números do topo, Opportunity Center, explorar menu — "Resumo executivo" ficou só com ajuste de palavra, o resto do texto já servia): fala de "imóveis"/"negócio imobiliário"/"catálogo" em vez de genérico, e o slide do Opportunity Center passa a mencionar explicitamente que a IA já sugere o imóvel certo do catálogo (reflete o matching estruturado da v1.101.0). 7 chaves i18n novas em 11 idiomas (1.387→1.394). Testado: balanceamento de chaves/parênteses/colchetes, paridade de chaves via `tools/check_i18n_parity.py`, revisão manual do fluxo (troca de `<div>` solto por `openGenericModal`/`closeGenericModal`, incluindo o ponto em `dismissOnboardingForever()` que antes removia o elemento antigo por id). Sem mudança de backend. |

| 1.105.0 | 02/09/2026 | Oficial | Multi-corretor: cada funcionário de uma imobiliária pode conectar o PRÓPRIO WhatsApp Business à IA, além do número principal da agência — pedido direto do usuário ("dando autonomia e automação pro funcionário também, não só pra imobiliária"), com investigação técnica completa antes de construir (agente de exploração mapeou o pipeline inteiro de WhatsApp/IA, que hoje era 100% por-hostel, sem nenhum grão mais fino). **Schema novo**: `membership_whatsapp_connections` (1 número por `membership_id`, espelhando a simplicidade de "1 número por hostel" já usada pra agência inteira) + `guests.owner_membership_id` (nullable, "dono" do lead — setado só na PRIMEIRA mensagem recebida por um número de corretor, nunca sobrescrito depois, evitando reatribuição automática). **Roteamento do webhook**: quando `phone_number_id` não bate com o número principal da agência (`get_hostel_id_by_whatsapp_phone_number_id`, fluxo de sempre, zero mudança), tenta como número de corretor (`get_membership_by_whatsapp_phone_number_id`) antes de descartar — os dois nunca colidem. **Pipeline de mensagem** (`process_incoming_message`): resolve o dono do lead, injeta a persona que o corretor escreveu (`broker_persona`) no prompt da IA (novo `_broker_persona_section()`, mesmo espírito de `custom_instructions_section` já existente, mas por pessoa) e despacha a resposta pelo número DO CORRETOR (não o principal), senão hóspede veria mensagem chegando de um número e resposta saindo de outro. **Self-service**: cada membro da equipe conecta o próprio número via `/team/my-whatsapp/embedded-signup`, reaproveitando 100% o mesmo `exchange_whatsapp_embedded_signup()` que a conexão da agência já usa (só muda o destino de persistência) — resolvido sempre pela PRÓPRIA sessão de quem chama (`get_membership(get_current_user_id(), hostel_id)`), nunca por um id recebido do cliente, então uma pessoa fisicamente não consegue mexer na conexão de outra. **Auditoria do dono**: nova aba "📱 WhatsApp da equipe" em Equipe, lista todos os corretores com status de conexão/telefone/apresentação (nunca o token) — a visibilidade de conversas em si não mudou (quem tem a permissão `chats` já via tudo, continua vendo), esse é só um painel de acompanhamento. **Chats**: tag "👤 Corretor" nos cards da lista e "Atendido por" no perfil do hóspede, achado de brinde corrigido no caminho — o enum cru de `intent` também vazava sem tradução na LISTA de chats (só o perfil individual tinha sido corrigido na v1.102.0), agora usa `intentLabel()` nos dois lugares. Escopo desta versão: só imobiliária (mesmo critério do usuário pra tudo que foi imobiliária-first nesta sessão) — schema/backend já é genérico o bastante pra estender a outras categorias de agência depois, sem retrabalho. Fora do escopo por decisão deliberada (não é bug, é corte consciente pra uma sessão sem supervisão): mensagens manuais/proativas fora do pipeline de auto-resposta (Ask StayFlow, cobranças, pedido a fornecedor) continuam sempre saindo pelo número principal, não pelo do corretor dono — fica sinalizado, não silenciado. 26 chaves i18n novas em 11 idiomas (1.394→1.420). Testado em banco SQLite isolado com Flask test client, IA e Meta mockadas: self-service (conectar/persona/desconectar) e auditoria do dono; resolução do webhook (hostel vs. membership, nunca colidem); pipeline completo — persona chega na IA, resposta sai pelo número certo, dono do lead nunca muda numa segunda mensagem mesmo chegando por outro canal; regressão confirmando que hóspede sem corretor envolvido continua 100% no fluxo antigo (número principal, sem persona). |

| 1.106.0 | 02/09/2026 | Oficial | BI mais rico nos Relatórios — primeiro item da fila de melhorias inspiradas em concorrência (WeSpeak), decisão registrada como "barato, alto retorno" por reaproveitar dado que já existia. Duas peças: **(1) Ticket médio** — nova query em `get_reports_summary()` (`AVG(amount)` sobre `reservations` com `status='confirmed' AND amount > 0`), exposta como `average_ticket` no `/reports`, renderizada como linha de estatística dentro do card "Conversão por etapa" (só aparece quando há reserva confirmada com valor, mesmo critério condicional dos outros blocos da página). **(2) Card "Relatório diário IA" deixa de ser órfão** — `reportsDailyContent`/`reportsDailyEmpty` existiam no HTML desde uma versão anterior mas `loadReports()` nunca os populava (achado ao investigar a página antes de decidir o escopo). Em vez de duplicar lógica de resumo executivo, a nova `loadReportsDailySummary()` consome o MESMO endpoint `/executive-summary` que já alimenta o topo do Dashboard (`loadExecutiveSummary()`) — zero backend novo, só uma segunda leitura da mesma IA com elementos de DOM próprios (não reaproveita os ids do Dashboard, já que as duas páginas ficam montadas simultaneamente no SPA). Badge de risco reaproveita as classes `.status-pill` já existentes (`ok`/`warm`/`hot`), sem CSS novo. 1 chave i18n nova em 11 idiomas (1.420→1.421). Testado: `get_reports_summary` em SQLite isolado (ticket médio correto com reservas mistas confirmed/pending, e retorna 0 sem erro pra hostel sem reserva confirmada — não é `NULL`/exceção), confirmado que `routes/reports.py` só repassa o dict via `jsonify` (nenhuma mudança de rota necessária), paridade i18n via `tools/check_i18n_parity.py`, balanceamento de chaves/parênteses conferido (a pequena divergência pré-existente de `<section>`/`<div>` no `dashboard.html`, 21/20 e 985/984, foi confirmada como já existente ANTES desta edição via `git show HEAD`, não introduzida agora — a edição desta versão adicionou 3 `<div>` e 3 `</div>`, balanceado). Sem mudança de schema. |

| 1.107.0 | 02/09/2026 | Oficial | Opportunity Center em pipeline visual (kanban) — segundo item da fila de melhorias inspiradas em concorrência (WeSpeak), mesma prioridade "barato, alto retorno" do item anterior. **Schema**: nova coluna `opportunities.stage` (`TEXT DEFAULT 'new'`), deliberadamente separada de `status` (que nunca sai de `'open'` em lugar nenhum do código, achado documentado desde a v1.63.0 — mudar o significado dele exigiria migrar todo consumidor existente; `stage` nasce paralelo, dono só do pipeline visual). 5 etapas fixas (`new`/`contacted`/`negotiating`/`won`/`lost`), constante única `OPPORTUNITY_STAGES` em `database.py` reaproveitada pela validação da rota. **Endpoint novo**: `PATCH /opportunities/<id>/stage`, escopado por hostel na própria query (`JOIN guests` dentro do `UPDATE`, mesmo padrão de segurança do self-service do multi-corretor v1.105.0) — nunca confia só no id vindo do cliente, testado explicitamente uma tentativa cross-tenant (hostel B tentando mover oportunidade do hostel A) pra confirmar que falha silenciosamente (404), sem vazar diferença entre "não existe" e "não é seu". **Frontend**: toggle "Lista | Pipeline" ao lado do título do Opportunity Center — view Lista é a tabela paginada de sempre, intocada; view Pipeline busca até 100 oportunidades (teto já existente da rota) e agrupa client-side em 5 colunas por `stage`, cada card com um `<select>` de transição (decisão deliberada: botão/select, não drag-and-drop, mais simples de implementar e testar numa sessão sem supervisão). Mudar a etapa dispara `PATCH` e recarrega o board. Pipeline recarrega sozinho se a página for reaberta enquanto essa view estava ativa (`reloadOpportunitiesKanbanIfActive`, registrado em `PAGE_LOADERS`). Métricas do sidebar (`probable_revenue`/`almost_closed`) e a view Lista continuam ignorando `stage` de propósito — pipeline é só uma lente visual adicional sobre o mesmo dado, não muda contagem nem filtro em lugar nenhum. 7 chaves i18n novas em 11 idiomas (1.421→1.428). Testado: banco SQLite isolado (etapa default `'new'` em linha nova, transição de etapa funciona, tentativa cross-tenant falha sem alterar nada, id inexistente retorna `False` sem lançar exceção); rota via Flask test client com sessão real (`create_session` + `session_transaction`, não chamada direta de função) cobrindo transição válida (200), etapa inválida (400) e oportunidade inexistente (404); smoke test de `/dashboard`, `/opportunities`, `/reports`, `/executive-summary` confirmando 200 em todos após as mudanças desta e da versão anterior; balanceamento de chaves/parênteses/colchetes em `dashboard.html`/`stayflow-live.js`/`app.css` (divergência pré-existente de `(`/`)` em `app.css`, 237/236 antes desta versão, confirmada via `git show HEAD` como não introduzida agora). |

| 1.108.0 | 02/09/2026 | Oficial | Venda cruzada contextual pra hospedagem (lodging) — terceiro e último item da fila de melhorias competitivas desta madrugada (inspirado na Hoteligy: IA sugere spa/restaurante/late checkout de forma contextual). Em vez de construir do zero, liberou o Portfolio — mecanismo que só agência tinha desde sempre — pra lodging, já que a camada de dado (`portfolio_items`) sempre foi 100% genérica por `hostel_id`, sem nada de agência hardcoded (confirmado por investigação antes de começar). **4 portões abertos**: (1) `_require_agency()` em `routes/portfolio.py` — agora só checa se o hostel existe, qualquer `account_kind` passa (nome da função ficou, a checagem real mudou, comentário explica); (2) `AGENCY_ONLY_PERMISSIONS` (`utils/permissions.py`) esvaziado — "portfolio" agora entra no catálogo de permissões de cargo (`permissions_for_account_kind`) também pra lodging, então o dono já pode delegar essa permissão pra um sub-cargo, não só ele mesmo (que já tinha via Admin/`ALL_PERMISSIONS_STR`); (3) nav do dashboard — removido o `data-required-account-kind="agency"` do botão "Portfólio", volta a ser gated só por permissão (mesmo padrão de Chats/Hóspedes/Financeiro); (4) `GET_OFFERINGS_TOOL` (`services/ai_service.py`) somado ao branch de tools de lodging (antes só agência tinha acesso à function-calling tool `get_offerings`) — catálogo vazio é inofensivo, o prompt já instrui a IA a não mencionar nada quando `get_offerings` volta vazio. **Prompt novo**: seção "EXTRA SERVICES" adicionada ao `SYSTEM_PROMPT` de lodging, mesma restrição da agência — nunca oferecer de forma proativa/genérica, só quando contextualmente natural (hóspede pergunta o que tem disponível, menciona relaxar/comer/estender a estadia, ou um add-on realmente relevante surge ao fechar reserva), sempre valida contra `get_offerings` antes de mencionar preço/disponibilidade, nunca inventa item. **Copy do frontend**: página Portfolio tinha subtítulo/vazio falando do modelo de COMISSÃO entre agência parceira e hospedagem terceira ("você ganha o valor cheio menos a comissão") — sem sentido nenhum quando é a própria hospedagem vendendo pro próprio hóspede. Nova `applyLodgingPortfolioCopy()` (mesmo padrão de `applyImobiliariaPortfolioCopy()` já existente) troca título/subtítulo/vazio pra "Serviços extras" com copy própria quando `account_kind==='lodging'`. Escopo deliberadamente fora desta versão (sinalizado, não esquecido): importação em lote (CSV) de itens de Portfolio continua exclusiva de agência no modal "Importar dados" — poucos itens esperados por hospedagem (spa/restaurante/late checkout), cadastro manual via "+ Novo item" já resolve, CSV fica pra se um piloto pedir de verdade. 5 chaves i18n novas em 11 idiomas (1.428→1.433). Testado: `permissions_for_account_kind("lodging")` e `("agency")` ambos retornam "portfolio"; rota `POST/GET /portfolio/items` funcionando fim a fim com sessão real de hostel `lodging` (antes retornava 403); `GET /permissions/catalog` de um hostel lodging confirmando "portfolio" na lista; `ask_ai()` chamado com `account_kind="lodging"` e OpenAI mockada (captura o `tools` passado pro client) confirmando `get_offerings` presente na lista de ferramentas — e AUSENTE quando `ai_persona="software"` (regressão do lead-capture-only, intocado); smoke test de `/dashboard`, `/portfolio/items`, `/opportunities`, `/reports` juntos confirmando 200 em todos. Balanceamento de chaves/parênteses/tags no `dashboard.html` conferido — zero `<div>`/`<section>` novos nesta versão (só atributos `id` e funções JS), divergência pré-existente inalterada. |

| 1.109.0 | 02/09/2026 | Oficial | Cancelamento de reserva direto pela conversa (item "h" da pesquisa do WhatsMinder/R2OS — o hóspede pede pra cancelar no próprio WhatsApp, sem precisar ligar/falar com recepção). Nova função `attempt_cancel_reservation(hostel_id, guest_id, reason)` em `database.py`, reaproveitando 100% o mesmo padrão de resolução já usado por `attempt_extend_reservation` (busca a reserva ativa mais recente do hóspede por `hostel_id`+`guest_id`, nunca por um `reservation_id` vindo da IA — o modelo não tem como saber o id real). **Decisão conservadora deliberada**: só cancela sozinho quando o hóspede AINDA NÃO fez check-in — se já fez, não cancela automaticamente, cria uma oportunidade (`type='cancellation'`) pra equipe revisar manualmente (mesmo espírito de `attempt_extend_reservation` quando a diária não pode ser calculada com segurança — situação ambígua nunca é decidida sozinha pela IA). Reaproveita `update_reservation_status_record()` já existente (mesma função usada pelo cancelamento manual via dashboard), então sync com Beds24, webhook e notificação ao hóspede continuam automáticos, sem nenhuma rota nova. Nova tool `cancel_reservation` em `RESERVATION_TOOLS` (`services/ai_service.py`) com instrução explícita no prompt: só chamar depois de confirmação clara e explícita do hóspede, nunca em resposta a uma pergunta sobre a política de cancelamento. Sem UI nova — cancelamento aparece na tabela de Reservas de sempre (`status='cancelled'`), e o caso "já fez check-in" aparece no Opportunity Center de sempre. `_create_extension_opportunity()` ganhou um parâmetro `opportunity_type` (antes hardcoded em `'extension'`) pra permitir o tipo `'cancellation'` sem duplicar a função. Testado em SQLite isolado: hóspede sem check-in cancela automaticamente (status muda pra `cancelled`, confirmado no banco); hóspede já com check-in NÃO cancela (status permanece `confirmed`), oportunidade criada com `type='cancellation'` correto (achado um bug próprio no caminho: o parâmetro `opportunity_type` foi adicionado à função mas esquecido na chamada, corrigido antes de publicar); hóspede sem nenhuma reserva ativa levanta `ValueError` esperado; confirmado via mock do cliente OpenAI que a tool `cancel_reservation` aparece na lista de ferramentas passadas pro modelo numa conversa de lodging. Sem chave i18n nova (feature 100% conversacional, sem UI). |

| 1.110.0 | 02/09/2026 | Oficial | Desconto automático por estadia longa (item "f" da pesquisa do WhatsMinder/R2OS). **Schema**: 2 colunas novas em `room_categories` (`long_stay_min_nights`/`long_stay_discount_pct`), nullable/opt-in, mesmo padrão de `weekend_price_per_night` (v1.75.0). `calculate_reservation_amount()` (já fazia o cálculo noite-a-noite considerando temporada/fim de semana) ganhou um passo final: se o total de noites bate o mínimo configurado, aplica o percentual sobre o TOTAL da estadia (desconto de volume, não mais uma tarifa por noite — por isso entra depois do loop, não dentro dele). **Achado ao investigar antes de construir, virou o fix mais importante desta versão**: o `SYSTEM_PROMPT` de lodging nunca instruía a IA a considerar `weekend_price_per_night`/tarifa de temporada ao COTAR um preço pro hóspede durante a conversa — ela só fazia `price_per_night × noites` na mão (a mesma lógica de fim de semana/temporada só era aplicada de verdade dentro de `calculate_reservation_amount`, no momento de criar a reserva de fato). Isso significava que a IA podia anunciar um valor errado pro hóspede antes de reservar, mesmo já existindo desconto de fim de semana/temporada configurado — bug pré-existente, não introduzido agora, só ficou visível porque desconto de estadia longa é mais um caso do mesmo problema. **Correção arquitetural**: nova tool `get_stay_total(category_name, checkin_date, checkout_date)` que chama `calculate_reservation_amount()` direto e devolve o total EXATO (já com fim de semana/temporada/estadia longa aplicados) — a seção PRICING do prompt foi reescrita pra instruir a IA a sempre usar essa tool em vez de multiplicar preço por noite na mão, mesmo espírito de por que `calculate_nights` já existe (nunca deixar o modelo fazer aritmética que pode errar). Frontend: 2 campos novos no modal de edição de modalidade ("Desconto a partir de X noites" + "Desconto de estadia longa %"), mesmo modal que já tem a tarifa de fim de semana, PATCH `/room-categories/<id>` estendido. 2 chaves i18n novas em 11 idiomas (1.433→1.435). Testado: `calculate_reservation_amount` isolado confirmando total correto abaixo do limiar (sem desconto), no limiar exato e acima dele; simulação completa do loop de tool-calling da IA (cliente OpenAI inteiro mockado com 2 respostas em sequência — uma chamando `get_stay_total`, outra com o texto final) confirmando que o valor com desconto (630 pra 7 noites com 10% off) chega correto na resposta final da IA; rota `PATCH /room-categories/<id>` + `GET /room-categories` via Flask test client com sessão real confirmando os 2 campos novos persistindo e retornando certo. Achado no caminho ao escrever o teste (não é bug de produção, só do próprio teste): `update_room_category()` sempre espera receber o formulário INTEIRO a cada chamada (mesmo comportamento pré-existente de `weekend_price_per_night` — um campo omitido vira `NULL`, não "mantém o valor atual"), consistente com como o frontend sempre reenvia todos os campos do modal juntos; não é regressão, só documentado aqui pra não confundir quem for integrar por fora do modal no futuro. |

| 1.111.0 | 02/09/2026 | Oficial | Cupom de desconto validado pela IA (item "g" da pesquisa do WhatsMinder/R2OS, fecha a trinca f/g/h dessa mesma pesquisa). **Schema**: nova tabela `discount_coupons` (`code` UNIQUE por `hostel_id`, `discount_pct`, `active`, `expires_at` opcional) — escopo deliberadamente enxuto: sem limite de uso/contador nesta rodada, staff só ativa/desativa manualmente. `reservations` ganhou `coupon_code` (nullable, só auditoria — o valor final já vem gravado direto em `amount`). **CRUD** (`create_coupon`/`list_coupons`/`set_coupon_active`/`delete_coupon`) + 4 rotas novas em `routes/rooms.py` (`/coupons`), permissão `operations` (mesmo tier de modalidades/tarifas). **Validação** (`validate_coupon`): código normalizado pra maiúsculo (case-insensitive), nunca lança exceção — sempre devolve `{valid, discount_pct}` ou `{valid: False, reason}`, pensado pra IA consumir direto. **Aplicação** (`apply_coupon_to_amount`, reaproveitada em 2 pontos): SEMPRE revalida o cupom no momento de aplicar (nunca confia num `validate_coupon` anterior da mesma conversa — cupom pode expirar/ser desativado entre uma chamada e outra). **IA**: nova tool `validate_coupon(code)`; `get_stay_total` e `create_reservation` ganharam `coupon_code` opcional — a MESMA lógica de aplicação roda nos dois pontos (cotação e reserva de fato), garantindo que o valor que a IA anuncia bate exatamente com o que é cobrado. Prompt novo (seção "DISCOUNT COUPONS"): só chamar `validate_coupon` quando o hóspede mencionar um código, nunca assumir que funciona, nunca calcular o desconto na mão. **Frontend**: novo modal "🎟️ Cupons de desconto" no menu ☰ Ações do Mapa de Quartos (mesmo padrão de Modalidades/Tarifas) — criar código+percentual+validade opcional, listar com ativar/desativar/excluir. **Bug próprio corrigido antes de publicar**: o texto inline "expira em" da lista de cupons e o rótulo do campo "Expira em (opcional)" do formulário foram escritos usando a MESMA chave i18n com fallbacks diferentes — corrigido separando em `coupons.expiresInline`/`coupons.expiresLabel` antes de gerar as traduções (achado na revisão do próprio código, não em teste automatizado). 15 chaves i18n novas em 11 idiomas (1.435→1.450). Testado em 4 frentes: (1) CRUD isolado em SQLite — normalização de código maiúsculo, validação de percentual (rejeita >100%), código duplicado no MESMO hostel rejeitado mas permitido em hosteis diferentes (`UNIQUE(hostel_id, code)`), cupom inativo/expirado/inexistente todos retornam `valid: False` com motivo certo, cross-tenant não vaza; (2) simulação completa do loop de tool-calling da IA com 3 respostas mockadas em sequência (`validate_coupon` → `get_stay_total` com `coupon_code` → texto final) confirmando que o valor com desconto (400 pra 5 noites de 100 com 20% off) chega certo na fala da IA; (3) `create_reservation_from_chat` com cupom válido (valor final gravado com desconto, `coupon_code` persistido) E com cupom inválido (valor cheio cobrado, `coupon_applied: False`, `coupon_error` preenchido — reserva não falha por causa de um código ruim); (4) as 4 rotas `/coupons` via Flask test client com sessão real (criar, listar, desativar, excluir, rejeitar percentual inválido). Smoke test final de regressão confirmando 200 em `/dashboard`, `/portfolio/items`, `/opportunities`, `/reports`, `/room-categories`, `/coupons`, `/bed-map`, `/rooms` juntos. Com essa versão fecha a trinca completa f/g/h da pesquisa WhatsMinder/R2OS. |

| 1.112.0 | 03/09/2026 | Oficial | Fecha a dívida de i18n pré-existente registrada desde a v1.97.0 (achado em auditoria naquela versão, adiado deliberadamente pra focar nas melhorias competitivas). Reauditoria (`T('chave', ...)` usado em `dashboard.html`/`stayflow-live.js`/`chats-live.js` contra o dicionário `pt`) confirmou exatamente as mesmas 100 chaves reais faltando da auditoria anterior (101 contando 1 falso-positivo — `portfolio.realEstate.amenity.` é uma concatenação dinâmica de chave em tempo de execução, `T('portfolio.realEstate.amenity.' + key, ...)`, as chaves concretas por trás dela já existiam desde a v1.101.0). Todas as 100 traduzidas nos 11 idiomas — texto em português extraído diretamente do próprio fallback já escrito em cada `T(chave, fallback)` no código (nunca reescrito do zero, pra não divergir do que já era exibido quando a chave faltava). Áreas cobertas: `guestCharge.*` (20, modal de cobrança manual), `home.kpi.*Note*` (4, notas dos KPIs do Dashboard), os 5 módulos operacionais — `kitchen.orders.*`/`maintenance.*`/`operations.tasks.*`/`parking.*`/`patrimonialSecurity.*` (28 no total), `partners.*` (2), `portfolio.*` (14, modal de item + rótulos), `settings.mercadopago.*`/`settings.nuvemshop.*`/`settings.whatsapp.*` (26, os 3 cards de integração em Configurações), mais 10 avulsas (`common.location.required`, `reservations.checkoutOverdueLabel`, `team.roleNamePlaceholderExampleAgency`, `settings.general.summaryDescAgency`, `settings.communication.pushTypeNuvemshopOrder`). 1.100 traduções no total (100 chaves × 11 idiomas), inseridas via script (mesmo padrão já usado nesta sessão pra lotes menores) que localiza os 11 blocos de idioma pelo cabeçalho `  xx: {` e insere antes do fechamento de cada bloco — verificado sem duplicar nenhuma chave já existente (checagem de contagem == 11 por chave amostrada) e sem colidir com nenhuma chave anterior. Testado: reauditoria pós-inserção confirma 0 chaves reais faltando (só o falso-positivo dinâmico permanece, esperado); `tools/check_i18n_parity.py` confirma os 3 dicionários com paridade total nos 11 idiomas (1.450→1.550 no `i18n-dashboard-data.js`); balanceamento de chaves/parênteses conferido no arquivo de tradução. Sem mudança de HTML/JS de comportamento — só preenchimento de dicionário, o `dashboard.html` não foi tocado nesta versão. |

| 1.113.0 | 03/09/2026 | Oficial | "Modo Dono" (item "i" da pesquisa do WhatsMinder/R2OS) — quem já atende a hospedagem consegue mandar QUALQUER mensagem pro número principal de WhatsApp da própria conta e receber de volta um resumo reduzido (ocupação, reservas confirmadas, receita, oportunidades em aberto), sem abrir o painel. Decisão de design tomada com o usuário antes de codar: entre 3 opções (número separado, palavra-chave de ativação, reconhecer pelo telefone já cadastrado no perfil), escolhida a terceira — nunca uma senha/palavra-chave em texto solto que poderia vazar e expor dado financeiro pra qualquer pessoa, sempre a identidade real de quem manda a mensagem (mesmo critério de segurança do self-service do multicorretor, v1.105.0). **Schema**: `users.phone` (nullable, opt-in) — achado real no caminho: existe uma migração de reconstrução da tabela `users` (`_migrate_users_to_memberships`, roda em TODO banco novo pra descartar as colunas legadas `hostel_id`/`role`) com uma lista de colunas hardcoded na nova tabela — a `phone` foi descartada silenciosamente na primeira tentativa até eu adicionar `phone` também na nova `CREATE TABLE`/`INSERT...SELECT` dessa migração (o comentário já existente no código avisava exatamente sobre esse risco, atribuído ao mesmo bug que já tinha acontecido antes com `onboarding_dismissed`). **Reconhecimento** (`find_owner_mode_user`): compara os ÚLTIMOS 8 DÍGITOS do telefone de quem manda contra o telefone cadastrado de cada membro ativo da equipe daquele hostel (não igualdade exata — formato digitado à mão raramente bate caractere a caractere com o que a Meta manda), e exige a permissão `"dashboard"` (nunca reconhece um membro sem essa permissão, mesmo com telefone cadastrado). **Interceptação** (`routes/chat.py::process_incoming_message`): checagem roda ANTES de criar/buscar o hóspede — quando reconhece o dono, responde só o resumo e retorna, sem gerar guest/lead/oportunidade nenhuma; quando não reconhece ninguém (o caso de praticamente toda mensagem real), o fluxo de hóspede segue 100% intacto, sem atraso. **Resumo** (`build_owner_mode_summary`): texto simples sem IA/tool-calling, reaproveitando 100% os mesmos dados que `get_dashboard_stats` já calcula pro topo do Dashboard — zero query nova; linha de ocupação (camas) só aparece pra `account_kind='lodging'`, agência recebe a versão sem essa linha. **Frontend**: novo card "📊 Modo Dono" em Configurações > Geral, modal de cadastro do próprio telefone, rotas self-service `GET/PUT /team/my-owner-mode` (resolvidas sempre pelo `user_id` da própria sessão, nunca por id vindo do cliente — mesmo padrão de segurança de sempre). Escopo deliberadamente fora desta versão: "projeção de fechamento do mês" (métrica nova que não existe em lugar nenhum do backend, mencionada na pesquisa original do WhatsMinder) e conversação/perguntas de acompanhamento (a versão atual é sempre a MESMA resposta fixa pra qualquer mensagem do dono, não um agente conversacional) — MVP estático deliberado, mais simples e mais barato de testar numa sessão sem supervisão; ambos ficam sinalizados pra uma v2 se o usuário pedir. 9 chaves i18n novas em 11 idiomas (1.550→1.559). Testado: `find_owner_mode_user` isolado (sem telefone cadastrado não reconhece nada; reconhece por sufixo mesmo com formato de telefone diferente; número com últimos 8 dígitos diferentes corretamente não reconhecido; cross-tenant não vaza — telefone cadastrado no hostel A não é reconhecido no hostel B); `build_owner_mode_summary` com e sem linha de ocupação por `account_kind`; `process_incoming_message` end-to-end confirmando que mensagem do dono NÃO cria guest (contagem de `guests` antes/depois idêntica) e devolve o resumo, E que mensagem de um número não-cadastrado continua criando guest normalmente (regressão); rotas `GET/PUT /team/my-owner-mode` via Flask test client com sessão real; smoke test final rodando 9 endpoints tocados nesta sessão inteira, todos 200. |

| 1.114.0 | 03/09/2026 | Oficial | "Modo StayFlow" — extensão do Modo Dono (v1.113.0) pro usuário acompanhar o NEGÓCIO da StayFlow em si (contas cadastradas/ativas, MRR estimado, comissão de parceiro arrecadada), não uma hospedagem cliente específica. Pedido direto do usuário depois de ativar o Modo Dono normal ("Sim quero usar pra acompanhar a Stayflow"). **Reconhecimento diferente do Modo Dono comum**: quando a mensagem chega no número que tem `ai_persona='software'` (a conta que representa a própria StayFlow no sistema multi-tenant, já usada pelo painel interno via `_get_software_hostel_id()`), o gate deixa de ser "permissão `dashboard` num hostel específico" e passa a ser `is_stayflow_admin_email()` — mesmo critério que já protege as rotas do `admin.html`, porque quem trabalha na StayFlow não necessariamente tem `hostel_memberships` em hostel nenhum. Nova `find_stayflow_admin_by_phone()` varre todos os usuários com telefone cadastrado (equipe pequena, custo desprezível) em vez de filtrar por um hostel_id só. **Resumo** (`build_stayflow_business_summary()`): reaproveita 100% `get_stayflow_admin_overview()` — o MESMO dado que já alimenta os cards financeiros do `admin.html` — total de contas, quantas estão com status `active`, MRR estimado (via `PLAN_PRICES`), comissão de parceiro arrecadada, e novas contas nos últimos 7 dias (`count_new_hostels_last_days`). Zero query nova. **Zero mudança de frontend**: o mesmo card "Modo Dono"/rota `/team/my-owner-mode` do v1.113.0 já serve pra isso — o self-service resolve só pelo `user_id` da sessão (não pelo hostel_id), então o usuário cadastra o telefone de qualquer conta seu que já tenha login, e o reconhecimento no número da StayFlow funciona pelo e-mail dele estar na allowlist, não por precisar logar numa conta específica. Escopo deliberadamente fora: contagem de leads na Prospecção (pipeline de vendas da própria StayFlow) não entrou nesse resumo — fica de fora até ficar claro que vale a pena, é métrica de fonte diferente das outras. Testado: `find_stayflow_admin_by_phone` isolado (sem telefone não reconhece; reconhece por sufixo quando o e-mail está na allowlist; dono de hostel comum com telefone cadastrado mas SEM ser da equipe StayFlow corretamente não reconhecido); `build_stayflow_business_summary` retornando texto com todos os campos esperados; `process_incoming_message` end-to-end confirmando que mensagem no número da StayFlow devolve o resumo de NEGÓCIO e mensagem num hostel comum continua devolvendo o resumo de HOSPEDAGEM normal — os dois caminhos não se confundem. |

| 1.115.0 | 03/09/2026 | Oficial | Rastreio de pedido em tempo real, tipo iFood/Rappi/PedidosYa — pedido do usuário. **Limite técnico explicado antes de construir**: uma notificação ÚNICA que atualiza no lugar (o padrão real desses apps) só existe em app nativo/PWA com push próprio — o WhatsApp Business API não suporta isso, cada mensagem é sempre nova e separada. Escopo acordado com o usuário: (1) mensagens de WhatsApp automáticas a cada mudança de etapa, e (2) um link de rastreio visual enviado quando o pedido é criado, pra quem quiser acompanhar abrindo uma página. **Achado real ao investigar antes de codar**: o pipeline de múltiplas etapas por item (`pending`→`preparing`→`ready`→`delivered`) já existia inteiro em `kitchen_order_items`/`update_kitchen_order_item_status`/`get_kitchen_order_aggregate_status`, construído numa sessão anterior — só nunca tinha notificação pro hóspede nem página pública. **Bug pré-existente corrigido no caminho**: `get_kitchen_order_aggregate_status()` nunca distinguia `'preparing'` de `'pending'` (os dois caíam no mesmo `return "pending"` final) — a etapa "em preparo" nunca aparecia pra ninguém observando só o status agregado. Corrigido de forma aditiva (só ganhou mais um `if`, as outras 4 saídas mantêm exatamente a mesma lógica). **Schema**: `tickets.tracking_token` (nullable, só gerado quando há `reported_by_guest_id` — sem hóspede vinculado, ninguém pra receber o link). **Notificação automática**: `notify_guest_kitchen_order_stage()` dispara uma mensagem só quando a etapa AGREGADA muda de verdade (`preparing`/`ready`/`delivered` — `pending` já foi confirmado na hora do pedido, `partially_ready` fica em silêncio pra não virar ruído), reaproveitando `send_message_to_guest_now()` já existente (resolve canal certo, salva no histórico — zero código de envio novo). Ligada dentro de `update_kitchen_order_item_status_route`, comparando o status agregado antes/depois da mudança. **Link de rastreio**: `create_kitchen_order()` gera o token; nova `get_ticket_tracking_url()` monta a URL pública (mesmo padrão de `_public_media_url` já usado pra foto de chat); a tool `create_kitchen_order` da IA devolve `tracking_url` no resultado quando existir, e o prompt (seção `DURING-STAY REQUESTS`) instrui a IA a compartilhar esse link ao confirmar o pedido — nunca inventar um link. **Bug próprio corrigido antes de testar**: o texto do prompt continha `{tracking_url}` sem escapar dentro de uma string que passa por `.format()` — `KeyError` na hora de montar o prompt (chave sem valor correspondente); corrigido removendo a interpolação literal, a IA já sabe pegar o link do resultado da tool sem precisar de um placeholder no texto fixo. **Página pública nova** (`Track.html`, roteada via o wildcard `/<page_name>.html` que já existia — nenhuma rota estática nova precisou ser criada): sem autenticação (a entropia do token de 24 bytes é a autorização, mesmo padrão de `/media/chat/<token>`/`/media/portfolio/<token>`), stepper visual de 4 etapas + lista de itens com status individual, atualiza sozinha a cada 5s (polling simples, sem WebSocket). Nova rota `GET /track/<token>` em `app.py` (JSON, valida formato do token via regex antes de consultar o banco, nunca vaza dado de outro hostel/hóspede). Testado: geração de token só quando há hóspede vinculado (staff criando pedido de walk-in nunca gera); `get_ticket_by_tracking_token` resolvendo hóspede/tipo/itens corretos, token inválido devolve `None`; notificações disparando certo em `preparing`/`ready`/`delivered` e ficando em silêncio em `pending`/`partially_ready`/sem hóspede vinculado; fluxo HTTP completo (mudar status → notificação disparada → página pública reflete a mudança → `delivered` resolve o ticket automaticamente) via Flask test client com sessão real; tokens inválidos e malformados retornando 404 (regex bloqueia antes de consultar o banco); fluxo da IA completo (tool-calling mockado) confirmando que não quebra mais com o bug do `.format()`. Smoke test final de regressão com 11 endpoints, todos 200. |

| 1.116.0 | 03/09/2026 | Oficial | Aba de Contatos (agenda) — pedido do usuário: "criar uma aba de contatos, tipo uma agenda... pra que ele pesquise um contato na aba chats e mande mensagem ou peça pro StayFlow fazer isso". **Limite técnico explicado antes de construir**: sincronização com Google Contacts é tecnicamente viável mas exige passar pela verificação de "escopo sensível" do Google (vídeo demonstrativo, verificação de domínio, revisão que pode levar semanas — mesmo espírito do App Review do Instagram já pendente). Sincronização com Apple/iCloud não tem API oficial pra terceiros — só CardDAV com senha de app gerada manualmente, fricção alta e integração parcial. Escopo acordado: construir a aba com **cadastro manual completo agora**, sync com Google fica pra quando o usuário criar o projeto no Google Cloud, Apple fica de fora. **Schema**: nova tabela `contacts` (`hostel_id`, `name`, `phone`, `email`, `notes`, `source` — sempre `'manual'` por ora), **deliberadamente separada de `guests`**: contato é alguém que a equipe SALVOU (pode nunca ter mandado mensagem), guest só existe depois de uma conversa real. **CRUD completo** (`create_contact`/`list_contacts` com busca por nome ou telefone via normalização de acento/`LIKE` em Python, mesmo critério de `find_guest_by_name`/`update_contact`/`delete_contact`) em `routes/contacts.py`, blueprint novo registrado em `app.py`, permissão `chats`. **"Mandar mensagem" (ação manual)**: nova `start_chat_with_contact()` resolve-ou-cria o guest correspondente ao telefone do contato (reaproveita 100% `get_or_create_guest_by_channel`, mesma identidade canônica de qualquer mensagem real — idempotente, chamar duas vezes não duplica guest) e devolve o `guest_id` pro frontend abrir a conversa normal na aba Chats. **"Pedir pro StayFlow fazer isso" (ação via IA)**: `propose_guest_message()` (Ask StayFlow) ganhou um fallback — quando a busca por nome não acha nenhum GUEST, cai pra `find_contact_by_name()` antes de desistir, cria o guest na hora e segue o fluxo normal de rascunho→confirmação→envio que já existia. Um tool só cobre os dois casos (hóspede existente ou contato nunca conversado), sem tool nova nem mudança de prompt. **Busca integrada na aba Chats** (pedido explícito): novo campo de busca acima da lista de conversas — filtra as conversas já carregadas (client-side, sem chamada nova) E busca contatos salvos que ainda não têm conversa (`/contacts?search=`, resultado com "💬 Iniciar conversa"). **Achado de risco evitado antes de quebrar o layout**: `.chat-layout` é CSS Grid de 3 colunas fixas esperando exatamente 3 filhos diretos (`.chat-list`/`.chat-window`/`.guest-profile`) — envolver `.chat-list` num wrapper novo pra caber o campo de busca exigia replicar manualmente `height:100%`/`flex` no wrapper (senão a coluna colapsava) e adicionar as mesmas regras de esconder/mostrar por `data-mobile-view` que já existiam só pra `.chat-list` (senão a busca ficava visível por cima da tela de conversa/perfil no mobile — bug real encontrado e corrigido ANTES de publicar, verificando a CSS existente linha por linha antes de mexer). Frontend novo: página "Contatos" (lista + busca + modal de cadastro/edição, mesmo padrão visual de Portfolio/Cupons), nav item novo. 17 chaves i18n novas em 11 idiomas (1.559→1.576). Testado: CRUD completo isolado (nome vazio rejeitado, busca com/sem acento, busca por telefone parcial, cross-tenant não vaza — hostel B não vê nem edita contato do hostel A); `start_chat_with_contact` idempotente (chamar duas vezes devolve o MESMO guest_id, não duplica); contato sem telefone corretamente rejeitado ao tentar iniciar conversa; `propose_guest_message` com fallback de contato testado ponta a ponta (nome que só existe como contato cria o guest e o rascunho corretamente; nome que não bate em nada dá erro claro); as 5 rotas HTTP via Flask test client com sessão real; smoke test final com 14 endpoints tocados nesta sessão inteira, todos 200. |

| 1.117.0 | 03/09/2026 | Oficial | Pedido automático de avaliação no Google logo após o checkout — ideia própria proposta ao usuário (não vinha de nenhuma fila anterior) quando ele pediu explicitamente uma sugestão nova, fora do que já estava planejado; aprovada com "Pode fazer". **Opt-in pela PRESENÇA do link, sem toggle separado**: novo campo `settings.google_review_link` (nullable) em Configurações > Empresa — hostel que não preenche o campo nunca dispara nada, decisão deliberada pra não precisar de uma segunda configuração ("ativar" + "link") quando uma só já basta. **Gatilho** (`send_checkout_review_request`, chamada dentro de `checkout_reservation_bed` logo após o commit do checkout): busca o link configurado, monta mensagem com o nome do hóspede quando disponível ("Foi um prazer receber você, {nome}!") e envia via `send_message_to_guest_now()` já existente — zero código de envio novo. **Silencioso por design em qualquer falha** (sem link configurado, reserva sem `guest_id` vinculado — ex.: walk-in que nunca conversou no WhatsApp —, erro de envio): a chamada inteira vive dentro de um `try/except` em `checkout_reservation_bed` que só imprime aviso no log, nunca deixa o checkout em si falhar por causa de um pedido de avaliação que é só um bônus. Campo exposto via `_SETTINGS_TEXT_FIELDS` (mesmo mecanismo genérico já usado por todo campo de texto de Configurações — GET/POST wireados automaticamente, só precisou adicionar o nome à lista e ao `SELECT` da rota). 3 chaves i18n novas em 11 idiomas (1.576→1.579). Testado em banco SQLite isolado: sem link configurado devolve `False` direto, sem tentar nada; com link configurado tenta o envio de verdade (confirmado pelo dict de retorno de `send_message_to_guest_now`, que não é booleano — é `{sent, phone}` — achado ao testar, não bug de produção, já que o único chamador ignora o valor de retorno); checkout real de ponta a ponta dispara o pedido sem lançar exceção; checkout de reserva SEM `guest_id` vinculado corretamente não quebra nem tenta enviar nada. Rotas `GET`/`POST /settings` via Flask test client com sessão real confirmando que o campo persiste e volta certo. Paridade de chaves nos 11 idiomas (`tools/check_i18n_parity.py`) e balanceamento de chaves/parênteses/colchetes de `dashboard.html`/`i18n-dashboard-data.js` conferidos antes de publicar. |

| 1.118.0 | 03/09/2026 | Oficial | Ajuste de UX na v1.117.0, pedido pelo usuário logo depois de publicada: o campo de link de avaliação do Google estava inline dentro do formulário grande de Configurações > Empresa (junto com razão social, CUIT, endereço etc) — usuário pediu explicitamente um botão em vez disso. Convertido pro mesmo padrão já usado pelo "Modo Dono": novo card clicável `⭐ Avaliações no Google` em Configurações > Geral (ao lado do card do Modo Dono), com resumo dinâmico (Ativado/Desativado conforme o link está configurado ou não), abrindo um modal dedicado (`openGenericModal`) com explicação + campo + botão Salvar, chamando `/settings` diretamente (POST/GET) em vez de passar pelo `saveSettings()` em lote. Campo removido do formulário de Empresa. Zero mudança de backend — `send_checkout_review_request`/`settings.google_review_link` da v1.117.0 continuam exatamente iguais, só mudou onde e como o dono cadastra o link. 3 chaves i18n antigas (`settings.company.googleReviewLink{Label,Placeholder,Hint}`) removidas dos 11 idiomas e substituídas por 6 novas no namespace `googleReview.*` (title, summaryDescOn/Off, modalDesc, linkLabel, linkPlaceholder) — reaproveitadas as chaves genéricas já existentes `common.save`/`common.savedMessage`/`common.saveFailed`/`common.saveConnError` em vez de duplicar (1.579→1.582). Testado: paridade de chaves nos 11 idiomas (`tools/check_i18n_parity.py`), balanceamento de chaves/parênteses/colchetes de `dashboard.html`/`i18n-dashboard-data.js`, grep confirmando zero referência órfã às 3 chaves antigas removidas e zero `data-setting="google_review_link"` sobrando no HTML. Sem mudança de rota/schema — puramente frontend. |

| 1.119.0 | 03/09/2026 | Oficial | Auditoria completa de "formulário exposto" em `dashboard.html`, pedida pelo usuário na sequência da v1.118.0 ("lembrando que nenhum formulário fica exposto, sempre guardados em botões... faz uma busca refinada por formulários soltos e guarda todos em botões"). Agente de exploração dedicado varreu as ~11 mil linhas do arquivo (todo `<input`/`<select`/`<textarea` fora de template de modal, todo `data-settings-section=`, todo `<div class="card"` nas 21 páginas) — resultado: **todas as outras 18 páginas já seguem o padrão corretamente** (toda ação de "criar/editar" já abre modal), a única categoria com violação real era dentro de Configurações, em 3 dos 10 itens do menu lateral: **Empresa** (razão social, CUIT/RUT, endereço, fuso, moeda, checkin/checkout padrão, logo), **Marca/White-label** (logo do painel, nome exibido, cor, favicon, domínio próprio) e **IA StayFlow** (toggles de resposta automática/geração de oportunidades + instruções customizadas) — os 3 renderizavam os campos direto na página (atrás de dois cliques de navegação, mas sem modal) em vez de atrás de um card clicável como os outros 7 itens do mesmo menu (Geral, Modo Dono, Avaliações Google, WhatsApp, Facebook, Instagram, Nuvemshop, Tokko, Trocar senha, Programa de indicação). Convertidos pro mesmo padrão: `openCompanySettingsModal()`/`openBrandingModal()`/`openAISettingsModal()`, cada um um card `settings-summary-card` com descrição estática + modal via `openGenericModal`. **Reaproveitamento total dos handlers de salvar**: Empresa e IA continuam usando o mesmo `saveSettings()` genérico de sempre (a função já era escrita pra funcionar com campos dentro de modal — o comentário original já explicava que ela busca `[data-setting]` no `document` inteiro, não só dentro de `#settings`, exatamente por causa de modais como o de "Geral"); Marca continua usando `saveBrandingSettings()` inalterado. **Achado no caminho**: como `hydrateSettingsFromBackend()` (que preenche os campos com o valor salvo ao carregar a página) É escopada só em `#settings` e nunca alcança `#genericModalBody` (que fica fora dessa árvore), os campos de Empresa/IA precisavam de hidratação própria ao abrir o modal — nova `hydrateModalSettingsFields()` (busca `/settings`, preenche qualquer `[data-setting]` presente dentro do modal aberto), reaproveitável pelos dois; Marca já tinha sua própria hidratação (`applyBranding`), só precisou ser rechamada depois de abrir o modal pra repopular os campos recém-criados. `data-required-account-kind="lodging"` nos campos de checkin/checkout (só fazem sentido pra hospedagem) reaplicado manualmente via `applyAccountKindVisibility()` após abrir o modal de Empresa, já que esse gate normalmente só roda uma vez no bootstrap da página. 1 chave i18n nova (`settings.ai.summaryDesc`, o "IA" não tinha descrição de resumo antes) em 11 idiomas; as demais 25 chaves usadas nos 3 modais novos são reaproveitadas das que já existiam (1.582→1.583). Testado: paridade de chaves nos 11 idiomas, balanceamento de chaves/parênteses/colchetes de `dashboard.html`/`i18n-dashboard-data.js`, contagem de backticks par (sanidade de template literal), grep confirmando as 3 novas funções definidas uma única vez cada e as 26 chaves `T(...)` usadas nos 3 modais novos todas presentes no dicionário `pt`. Sem navegador disponível neste ambiente pra clicar de fato nos 3 modais novos — testado por revisão de código/lógica (mesmo padrão de `openGeneralSettingsModal`/`openGoogleReviewModal` já usados e validados em produção), não por teste end-to-end em UI real; sinalizado explicitamente, não alegado como testado visualmente. Sem mudança de rota/schema — puramente frontend. |

| 1.120.0 | 03/09/2026 | Oficial | "Equipe" removida do submenu de Configurações — usuário notou que o item aparecia em 3 lugares (menu lateral principal, submenu de Configurações, dropdown do ícone de usuário) e que, diferente dos outros 7 itens do mesmo submenu (Geral/Empresa/IA/Comunicação/Integrações/Segurança/Billing, que abrem uma seção INLINE), "Equipe" só redirecionava pra fora de Configurações (`openPage('team', ...)`) — puramente redundante com o menu lateral, sem servir a nenhum propósito próprio ali. Usuário concordou com a recomendação de manter só menu lateral (acesso principal) + ícone de usuário (atalho rápido, mesmo lugar de "Sair") e remover a entrada de dentro de Configurações. Fix de uma linha (`dashboard.html`), sem tocar em JS/CSS/backend — o botão não tinha `data-settings-target`, então nunca fez parte da lógica de `switchSettingsSection()`, era só um item de navegação a mais na lista. Testado: balanceamento de chaves/parênteses/colchetes, confirmado que a chave i18n `nav.team` continua em uso nos outros 2 lugares (nenhuma chave órfã). |

| 1.121.0 | 03/09/2026 | Oficial | Lista de conversas redesenhada em padrão "inbox mobile premium" (tipo WhatsApp/Telegram) — usuário mandou print do "Meu chat" no celular reclamando que cada conversa aparecia como um cartão flutuante separado (borda arredondada + gap entre um e outro) em vez de linhas cheias como qualquer app de mensagens de verdade. **Causa raiz**: `.chat-item` (classe compartilhada entre a aba Chats do dashboard normal e Meu chat/Suporte do painel interno, `admin.html`) tinha `border-radius:15px;border:1px solid;margin-bottom:8px` — cada item virava seu próprio cartão arredondado boiando dentro do cartão maior da lista (cartão dentro de cartão). **Redesenho em `app.css`** (arquivo único, afeta as 3 listas de uma vez): linhas agora borda-a-borda (`border-radius:0`, sem `margin-bottom`, separadas por um fio de 1px), destaque de seleção virou fundo azul + borda esquerda de 3px (em vez de borda ao redor inteira), `.chat-list` com padding reduzido pra as linhas ocuparem quase toda a largura do cartão externo. **Avatar circular novo**: inicial do nome + cor derivada por hash determinístico (mesma paleta de tokens da StayFlow: azul/ciano/verde/amarelo/vermelho/roxo, sem precisar de foto real que a StayFlow não tem — mesma ideia do Slack/Telegram), com uma bolinha colorida no canto inferior direito indicando o canal (WhatsApp/Messenger/Instagram) — substitui o pill de texto cheio que antes ficava ao lado do nome disputando espaço numa tela estreita (o nome do canal virou só um `title` no hover, pra quem quiser conferir no desktop). Nome+preview ganharam truncamento com reticências (`text-overflow:ellipsis`) em vez de estourar a linha. **Estado "não lida" tratado como no WhatsApp de verdade**: nome e preview em negrito/branco (em vez de cinza) + bolinha azul à direita da prévia, só em Meu chat/Suporte (os únicos com esse dado — a aba Chats principal do dashboard não tem conceito de "não lida" por conversa, só um contador global de notificações). **Achado de bug evitado antes de testar**: a primeira versão do helper de avatar extraía a inicial com `charAt(0)` de qualquer rótulo recebido — funcionaria pra nomes normais, mas quebraria pela metade um emoji usado como avatar (ex: o ícone de tipo de hospedagem nas conversas de Suporte, `kindIcon()`), já que a maioria dos emojis é par substituto UTF-16 (2 unidades de código). Corrigido adicionando um parâmetro `rawContent` que passa o emoji direto, sem fatiar. Aplicado nos 3 lugares que renderizam `.chat-item`: `chatGuestItemHtml`/`supportItemHtml` (`admin.html`, com helper de avatar duplicado ali por serem arquivos HTML separados sem módulo JS compartilhado) e o loader da aba Chats principal (`assets/js/chats-live.js`, reaproveitando as funções globais já expostas em `dashboard.html` já que os dois scripts compartilham o mesmo `window` na mesma página) — nesse último a bandeirinha de país (que já existia antes da conversa, indicando o país do hóspede pelo DDI do telefone) continuou como prefixo de texto do nome, não virou conteúdo do avatar, pra não confundir "identidade visual" com "informação geográfica". 2 blocos de estado vazio/erro (aba Chats) e o resultado de busca de contato salvo (aba Chats) precisaram de um `<div class="chat-item-body">` novo ao redor do conteúdo, senão a mudança de `.chat-item` pra `display:flex` os quebraria (nome e prévia ficariam lado a lado em vez de empilhados). Sem chave i18n nova — só rótulo de canal reaproveitado como `title` de hover, texto visível não mudou. Testado: balanceamento de chaves/parênteses/colchetes e contagem de crases pareada nos 4 arquivos tocados (`dashboard.html`, `admin.html`, `assets/js/chats-live.js`, `static/css/app.css` — a única divergência de parênteses encontrada em `app.css`, 250/249, é a MESMA já documentada como pré-existente desde a v1.107.0, confirmado via `git diff` que as linhas adicionadas nesta versão somam 7 abre/7 fecha, balanceadas); revisão manual de todo ponto onde `.chat-item` é usado no repositório (grep completo nos 3 arquivos) confirmando que nenhum ficou sem o wrapper novo. Sem navegador disponível neste ambiente pra conferir visualmente — testado por revisão de código/lógica, sinalizado explicitamente como no padrão já estabelecido pra mudanças de frontend sem acesso a browser. |

| 1.122.0 | 03/09/2026 | Oficial | Segunda rodada de ajuste no mesmo print — usuário confirmou que o padrão de linha ficou melhor (v1.121.0), mas apontou que os 3 painéis de chat no mobile (lista/conversa/perfil) ainda apareciam como um cartão flutuante inteiro dentro da página, com borda/raio/sombra visíveis e uma margem em volta — pediu pra tirar toda borda e deixar ocupar a tela cheia. **Causa raiz**: no mobile, cada painel (`.chat-list`/`.chat-window`/`.guest-profile`) já vira a TELA INTEIRA sozinho quando ativo (mecanismo `data-mobile-view` de troca de painel único, existente desde antes) — mas continuava com a classe `.card` puxando border-radius/border/box-shadow/padding de 24px, então mesmo sendo "a tela inteira" ainda parecia uma caixa arredondada boiando dentro da margem de `.main` (20px topo, 18px lateral, 22px embaixo no mobile). **Fix cirúrgico, sem tocar `.main`/`.topbar` (compartilhados por TODAS as páginas do app, não só chat)**: nova regra `.main.chat-fullscreen .chat-list/.chat-window/.guest-profile` com margem negativa cancelando exatamente o padding lateral/inferior de `.main` (`margin:0 -18px -22px` + `width:calc(100% + 36px)` + `height:calc(100% + 22px)`), zerando border-radius/border/box-shadow/background — escolhida margem negativa em vez de reescrever `.main`/`.topbar` porque essas classes são a moldura de TODO o app (Dashboard, Reservas, Financeiro etc.), mexer nelas globalmente arriscaria quebrar página que não tem nada a ver com chat. `.chat-list` zera padding lateral por completo (cada `.chat-item` já tem o próprio padding interno desde a v1.121.0, não perde respiro nenhum); `.chat-window`/`.guest-profile` mantêm 16px de padding próprio (reduzido dos 24px do `.card` original) porque bolha de mensagem e campo de perfil não têm padding embutido, zerar totalmente colaria o conteúdo na borda da tela. Especificidade de 3 classes (`.main.chat-fullscreen .chat-list`) já vence `.card.chat-list` (2 classes) sem precisar prefixar por `#chatShell`/`#supportShell`/`#chats` como as regras de visibilidade vizinhas — aqui é tratamento visual igual pros 3 shells, não uma condição por página, então uma regra só cobre todos. `.chat-fullscreen` já era alternado por JS tanto em `admin.html` (abas Meu chat/Suporte) quanto `dashboard.html` (aba Chats) há tempo, confirmado sem mudança de JS necessária — só CSS. Testado: balanceamento de chaves/colchetes; divergência de parênteses em `app.css` permanece exatamente 1 (a mesma pré-existente desde a v1.107.0 — confirmado via `git diff` que as 11 linhas adicionadas nesta versão somam 11 abre/11 fecha, balanceadas). Sem navegador disponível neste ambiente — testado por revisão de código/CSS, não visualmente; usuário avisado que, se a conversa (janela de mensagens) ou o perfil do hóspede ainda parecerem "encaixotados" no mobile, é só mandar print de novo pra estender o mesmo ajuste. |

| 1.123.0 | 03/09/2026 | Oficial | Início da revisão completa de emojis pedida pelo usuário ("nenhum emoji feio, tudo no padrão StayFlow azul") — primeiro lote de um projeto multi-versão. Auditoria dedicada (agente de exploração) mapeou o tamanho real do trabalho antes de começar: **81 emojis distintos, ~500 ocorrências reais no código** (fora ~1.400 repetições que são só o mesmo texto traduzido em 11 idiomas) espalhados por `dashboard.html`/`admin.html`/páginas avulsas. Achado importante: o menu lateral principal (`dashboard.html`/`admin.html`) já é 100% livre de emoji — usa SVG (`viewBox="0 0 24 24"`, `stroke:currentColor`, sem preenchimento) desde sempre, esse é o padrão "bom" a replicar. Decisão de direção confirmada com o usuário: ícone SVG no mesmo estilo do menu (não emoji recolorido por CSS, que fica inconsistente entre Apple/Windows/Android e quebra o acabamento "premium" já buscado no inbox). **Este lote**: os 3 arquivos que quebravam o PRÓPRIO padrão de SVG do produto — `admin-hostel.html`/`admin-list.html` (mini-menu 🛠/🏨/✈️) e `Login.html` (botão "🛠 StayFlow — Admin") — convertidos pros mesmos ícones SVG (casa/prédio/avião) já usados no menu principal, reaproveitando os MESMOS paths (consistência automática). De brinde, consolidado `.hostel-avatar` (que tinha 🏨 em `dashboard.html` e 🏢 em `admin.html` — dois emojis diferentes pro mesmo conceito) num ícone de prédio único compartilhado via CSS (`.hostel-avatar svg`), e `KIND_ICONS`/`kindIcon()` em `admin.html` (mapa de ícone por tipo de conta — hospedagem/agência/imobiliária, usado em 7 lugares incluindo o avatar do Suporte da v1.121.0) convertido de emoji pra SVG, com tamanho em `1em` (não px fixo) pra herdar automaticamente o `font-size` de cada contexto onde aparece, sem precisar de variante por lugar. **Achado de segurança evitado no caminho**: a linha do dono/contato em `admin-hostel.html` (nome/e-mail/telefone/endereço do responsável pela hospedagem) usava `.textContent` — pra acrescentar ícone SVG precisei trocar pra `.innerHTML`, e como esses campos vêm de dado preenchido pelo próprio usuário no cadastro (não é conteúdo controlado pelo código), adicionei um `escapeHtml()` novo antes de interpolar, evitando abrir uma injeção nova ao fazer a troca (mesma classe de risco já corrigida pra hóspede na v1.39.0, aqui prevenida antes de existir). Testado: balanceamento de chaves/parênteses/colchetes e crases nos 6 arquivos tocados; varredura com regex de emoji Unicode confirmando ZERO emoji restante nos 3 arquivos alvo deste lote (`admin-hostel.html`/`admin-list.html`/`Login.html`); grep confirmando os alvos específicos deste lote (`hostel-avatar`, `KIND_ICONS`) sem nenhuma ocorrência antiga sobrando. Seguem ~78 emojis/~490 ocorrências pra próximos lotes — maior deles é o badge "✅ Conectado" sozinho (201 ocorrências, praticamente um componente só repetido), fica como próxima versão. |

| 1.124.0 | 03/09/2026 | Oficial | Revisão de emojis — lote 2: o badge "✅ Conectado/Ativado/Configurado", maior item isolado da auditoria (187 ocorrências reais confirmadas: 14 chaves i18n × 11 idiomas em `i18n-dashboard-data.js` + 3 chaves × 11 idiomas no dicionário inline de `admin.html`). **Abordagem**: em vez de reescrever a estrutura HTML/JS de cada um dos 15 pontos de chamada (que exigiria trocar `.textContent` por `.innerHTML` em todo lugar, superfície de risco bem maior), o emoji foi retirado da PRÓPRIA STRING traduzida (script mecânico, `"✅ Conectado"` → `"Conectado"` nas 11 línguas, mesma técnica de inserção/remoção já usada a sessão inteira) e o ícone de check virou responsabilidade só do CSS: nova classe `.settings-summary-card .settings-summary-desc.is-connected` que pinta o texto em `var(--green)` e desenha um ícone de check via `mask`/`-webkit-mask` (SVG embutido como data URI, cor controlada 100% por `background`, sem depender de fonte de emoji nenhuma) — JS só precisou ganhar UMA linha nova por ponto de chamada (`summaryDesc.classList.toggle("is-connected", condição)`), reaproveitando a MESMA condição booleana que já decidia qual texto mostrar. Aplicado nos 15 pontos reais: 10 cards `.settings-summary-card` no `dashboard.html` (WhatsApp, Meu WhatsApp, Facebook, Instagram, Mercado Pago, Nuvemshop, Tokko, Beds24, Webhook de saída, Câmeras de segurança patrimonial) via a classe CSS nova; 3 pontos sem esse wrapper (status de token do WhatsApp dentro do modal, e os 2 cards de comunicação da persona StayFlow em `admin.html`) via `.style.color` direto (mesmo efeito visual, sem precisar estender a classe CSS pra fora do padrão `.settings-summary-card`); 2 pontos compostos/já com feedback próprio (resumo de notificações push, disponibilidade de espaço de evento) só tiveram o emoji retirado do texto, sem ícone novo, por já terem sua própria lógica de cor ou não se encaixarem no padrão binário conectado/desconectado. De brinde, aproveitando que já estava mexendo nos pontos vizinhos: `settings.whatsapp.tokenMissing`/`events.availability.busy` (⚠️, par de aviso dos textos "Conectado"/"disponível" que acabaram de perder o ✅) também tiveram o emoji retirado das 11 traduções, para não deixar metade de um par de estados arrumada e a outra metade feia. 187 chaves de tradução tiveram só o VALOR alterado (emoji removido do início da string) — nenhuma chave nova, nenhuma removida, paridade nos 3 dicionários (1.583/91/295) inalterada. Testado: paridade de chaves nos 11 idiomas (`tools/check_i18n_parity.py`), balanceamento de chaves/parênteses/colchetes/crases em `dashboard.html`/`admin.html`/`i18n-dashboard-data.js`/`app.css` (divergência de parênteses do `app.css` seguindo pré-existente, confirmada via `git diff` que as 7 linhas adicionadas somam 7/7 balanceadas), grep confirmando ZERO `✅` restante nos 3 arquivos tocados. Seguem ~77 emojis/~300 ocorrências pra próximos lotes. |

| 1.125.0 | 03/09/2026 | Oficial | **Bug crítico de cache encontrado e corrigido**: usuário reportou (com print) que o ajuste de tela cheia no mobile do "Meu chat" (v1.122.0) continuava com a mesma "caixa flutuante" de antes, apesar de já publicado. Investigação da regra CSS em si (`.main.chat-fullscreen .chat-list`) confirmou que a lógica estava correta (especificidade de 3 classes vencendo `.card.chat-list` de 2, nenhuma regra com ID competindo nas propriedades relevantes, aninhamento de chaves do bloco `@media` verificado manualmente linha a linha) — mas o print mostrava claramente as mudanças da v1.121.0 (avatares, linha borda-a-borda) já ativas, então não era simplesmente "nada carregou". Causa raiz real: **nenhum arquivo estático (`static/css/app.css`, `tokens.css`, `reset.css`, `landing.css`, `auth.css`, os `assets/js/*.js` compartilhados) tinha cache-busting nenhum** — `<link href="static/css/app.css">` sem query string, servido por `send_from_directory` sem cabeçalho `Cache-Control` explícito. Isso significa que o navegador do celular pode ter ficado servindo uma versão intermediária de `app.css` (já com a v1.121.0, mas anterior à v1.122.0) por tempo indefinido, sem nunca buscar a versão nova de verdade — mesma classe de bug que um comentário já existente em `sw.js` alertava ter acontecido antes nesta mesma sessão ("servir JS/HTML desatualizado depois de um deploy já foi um problema real"), só que dessa vez em CSS, não JS/HTML. **Fix**: script mecânico adicionou `?v=1125` em toda referência a CSS/JS compartilhado nas 7 páginas que os usam (`dashboard.html`, `admin.html`, `admin-hostel.html`, `admin-list.html`, `index.html`, `Login.html`, `planos.html`) — 29 referências no total. Convenção daqui pra frente: esse número precisa subir a cada mudança relevante nesses arquivos compartilhados, senão o mesmo problema volta a acontecer silenciosamente. Testado: balanceamento de chaves/parênteses/colchetes nos 7 arquivos; confirmado que o roteamento do Flask (`@app.route("/static/<path:filename>")`, `Werkzeug`) ignora query string na hora de casar a rota, então `?v=1125` não quebra o backend, só afeta a chave de cache do navegador. Recomendado ao usuário fazer um refresh completo (não só reabrir a aba) depois do deploy pra garantir que o HTML novo (que já referencia os assets com `?v=1125`) seja buscado. |

| 1.126.0 | 03/09/2026 | Oficial | Resync automático do Tokko Broker acelerado de 6h pra 15min (`app.py::_tokko_resync_loop`) — usuário, se preparando pra reunião com a indicadora do setor imobiliário (Julia de Luna), achou 6h de atraso pra um imóvel vendido/alterado refletir na StayFlow tempo demais. Mudança de uma constante só (`time.sleep(21600)` → `time.sleep(900)`), alinhando com o mesmo ritmo já usado por `_late_arrival_alert_loop` (alertas de atraso/no-show), já validado nesta mesma arquitetura de threads em background como frequência segura de rodar em paralelo nos 3 workers do gunicorn sem sobrecarregar nada. Sem mudança de schema/rota — o mecanismo de sync em si (`resync_all_tokko_properties`, leitura via API do Tokko, upsert idempotente em `portfolio_items`/`real_estate_details`) continua exatamente igual, só a cadência mudou. Testado: `ast.parse()` confirmando sintaxe válida; grep confirmando nenhuma referência residual ao valor antigo (6h/21600) fora do comentário histórico que documenta a mudança. |

| 1.127.0 | 03/09/2026 | Oficial | Quarta rodada de auditoria de vazamento de contexto hospedagem→imobiliária (depois das v1.100/101/102), motivada por dois prints reais do usuário (checkbox de permissão "parking"/"scheduling" cru no modal de exceção individual de Equipe, e página de Relatórios inteira vazia/com rótulo de hospedagem pra conta de imobiliária). Auditoria dedicada (agente de exploração) encontrou **11 pontos reais**, dos quais os de maior visibilidade foram corrigidos nesta versão. **Causa raiz do achado do print** (`get_permission_detail`, usada no modal "Permissões de [pessoa]"): iterava `ALL_PERMISSIONS` (24 chaves) sem filtro nenhum, diferente de `/permissions/catalog` (usada pra criar cargo novo) que já filtrava corretamente via `permissions_for_account_kind()` — dois caminhos calculando o mesmo conceito de formas diferentes; como o catálogo (com o rótulo certo) não incluía as chaves lodging-only pra agência, o frontend caía no fallback de mostrar a CHAVE CRUA em inglês. **Fix mais profundo que o necessário só pra esse modal**: em vez de só filtrar `get_permission_detail`, o filtro foi aplicado na função CENTRAL `get_effective_permissions()` (database.py) — usada também pelo card de contagem "N permissões" em Equipe, por `routes/auth.py` (sessão), por `utils/tenant.py` (gate de rota real) e por `services/ask_agent_service.py` (ferramentas oferecidas à IA). Raiz do vazamento: a role "Admin" é criada com `ALL_PERMISSIONS_STR` (todas as 24) pra QUALQUER `account_kind`, então uma imobiliária tinha `parking`/`scheduling`/`events` etc. genuinamente gravado na própria role — sem esse filtro central, o vazamento se propagava pra tudo que consome essa função. Testado em SQLite isolado: imobiliária não vaza nenhuma permissão lodging-only nem em `get_effective_permissions` nem em `get_permission_detail`; hostel lodging continua com as 24 permissões completas (zero regressão). **Demais correções do lote**: caixa de mensagem manual da aba Chats ("Escrever mensagem como recepção...") ganhou variante "...como equipe" pra agência; card "Câmbio (pagamento em moeda estrangeira)" (Financeiro) gated `data-required-account-kind="lodging"` (conceito de troco em dinheiro estrangeiro não existe em venda/locação de imóvel); página de Relatórios inteira (construída 100% sobre a tabela de reservas, sem nenhum gate) escondida do menu pra agência (`data-hide-for-account-kind="promoter,agency"`) até uma versão própria com métricas relevantes ser construída; fallback "Hóspede" em 3 notificações push (`routes/chat.py` × 2, `services/decision_engine.py` × 2) trocado por `agency_guest_noun()` (singular Cliente/PAX conforme categoria, mesmo critério de `guestFallbackName()` do frontend); Opportunity Center (`stayflow-live.js`) parou de mostrar o enum cru (`opportunity.type`) quando a descrição vem vazia, passou a usar `intentLabel()`; botão "Gerar cobrança" não aparece mais pra oportunidade de imobiliária mesmo se a IA classificar como "upsell" por engano (imóvel próprio nunca é cobrado por link de pagamento, mesmo critério de `isOwnCatalogSuggestion()`); checkbox de notificação "Hóspede com problema..." em Configurações ganhou variante com o substantivo certo pra agência. 1 chave i18n nova em 11 idiomas (1.583→1.584). Testado: paridade de chaves via `tools/check_i18n_parity.py`, balanceamento de chaves/parênteses/colchetes em `dashboard.html`/`stayflow-live.js`/`i18n-dashboard-data.js`, `ast.parse()` dos 3 arquivos Python tocados. Restam ~4 pontos de menor visibilidade da auditoria (descrições de ferramenta da IA com "hóspede"/"hostel" hardcoded mesmo já filtradas por permissão, papel do sistema em `decision_engine.py` dizendo "hospitality operations" sempre) — mais sutis, ficam pra um lote futuro sem a urgência dos achados visuais desta versão. |

| 1.128.0 | 03/09/2026 | Oficial | Layout de Chats no desktop deixa de ser 3 cartões separados com espaço entre eles e vira um painel único — usuário mandou uma imagem gerada por IA (referência de estilo "inbox premium", não uma tela real do produto, confirmado explicitamente por ele) reclamando que a janela de conversa ainda passava impressão de "presa numa caixa". Investigação confirmou: a v1.121.0/v1.122.0 já tinham resolvido isso na LISTA (linha cheia em vez de item-cartão) e no MOBILE (painéis full-screen sem borda), mas o `.chat-layout` do DESKTOP nunca tinha sido tocado — cada uma das 3 colunas (lista/conversa/perfil) era seu próprio `.card` com `gap:var(--gap)` (24px) entre elas, exatamente o efeito de "3 caixas soltas boiando lado a lado". **Fix**: `.chat-layout` ganhou a moldura própria (fundo, borda, raio, sombra) que as 3 colunas tinham individualmente antes, com `gap:0`; as colunas perderam a moldura própria e ganharam divisória fina (`border-right`) entre si, replicando o mesmo princípio já usado na lista (v1.121.0) — um painel contínuo com linha fina separando seções, não caixas separadas. **Cuidado necessário pra não quebrar o mobile**: como `.chat-layout` sozinho ganhou border/background/box-shadow/border-radius novos, e o mobile (`.main.chat-fullscreen`, v1.122.0) depende de margem NEGATIVA nos painéis internos pra "vazar" pra fora do container e ir borda-a-borda, o `overflow:hidden` novo do desktop (usado pra arredondar os cantos do painel único) CORTARIA esse vazamento no mobile se não fosse cancelado — nova regra `.main.chat-fullscreen .chat-layout{background:transparent;border:none;box-shadow:none;border-radius:0;overflow:visible}` especificamente dentro do breakpoint mobile, garantindo que o tratamento novo de desktop e o tratamento já existente de mobile (v1.122.0) não competem entre si (cada um só é visível na largura de tela onde faz sentido). Testado: balanceamento de chaves/parênteses/colchetes (a divergência de parênteses do arquivo, pré-existente desde a v1.107.0, confirmada inalterada — as 13 linhas adicionadas somam 13/13 balanceadas). Sem navegador disponível neste ambiente pra conferir visualmente o resultado — testado por revisão de CSS/especificidade linha a linha, sinalizado explicitamente ao usuário. |

| 1.129.0 | 04/09/2026 | Oficial | Duas mudanças no mobile: (1) fix de bug real de corte de conteúdo na aba Chats, achado via print; (2) nova barra de atalhos fixa, ideia validada a partir da v1.128.0. **Bug corrigido**: usuário reportou avatar/texto cortados do lado na aba Chats (não em Meu chat/Suporte). Causa raiz: a v1.122.0 dava fuga de margem negativa (borda-a-borda) pra `#realChatList`, mas a aba Chats do dashboard (diferente do admin.html) tem um wrapper extra ao redor dele — `.chat-list-wrap` (v1.116.0, carrega a busca de contato) — que é quem de fato ocupa a célula do grid dentro do padding de `.main`; `#realChatList` sozinho só conseguia fugir até a borda do PRÓPRIO wrapper, que continuava preso dentro do padding de `.main`, cortando o conteúdo. Fix: a fuga de margem passou pro `.chat-list-wrap` (o container real); `#realChatList` (já dentro de um pai borda-a-borda) volta a ser 100% normal — fuga dupla empilhada era o que causava o corte. `#chatGuestList`/`#supportThreadList` (admin.html, sem wrapper) continuam intactos pela regra genérica `.chat-list` já existente. **Barra de atalhos nova** (`.mobile-tabbar`, só mobile): soma ao menu hambúrguer completo (não substitui — a StayFlow tem seções demais pra caber em 5 abas fixas), com 3 atalhos pros itens mais usados (Dashboard/Chats/Oportunidades) + "Mais" abrindo o menu de sempre (`toggleSidebar()`). Mesmos atributos `data-hide-for-account-kind`/`data-required-permission` dos botões espelhados no menu lateral, herdando a visibilidade certa por tipo de conta sem JS novo. `setActiveMenu()` estendida pra marcar o botão ativo também na barra nova. Espaço reservado via `.page{padding-bottom:70px}` dentro do breakpoint mobile — como o reset global já é `box-sizing:border-box`, esse padding é DESCONTADO da altura declarada (não somado por cima), então o `.chat-layout` (`height:100%`) encolhe sozinho pra sobrar espaço pra barra, sem precisar de regra especial só pra Chats. 2 chaves i18n novas (rótulos curtos "Oportunidades"/"Mais" pra caber na aba estreita, em vez de reaproveitar "Opportunity Center" que estouraria a largura) em 11 idiomas (1.584→1.586). Testado: paridade de chaves, balanceamento de chaves/parênteses/colchetes em `dashboard.html`/`app.css`/`i18n-dashboard-data.js`, grep confirmando as 2 chaves novas presentes no dicionário `pt`. Sem navegador disponível — testado por revisão de CSS/especificidade, sinalizado como sempre. Usuário avisado: ideia validada como "se não gostar, tira" — reversível, não é decisão definitiva de produto ainda. |

| 1.130.0 | 04/09/2026 | Oficial | Duas features novas pro setor de imobiliária, pedidas pelo usuário se preparando pra reunião com a Julia (indicadora do setor): **Agenda de Visitas** (agendamento de visita a imóvel) e **captação de lead pela IA** — motivadas em parte pela pesquisa de mercado sobre o Imoview (Universal Software), que tem módulos equivalentes (Agendador nativo + Imoview PRÉ) cobrados à parte por usuário/contrato. **Agenda de Visitas** (`property_visits`, nova tabela: `hostel_id`, `portfolio_item_id`, `guest_id`, `membership_id`, `client_name`, `client_phone`, `scheduled_at`, `duration_minutes`, `status`, `notes`): conflito de horário checado POR CORRETOR (`membership_id`), não por imóvel — dois corretores diferentes podem levar clientes distintos no mesmo imóvel no mesmo horário, mas o mesmo corretor não pode ter duas visitas sobrepostas (`check_visit_conflict`/`_visit_overlaps`, database.py). Status muda por transição (`scheduled`→`completed`/`cancelled`/`no_show`), nunca por delete. CRUD completo (`create_property_visit`, `get_property_visit`, `list_property_visits`, `update_property_visit_status`, `reschedule_property_visit` — reagendar reusa o mesmo checker de conflito, excluindo a própria visita) + 5 rotas em `routes/portfolio.py` (`GET/POST /portfolio/visits`, `GET /portfolio/visits/brokers`, `PATCH .../status`, `PATCH .../reschedule`), todas atrás de `_require_real_estate()` (mais estrito que `_require_agency` — exige `account_kind=='agency' AND agency_category=='imobiliaria'`). **Tool de IA `schedule_property_visit`** (`services/ai_service.py`, exclusiva de `agency_category=='imobiliaria'` via `REAL_ESTATE_TOOLS`): a IA agenda a visita DE VERDADE na conversa quando o cliente concorda em imóvel+horário específicos, em vez de só prometer retorno da equipe — prompt de fechamento do imobiliária reescrito pra instruir isso explicitamente, com fallback pro texto antigo ("equipe retorna em breve") se o agendamento não for possível na hora. Pré-requisito: `get_offerings` (usada por toda conta agency) passou a devolver `id` de cada item — antes só tinha nome/descrição/preço, e a IA não tinha como referenciar qual imóvel exato agendar. **Captação de lead** (`leads`, tabela já existente no schema desde antes mas nunca usada de verdade — zero CRUD, zero rota, zero consumidor): ganhou CRUD real (`create_lead`, `get_lead`, `list_leads` — ordenado por `created_at DESC, id DESC`, tie-break necessário porque `CURRENT_TIMESTAMP` tem resolução de segundo e leads podem nascer no mesmo segundo — `update_lead_status`) e rotas `GET /leads` + `PATCH /leads/<id>/status` em `routes/opportunities.py` (reaproveitando a permissão `opportunities`, já que lead é conceitualmente parte do mesmo funil). **Tool de IA `capture_lead`** — deliberadamente GENÉRICA, em `AGENCY_TOOLS` (não em `REAL_ESTATE_TOOLS`): qualquer categoria de agência (turismo, aluguel de carro/bike/equipamento, imobiliária) se beneficia de salvar nome+contato+interesse pro time seguir mesmo quando o cliente não fecha na hora — instrução de quando chamar foi pro skeleton COMPARTILHADO do prompt (`_AGENCY_PROMPT_SKELETON`), não duplicada em cada categoria, seguindo o mesmo princípio já documentado no código ("espinha dorsal idêntica em todas — são garantias do produto, não sabor de nicho"). **Frontend**: nova aba "Agenda" no menu (só aparece pra `account_kind=agency` + `agency_category=imobiliaria`) — primeiro item de menu lateral a usar `data-required-agency-category`, que até agora só existia em cards soltos (`applyAccountKindVisibility`, que pula `.menu` de propósito); estendido `hideNavItemsWithoutPermission()` pra aceitar esse atributo também nos botões do menu. Página agrupada por dia (Hoje/Amanhã/data por extenso), cards com horário+imóvel+cliente+corretor, select inline de status e botão "Reagendar" (abre modal com só o campo de data/hora). Modal "Nova visita" behind-button (imóvel/cliente/telefone/data-hora/corretor via `/portfolio/visits/brokers`/observações), reaproveitando `eventsToBackendDatetime`/`eventsFromBackendDatetime`/`formatEventDateTime` (já existiam pra Eventos, mesmo formato `datetime-local`↔backend). Seção "Leads capturados" nova dentro do Opportunity Center (não uma aba própria — evita fragmentar mais o menu), tabela simples com select de status inline. CSS novo: `.agenda-day-group`/`.agenda-visit-card` (borda esquerda colorida por status) + ajuste mobile (`flex-wrap` nos cards). **i18n**: 38 chaves novas (nav.agenda, leads.*, agenda.*) em 11 idiomas = 418 traduções, 1.586→1.624 chaves, paridade confirmada via `tools/check_i18n_parity.py`. **Testado**: suite isolada em SQLite temporário (`STAYFLOW_DATA_DIR` apontando pra diretório temp, nunca o banco real) cobrindo conflito por corretor (bloqueia overlap do mesmo corretor, permite overlap de corretores diferentes, visita `completed` não bloqueia mais o horário), reagendamento (bloqueia conflito com visita ainda `scheduled`, aceita reagendar pro próprio horário atual), CRUD de leads (isolamento multi-tenant por `hostel_id`, filtro por status, ordenação) — 2 bugs reais pegos e corrigidos nessa rodada: `list_leads` sem tie-break de `id` na ordenação (corrigido) e um teste mal desenhado meu (não bug de produto) que testava conflito de reagendamento contra uma visita já `completed`. App inteiro importado com sucesso (`import app`), confirmando registro de todas as 5 rotas de visita + 2 rotas de lead sem colisão com as rotas antigas de `/stayflow-admin/leads` (CRM interno da StayFlow, tabela `stayflow_leads`, sistema totalmente diferente). `ast.parse()` em todos os arquivos Python tocados. Sem teste de HTTP end-to-end com sessão real (autenticação usa token opaco em tabela própria, não sessão assinada do Flask) — coberto por revisão manual do contrato de cada rota contra o mesmo decorator `@require_permission` já usado em produção. |

| 1.131.0 | 04/09/2026 | Oficial | Fecha os 3 achados de menor visibilidade deixados em aberto na auditoria de imobiliária da v1.127.0. **(1) Descrições de tool do Ask StayFlow com "hóspede" hardcoded**: `get_dashboard_overview`/`get_guests`/`find_guest`/`get_guest_details`/`get_chats_overview`/`propose_guest_message`/`cancel_guest_message` (todas SEM permissão em `LODGING_ONLY_PERMISSIONS`, ou seja, genuinamente oferecidas a conta agency) tinham o texto que o MODELO lê ainda dizendo "hóspede" hardcoded, mesmo já corretamente filtradas por permissão — risco de a IA espelhar esse substantivo errado na própria resposta pro admin da agência. Corrigido com `_AGENCY_TOOL_DESCRIPTION_OVERRIDES` (dict tool→template com `{guest_noun_lower}`/`{singular_lower}`), aplicado só quando `account_kind=='agency'`, construindo specs NOVOS (nunca mutando `TOOLS_CATALOG`, que é módulo-level e compartilhado por toda requisição futura de qualquer conta — verificado com teste de identidade). `get_reports_summary` (fala de "funil hóspedes -> reservas confirmadas", conceito sem equivalente de agência ainda) excluído por nome da lista de tools de agência, mesmo critério já usado pra esconder a aba Relatórios do menu desde a v1.127.0. **(2) `decision_engine.py` com role de sistema fixo "hospitality operations"**: a função já calculava `business_context` (texto certo por `agency_category`, usado em outro lugar do prompt) mas o role da mensagem system pro modelo classificador ainda tinha o texto fixo hardcoded — trocado pra usar a mesma variável via f-string. **Achado extra fora da lista original**, pego lendo a função inteira pra fazer o fix acima: o log de conversa enviado pro classificador rotulava toda linha do hóspede/cliente como `"Hospede:"` e da equipe como `"Recepcao/IA:"`, hardcoded, mesmo pra conta agency — corrigido com `speaker_guest_label`/`speaker_staff_label` (PAX/Cliente + "Equipe/IA" pra agência). **(3) Fallback de notificação push de reserva criada**: avaliado e confirmado que NÃO é um bug real — reservas são feature `LODGING_ONLY_PERMISSIONS`, nunca alcançável por conta agency por construção (o subsistema de reservas inteiro não existe pra agência), então o fallback "Hóspede" ali é sempre correto no único tipo de conta que consegue chegar nesse código. Nenhuma mudança feita nesse ponto. Testado: `ast.parse()` nos 2 arquivos tocados, teste isolado confirmando que a substituição de descrição de tool NÃO muta `TOOLS_CATALOG` (comparação de identidade antes/depois) e que `get_reports_summary` some da lista pra agency. |

| 1.132.0 | 04/09/2026 | Oficial | Primeiro item da fila inspirada na pesquisa do Kenlo (LYA gera descrição/título de imóvel com IA): botão "✨ Gerar com IA" no modal Novo/Editar item do Portfólio, gera título+descrição de marketing a partir dos campos JÁ preenchidos na tela — funciona até em item NOVO, ainda não salvo (manda os valores atuais do formulário, não exige `item_id`). Deliberadamente construído GENÉRICO pra qualquer categoria de agência (imóvel, tour, aluguel de bike/equipamento, produto), não exclusivo de imobiliária — mesma disciplina de "espinha dorsal idêntica, não sabor de nicho" já usada nas tools de IA. `generate_portfolio_item_description(fields)` (novo, `services/ai_service.py`): monta uma lista de fatos só com os campos que TÊM valor (nome, categoria, preço, operação, localização, quartos/banheiros/área, condomínio/IPTU, comodidades, e o rascunho de descrição já escrito pela pessoa, se houver) e pede pro modelo (gpt-4.1-mini) um título curto + descrição de 2-4 frases em JSON, com regra explícita de nunca inventar característica/número/localização fora dos fatos dados. Rota `POST /portfolio/items/generate-description` (`routes/portfolio.py`), atrás de `@require_permission("portfolio")` + `_require_agency()`. Resultado só PREENCHE os campos nome/descrição pra revisão — nunca salva sozinho, mesmo princípio de `propose_guest_message`/toda geração de texto por IA no produto já ter revisão humana antes de virar definitivo. 4 chaves i18n novas em 11 idiomas (1.624→1.628). Testado: `ast.parse()`, app inteiro importado confirmando a rota nova registrada, teste isolado com o client da OpenAI mockado (sem chamar a API de verdade) cobrindo: erro sem nome informado, parsing de resposta com fence de markdown (` ```json `), e confirmação de que os fatos informados (operação/localização/comodidades) realmente aparecem no prompt montado. Balanceamento de chaves/parênteses/colchetes no bloco novo de `dashboard.html`, paridade de i18n via `tools/check_i18n_parity.py`. |

| 1.133.0 | 04/09/2026 | Oficial | Terceiro item da fila do Kenlo: roteamento automático de lead por FILA (round-robin) — Kenlo cita "plantão/fila/região/tipo/time" como critérios de roteamento; implementado o de fila agora (o mais genérico e sem exigir nenhuma configuração nova da pessoa), região/plantão ficam registrados como próximo passo (precisam de definição de produto ainda inexistente: tag de bairro por corretor, escala de plantão). **Arquitetura deliberadamente sem tabela de estado/cursor própria**: `_next_broker_for_lead_routing(hostel_id)` sempre atribui pro corretor ATIVO com MENOS leads recebidos até agora (`COUNT` por `membership_id`, empate resolvido por `membership_id` menor) — se autoequilibra sozinho mesmo em uso intermitente (diferente de um ponteiro round-robin fixo, que "atrasaria" alguém em dias sem lead nenhum). Coluna `membership_id` nova em `leads` (nullable — conta sem nenhum corretor ativo no momento não trava, lead fica sem atribuição pra qualquer um assumir manualmente). `create_lead()` só chama o roteamento automático quando `membership_id` não foi passado explicitamente — a tool de IA `capture_lead` nunca informa corretor, então todo lead capturado pela IA passa pela fila; chamadas futuras que já souberem o corretor certo (ex: se um dia a IA identificar o corretor da conversa) continuam podendo forçar. Reatribuição manual: `update_lead_broker()` + rota `PATCH /leads/<id>/broker`, sempre disponível pra sobrepor a fila (corretor de férias, erro). `GET /leads/brokers` nova (lista membros ativos, mesmo padrão de `/portfolio/visits/brokers` da v1.130.0, mas sob a permissão `opportunities` em vez de `portfolio` — quem vê Leads não necessariamente vê Portfólio). `get_lead`/`list_leads` ganharam `LEFT JOIN` pra trazer `broker_name` resolvido, evitando N chamadas do frontend. **Frontend**: coluna "Corretor" nova na tabela de Leads capturados (Opportunity Center), select inline (mesmo padrão de status) alimentado por `/leads/brokers`, carregado em paralelo com `/leads` via `Promise.all`. 2 chaves i18n novas em 11 idiomas (1.628→1.630). Testado em SQLite isolado: 3 corretores ativos recebem 1 lead cada quando a fila está vazia; corretor INATIVO nunca recebe; 4º lead vai pro que tem menos (empate por id); `broker_name` presente via JOIN em `get_lead`/`list_leads`; reatribuição manual funciona e sobrepõe corretamente; `membership_id` explícito passado pro `create_lead` é respeitado (não força roteamento); conta sem nenhum corretor ativo não quebra, só fica `None`. `ast.parse()`, app importado confirmando as 2 rotas novas registradas sem colisão, paridade i18n, balanceamento de chaves/parênteses/colchetes em `stayflow-live.js`. |

| 1.133.1 | 04/09/2026 | Oficial | **Fix crítico de produção**, usuário reportou "me bugou o site" durante a sequência v1.130.0-v1.133.0. Causa raiz: `app.css`/`stayflow-live.js`/`i18n-dashboard-data.js` foram alterados repetidas vezes ao longo dessas 4 versões, mas a query string de cache-busting (`?v=`) ficou parada em `1125` — convenção já estabelecida desde antes desta sessão ("bumpar sempre que asset compartilhado muda"), esquecida ao longo de toda a sequência de features desta sessão. Navegador podia continuar servindo uma versão em cache de um desses 3 arquivos enquanto `dashboard.html`/`admin.html` (servidos frescos) já referenciavam elemento/classe/chave i18n novos que só existem na versão atualizada — mistura de HTML novo com asset velho, sintoma clássico de cache-busting esquecido. Corrigido bumpando `?v=1125` → `?v=1133` em `dashboard.html` (as 3 referências) e em `admin.html`/`admin-list.html`/`admin-hostel.html` (que também carregam `app.css`, compartilhado). Scripts não tocados nesta sessão (`chats-live.js`, `i18n-core.js`) deliberadamente NÃO bumpados — bump é só pra asset que de fato mudou. Testado: balanceamento de chaves/parênteses de todos os 8 blocos `<script>` inline de `dashboard.html` (nenhum desbalanceado), balanceamento standalone de `app.css`/`stayflow-live.js`/`i18n-dashboard-data.js` (o único desvio, 1 parêntese a mais em `app.css`, é o mesmo achado pré-existente já confirmado inalterado desde a v1.107.0/v1.128.0, não é regressão nova). Publicado imediatamente nos 2 repos por ser bug de produção ativo. Se o sintoma persistir após o deploy, o próximo passo é o usuário fazer hard-refresh (Ctrl+Shift+R) — é possível que o PRÓPRIO `dashboard.html`/`admin.html` (servido por `send_from_directory`, sem header `no-cache` explícito) também esteja em cache no navegador do usuário, o que só se resolve client-side. |

| 1.134.0 | 04/09/2026 | Oficial | **Fix de achado real de cliente em teste ao vivo**: Elaine (dona de imobiliária, testando a StayFlow no mesmo dia da reunião com a Julia) relatou que a IA anterior que ela usava "não identifica o momento certo de passar pro corretor — o cliente já foi atendido, já quer agendar visita e não é passado com corretor, acaba perdendo o cliente". Investigação confirmou que a StayFlow tinha exatamente essa mesma lacuna: `schedule_property_visit` (tool de IA, v1.130.0) criava a visita sem NUNCA atribuir `membership_id` — visita existia na Agenda, mas sem corretor dono, e sem notificação nenhuma pra ninguém saber que precisava agir. **Fix em duas partes.** (1) `_next_broker_for_lead_routing` generalizada pra `_next_broker_for_routing(hostel_id, count_table)` — mesma lógica de fila por contagem, agora parametrizada pela tabela (`leads` ou `property_visits`), cada uma com sua PRÓPRIA fila (não soma lead+visita — são cargas de trabalho diferentes). Nova `_next_available_broker_for_visit(hostel_id, scheduled_at, duration_minutes)`, mais esperta que o roteamento de lead: percorre os corretores ativos em ordem de fila (menos visita primeiro) e devolve o PRIMEIRO sem sobreposição de horário — de nada adiantaria atribuir pro corretor "da vez" se ele já tem outro compromisso, isso só trocaria "sem corretor" por "agendamento falha por conflito", perdendo o cliente de outro jeito. `create_property_visit()` agora chama isso sempre que `membership_id` não vem explícito — cobre tanto a tool de IA quanto o modal "Nova visita" quando a pessoa deixa em branco (rótulo do dropdown atualizado de "Sem corretor definido" pra "Atribuir automaticamente (recomendado)" nos 11 idiomas, pra refletir o comportamento novo). Só fica sem corretor quando literalmente TODOS os ativos têm conflito nesse horário exato (edge case raro) — nesse caso a visita ainda é criada (não trava o agendamento), só sem dono. (2) **Notificação push real**: `_notify_hostel_of_new_opportunity()` nova (best-effort, mesmo padrão de `notify_on_duty_staff_for_ticket` — falha no push nunca derruba a criação do registro), chamada tanto por `create_lead` quanto por `create_property_visit`, via `notification_type="opportunity"` (reaproveita a preferência que já existe em Configurações, ligada por padrão — lead/visita É uma oportunidade, não precisa de checkbox nova). Antes deste fix, um lead capturado ou visita agendada pela IA existia silenciosamente no banco até alguém abrir o painel por conta própria — exatamente o "perde o cliente" que a Elaine descreveu, mesmo com o roteamento automático da v1.133.0 já funcionando (atribuir sem avisar não resolve o problema na prática). Testado em SQLite isolado: visita sem corretor explícito sempre é auto-atribuída quando há corretor ativo livre; duas visitas no MESMO horário vão pra corretores DIFERENTES automaticamente (sem falso conflito); quando todos estão ocupados nesse horário a visita nasce sem corretor mas SEM lançar erro; empate de fila desempata por menor `membership_id`; corretor genuinamente menos carregado recebe a próxima quando não há empate; `membership_id` explícito com conflito real ainda levanta `ValueError` normalmente. Suítes de roteamento de lead e Agenda/leads da v1.130.0/v1.133.0 re-executadas sem regressão. App inteiro importado com sucesso (336 rotas). Publicado numa única leva (não repetidas vezes) depois do incidente da v1.133.0/v1.133.1 — lição levada a sério: não publicar em produção durante janela de demonstração ao vivo do usuário. |



\---



\# APRESENTAÇÃO



O \*\*STAYFLOW\_MASTER\_CONTEXT.md\*\* é a documentação oficial da StayFlow.



Este documento representa a principal fonte de verdade da empresa.



Seu propósito é preservar conhecimento, registrar decisões permanentes, orientar o desenvolvimento do produto e garantir consistência durante toda a evolução da plataforma.



Este documento faz parte do produto.



Ele deve evoluir junto com o software.



Sempre que uma decisão permanente alterar a arquitetura, o produto, a engenharia, a experiência do usuário ou qualquer componente estrutural da StayFlow, este documento deverá ser atualizado.



Nenhuma conversa possui prioridade sobre este documento.



Quando houver divergência entre qualquer informação e este Documento Mestre, prevalecerá sempre sua versão mais recente.



\---



\# COMO UTILIZAR ESTE DOCUMENTO



Este documento está dividido em duas partes.



\## PARTE I — FUNDAÇÃO



Define a identidade permanente da StayFlow.



Reúne missão, visão, princípios, cultura, filosofia de produto, filosofia de engenharia e regras permanentes.



Esses capítulos mudam pouco ao longo da vida da empresa.



Eles representam os fundamentos da StayFlow.



\---



\## PARTE II — ESPECIFICAÇÃO TÉCNICA



Documenta o estado real do software.



Toda evolução do produto deverá ser refletida nesta parte.



Ela registra oficialmente:



\- arquitetura;

\- backend;

\- frontend;

\- banco de dados;

\- APIs;

\- motores de inteligência;

\- funcionalidades;

\- roadmap;

\- histórico de evolução.



A Parte II deve refletir continuamente o estado atual do software.



\---



\# MANUTENÇÃO DO DOCUMENTO



Este Documento Mestre é permanente.



Seu crescimento deverá ocorrer através da atualização dos capítulos existentes.



Novos capítulos somente deverão ser criados quando uma nova área estrutural da StayFlow surgir.



Toda atualização relevante deverá também ser registrada no \*\*Registro Oficial de Evolução\*\*.



O objetivo é manter um documento organizado, confiável e preparado para acompanhar a empresa durante muitos anos.



\---



\# SUMÁRIO



\## PARTE I — FUNDAÇÃO



\- \[1. A StayFlow](#capitulo-1)

\- \[2. Princípios Fundamentais](#capitulo-2)

\- \[3. Filosofia de Produto](#capitulo-3)

\- \[4. Filosofia de Engenharia](#capitulo-4)

\- \[5. Cultura de Desenvolvimento](#capitulo-5)

\- \[6. Inteligência Artificial](#capitulo-6)

\- \[7. Padrões Permanentes](#capitulo-7)



\---



\## PARTE II — ESPECIFICAÇÃO TÉCNICA



\- \[8. Arquitetura Oficial](#capitulo-8)

\- \[9. Estrutura do Projeto](#capitulo-9)

\- \[10. Backend](#capitulo-10)

\- \[11. Frontend](#capitulo-11)

\- \[12. Banco de Dados](#capitulo-12)

\- \[13. APIs](#capitulo-13)

\- \[14. Motores de Inteligência](#capitulo-14)

\- \[15. Dashboard](#capitulo-15)

\- \[16. Funcionalidades Implementadas](#capitulo-16)

\- \[17. Roadmap Oficial](#capitulo-17)

\- \[18. Registro Oficial de Evolução](#capitulo-18)



\---



<a id="capitulo-1"></a>



\# 1. A STAYFLOW



\## Propósito



Construir o melhor Gerente Digital Inteligente para hotelaria do mundo.



A StayFlow existe para transformar Inteligência Artificial em uma ferramenta capaz de aumentar receita, reduzir trabalho operacional e melhorar continuamente a tomada de decisões em meios de hospedagem.



\---



\## Missão



Desenvolver uma plataforma capaz de compreender operações, interpretar contexto, apoiar decisões e automatizar processos de forma confiável, tornando a gestão mais inteligente, eficiente e rentável.



\---



\## Visão



Tornar a StayFlow a principal referência mundial em Inteligência Artificial aplicada à gestão da hotelaria.



Toda decisão estratégica, técnica ou de produto deve aproximar a empresa dessa visão.



\---



\## O Produto

\## Posicionamento Atual



A StayFlow é posicionada como um \*\*Sistema Operacional Inteligente para Hotelaria (AI Operating System for Hospitality)\*\*.



O Gerente Digital Inteligente permanece sendo a principal forma como o usuário percebe o produto, enquanto a plataforma integra inteligência, automação e operação em um único ambiente.





A StayFlow é uma plataforma de inteligência operacional.



Seu papel é atuar como um Gerente Digital Inteligente que observa continuamente a operação, interpreta acontecimentos, identifica riscos, encontra oportunidades, recomenda ações e automatiza processos quando apropriado.



A plataforma foi concebida para trabalhar ao lado do gestor, ampliando sua capacidade de decisão.



\---



\## Mercado-alvo: hospedagens de todo porte, não um nicho



\*\*Decisão permanente de posicionamento (registrada em 02/08/2026):\*\* a StayFlow nunca deve ser descrita, em nenhum material voltado para fora da empresa (marketing, App Review, documentação institucional, apresentações comerciais), como um produto nichado em hostels.



Hostel é apenas a \*\*primeira categoria de hospedagem atacada\*\* — por ser aquela a que o fundador tem acesso direto hoje para validar a operação com um cliente real. A ambição declarada do produto é ser o maior e mais completo software de hotelaria que existe, servindo hospedagens de todo porte: hostels, hotéis, pousadas e resorts, pequenos e grandes.



Essa decisão já foi aplicada na landing page (`index.html`) e na política de privacidade (`privacy.html`), substituindo linguagem nichada ("for hostels, hotels and pousadas") por linguagem abrangente ("hospitality businesses of every kind"). O piloto comercial em validação a partir de agosto de 2026 é, propositalmente, um hotel de grande porte (fora do nicho hostel), para comprovar essa ambição na prática.



\---



\## O que a StayFlow não é



A StayFlow não é definida por funcionalidades isoladas.



Ela não é apenas:



\- um chatbot;

\- um CRM;

\- um dashboard;

\- um PMS;

\- um sistema administrativo.



Esses recursos podem existir dentro da plataforma, porém representam apenas partes de um sistema muito maior.



O verdadeiro produto é a inteligência operacional construída sobre eles.



\---



\## Compromisso Permanente



Toda evolução da StayFlow deverá fortalecer quatro pilares fundamentais:



\- Inteligência;

\- Simplicidade;

\- Qualidade;

\- Evolução Contínua.



Esses pilares orientam permanentemente todas as decisões relacionadas ao produto.



\---



\## Decisões Consolidadas



\- A StayFlow desenvolve um Gerente Digital Inteligente.

\- Inteligência operacional representa o núcleo da plataforma.

\- O objetivo do produto é transformar dados em decisões.

\- A evolução do software é contínua.

\- A StayFlow serve hospedagens de todo porte; hostel é a primeira categoria atacada, não o mercado-alvo final — nunca deve ser descrita como produto nichado em hostel.

\- Este Documento Mestre representa a principal fonte de verdade da StayFlow.



\---



<a id="capitulo-2"></a>



\# 2. PRINCÍPIOS FUNDAMENTAIS



Os Princípios Fundamentais representam as regras permanentes que orientam todas as decisões da StayFlow.



Eles possuem prioridade sobre preferências individuais, escolhas técnicas ou decisões momentâneas.



Toda evolução do produto deve respeitar estes princípios.



\---



\## 2.1 Produto acima da tecnologia



Tecnologia é um meio.



O produto é o objetivo.



Frameworks, linguagens, bibliotecas e modelos de Inteligência Artificial poderão mudar ao longo dos anos.



A missão da StayFlow permanece.



Toda decisão técnica deve fortalecer o produto.



Nunca o contrário.



\---



\## 2.2 Inteligência acima de funcionalidades



A StayFlow não busca possuir o maior número de funcionalidades.



Busca possuir a maior capacidade de compreender operações, gerar contexto e apoiar decisões.



Sempre que houver conflito entre adicionar funcionalidades ou aumentar a inteligência do produto, a inteligência terá prioridade.



\---



\## 2.3 Valor acima de esforço



Toda implementação deve gerar valor claro.



Antes de iniciar qualquer desenvolvimento, deve-se responder:



\- Qual problema será resolvido?

\- Quem será beneficiado?

\- Qual valor será entregue?

\- O benefício justifica a complexidade?



Implementações sem propósito claro não devem ser priorizadas.



\---



\## 2.4 Simplicidade acima de complexidade



Complexidade deve existir apenas na engenharia.



Nunca na experiência do usuário.



Sempre que duas soluções entregarem o mesmo resultado, deverá ser escolhida aquela que oferecer maior simplicidade, clareza e facilidade de manutenção.



Interfaces simples normalmente exigem engenharia sofisticada.



Esse é o padrão buscado pela StayFlow.



\---



\## 2.5 Evolução contínua



Nenhuma parte do produto deve ser considerada definitiva.



Arquitetura.



Interface.



Motores de Inteligência.



Banco de Dados.



APIs.



Todos poderão evoluir continuamente.



A única condição é preservar estabilidade, organização e consistência.



\---



\## 2.6 Decisões orientadas por longo prazo



Toda decisão deve considerar seus impactos futuros.



Atalhos que comprometam a qualidade, aumentem dívida técnica ou dificultem evolução devem ser evitados.



Construímos uma empresa.



Não apenas uma versão do software.



\---



\## 2.7 Qualidade como padrão mínimo



Qualidade não representa uma etapa do desenvolvimento.



Ela representa a forma como o produto é construído.



Uma funcionalidade somente será considerada concluída quando atender simultaneamente aos critérios de:



\- funcionamento;

\- arquitetura;

\- experiência do usuário;

\- consistência;

\- documentação.



\---



\## 2.8 Evolução sem limitações artificiais



Este documento não limita a evolução da StayFlow.



Ao contrário.



Ele existe para preservar conhecimento e permitir evolução organizada.



Sempre que surgir uma solução objetivamente superior, ela deverá ser analisada.



Se representar ganho real para o produto, poderá ser implementada imediatamente.



Não existe a filosofia de adiar melhorias apenas porque pertencem a uma fase futura.



O melhor momento para melhorar o produto é quando essa melhoria faz sentido.



\---



\## 2.9 Mentalidade de referência mundial



Toda decisão deve aproximar a StayFlow de sua visão.



Não buscamos apenas competir.



Buscamos estabelecer um novo padrão para a Inteligência Artificial aplicada à hotelaria.



Cada melhoria representa um investimento nessa visão.



\---



\## Decisões Consolidadas



\- O produto possui prioridade sobre a tecnologia.

\- Inteligência vale mais do que quantidade de funcionalidades.

\- Toda implementação deve gerar valor claro.

\- Simplicidade representa maturidade.

\- O produto evolui continuamente.

\- Toda decisão considera o longo prazo.

\- Qualidade é um requisito permanente.

\- A evolução nunca deve ser limitada artificialmente.

\- O objetivo da StayFlow é tornar-se a principal referência mundial em IA para hotelaria.



\---



<a id="capitulo-3"></a>



\# 3. FILOSOFIA DE PRODUTO



A StayFlow é desenvolvida como um produto de longo prazo.



Cada decisão deve fortalecer sua capacidade de gerar valor para clientes, aumentar inteligência operacional e consolidar sua posição como referência mundial em Inteligência Artificial para hotelaria.



O desenvolvimento do produto não é orientado por funcionalidades.



É orientado por capacidades.



\---



\## 3.1 O produto resolve problemas



Toda funcionalidade deve existir para resolver um problema real.



Nenhuma implementação deve ser realizada apenas porque é tecnicamente interessante ou porque existe em produtos concorrentes.



Antes de iniciar qualquer desenvolvimento, deve-se responder:



\- Qual problema será resolvido?

\- Quem será beneficiado?

\- Como o usuário trabalha hoje?

\- Como ele trabalhará depois desta implementação?



Se o ganho não for claro, a implementação deve ser reavaliada.



\---



\## 3.2 O cliente compra resultados



O cliente não compra Inteligência Artificial.



Não compra dashboards.



Não compra automações.



O cliente compra resultados.



Toda evolução da StayFlow deve contribuir para pelo menos um dos objetivos abaixo:



\- aumentar receita;

\- reduzir perdas;

\- economizar tempo;

\- melhorar decisões;

\- melhorar a experiência do hóspede;

\- reduzir trabalho operacional;

\- aumentar previsibilidade da operação.



\---



\## 3.3 Capacidades acima de funcionalidades



A evolução da StayFlow será medida pelas capacidades que entrega.



Exemplos:



Em vez de apenas possuir um chat, a plataforma deve compreender intenções.



Em vez de apenas possuir um dashboard, deve explicar a operação.



Em vez de apenas armazenar hóspedes, deve conhecer cada hóspede.



Essa forma de pensar orienta toda a arquitetura do produto.



\---



\## 3.4 Inteligência invisível



A melhor Inteligência Artificial é aquela que trabalha sem exigir atenção.



O usuário deve perceber seus benefícios, não sua complexidade.



Sempre que possível, a IA deve agir em segundo plano, antecipando necessidades, organizando informações e recomendando ações naturalmente.



\---



\## 3.5 Simplicidade operacional



A plataforma deve reduzir esforço.



Nunca aumentá-lo.



Sempre que uma atividade puder ser automatizada com segurança, essa possibilidade deverá ser considerada.



O tempo do gestor deve ser dedicado à tomada de decisões.



Não à execução de tarefas repetitivas.



\---



\## 3.6 Crescimento sustentável



O crescimento da StayFlow deverá preservar:



\- qualidade;

\- arquitetura;

\- consistência;

\- desempenho;

\- experiência do usuário.



Adicionar funcionalidades nunca poderá comprometer a identidade do produto.



\---



\## 3.7 Referência mundial



A StayFlow não pretende apenas acompanhar o mercado.



Pretende contribuir para definir seu futuro.



Sempre que possível, soluções deverão ser desenvolvidas considerando primeiro as necessidades reais da operação hoteleira, e não apenas reproduzindo padrões existentes.



A inovação deve surgir da compreensão profunda do problema.



\---



\## Decisões Consolidadas



\- O produto evolui para resolver problemas reais.

\- O cliente compra resultados, não funcionalidades.

\- A evolução é medida por capacidades.

\- A Inteligência Artificial deve atuar de forma invisível.

\- A plataforma existe para reduzir esforço operacional.

\- Crescimento deve preservar qualidade e consistência.

\- A StayFlow busca estabelecer um novo padrão para a hotelaria inteligente.



\---



<a id="capitulo-4"></a>



\# 4. FILOSOFIA DE ENGENHARIA



A engenharia da StayFlow existe para transformar visão em produto.



Seu objetivo não é apenas produzir software funcional, mas construir uma plataforma confiável, escalável, organizada e preparada para evoluir durante décadas.



Toda decisão técnica deve fortalecer o produto.



Nunca dificultar sua evolução.



\---



\## 4.1 Engenharia orientada ao produto



Toda decisão técnica deve existir para beneficiar o produto.



Arquitetura, frameworks, bibliotecas, padrões e ferramentas possuem valor apenas quando aumentam:



\- qualidade;

\- estabilidade;

\- produtividade;

\- escalabilidade;

\- capacidade de evolução.



Tecnologia nunca é um fim.



Ela é um instrumento para construir um produto melhor.



\---



\## 4.2 Clareza acima de complexidade



Código é escrito para pessoas.



Computadores apenas o executam.



Sempre que duas soluções atenderem igualmente ao objetivo proposto, deverá ser escolhida aquela que apresentar:



\- maior clareza;

\- menor complexidade;

\- melhor legibilidade;

\- maior facilidade de manutenção.



Complexidade somente será aceita quando gerar benefícios comprovados.



\---



\## 4.3 Arquitetura modular



A arquitetura da StayFlow deve crescer através de módulos independentes.



Cada componente deve possuir uma responsabilidade única e claramente definida.



Essa organização reduz acoplamento, facilita manutenção e permite evolução contínua do sistema.



\---



\## 4.4 Evolução incremental



Grandes reescritas representam exceções.



O crescimento da plataforma deverá ocorrer através de melhorias sucessivas sobre uma base estável.



Sempre que possível, evoluir será preferível a substituir.



Essa abordagem preserva conhecimento, reduz riscos e acelera o desenvolvimento.



\---



\## 4.5 Estabilidade



Toda alteração deve preservar o funcionamento do sistema.



Nenhuma melhoria justifica comprometer funcionalidades já consolidadas sem benefícios claramente superiores.



A estabilidade operacional é um requisito permanente.



\---



\## 4.6 Escalabilidade consciente



A arquitetura deve estar preparada para crescer.



Entretanto, não devemos criar complexidade antecipadamente.



O sistema deve evoluir conforme necessidades reais surgirem, mantendo equilíbrio entre simplicidade e capacidade de expansão.



\---



\## 4.7 Engenharia como investimento



Tempo investido em boa engenharia reduz custos futuros.



Código organizado.



Arquitetura consistente.



Documentação atualizada.



Processos bem definidos.



Tudo isso aumenta a velocidade de evolução do produto ao longo dos anos.



Boa engenharia representa um investimento permanente na empresa.



\---



\## 4.8 Responsabilidade técnica



Toda implementação influencia diretamente o futuro da plataforma.



Antes de qualquer alteração relevante, deve-se avaliar seus impactos sobre:



\- arquitetura;

\- desempenho;

\- segurança;

\- manutenção;

\- experiência do usuário;

\- futuras evoluções.



Toda decisão técnica deve fortalecer a StayFlow.



\---



\## Decisões Consolidadas



\- A engenharia existe para fortalecer o produto.

\- Clareza possui prioridade sobre complexidade desnecessária.

\- A arquitetura deve permanecer modular.

\- O produto evolui de forma incremental.

\- Estabilidade é um requisito permanente.

\- Escalabilidade deve acompanhar o crescimento do produto.

\- Boa engenharia representa um investimento de longo prazo.

\- Toda decisão técnica deve facilitar a evolução futura da StayFlow.



\---



<a id="capitulo-5"></a>



\# 5. CULTURA DE DESENVOLVIMENTO



A cultura de desenvolvimento da StayFlow define como o produto deve ser construído.



Ela estabelece o comportamento esperado durante todo o ciclo de vida do projeto e garante que cada decisão contribua para a evolução contínua da plataforma.



Mais importante do que escrever código é construir um produto excepcional.



\---



\## 5.1 Pensar antes de implementar



Toda implementação deve começar pela compreensão do problema.



Antes de escrever código, deve-se compreender:



\- qual problema será resolvido;

\- por que ele existe;

\- qual solução gera maior valor;

\- quais impactos essa decisão produzirá.



Implementar rapidamente uma solução inadequada gera mais custo do que investir tempo planejando corretamente.



\---



\## 5.2 Resolver causas, não sintomas



Problemas devem ser solucionados em sua origem.



Correções temporárias somente serão aceitas quando representarem uma medida emergencial claramente identificada.



Sempre que possível, a StayFlow deve eliminar a causa do problema e não apenas seus efeitos.



\---



\## 5.3 Objetividade



Tempo é um recurso estratégico.



Durante o desenvolvimento deve-se priorizar:



\- decisões claras;

\- implementações completas;

\- menor quantidade de etapas;

\- menor possibilidade de erro;

\- menor retrabalho.



Explicações devem existir apenas quando contribuírem para melhores decisões.



\---



\## 5.4 Evolução contínua



Nenhuma implementação deve ser considerada definitiva.



Sempre que uma melhoria representar ganho real de qualidade, desempenho, organização ou experiência do usuário, ela deverá ser considerada.



A melhoria contínua faz parte da cultura da StayFlow.



\---



\## 5.5 Continuidade



O desenvolvimento deve preservar o trabalho já realizado.



Sempre que possível, novas capacidades devem ser incorporadas sobre a base existente.



Reescritas completas somente deverão ocorrer quando apresentarem benefícios claramente superiores.



\---



\## 5.6 Documentação como parte da entrega



Uma implementação não termina quando o código funciona.



Toda decisão permanente deve ser documentada.



Sempre que houver alteração relevante em:



\- arquitetura;

\- produto;

\- APIs;

\- banco de dados;

\- motores de inteligência;

\- processos;



o Documento Mestre deverá ser atualizado.



\---



\## 5.7 Mentalidade de dono



Toda decisão deve ser tomada considerando que a StayFlow está sendo construída para durar décadas.



Antes de concluir qualquer implementação, deve-se perguntar:



\- esta solução fortalece o produto?

\- ela facilita futuras evoluções?

\- eu teria orgulho desta decisão daqui a cinco anos?



Se a resposta for negativa, a solução deve ser reavaliada.



\---



\## 5.8 Excelência como hábito



Excelência não é consequência de grandes momentos.



Ela é construída diariamente através de centenas de pequenas decisões corretas.



Cada entrega deve elevar o padrão da plataforma.



Esse compromisso é permanente.



\---



\## Decisões Consolidadas



\- Toda implementação começa pela compreensão do problema.

\- A StayFlow busca resolver causas, não sintomas.

\- Objetividade reduz erros e acelera o desenvolvimento.

\- O produto evolui continuamente.

\- Evoluir é preferível a reescrever.

\- Documentação faz parte da entrega.

\- Toda decisão deve ser tomada com mentalidade de longo prazo.

\- Excelência representa o padrão permanente da StayFlow.



\---



<a id="capitulo-6"></a>



\# 6. INTELIGÊNCIA ARTIFICIAL



A Inteligência Artificial é o núcleo da StayFlow.



Ela não representa uma funcionalidade adicional da plataforma.



Ela representa a principal capacidade do produto.



Seu papel é compreender operações, interpretar contexto, identificar padrões, antecipar acontecimentos e apoiar decisões de forma contínua.



Toda evolução relacionada à IA deve fortalecer essa missão.



\---



\## 6.1 Papel da Inteligência Artificial



A Inteligência Artificial atua como um Gerente Digital.



Seu objetivo não é apenas responder perguntas.



Ela deve compreender a operação do estabelecimento, identificar situações relevantes e gerar recomendações que aumentem a eficiência da gestão.



Toda decisão da IA deve produzir valor para o usuário.



\---



\## 6.2 Inteligência orientada por contexto



Nenhuma decisão deve ser baseada apenas em uma informação isolada.



Sempre que possível, a IA deverá considerar:



\- histórico do hóspede;

\- histórico da conversa;

\- oportunidades existentes;

\- contexto operacional;

\- informações financeiras;

\- comportamento anterior;

\- dados produzidos pelos demais motores da plataforma.



Quanto maior o contexto disponível, maior deverá ser a qualidade da decisão.



\---



\## 6.3 Inteligência distribuída



A inteligência da StayFlow não pertence a um único componente.



Ela é distribuída entre motores especializados.



Cada motor possui responsabilidades específicas e atua em conjunto com os demais para produzir uma visão completa da operação.



Essa arquitetura aumenta organização, escalabilidade e capacidade de evolução.



\---



\## 6.4 Apoio à decisão



A principal função da Inteligência Artificial é apoiar decisões.



Sempre que possível, ela deverá responder:



\- O que aconteceu?

\- O que está acontecendo?

\- O que representa risco?

\- Onde existe oportunidade?

\- O que deve ser feito agora?

\- Por que essa ação é recomendada?



A IA deve reduzir incertezas.



Nunca aumentá-las.



\---



\## 6.5 Automação responsável



Sempre que uma tarefa puder ser automatizada com segurança, essa possibilidade deverá ser considerada.



Entretanto, decisões críticas permanecerão sob controle do gestor até que existam evidências suficientes para ampliar a autonomia da plataforma.



Automação deve aumentar confiança.



Nunca reduzi-la.



\---



\## 6.6 Evolução permanente



A Inteligência Artificial deverá evoluir continuamente.



Novos modelos, técnicas e capacidades poderão ser incorporados sempre que representarem ganho real para o produto.



A arquitetura da StayFlow deve permitir essa evolução sem comprometer estabilidade ou consistência.



\---



\## 6.7 Transparência



Sempre que uma recomendação possuir impacto relevante, o usuário deverá conseguir compreender sua origem.



A plataforma deverá apresentar contexto suficiente para gerar confiança nas decisões produzidas pela IA.



Confiança é um requisito permanente.



\---



\## 6.8 Objetivo de longo prazo



A Inteligência Artificial da StayFlow deverá evoluir até tornar-se capaz de compreender toda a operação de um meio de hospedagem.



Seu papel será atuar continuamente como um gerente digital, antecipando problemas, identificando oportunidades e apoiando decisões estratégicas em tempo real.



\---



\## Decisões Consolidadas



\- A Inteligência Artificial representa o núcleo da StayFlow.

\- Toda decisão deve considerar contexto.

\- A inteligência é distribuída entre motores especializados.

\- O principal objetivo da IA é apoiar decisões.

\- Automação deve ocorrer de forma responsável.

\- A IA evolui continuamente.

\- Transparência aumenta confiança.

\- O objetivo final é construir o melhor Gerente Digital Inteligente para hotelaria do mundo.



\---



<a id="capitulo-7"></a>



\# 7. PADRÕES PERMANENTES



Este capítulo reúne as regras permanentes que deverão orientar toda a evolução da StayFlow.



Diferentemente dos princípios, que definem a forma de pensar da empresa, estes padrões definem como o produto deve ser desenvolvido, mantido e aprimorado ao longo dos anos.



São compromissos permanentes.



\---



\## 7.1 Evolução sem limitações



A StayFlow não possui uma evolução dividida por fases rígidas.



Sempre que uma melhoria representar ganho real para o produto, ela poderá ser implementada imediatamente.



Não existe a filosofia de adiar uma evolução apenas porque "pertence a uma versão futura".



A prioridade será sempre construir o melhor produto possível.



\---



\## 7.2 Preservação da base



Toda melhoria deve buscar preservar:



\- funcionalidades aprovadas;

\- arquitetura consolidada;

\- estabilidade do sistema;

\- organização do código;

\- experiência do usuário.



Evoluir deve ser preferível a reconstruir.



\---



\## 7.3 Produto acima da tarefa



O objetivo nunca será concluir tarefas.



O objetivo será melhorar continuamente a StayFlow.



Cada implementação deve deixar o produto melhor do que estava anteriormente.



Toda entrega representa um investimento permanente na plataforma.



\---



\## 7.4 Redução de desperdícios



Durante o desenvolvimento devem ser eliminados continuamente:



\- retrabalho;

\- duplicação de código;

\- processos desnecessários;

\- etapas manuais;

\- complexidade sem benefício;

\- informações redundantes.



Desenvolvimento eficiente significa produzir mais valor com menos desperdício.



\---



\## 7.5 Continuidade do conhecimento



Conhecimento importante nunca deve permanecer apenas em conversas.



Sempre que uma decisão possuir impacto permanente, ela deverá ser registrada no Documento Mestre.



A documentação faz parte da arquitetura da empresa.



\---



\## 7.6 Consistência



Toda evolução deve preservar consistência entre:



\- produto;

\- engenharia;

\- arquitetura;

\- design;

\- experiência do usuário;

\- Inteligência Artificial.



O usuário deve perceber um único produto.



Nunca um conjunto de funcionalidades independentes.



\---



\## 7.7 Objetividade operacional



Durante o desenvolvimento deve-se buscar continuamente:



\- reduzir tempo de implementação;

\- reduzir possibilidade de erros;

\- reduzir necessidade de retrabalho;

\- aumentar previsibilidade;

\- aumentar qualidade das entregas.



Sempre que possível, soluções completas devem ser preferidas a alterações fragmentadas.



\---



\## 7.8 Compromisso permanente



A StayFlow está sendo construída para tornar-se a principal empresa de Inteligência Artificial para hotelaria do mundo.



Toda decisão deve ser compatível com essa ambição.



Qualidade, organização, inteligência e evolução contínua não representam objetivos futuros.



Representam o padrão mínimo esperado para todo o projeto.



\---



\## Decisões Consolidadas



\- A evolução da StayFlow nunca será artificialmente limitada.

\- Toda melhoria deve preservar a base existente.

\- O foco permanente é fortalecer o produto.

\- Desperdícios devem ser eliminados continuamente.

\- Conhecimento permanente deve ser documentado.

\- Consistência é obrigatória em toda a plataforma.

\- Objetividade aumenta velocidade e reduz erros.

\- Toda decisão deve aproximar a StayFlow de sua visão de longo prazo.



\---



\# PARTE II — ESPECIFICAÇÃO TÉCNICA



A partir deste ponto, o Documento Mestre deixa de definir apenas a filosofia da StayFlow e passa a documentar oficialmente sua implementação.



Toda informação desta seção deve refletir o estado real do software.



Sempre que a arquitetura, o backend, o frontend, o banco de dados, as APIs ou qualquer componente estrutural evoluírem, esta parte deverá ser atualizada.



Ela representa a especificação técnica oficial da plataforma.



\---



<a id="capitulo-8"></a>



\# 8. ARQUITETURA OFICIAL



A arquitetura da StayFlow define a organização estrutural da plataforma e estabelece como seus componentes se relacionam.



Seu principal objetivo é permitir evolução contínua sem comprometer estabilidade, organização ou qualidade.



Toda decisão arquitetural deve preservar estes princípios.



\---



\## 8.1 Objetivo



A arquitetura da StayFlow foi projetada para:



\- separar responsabilidades;

\- reduzir acoplamento;

\- facilitar manutenção;

\- permitir escalabilidade;

\- acelerar evolução do produto.



Cada componente possui uma responsabilidade clara e independente.



\---



\## 8.2 Visão Geral



A plataforma é composta por dois projetos principais.



\### Backend



Projeto responsável por toda a inteligência operacional.



Nome oficial:



```text

HostelBot

```



Responsabilidades:



\- regras de negócio;

\- APIs;

\- Inteligência Artificial;

\- processamento;

\- banco de dados;

\- integrações.



\---



\### Frontend



Projeto responsável pela experiência do usuário.



Nome oficial:



```text

StayFlow---Site

```



Responsabilidades:



\- interface;

\- navegação;

\- componentes visuais;

\- consumo das APIs;

\- apresentação da inteligência produzida pelo Backend.



\---



\## 8.3 Arquitetura Geral



O fluxo oficial da plataforma é:



```text

Usuário

&#x20;     │

&#x20;     ▼

Frontend

&#x20;     │

&#x20;     ▼

APIs

&#x20;     │

&#x20;     ▼

Backend

&#x20;     │

&#x20;     ▼

Motores de Inteligência

&#x20;     │

&#x20;     ▼

Banco de Dados

&#x20;     │

&#x20;     ▼

APIs

&#x20;     │

&#x20;     ▼

Frontend

```



Toda informação percorre esse fluxo.



\---



\## 8.4 Separação de Responsabilidades



Cada camada possui responsabilidade única.



\### Frontend



Responsável apenas por:



\- interface;

\- experiência;

\- navegação;

\- apresentação.



\---



\### Backend



Responsável por:



\- processamento;

\- decisões;

\- persistência;

\- comunicação;

\- inteligência.



\---



\### Banco de Dados



Responsável por:



\- armazenamento;

\- histórico;

\- contexto;

\- consistência.



\---



\### Motores de Inteligência



Responsáveis por:



\- interpretação;

\- análise;

\- classificação;

\- recomendações;

\- geração de conhecimento.



\---



\## 8.5 Comunicação



Toda comunicação entre Frontend e Backend ocorre exclusivamente através das APIs oficiais.



O Frontend nunca acessa diretamente o banco de dados.



Toda regra de negócio permanece centralizada no Backend.



\---



\## 8.6 Evolução



A arquitetura foi projetada para crescer através da adição de novos módulos.



Novos componentes poderão ser incorporados sem necessidade de reestruturar a base existente.



Essa capacidade representa um dos principais objetivos da arquitetura da StayFlow.



\---



\## Decisões Consolidadas



\- O Backend concentra toda a inteligência da plataforma.

\- O Frontend concentra toda a experiência do usuário.

\- Toda comunicação ocorre através das APIs oficiais.

\- O banco de dados nunca é acessado diretamente pelo Frontend.

\- Os Motores de Inteligência representam o núcleo lógico do produto.

\- A arquitetura deve evoluir preservando modularidade, estabilidade e baixo acoplamento.



\---



<a id="capitulo-9"></a>



\# 9. ESTRUTURA DO PROJETO



Este capítulo documenta a organização oficial dos projetos que compõem a StayFlow.



A estrutura foi definida para manter separação clara entre responsabilidades, facilitar manutenção e permitir crescimento contínuo.



Toda alteração estrutural permanente deverá ser refletida neste documento.



\---



\## 9.1 Organização Geral



A estrutura oficial da StayFlow é:



```text

C:\\StayFlow



│

├── HostelBot

│

└── StayFlow---Site

    │

    ├── (arquivos e pastas do Frontend — ver Capítulo 11)

    │

    └── docs

        ├── STAYFLOW\_MASTER\_CONTEXT.md

        └── DIARIO\_DE\_ENGENHARIA.md

```

Nota (atualizada em 05/08/2026, versão 1.46.0): o arquivo
`CHECKLIST\_ATIVO.md`, citado em versões anteriores deste documento e do
Diário de Engenharia como "fonte única de prioridades de trabalho em
andamento", não existe mais no repositório — confirmado por busca no
sistema de arquivos durante a auditoria completa desta versão.
Não há registro de quando nem por que ele deixou de existir; nenhuma
sessão documentada no Diário registra sua remoção. Todas as menções a
ele em capítulos anteriores foram corrigidas nesta versão. A prática
de não iniciar escopo novo antes de concluir o pendente continua
válida como princípio (ver Capítulo 7), só deixou de ser rastreada
nesse arquivo específico.



Nota (atualizada em 09/07/2026, versão 1.3.0): a pasta `docs/` não é mais

uma pasta irmã de `HostelBot`/`StayFlow---Site` — ela vive dentro de

`StayFlow---Site/docs/`. Essa decisão foi tomada para permitir que o

skill de contexto automático do Claude Code (`.claude/skills/`) localize

e carregue este documento e o Diário de Engenharia no início de cada

sessão de desenvolvimento, já que a ferramenta opera a partir da raiz do

repositório Frontend.



Cada projeto possui responsabilidades independentes e bem definidas.



\*\*Nota crítica de infraestrutura (atualizada em 23/08/2026, versão
1.58.0):\*\* o ambiente de hospedagem (Render) builda apenas um
repositório por serviço. Por isso, além do repositório `StayFlow---Site`
independente (onde o desenvolvimento do frontend efetivamente
acontece), existe uma cópia de todo o conteúdo do frontend dentro de
`HostelBot/StayFlow---Site/`, versionada dentro do próprio repositório
do backend. É essa cópia interna, não o repositório `StayFlow---Site`
sozinho, que o Render de fato publica em produção.

Até a v1.57.0 essa cópia era mantida à mão (`cp`/`xcopy`/`robocopy`,
arquivo por arquivo) — dívida técnica ativa que já causou retrabalho e
divergência real entre os repositórios quando um passo era esquecido.
Desde a v1.58.0, `HostelBot/StayFlow---Site/` é um \*\*git subtree\*\* do
repositório `StayFlow---Site` (não mais arquivos soltos copiados à
mão): sincronizar passa a ser um único comando —
`bash sync_frontend.sh` na raiz do `HostelBot` (wrapper de
`git subtree pull --squash`) — seguido de `git push` depois de revisar
a mudança. Isso elimina o risco de esquecer de copiar algum arquivo
(o git garante conteúdo idêntico ao commitado no `StayFlow---Site`),
mas continua sendo dois repositórios de fato — não virou monorepo, e
o Render continua servindo exatamente o mesmo caminho de sempre, sem
nenhuma mudança de configuração do lado dele. De brinde, resolveu uma
terceira cópia órfã que existia solta na raiz do `HostelBot`
(`admin.html`, versão antiga e desatualizada, não referenciada por
nenhuma rota) — removida.

A resolução definitiva do ponto de vista arquitetural (separar o
frontend como Static Site próprio do Render, com o Backend expondo
apenas API, possivelmente num subdomínio dedicado) continua
deliberadamente fora de escopo: implicaria reconfigurar cookies de
sessão entre domínios, CORS e o escopo do Service Worker (push/PWA),
com corte de DNS — risco real demais pra uma base com pilotos reais
ativos, pra um ganho que a solução do subtree já entrega (fim da
cópia manual) sem mexer em topologia de produção. Continua registrada
no Roadmap Oficial (Capítulo 17) como decisão adiada, não esquecida.



\---



\## 9.2 HostelBot



O projeto \*\*HostelBot\*\* representa o Backend oficial da StayFlow.



Ele concentra toda a lógica operacional da plataforma.



\### Responsabilidades



\- APIs;

\- regras de negócio;

\- Inteligência Artificial;

\- motores de inteligência;

\- banco de dados;

\- integrações;

\- processamento das informações.



Nenhuma lógica operacional deve existir fora deste projeto.



\---



\## 9.3 StayFlow---Site



O projeto \*\*StayFlow---Site\*\* representa o Frontend oficial.



Seu objetivo é transformar a inteligência produzida pelo Backend em uma experiência clara, moderna e intuitiva.



\### Responsabilidades



\- interface do usuário;

\- componentes visuais;

\- navegação;

\- consumo das APIs;

\- apresentação das informações.



O Frontend não implementa regras de negócio.



\---



\## 9.4 docs



A pasta \*\*docs\*\* concentra toda a documentação oficial da StayFlow, e

está localizada dentro de `StayFlow---Site/docs/` (ver nota na seção 9.1).



Atualmente contém:



\- STAYFLOW\_MASTER\_CONTEXT.md — este documento, a principal fonte de

  verdade;

\- DIARIO\_DE\_ENGENHARIA.md — histórico detalhado sessão a sessão, com

  decisões, descobertas e pendências registradas cronologicamente.



`CHECKLIST\_ATIVO.md`, citado em versões anteriores como terceiro
arquivo desta pasta, não existe mais no repositório — ver nota na
seção 9.1.



No futuro poderão existir documentos complementares.



Entretanto, o Documento Mestre permanecerá como a principal referência

técnica da empresa.



\---



\## 9.5 Organização por responsabilidade



Cada projeto deve possuir um único propósito principal.



\### Backend



\- processamento;

\- inteligência;

\- persistência;

\- integrações;

\- APIs.



\### Frontend



\- experiência;

\- interface;

\- navegação;

\- componentes visuais.



\### Documentação



\- arquitetura;

\- engenharia;

\- produto;

\- histórico;

\- decisões permanentes.



Misturar responsabilidades aumenta complexidade, dificulta manutenção e reduz velocidade de evolução.



\---



\## 9.6 Evolução da estrutura



A estrutura da StayFlow poderá crescer continuamente.



Novos projetos poderão ser adicionados quando representarem uma responsabilidade claramente independente.



Exemplos futuros:



\- aplicativo móvel;

\- portal do viajante;

\- APIs públicas;

\- SDK;

\- ferramentas internas;

\- serviços especializados.



Toda expansão deverá preservar a arquitetura modular definida neste documento.



\---



\## Decisões Consolidadas



\- O Backend oficial da StayFlow é o projeto HostelBot.

\- O Frontend oficial é o projeto StayFlow---Site.

\- A documentação oficial permanece centralizada na pasta docs.

\- Cada projeto possui responsabilidade única.

\- A estrutura deve crescer preservando organização e modularidade.



\---



<a id="capitulo-10"></a>



\# 10. BACKEND



O Backend da StayFlow representa o núcleo operacional da plataforma.



Toda regra de negócio, processamento, integração, persistência e inteligência artificial são executados nesta camada.



O Backend deve permanecer independente da interface gráfica, permitindo que diferentes aplicações utilizem os mesmos serviços no futuro.



\---



\## 10.1 Objetivo



O Backend possui cinco responsabilidades fundamentais:



\- receber requisições;

\- processar informações;

\- aplicar regras de negócio;

\- persistir dados;

\- disponibilizar informações através das APIs oficiais.



Toda inteligência operacional nasce nesta camada.



\---



\## 10.2 Tecnologia



O Backend oficial da StayFlow é desenvolvido em \*\*Python\*\*, utilizando \*\*Flask\*\* como framework para disponibilização das APIs.



A arquitetura foi escolhida por oferecer:



\- simplicidade;

\- produtividade;

\- flexibilidade;

\- facilidade de manutenção;

\- excelente integração com Inteligência Artificial.



A tecnologia poderá evoluir futuramente sem alterar os princípios definidos neste documento.



\---



\## 10.3 Estrutura



A organização atual do Backend segue o modelo abaixo:



```text

HostelBot/



├── app.py

├── database.py

├── routes/

├── services/

├── prompts/

├── models/

├── utils/

└── database/

```



Cada diretório possui responsabilidade específica.



\---



\## 10.4 Camadas



O Backend está organizado nas seguintes camadas:



\### Entrada



Recebe requisições através das APIs.



\### Processamento



Executa regras de negócio e coordena os motores de inteligência.



\### Persistência



Armazena e consulta informações no banco de dados.



\### Integração



Comunica-se com modelos de IA e futuros serviços externos.



Essa separação reduz acoplamento e facilita evolução.



\---



\## 10.5 Regras de negócio



Toda regra permanente da plataforma deve permanecer no Backend.



O Frontend nunca deve conter lógica operacional.



Essa decisão garante:



\- consistência;

\- segurança;

\- reutilização;

\- facilidade de manutenção.



\---



\## 10.6 Comunicação



Toda comunicação externa ocorre através das APIs oficiais.



Nenhum módulo externo acessa diretamente o banco de dados.



O Backend representa a única camada autorizada a manipular informações persistentes.



\---



\## 10.7 Evolução



O Backend foi projetado para crescer através da incorporação de novos módulos.



Toda nova implementação deverá preservar:



\- organização;

\- modularidade;

\- baixo acoplamento;

\- alta coesão;

\- facilidade de testes.



\---



\## Decisões Consolidadas



\- O Backend representa o núcleo operacional da StayFlow.

\- Toda regra de negócio permanece centralizada nesta camada.

\- O Backend é desenvolvido em Python utilizando Flask.

\- A arquitetura é organizada por responsabilidades.

\- Toda comunicação ocorre através das APIs oficiais.

\- O Backend evolui preservando modularidade e organização.



\---



<a id="capitulo-11"></a>



\# 11. FRONTEND



O Frontend da StayFlow é responsável por transformar a inteligência produzida pelo Backend em uma experiência clara, moderna e eficiente.



Seu objetivo é permitir que o gestor compreenda rapidamente a situação da operação e tome decisões com confiança.



O Frontend representa a camada de apresentação da plataforma.



\---



\## 11.1 Objetivo



O Frontend possui cinco responsabilidades fundamentais:



\- apresentar informações;

\- organizar a experiência do usuário;

\- consumir as APIs oficiais;

\- facilitar a navegação;

\- transformar dados em decisões visuais.



Toda inteligência permanece no Backend.



\---



\## 11.2 Tecnologia



O Frontend oficial da StayFlow é desenvolvido utilizando:



\- HTML5;

\- CSS3;

\- JavaScript.



A escolha privilegia simplicidade, desempenho, facilidade de manutenção e evolução contínua.



Novas tecnologias poderão ser incorporadas futuramente quando representarem benefícios claros para o produto.



\---



\## 11.3 Estrutura



A estrutura atual do Frontend segue o modelo abaixo (atualizada em 09/07/2026,
versão 1.3.0, após a refatoração de CSS):



```text

StayFlow---Site/



├── index.html          (landing page pública)

├── planos.html         (página pública de preços — novo em 13/08/2026,

│                         versão 1.47.0: 3 planos reais — Starter US$89,

│                         Business US$349, Enterprise US$699+ negociado —

│                         cada botão linka pra Register.html?plan=<nome>)

├── dashboard.html      (aplicação principal — single-page, abas internas:

│                         dashboard, chats, reservas, mapa de quartos,

│                         opportunity center, hóspedes, operações (com

│                         sub-abas de cozinha, manutenção, segurança

│                         patrimonial, estacionamento e tarefas — v1.47.0),

│                         financeiro, estoque, receitas, relatórios,

│                         eventos, portfólio/parceiros (só visível para

│                         conta de agência — v1.47.0, ver 16.33),

│                         configurações (com sub-abas, incluindo

│                         segurança e billing) — equipe acessível pelo

│                         menu do avatar no topbar, com sub-aba própria

│                         de escala de turnos; tour de introdução no

│                         primeiro acesso — v1.47.0, ver 16.33)

├── Login.html

├── Register.html       (lê `?plan=` da URL desde a v1.47.0 — mostra o

│                         plano escolhido e envia `plan_name` no POST

│                         /register, ver Capítulo 17)

├── admin.html, admin-list.html, admin-hostel.html, stayflow-hub.html

│                        (StayFlow Hub — painel interno da própria

│                         StayFlow, não do cliente; novo em 13/08/2026,

│                         versão 1.47.0, ver 16.33)

│

├── static/css/

│   ├── tokens.css       (fonte única de cores, radius, shadow, breakpoints —

│   │                      #0b84ff é o token de cor oficial)

│   ├── reset.css         (reset universal compartilhado)

│   ├── app.css           (estilos da aplicação/dashboard)

│   ├── landing.css       (estilos da landing page)

│   ├── auth.css          (estilos de Login/Register)

│   └── legacy.css        (entry-point opcional via @import, não usado

│                           por nenhuma página em produção)

│

├── assets/

│   ├── js/               (scripts JS, ex.: chats-live.js, stayflow-live.js)

│   ├── images/

│   ├── icons/

│   └── fonts/

│

├── docs/

│   ├── DIARIO_DE_ENGENHARIA.md    (histórico detalhado sessão a sessão)

│   └── STAYFLOW_MASTER_CONTEXT.md (este documento)

│

├── .claude/skills/stayflow-context/  (skill que carrega o histórico do

│                                       projeto automaticamente em sessões

│                                       do Claude Code)

│

├── _backup_antigo/       (arquivos órfãos preservados por segurança,

│                           fora do caminho de execução)

│

└── futuras páginas

```



Nota de arquitetura (versão 1.3.0): antes da refatoração de 09/07/2026, cada

página tinha seu próprio bloco `<style>` inline, com blocos cronológicos

acumulados e uso extensivo de `!important`, causando bugs reais de UX em

telas mobile. A extração para `static/css/` com tokens compartilhados

resolveu essa dívida técnica, mantendo isolamento por página (evitando

colisão de nomes de classe entre app/landing/auth).



Cada recurso deve permanecer organizado conforme sua responsabilidade.



\---



\## 11.4 Dashboard



O Dashboard representa a principal interface operacional da StayFlow.



Seu papel é consolidar a inteligência produzida pelos motores da plataforma e apresentá-la ao gestor de forma objetiva.



O Dashboard não substitui os módulos da plataforma.



Ele funciona como o Centro de Comando Inteligente da operação.



\---



\## 11.5 Componentização



Toda evolução do Frontend deverá buscar reutilização.



Componentes comuns devem ser compartilhados entre páginas.



Essa abordagem reduz:



\- duplicação;

\- manutenção;

\- inconsistências visuais.



A arquitetura visual deve crescer através da reutilização de componentes.



\---



\## 11.6 Comunicação



Toda informação exibida pelo Frontend deve ser obtida através das APIs oficiais.



O Frontend nunca deve:



\- acessar diretamente o banco de dados;

\- implementar regras de negócio;

\- manter informações críticas apenas em memória local.



Toda decisão operacional pertence ao Backend.



\---



\## 11.7 Design System



A interface da StayFlow deverá seguir um Design System único.



Todos os módulos deverão compartilhar:



\- tipografia;

\- espaçamentos;

\- cores;

\- componentes;

\- ícones;

\- animações;

\- padrões de interação.



A consistência visual faz parte da identidade do produto.



\---



\## 11.8 Evolução



Toda evolução do Frontend deverá tornar a plataforma:



\- mais clara;

\- mais rápida;

\- mais intuitiva;

\- mais elegante;

\- mais eficiente.



Mudanças visuais nunca deverão comprometer usabilidade ou desempenho.



\---



\## Decisões Consolidadas



\- O Frontend transforma inteligência em experiência.

\- Toda regra de negócio permanece no Backend.

\- O Dashboard representa a principal interface da plataforma.

\- Componentes devem ser reutilizáveis.

\- Toda comunicação ocorre através das APIs oficiais.

\- O Frontend deverá evoluir continuamente preservando consistência visual e excelência na experiência do usuário.



\---



<a id="capitulo-12"></a>



\# 12. BANCO DE DADOS



O banco de dados da StayFlow representa a memória permanente da plataforma.



Sua função é preservar informações, fornecer contexto para os motores de inteligência e garantir a consistência da operação.



Toda informação armazenada deve possuir um propósito claro e contribuir para a evolução da inteligência do sistema.



\---



\## 12.1 Objetivo



O banco de dados possui cinco responsabilidades principais:



\- armazenar informações permanentes;

\- preservar o histórico operacional;

\- fornecer contexto para a Inteligência Artificial;

\- sustentar as regras de negócio;

\- apoiar análises e decisões futuras.



O banco não existe apenas para guardar dados.



Ele existe para preservar conhecimento.



\---



\## 12.2 Tecnologia



Na versão atual, a StayFlow utiliza \*\*SQLite\*\*.



A escolha atende plenamente às necessidades da fase atual do projeto, oferecendo:



\- simplicidade;

\- desempenho;

\- facilidade de manutenção;

\- rapidez no desenvolvimento.



A arquitetura foi projetada para permitir futura migração para bancos como PostgreSQL sem alterações significativas na lógica da aplicação.



\---



\## 12.3 Entidades Principais



Atualmente, o banco de dados é composto pelas seguintes entidades principais:



\### Hostels



Armazena os dados de cada hostel/hotel/pousada cliente da plataforma —

incluindo credenciais do WhatsApp Business (Phone Number ID, Access

Token) por unidade, preparando a base para múltiplos hostels com números

próprios. É a entidade-raiz do isolamento multi-tenant: toda consulta em

outras tabelas é escopada por `hostel_id`.



\---



\### Guests



Armazena informações dos hóspedes. Escopado por `hostel_id` — o mesmo

telefone pode existir em hostels diferentes sem conflito.



\---



\### Messages



Armazena todo o histórico de comunicação, com timestamp (`created_at`) por

mensagem — base que sustenta a linha do tempo da conversa exibida no

Frontend.



\---



\### Opportunities



Armazena oportunidades identificadas pelos motores de inteligência.
Ganhou a coluna `suggested\_partner\_item\_id` em 13/08/2026 (versão
1.47.0), referenciando um item de `portfolio\_items` quando o Decision
Engine identifica que o hóspede pediu algo que a hospedagem não vende
mas uma agência parceira vende — ver 16.4.



\---



\### Reservations



Armazena as reservas dos hóspedes, com status atualizável (pendente,

confirmada, check-in, check-out, cancelada).



\---



\### Settings



Armazena as configurações de cada hostel (nome, tipo de propriedade,

horários de check-in/check-out).



\---



\### Suppliers e Inventory Items



Armazenam, respectivamente, os fornecedores cadastrados e os itens de

estoque (com categoria, quantidade, quantidade mínima e fornecedor

vinculado), sustentando os alertas de reposição do módulo de Estoque.



\---



\### Offerings



Armazena o catálogo de experiências, passeios e upsells oferecidos pelo

hostel, usado pelo módulo de Receitas.



\---



\### Users, Roles, Hostel\_Memberships e Membership\_Permission\_Overrides



A entidade `Users` representa uma \*\*identidade única de pessoa\*\* (nome,
e-mail globalmente único, senha) — sem `hostel_id` nem função (`role`)
próprios.



O vínculo entre uma pessoa e um hostel vive em `Hostel_Memberships`,
permitindo que a mesma pessoa tenha acesso a mais de um hostel
simultaneamente (cada vínculo com sua própria função), com troca entre
hostels sem necessidade de novo login.



Cada hostel define suas próprias funções em `Roles` (nome + lista
configurável de permissões, de um catálogo de 20 chaves — ver 13.3 e
16.22 — não existem funções fixas no sistema, apenas a função "Admin"
com todas as permissões e "Staff" sem nenhuma permissão por padrão,
criadas automaticamente durante a migração de dados existentes). O
catálogo passou de 14 para 19 chaves em 04/08/2026 (cinco módulos
operacionais novos — cozinha, manutenção, segurança patrimonial,
estacionamento, escala — cada um com permissão própria) e de 19 para
20 em 05/08/2026, versão 1.45.0, com a adição de `events`. A rodada de
04/08/2026 nunca tinha sido registrada neste documento nem no Diário
de Engenharia até a auditoria retroativa de 05/08/2026 (versão
1.46.0) — ver Capítulo 18.



`Membership\_Permission\_Overrides` permite ao administrador do hostel
conceder ou revogar permissões específicas para uma pessoa individual, por
cima do padrão definido pela função dela — sem afetar as demais pessoas
com a mesma função. O cálculo da permissão efetiva de cada pessoa é
sempre recalculado em tempo real (função + exceções), nunca guardado em
cache de sessão — uma mudança feita pelo administrador vale
imediatamente, sem esperar novo login.



\*\*Status de implantação (atualizado em 19/07/2026, versão 1.5.0):\*\* schema,
migração de dados e todas as APIs consumidoras (login com múltiplos
hostels, CRUD de funções e vínculos, exceções individuais) estão
publicados e validados em produção — ver Capítulo 16, seção 16.22.



\---



\### Rooms, Room\_Categories e Beds



Sustentam o Mapa de Quartos: `room\_categories` armazena as modalidades de
quarto configuráveis por propriedade (com padrão automático por tipo de
hospedagem), `rooms` os quartos cadastrados e `beds` cada cama
individual, com status real (livre, ocupada, precisa de limpeza,
reservada, manutenção, na lavanderia) e suporte a camas pareadas
(beliche). `linen\_kits`/`linen\_kit\_items` sustentam o ciclo de
lavanderia (desconto de roupa de cama limpa no check-out, devolução ao
estoque quando a lavanderia retorna). Ver Capítulo 16.



\---



\### Guest\_Channel\_Identities



Modelo de identidade multi-canal de verdade: associa um `guest\_id` a um
identificador externo por canal (`UNIQUE(hostel\_id, channel,
external\_id)` — telefone no WhatsApp, PSID no Messenger, IGSID no
Instagram), permitindo que o mesmo hóspede seja reconhecido
independentemente de por qual canal está conversando. Ver Capítulo 16.



\---



\### Beds24\_Master\_Account, Channel\_Room\_Mapping e Channel\_Webhook\_Events



Sustentam a integração com o Channel Manager (Beds24): credencial
mestra criptografada (modelo agência/white-label, uma conta StayFlow
com cada cliente virando sub-propriedade), mapeamento de modalidade de
quarto para o quarto correspondente na sub-propriedade do Beds24, e
registro cru de todo evento de webhook recebido antes de qualquer
interpretação (com proteção de idempotência). Ver Capítulo 16.



\---



\### Guest\_Documents e Reservation\_Payments



`guest\_documents` armazena a galeria de documentos de identidade do
hóspede (recebidos via WhatsApp/Messenger/Instagram ou upload manual).
`reservation\_payments` sustenta o saldo devedor/crédito de hóspedes de
Longa Duração, controlado à parte do valor de reservas fixas. Ver
Capítulo 16.



\---



\### Sessions, Login\_Attempts, Quick\_Replies, Billing e API\_Keys



`sessions`/`login\_attempts` sustentam o módulo de Segurança (sessões
ativas revogáveis, histórico de tentativas de login) — `sessions` ganhou
a coluna `impersonating\_from\_hostel\_id` em 13/08/2026 (versão 1.47.0,
ver 16.33). `quick\_replies` sustenta as Respostas Rápidas da aba Chats.
`billing` guarda plano, status e trial por hostel (Fase 1, em produção
há mais tempo do que este documento registrava — Starter/Business/
Enterprise, `status='trialing'` por 30 dias a partir da criação do
hostel; a cobrança recorrente automática da assinatura em si, Fase 2-3,
segue sem processador ligado — ver correção do Capítulo 17). `api\_keys`
sustenta o webhook de saída assinado (Fase 6 da integração de canais).
Ver Capítulo 16.



\---



\### Currency\_Exchanges (atualizado em 04/08/2026, versão 1.41.0)



Sustenta a casa de câmbio: moeda e valor estrangeiro recebidos,
cotação usada (com o hóspede) e cotação de mercado no momento do
registro, lucro calculado na diferença, operador responsável e
horário, com vínculo opcional a um `guest\_id`. Alimenta tanto o
Financeiro quanto o histórico do perfil do hóspede. Ver Capítulo 16,
seção 16.11.



\---



\### Push\_Subscriptions, Totp\_Pending\_Challenges e Totp\_Backup\_Codes
(criadas em 05/08/2026, versões 1.43.0 e 1.44.0)



`push\_subscriptions` guarda uma inscrição de notificação push por
pessoa+dispositivo (PC e celular contam como inscrições separadas),
com as chaves criptográficas exigidas pela Web Push API.
`totp\_pending\_challenges` sustenta a etapa intermediária do login com
2FA — token de curta duração criado depois da senha certa, antes do
código TOTP confirmar a sessão de verdade. `totp\_backup\_codes` guarda
o hash dos códigos de backup de uso único gerados na ativação do 2FA.
Ver Capítulo 16, seções 16.28 e a nova seção de Notificações Push.



\---



\### Event\_Spaces, Events, Event\_Addons e Event\_Addon\_Selections
(criadas em 05/08/2026, versão 1.45.0)



Sustentam o módulo de Eventos: `event\_spaces` os espaços alugáveis
(salões, jardins, auditórios) com capacidade e preço; `events` cada
reserva de espaço, com cliente (não precisa ser hóspede cadastrado),
período, status e preço base; `event\_addons` o catálogo de serviços
extras (buffet, decoração, som); `event\_addon\_selections` os
adicionais anexados a um evento específico, com o preço do catálogo
congelado no momento da escolha. Ver Capítulo 16, nova seção de
Eventos.



\---



\### Portfolio\_Items, Partner\_Offers e Partner\_Referral\_Ledger
(criadas em 13/08/2026, versão 1.47.0)



Sustentam contas de agência parceira (Portfólio/Parceiros): `hostels`
ganhou as colunas `account\_kind` (`lodging`/`agency`), `agency\_category`
(8 grupos: `turismo`, `aluguel\_carro`, `aluguel\_bike`,
`aluguel\_equipamentos`, `imobiliaria`, `automotivo`, `comercio`,
`servico\_generico` — ampliado em 20/08/2026, versão 1.50.0, ver 14.3)
e `agency\_subcategory` (texto livre, detalhe dentro dos grupos
`automotivo`/`comercio`, mesma versão) — não é entidade nova, é a mesma
linha de hostel reaproveitada. `portfolio\_items` é o catálogo de itens de uma
agência (nome, descrição, foto, categoria, preço fixo ou variável).
`partner\_offers` é o opt-in de uma hospedagem para vender um item de
outra (`UNIQUE(hostel\_id, portfolio\_item\_id)`). `partner\_referral\_ledger`
guarda a comissão a pagar para a hospedagem que indicou o hóspede,
sempre que o pagamento é coletado pela agência via Mercado Pago Split
(`guest\_charges` ganhou `referring\_hostel\_id` e
`referring\_hostel\_commission\_pct`) — pago "por fora", sem processador
de payout automático (stub contábil deliberado). Ver Capítulo 14, seção
14.3, e Capítulo 16, nova seção 16.33.



\---



\### Impersonation\_Log (criada em 13/08/2026, versão 1.47.0)



Registra cada visita de um administrador da StayFlow (`admin\_user\_id`)
à conta de um hostel cliente (`hostel\_id`), com início e fim
(`started\_at`/`ended\_at`). Trabalha em conjunto com a coluna nova
`sessions.impersonating\_from\_hostel\_id`, que guarda o hostel de origem
do administrador enquanto `sessions.hostel\_id` é reapontado
temporariamente para a conta visitada. Ver Capítulo 16, nova seção
16.33.



\---



\### User\_Feature\_Intros (criada em 13/08/2026, versão 1.47.0)



Registra, por pessoa (`user\_id`) e por item de menu (`feature\_key`),
se o tour de introdução já mostrou a dica daquele item
(`UNIQUE(user\_id, feature\_key)`) — preferência gravada no banco, não em
localStorage, então vale em qualquer dispositivo. `users` ganhou a
coluna `onboarding\_dismissed` para desligar o tour inteiro de uma vez.
Ver Capítulo 16, nova seção 16.33.



\---



Novas entidades serão incorporadas conforme a evolução da plataforma.



\---



\## 12.4 Princípios



Toda estrutura do banco deve seguir os seguintes princípios:



\- responsabilidade única por entidade;

\- integridade referencial;

\- baixa redundância;

\- consistência dos dados;

\- facilidade de evolução.



A modelagem deve permanecer simples e organizada.



\---



\## 12.5 Histórico



Sempre que possível, informações relevantes devem ser preservadas.



O histórico operacional aumenta significativamente a capacidade analítica da Inteligência Artificial.



Quanto maior o contexto disponível, melhores serão as decisões produzidas pela plataforma.



\---



\## 12.6 Acesso



O banco de dados é acessado exclusivamente pelo Backend.



Nenhum componente do Frontend possui acesso direto às informações persistentes.



Toda leitura e escrita ocorre através das regras de negócio implementadas no Backend.



\---



\## 12.7 Evolução



O modelo de dados deverá evoluir continuamente.



Novas tabelas, relacionamentos e estruturas poderão ser adicionados sempre que contribuírem para aumentar a capacidade operacional da plataforma.



Toda alteração estrutural deverá preservar consistência e compatibilidade sempre que possível.



\---



\## 12.8 Persistência em Produção



O ambiente de produção da StayFlow roda sobre infraestrutura com sistema de arquivos efêmero por padrão — ou seja, arquivos gravados durante a execução do serviço não sobrevivem automaticamente a um novo deploy ou reinício.



Para garantir que o banco de dados SQLite não seja perdido nessas ocasiões, a plataforma utiliza um \*\*disco persistente\*\* anexado ao serviço de produção, e o caminho do arquivo de banco é definido dinamicamente através de variável de ambiente, com um valor padrão seguro para uso em ambiente local de desenvolvimento.



Essa decisão garante que:



\- o ambiente de desenvolvimento local continue funcionando sem nenhuma configuração adicional;

\- o ambiente de produção grave o banco de dados exclusivamente na área persistente;

\- nenhum dado de produção seja perdido em deploys ou reinícios futuros.



Essa configuração é considerada uma decisão permanente de infraestrutura e deve ser preservada em qualquer evolução futura do ambiente de hospedagem.



\---



\## Decisões Consolidadas



\- O banco de dados representa a memória permanente da StayFlow.

\- SQLite é a tecnologia oficial na fase atual do projeto.

\- O Backend é o único responsável pelo acesso aos dados.

\- O histórico operacional deve ser preservado.

\- A modelagem deverá evoluir continuamente de forma organizada.

\- Toda informação armazenada deve possuir propósito claro.

\- O ambiente de produção deve sempre gravar o banco em armazenamento persistente, nunca em caminho efêmero.



\---



<a id="capitulo-13"></a>



\# 13. APIs



As APIs da StayFlow representam a camada oficial de comunicação entre todos os componentes da plataforma.



Elas estabelecem um contrato único entre Frontend, Backend, motores de inteligência e futuras integrações externas.



Toda informação que entra ou sai do sistema deve passar pelas APIs oficiais.



\---



\## 13.1 Objetivo



As APIs possuem cinco responsabilidades principais:



\- receber requisições;

\- validar informações;

\- encaminhar processamento;

\- retornar respostas padronizadas;

\- preservar o desacoplamento entre os componentes da plataforma.



Elas representam a fronteira oficial do Backend.



\---



\## 13.2 Arquitetura



A StayFlow utiliza APIs REST sobre HTTP.



Toda comunicação entre aplicações ocorre através dessa camada.



O Frontend nunca acessa diretamente:



\- banco de dados;

\- motores de inteligência;

\- regras de negócio.



Toda comunicação deve passar pelas APIs.



\---



\## 13.3 Estrutura



Cada domínio funcional da plataforma possui seu próprio conjunto de rotas.



Exemplos:



\- Autenticação (login, sessão via `/me`, logout)

\- Dashboard

\- Chats, Quick Replies (respostas rápidas)

\- Guests

\- Opportunities

\- Activity

\- Executive Summary

\- Ask StayFlow (`/ask`, agente conversacional com function calling)

\- Reservations

\- Rooms / Bed Map (Mapa de Quartos, camas, check-in/check-out, lavanderia)

\- Finance

\- Reports

\- Inventory (fornecedores e itens de estoque)

\- Operations

\- Revenue (catálogo de upsells)

\- Settings (WhatsApp, Facebook, Instagram, Beds24, webhook de saída)

\- Team e Roles (gestão de equipe, funções e permissões individuais)

\- Security (troca de senha, sessões, tentativas de login, 2FA — ver
  16.28)

\- Push (`/push/status`, `/push/subscribe`, inscrição de notificação
  push por dispositivo — ver nova seção de Notificações Push no
  Capítulo 16)

\- Events (espaços, eventos, adicionais e disponibilidade — ver nova
  seção de Eventos no Capítulo 16)

\- WhatsApp Webhook (integração com a Meta Cloud API)

\- Meta Webhook (Messenger e Instagram Direct, endpoint compartilhado)

\- Beds24 Webhook (entrada de reservas de OTAs via Channel Manager)



Novos módulos deverão seguir o mesmo padrão arquitetural.



\---



\## 13.4 Responsabilidades



As APIs não executam regras de negócio.



Sua responsabilidade limita-se a:



\- receber requisições;

\- validar parâmetros;

\- encaminhar processamento;

\- devolver respostas padronizadas.



Toda inteligência permanece centralizada no Backend.



\---



\## 13.5 Padrão de respostas



As respostas das APIs devem seguir um padrão único.



Sempre que possível deverão conter:



\- status da operação;

\- dados solicitados;

\- mensagens de erro padronizadas;

\- estrutura consistente.



Esse padrão reduz complexidade no Frontend e facilita integrações futuras.



\---



\## 13.6 Segurança



Toda entrada recebida deve ser validada.



Nenhuma informação enviada pelo cliente deve ser considerada confiável sem validação.



A responsabilidade pela segurança pertence ao Backend.



\*\*Padrão estabelecido (credenciais de integração):\*\* nenhuma rota
`GET /settings/*` (WhatsApp, Facebook, Instagram, Beds24) devolve o
valor bruto de um token de acesso para o Frontend — sempre apenas um
booleano (`has\_access\_token`). Ver também Capítulo 16, seção 16.28.



\---



\## 13.7 Escalabilidade



A arquitetura das APIs foi projetada para permitir futuras integrações com:



\- aplicativo do viajante;

\- PMS;

\- motores de reserva;

\- plataformas de pagamento;

\- parceiros estratégicos;

\- serviços de Inteligência Artificial.



Channel Managers (Beds24) já deixou de ser integração futura: está

implementado e validado em produção desde a versão 1.18.0, com seis

fases concluídas (ver Capítulo 16, seção 16.25).



Novas integrações deverão reutilizar os mesmos princípios definidos neste documento.



\---



\## 13.8 Evolução



Novos endpoints poderão ser adicionados continuamente.



Sempre que possível, alterações deverão preservar compatibilidade com versões anteriores.



Mudanças incompatíveis deverão ser documentadas no Registro Oficial de Evolução.



\---



\## Decisões Consolidadas



\- Toda comunicação da StayFlow ocorre através das APIs oficiais.

\- APIs não implementam regras de negócio.

\- O Backend concentra toda a inteligência da plataforma.

\- As respostas seguem padrão consistente.

\- Toda entrada deve ser validada.

\- A arquitetura foi preparada para futuras integrações.

\- Toda alteração relevante nas APIs deverá ser documentada oficialmente.



\---



<a id="capitulo-14"></a>



\# 14. MOTORES DE INTELIGÊNCIA



Os Motores de Inteligência constituem o núcleo analítico da StayFlow.



Eles são responsáveis por transformar dados operacionais em conhecimento estruturado, permitindo que a plataforma compreenda contexto, identifique oportunidades, produza recomendações e apoie decisões.



A inteligência da StayFlow é distribuída entre motores especializados, cada um com responsabilidades claramente definidas.



Essa arquitetura permite evolução independente, maior organização e alta escalabilidade.



\---



\## 14.1 Objetivo



Os Motores de Inteligência existem para transformar informações operacionais em conhecimento útil.



Suas responsabilidades incluem:



\- interpretar eventos;

\- compreender contexto;

\- identificar padrões;

\- gerar recomendações;

\- produzir conhecimento reutilizável;

\- apoiar decisões humanas e automáticas.



\---



\## 14.2 Arquitetura



Cada motor possui responsabilidade única.



Nenhum motor deve assumir funções pertencentes a outro.



Essa separação permite evolução modular e reduz acoplamento entre componentes.



Toda comunicação entre motores deve ocorrer através de estruturas de dados padronizadas.



\---



\## 14.3 Decision Engine



Responsável por interpretar informações recebidas pela plataforma.



Principais responsabilidades:



\- identificar intenção;

\- compreender contexto;

\- calcular prioridade;

\- definir urgência;

\- estimar valor potencial;

\- recomendar próxima ação.



É o primeiro motor acionado durante o processamento de um evento.



\*\*Consciência de tipo de conta (atualizado em 13/08/2026, versão
1.47.0):\*\* `services/decision\_engine.py`
(`analyze\_message`/`analyze\_with\_ai`) e `services/ai\_service.py`
(`ask\_ai`) passam a receber `account\_kind` (`lodging`/`agency`) e mudam
de comportamento quando o hostel é uma conta de agência parceira —
ferramentas próprias (`AGENCY\_TOOLS`, com `get\_offerings` consultando o
portfólio da agência) e nenhuma tentativa de fluxo de reserva de
quarto/check-in, que não faz sentido para esse tipo de conta. Quando o
intent identificado é `tour` e existe algum item de portfólio parceiro
habilitado para a hospedagem, o Decision Engine também passa a sugerir
esse item na oportunidade criada (`suggested\_partner\_item\_id`) — ver
16.4. Ver Capítulo 16, nova seção 16.33, para o schema completo de
contas de agência (Portfólio/Parceiros).

\*\*Contexto separado por categoria de negócio, não só por tipo de
conta (atualizado em 20/08/2026, versão 1.50.0):\*\* até aqui, TODAS as
categorias de agência (turismo, aluguel de carro/bike/equipamento)
compartilhavam um único `AGENCY\_SYSTEM\_PROMPT`, só trocando um rótulo
(`agency\_category\_label`) dentro do texto — não era um contexto de
verdade separado por tipo de negócio, era um prompt genérico com um
substantivo diferente. Motivado pelo usuário querer receber pilotos de
verticais bem diferentes entre si (imobiliária, estética/película
automotiva, estamparia, loja online), corrigido: cada categoria agora
tem seu próprio prompt COMPLETO em `AGENCY\_CATEGORY\_PROMPTS`
(`services/ai\_service.py`), com vocabulário e perguntas específicas do
negócio real (ex.: imobiliária pergunta tipo de imóvel/bairro/orçamento
e fala de "visita", não de "disponibilidade"). A espinha dorsal que
garante o produto (nunca inventar preço/item, sempre checar
`get\_offerings`, nunca fechar a venda sozinho) é deliberadamente
idêntica em todas as categorias — só o "sabor" de negócio muda.
Categoria ausente ou não mapeada cai no prompt `servico\_generico`
(catch-all). Mesmo padrão aplicado ao `business\_context` do Decision
Engine (`\_AGENCY\_CATEGORY\_BUSINESS\_CONTEXT`).

`database.AGENCY\_CATEGORIES` (8 valores): `turismo`, `aluguel\_carro`,
`aluguel\_bike`, `aluguel\_equipamentos`, `imobiliaria`, `automotivo`,
`comercio`, `servico\_generico`. \*\*"automotivo" e "comercio" são GRUPOS,
não categorias fechadas\*\* — mesmo espírito de `account\_kind = "lodging"`
ter `hostel\_type` como campo livre pra hostel/pousada/hotel/etc: a
variedade real dentro de "automotivo" (estética, película, mecânica,
funilaria e pintura, elétrica, borracharia, peças de carro/moto/
caminhão/máquinas — "auto peças" sozinho foi desdobrado em 4 presets,
por pedido do usuário: peça de carro ≠ peça de moto/caminhão/máquina,
catálogo e vocabulário bem diferentes) ou de "comércio" (são "muitas"
categorias, nas palavras do usuário) é grande
demais pra virar prompt separado por subtipo. Nova coluna
`hostels.agency\_subcategory` (texto livre, mesmo padrão de
`hostel\_type`/"+ Novo tipo...", com presets em
`database.AGENCY\_SUBCATEGORY\_PRESETS`) guarda o detalhe dentro do
grupo — entra no prompt via `{agency\_subcategory\_line}` ("...an
automotive shop specializing in Funilaria e pintura.", ou frase limpa
sem esse trecho quando a subcategoria está vazia). `Register.html`
pede o grupo e, só quando é automotivo/comércio, um segundo seletor
(presets + campo livre) pra subcategoria.

De quebra, mesma versão: contas `agency` (sem reserva/check-in) ganham
`dispatch\_opportunity\_webhook` (`database.py`) como evento de
conversão pro webhook de saída genérico — dispara `opportunity\_created`/
`opportunity\_updated` toda vez que o Decision Engine cria ou atualiza
uma oportunidade aberta, chamado direto de `analyze\_message` logo após
o commit. Analógo ao `dispatch\_reservation\_webhook` que hospedagem já
tinha (v1.27.0) — ver seção 16.25 pro detalhe completo do mecanismo.



\---



\## 14.4 Opportunity Engine



Responsável por identificar e gerenciar oportunidades comerciais.



Principais responsabilidades:



\- criar oportunidades;

\- evitar duplicidades;

\- calcular potencial financeiro;

\- acompanhar status;

\- organizar prioridades.



Seu objetivo é garantir que nenhuma oportunidade relevante seja perdida.



\---



\## 14.5 Executive Engine



Responsável por consolidar informações operacionais em resumos executivos.



Principais responsabilidades:



\- produzir Executive Summary;

\- identificar riscos;

\- destacar oportunidades;

\- organizar prioridades;

\- recomendar ações.



Seu foco é reduzir o tempo necessário para compreender a operação.



\---



\## 14.6 Guest Intelligence Engine



Responsável por construir o Perfil Inteligente de cada hóspede.



Principais responsabilidades:



\- consolidar histórico;

\- registrar preferências;

\- compreender comportamento;

\- preservar contexto;

\- disponibilizar conhecimento aos demais motores.



Esse motor representa a memória inteligente da plataforma.



\---



\## 14.7 Comunicação



Os motores compartilham informações entre si.



Entretanto, cada motor permanece responsável apenas pelo seu domínio de conhecimento.



Essa organização evita duplicidade de responsabilidades e facilita evolução futura.



\---



\## 14.8 Evolução



Novos motores poderão ser incorporados sempre que uma nova responsabilidade justificar independência arquitetural.



Toda expansão deverá preservar:



\- modularidade;

\- baixo acoplamento;

\- alta coesão;

\- clareza estrutural.



\---



\## Decisões Consolidadas



\- A inteligência da StayFlow é distribuída entre motores especializados.

\- Cada motor possui responsabilidade única.

\- O Decision Engine inicia a interpretação operacional.

\- O Opportunity Engine gerencia oportunidades comerciais.

\- O Executive Engine produz visão executiva da operação.

\- O Guest Intelligence Engine representa a memória inteligente dos hóspedes.

\- Novos motores poderão ser incorporados preservando a arquitetura modular.



\---



<a id="capitulo-15"></a>



\# 15. DASHBOARD



O Dashboard é o Centro de Comando Inteligente da StayFlow.



Ele concentra, organiza e apresenta todas as informações relevantes produzidas pela plataforma, permitindo que o gestor compreenda rapidamente a situação da operação e tome decisões com segurança.



O Dashboard não é um painel administrativo.



Ele é a principal interface entre o gestor e a inteligência da StayFlow.



\---



\## 15.1 Objetivo



O Dashboard possui uma missão permanente:



Transformar informações complexas em decisões simples.



Toda informação exibida deve responder, direta ou indiretamente, a uma destas perguntas:



\- O que aconteceu?

\- O que está acontecendo agora?

\- O que exige minha atenção?

\- Onde existe oportunidade?

\- Qual deve ser minha próxima ação?



\---



\## 15.2 Responsabilidades



O Dashboard é responsável por:



\- consolidar informações da plataforma;

\- destacar prioridades;

\- apresentar indicadores;

\- facilitar navegação;

\- reduzir tempo de tomada de decisão;

\- servir como ponto central da operação.



Ele não executa processamento.



Ele apresenta inteligência.



\---



\## 15.3 Fontes de Dados



Todas as informações exibidas são provenientes do Backend.



Principais fontes:



\- Decision Engine;

\- Opportunity Engine;

\- Executive Engine;

\- Guest Intelligence Engine;

\- Banco de Dados;

\- APIs Oficiais.



O Frontend nunca produz dados operacionais.



\---



\## 15.4 Estrutura



A arquitetura do Dashboard é composta por módulos independentes.



Na versão atual, os principais módulos são:



\- Executive Summary;

\- Opportunities;

\- Chats (com Respostas Rápidas);

\- Guest Profile;

\- Recent Activity;

\- Reservas;

\- Mapa de Quartos (housekeeping);

\- Financeiro;

\- Relatórios;

\- Estoque;

\- Operações;

\- Receitas (catálogo de upsells);

\- Eventos (espaços, agenda e adicionais — ver Capítulo 16);

\- Portfólio/Parceiros (catálogo de itens de agência e opt-in de

  parceria entre hospedagens — só visível para conta `agency`, oculta

  Estoque/Operações/Eventos/KPIs de hospedagem nesse tipo de conta;

  adicionado em 13/08/2026, versão 1.47.0, ver Capítulo 16, seção

  16.33);

\- Equipe (gestão de funções e permissões);

\- Configurações (com Billing, ver Capítulo 17);

\- Ask StayFlow (agente conversacional flutuante, com visão de imagem

  desde a v1.47.0 — ver 16.27);

\- Navegação Principal.



Novos módulos poderão ser incorporados sem alterar a arquitetura existente.



\---



\## 15.5 Navegação



O Dashboard funciona como um Centro de Comando.



Cada módulo deve permitir acesso direto à área correspondente da plataforma.



O usuário nunca deve percorrer múltiplas telas para executar uma ação importante.



A navegação deve ser rápida, previsível e consistente.



\---



\## 15.6 Princípios de Interface



Toda informação apresentada deve possuir:



\- contexto;

\- prioridade;

\- clareza;

\- utilidade.



Indicadores sem aplicação prática não devem ocupar espaço na interface.



A interface deve privilegiar compreensão imediata.



\---



\## 15.7 Evolução



O Dashboard deverá evoluir continuamente para incorporar novas capacidades da plataforma.



Entre as evoluções previstas estão:



\- Revenue Management avançado (o catálogo básico de upsells já está

  implementado, ver Capítulo 16);

\- Ocupação em tempo real (o Mapa de Quartos já cobre o status físico
  de cada cama — falta uma visão agregada de ocupação por período);

\- Calendário Operacional;

\- Indicadores personalizados.



Já implementados nesta frente, portanto removidos da lista de futuro:
Housekeeping (Mapa de Camas — ver 16.24), Comandos por IA (Ask
StayFlow como agente real — ver 16.27) e Notificações Inteligentes
nativas no aparelho (Web Push API, service worker, VAPID — atualizado
em 05/08/2026, versão 1.43.0, ver Capítulo 16).



Toda expansão deverá preservar simplicidade e consistência.



\---



\## 15.8 Objetivo de Longo Prazo



O Dashboard da StayFlow deverá tornar-se a principal ferramenta de gestão operacional da hotelaria.



Seu papel não será apenas apresentar dados.



Seu papel será explicar o negócio, antecipar problemas e orientar decisões em tempo real.



\---



\## Decisões Consolidadas



\- O Dashboard representa o Centro de Comando Inteligente da StayFlow.

\- Toda informação apresentada é proveniente do Backend.

\- O Dashboard organiza inteligência, não executa regras de negócio.

\- A navegação deve reduzir o tempo necessário para tomar decisões.

\- Cada módulo possui responsabilidade própria.

\- O Dashboard evoluirá continuamente conforme novas capacidades forem incorporadas ao produto.



\---



<a id="capitulo-16"></a>



\# 16. FUNCIONALIDADES IMPLEMENTADAS



Este capítulo registra oficialmente as funcionalidades implementadas na StayFlow.



Seu objetivo é manter um inventário técnico do produto, permitindo que qualquer integrante da equipe compreenda rapidamente o estado atual da plataforma.



Somente funcionalidades efetivamente implementadas devem constar como concluídas.



Funcionalidades em desenvolvimento ou planejadas deverão ser registradas no Roadmap Oficial.



\---



\## 16.1 Dashboard Inteligente



\*\*Status:\*\* Implementado



\### Objetivo



Centralizar toda a inteligência operacional da plataforma em uma única interface.



\### Capacidades atuais



\- Executive Summary;

\- Opportunities;

\- Recent Activity;

\- Chats;

\- Guest Profile;

\- Navegação principal.



\---



\## 16.2 Sistema de Chats



\*\*Status:\*\* Implementado



\### Objetivo



Centralizar todas as conversas realizadas pela plataforma.



\### Capacidades atuais



\- listagem de conversas;

\- histórico, com divisores de data entre mensagens (estilo WhatsApp);

\- identificação de bandeira de país por código de telefone;

\- exibição do nome do hóspede (quando capturado — ver 16.19) em vez do
  telefone, tanto na lista de conversas quanto no título da conversa
  aberta, com telefone como reserva (fallback) quando o nome ainda não
  foi coletado;

\- integração com IA;

\- atualização automática das informações operacionais;

\- \*\*fotos (adicionado em versão 1.48.0)\*\*: antes, toda imagem recebida
  de um hóspede era arquivada automaticamente como "documento de
  identidade", mesmo sem ser uma foto de documento, e a IA nunca via a
  imagem. Agora `messages.media\_path`/`media\_mime\_type`/`media\_token`
  guardam a mídia de verdade, o webhook do WhatsApp/Meta passa a
  encaminhar a foto pro pipeline normal de atendimento
  (`process\_incoming\_message`, que aceita `media\_bytes`/
  `media\_mime\_type`), e `ask\_ai()` (`services/ai\_service.py`) ganhou
  suporte a visão (conteúdo multimodal `image\_url`), então a IA reage
  de verdade ao que está na foto em vez de ignorá-la. Equipe também
  pode enviar foto pro hóspede (`POST /guests/<id>/send-photo` e
  equivalente em "Meu chat"), despachada pelo canal real do hóspede
  (`send\_whatsapp\_image`/`send\_messenger\_image`/`send\_instagram\_image`
  — corrigido de brinde um bug real: `send\_message\_to\_guest\_now` só
  mandava por WhatsApp antes, independente do canal de origem do
  hóspede). Rota pública `GET /media/chat/<token>` (token de 16
  caracteres hex, sem sessão) existe porque as APIs da Meta baixam a
  imagem enviada, e não conseguem autenticar com cookie de sessão.



\---



\## 16.3 Executive Summary



\*\*Status:\*\* Implementado



\### Objetivo



Produzir um resumo executivo da operação.



\### Capacidades atuais



\- panorama geral;

\- prioridades;

\- oportunidades;

\- riscos;

\- recomendações iniciais.



\---



\## 16.4 Opportunity Center



\*\*Status:\*\* Implementado



\### Objetivo



Apresentar oportunidades identificadas automaticamente pelos motores de inteligência.



\### Capacidades atuais



\- score;

\- urgência;

\- valor estimado;

\- status;

\- próxima ação;

\- sugestão de item de parceiro (adicionado em 13/08/2026, versão

  1.47.0): quando o Decision Engine identifica intent `tour` e a

  hospedagem não vende esse tipo de experiência mas existe algum item

  de `portfolio\_items` habilitado via `partner\_offers`, a oportunidade

  grava `suggested\_partner\_item\_id`. Desde a versão 1.57.0 (23/08/2026)

  a escolha tem matching semântico de verdade: a mesma chamada de IA

  do `analyze\_with\_ai` recebe a lista de itens habilitados (nome,

  categoria, descrição) e escolhe qual combina com o pedido real do

  hóspede, com validação contra a lista de ids oferecidos pra não

  aceitar uma escolha alucinada — dívida técnica registrada na v1.47.0

  agora resolvida. O Frontend (`stayflow-live.js`) mostra "💡

  Sugestão: {item} via {agência}" com botão "Oferecer parceiro" que

  abre o modal de cobrança já existente com `chargeType='partner\_item'`,

  reaproveitando a resolução de vendedor do Mercado Pago Split sem

  alterá-la. Ver Capítulo 14, seção 14.3, e Capítulo 16, seção 16.33.



\---



\## 16.5 Guest Profile



\*\*Status:\*\* Implementado



\### Objetivo



Concentrar informações relevantes sobre cada hóspede.



\### Capacidades atuais



\- perfil completo do hóspede (atualizado em 31/07/2026, versão 1.22.0
  em diante): contato editável (nome, telefone, email, endereço, data
  de nascimento, nacionalidade), documento (tipo + número, editáveis) e
  galeria de fotos do documento, com upload manual ou recebimento
  automático via WhatsApp/Messenger;

\- abre em modo leitura por padrão (campos fixos, "—" quando vazio), com
  botão explícito "Editar" para alternar ao formulário;

\- histórico completo de estadias com status e valor, incluindo saldo
  devedor/crédito calculado ao vivo para hóspedes de Longa Duração;

\- selo discreto do canal de origem (WhatsApp/Messenger/Instagram);

\- acessível por clique no nome do hóspede em qualquer lugar do sistema
  que já exiba `guest\_id` (aba Hóspedes, Reservas, morador de Longa
  Duração, lista de reservas canceladas);

\- histórico de conversas;

\- oportunidades relacionadas;

\- histórico de câmbios feitos com o hóspede, quando houver (atualizado
  em 04/08/2026, versão 1.41.0 — ver 16.11);

\- seção de Privacidade com exclusão de dados de uso único (atualizado
  em 04/08/2026, versão 1.40.0): apaga documentos e conversas de
  verdade, anonimiza nome/telefone/email/data de nascimento/
  nacionalidade/documento, mantendo reservas e valores sem identificar
  a pessoa — atende pedido de direito ao esquecimento (LGPD/Ley
  25.326), com confirmação forte antes de executar (ação
  irreversível);

\- informações consolidadas da operação.



\---



\## 16.6 Banco de Dados



\*\*Status:\*\* Implementado



\### Capacidades atuais



Persistência de:



\- hostels (multi-tenant, com credenciais de WhatsApp, Facebook Messenger, Instagram Direct e Beds24 por unidade);

\- identidade única de pessoa, funções por hostel e exceções individuais de permissão;

\- hóspedes, com identidade multi-canal e documentos de identidade;

\- mensagens (com timestamp por mensagem) e respostas rápidas (Quick Replies);

\- oportunidades;

\- reservas, incluindo hóspede de Longa Duração com saldo devedor/crédito;

\- Mapa de Quartos (modalidades, quartos, camas, ciclo de lavanderia);

\- credenciais e mapeamento do Channel Manager Beds24, com log cru de webhooks recebidos;

\- configurações do hostel;

\- fornecedores e itens de estoque;

\- catálogo de experiências/upsells (offerings);

\- sessões ativas e tentativas de login;

\- câmbios (cotação usada, cotação de mercado, lucro, operador —
  atualizado em 04/08/2026, versão 1.41.0);

\- inscrições de notificação push por dispositivo e segredo/códigos de
  backup de autenticação em duas etapas (atualizado em 05/08/2026,
  versões 1.43.0 e 1.44.0);

\- espaços, reservas e adicionais de eventos (atualizado em 05/08/2026,
  versão 1.45.0).



O banco representa a memória operacional da plataforma.



\---



\## 16.7 APIs Oficiais



\*\*Status:\*\* Implementado



\### APIs disponíveis



\- Autenticação (login, sessão, logout);

\- Dashboard;

\- Chats;

\- Quick Replies (respostas rápidas);

\- Guests;

\- Opportunities;

\- Activity;

\- Executive Summary;

\- Ask StayFlow (`/ask`, agente conversacional com histórico próprio);

\- Reservations;

\- Rooms / Bed Map (Mapa de Quartos: modalidades, quartos, camas,
  check-in/check-out, lavanderia);

\- Finance;

\- Reports;

\- Inventory (fornecedores e estoque);

\- Operations;

\- Revenue;

\- Team e Roles (gestão de equipe, funções e permissões);

\- Security (troca de senha, sessões ativas, tentativas de login,
  autenticação em duas etapas — ver 16.28);

\- Push (inscrição e status de notificação push por dispositivo — ver
  nova seção de Notificações Push);

\- Events (espaços, eventos, adicionais e disponibilidade — ver nova
  seção de Eventos);

\- Settings (inclui Beds24, Meta OAuth de Facebook/Instagram);

\- WhatsApp Webhook;

\- Meta Webhook (Messenger e Instagram Direct, endpoint compartilhado);

\- Beds24 Webhook (entrada de reservas de OTAs via Channel Manager);

\- Webhook de saída (notificação assinada para sistemas de clientes).



Novas APIs serão adicionadas conforme a evolução da plataforma.



\---



\## 16.8 Arquitetura Base



\*\*Status:\*\* Implementado



A arquitetura atual possui:



\- Frontend independente;

\- Backend modular;

\- SQLite;

\- APIs REST;

\- Motores de Inteligência;

\- separação clara entre responsabilidades.



Essa estrutura representa a fundação oficial da StayFlow.



\---



\## 16.9 Integração com WhatsApp Business



\*\*Status:\*\* Implementado e validado em produção



\### Objetivo



Permitir que hóspedes se comuniquem com o hostel diretamente pelo WhatsApp, com respostas automáticas geradas pela Inteligência Artificial da plataforma.



\### Capacidades atuais



\- recebimento de mensagens reais via webhook oficial da Meta Cloud API;

\- identificação automática do hostel a partir do número que recebeu a mensagem;

\- geração de resposta pela IA com base no histórico da conversa;

\- envio da resposta de volta ao hóspede pelo WhatsApp real;

\- credenciais (Phone Number ID e Token de Acesso) armazenadas por hostel, preparando o sistema para múltiplos hostels com números próprios;

\- domínio oficial próprio (`stayflowsolutions.com`) com certificado HTTPS válido, usado como endereço do webhook.



\### Limitação de plataforma conhecida



A Meta impõe uma restrição de mensageria entre países que impede contas comerciais de WhatsApp Business de entregarem mensagens a destinatários localizados no \*\*Brasil\*\* e na \*\*Indonésia\*\*, quando a conta é registrada em outro país. Essa restrição:



\- é imposta diretamente pela Meta, sem alternativa de configuração do lado da StayFlow;

\- não impede o recebimento de mensagens desses países, apenas o envio de resposta;

\- não possui, até o momento, previsão oficial de encerramento;

\- pode ser contornada apenas através do registro de uma conta de WhatsApp Business adicional, localizada no país do destinatário.



Essa limitação é relevante para o produto por afetar hóspedes brasileiros de hostels localizados fora do Brasil, e deve ser considerada em decisões futuras de expansão e atendimento.



\---



\## 16.10 Módulo de Reservas



\*\*Status:\*\* Implementado



\### Objetivo



Gerenciar as reservas dos hóspedes de cada hostel, de qualquer origem
(manual, WhatsApp, Messenger, Instagram ou OTA via Beds24), com o mesmo
nível de controle da equipe sobre o ciclo completo (pendente até
check-out).



\### Capacidades atuais



\- listagem e criação de reservas, com seletor de cama real (dependente
  da modalidade escolhida, sufixo "Beliche - Cima/Baixo" quando
  aplicável) e cálculo automático de valor pelo preço configurado (sem
  sobrescrever valor digitado manualmente, ex.: desconto negociado);

\- botões "Check-in"/"Check-out" na própria linha da reserva,
  reaproveitando as mesmas rotas do Mapa de Quartos — confirmam a
  mudança de status físico da cama (`checked\_in\_at`/`checked\_out\_at`),
  distinto do status comercial da reserva;

\- coluna de Origem com selo formatado por canal (Airbnb, Booking.com,
  Hostelworld, WhatsApp, Direto etc.);

\- nome do hóspede clicável, levando ao perfil completo (ver 16.5);

\- modal "Ver cancelamentos", com opção de reativar sem sair da tela;

\- \*\*reserva criada por WhatsApp/Messenger/Instagram nasce sempre como
  `pending`\*\* — a IA já reúne toda a informação necessária (datas,
  modalidade, cama disponível, preço) e é tecnicamente capaz de
  confirmar sozinha, mas essa é uma escolha deliberada de produto
  (controle da equipe, proteção contra overbooking), não uma limitação
  técnica; reserva criada manualmente nasce já confirmada;

\- ao confirmar ou cancelar uma reserva originada de chat, o hóspede é
  avisado de volta no mesmo canal (`notify\_guest\_reservation\_status`),
  com horário de check-in e endereço na confirmação (WhatsApp,
  Messenger e Instagram — corrigido nesta auditoria: esta seção estava
  desatualizada, dizendo que Instagram não tinha envio implementado;
  o código (`database.py`) já suporta os três canais desde a v1.37.0,
  como a seção 16.26 já registrava corretamente);

\- suporte a hóspede de Longa Duração (estadia sem data de saída fixa,
  saldo devedor/crédito calculado sob demanda — ver 16.6);

\- sincronização bidirecional com o Beds24 quando a reserva/estadia não é
  de Longa Duração (ver Integração com Channel Manager, mais adiante
  neste capítulo).



\---



\## 16.11 Módulo Financeiro



\*\*Status:\*\* Implementado



\### Objetivo



Consolidar a visão financeira da operação a partir de dados já existentes

na plataforma.



\### Capacidades atuais



\- reaproveita dados de Reservas e Opportunities, sem duplicar informação

  em tabela própria;

\- inclui pagamentos de hóspede de Longa Duração (`reservation\_payments`)
  na receita confirmada — valor de reserva fixa continua vindo de
  `reservations.amount`, já que são modelos de cobrança diferentes;

\- extrato de movimentações com linha própria para pagamento de estadia
  de Longa Duração;

\- \*\*casa de câmbio\*\* (atualizado em 04/08/2026, versão 1.41.0): registro
  de pagamento recebido em moeda estrangeira, com cotação de mercado
  (referência automática — ancorada no dólar blue via Bluelytics
  quando a moeda da hospedagem é ARS, cruzada pra qualquer outra moeda
  recebida; taxa oficial direta via `open.er-api.com` nos demais
  casos) separada da cotação usada com o hóspede, lucro calculado na
  diferença, operador e horário registrados, vínculo opcional com o
  perfil do hóspede; entra na receita confirmada e no extrato de
  movimentações;

\- \*\*receita de eventos\*\* (atualizado em 05/08/2026, versão 1.45.0):
  eventos confirmados (preço base + adicionais) entram na receita
  confirmada e no extrato de movimentações, mesmo critério já usado
  pra reservas — ver Capítulo 16, seção de Eventos.



\---



\## 16.12 Módulo de Relatórios



\*\*Status:\*\* Implementado



\### Objetivo



Apresentar indicadores agregados da operação.



\### Capacidades atuais



\- receita por canal;

\- funil de conversão.



\---



\## 16.13 Módulo de Estoque



\*\*Status:\*\* Implementado



\### Objetivo



Controlar fornecedores e itens de estoque, antecipando a necessidade de

reposição.



\### Capacidades atuais



\- cadastro de fornecedores e itens (categoria, quantidade, quantidade

  mínima, fornecedor vinculado);

\- alertas automáticos de estoque baixo;

\- geração de mensagem sugerida, pronta para copiar e enviar ao

  fornecedor, quando um item atinge o nível mínimo;

\- edição, exclusão e marcação de item como esgotado.



\---



\## 16.14 Módulo de Operações



\*\*Status:\*\* Implementado



\### Objetivo



Agregar alertas operacionais do dia a dia em um único lugar.



\### Capacidades atuais



\- alertas de check-in/check-out pendente, incluindo chegada do dia sem
  check-in físico ainda confirmado;

\- alertas de oportunidade urgente sem resposta;

\- alertas de estoque baixo;

\- tarefas de limpeza (housekeeping) espelhadas em tempo real do Mapa de
  Quartos: toda cama que sai do check-out entra automaticamente na lista
  de limpeza, com contagem no sininho de notificações do topbar (ver
  Mapa de Quartos, mais adiante neste capítulo);

\- alerta de nova reserva vinda de qualquer canal automático (WhatsApp,
  Messenger, Instagram, Beds24/qualquer OTA) nas últimas 24h;

\- atualização automática entre Operações e Mapa de Quartos após qualquer
  ação que muda status de cama/reserva (check-in, check-out, marcar
  como limpa), sem precisar recarregar a página;

\- \*\*Cozinha, Manutenção, Segurança Patrimonial e Estacionamento\*\*
  (adicionados em 04/08/2026, com permissões próprias `kitchen`/
  `maintenance`/`patrimonial\_security`/`parking` e IA integrada — a IA
  de atendimento pode abrir chamado de cozinha direto pela conversa,
  sem passar pela equipe) consolidados como abas dentro da própria
  página de Operações (não páginas próprias no menu lateral), cada uma
  com sua permissão específica ainda respeitada; os quatro compartilham
  um sistema genérico de "chamado" (`tickets`, com urgência e fila
  calculada por espera dentro do mesmo nível de urgência) e de
  notificação pra quem está de plantão
  (`notify\_on\_duty\_staff\_for\_ticket`, cobrindo tanto chamado aberto
  pela equipe quanto chamado aberto pela própria IA a partir de uma
  conversa — ver a seção de Notificações Push). \*\*Esta rodada inteira
  (04/08/2026) nunca tinha sido registrada neste documento nem no
  Diário de Engenharia\*\* até a auditoria retroativa de 05/08/2026
  (versão 1.46.0) — ver Capítulo 18;

\- \*\*botão de abrir chamado manual\*\* nas abas Cozinha, Manutenção e

  Segurança Patrimonial (adicionado em 13/08/2026, versão 1.47.0) — as

  rotas (`POST /kitchen/orders`, `/maintenance/tickets`,

  `/patrimonial-security/incidents`) já existiam desde 04/08/2026 e já

  disparavam `notify\_on\_duty\_staff\_for\_ticket`, mas não havia nenhum

  botão no Dashboard ligado a elas — a equipe só conseguia abrir

  chamado indiretamente, pela IA. Estacionamento ganhou botão

  equivalente dedicado no topo da própria aba, abrindo modal de

  escolha de veículo (mesma rota `POST

  /parking/vehicles/<id>/valet-request` já existente);

\- \*\*aba "Tarefas"\*\* (adicionada em 13/08/2026, versão 1.47.0): chamado

  avulso que não se encaixa em cozinha/manutenção/segurança (ex:

  "trocar lâmpada do corredor"). `POST /operations/tasks` reaproveita a

  tabela `tickets` já existente (`type='task'`), sem criar tabela nova

  — diferente dos outros quatro tipos, não notifica nenhum setor de

  plantão automaticamente (não existe um setor fixo pra tarefa

  genérica). `POST /operations/tasks/<id>/resolve` conclui a tarefa;

  aparece misturada na mesma lista de alertas que já mostrava limpeza

  pendente, com botão "concluir" próprio (diferente da limpeza, que

  resolve sozinha ao marcar a cama como limpa).



\---



\## 16.15 Módulo de Receitas (Upsell)



\*\*Status:\*\* Implementado



\### Objetivo



Apresentar o catálogo de experiências/upsells do hostel e as oportunidades

de venda adicional identificadas pela IA.



\### Capacidades atuais



\- catálogo de experiências/upsells (tabela `offerings`);

\- oportunidades já classificadas pela IA como `tour`/`upsell`

  (reaproveitadas do Decision Engine).



\---



\## 16.16 Autenticação e Sessão



\*\*Status:\*\* Implementado e validado em produção



\### Objetivo



Garantir que o acesso ao Dashboard dependa de uma sessão real e

verificável, com suporte a uma pessoa possuir acesso a mais de um

hostel simultaneamente.



\### Capacidades atuais



\- identidade única por pessoa (e-mail globalmente único), independente

  de quantos hostels ela tenha acesso;

\- login que reconhece automaticamente se a pessoa tem acesso a mais de

  um hostel e, nesse caso, apresenta a lista para escolha antes de

  liberar a sessão completa;

\- troca de hostel a qualquer momento, sem necessidade de nova senha

  (equivalente à troca de conta/workspace de ferramentas como Slack ou

  Notion);

\- verificação de sessão real via endpoint dedicado (`/me`), que devolve

  também a função e as permissões efetivas da pessoa no hostel atual, e

  a lista dos demais hostels disponíveis;

\- logout funcional;

\- link de cadastro (Register.html) disponível na tela de Login para novos

  hostels.



\---



\## 16.17 Arquitetura de CSS / Design System



\*\*Status:\*\* Implementado



\### Objetivo



Sustentar consistência visual entre as páginas da plataforma através de

uma fonte única de tokens de design, eliminando a duplicação de estilo

que causava bugs reais de experiência do usuário.



\### Capacidades atuais



\- tokens de design centralizados (cores, raio de borda, sombra,

  breakpoints), com `#0b84ff` como cor oficial da marca;

\- reset universal compartilhado entre páginas;

\- arquivos de estilo separados por responsabilidade (aplicação, landing

  page, autenticação), evitando colisão de nomes de classe entre eles;

\- correção das principais dívidas de responsividade mobile identificadas

  no Roadmap Oficial (ver Capítulo 17).



\---



\## 16.19 Captura do Nome do Hóspede via Inteligência Artificial



\*\*Status:\*\* Implementado e validado em produção com número real de
WhatsApp



\### Objetivo



Permitir que o nome do hóspede seja reconhecido durante a conversa natural
com a IA e persistido automaticamente, sem exigir formulário ou pergunta
estruturada separada.



\### Capacidades atuais



\- a IA identifica quando o hóspede declara o próprio nome durante a
  conversa e aciona uma ferramenta estruturada (function calling da
  OpenAI), separada do texto da resposta enviada ao hóspede;

\- o nome capturado é persistido no cadastro do hóspede automaticamente,
  sem intervenção manual;

\- a captura ocorre no máximo uma vez por conversa, evitando sobrescrever
  o nome já registrado se o hóspede mencionar outro nome depois;

\- validado de ponta a ponta com uma conversa real de WhatsApp em
  produção, confirmando a gravação correta no banco de dados.



\### Limitação conhecida



Conversas anteriores à implementação desta funcionalidade não têm o nome
preenchido retroativamente — o campo permanece vazio (com telefone como
reserva na exibição) até que o hóspede converse novamente após a
funcionalidade estar ativa.



\---



\## 16.20 Indicadores Reais de Status do Sistema



\*\*Status:\*\* Implementado



\### Objetivo



Garantir que o painel de Configurações informe o estado verdadeiro de
conectividade do Backend e da integração com WhatsApp Business, em vez de
texto fixo.



\### Capacidades atuais



\- indicador de conexão com o Backend, atualizado a partir da resposta
  real da API de configurações;

\- indicador de conexão com o WhatsApp Business, atualizado a partir da
  presença confirmada de credenciais válidas (identificador do número e
  token de acesso).



\---



\## 16.21 Painel de Equipe



\*\*Status:\*\* Implementado e validado em produção



\### Objetivo



Permitir a gestão completa da equipe de cada hostel: convidar pessoas,
atribuir e trocar funções, ajustar exceções individuais de permissão, e
desativar/reativar acesso — tudo a partir de uma interface dedicada,
acessível tanto pelo menu principal quanto pelo atalho da barra lateral.



\### Capacidades atuais



\- listagem de todos os membros do hostel (ativos e inativos), com nome,
  e-mail, função e contagem de permissões efetivas;
\- convite de pessoa nova ou já existente na plataforma (se o e-mail já
  é uma identidade cadastrada, apenas cria o vínculo com o hostel; se é
  pessoa nova, cria a identidade com senha temporária de uso único,
  exibida apenas no momento do convite);
\- troca da função de qualquer membro;
\- ajuste de exceções individuais de permissão por pessoa, com
  distinção visual clara entre o que vem por padrão da função
  ("herdado") e o que foi ajustado manualmente para aquela pessoa
  específica;
\- desativação e reativação de acesso, sem apagar histórico;
\- aba dedicada de gestão de Funções: criar, editar (nome e permissões)
  e apagar funções do hostel, com seleção das 20 permissões disponíveis
  por checkbox.



\### Limitação histórica corrigida nesta versão



Este módulo nunca teve a marcação visual (HTML) do painel criada, apesar
da lógica de carregamento já existir — descoberta registrada na versão
1.4.0. Reconstruído por completo nesta versão, junto com toda a
funcionalidade de gestão descrita acima.



\---



\## 16.22 Sistema de Permissões Multi-Hostel



\*\*Status:\*\* Implementado e validado em produção



\### Objetivo



Permitir que uma mesma pessoa tenha acesso a múltiplos hostels de forma
independente, e que cada hostel controle com precisão o que cada membro
da equipe pode ver e fazer na plataforma.



\### Capacidades atuais



\- catálogo de 20 permissões, uma por seção principal do produto
  (dashboard, chats, opportunities, reservations, operations, guests,
  finance, reports, inventory, revenue, settings, team, security,
  billing, kitchen, maintenance, patrimonial\_security, parking,
  scheduling, events — security/billing adicionadas junto com a
  construção das telas de Segurança e Billing dentro de Configurações;
  kitchen/maintenance/patrimonial\_security/parking/scheduling
  adicionadas em 04/08/2026 junto com os módulos operacionais
  correspondentes (ver 16.14 e 16.32); events adicionada em
  05/08/2026, versão 1.45.0, junto com o módulo de Eventos), centralizado
  numa única fonte de verdade (`utils/permissions.py`) reutilizada por
  todas as camadas do sistema (migração de dados, controle de acesso
  das rotas, interface);
\- toda rota protegida da plataforma exige a permissão específica
  correspondente à sua área, verificada a cada requisição — nunca
  apenas "estar logado";
\- funções totalmente configuráveis por hostel (o administrador decide
  quais das 20 permissões cada função concede, sem funções fixas
  impostas pelo sistema além dos padrões "Admin" e "Staff" criados
  automaticamente na migração);
\- exceções de permissão por pessoa individual, por cima do padrão da
  função dela, sem afetar as demais pessoas com a mesma função;
\- proteções de segurança automáticas: nenhuma alteração (troca de
  função, exceção individual ou desativação) pode deixar um hostel sem
  nenhuma pessoa capaz de gerenciar a própria equipe; uma função só pode
  ser apagada quando nenhum vínculo, ativo ou inativo, ainda a
  referencia;
\- navegação principal da plataforma escondendo automaticamente as
  seções que a pessoa logada não tem permissão para acessar.



\### Nota de arquitetura



Diferente do restante da sessão do usuário (que guarda apenas a
identidade da pessoa e o hostel atualmente selecionado), a permissão
efetiva de cada pessoa nunca é armazenada em cache — é recalculada a
partir do banco de dados a cada requisição, garantindo que qualquer
ajuste feito por um administrador valha imediatamente, sem exigir novo
login de quem foi afetado.



\---



\## 16.23 Configurações de Inteligência Artificial



\*\*Status:\*\* Parcialmente implementado (um dos dois controles
depende de um recurso futuro)



\### Objetivo



Permitir que o administrador do hostel controle aspectos do
comportamento da Inteligência Artificial diretamente pela interface,
sem depender de alteração de código.



\### Capacidades atuais



\- controle real de geração de oportunidades: quando desativado pelo
  administrador, a plataforma deixa de registrar novas oportunidades
  comerciais a partir das conversas, sem afetar a geração normal de
  respostas pela IA;

\- a preferência é persistida por hostel e recalculada a cada mensagem
  recebida — não existe atraso nem necessidade de reiniciar nada para
  a mudança valer.



\### Limitação conhecida



O controle de "resposta automática" permanece desabilitado na
interface, com aviso explícito ao administrador. Este controle só
poderá ser implementado de forma real quando existir um mecanismo de
revisão humana antes do envio de mensagens de atendimento — o padrão
propor→aprovar→enviar já existe para ações proativas específicas
(pedido de reposição a fornecedor, aviso proativo a hóspede — ver 16.27)
mas ainda não cobre o fluxo geral de resposta automática do chat. Sem
esse mecanismo, desativar a resposta automática significaria
simplesmente parar de responder o hóspede, o que não é o comportamento
pretendido pelo controle.



\---



\## 16.24 Mapa de Quartos (Room Map / Housekeeping)



\*\*Status:\*\* Implementado e validado em produção



\### Objetivo



Dar visibilidade em tempo real do status físico de cada cama da
propriedade e automatizar o ciclo operacional de limpeza e lavanderia,
eliminando controle manual em papel ou planilha.



\### Capacidades atuais



\- modalidades de quarto configuráveis por propriedade (`room\_categories`),
  com padrão automático por tipo de hospedagem (hostel ganha
  Privado/Compartilhado, hotel/pousada/resort ganham Standard/Luxo);

\- cadastro de quartos em lote e camas normais ou pareadas (beliche,
  com sufixo "Cima"/"Baixo"), com edição e exclusão (bloqueada se a
  cama estiver ocupada);

\- cinco estados visuais reais, refletidos em mapa colorido: livre,
  ocupada (vermelha), ocupada por hóspede de Longa Duração (roxa,
  distinta da ocupação comum), precisa de limpeza (amarela), reservada
  (azul — só a partir do dia do check-in, não semanas antes) e em
  manutenção;

\- ciclo completo de lavanderia: check-out move a cama para a lista de
  limpeza automaticamente; marcar como limpa desconta roupa de cama
  limpa do estoque e move para "na lavanderia"; ação de devolução ao
  estoque quando a lavanderia retorna;

\- check-in/check-out confirmados a partir do próprio Mapa de Quartos ou
  da aba Reservas (mesmas rotas), com seletor de cama livre que
  pré-seleciona a já atribuída automaticamente por canal/WhatsApp;

\- lista de limpeza espelhada em tempo real na aba Operações e no
  sininho de notificações do topbar;

\- ações de criação (categoria, quarto, cama) organizadas em um único
  menu "☰ Ações" no card do mapa, abrindo modal central, deixando o
  mapa visual como conteúdo permanente da tela.



\---



\## 16.25 Integração com Channel Manager (Beds24)



\*\*Status:\*\* Implementado e validado em produção (6 fases concluídas)



\### Objetivo



Receber e sincronizar reservas de OTAs (Booking.com, Airbnb,
Hostelworld, Expedia, Agoda, Vrbo) automaticamente, sem exigir que o
hóspede fale com o hostel para reservar por fora do StayFlow, e sem
expor ao cliente final nenhuma plataforma terceira no meio do processo.



\### Capacidades atuais



\- modelo agência/white-label: uma conta master do StayFlow no Beds24,
  cada hostel-cliente vira uma sub-propriedade, sem custo nem conta
  separada para o cliente final;

\- mapeamento de cada modalidade de quarto para o quarto correspondente
  na sub-propriedade do Beds24, com opção de criar o quarto lá direto
  pela própria StayFlow;

\- \*\*webhook de entrada\*\* (`POST /webhook/beds24/<secret>`) recebe em
  tempo real toda notificação de reserva nova ou alterada vinda de
  qualquer OTA conectada; grava o payload cru em `channel\_webhook\_events`
  antes de qualquer interpretação (nunca perde uma reserva por erro de
  formato de campo); protegido por idempotência
  (`try\_claim\_webhook\_event`/`finalize\_webhook\_event`, chave inclui
  `modifiedTime`) e por proteção contra duplicação por eco (quando a
  StayFlow cria a reserva primeiro e o Beds24 ecoa de volta quase na
  hora — `find\_recent\_unlinked\_stayflow\_reservation` vincula em vez de
  duplicar);

\- cria (`create\_reservation\_from\_channel`) ou atualiza
  (`update\_reservation\_from\_channel`) a reserva local automaticamente,
  sempre usando o valor vindo do canal/OTA (nunca recalculado pelo
  preço do StayFlow, já que a OTA pode vender com desconto);

\- \*\*saída/disponibilidade\*\*: toda criação, cancelamento ou reversão de
  cancelamento de reserva recalcula e empurra a disponibilidade real da
  modalidade para o Beds24 (`sync\_availability\_to\_channel`), fechando o
  risco de overbooking entre canais;

\- \*\*reserva de verdade\*\* (não só disponibilidade agregada):
  `sync\_booking\_to\_channel` cria a reserva no Beds24 na primeira vez que
  a origem é manual/WhatsApp/Messenger/Instagram e a reserva sai de
  `pending` (nunca publica reserva ainda pendente, nunca roda para
  reserva vinda do próprio Beds24, nunca roda para hóspede de Longa
  Duração);

\- \*\*webhook de saída genérico\*\*: cliente com sistema próprio cadastra
  uma URL em Configurações → Integrações e recebe um `POST` JSON
  assinado (`X-StayFlow-Signature`, HMAC-SHA256) para toda reserva
  criada, alterada, cancelada ou com check-in/check-out feito, de
  qualquer origem — só pra `account\_kind = "lodging"` (`dispatch\_reservation\_webhook`).
  Contas `agency` (imobiliária, estética automotiva, loja online etc.)
  não têm reserva/check-in, então usam um evento equivalente:
  `dispatch\_opportunity\_webhook` (`database.py`, adicionado em
  20/08/2026, versão 1.50.0) dispara `opportunity\_created`/
  `opportunity\_updated` sempre que o Decision Engine cria ou atualiza
  uma oportunidade aberta pra essa conta — é o evento de conversão
  real desse tipo de negócio, no lugar da reserva. Texto do modal de
  configuração muda de acordo com `account\_kind` pra não falar de
  "reserva" pra quem não tem esse conceito;

\- \*\*proteção multi-canal contra overbooking já em produção, não apenas
  planejada\*\*: `find\_available\_beds` (mecanismo de disponibilidade
  usado pela IA de atendimento) já considera reservas vindas de
  qualquer canal — IA, painel manual ou OTA via Beds24 — no mesmo
  cálculo.



\---



\## 16.26 Integração com Messenger e Instagram Direct



\*\*Status:\*\* Messenger implementado e validado em produção; Instagram
Direct conectado e funcional para envio, com uma limitação de
plataforma conhecida no recebimento via API de conversas



\### Objetivo



Estender o mesmo atendimento por Inteligência Artificial já validado no
WhatsApp para os outros canais de mensagem que o hóspede já usa no
dia a dia, com uma única identidade de conversa por hóspede
independente do canal.



\### Capacidades atuais



\- modelo de identidade multi-canal de verdade (`guest\_channel\_identities`,
  `UNIQUE(hostel\_id, channel, external\_id)`), em vez de forçar PSID/IGSID
  dentro de `guests.phone`; hóspede de WhatsApp criado antes da
  integração é adotado pelo telefone já existente, sem duplicar;

\- conexão via OAuth real para os dois canais (Facebook Login for
  Business com Configuration para Messenger; Instagram API with
  Instagram Login, stack separada com App ID/Secret próprios, para
  Instagram), com alternativa de configuração manual (Page/Business ID
  + Access Token) para os dois;

\- webhook único `/webhook/meta` para os dois canais, resolvido pelo
  campo `object` do payload (`"page"` = Messenger, `"instagram"` =
  Instagram), processado pelo mesmo pipeline de IA do WhatsApp;

\- Messenger/Instagram já entregam a conversa identificada — a IA usa o
  nome do perfil automaticamente na primeira mensagem, sem precisar
  perguntar (diferente do WhatsApp, onde o número não revela
  identidade);

\- recebimento de documento/imagem enviado pelo hóspede (Messenger via
  CDN da Send API, Instagram via `download\_instagram\_attachment`);

\- selo colorido do canal de origem na aba Chats, no título da conversa e
  no perfil do hóspede;

\- notificação automática de reserva confirmada/cancelada (ver 16.10)
  chega também por Messenger e Instagram;

\- IA sugere o número real de WhatsApp do hostel como contato
  alternativo quando a conversa acontece por um canal que não é o
  WhatsApp.



\### Limitação de plataforma conhecida (Instagram)



A Conversations API oficial do Instagram (`GET
/{instagram\_business\_id}/conversations`) devolve `HTTP 200` com `"data":
[]` (lista vazia) mesmo havendo mensagens reais acontecendo na conta —
confirmado por evidência técnica direta, não é bug de código do
StayFlow (versão de API, reinscrição de webhook e endpoint oficial já
descartados como causa). É uma restrição de "Standard Access" da
própria Meta: contas de teste/desenvolvimento não têm acesso total ao
conteúdo de mensagem por essa API até o aplicativo passar por App
Review e ganhar "Advanced Access" para as permissões
`instagram\_business\_basic` e `instagram\_business\_manage\_messages`.
Conexão de conta, assinatura de webhook e envio de mensagem continuam
funcionando normalmente — a submissão de App Review está preparada,
pendente de envio pelo usuário.



\---



\## 16.27 Ask StayFlow — Agente Conversacional Real



\*\*Status:\*\* Implementado e validado em produção



\### Objetivo



Permitir que o gestor converse em linguagem natural com a operação do
próprio hostel — não apenas visualizar dados, mas fazer a IA executar
consultas e ações reais sobre eles.



\### Capacidades atuais



\- agente real com function calling multi-rodada (não mais uma
  simulação de conversa), autenticado, com 34 ferramentas escopadas
  pela permissão de quem está perguntando;

\- endpoint `/ask` com histórico de conversa próprio, persistido em SQL
  (`ask\_messages`), separado do histórico de conversa com hóspedes;

\- fase de ações reais: pedido de reposição a fornecedor e aviso
  proativo a hóspede, ambos com fluxo propor→aprovar→enviar via
  WhatsApp Business antes de qualquer mensagem sair para fora do
  sistema;

\- responde no idioma atual selecionado no painel;

\- \*\*visão de imagem\*\* (adicionado em 13/08/2026, versão 1.47.0):

  `POST /ask` passa a aceitar `multipart/form-data` com campo `file`

  opcional (além do JSON puro já existente), limitado a

  `image/jpeg`/`image/png`/`image/webp` (não aceita PDF — é o formato

  que a câmera do celular gera e o único que o modelo "vê" direto via

  `image\_url`), convertida em data URI base64 e passada para

  `ask\_agent(..., image\_data\_url=...)`

  (`services/ask\_agent\_service.py`, modelo `gpt-4.1-mini` da OpenAI —

  este módulo específico não usa Claude/Anthropic). A partir da foto, a

  IA decide sozinha para qual setor ela faz sentido e chama a

  ferramenta certa sem exigir confirmação prévia (diferente do fluxo de

  reposição a fornecedor): `\_create\_kitchen\_order\_by\_name` (Estoque/

  Cozinha), `\_create\_maintenance\_ticket` (Manutenção) ou

  `\_create\_security\_incident` (Segurança Patrimonial) — as três chamam

  em seguida `notify\_on\_duty\_staff\_for\_ticket`, o mesmo mecanismo dos

  botões manuais de Operações (ver 16.14). O prompt de sistema instrui

  a IA a perguntar em vez de adivinhar quando a foto for ambígua ou

  faltar informação essencial.



\---



\## 16.28 Segurança



\*\*Status:\*\* Implementado



\### Objetivo



Dar ao usuário controle e visibilidade sobre o próprio acesso à
plataforma.



\### Capacidades atuais



\- troca de senha (`POST /security/change-password`);

\- listagem de sessões ativas por dispositivo/navegador, com opção de
  revogar uma sessão específica (`GET`/`DELETE /security/sessions`),
  bloqueando o próximo acesso dela imediatamente;

\- histórico das últimas tentativas de login, com indicação de sucesso
  ou falha (`GET /security/login-attempts`);

\- proteção contra força bruta no login: 5 tentativas erradas pro mesmo
  e-mail travam por 15 minutos (`count\_recent\_failed\_logins`,
  atualizado em 04/08/2026, versão 1.39.0);

\- cabeçalhos de segurança (`X-Content-Type-Options`, `X-Frame-Options`,
  `Referrer-Policy`, `Strict-Transport-Security`) e Content-Security-Policy
  em toda resposta (atualizado em 04/08/2026, versão 1.39.0 — CSP
  mantém `unsafe-inline` em script/style deliberadamente, ver nota
  abaixo);

\- verificação de assinatura dos webhooks da Meta (`X-Hub-Signature-256`,
  HMAC-SHA256 sobre o corpo cru), confirmada funcionando contra
  tráfego real da Meta em produção (atualizado em 04/08/2026, versão
  1.39.0);

\- \*\*autenticação em duas etapas (2FA/TOTP)\*\* (implementada em
  05/08/2026, versão 1.44.0): ativação com QR code + chave manual
  (compatível com Google Authenticator e apps equivalentes), gerado no
  servidor via `pyotp`/`qrcode` (SVG, sem CDN externo); confirmação
  com o primeiro código antes de habilitar de verdade; 8 códigos de
  backup de uso único mostrados apenas na ativação (hash bcrypt,
  aceitos com ou sem formatação); login com 2FA ativo passa por uma
  etapa intermediária (`challenge\_token` de 5 minutos/5 tentativas,
  `POST /login/2fa`) antes de a sessão de verdade ser criada — senha
  sozinha nunca basta pra quem ativou o 2FA.



\### Padrão de segurança estabelecido



Nenhuma rota `GET /settings/*` (WhatsApp, Facebook, Instagram, Beds24)
devolve o valor bruto de um `access\_token` para o Frontend — sempre
apenas um booleano (`has\_access\_token`). Essa é uma propriedade de
design consistente em todo o sistema, não uma decisão isolada de um
único canal.



\### Decisão permanente registrada (04/08/2026, versão 1.39.0)



A sessão nunca deve expirar automaticamente por tempo — nem de forma
absoluta, nem por inatividade. O usuário considera reentrar
recorrentemente um incômodo real; revogação continua existindo
normalmente (logout, troca de senha derruba as demais sessões,
revogação individual de uma sessão específica). Content-Security-Policy
mantém `unsafe-inline` em `script-src`/`style-src` de propósito —
remover essa exceção exigiria reescrever centenas de atributos
`onclick`/`onchange`/`onsubmit` inline pro padrão `addEventListener`,
avaliado como refatoração grande demais pra fazer sem capacidade de
teste visual real; `connect-src 'self'` já fecha o vetor mais grave
(exfiltração de dados por XSS), independente dessa exceção.

**Revisão desta decisão (23/08/2026, versão 1.60.0):** item reavaliado
com números concretos, não só revisitado — a decisão de não remover
`unsafe-inline` foi CONFIRMADA, não esquecida. Contagem atual: ~341
atributos de evento inline (`onclick`/`onchange`/`onsubmit`/`oninput`/
`onkeydown`), 81% em `dashboard.html` (10.881 linhas) e 17% em
`admin.html` (2.896 linhas) — crescido de ~186 (`onclick`/`onchange`/
`onsubmit`) desde a v1.39.0, confirmando que o custo só aumenta com o
tempo, nunca diminui; mais ~990 atributos `style=` inline (82% em
`dashboard.html`). Achado técnico novo que fecha a porta de uma
migração incremental: por especificação, assim que `script-src` ganha
um `'nonce-...'`, todo navegador compatível com CSP nível 2+ **ignora
`'unsafe-inline'` na mesma diretiva** — ou seja, não dá pra adicionar
nonce só nos ~14 blocos `<script>` inline mantendo os ~341 `onclick`
funcionando via `unsafe-inline` ao mesmo tempo; seria tudo ou nada.
Pra `style-src`, `'unsafe-hashes'` (CSP3) exigiria valor estático, e
boa parte dos 990 `style=` é gerada dinamicamente via JS (template
string com valor interpolado), invalidando hash fixo. Conclusão:
continua sendo puramente defesa em profundidade (o vetor grave já
está fechado por `connect-src 'self'`), sem meio-termo possível, e o
risco de regressão espalhada num arquivo de quase 11 mil linhas sem
teste visual automatizado não se justifica sem uma demanda real
(cliente enterprise pedindo auditoria de segurança formal, por
exemplo) — não é dívida técnica de rotina, é decisão de escopo válida
até que essa demanda apareça.



\---



\## 16.29 Respostas Rápidas (Quick Replies)



\*\*Status:\*\* Implementado



\### Objetivo



Permitir que a equipe responda perguntas frequentes na aba Chats sem
digitar o mesmo texto repetidamente.



\### Capacidades atuais



\- listagem, criação e exclusão de respostas rápidas por hostel
  (`GET`/`POST`/`DELETE /quick-replies`), protegidas pela permissão de
  `chats`.



\---



\## 16.30 Notificações Push (Web Push API)



\*\*Status:\*\* Implementado e testado contra o serviço real do Google
(FCM)



\### Objetivo



Avisar a equipe em tempo real, mesmo com a aba/app fechado, quando
algo relevante acontece — sem depender de a pessoa estar olhando o
Dashboard no momento.



\### Capacidades atuais



\- inscrição por dispositivo/pessoa (PC e celular contam como
  inscrições separadas), com chave pública VAPID gerada no servidor e
  service worker próprio (`sw.js`, servido na raiz do site pra cobrir
  o site inteiro); recurso fica desligado em silêncio se as chaves
  VAPID não estiverem configuradas no ambiente, mesmo padrão já usado
  pro `META_APP_SECRET`;

\- nove tipos de evento configuráveis por hospedagem (cada um pode ser
  ligado/desligado independente): nova oportunidade de alta
  prioridade, nova reserva pendente, hóspede com problema/dúvida/
  frustração detectado pela IA mesmo quando a mensagem não vira
  oportunidade de venda, mensagem nova numa conversa assumida
  manualmente pela equipe, novo pedido de cozinha, novo chamado de
  manutenção, nova ocorrência de segurança, novo chamado de
  manobrista, novo evento cadastrado — mais "toda mensagem nova no
  chat" (única desligada por padrão, por risco de virar ruído numa
  hospedagem movimentada; as demais vêm ligadas);

\- cada opção de "o que deve notificar" só aparece pra quem tem a
  permissão da área correspondente (manutenção só vê a notificação de
  manutenção, manobrista só a de estacionamento, e assim por diante),
  reaproveitando o mesmo mecanismo genérico de visibilidade por
  permissão já usado no menu lateral e em Configurações;

\- horário de silêncio (campo que já existia reservado exatamente pra
  esse uso desde a Sessão 7) suprime o envio nesse intervalo, sem
  afetar a resposta automática ao hóspede;

\- gatilho de chamado operacional (Cozinha/Manutenção/Segurança
  Patrimonial/Estacionamento) é único e cobre tanto chamado aberto
  pela equipe pelo painel quanto chamado aberto pela própria IA a
  partir de uma conversa, sem duplicar lógica;

\- inscrição expirada (navegador invalidou, ex: dados do navegador
  limpos) é removida automaticamente do banco assim que uma tentativa
  de envio recebe 404/410 do serviço de push.



\---



\## 16.31 Módulo de Eventos



\*\*Status:\*\* Implementado



\### Objetivo



Permitir que uma hospedagem alugue espaços (salões, jardins,
auditórios) pra eventos — casamentos, aniversários, corporativo,
conferências, formaturas — como receita própria, independente da
hospedagem em si. Conceito deliberadamente separado do Mapa de
Quartos: quarto/cama é pra hospedagem, espaço de evento é pra aluguel
por período, com cliente que não precisa ser hóspede.



\### Capacidades atuais



\- cadastro de espaços com capacidade (sentados e em pé) e preço de
  aluguel;

\- agenda de eventos com checagem de disponibilidade em tempo real —
  sobreposição de horário no mesmo espaço (considerando eventos
  pendentes ou confirmados, nunca cancelados) é rejeitada na criação;

\- ficha do cliente (nome, telefone, e-mail, vínculo opcional com um
  hóspede já cadastrado), tipo de evento, número esperado de
  convidados e status (pendente → confirmado → concluído, ou
  cancelado);

\- catálogo de adicionais/serviços extras (buffet, decoração, som,
  etc.), com preço congelado no momento em que são anexados a um
  evento — reajustar o catálogo depois não altera retroativamente um
  evento já fechado;

\- preço total do evento é sempre preço base (herdado do espaço, ou
  negociado por evento) mais a soma dos adicionais escolhidos;

\- receita de eventos confirmados entra automaticamente no Financeiro
  (ver 16.11);

\- notificação push própria pra novo evento cadastrado (ver 16.30).



\### Decisão de posicionamento na navegação



Eventos é item próprio na barra lateral, com permissão própria
(`events`) — avaliado explicitamente com o usuário e descartado tanto
dentro de Operações (que reúne "chamados" rápidos resolvidos por quem
está de plantão, um conceito diferente de reserva planejada com peso
financeiro próprio) quanto dentro de Reservas ou Receitas (que são
sobre hospedagem e upsell pro hóspede já hospedado, não aluguel de
espaço com cliente e calendário próprios).



\---



\## 16.32 Escala de Equipe (Scheduling)



\*\*Status:\*\* Implementado (adicionado em 04/08/2026, nunca registrado
neste documento nem no Diário de Engenharia até a auditoria retroativa
de 05/08/2026, versão 1.46.0 — ver Capítulo 18)



\### Objetivo



Organizar os turnos de trabalho da equipe por departamento e permitir
saber, a qualquer momento, quem está de plantão agora — usado pelo
gatilho de notificação de chamado operacional (Cozinha, Manutenção,
Segurança Patrimonial, Estacionamento — ver 16.14).



\### Capacidades atuais



\- setores configuráveis por departamento (`sections`);

\- grade de turnos (linha = pessoa, coluna = dia), filtrável por
  período (`GET /scheduling/shifts?start\_date=...&end\_date=...`);

\- criação de turno pra si mesmo ou pra outra pessoa da equipe
  (resolve automaticamente o vínculo da própria pessoa logada quando
  `membership\_id` não é informado);

\- consulta de quem está de plantão agora por departamento
  (`GET /scheduling/on-duty`), fonte usada pela notificação de chamado
  operacional;

\- pedido e aceite de cobertura de turno entre membros da equipe
  (`POST /scheduling/shifts/<id>/coverage-request` e
  `.../accept`);

\- aba própria dentro de Equipe (`data-team-tab="scheduling"`), com
  permissão dedicada `scheduling`.



\---



\## 16.33 StayFlow Hub, Importador de Dados (CSV) e Tour de Onboarding



\*\*Status:\*\* Implementado (adicionado em 13/08/2026, versão 1.47.0)



\### 16.33.1 StayFlow Hub (painel interno + impersonation)



\#### Objetivo



Dar à própria equipe da StayFlow (não ao cliente) uma visão de todas as
hospedagens e agências cliente da plataforma, com receita/comissão
real e a capacidade de entrar diretamente no dashboard de qualquer
conta para dar suporte, sem precisar da senha do cliente.



\#### Capacidades atuais



\- acesso restrito por allowlist de e-mail (variável de ambiente

  `STAYFLOW\_ADMIN\_EMAILS`, checada por

  `utils.tenant.is\_stayflow\_admin\_email`) — não existe uma role

  "superadmin" no banco de dados, a autorização é 100% allowlist;

\- `GET /stayflow-admin/overview` (`?kind=agency|lodging` opcional)

  lista todas as hospedagens/agências com MRR estimado (a partir de

  `PLAN\_PRICES`, nunca dinheiro de fato coletado da assinatura StayFlow

  — essa parte segue sem processador ligado, ver Capítulo 17) e

  comissão real coletada via Mercado Pago Split (`SUM(paid\_amount \*

  commission\_pct / 100.0)` sobre `guest\_charges`), mantidas

  deliberadamente separadas;

\- `GET /stayflow-admin/hostel/<id>` — perfil de uma hospedagem/agência

  específica (troca estatística de quarto/cama por estatística de

  portfólio quando é conta `agency`);

\- `GET /stayflow-admin/partner-ledger` e `POST

  /stayflow-admin/partner-ledger/payout` — acompanhamento e baixa

  manual do `partner\_referral\_ledger` (ver Capítulo 12, seção 12.3);

\- \*\*impersonation real\*\*: `POST /stayflow-admin/impersonate` (body

  `{hostel\_id}`) reaponta `sessions.hostel\_id` para a conta visitada,

  preservando o hostel de origem do administrador em

  `sessions.impersonating\_from\_hostel\_id`; `POST

  /stayflow-admin/stop-impersonating` devolve. Cada início/fim é

  registrado em `impersonation\_log`. Visita encadeada (admin visita B

  estando já em visita de A) preserva sempre o endereço de volta

  original, nunca aninha;

\- `require\_permission`/`require\_plan\_feature`/`get\_current\_user`

  (`utils/tenant.py`) liberam acesso equivalente a Admin quando

  `is\_impersonating()` é verdadeiro — documentado no próprio código

  como exceção deliberada à regra de que `hostel\_id` nunca vem do

  cliente;

\- banner visível no Dashboard (`#impersonationBanner`) enquanto uma

  sessão de impersonation está ativa, e link "Painel StayFlow" no menu

  para quem está na allowlist.



\#### Limitações conhecidas



Não existe tela de auditoria para ler o `impersonation\_log` (o registro

é gravado, mas nada no Dashboard exibe esse histórico ainda).



\---



\### 16.33.2 Importador de Dados (CSV)



\#### Objetivo



Permitir que uma hospedagem/agência que está migrando de outro sistema

carregue seus dados existentes em lote, em vez de recadastrar um por

um manualmente.



\#### Capacidades atuais



\- card "Importar dados" em Configurações, com modelo de CSV para

  download por tipo (`modelo\_quartos.csv`, `modelo\_hospedes.csv`,

  `modelo\_reservas.csv`, `modelo\_equipe.csv`, `modelo\_portfolio.csv`);

\- parser de CSV próprio em JavaScript (`parseImportCSV`, suporta campos

  entre aspas com vírgula interna), sem depender de biblioteca externa

  — o parsing acontece inteiramente no Frontend, o backend recebe JSON

  já estruturado (`{"rows": [...]}`);

\- `IMPORT\_FIELD\_ALIASES` mapeia nomes de coluna em português/inglês

  para os campos esperados pelo backend, e

  `IMPORT\_VALUE\_NORMALIZERS` normaliza valores (ex.: "fixo"/"a

  combinar" → `fixed`/`variable`);

\- rotas por tipo de dado, todas `POST` recebendo `{"rows": [...]}`:

  \- `/rooms/import` — cria modalidade de quarto que ainda não existir

    em vez de rejeitar a linha, respeitando o teto de quartos do plano

    contratado (`check\_room\_limit`);

  \- `/guests/import` — idempotente via `get\_or\_create\_guest`,

    normaliza telefone para só dígitos;

  \- `/reservations/import` — `create\_reservation\_record(...,

    source="import", notify=False)`, com `notify=False` evitando

    sincronizar com Beds24 ou disparar webhook de saída durante a

    carga em massa;

  \- `/team/import` — convida em lote (`invite\_to\_hostel`); se a

    função citada não existir ainda, cria com zero permissões

    (`roles\_created\_empty` na resposta) em vez de falhar, respeitando

    o teto de assentos do plano (`check\_seat\_limit`);

  \- `/portfolio/items/import` — restrito a conta `agency`.



\---



\### 16.33.3 Tour de Onboarding



\#### Objetivo



Reduzir a curva de aprendizado de quem acessa o Dashboard pela primeira

vez, sem depender de treinamento externo ou documentação lida à parte.



\#### Capacidades atuais



\- slide explicativo dos blocos do Dashboard no primeiro acesso de cada

  pessoa;

\- dica curta por item de menu, mostrada uma única vez, na primeira vez

  que aquele item é clicado;

\- implementação própria (sem biblioteca externa como intro.js/

  shepherd.js), consistente com o padrão do projeto de não depender de

  CDN externo;

\- preferência gravada no banco por pessoa, não em `localStorage` —

  funciona em qualquer dispositivo que a pessoa use para logar:

  `users.onboarding\_dismissed` desliga o tour inteiro,

  `user\_feature\_intros` (`UNIQUE(user\_id, feature\_key)`) marca cada

  item de menu já visto individualmente;

  \- `POST /onboarding/seen` (`{feature\_key}`) e `POST

    /onboarding/dismiss`; o estado inicial vem embutido na resposta de

    `/me`.



\---



\## 16.34 Prospecção (CRM leve de outreach comercial)



\*\*Status:\*\* Implementado e validado em produção (adicionado em 20/08/2026, versão 1.49.0)



\### Objetivo



Dar à própria equipe da StayFlow (não ao cliente) um lugar dentro do
painel interno pra organizar a prospecção de hospedagens piloto —
substitui uma planilha externa que era mantida fora do sistema.



\### Capacidades atuais



\- tabela `stayflow\_leads`, sem `hostel\_id` (mesma categoria não-tenant
  de `stayflow\_expenses`/`stayflow\_team`, dado da própria StayFlow, não
  de um cliente): nome, hospedagem, prioridade (`alta`/`media`/`baixa`),
  canal (`whatsapp`/`email`/`instagram`/`presencial`/`outro`), status
  (`a\_contatar` → `mensagem\_enviada` → `respondeu` → `call\_agendada` →
  `call\_feita` → `piloto\_ativo`, ou `sem\_interesse`/`perdido`), data do
  último contato, próxima ação (texto + data), observações;

\- `GET/POST /stayflow-admin/leads` e `PATCH/DELETE
  /stayflow-admin/leads/<id>`, todas `@require\_stayflow\_admin`, mesmo
  padrão de validação (allowlist de valores aceitos pra
  prioridade/canal/status) e de `UPDATE` dinâmico por allowlist de
  campos já usado em `update\_stayflow\_expense`;

\- aba "Prospecção" em `admin.html`, mesmo componente visual (cards de
  KPI, formulário inline de criar/editar, tabela com filtro) já usado
  na aba Despesas — status renderizado como selo colorido (`plan-chip`
  com cor por status), e a data da próxima ação aparece em vermelho
  quando já venceu, com um badge de contagem no item de menu;

\- diferente do resto do painel, o conteúdo da aba (rótulos do
  formulário, cabeçalhos da tabela) fica só em português, sem
  `data-i18n` — é ferramenta de uso exclusivo do usuário, não faz
  sentido i18n completo aqui; só o item de menu e o título/subtítulo do
  topbar têm chave de tradução, pra não quebrar o mecanismo de troca de
  aba (que sempre busca `topbar.<aba>.title/subtitle`);

\- `stayflow\_leads.training\_candidate` (adicionado em 20/08/2026, versão
  1.51.0) — flag simples (não um sistema de tags genérico) pra marcar
  contas de operação grande (ex: hotel com equipe numerosa) como
  candidatas a treinamento presencial/remoto pago, separado da
  mensalidade/comissão do piloto. Checkbox no formulário, selo 🎓 na
  linha da tabela, filtro "Só candidatos a treinamento" na toolbar.

\- Alarme real de compromisso (adicionado em 22/08/2026, versão 1.52.0)
  — `stayflow\_leads.next\_action\_time` (hora do compromisso, além da
  data que já existia) e `alarm\_offsets\_minutes` (minutos antes do
  compromisso pra avisar, ex. `"30,10"`, editável no formulário via
  checkboxes de 30/10 min + campo livre). Entrega via Web Push nativo
  (reaproveita a MESMA infraestrutura já usada pelo dashboard das
  hospedagens desde a v1.43.0 — `services/push\_service.py`, `sw.js`,
  `/push/subscribe` — sem rota nova: o login do painel interno é dono
  do `hostel\_id=1`, então a inscrição já funciona sem mudança de
  backend). Checagem feita por uma thread em background iniciada em
  `app.py` (acorda a cada 60s, sem dependência nova tipo APScheduler);
  como o `Procfile` roda 3 workers do gunicorn em paralelo, a
  deduplicação usa uma tabela de "claim" (`stayflow\_lead\_alarms\_fired`,
  `INSERT OR IGNORE` com `UNIQUE(lead\_id, offset\_minutes)`) em vez de
  lock distribuído. Fuso horário fixo em `America/Argentina/Mendoza`
  (`services/lead\_alarm\_service.py`) — decisão deliberada, já que essa
  é uma ferramenta de uso pessoal do usuário, não multi-tenant. Alarme
  nunca respeita horário de silêncio (diferente de `send\_push\_to\_hostel`),
  porque é um aviso pessoal que o usuário configurou explicitamente,
  não uma notificação de hóspede que pode esperar. Selo 🔔 na tabela
  indica compromisso com alarme ativo.



\### Limitações conhecidas



Sem importação em lote da planilha anterior (lista pequena,
recadastrada manualmente).



\---



\## 16.35 Seis idiomas novos nos dicionários i18n (ja/it/zh/ru/ko/nl)



\*\*Status:\*\* Implementado e validado (23-24/08/2026, versões 1.61.0 a
1.62.0). Pedido inicial era só japonês e italiano; usuário lembrou de
um pedido anterior de "encher de idiomas" e pediu mais 4 (chinês
mandarim simplificado, russo, coreano, holandês) na mesma sessão.
Árabe/hebraico (RTL) ficaram deliberadamente fora, registrados como
pendência à parte — exigem trabalho de CSS de layout espelhado
(`dir="rtl"`), não é só tradução de texto.



\### Objetivo



Atender a pendência "idiomas novos" registrada na auditoria de
22/08/2026 (Sessão 12) — os 3 dicionários de tradução do produto
(landing pública, Dashboard das hospedagens, painel interno da própria
StayFlow) tinham 5 idiomas (pt/en/es/fr/de) desde a v1.12.0 e nunca
tinham sido expandidos, apesar de pilotos e leads internacionais fora
desses 5 mercados.



\### O que foi adicionado



\- \*\*Japonês (`ja`), italiano (`it`), chinês (`zh`), russo (`ru`),
  coreano (`ko`) e holandês (`nl`)\*\*, nos 3 dicionários:
  `assets/js/i18n-landing-data.js` (90 chaves), `assets/js/i18n-dashboard-data.js`
  (1.028 chaves à época da tradução, mais 9 chaves novas da feature de
  métricas de chat adicionadas depois — ver 16.36) e o objeto
  `ADMIN\_I18N` dentro de `admin.html` (223 chaves) — total de 1.341
  chaves por idioma, ~8.046 chaves novas ao todo pros 6 idiomas juntos;

\- terminologia de hotelaria/PMS revisada por comparação direta com os
  blocos `en`/`pt` existentes em cada tradução (ex.: "Modalidade de
  quarto" vira "Categoria camera" em italiano, "客室カテゴリー" em
  japonês, "객실 유형" em coreano; "Beliche" vira "Letto a
  castello"/"二段ベッド"/"2층 침대"), não tradução literal palavra por
  palavra;

\- placeholders (`{price}`, `{days}`, `{count}` etc.) e tags HTML
  (`<strong>`, `<br>`) preservados exatamente iguais em todo idioma,
  só o texto muda;

\- cada idioma usa a convenção de aspas nativa apropriada onde o
  original tem aspas internas (japonês: 「」; chinês/coreano: aspas
  retas escapadas, consistente com o resto do arquivo; russo: aspas
  angulares « » quando aplicável);

\- \*\*correção de um erro registrado nesta mesma seção antes\*\*: o
  seletor de idioma NÃO é genérico — `assets/js/i18n-core.js` tem
  `SUPPORTED\_LANGS` hardcoded (ganhou os 6 códigos novos), e os 3
  dropdowns visíveis (`index.html`, `dashboard.html`, `admin.html`)
  são blocos HTML fixos, sem nenhum vindo de array JS. Cada idioma
  novo exigiu editar os 4 pontos manualmente (motor + 3 dropdowns),
  além da tradução em si — a versão anterior desta nota dizia o
  contrário por engano, já corrigida.



\### Ferramenta nova: `tools/check\_i18n\_parity.py`



Não existia nenhuma rede de segurança automática garantindo que todo
idioma tivesse exatamente o mesmo conjunto de chaves nos 3 dicionários
— a paridade era só disciplina manual, arriscada num arquivo de mais
de 1.000 chaves por idioma. Script novo faz o parsing dos blocos de
cada idioma (balanceamento de chaves `{}` que ignora chaves dentro de
literais de string, pra não confundir `"ARS {price}/mês"` com uma
chave de bloco), extrai o conjunto de chaves de cada um e falha
(código de saída 1) se qualquer idioma tiver chave faltando ou
sobrando em qualquer um dos 3 arquivos. Uso: `python
tools/check\_i18n\_parity.py`. Deve ser rodado sempre que um idioma novo
for adicionado ou uma chave nova for criada em qualquer dicionário.



\---



\## 16.36 Dashboard de métricas de chat por período



\*\*Status:\*\* Implementado e validado (24/08/2026, versão 1.63.0).



\### Objetivo



Item motivado por comparação competitiva com a Aoki (ia.aoki,
concorrente argentino de chatbot IA multi-vertical), que mostra
"mensagens recebidas / conversas / conversões" com filtro por período
— gap real confirmado no código: `routes/executive.py` e o módulo de
Relatórios (`get\_reports\_summary`) só tinham totais acumulados desde
sempre, sem nenhuma agregação por tempo, apesar da documentação
descrever o funil/receita por canal como "implementado" (era, mas sem
quebra temporal).



\### O que foi adicionado



\- `database.get\_reports\_summary(hostel\_id, period="daily")` ganha
  parâmetro de período (`daily`/`weekly`/`monthly`, janela fixa de
  14 dias / 12 semanas / 12 meses respectivamente) e uma chave nova na
  resposta JSON, `chat\_activity`: lista de `{bucket, messages\_received,
  conversations, conversions}` por período, usando `strftime` do
  SQLite pra agrupar (mesmo padrão já usado em
  `get\_account\_growth\_by\_month`, painel interno);

\- `messages\_received` = `COUNT(*)` de `messages` com `sender='user'`
  (hóspede) — confirmado que os 3 valores reais gravados em
  `messages.sender` são `'user'`/`'assistant'`/`'staff'` (lidos direto
  dos 2 pontos de `INSERT INTO messages` e seus chamadores, não
  documentação desatualizada); `conversations` = conversas distintas
  ativas no bucket; `conversions` reaproveita o MESMO proxy já usado
  no funil existente (`reservations.status='confirmed'`), não um
  conceito novo — `opportunities.status` nunca muda de `'open'` em
  lugar nenhum do código hoje, não é sinal de conversão utilizável;

\- `routes/reports.py` valida `?period=` contra os 3 valores aceitos
  (400 se inválido);

\- UI nova na aba Relatórios (`dashboard.html`): card "Atividade de
  chat" com 3 botões de período e um gráfico em Canvas nativo (linha
  com gradiente, 3 séries — mensagens/conversas/conversões), seguindo
  o mesmo estilo já estabelecido em `admin.html::renderGrowthChart`
  (painel interno) — não existia nenhuma biblioteca de gráfico
  carregada em lugar nenhum do frontend, decisão deliberada de não
  introduzir uma dependência nova só pra isso;

\- `statistics.html` (página órfã, confirmado que só ela mesma se
  referenciava, dado 100% hardcoded/fake, fora do design system,
  padrão de navegação multi-página que não bate com a SPA real)
  removida de brinde — mesmo perfil de órfãs já removidas na v1.53.0.



Testado com dado real (hostel de teste isolado): contagem de mensagens
por dia, conversas distintas e conversões batendo exatamente com
`SELECT` manual equivalente; janela de período respeitada (mensagem de
20 dias atrás corretamente excluída da janela diária de 14 dias).



\---



\## 16.37 3 ajustes no painel interno (F5, Despesas/Financeiro, Comunicação)



\*\*Status:\*\* Implementado e validado (24/08/2026, versão 1.64.0).



\### Objetivo



`admin.html` virou o painel principal do usuário no dia a dia — 3
pedidos reais nasceram de uso ao vivo: F5 sempre resetava pra Visão
Geral; Despesas deveria estar dentro de Financeiro; Configurações sem
as conectividades de canal que o dashboard normal já tem.



\### F5 mantém a aba atual



`switchAdminTab()` não tinha NENHUMA persistência — `currentAdminTab`
era só variável JS em memória, e `page-overview` nascia com `class="page
active"` hardcoded no HTML estático, então F5 sempre voltava pra lá.
Corrigido com `localStorage` (`stayflow_admin_tab`), mesmo padrão já
usado pelo idioma (`stayflow_lang` em `i18n-core.js`) — grava a cada
troca de aba, restaura no bootstrap da página (depois de todos os
dados já carregados, já que nenhuma aba faz lazy-load próprio hoje).



\### Despesas dentro de Financeiro



Virou sub-aba (pill switcher "Visão geral"/"Despesas" no topo da
seção Financeiro), mesmo padrão `.ops-tabs`/`.ops-tab` já usado em
Operações/Eventos/Equipe no dashboard normal — reaproveitado, não
criado do zero. O item de menu "Despesas" foi removido (sobra só
"Financeiro"); o badge de despesa vencendo/atrasada
(`expensesDueBadge`) migrou pro botão de Financeiro. Investigação
prévia confirmou que o botão "+ Nova despesa" já usava a classe CSS
padrão do sistema (`class="btn"`), igual "+ Novo contato"/"+
Adicionar à equipe" — a sensação de "fora do padrão" era de
posição/contexto no menu, não de estilo visual; o CSS do botão em si
não mudou nesta rodada. Todo o backend/JS de despesas (CRUD completo,
já publicado antes) continua igual — só a casca visual mudou de lugar.



\### Comunicação (WhatsApp/Facebook/Instagram) em Configurações



Antes, Configurações do painel interno só mostrava status agregado
READ-ONLY de credenciais de PLATAFORMA (App Meta, App Instagram,
Beds24 master, MP marketplace — editáveis só via variável de ambiente
no Render) — zero conectividade POR CONTA. "Meu chat" já usa uma
hospedagem real marcada como assistente comercial ("persona software",
`hostels.ai\_persona='software'`, resolvida via
`get\_hostel\_id\_by\_ai\_persona`), mas conectar o WhatsApp/Instagram/
Facebook dessa conta exigia ir em `dashboard.html` (Configurações de
outra hospedagem) — sem link nem UI dentro do próprio `admin.html`.



Solução: novo bloco "Comunicação" em Configurações, 3 cards (WhatsApp,
Facebook, Instagram) da conta persona software. Backend: rotas novas
`GET/POST/DELETE /stayflow-admin/software-persona/{whatsapp,facebook,instagram}`
em `routes/stayflow_admin.py`, reaproveitando as MESMAS funções de
`database.py`/`services/meta\_oauth\_service.py` que `routes/settings.py`
já usa pra hospedagem normal — zero duplicação de lógica de negócio,
só uma camada de autorização diferente (`@require\_stayflow\_admin`,
sessão sem `hostel\_id` de tenant, resolve o hostel fixo internamente
em vez de pegar da sessão).



Dois mecanismos de "conectar" distintos, por limitação técnica real:



\- \*\*WhatsApp\*\*: usa o MESMO Embedded Signup já construído (v1.53.0,
  `FB.login()` no navegador + evento `postMessage` `WA\_EMBEDDED\_SIGNUP`)
  — não precisa de `redirect\_uri` registrado na Meta (roda embutido na
  própria página via SDK JS), então dá pra reproduzir 100% dentro do
  `admin.html` sem sair da tela. Nova rota
  `POST /stayflow-admin/software-persona/whatsapp/embedded-signup`
  espelha `POST /settings/whatsapp/embedded-signup`.

\- \*\*Facebook/Instagram\*\*: usam OAuth com redirect de verdade pra tela
  de consentimento da Meta, e o callback (`/oauth/facebook/callback`,
  `/oauth/instagram/callback`) é uma URL FIXA já registrada no painel
  de desenvolvedor da Meta — não dá pra duplicar esse fluxo dentro do
  `admin.html` sem registrar um `redirect\_uri` novo lá (mudança
  externa, fora do que dá pra fazer só por código). Solução:
  o botão "Conectar" chama `POST /stayflow-admin/impersonate`
  (mecanismo já existente do Hub) pra essa conta específica, e navega
  pro fluxo OAuth normal (`/oauth/facebook/connect`) — ao terminar, o
  usuário cai no dashboard da conta persona (impersonada), com o
  banner "Sair da visualização" já existente pra voltar ao
  `admin.html`. Não é "clique único sem sair da tela" como o WhatsApp,
  mas ainda é clique-e-conecta — sem colar `page\_id`/token manualmente
  — reaproveitando um mecanismo de navegação já familiar no produto
  (o mesmo usado pra qualquer visita de suporte a hospedagem/agência).



\---



\## 16.18 Critério para atualização



Este capítulo deverá ser atualizado sempre que uma funcionalidade:



\- for implementada;

\- sofrer alteração estrutural;

\- for removida;

\- deixar de fazer parte do produto.



O conteúdo deste capítulo deve refletir exatamente o estado atual da plataforma.



\---



\## Decisões Consolidadas



\- Este capítulo representa o inventário oficial das funcionalidades da StayFlow.

\- Apenas funcionalidades implementadas podem ser registradas como concluídas.

\- Funcionalidades futuras pertencem ao Roadmap Oficial.

\- Toda alteração funcional deverá atualizar este capítulo.

\- O Documento Mestre representa o estado real do produto.



\---



<a id="capitulo-17"></a>



\# 17. ROADMAP OFICIAL



O Roadmap Oficial define a direção estratégica da evolução da StayFlow.



Ele organiza prioridades, registra os principais objetivos do produto e orienta a sequência de desenvolvimento.



O Roadmap não limita a inovação.



Sempre que uma oportunidade representar ganho real para o produto, ela poderá alterar a ordem das prioridades.



\---



\## 17.1 Objetivo



O Roadmap existe para:



\- orientar o desenvolvimento;

\- organizar prioridades;

\- reduzir retrabalho;

\- manter alinhamento entre produto e engenharia;

\- preservar a visão de longo prazo.



Ele representa o planejamento oficial da StayFlow.



\---



\## 17.2 Situação Atual



\*\*Versão do Produto\*\*



Plataforma multi-canal (WhatsApp, Messenger, Instagram Direct) com

Channel Manager (Beds24), Mapa de Quartos, agente conversacional real

(Ask StayFlow) e sistema de permissões multi-hostel em produção. Em

validação comercial fora do nicho hostel (ver Capítulo 1).



\*\*Objetivo atual\*\*



Validar a StayFlow em um piloto de hospedagem de grande porte fora do

nicho hostel (primeiro cliente potencial fora da validação inicial),

consolidando as frentes de atendimento multi-canal e integração com

Channel Manager que sustentam essa apresentação.



Prioridades atuais:



\- \*\*Instagram Direct — App Review da Meta\*\*: submissão preparada,

  pendente de envio pelo usuário, para obter "Advanced Access" às

  permissões `instagram\_business\_basic`/`instagram\_business\_manage\_messages`

  e destravar a Conversations API (ver Capítulo 16, seção 16.26);

\- ~~cobrança recorrente automática da própria assinatura StayFlow

  (Billing Fase 2-3)~~: \*\*resolvido na v1.59.0\*\* (23/08/2026) — ver

  Capítulo 16, seção 16.4-bis (ou busca por "Billing Fase 2" no

  changelog). Decisão: Mercado Pago (API `preapproval`), não Stripe —

  Stripe não abre conta padrão pra recebedor domiciliado na Argentina

  (monotributo), inviabilizando o recebimento do dinheiro. Usa uma

  credencial própria da conta MP da StayFlow

  (`MERCADOPAGO_PLATFORM_ACCESS_TOKEN`), diferente da credencial OAuth

  usada pelo Split guest-facing (que é por-hostel). Cobrança em ARS

  (`PLAN_PRICES_ARS`, mantido manualmente, sem motor de câmbio

  automático — essa parte continua fora de escopo). Bloqueio de acesso

  por inadimplência foi deixado deliberadamente de fora desta rodada —

  hoje o trial vencido sem assinatura só atualiza o `status` pra

  `past_due` (bookkeeping), sem travar nenhuma rota. Não confundir com

  o Mercado Pago Split guest-facing (cobrança do hóspede pelo hostel),

  que já era real e está em produção desde antes, com credencial e

  fluxo completamente separados;

\- avaliar estratégia de atendimento para hóspedes localizados no Brasil,

  dada a limitação de mensageria do WhatsApp descrita no Capítulo 16 —

  decisão já tomada de registrar uma segunda conta de WhatsApp Business

  localizada no Brasil, implementação pendente;

\- separação definitiva de infraestrutura de deploy (ver 17.3) — dívida

  técnica conhecida, ainda ativa;

\- ampliar automações operacionais;

\- evoluir continuamente a experiência do usuário.



\*\*Concluído desde a última grande revisão deste capítulo\*\* (não repetir

como pendência): responsividade mobile da navbar; menu de Configurações

com Empresa, Comunicação (WhatsApp/Messenger/Instagram), Integrações

(Beds24 e webhook de saída), Segurança e Billing Fase 1 (planos/trial/

comp accounts) todos funcionais — resta apenas a cobrança recorrente

automática da assinatura em si (Fase 2-3, ver bullet acima); arquitetura

de tradução do Dashboard unificada (i18n-core.js, 5 idiomas, ~570

chaves), incluindo correção de uma condição de corrida real entre

`i18n-core.js` e `i18n-dashboard-data.js` (v1.47.0, ver 16.33); criação

de reserva via modal flutuante; Ask StayFlow como agente real, com

visão de imagem desde a v1.47.0 (ver 16.27); Mapa de Quartos completo;

integração com Channel Manager (Beds24, 6 fases); auditoria de

segurança completa com CSP, proteção contra força bruta e verificação

de assinatura de webhook (v1.39.0); direito ao esquecimento/exclusão de

dados do hóspede (v1.40.0); câmbio evoluído pra casa de câmbio real com

cotação automática de todas as moedas cadastradas (v1.41.0 — item

"moeda/câmbio automático por país" da revisão anterior foi resolvido

dessa forma, não pela regra fixa de margem originalmente cogitada em

1.22.0); revisão mobile de Configurações/Operações/Equipe (v1.42.0);

notificações push nativas no aparelho (v1.43.0); autenticação em duas

etapas — 2FA (v1.44.0); módulo de Eventos (v1.45.0); cadastro self-serve

com página pública de planos, StayFlow Hub com impersonation, contas

de agência parceira (Portfólio/Parceiros), importador de dados via CSV

e tour de onboarding (todos v1.47.0, ver 16.33 e 14.3).





\---



\## 17.3 Próximas Prioridades



Após a consolidação da plataforma base, as próximas grandes capacidades serão desenvolvidas conforme sua relevância estratégica.



Entre elas:



\- Revenue Management avançado (precificação dinâmica, previsão de

  demanda — o catálogo básico de upsells já está implementado, ver

  Capítulo 16);

\- CRM Inteligente;

\- Agenda Operacional;

\- Gestão Financeira avançada (fluxo de caixa, projeções — a consolidação

  básica já está implementada, ver Capítulo 16);

\- conexão direta com Booking.com/Airbnb via parceria de API própria —

  pesquisa de 13/07/2026 confirmou acesso fechado a desenvolvedores

  independentes; hoje contornado via Channel Manager (Beds24, ver

  Capítulo 16, seção 16.25), que já resolve a necessidade prática de

  receber e sincronizar reservas dessas OTAs. Conexão direta permanece

  como alternativa avaliável no futuro, condicionada a custo/escopo;

\- Relatórios Inteligentes avançados (a versão básica de receita por

  canal e funil de conversão já está implementada, ver Capítulo 16);

\- ~~cobrança recorrente automática da própria assinatura StayFlow

  (Billing Fase 2-3)~~ — \*\*resolvido na v1.59.0\*\*, ver 17.2;

\- Automações Operacionais;

\- Separação definitiva de infraestrutura de deploy (Frontend como

  Static Site independente do Render, Backend exposto só como API,

  possivelmente em subdomínio dedicado) — a v1.58.0 já eliminou a

  cópia manual arquivo-por-arquivo (`HostelBot/StayFlow---Site/` virou

  `git subtree`, sincronizado com um comando só, ver nota crítica no

  Capítulo 9), mas a separação de domínio/topologia em si continua

  deliberadamente adiada: implicaria cookies de sessão cross-domain,

  CORS e reconfiguração do escopo do Service Worker, risco real demais

  pra pilotos ativos agora, pra um ganho que o subtree já entrega sem

  mexer em produção.



A ordem poderá ser ajustada conforme a evolução do produto.



\---



\## 17.4 Expansão do Ecossistema



Após a maturidade da plataforma principal, o ecossistema StayFlow será expandido.



Produtos previstos:



\- Aplicativo do Viajante;

\- Marketplace de Passeios;

\- Plataforma para Redes Hoteleiras;

\- APIs Públicas;

\- Portal do Cliente;

\- Integrações Estratégicas.



Todos compartilharão a mesma arquitetura e os mesmos motores de inteligência.



\---



\## 17.5 Evolução Permanente



O Roadmap deverá ser atualizado sempre que:



\- uma grande funcionalidade for concluída;

\- novas prioridades forem definidas;

\- decisões estratégicas alterarem a direção do produto.



Ele deve representar sempre a realidade da StayFlow.



\---



\## 17.6 Critérios de Priorização



As prioridades da StayFlow deverão considerar, nesta ordem:



1\. Valor entregue ao cliente.

2\. Impacto financeiro.

3\. Inteligência do produto.

4\. Experiência do usuário.

5\. Redução de trabalho operacional.

6\. Escalabilidade.

7\. Facilidade de manutenção.



Esses critérios orientam permanentemente a evolução da plataforma.



\---



\## Decisões Consolidadas



\- O Roadmap representa o planejamento oficial da StayFlow.

\- O Roadmap pode evoluir conforme novas oportunidades surgirem.

\- A plataforma base possui prioridade sobre novas expansões.

\- O ecossistema será desenvolvido sobre a mesma arquitetura.

\- Toda alteração estratégica deverá atualizar este capítulo.

\- A evolução da StayFlow será sempre orientada por geração de valor.



\---



<a id="capitulo-18"></a>



\# 18. REGISTRO OFICIAL DE EVOLUÇÃO



O Registro Oficial de Evolução representa a memória permanente da StayFlow.



Seu objetivo é documentar todas as mudanças relevantes realizadas no produto, preservando contexto, justificativas e histórico técnico.



Nenhuma decisão estrutural importante deve permanecer apenas em conversas.



Toda evolução permanente deverá ser registrada neste capítulo.



\---



\## 18.1 Objetivo



O Registro Oficial de Evolução possui quatro responsabilidades principais:



\- preservar a história da plataforma;

\- documentar decisões importantes;

\- registrar mudanças estruturais;

\- facilitar rastreabilidade técnica.



Este registro representa o histórico oficial da engenharia da StayFlow.



\---



\## 18.2 Quando registrar



Um novo registro deverá ser criado sempre que ocorrer:



\- alteração de arquitetura;

\- criação de um novo módulo;

\- mudança relevante no banco de dados;

\- alteração importante nas APIs;

\- evolução dos Motores de Inteligência;

\- mudança estrutural no Dashboard;

\- implementação de funcionalidades estratégicas;

\- alteração permanente neste Documento Mestre.



Mudanças pequenas e correções rotineiras não precisam ser registradas.



\---



\## 18.3 Padrão de Registro



Cada registro deverá seguir o formato abaixo.



```text

Versão:



Data:



Área:



Descrição:



Motivação:



Impacto:



Responsável:

```



Esse padrão deverá ser mantido durante toda a vida do projeto.



\---



\## 18.4 Registro Inicial



\### Versão 1.0.0



\*\*Data\*\*



28/06/2026



\*\*Área\*\*



Estrutura da Plataforma



\*\*Descrição\*\*



Publicação da primeira versão oficial do Documento Mestre da StayFlow.



Consolidação da arquitetura, princípios de engenharia, visão do produto, estrutura técnica e documentação oficial da plataforma.



\*\*Motivação\*\*



Estabelecer uma fonte única de verdade para orientar toda a evolução futura da StayFlow.



\*\*Impacto\*\*



Padronização do desenvolvimento, preservação do conhecimento e criação da documentação oficial da empresa.



\---



\### Versão 1.1.0



\*\*Data\*\*



01/07/2026



\*\*Área\*\*



Produto, Frontend, Arquitetura e Dashboard



\*\*Descrição\*\*



Consolidação do posicionamento da StayFlow como Sistema Operacional Inteligente para Hotelaria, atualização da estrutura oficial do frontend, refinamento do conceito do Dashboard Inteligente e atualização do roadmap de desenvolvimento.



\*\*Motivação\*\*



Alinhar a documentação ao estado atual do projeto e registrar decisões permanentes tomadas durante a evolução da plataforma.



\*\*Impacto\*\*



Maior consistência entre produto, engenharia e documentação oficial.



\---



\### Versão 1.2.0



\*\*Data\*\*



05/07/2026



\*\*Área\*\*



Infraestrutura, Integrações e Roadmap



\*\*Descrição\*\*



Publicação da plataforma em domínio oficial próprio (`stayflowsolutions.com`) com certificado HTTPS válido. Correção de decisão de infraestrutura para garantir persistência do banco de dados em produção através de disco dedicado, eliminando o risco de perda de dados em deploys e reinícios. Conclusão e validação de ponta a ponta da integração com WhatsApp Business (Meta Cloud API), incluindo recebimento, processamento pela IA e envio de resposta real ao hóspede. Identificação e documentação de limitação da própria plataforma Meta que restringe mensageria comercial para destinatários no Brasil e na Indonésia. Atualização do Roadmap Oficial com dívidas técnicas de experiência do usuário identificadas durante a sessão.



\*\*Motivação\*\*



Registrar a evolução de infraestrutura crítica e a validação de uma integração estratégica do produto, além de preservar o conhecimento sobre uma limitação externa relevante para decisões futuras de atendimento e expansão.



\*\*Impacto\*\*



O canal de comunicação via WhatsApp passa de "implementado em código" para "validado e funcional em produção", tornando-se oficialmente disponível para uso operacional real, respeitada a limitação de mensageria documentada.



\---



\### Versão 1.3.0



\*\*Data\*\*



09/07/2026



\*\*Área\*\*



Frontend, Engenharia de Desenvolvimento, Chats, Documentação Oficial

(auditoria e correção dos Capítulos 12, 13, 15, 16 e 17)



\*\*Descrição\*\*



Refatoração completa da arquitetura de CSS do Frontend: extração dos blocos

`<style>` inline (acumulados cronologicamente, com uso extensivo de

`!important`) de `dashboard.html`, `index.html` e `Login.html` para arquivos

CSS organizados por responsabilidade (`tokens.css`, `reset.css`, `app.css`,

`landing.css`, `auth.css`), com `#0b84ff` estabelecido como token de cor

oficial. Correção de múltiplas dívidas técnicas de UX em mobile: grid de

KPIs cortado, logo do hero estourando a tela, botões do topbar cortados,

card de login sem margem de segurança, navbar da landing piscando durante

o scroll em Safari iOS (bug conhecido do WebKit), scroll da aba Chats

rolando a página inteira em vez de isolar internamente as mensagens.

Redesenho do cabeçalho mobile da landing page para padrão de barra fixa

compacta. Novas funcionalidades no módulo de Chats: divisores de data

entre mensagens (estilo WhatsApp) e identificação de bandeira de país por

código de telefone no título da conversa. Adoção formal do Claude Code

como ferramenta de desenvolvimento assistido dentro do fluxo de trabalho,

incluindo a criação de um skill de contexto automático

(`.claude/skills/stayflow-context/`) que carrega este documento e o Diário

de Engenharia no início de cada sessão. Criação do processo formal de

Checklist Ativo (`docs/CHECKLIST_ATIVO.md`) como fonte única de

prioridades, com regra explícita de não iniciar trabalho novo antes de

concluir o que já está registrado.



Adicionalmente, esta versão inclui uma auditoria retroativa do próprio

Documento Mestre: os Capítulos 12 (Banco de Dados), 13 (APIs), 15

(Dashboard) e 16 (Funcionalidades Implementadas) estavam desatualizados

desde a sessão de 05/07/2026 — seis módulos completos (Reservas,

Financeiro, Relatórios, Estoque, Operações, Receitas/Upsell), além de

autenticação por sessão real, foram construídos naquela sessão mas nunca

haviam sido registrados oficialmente neste documento, mesmo a versão

1.2.0 tendo sido publicada no mesmo dia. O Capítulo 17 (Roadmap) também

continha uma contradição real: listava "Gestão Financeira", "Motor de

Reservas" e "Relatórios Inteligentes" como prioridades futuras quando

versões básicas dessas capacidades já estavam implementadas e em uso.



\*\*Motivação\*\*



A dívida técnica de CSS acumulada ao longo de múltiplas sessões estava

causando bugs reais e visíveis em produção, além de tornar qualquer

alteração visual arriscada por conta da guerra de especificidade entre

blocos `!important`. A padronização do processo de trabalho (Checklist

Ativo, skill de contexto automático) responde à necessidade identificada

de evitar dispersão de escopo entre sessões consecutivas. A auditoria

retroativa responde a uma exigência explícita do usuário: o Documento

Mestre deve ser revisado e atualizado por completo ao final de cada

sessão relevante, não apenas receber uma entrada de changelog pontual —

nenhuma divergência entre o documento e o estado real do produto deve

persistir de uma sessão para a outra.



\*\*Impacto\*\*



O Frontend passa a ter uma arquitetura de CSS sustentável e auditável, com

fonte única de tokens de design. Bugs de mobile que afetavam a experiência

real de uso foram eliminados. O processo de desenvolvimento ganha uma

camada de continuidade entre sessões (via skill automático) e de controle

de escopo (via Checklist Ativo), reduzindo risco de retrabalho. O

Documento Mestre volta a refletir fielmente o estado real do produto,

eliminando um atraso de documentação de mais de quatro dias sobre

funcionalidades já em produção.



\---



\### Versão 1.4.0



\*\*Data\*\*



13/07/2026



\*\*Área\*\*



Infraestrutura, Backend, Frontend, Inteligência Artificial, Banco de

Dados, Roadmap



\*\*Descrição\*\*



Correção de uma divergência crítica entre as branches `main` e

`arquitetura-v2` do repositório do Frontend — a branch `main` nunca havia

recebido a correção do bug de duplicação de arquivo `login.html`/

`Login.html` já resolvida anteriormente na branch de trabalho, o que

bloqueava a publicação de todo o trabalho acumulado. Após a correção,

publicação em produção de todos os commits pendentes desde a versão

1.3.0. Identificação e remoção de um serviço de hospedagem órfão,

sem função real, mantido ativo desnecessariamente. Documentação formal,

pela primeira vez, da duplicação física do Frontend dentro do repositório

do Backend, necessária para o processo de publicação atual (Capítulo 9).



Implementação e validação em produção, com número real de WhatsApp, da

captura do nome do hóspede durante a conversa com a Inteligência

Artificial, utilizando function calling — encerrando uma investigação em

aberto desde a versão anterior. Exibição do nome do hóspede (com telefone

como reserva) na lista de conversas e no título da conversa aberta.



Auditoria completa do menu de Configurações, revelando que apenas duas de

nove categorias possuíam implementação real. Correção dos indicadores de

status do sistema, que exibiam informação falsa independentemente do

estado real de conectividade. Conexão do botão de gestão de Equipe do

menu de Configurações ao painel já existente, expondo (sem introduzir) uma

falha estrutural pré-existente na marcação do próprio painel. Identificação

de um bug de perda silenciosa de dados nas configurações de Inteligência

Artificial.



Início da primeira fase (modelagem e migração de dados) de um sistema de

permissões multi-hostel, permitindo que uma mesma pessoa possua acesso a

múltiplos hostels com funções independentes por hostel, funções

configuráveis por cada administrador, e exceções de permissão por pessoa

individual. Migração de dados existentes escrita, testada e validada em

ambiente isolado, ainda não publicada em produção.



Pesquisa de mercado sobre integração com agências de viagem on-line

(Booking.com, Airbnb), confirmando restrição de acesso a desenvolvedores

independentes nas duas plataformas, e definição de estratégia alternativa

(captura via e-mail de confirmação) para quando essa frente for

priorizada.



\*\*Motivação\*\*



Resolver o acúmulo de trabalho não publicado desde a versão anterior,

validar de ponta a ponta uma capacidade da Inteligência Artificial que

permanecia apenas planejada, e tratar com seriedade estrutural um pedido

explícito do usuário: nenhuma funcionalidade de gestão de equipe deveria

ser entregue de forma parcial, mesmo que isso exigisse desenhar uma

arquitetura de permissões mais ampla antes de continuar corrigindo

sintomas pontuais no menu de Configurações.



\*\*Impacto\*\*



A plataforma volta a ter, em produção, todo o trabalho acumulado desde a

versão 1.3.0. A Inteligência Artificial passa a coletar de forma

autônoma uma informação de perfil do hóspede antes obtida apenas

manualmente. O menu de Configurações deixa de aparentar funcionalidade

completa quando na verdade não possuía — a distância entre aparência e

realidade do produto foi documentada com precisão, criando uma base

confiável para o trabalho de conclusão. A gestão de equipe do produto

recebe uma base arquitetural pensada para o cenário real de operação com

múltiplos hostels, evitando uma reconstrução futura.



\---



\### Versão 1.5.0



\*\*Data\*\*



19/07/2026



\*\*Área\*\*



Backend, Frontend, Banco de Dados, Roadmap



\*\*Descrição\*\*



Conclusão das Fases 2 e 3 do sistema de permissões multi-hostel iniciado

na versão anterior, com publicação completa em produção. No Backend:

reescrita total do fluxo de autenticação, permitindo que uma pessoa

possua acesso a múltiplos hostels com troca de conta sem necessidade de

nova senha; criação de um decorator central que passou a proteger toda

rota da plataforma pela permissão específica da área acessada, calculada

em tempo real a partir da função da pessoa somada a eventuais exceções

individuais, nunca a partir de valor guardado em sessão; criação de um

módulo completo de gestão de equipe e funções (nove rotas novas), com

proteções de segurança automáticas contra configurações que deixariam um

hostel sem ninguém capaz de gerenciar a própria equipe; expansão do

catálogo de permissões de dez para doze chaves.



No Frontend: reconstrução completa do painel de gestão de Equipe, que

nunca havia possuído marcação visual própria; criação de um seletor de

conta na barra lateral para troca de hostel; tela de gestão de funções

com seleção de permissões por checkbox; tela de exceções individuais de

permissão por pessoa, com distinção visual entre o que é herdado da

função e o que foi ajustado manualmente; reordenação do menu de

navegação principal por prioridade de uso real, e filtragem automática

dos itens do menu conforme a permissão da pessoa logada.



Durante a construção, três bugs reais nos indicadores de identidade do

usuário na barra lateral (nome do hostel, e-mail do hostel e função da

pessoa, todos presos em texto de reserva fixo) foram identificados e

corrigidos por revisão própria, antes de qualquer reclamação de uso —

mesmo padrão aplicado a diversos outros pontos ao longo da sessão

(tratamento de concorrência em cadastro de função, proteção contra

apagar função com vínculo inativo remanescente, prevenção de quebra de

atributo HTML por caracteres especiais em nome de pessoa).



\*\*Motivação\*\*



Encerrar por completo uma iniciativa que o usuário determinou

explicitamente não poder ficar parcialmente implementada — uma vez que a

decisão de construir o sistema de permissões foi tomada, o compromisso

assumido foi de não interromper o trabalho até toda a extensão da

visão original (identidade única multi-hostel, funções configuráveis,

exceções individuais com distinção de origem) estar funcional e

publicada, evitando o retrabalho estrutural que uma entrega parcial

inevitavelmente geraria.



\*\*Impacto\*\*



A plataforma passa a operar oficialmente sob um modelo de identidade e

permissões preparado para o cenário real de múltiplos hostels e equipes,

eliminando a limitação anterior de um usuário por hostel. A categoria

Equipe do menu de Configurações, que era a maior lacuna identificada na

auditoria da versão anterior, torna-se a primeira categoria totalmente

funcional além de Geral e WhatsApp Business. O produto ganha uma base

de controle de acesso que qualquer funcionalidade futura poderá herdar

automaticamente, sem exigir nova arquitetura de segurança.



\---



\### Versão 1.6.0



\*\*Data\*\*



21/07/2026



\*\*Área\*\*



Frontend, Backend, Banco de Dados



\*\*Descrição\*\*



Reorganização do cabeçalho principal do Dashboard: o card de hostel e
o card de usuário, antes na barra lateral, foram movidos para a faixa
superior da interface, ao lado do indicador de alertas operacionais
(que nesta mesma frente passou de botão de texto para ícone de sino
com contador de notificações). O avatar do usuário passou a abrir um
menu suspenso com acesso à gestão de Equipe (respeitando a permissão
da pessoa) e à opção de sair da sessão, substituindo o acesso direto
anterior. Unificação visual dos dois botões flutuantes da interface
(atalho de conversa com a IA e atalho de nova reserva), padronizados
em tamanho, formato e paleta de cores.



Correção do controle de geração de oportunidades no menu de
Configurações: identificado que o valor selecionado pelo administrador
nunca chegava a ser persistido pelo Backend, mascarado por uma camada
de armazenamento local no navegador que dava a falsa impressão de que
a preferência era respeitada. Corrigido de ponta a ponta, incluindo a
alteração do comportamento real do motor de geração de oportunidades,
que passou a respeitar a preferência configurada por cada hostel. O
controle de resposta automática, por depender de um mecanismo de
revisão humana ainda não construído, foi desabilitado de forma
transparente na interface em vez de manter uma aparência de
funcionalidade inexistente.



\*\*Motivação\*\*



Dar continuidade ao plano de reorganização visual já registrado no
Roadmap Oficial, e eliminar uma divergência real entre o que a
interface comunicava ao administrador do hostel e o que efetivamente
acontecia no sistema — uma configuração que parece funcionar mas não
tem efeito real compromete a confiança no produto de forma mais grave
do que a ausência do próprio controle.



\*\*Impacto\*\*



O cabeçalho do Dashboard ganha organização mais alinhada a padrões
consolidados de produtos de gestão, com identidade do usuário e do
hostel sempre visíveis independente da página aberta. O administrador
do hostel passa a ter controle real, não apenas aparente, sobre a
geração automática de oportunidades comerciais pela Inteligência
Artificial — um dos dois controles do card de IA em Configurações
sai do estado de dívida técnica identificado na versão 1.4.0.



\---



\*\*Nota sobre continuidade deste registro:\*\* entre a versão 1.6.0 e a
versão 1.38.0 abaixo, o produto avançou por mais de trinta versões
(sistema completo de Mapa de Quartos, hóspede de Longa Duração, Ask
StayFlow como agente real, integração completa com Beds24, integração
com Messenger e Instagram Direct, módulo de Segurança, entre outras),
todas registradas de forma resumida na tabela de Controle de Versões no
início deste documento, mas sem entrada narrativa completa
(Versão/Data/Área/Descrição/Motivação/Impacto) neste capítulo. Esse é um
gap conhecido deste registro, sinalizado explicitamente aqui para não
passar como esquecimento silencioso — a reconstrução retroativa de cada
uma dessas entradas fica como pendência separada, priorizável sob
demanda.



\### Versão 1.38.0



\*\*Data\*\*



03/08/2026



\*\*Área\*\*



Documentação Oficial (auditoria e correção integral do próprio
Documento Mestre)



\*\*Descrição\*\*



Auditoria completa do Documento Mestre, linha a linha (protocolo
formal de revisão integral, mesmo padrão já aplicado na versão 1.3.0),
motivada por uma sessão de Claude Code diferente não ter conseguido
identificar, a partir deste documento, várias funcionalidades reais já
em produção. Correções principais: catálogo de permissões corrigido de
12 para 14 chaves nos três pontos onde estava desatualizado (Capítulo
12, seções 16.21 e 16.22 do Capítulo 16); Capítulo 16 e Capítulo 17
corrigidos onde descreviam como "não implementado" ou "planejado"
capacidades já construídas (Mapa de Quartos, Ask StayFlow como agente
real, Channel Manager Beds24, módulo de Segurança); seis novas seções
criadas no Capítulo 16 para módulos que não tinham nenhum registro
(Mapa de Quartos, Integração com Beds24, Integração com Messenger e
Instagram Direct, Ask StayFlow, Segurança, Respostas Rápidas);
Capítulo 12 (Banco de Dados) e seção 16.6 expandidos com as entidades
reais que sustentam essas funcionalidades. Registrada, pela primeira
vez de forma explícita, a decisão permanente de posicionamento de
produto: a StayFlow nunca deve ser descrita como nichada em hostel —
hostel é a primeira categoria de hospedagem atacada, não o mercado-alvo
final.



\*\*Motivação\*\*



O Documento Mestre é a fonte de verdade oficial usada para orientar
qualquer sessão de trabalho, incluindo apresentações comerciais — uma
divergência entre o que o documento descreve e o que o produto
realmente faz compromete tanto o desenvolvimento quanto a comunicação
externa da empresa. A auditoria foi motivada diretamente por essa
divergência ter sido observada na prática.



\*\*Impacto\*\*



O Documento Mestre volta a refletir com precisão o estado real da
plataforma antes de uma apresentação comercial estratégica (piloto fora
do nicho hostel). Fica registrado como gap conhecido (ver nota acima) a
ausência de entradas narrativas completas para as versões 1.7.0 a
1.37.0 neste capítulo — a tabela de Controle de Versões no início do
documento permanece completa e atualizada para todo esse intervalo.



\---



\### Versão 1.45.0



\*\*Data\*\*



05/08/2026



\*\*Área\*\*



Segurança, Financeiro, Configurações/Mobile, Notificações,
Autenticação, novo módulo de Eventos



\*\*Descrição\*\*



Sessão longa e produtiva cobrindo sete frentes distintas, registradas
em detalhe na tabela de Controle de Versões (1.39.0 a 1.45.0) e no
Diário de Engenharia: (1) auditoria de segurança completa (XSS
armazenado corrigido, força bruta no login bloqueada, cabeçalhos de
segurança e CSP, verificação de assinatura dos webhooks da Meta
confirmada com tráfego real, decisão permanente de nunca expirar
sessão por tempo); (2) direito ao esquecimento — exclusão de dados do
hóspede a pedido, e documentação de onde os dados ficam fisicamente
hospedados (Render, Oregon); (3) câmbio evoluído pra casa de câmbio
real, com cotação automática pra todas as moedas cadastradas (não só
USD) e caixa de lucro dedicada; (4) revisão de UX mobile em
Configurações/Operações/Equipe, incluindo um bug real de scroll ao
trocar de seção e um bug real de save que nunca persistia o modal
"Geral"; (5) sistema completo de notificações push nativas (Web Push
API), nove tipos de evento configuráveis, filtrados por permissão de
cada área; (6) autenticação em duas etapas (2FA/TOTP) com códigos de
backup, incluindo a correção de um bug real de migração de banco que
descartava colunas novas em qualquer banco criado do zero; (7) módulo
de Eventos inteiro (espaços, agenda com checagem de disponibilidade,
adicionais com preço congelado, integração com o Financeiro). Reforçada
pela terceira vez a decisão de posicionamento registrada em 1.38.0: a
StayFlow nunca deve ser descrita como nichada em hostel, nem em texto
visível nem em comentários de código que descrevem lógica de negócio.



\*\*Motivação\*\*



Consolidar a plataforma antes da apresentação comercial ao Diplomatic
Hotel: fechar lacunas de segurança e compliance que poderiam surgir
como pergunta direta durante a venda, entregar capacidades que hotéis
de maior porte esperam de um sistema de gestão (câmbio de verdade,
2FA, notificações em tempo real, gestão de eventos), e manter a
qualidade de UX consistente entre desktop e mobile.



\*\*Impacto\*\*



A plataforma sai desta sessão com resposta pronta para praticamente
qualquer pergunta de segurança/compliance que a venda ao Diplomatic
Hotel possa levantar, e com duas capacidades novas de peso (2FA,
Eventos) que hotéis de grande porte tendem a considerar essenciais.
Pendências reais que continuam abertas, sem mudança nesta versão:
Billing (modelo de cobrança) ainda sem processador de pagamento real;
Instagram Direct App Review ainda não submetido (ação do usuário);
segunda conta de WhatsApp Business no Brasil ainda não registrada;
separação de infraestrutura de deploy ainda pendente. Este próprio
Documento Mestre e o Diário de Engenharia foram atualizados de ponta a
ponta nesta versão, cobrindo os capítulos 12, 13, 15, 16, 17 e 18, além
de varredura por palavras-chave no restante do documento.



\---



\### Versão 1.46.0



\*\*Data\*\*



05/08/2026



\*\*Área\*\*



Documentação Oficial (segunda auditoria integral do Documento Mestre e
do Diário de Engenharia, na mesma sessão da versão 1.45.0)



\*\*Descrição\*\*



O usuário questionou diretamente a auditoria que produziu a versão
1.45.0 ("por que não fez o que eu pedi exatamente?"), apontando que a
cobertura declarada (leitura dos capítulos 9 e 12–18 mais varredura por
palavras-chave) não era o protocolo formal de revisão integral já
estabelecido neste documento desde a versão 1.3.0. Repetida do zero,
com leitura sequencial confirmada de 100% das 8190 linhas do Documento
Mestre e das 5397 linhas do Diário de Engenharia, mais verificação
cruzada de afirmações técnicas contra o código real do backend e do
frontend (não feita em nenhuma auditoria anterior deste documento).

A segunda passada encontrou divergências reais que a primeira (versão
1.45.0) não tinha pego: catálogo de permissões documentado como 15
chaves (seções 12.3, 16.21, 16.22) quando `utils/permissions.py` já
tinha 20 — faltavam `kitchen`, `maintenance`, `patrimonial_security`,
`parking` e `scheduling`, adicionadas em 04/08/2026 junto com um módulo
operacional inteiro (cinco áreas novas, com IA integrada — a IA de
atendimento consegue abrir chamado de cozinha direto pela conversa)
que nunca chegou a ser registrado em nenhum dos dois documentos, apesar
de já estar em produção havia mais de um dia quando esta auditoria
rodou; duas menções residuais a "14 permissões" dentro da própria
seção 16.22, nunca corrigidas nas rodadas anteriores de 12→14→15;
módulo de Escala (gestão de turnos, `routes/scheduling.py`) sem nenhum
registro em lugar nenhum do documento; lista de abas do Frontend
(11.3) sem menção à aba Eventos; e `docs/CHECKLIST_ATIVO.md`, citado
em cinco pontos entre os dois documentos como arquivo ainda em uso,
confirmado inexistente no repositório atual — sem nenhum registro de
quando ou por que foi removido.



\*\*Motivação\*\*



Pedido explícito e direto do usuário: os dois documentos "têm que estar
sempre perfeitamente atualizados e alinhados", sem admitir falhas.
Uma auditoria que declara cobertura completa sem de fato ler o
documento inteiro, e sem comparar contra o código real do produto, não
cumpre esse padrão — mesmo que encontre e corrija alguns problemas
reais no caminho, como a versão 1.45.0 encontrou.



\*\*Impacto\*\*



Os dois documentos voltam a refletir com precisão o estado real do
produto, incluindo um módulo inteiro (operações: cozinha, manutenção,
segurança patrimonial, estacionamento, escala) que existia em produção
sem nenhum registro escrito até agora. Resolvida de quebra uma dívida
técnica antiga citada no próprio Diário (Sessão 7): a pasta
`HostelBot/StayFlow---Site/docs/` estava fora do controle de versão
desde 23/07/2026 — os dois documentos passaram a ser commitados também
no repositório do backend, não só no do frontend.



\---



\## 18.5 Atualização do Documento Mestre



Sempre que este documento receber alterações permanentes, um novo registro deverá ser criado.



O histórico do Documento Mestre faz parte da história da própria StayFlow.



Documentação também é produto.



\---



\## 18.6 Encerramento da Versão



Ao final de cada grande ciclo de desenvolvimento deverá ser registrada uma nova versão oficial.



Cada versão deverá representar um marco relevante na evolução da plataforma.



\---



\## Decisões Consolidadas



\- O Registro Oficial de Evolução representa a memória técnica da StayFlow.

\- Toda alteração estrutural deverá ser registrada.

\- O Documento Mestre possui histórico próprio.

\- Cada versão oficial representa um marco da evolução da plataforma.

\- A documentação evolui junto com o software.



\---



\# ENCERRAMENTO



O \*\*STAYFLOW\_MASTER\_CONTEXT.md\*\* representa a documentação oficial da StayFlow.



Este documento define a identidade da empresa, estabelece seus princípios permanentes e documenta tecnicamente o estado do produto.



A partir desta versão, toda evolução da plataforma deverá respeitar os princípios aqui definidos e manter esta documentação atualizada.



O objetivo da StayFlow permanece inalterado:



\*\*Construir o melhor Gerente Digital Inteligente para hotelaria do mundo.\*\*



Este documento é um ativo permanente da empresa e deverá evoluir junto com o produto durante toda a sua história.



\*\*Fim da Versão Oficial 1.64.0\*\*