# MarketFlow AI — Intelligent Marketing Campaign Studio

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-059669.svg)](https://langchain-ai.github.io/langgraph/)
[![OpenRouter](https://img.shields.io/badge/Gateway-OpenRouter-6366F1.svg)](https://openrouter.ai/)
[![Tavily](https://img.shields.io/badge/Search-Tavily%20API-0284C7.svg)](https://tavily.com/)
[![n8n](https://img.shields.io/badge/Automation-n8n-EA580C.svg)](https://n8n.io/)
[![Google Sheets](https://img.shields.io/badge/Sheets-Registration-34A853.svg)](https://www.google.com/sheets/about/)
[![Gmail](https://img.shields.io/badge/Email-Gmail%20API-EA4335.svg)](https://workspace.google.com/products/gmail/)

O **MarketFlow AI** é uma plataforma avançada desenvolvida para a criação estruturada, fundamentada e automatizada de campanhas completas de marketing digital multicanal. A aplicação combina **pesquisa de tendências em tempo real**, **orquestração determinística multiagente via LangGraph**, **camada de conformidade e guardrails**, e **automação externa de registro e entrega via n8n, Google Sheets e Gmail**.

---

## 🎯 1. Objetivo do MarketFlow AI

O objetivo do MarketFlow AI é transformar um briefing inicial bruto em uma campanha publicitária abrangente, consistente e pronta para execução, eliminando alucinações e garantindo aderência estrita às diretrizes da marca e às normas comerciais.

A solução cobre o ciclo completo de planejamento e produção:
- **Pesquisa de Mercado:** Consulta a dados reais e tendências recentes antes da geração estratégica.
- **Estratégia Coesa:** Posicionamento de valor, proposta central e direcionamento de tom de voz.
- **Redação Publicitária Multicanal:** Produção de peças sob medida para Instagram, WhatsApp e E-mail marketing.
- **Revisão Crítica e SEO:** Avaliação estrutural, validação de apelos de venda e sugestão de palavras-chave para descoberta orgânica.
- **Direção de Arte e Prompts de Imagem:** Especificação estética e geração de prompts detalhados para geradores generativos visuais.
- **Conformidade Determinística (Guardrails):** Análise automatizada de risco legal, promessas excessivas e consistência de briefing.
- **Distribuição e Registro:** Exportação em Markdown (.md) e Texto (.txt), além de despacho via webhook seguro para registro no Google Sheets e envio aos revisores humanos via Gmail.

---

## 🛠️ 2. Tecnologias Utilizadas

| Tecnologia | Função na Aplicação |
|---|---|
| **Python 3.11+** | Linguagem principal do backend e orquestração. |
| **Streamlit 1.35+** | Interface visual moderna com arquitetura Dark SaaS Studio, CSS refinado, gestão de sessão e reatividade em tempo real. |
| **LangGraph 0.2+** | Orquestração do pipeline multiagente determinístico com estado compartilhado (`CampaignState`), sem ciclos infinitos e com propagação de progresso via callbacks. |
| **OpenRouter API** | Gateway unificado de modelos de linguagem (LLM) com roteamento automático (`openrouter/auto`) e fallback de modelos. |
| **Tavily Search API** | Motor de busca em tempo real otimizado para agentes de IA, com sanitização de dados, normalização de fontes e cache em memória. |
| **Guardrails Determinísticos** | Camada própria e determinística de validação sintática, estrutural e regulatória de publicidade. |
| **n8n Workflow Automation** | Orquestrador de processos que processa submissões via Webhook seguro com autenticação de cabeçalho (`Header Auth`). |
| **Google Sheets API** | Registro persistente e tabulado do histórico de submissões das campanhas gerenciado pelo n8n. |
| **Gmail API** | Disparo automatizado de e-mails de notificação e revisão com o relatório integral da campanha. |
| **Requests / OpenAI SDK** | Clientes HTTP de alta performance para comunicação com APIs externas com sanitização de credenciais e mascaramento de logs. |

---

## 🤖 3. Arquitetura Multiagente e Responsabilidades

A geração da campanha é estruturada em uma cadeia linear de **4 agentes especializados de IA** antecedidos por uma etapa de pesquisa de mercado e sucedidos por uma camada de compliance:

```
[ Usuário / Streamlit UI ]
           │ (Briefing validado)
           ▼
[ Pesquisa Web (Tavily API) ] ──► Fontes reais de mercado (URLs, títulos e trechos)
           │
           ▼
[ Agente 1: Pesquisador & Estrategista ] ──► Plano estratégico fundamentado em fatos
           │
           ▼
[ Agente 2: Copywriter Multicanal ]      ──► Textos adaptados aos canais selecionados
           │
           ▼
[ Agente 3: Revisor Crítico & SEO ]      ──► Refinamento, coerência e palavras-chave
           │
           ▼
[ Agente 4: Designer de Prompts de Imagem] ──► Direção visual e prompts de arte
           │
           ▼
[ Guardrails de Compliance ]             ──► Avaliação determinística de conformidade
           │
     ┌─────┴────────────────────────────────┐
     ▼                                      ▼
[ Exportação de Arquivos ]             [ Automação n8n ]
(.md e .txt)                                   │ (Webhook + Header Auth)
                                        ┌──────┴──────┐
                                        ▼             ▼
                              [ Google Sheets ]  [ Gmail API ]
```

### Detalhamento dos Agentes:

1. **Agente 1 — Pesquisador de Tendências e Estrategista de Marketing:**
   - **Entrada:** Briefing original do formulário + resultados estruturados da pesquisa de mercado (Tavily).
   - **Responsabilidade:** Estruturar a proposta de valor, mensagem central, posicionamento e tom de voz.
   - **Diretriz de Integridade:** Separa categoricamente fatos comprovados de inferências ou suposições. Não inventa métricas, dados de mercado ou fontes fictícias.

2. **Agente 2 — Copywriter Multicanal:**
   - **Entrada:** Briefing da oferta + estratégia definida pelo Agente 1.
   - **Responsabilidade:** Redigir conteúdos publicitários persuasivos exclusivamente para os canais selecionados pelo usuário:
     - *Instagram:* Ganchos de atenção, corpo da legenda, chamadas para ação (CTA) e hashtags temáticas.
     - *WhatsApp:* Mensagens conversacionais de abordagem direta e modelos de follow-up.
     - *E-mail Marketing:* Linhas de assunto (com gatilhos de curiosidade/benefício), pré-cabeçalhos e corpo do e-mail.

3. **Agente 3 — Revisor Crítico e Otimizador SEO:**
   - **Entrada:** Briefing original + estratégia do Agente 1 + textos preliminares do Agente 2.
   - **Responsabilidade:** Avaliar criticamente o alinhamento das peças à estratégia, conferir a consistência das promessas e chamadas para ação, sugerir palavras-chave estratégicas para busca orgânica e intenção de busca, e consolidar a versão final polida dos textos.

4. **Agente 4 — Designer de Prompts de Imagem:**
   - **Entrada:** Briefing da oferta + estratégia do Agente 1 + versão final dos textos do Agente 3.
   - **Responsabilidade:** Definir o guia de direção visual da campanha (paleta de cores, estilo de iluminação, enquadramento e proporção/aspect ratio) e redigir prompts técnicos detalhados e prontos para uso em motores generativos visuais (Midjourney, DALL-E 3, Stable Diffusion) para cada canal ativo.

---

## 🌐 4. Pesquisa Externa e Tratamento das Fontes (Tavily API)

O módulo `research_service.py` conecta a aplicação à **Tavily Search API**, permitindo que a IA baseie o posicionamento mercadológico em dados reais do setor:

- **Execução Prévia:** A consulta externa é realizada de forma determinística antes da primeira chamada de LLM do Agente 1.
- **Normalização e Validação:**
  - Descarte rigoroso de itens sem URL válida, sem título ou com corpo vazio.
  - Formatação padronizada contendo URL real, título da publicação, trecho observado e data de publicação (quando disponível).
- **Sanitização de Segurança:** Filtro e neutralização preventiva contra potenciais ataques de injeção de prompt (*prompt injection*) embutidos no conteúdo de páginas de terceiros.
- **Cache em Memória:** As consultas e seus resultados são mantidos em cache para evitar chamadas redundantes e desperdício de requisições durante a mesma sessão.
- **Fallback Gracioso e Transparente:** Caso a API de pesquisa esteja sem chave configurada, com cota esgotada ou com problemas de rede, a aplicação não falha. O Agente 1 é instruído a seguir estritamente com os dados do briefing, e o relatório registra de forma explícita a indisponibilidade temporária da pesquisa externa, sem alucinar URLs ou fontes inexistentes.

---

## 🧭 5. Orquestração com LangGraph

A orquestração do pipeline multiagente é implementada no módulo `graph_orchestrator.py` utilizando o **LangGraph**:

- **Grafo Dirigido Determinístico:** O fluxo é modelado por meio de um `StateGraph` estritamente sequencial:
  `START` ➔ `pesquisador_tendencias` ➔ `copywriter` ➔ `especialista_seo` ➔ `designer_prompts_imagem` ➔ `guardrails` ➔ `END`.
- **Estado Estruturado (`CampaignState`):** Um `TypedDict` central mantém e propaga os dados entre os nós:
  - `form_data`: Dados do formulário de entrada.
  - `research_data`: Dados normalizados da pesquisa externa.
  - `strategy`: Saída estruturada do Agente 1.
  - `preliminary_copy`: Textos gerados pelo Agente 2.
  - `review_and_final`: Análise e versão final do Agente 3.
  - `image_prompts`: Prompts e direção visual do Agente 4.
  - `guardrails_result`: Dicionário com a avaliação determinística de conformidade.
  - `error`: Registro de eventuais falhas durante o percurso.
- **Comunicação Reativa com a UI:** Os eventos de início, conclusão e falha de cada nó são despachados para a interface do Streamlit em tempo real via callbacks (`RunnableConfig` e `contextvars.ContextVar`), atualizando o painel visual sem exigir polling ativo ou recargas de página.
- **Controle de Execução:** Ausência intencional de ciclos ou comportamentos autônomos indeterminados, garantindo tempo de resposta previsível e custo controlado de tokens.

---

## 🛡️ 6. Guardrails e Conformidade Publicitária

A aplicação conta com um módulo determinístico independente de validação em `guardrails.py`, executado internamente ao grafo do LangGraph e exibido na interface visual:

- **Validações Executadas (Sem chamadas adicionais a LLMs):**
  - **Integridade Estrutural:** Validação da presença de todas as seções obrigatórias da estratégia, cópias, revisão e direção de arte.
  - **Cobertura de Canais:** Verificação de que todos os canais solicitados no briefing receberam textos específicos.
  - **Detecção de Promessas Irrealistas:** Identificação de expressões vedadas ou de alto risco publicitário (ex.: *"100% garantido"*, *"retorno sem risco"*, promessas de enriquecimento rápido, alegações médicas ou de cura não comprovadas).
  - **Aderência aos Dados de Entrada:** Checagem de conformidade com a chamada para ação (CTA) e os diferenciais declarados.
- **Classificação e Ações:**
  - **Score de Conformidade:** Pontuação de 0 a 100 baseada na gravidade dos desvios identificados.
  - **Status Aprovado (`approved`):** Campanha validada, sem bloqueios.
  - **Avisos de Atenção (`warning`):** Alertas comerciais que recomendam verificação humana, mas não impedem o envio.
  - **Falhas Críticas (`blocked`):** Bloqueio preventivo e automático do botão de disparo para a automação n8n. O usuário recebe diagnósticos com instruções claras de remediação para ajustar o briefing.

---

## ⚡ 7. Integração n8n, Gmail e Google Sheets

Após a geração da campanha e a aprovação pelos Guardrails, o usuário pode revisar os materiais e acionar o encaminhamento automatizado:

```
[ MarketFlow AI ] ──(HTTP POST + Header Auth)──► [ Webhook n8n ]
                                                         │
                                        ┌────────────────┴────────────────┐
                                        ▼                                 ▼
                             [ Nó: Google Sheets ]               [ Nó: Gmail API ]
                             Gravação estruturada da              Disparo de e-mail ao
                             submissão com ID e resumo            revisor com relatório
```

- **Autenticação e Segurança:** A requisição para o webhook do n8n utiliza cabeçalho de autenticação seguro (`X-Campanha-Token`) comparado em tempo constante.
- **Nó Google Sheets (Registro Histórico):** Registra de forma persistente a submissão com os campos:
  `Data/Hora`, `ID da Submissão`, `Nome do Produto`, `Objetivo`, `Canais Selecionados`, `Status da Campanha` e `Resumo da Estratégia`.
- **Nó Gmail (Notificação ao Revisor):** Encaminha um e-mail estruturado contendo o relatório completo em formato Markdown e texto puro para validação da equipe de marketing.
- **Resposta Síncrona (`responseNode`):** O n8n responde com HTTP 200 contendo payload JSON estruturado (`success`, `submission_id`, `message`).
- **Estados Estritamente Observáveis:** A interface do Streamlit representa apenas os estados que a aplicação consegue observar diretamente via protocolo HTTP (Pronto ➔ Enviando ➔ Concluído/Erro/Incerteza), sem simular de forma fictícia o progresso interno de nós do n8n enquanto a requisição estiver em trânsito.
- **Tratamento Seguro de Falhas:** Prevenção contra duplo clique, descarte seguro de retornos em formato HTML inesperado e detecção de incerteza em cenários de *timeout* (`uncertain=True`).

---

## 💻 8. Configuração de Desenvolvimento

### Pré-requisitos:
- Python 3.11 ou superior instalado.
- Chave de API do [OpenRouter](https://openrouter.ai/).
- Chave de API do [Tavily Search](https://tavily.com/) *(opcional para pesquisa de tendências; sistema opera em fallback transparente se ausente)*.
- Instância do [n8n](https://n8n.io/) configurada com credenciais do Google Sheets e Gmail *(opcional para a etapa de automação)*.

### Estrutura de Arquivos:
```text
campanha-ia/
├── app.py                         # Interface Streamlit e gerenciamento de estado
├── agents.py                      # Funções individuais dos 4 agentes
├── graph_orchestrator.py          # Orquestração do StateGraph via LangGraph
├── prompts.py                     # Engenharia de prompts e personas dos agentes
├── research_service.py            # Integração com Tavily Search API e sanitização
├── guardrails.py                  # Validação determinística de compliance
├── openrouter_service.py          # Cliente OpenRouter com auto-routing de modelos
├── automation_service.py          # Integração HTTP segura com n8n (Sheets + Gmail)
├── ui_components.py               # Componentes estilizados em HTML/CSS (Dark SaaS)
├── requirements.txt               # Dependências do projeto
├── .gitignore                     # Proteção de segredos e ambientes locais
├── .streamlit/
│   ├── config.toml                # Otimizações de renderização do Streamlit
│   ├── secrets.toml               # Credenciais locais (NÃO versionar)
│   └── secrets.toml.example       # Template de referência para configuração
└── n8n/
    ├── workflow-marketflow-v2-dev.json # Definição exportada do fluxo no n8n
    └── postman-payload-example.json    # Exemplo de payload HTTP aceito pelo webhook
```

### Configuração dos Segredos (`secrets.toml`):
Crie o arquivo `.streamlit/secrets.toml` a partir do template `.streamlit/secrets.toml.example`:

```toml
# ==============================================================================
# MARKETFLOW AI — CONFIGURAÇÕES DE SEGREDOS LOCAIS
# ==============================================================================

# 1. Gateway de Inteligência Artificial (OpenRouter)
OPENROUTER_API_KEY = "sua_chave_openrouter_aqui"
OPENROUTER_MODEL = "auto"

# 2. Pesquisa de Tendências de Mercado em Tempo Real (Tavily Search API)
TAVILY_API_KEY = "sua_chave_tavily_aqui"

# 3. Automação de Processos (n8n Webhook)
N8N_WEBHOOK_URL = "https://sua-instancia.app.n8n.cloud/webhook/seu-endpoint"
N8N_WEBHOOK_TOKEN = "seu_token_secreto_aqui"

# 4. Senha de Proteção de Acesso à Demonstração
DEMO_ACCESS_PASSWORD = "sua_senha_aqui"
```

---

## 🚀 9. Instruções de Execução e Testes

### 1. Criar e Ativar Ambiente Virtual:

No Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

No Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Instalar Dependências:
```bash
pip install -r requirements.txt
```

### 3. Iniciar a Aplicação Web:
```bash
streamlit run app.py
```
Acesse a aplicação no seu navegador em: `http://localhost:8501`.

### 4. Execução dos Testes Automatizados:

A suíte de testes do MarketFlow AI utiliza **mocks rigorosos**, garantindo que nenhum teste realize chamadas reais a APIs externas ou consuma tokens e créditos:

**Executar a suíte completa de testes unitários (69 testes):**
```bash
python -m unittest test_langgraph_orchestration test_agent1_research_mock test_agent4_mock test_guardrails test_n8n_v2_sheets_mock test_research_service test_robustness -v
```

**Executar testes de geração e exportação de relatórios:**
```bash
python test_export.py
```

**Executar testes unitários de integração HTTP com n8n:**
```bash
python test_stage9_unit.py
```

---

## ⚠️ 10. Limitações da Aplicação

1. **Dependência de Serviços de Rede Externos:**
   - A geração dos textos depende da disponibilidade e latência do gateway OpenRouter e dos provedores de LLM associados.
   - A pesquisa de tendências depende da disponibilidade e conectividade com a Tavily Search API.
   - O encaminhamento de automação depende da estabilidade do n8n e das quotas de API do Google Sheets e Gmail.
2. **Geração de Imagens:**
   - O Agente 4 produz **diretrizes visuais e prompts textuais de alta fidelidade técnica**, mas a aplicação não renderiza imagens binárias diretamente (os prompts devem ser aplicados em ferramentas como Midjourney ou DALL-E 3).
3. **Persistência de Sessão:**
   - O MarketFlow AI opera de maneira *stateless* e em memória durante a sessão web do Streamlit. O histórico persistente de campanhas aprovadas é registrado externamente na planilha do Google Sheets através do n8n.
4. **Natureza Estatística da IA Generativa:**
   - Textos, estimativas e sugestões de SEO gerados por modelos de linguagem têm finalidade estritamente orientativa e criativa. Todo material deve passar por **criteriosa validação e revisão humana** antes de qualquer publicação comercial ou veiculação em mídia paga.
