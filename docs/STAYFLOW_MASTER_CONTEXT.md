\# STAYFLOW MASTER CONTEXT

\## Documento Mestre Oficial



\*\*Documento:\*\* STAYFLOW\_MASTER\_CONTEXT.md



\*\*Versão:\*\* 1.9.1



\*\*Status:\*\* Oficial



\*\*Projeto:\*\* StayFlow



\*\*Classificação:\*\* Confidencial – Uso Interno



\*\*Última atualização:\*\* 23/07/2026



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

        ├── DIARIO\_DE\_ENGENHARIA.md

        └── CHECKLIST\_ATIVO.md

```



Nota (atualizada em 09/07/2026, versão 1.3.0): a pasta `docs/` não é mais

uma pasta irmã de `HostelBot`/`StayFlow---Site` — ela vive dentro de

`StayFlow---Site/docs/`. Essa decisão foi tomada para permitir que o

skill de contexto automático do Claude Code (`.claude/skills/`) localize

e carregue este documento e o Diário de Engenharia no início de cada

sessão de desenvolvimento, já que a ferramenta opera a partir da raiz do

repositório Frontend.



Cada projeto possui responsabilidades independentes e bem definidas.



\*\*Nota crítica de infraestrutura (atualizada em 13/07/2026, versão 1.4.0):\*\*
o ambiente de hospedagem (Render) builda apenas um repositório por serviço.
Por isso, além do repositório `StayFlow---Site` independente (onde o
desenvolvimento do frontend efetivamente acontece), existe uma \*\*cópia
física\*\* de todo o conteúdo do frontend dentro de
`HostelBot/StayFlow---Site/`, versionada dentro do próprio repositório do
backend. É essa cópia interna, não o repositório `StayFlow---Site`
sozinho, que o Render de fato publica em produção.



Isso significa que \*\*toda alteração de frontend precisa ser replicada
manualmente\*\* para dentro do `HostelBot` (cópia de arquivo + commit + push
nos dois repositórios) antes de chegar ao ar. Esse processo manual é uma
dívida técnica conhecida e ativa — gera risco real de divergência entre os
dois repositórios se um dos dois passos for esquecido, e já causou
retrabalho e confusão real durante o desenvolvimento. A resolução
definitiva (separar o frontend como Static Site próprio do Render, com o
Backend expondo apenas API, possivelmente num subdomínio dedicado) está
registrada no Roadmap Oficial (Capítulo 17) como item a resolver quando a
prioridade operacional atual estiver concluída.



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

  decisões, descobertas e pendências registradas cronologicamente;

\- CHECKLIST\_ATIVO.md — fonte única de prioridades de trabalho em

  andamento, com regra de não iniciar escopo novo antes de concluir o que

  já está registrado.



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

├── dashboard.html      (aplicação principal — single-page, abas internas:

│                         dashboard, chats, configurações, reservas,

│                         financeiro, estoque, operações, receitas)

├── Login.html

├── Register.html

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

│   ├── STAYFLOW_MASTER_CONTEXT.md (este documento)

│   └── CHECKLIST_ATIVO.md         (fonte única de prioridades de trabalho)

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
configurável de permissões, de um catálogo de 12 chaves — ver 13.3 e
16.22 — não existem funções fixas no sistema, apenas a função "Admin"
com todas as permissões e "Staff" sem nenhuma permissão por padrão,
criadas automaticamente durante a migração de dados existentes).



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

\- Chats

\- Guests

\- Opportunities

\- Activity

\- Executive Summary

\- Reservations

\- Finance

\- Reports

\- Inventory (fornecedores e itens de estoque)

\- Operations

\- Revenue (catálogo de upsells)

\- Settings

\- Team e Roles (gestão de equipe, funções e permissões individuais)

\- WhatsApp Webhook (integração com a Meta Cloud API)



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



\---



\## 13.7 Escalabilidade



A arquitetura das APIs foi projetada para permitir futuras integrações com:



\- aplicativo do viajante;

\- PMS;

\- Channel Managers;

\- motores de reserva;

\- plataformas de pagamento;

\- parceiros estratégicos;

\- serviços de Inteligência Artificial.



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

\- Chats;

\- Guest Profile;

\- Recent Activity;

\- Reservas;

\- Financeiro;

\- Relatórios;

\- Estoque;

\- Operações;

\- Receitas (catálogo de upsells);

\- Configurações;

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

\- Ocupação em tempo real;

\- Housekeeping (Mapa de Camas);

\- Calendário Operacional;

\- Notificações Inteligentes;

\- Comandos por IA;

\- Indicadores personalizados.



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

\- atualização automática das informações operacionais.



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

\- próxima ação.



\---



\## 16.5 Guest Profile



\*\*Status:\*\* Implementado



\### Objetivo



Concentrar informações relevantes sobre cada hóspede.



\### Capacidades atuais



\- dados cadastrais;

\- histórico de conversas;

\- oportunidades relacionadas;

\- informações consolidadas da operação.



\---



\## 16.6 Banco de Dados



\*\*Status:\*\* Implementado



\### Capacidades atuais



Persistência de:



\- hostels (multi-tenant, com credenciais de WhatsApp por unidade);

\- hóspedes;

\- mensagens (com timestamp por mensagem);

\- oportunidades;

\- reservas;

\- configurações do hostel;

\- fornecedores e itens de estoque;

\- catálogo de experiências/upsells (offerings).



O banco representa a memória operacional da plataforma.



\---



\## 16.7 APIs Oficiais



\*\*Status:\*\* Implementado



\### APIs disponíveis



\- Autenticação (login, sessão, logout);

\- Dashboard;

\- Chats;

\- Guests;

\- Opportunities;

\- Activity;

\- Executive Summary;

\- Reservations;

\- Finance;

\- Reports;

\- Inventory (fornecedores e estoque);

\- Operations;

\- Revenue;

\- Settings;

\- WhatsApp Webhook.



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



Gerenciar as reservas dos hóspedes de cada hostel.



\### Capacidades atuais



\- listagem e criação de reservas;

\- atualização de status (pendente, confirmada, check-in, check-out,

  cancelada) diretamente na tabela;

\- vínculo com o hóspede correspondente.



\---



\## 16.11 Módulo Financeiro



\*\*Status:\*\* Implementado



\### Objetivo



Consolidar a visão financeira da operação a partir de dados já existentes

na plataforma.



\### Capacidades atuais



\- reaproveita dados de Reservas e Opportunities, sem duplicar informação

  em tabela própria.



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



\- alertas de check-in/check-out pendente;

\- alertas de oportunidade urgente sem resposta;

\- alertas de estoque baixo.



Tarefas de limpeza (housekeeping) permanecem vazias intencionalmente —

dependem do Mapa de Camas, ainda não implementado (ver Roadmap Oficial).



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
  e apagar funções do hostel, com seleção das 12 permissões disponíveis
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



\- catálogo de 12 permissões, uma por seção principal do produto
  (dashboard, chats, opportunities, reservations, operations, guests,
  finance, reports, inventory, revenue, settings, team), centralizado
  numa única fonte de verdade reutilizada por todas as camadas do
  sistema (migração de dados, controle de acesso das rotas, interface);
\- toda rota protegida da plataforma exige a permissão específica
  correspondente à sua área, verificada a cada requisição — nunca
  apenas "estar logado";
\- funções totalmente configuráveis por hostel (o administrador decide
  quais das 12 permissões cada função concede, sem funções fixas
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
revisão humana antes do envio de mensagens (ver "Ask StayFlow como
agente de ação", Capítulo 17) — sem esse mecanismo, desativar a
resposta automática significaria simplesmente parar de responder o
hóspede, o que não é o comportamento pretendido pelo controle.



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



Plataforma Base em desenvolvimento.



\*\*Objetivo atual\*\*



Consolidar a primeira versão operacional da StayFlow com todos os componentes principais integrados.



Prioridades atuais:



\- corrigir a responsividade da plataforma para dispositivos móveis —

  \*\*confirmação do fix de navbar concluída em 13/07/2026\*\*: testado

  fisicamente em Safari iOS real (não apenas ferramenta headless),

  navbar permanece estável durante scroll rápido, sem piscar. Pendente:

  correção de um seletor de idioma que aparece cortado fora da tela em

  telas mobile estreitas (bug real confirmado, correção adiada de

  propósito para a fase de lapidação visual completa, já que o layout

  mobile do cabeçalho será reorganizado por completo);

\- \*\*terminar de concluir o menu de Configurações\*\* — as categorias

  Equipe (16.21/16.22) e IA (16.23) já estão 100% funcionais. Restam as

  5 categorias vazias (Empresa, Comunicação, Integrações além do

  WhatsApp, Segurança, Billing, Developer), que continuam sendo apenas

  botões visuais, sem decisão tomada sobre construir cada uma ou

  remover;

\- \*\*criação de reserva via modal flutuante\*\* — reaproveitando o sistema

  de modal genérico já construído para o painel de Equipe, em vez de

  exigir navegação para outra tela;

\- \*\*corrigir a arquitetura de tradução do Dashboard\*\* — a landing page

  (`index.html`) já possui um sistema central de tradução (PT/EN/ES);

  o Dashboard não segue o mesmo padrão de forma consistente, com partes

  traduzidas e partes que permanecem no idioma original independente da

  seleção. Correção priorizada antes de adicionar francês, alemão e

  possivelmente japonês ao seletor de idioma, para não multiplicar a

  inconsistência existente;

\- cadastrar o Hostel Lagares como o primeiro hostel-cliente real de

  produção, com cadastro, login e número de WhatsApp próprios — separado

  da conta de demonstração de vendas atualmente em uso pelo fundador;

\- avaliar estratégia de atendimento para hóspedes localizados no Brasil,

  dada a limitação de mensageria descrita no Capítulo 16 — decisão já

  tomada de registrar uma segunda conta de WhatsApp Business localizada

  no Brasil, implementação pendente;

\- concluir a experiência completa do frontend;

\- consolidar os Motores de Inteligência;

\- ampliar automações operacionais;

\- evoluir continuamente a experiência do usuário.





\---



\## 17.3 Próximas Prioridades



Após a consolidação da plataforma base, as próximas grandes capacidades serão desenvolvidas conforme sua relevância estratégica.



Entre elas:



\- Revenue Management avançado (precificação dinâmica, previsão de

  demanda — o catálogo básico de upsells já está implementado, ver

  Capítulo 16);

\- CRM Inteligente;

\- Agenda Operacional;

\- Housekeeping (Mapa de Camas e fluxo de limpeza);

\- Gestão Financeira avançada (fluxo de caixa, projeções — a consolidação

  básica já está implementada, ver Capítulo 16);

\- \*\*Ask StayFlow como agente de ação\*\* — hoje esse botão flutuante do

  Dashboard é uma simulação de conversa, sem conexão real com o Backend.

  Visão registrada em 19/07/2026: usar o mesmo mecanismo de function

  calling já validado na captura do nome do hóspede (ver Capítulo 16,

  seção 16.19) para permitir que o usuário converse com a IA sobre a

  própria operação e ela execute ações reais (ex.: relatar a chegada de

  uma compra e a IA atualizar o estoque correspondente sozinha), além de

  responder perguntas com contexto real da operação;

\- Motor de Reservas avançado, incluindo integração com Channel Managers —

  pesquisa realizada em 13/07/2026 confirmou que os principais canais de

  distribuição (Booking.com, Airbnb) mantêm hoje acesso de API fechado

  para desenvolvedores independentes/pequenos. Estratégia decidida: como

  primeiro passo, captura de reservas via leitura automatizada dos

  e-mails de confirmação que essas plataformas já enviam ao hostel

  (extração de dados estruturados via Inteligência Artificial, mesmo

  padrão já usado na captura de mensagens de WhatsApp), sem dependência

  de aprovação de parceria. A conexão via channel manager terceirizado

  (parceiro já certificado pelas OTAs) permanece como alternativa

  avaliável no futuro, condicionada a validação de custo e escopo de

  acesso. Esta frente fica deliberadamente represada até a conclusão

  total do menu de Configurações (ver 17.2);

\- Relatórios Inteligentes avançados (a versão básica de receita por

  canal e funil de conversão já está implementada, ver Capítulo 16);

\- Notificações Inteligentes;

\- Automações Operacionais;

\- Separação definitiva de infraestrutura de deploy — hoje o Frontend é

  publicado através de uma cópia manual mantida dentro do repositório do

  Backend (ver nota crítica no Capítulo 9), o que exige replicação manual

  de toda alteração de Frontend. Solução de longo prazo identificada:

  Frontend publicado como Static Site independente, Backend exposto

  apenas como API (possivelmente em subdomínio dedicado), eliminando a

  cópia manual.



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



\*\*Fim da Versão Oficial 1.6.0\*\*