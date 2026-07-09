---
name: stayflow-context
description: Carrega o contexto histórico do projeto StayFlow (decisões, padrões, pendências). Use no início de qualquer sessão nova de trabalho no projeto, antes de propor ou implementar mudanças.
---

# Contexto StayFlow

Antes de propor ou implementar qualquer mudança neste projeto, leia:

1. docs/DIARIO_DE_ENGENHARIA.md — histórico detalhado de cada sessão de trabalho, decisões tomadas e o porquê, pendências abertas.
2. docs/STAYFLOW_MASTER_CONTEXT.md — visão geral da arquitetura, stack e estado atual do produto.

## Padrões já decididos (não re-perguntar, não re-propor alternativas sem justificativa forte)

- Token de cor oficial: #0b84ff
- Arquitetura de CSS: arquivos separados por página/responsabilidade (tokens.css, reset.css, app.css, landing.css, auth.css), não um legacy.css monolítico
- Padrão de UI "+ criar novo na hora" para campos como categoria, unidade de medida, tipo de quarto, tipo de propriedade
- Multi-tenant: todas as queries devem ser escopadas por hostel_id via @require_auth (utils/tenant.py)
- Banco de dados vive em disco persistente no Render (STAYFLOW_DATA_DIR), nunca caminho relativo

## Como trabalhar com o usuário (Caio)

- Caio é autodidata, aprende via IA, quer entender profundamente o código, não só receber a solução pronta
- Prefere trabalhar em etapas pequenas e confirmadas, uma de cada vez
- Sempre que uma mudança for potencialmente destrutiva (reescrever arquivo, matar processos, deletar dados), avisar antes com clareza do que pode dar errado

## Pendências ativas (conferir se já não mudou)

Ver seção "O que ficou pendente" no DIARIO_DE_ENGENHARIA.md mais recente.
