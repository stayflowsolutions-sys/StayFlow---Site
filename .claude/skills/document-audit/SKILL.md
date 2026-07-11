---
name: document-audit
description: Protocolo obrigatório para revisões completas de documentos longos (Master Context, diários, etc). Use sempre que for pedido para revisar, auditar ou atualizar 100% de um documento.
---

# Protocolo de Auditoria Completa de Documentos

Quando pedido para fazer uma "revisão completa" ou garantir que um documento está "100% atualizado", NUNCA declarar isso concluído sem seguir este protocolo:

1. Contar o total de linhas do arquivo antes de começar (wc -l).
2. Ler o arquivo inteiro em blocos sequenciais de ~800-900 linhas, com pequena sobreposição entre blocos, garantindo cobertura de 100% das linhas.
3. Nunca pular um trecho por assumir "isso é só filosofia/não deve ter mudado" — confirmar isso lendo o texto real, não pelo índice ou sumário.
4. Para cada bloco lido, comparar mentalmente com fatos conhecidos do projeto (histórico recente, decisões registradas, funcionalidades construídas) e sinalizar qualquer contradição ou desatualização encontrada.
5. Ao final, declarar explicitamente a cobertura total (ex: "linhas 1-6221 de 6221 confirmadas") antes de dizer que a revisão está completa.
6. Se o usuário perguntar "tem certeza que não falta nada?", isso é sinal para repetir o protocolo do zero com ainda mais rigor, não para apenas reafirmar a resposta anterior.

Este protocolo existe porque uma revisão anterior do Master Context da StayFlow foi declarada "completa" sem cobrir 100% do arquivo, e uma segunda passada revelou uma inconsistência real que tinha passado despercebida. Revisão incompleta apresentada como completa é inadmissível.
