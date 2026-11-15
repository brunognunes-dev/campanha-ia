# Campanha IA — Central Automatizada de Campanhas de Marketing Multicanal

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![OpenRouter](https://img.shields.io/badge/Gateway-OpenRouter-6366F1.svg)](https://openrouter.ai/)
[![n8n](https://img.shields.io/badge/Automation-n8n%20Cloud-EA580C.svg)](https://n8n.io/)

Aplicativo web acadêmico desenvolvido para a criação automatizada, consistente e personalizada de campanhas de marketing digital para múltiplos canais, utilizando **arquitetura multiagente com IA generativa** e **automação de encaminhamento via n8n e Gmail**.

---

## 📌 1. Visão Geral e Contexto Acadêmico

- **Programa:** Geração Tech
- **Curso:** Inteligência Artificial Generativa
- **Tema:** Arquitetura Multiagente e Automação de Processos de Marketing
- **Apresentação:** Novembro de 2026
- **Objetivo:** Demonstrar a aplicação prática de agentes especializados de IA generativa colaborando em sequência para planejamento, redação e revisão de campanhas publicitárias, com posterior encaminhamento manual para revisão humana através de webhook automatizado.

---

## 🏗️ 2. Arquitetura do Sistema

A aplicação foi projetada com separação rigorosa de responsabilidades, sem complexidade desnecessária ou acoplamento a bancos de dados:

```
[ Usuário / Streamlit UI ]
           │
           ▼
[ Agente 1: Estrategista ]  ──► Interpreta briefing e gera plano de marketing
           │
           ▼
[ Agente 2: Copywriter ]    ──► Redige conteúdos específicos por canal (Instagram, WhatsApp, E-mail)
           │
           ▼
[ Agente 3: Revisor ]       ──► Valida coerência, sugere SEO orientativo e entrega versão final
           │
     ┌─────┴────────────────────────────────┐
     ▼                                      ▼
[ Exportação ]                     [ Automação n8n ]
(.md e .txt)                                │ (Webhook + Header Auth)
                                            ▼
                                   [ Envio Gmail ]
```

### Pipeline Multiagente:
1. **Agente 1 — Estrategista de Marketing:** Recebe os dados de produto/serviço, objetivo, público-alvo e tom, gerando a proposta de valor, mensagem central e diretrizes estratégicas sem alucinar fatos.
2. **Agente 2 — Copywriter Multicanal:** Produz os textos persuasivos adaptados com exclusividade aos canais selecionados (Instagram: gancho, legenda e hashtags; WhatsApp: mensagem conversacional e follow-up; E-mail marketing: assunto, prévia e corpo).
3. **Agente 3 — Revisor e Otimizador:** Analisa criticamente a coerência dos textos frente aos dados reais, fortalece as chamadas para ação (CTAs), sugere palavras-chave orientativas para descoberta orgânica e entrega a versão final pronta para uso.

---

## 🛠️ 3. Tecnologias Utilizadas

- **Linguagem:** Python 3.11+
- **Front-end e Apresentação:** Streamlit
- **Gateway de Modelos (LLM):** OpenRouter API (SDK OpenAI com resolução dinâmica de modelos gratuitos do catálogo)
- **Automação de Fluxo:** n8n Cloud
- **Notificação e Entrega:** Gmail API
- **Versionamento e Hospedagem:** GitHub e Streamlit Community Cloud

---

## 📂 4. Estrutura do Projeto

```text
campanha-ia/
├── app.py                     # Interface Web, controle de sessão e visualização
├── agents.py                  # Orquestração das funções dos 3 agentes
├── prompts.py                 # Prompts de sistema e engenharia de contexto
├── openrouter_service.py      # Cliente OpenRouter e fallback dinâmico de modelos
├── automation_service.py      # Comunicação HTTP segura com o webhook do n8n
├── requirements.txt           # Dependências do projeto (Streamlit, OpenAI, Requests)
├── README.md                  # Documentação completa
├── .gitignore                 # Proteção de credenciais, caches e ambiente virtual
├── .streamlit/
│   ├── config.toml            # Otimizações de desempenho e servidor do Streamlit
│   ├── secrets.toml           # Credenciais locais seguras (nunca versionar)
│   └── secrets.toml.example   # Modelo de referência dos segredos
└── n8n/
    └── workflow-campanha-ia.json # Definição exportada e sanitizada do workflow n8n
```

---

## 🚀 5. Instalação e Execução Local

### Pré-requisitos:
- Python 3.11 ou superior instalado
- Conta no [OpenRouter](https://openrouter.ai/) (para obter uma API Key)
- Conta no [n8n Cloud](https://n8n.io/) (para o workflow de automação)

### Passo a passo no Windows (PowerShell):

1. **Clonar ou acessar a pasta do projeto:**
   ```powershell
   cd "c:\Users\Bruno Gabriel\Documents\campanha-ia"
   ```

2. **Criar e ativar o ambiente virtual:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Instalar as dependências:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configurar os segredos locais:**
   Crie ou edite o arquivo `.streamlit/secrets.toml` com base no `.streamlit/secrets.toml.example`:
   ```toml
   # Gateway OpenRouter
   OPENROUTER_API_KEY = "sua_chave_sk_or_v1_aqui"
   OPENROUTER_MODEL = "auto"

   # Automação n8n
   N8N_WEBHOOK_URL = "https://sua-instancia.app.n8n.cloud/webhook/campanha-ia-webhook"
   N8N_WEBHOOK_TOKEN = "seu_token_secreto_aqui"

   # Senha de proteção da demonstração
   DEMO_ACCESS_PASSWORD = "admin"
   ```

5. **Iniciar a aplicação web:**
   ```powershell
   streamlit run app.py
   ```
   Acesse no navegador: `http://localhost:8501`.

---

## ⚙️ 6. Configuração da Automação no n8n

O arquivo sanitizado [`n8n/workflow-campanha-ia.json`](n8n/workflow-campanha-ia.json) contém o fluxo oficial com 4 nós integrados:

1. **Importação:** No seu painel do n8n Cloud, crie um novo workflow e selecione **Import from File**, escolhendo `workflow-campanha-ia.json`.
2. **Autenticação (Header Auth):** Configure uma credencial do tipo *Header Auth* com o nome de cabeçalho `X-Campanha-Token` e o mesmo valor definido em `N8N_WEBHOOK_TOKEN`.
3. **Gmail:** Conecte sua conta do Google e defina no nó Gmail o endereço de e-mail fixo que receberá os relatórios de revisão.
4. **Ativação:** Mude o status do workflow para **Active** e copie a Production URL para o seu arquivo `secrets.toml`.

---

## ☁️ 7. Demonstração e Publicação no Streamlit Community Cloud

Para a apresentação acadêmica utilizando computadores externos ou dispositivos móveis:

1. Suba o código para o seu repositório no **GitHub** (o arquivo `.gitignore` já impede o envio de `.streamlit/secrets.toml`).
2. Acesse [share.streamlit.io](https://share.streamlit.io/) e conecte seu repositório GitHub.
3. Configure o arquivo principal como `app.py`.
4. Em **Advanced Settings > Secrets**, cole o conteúdo completo do seu `.streamlit/secrets.toml`.
5. Clique em **Deploy**. A aplicação estará disponível publicamente em uma URL `.streamlit.app` protegida pela senha de demonstração configurada.

---

## 🔒 8. Segurança e Boas Práticas

- **Proteção contra Acesso Indevido:** Bloqueio por senha de demonstração gerenciada via `st.session_state` e `st.secrets`.
- **Prevenção de Vazamento:** Chaves de API e tokens nunca aparecem na interface, no código versionado ou em mensagens de erro.
- **Proteção de Envio Duplo:** A automação impede cliques repetidos e não realiza tentativas automáticas em caso de timeout.
- **Aviso Ético e Legal:** Todos os relatórios contêm nota obrigatória orientando que todo conteúdo gerado por IA deve passar por criteriosa validação e revisão humana antes de veiculação pública comercial.
