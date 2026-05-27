PROMPT GERAL:
OBJETIVO-DESENVOLVER E APRIMORAR NOSSA IDEIA DE FORMA LÓGICA E COESA COM A PROPOSTA DA GS (Global Solution).

Como a IA foi utilizada
A IA foi utilizada como copiloto de desenvolvimento, auxiliando nas seguintes etapas:

-Planejamento da arquitetura — discutir como separar responsabilidades em módulos
-Revisão de lógica — verificar se as condicionais de alerta estavam corretas
-Formatação de output — sugestões para exibição de barras de progresso e emojis no terminal
-Revisão de docstrings — garantir clareza nas descrições de funções

O que NÃO foi feito pela IA:

A definição do problema e dos dados simulados foi feita pelo grupo
Os limites de alerta (limiares) foram pesquisados e decididos pelo grupo
A lógica do cálculo ambiental (fórmulas de CO₂, PUE) foi compreendida e validada pelo grupo

Registro de Prompts:

Prompt 1 — Planejamento da Arquitetura
Objetivo: Decidir como organizar os módulos do sistema.
Prompt enviado:  Estou fazendo um projeto Python de monitoramento de satélites para uma disciplina de programação estruturada. O projeto precisa:
               - Usar listas e dicionários para armazenar dados simulados de missões
               - Ter funções separadas para ingestão, análise e exibição
               - Calcular alertas de falhas e impacto ambiental dos data centers

Como eu poderia organizar os módulos? Quero separar bem as responsabilidades.

O que foi utilizado da resposta:
A sugestão de separar em dados/, core/ e relatorios/ foi aproveitada. A definição do que vai em cada camada partiu do grupo.

Prompt 2 — Lógica de Classificação de Nível de Alerta
Objetivo: Verificar se a abordagem com funções separadas _nivel_por_limiar_minimo e _nivel_por_limiar_maximo fazia sentido.
Prompt enviado:  Tenho um sistema onde alguns parâmetros são piores quando são baixos (combustível, bateria) e outros são piores quando são altos (temperatura). 
                 Faz sentido ter duas funções separadas para classificar o nível de alerta, ou tem uma forma mais simples?

O que foi utilizado da resposta:
A confirmação de que duas funções auxiliares pequenas são preferíveis a uma função com parâmetro booleano complexo. 
O grupo já havia chegado a uma conclusão similar.

Prompt 3 — Fórmulas de Impacto Ambiental
Objetivo: Verificar se as fórmulas de CO₂ e PUE estavam corretas.
Prompt enviado:  Para calcular a emissão de CO₂ de um data center, eu multiplico o consumo em kWh pelo fator de emissão da fonte de energia (em kg CO₂/kWh), certo? E o PUE divide o consumo total pelo consumo real de TI — então um PUE de 1.65 significa                    que 39% da energia vai para resfriamento e infra?

O que foi utilizado da resposta:
Confirmação das fórmulas e da interpretação do PUE como overhead percentual. Os valores dos fatores de emissão foram pesquisados pelo grupo nas fontes IPCC 2021 e ANEEL 2024.

Prompt 4 — Tratamento de Erros no Menu
Objetivo: Entender a melhor forma de validar entrada do usuário em um loop while.
Prompt enviado:  No meu menu Python, preciso que o usuário só consiga avançar digitando opções válidas (0-5). 
                 Qual a forma mais limpa de fazer isso com while + try/except?

O que foi utilizado da resposta:
O padrão while True com try/except ValueError e break após validação bem-sucedida. Adaptado para a estrutura específica do nosso menu.
