async function loadOpportunities() {
    try {
        const response = await fetch("/opportunities");
        const opportunities = await response.json();

        console.log("StayFlow opportunities:", opportunities);

        const container = document.querySelector("[data-opportunity-center]");

        if (!container) {
            return;
        }

        container.innerHTML = "";

        if (!opportunities.length) {
            container.innerHTML = `
                <div class="empty-state">
                    Nenhuma oportunidade ativa no momento.
                </div>
            `;
            return;
        }

        opportunities.forEach((opportunity) => {
            const card = document.createElement("div");
            card.className = "opportunity-card";

            card.innerHTML = `
                <div class="opportunity-header">
                    <span class="opportunity-type">${opportunity.type || "opportunity"}</span>
                    <span class="opportunity-urgency ${opportunity.urgency || "low"}">
                        ${(opportunity.urgency || "low").toUpperCase()}
                    </span>
                </div>

                <div class="opportunity-description">
                    ${opportunity.description || "Sem descrição."}
                </div>

                <div class="opportunity-meta">
                    <span>Score: ${opportunity.score || 0}/100</span>
                    <span>Valor estimado: R$ ${Number(opportunity.estimated_value || 0).toFixed(2)}</span>
                </div>

                <div class="opportunity-action">
                    ${opportunity.next_action || "Revisar conversa manualmente."}
                </div>

                <div class="opportunity-phone">
                    Hóspede: ${opportunity.phone || "sem telefone"}
                </div>
            `;

            container.appendChild(card);
        });

    } catch (error) {
        console.error("Erro ao carregar oportunidades:", error);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    loadOpportunities();
});