"""
Modulo de Demonstracao Offline do MarketFlow AI 2.0.

Fornece dados e simulacao completa para apresentacao academica e testes offline,
sem dependencia de chamadas externas ao OpenRouter, Tavily Search API ou automacoes do n8n.
Cenario padrao: Café Aurora (Fortaleza - CE) — Campanha 'Sua Pausa Especial'.
"""

import datetime
from typing import Any, Callable, Optional
from guardrails import validate_campaign_guardrails
from output_validation import (
    validate_strategist_output,
    validate_copywriter_output,
    validate_reviewer_output,
    validate_image_designer_output
)

# ==============================================================================
# 1. BRIEFING FICTÍCIO PADRÃO (CAFÉ AURORA)
# ==============================================================================

DEMO_FORM_DATA: dict[str, Any] = {
    "product_name": "Café Aurora",
    "product_description": (
        "Cafeteria especializada em cafés artesanais, cappuccinos, bebidas geladas "
        "e acompanhamentos frescos, localizada em Fortaleza, Ceará. Um espaço dedicado "
        "a proporcionar momentos de pausa, aconchego e experiências gastronômicas de qualidade."
    ),
    "target_audience": (
        "Jovens adultos, estudantes universitários e profissionais de 20 a 45 anos "
        "interessados em cafés especiais, momentos de pausa na rotina e experiências gastronômicas acolhedoras."
    ),
    "objective": "Atrair novos clientes e gerar leads",
    "tone": "Criativo, descontraído e dinâmico",
    "differentials": (
        "Bebidas preparadas na hora com grãos selecionados; opções quentes e geladas adaptadas ao clima; "
        "ambiente confortável e acolhedor; atendimento atencioso; espaço apropriado para encontros e pausas."
    ),
    "cta": "Visite o Café Aurora e descubra o sabor da sua nova pausa especial.",
    "channels": ["Instagram", "WhatsApp", "E-mail marketing"]
}

# ==============================================================================
# 2. PESQUISA ILUSTRATIVA (SEM CONSULTA EXTERNA À TAVILY)
# ==============================================================================

DEMO_RESEARCH_DATA: dict[str, Any] = {
    "success": True,
    "query": "tendências de consumo cafés especiais cafeterias artesanais fortaleza ceará",
    "total_results": 3,
    "cached": False,
    "is_demo": True,
    "disclaimer": "Pesquisa ilustrativa — Modo Demonstração. Nenhuma consulta externa foi realizada.",
    "results": [
        {
            "title": "Exemplo Ilustrativo 1: Crescimento do Mercado de Cafés Especiais no Nordeste",
            "url": "https://exemplo-demonstracao.local/tendencias/cafes-especiais",
            "published_date": "Demonstração Offline",
            "content": (
                "Estudo conceitual ilustrativo indicando que consumidores jovens e profissionais urbanos "
                "buscam cafeterias que combinem cafés de alta qualidade com ambientes propícios para desacelerar e socializar."
            )
        },
        {
            "title": "Exemplo Ilustrativo 2: Bebidas Geladas à Base de Café em Regiões de Clima Quente",
            "url": "https://exemplo-demonstracao.local/tendencias/cold-brew-nordeste",
            "published_date": "Demonstração Offline",
            "content": (
                "Hipótese de mercado que aponta alta atratividade de cold brews, iced lattes e cafés gelados autorais "
                "em capitais com temperaturas elevadas, como Fortaleza."
            )
        },
        {
            "title": "Exemplo Ilustrativo 3: O Conceito de 'Third Place' (Terceiro Lugar) na Hospitalidade",
            "url": "https://exemplo-demonstracao.local/tendencias/hospitalidade-ambiente",
            "published_date": "Demonstração Offline",
            "content": (
                "Referência teórica sobre cafeterias que se consolidam como ponto de refúgio entre o trabalho e o lar, "
                "priorizando conforto, atendimento atencioso e produtos artesanais frescos."
            )
        }
    ]
}

# ==============================================================================
# 3. AGENTE 1 — ESTRATEGISTA DE MARKETING E PESQUISADOR
# ==============================================================================

DEMO_STRATEGY: str = (
    "## 1. Resumo do Briefing\n"
    "O **Café Aurora** é uma cafeteria fictícia sediada em Fortaleza (CE), focada em cafés artesanais, "
    "cappuccinos, bebidas geladas inovadoras e acompanhamentos frescos. O posicionamento baseia-se no acolhimento, "
    "na alta qualidade dos grãos e na criação de um refúgio acolhedor no cotidiano urbano.\n\n"
    "## 2. Objetivo da Campanha\n"
    "Promover a campanha **'Sua Pausa Especial'**, voltada para atrair novos clientes, fortalecer o reconhecimento "
    "da marca e incentivar visitas experienciais presenciais ao espaço da cafeteria.\n\n"
    "## 3. Caracterização do Público-Alvo\n"
    "Jovens adultos, estudantes universitários e profissionais de 20 a 45 anos que valorizam cafés especiais, buscam "
    "ambientes agradáveis para encontros ou leitura e desejam alternativas gastronômicas artesanais e refrescantes.\n\n"
    "## 4. Posicionamento Sugerido\n"
    "Posicionar o Café Aurora como o ponto de desaceleração ideal no ritmo acelerado de Fortaleza: um local onde cada "
    "xícara é preparada com cuidado técnico e servida com calor humano.\n\n"
    "## 5. Proposta de Valor\n"
    "A **Proposta de Valor** do Café Aurora reside na combinação entre cafés artesanais de alta seleção, "
    "bebidas quentes e geladas preparadas na hora e um ambiente confortável pensado para ser uma pausa restauradora no dia.\n\n"
    "## 6. Tom de Comunicação\n"
    "Acolhedor, moderno, natural, convidativo e criativo, transmitindo serenidade, frescor e paixão pela cultura do café.\n\n"
    "## 7. Mensagem Central\n"
    "**Mensagem Central:** 'O seu dia merece uma pausa especial: descubra os cafés artesanais e o aconchego do Café Aurora.'\n\n"
    "## 8. Estratégia por Canal de Distribuição\n"
    "- **Instagram:** Foco no apelo visual dos cafés, xícaras artesanais e atmosfera aconchegante, estimulando identificação e desejo de visita.\n"
    "- **WhatsApp:** Comunicação próxima, conversacional e empática, oferecendo um convite amigável e direto para um momento de descanso.\n"
    "- **E-mail marketing:** Narrativa imersiva (storytelling) sobre o ritual do café e os momentos de pausa, com estrutura organizada e chamada para conhecer o local.\n\n"
    "## 9. Análise de Mercado e Pesquisa Ilustrativa\n"
    "> *Pesquisa ilustrativa — Modo Demonstração. Nenhuma consulta externa foi realizada.*\n"
    "Com base em hipóteses ilustrativas de mercado, observa-se alta demanda por cafeterias que ofereçam opções geladas autênticas "
    "em Fortaleza, aliadas a espaços confortáveis que funcionem como respiro na rotina.\n\n"
    "## 10. Recomendações de Comunicação e Limitações da Análise\n"
    "Recomenda-se manter coerência visual em todos os pontos de contato e preservar a autenticidade das informações. "
    "**Limitações:** Por tratar-se de um ambiente de demonstração acadêmica com dados fictícios, não foram aferidos preços, horários "
    "ou métricas de concorrência local."
)

# ==============================================================================
# 4. AGENTE 2 — COPYWRITER MULTICANAL (VERSÃO PRELIMINAR)
# ==============================================================================

DEMO_PRELIMINARY_COPY: str = (
    "### 📸 Canal: Instagram (Feed / Stories)\n\n"
    "**Gancho (Hook):**\n"
    "Quando foi a última vez que você desacelerou para saborear de verdade o seu café?\n\n"
    "**Legenda:**\n"
    "Entre a correria do dia e os prazos de Fortaleza, reserve alguns minutos para você. "
    "No Café Aurora, cada bebida é preparada na hora com grãos artesanais cuidadosamente selecionados. "
    "Seja um cappuccino cremoso para começar a manhã ou um café gelado autoral para refrescar a tarde, "
    "nosso espaço acolhedor está de portas abertas para ser o seu momento de paz.\n\n"
    "**Chamada para Ação (CTA):**\n"
    "Venha viver essa experiência! Visite o Café Aurora e conheça o seu novo refúgio favorito.\n\n"
    "**Hashtags:**\n"
    "#CafeAurora #CafesEspeciais #FortalezaGastronomia #PausaEspecial #CafeArtesanal #MomentosCafe\n\n"
    "---\n\n"
    "### 💬 Canal: WhatsApp (Mensagem Direta / Lista de Transmissão)\n\n"
    "**Mensagem Natural:**\n"
    "Olá! Como está o seu dia por aí?\n\n"
    "Sabemos que a rotina na cidade não para, mas o seu bem-estar também merece prioridade. "
    "Passando para te fazer um convite sincero: que tal trocar a pressa por uma pausa especial hoje? "
    "Aqui no Café Aurora preparamos cafés artesanais e bebidas geladas refrescantes, sempre na hora, "
    "em um ambiente pensado para você respirar fundo e relaxar.\n\n"
    "**Chamada para Ação (CTA):**\n"
    "Dê uma passadinha para nos conhecer e descubra o sabor da sua nova pausa especial. Estamos esperando por você!\n\n"
    "---\n\n"
    "### ✉️ Canal: E-mail marketing\n\n"
    "**Assunto:** O seu dia merece uma pausa especial em Fortaleza ☕\n"
    "**Pre-header:** Descubra cafés artesanais preparados na hora em um espaço feito para desacelerar.\n\n"
    "**Saudação:** Olá,\n\n"
    "**Corpo do e-mail:**\n"
    "Você já reparou em quantas coisas acontecem ao mesmo tempo ao longo da semana? Entre compromissos, trânsito "
    "e telas, é comum esquecermos de criar pequenos rituais de cuidado pessoal.\n\n"
    "O Café Aurora nasceu exatamente para ser essa pausa no seu dia. Aqui, cada xícara conta uma história de dedicação: "
    "utilizamos cafés artesanais de alta qualidade, servimos acompanhamentos frescos e oferecemos desde o clássico espresso "
    "até bebidas geladas que combinam com a brisa de Fortaleza.\n\n"
    "Nosso espaço foi desenhado para acolher conversas leves, boas leituras ou simplesmente alguns minutos de tranquilidade.\n\n"
    "**Chamada para Ação (CTA):**\n"
    "Planeje a sua próxima pausa: conheça o Café Aurora e vivencie uma experiência pensada para você.\n\n"
    "**Encerramento:**\n"
    "Com carinho e café fresco,\n"
    "Equipe Café Aurora"
)

# ==============================================================================
# 5. AGENTE 3 — REVISOR E ESPECIALISTA EM SEO (DIAGNÓSTICO E VERSÃO FINAL)
# ==============================================================================

DEMO_REVIEWER_AND_FINAL: str = (
    "## 1. Diagnóstico de Revisão e Otimização Temática (SEO Orientativo)\n\n"
    "### Avaliação Crítica dos Textos Preliminares\n"
    "- **Gancho do Instagram:** O gancho inicial funciona bem, mas pode ser tornado ainda mais envolvente ao conectar diretamente a sensação de pausa com os aromas do café artesanal fresco.\n"
    "- **Naturalidade do WhatsApp:** A redação é amigável e conversacional, porém a chamada para ação precisa de um fechamento ainda mais convidativo e conciso para facilitar a leitura rápida em dispositivos móveis.\n"
    "- **Estrutura do E-mail Marketing:** A estrutura narrativa é clara; recomenda-se intensificar a proposta de valor sensorial (café quente aromático vs. bebidas geladas para o calor de Fortaleza) e destacar o convite visualmente.\n"
    "- **Coerência de Marca:** Todas as peças mantêm fidelidade total ao tom acolhedor e evitam promessas exageradas, respeitando as diretrizes éticas e de compliance.\n\n"
    "### Palavras-Chave e Otimização Temática (SEO)\n"
    "- *Termos Principais:* `cafés especiais fortaleza`, `cafeteria artesanal`, `pausa especial`, `bebidas geladas café`, `café aconchegante fortaleza`.\n"
    "- *Diretriz de Aplicação:* Integrar os termos de forma orgânica nas legendas, assuntos de e-mail e comunicações digitais para ampliar a relevância temática de busca local sem canibalização de texto.\n\n"
    "---\n\n"
    "## 2. Versões Finais Corrigidas dos Conteúdos\n\n"
    "### 📸 Canal: Instagram (Feed / Stories — Versão Final Lapidada)\n\n"
    "**Gancho (Hook):**\n"
    "O aroma do café acabado de moer tem o poder de transformar qualquer dia comum em um momento inesquecível.\n\n"
    "**Legenda Revisada:**\n"
    "Em meio à agitação de Fortaleza, você merece um instante só seu. "
    "No Café Aurora, cada xícara é uma celebração ao artesanato: grãos especiais selecionados, preparo cuidadoso na hora "
    "e bebidas quentes e geladas pensadas para o seu momento de respirar fundo. "
    "Seja para um encontro acolhedor, uma leitura tranquila ou simplesmente para saborear um cappuccino impecável, "
    "o nosso espaço foi criado para ser a sua pausa de acolhimento.\n\n"
    "**Chamada para Ação (CTA):**\n"
    "Dê uma pausa no seu dia: visite o Café Aurora e descubra o sabor de momentos feitos com afeto.\n\n"
    "**Hashtags Temáticas:**\n"
    "#CafeAurora #CafesEspeciaisFortaleza #CafeteriaArtesanal #PausaEspecial #MomentosDeAconchego #CafeArtesanal\n\n"
    "---\n\n"
    "### 💬 Canal: WhatsApp (Mensagem Direta — Versão Final Lapidada)\n\n"
    "**Mensagem Revisada:**\n"
    "Olá! Esperamos que sua semana esteja caminhando bem por aí. ☕\n\n"
    "Com tantas tarefas na rotina em Fortaleza, às vezes tudo o que precisamos é de alguns minutos para desacelerar "
    "e desfrutar de um bom café preparado com calma. "
    "Por isso, queremos te convidar para conhecer o Café Aurora: um cantinho confortável feito para quem aprecia "
    "cafés artesanais de verdade, cappuccinos cremosos e opções geladas deliciosas feitas na hora.\n\n"
    "**Chamada para Ação (CTA):**\n"
    "Venha viver a sua pausa especial: visite o Café Aurora hoje mesmo e sinta-se em casa!\n\n"
    "---\n\n"
    "### ✉️ Canal: E-mail marketing (Versão Final Lapidada)\n\n"
    "**Assunto:** Sua pausa especial tem aroma de café fresco em Fortaleza ☕\n"
    "**Pre-header:** Descubra cafés artesanais, bebidas geladas autorais e um refúgio acolhedor feito para você.\n\n"
    "**Saudação:** Olá,\n\n"
    "**Corpo do E-mail Revisado:**\n"
    "Quantas vezes nesta semana você conseguiu realmente parar por dez minutos para saborear uma conversa ou uma bebida com tranquilidade?\n\n"
    "No ritmo intenso da nossa rotina, momentos de pausa não são luxo — são um cuidado essencial com o nosso bem-estar. "
    "Foi pensando nisso que criamos o **Café Aurora**, uma cafeteria que valoriza o tempo, o afeto e a riqueza dos grãos selecionados.\n\n"
    "Aqui em Fortaleza, preparamos cada bebida artesanalmente no momento em que você pede: desde o clássico espresso equilibrado "
    "e o cappuccino aveludado até cafés gelados refrescantes que harmonizam perfeitamente com os nossos acompanhamentos frescos.\n\n"
    "Seja para encontrar amigos, colocar a leitura em dia ou simplesmente recarregar as energias, o nosso ambiente aconchegante "
    "está pronto para receber você com toda a atenção que você merece.\n\n"
    "**Chamada para Ação (CTA):**\n"
    "Permita-se essa experiência: visite o Café Aurora e transforme a sua pausa em um momento especial.\n\n"
    "**Encerramento:**\n"
    "Com atenção e café fresco preparado na hora,\n"
    "Equipe Café Aurora — Fortaleza, CE\n\n"
    "> **Aviso Importante:** Conteúdo gerado com inteligência artificial, de caráter orientativo e sujeito a revisão humana prévia."
)

# ==============================================================================
# 6. AGENTE 4 — DESIGNER DE PROMPTS DE IMAGEM
# ==============================================================================

DEMO_IMAGE_PROMPTS: str = (
    "## Guia de Conceito Visual e Direção de Arte\n"
    "- **Conceito Visual Geral:** Estética acolhedora, contemporânea e luminosa (Warm Natural Daylight). "
    "A atmosfera enfatiza a textura artesanal da cerâmica, a crema dourada do café, a madeira clara do mobiliário "
    "e plantas naturais, transmitindo refúgio, frescor e hospitalidade.\n"
    "- **Paleta de Cores:** Tons terrosos suaves (café tostado, terracota, bege linho), verde botânico e toques dourados da luz natural da manhã.\n\n"
    "---\n\n"
    "### 1. Peça Publicitária — Instagram (Feed Quadrado)\n"
    "- **Canal:** Instagram\n"
    "- **Objetivo:** Destacar a bebida artesanal e o ambiente acolhedor, gerando identificação estética e desejo de visita.\n"
    "- **Conceito Visual:** Close-up elegante de uma xícara de cappuccino com latte art delicado sobre mesa de madeira rústica, iluminada por suave luz solar lateral.\n"
    "- **Formato / Aspect Ratio:** 1:1 (quadrado para feed de Instagram)\n"
    "- **Prompt Otimizado para Instagram (Midjourney / DALL-E / Flux):**\n"
    "```text\n"
    "prompt: A professional artisanal coffee photograph, top-angled close-up of a handmade ceramic cup filled with creamy cappuccino featuring intricate latte art, placed on a light oak wooden cafe table beside a small open notebook and fresh eucalyptus leaves. Soft natural morning sunlight streaming from a nearby window, shallow depth of field, warm cozy coffeehouse atmosphere, photorealistic, cinematic lighting, 8k resolution, shot on 85mm lens f/1.8 --ar 1:1 --v 6.0\n"
    "```\n"
    "- **Orientações de Composição (Português):** Manter o foco nítido na xícara de cappuccino e no desenho do latte art. O fundo deve estar suavemente desfocado, sugerindo um ambiente de cafeteria moderno e aconchegante.\n"
    "- **Elementos a Evitar (Negative Prompt):** Evitar cores néon artificiais, logotipos ilegíveis de marcas reais, aspecto plástico, superexposição e ambientes escuros ou frios.\n\n"
    "---\n\n"
    "### 2. Peça Visual Convidativa — WhatsApp (Stories / Compartilhamento Vertical)\n"
    "- **Canal:** WhatsApp\n"
    "- **Objetivo:** Apresentar a opção de bebida gelada refrescante com apelo direto e acolhedor para compartilhamento em dispositivos móveis.\n"
    "- **Conceito Visual:** Copo de vidro transparente com café gelado autoral (cold brew com camadas de leite e gelo cristalino), transmitindo frescor e vivacidade.\n"
    "- **Formato / Aspect Ratio:** 9:16 (vertical para status e mensagens de WhatsApp)\n"
    "- **Prompt Otimizado para WhatsApp (Midjourney / DALL-E / Flux):**\n"
    "```text\n"
    "prompt: Commercial food photography of a refreshing iced artisan coffee drink in a tall clear ribbed glass with crystal clear ice cubes and swirling cream layers, sitting on a sunlit cafe counter near green potted plants. Bright airy coastal cafe vibe, gentle condensation on the glass surface, bright natural daylight, highly detailed, realistic textures, vibrant refreshing mood --ar 9:16 --style raw --v 6.0\n"
    "```\n"
    "- **Orientações de Composição (Português):** O copo deve estar centralizado na porção média-inferior para permitir leitura limpa em tela cheia de smartphones. O contraste entre o café escuro e o leite confere sofisticação visual.\n"
    "- **Elementos a Evitar (Negative Prompt):** Não incluir dedos deformados, copos plásticos descartáveis, excesso de saturação ou tipografia embutida na imagem.\n\n"
    "---\n\n"
    "### 3. Banner Horizontal — E-mail Marketing (Cabeçalho)\n"
    "- **Canal:** E-mail marketing\n"
    "- **Objetivo:** Servir como cabeçalho visual convidativo (hero banner) para o e-mail da campanha 'Sua Pausa Especial'.\n"
    "- **Conceito Visual:** Vista panorâmica da bancada artesanal do café com xícaras, grãos selecionados e uma janela ampla com luz natural, transmitindo sensação de boas-vindas.\n"
    "- **Formato / Aspect Ratio:** 16:9 (horizontal para cabeçalho de e-mail marketing)\n"
    "- **Prompt Otimizado para E-mail (Midjourney / DALL-E / Flux):**\n"
    "```text\n"
    "prompt: Wide banner hero shot of a cozy artisan coffee bar interior, featuring freshly brewed espresso cups, a wooden counter with glass jars of whole roasted coffee beans, clean minimalist interior design with warm lighting and lush indoor botanicals in the background. Spacious composition with negative space for marketing banners, premium editorial cafe atmosphere, 8k resolution, photorealistic --ar 16:9 --v 6.0\n"
    "```\n"
    "- **Orientações de Composição (Português):** Composição ampla e equilibrada, preservando espaço visual harmônico à esquerda ou centro para não poluir o layout do e-mail.\n"
    "- **Elementos a Evitar (Negative Prompt):** Evitar aglomeração excessiva de objetos, ruído visual, iluminação hospitalar fria ou artefatos de IA desproporcionais."
)

# ==============================================================================
# 7. FUNÇÕES DE ACESSO E VALIDAÇÃO LOCAL DE CONFORMIDADE
# ==============================================================================

def get_demo_form_data() -> dict[str, Any]:
    """Retorna os dados de briefing da campanha fictícia do Café Aurora."""
    return dict(DEMO_FORM_DATA)


def get_demo_research_data() -> dict[str, Any]:
    """Retorna os dados de pesquisa ilustrativa (sem consulta externa)."""
    return dict(DEMO_RESEARCH_DATA)


def get_demo_strategist_output() -> str:
    """Retorna o plano estratégico do Agente 1."""
    return DEMO_STRATEGY


def get_demo_copywriter_output() -> str:
    """Retorna a redação publicitária preliminar do Agente 2."""
    return DEMO_PRELIMINARY_COPY


def get_demo_reviewer_output() -> str:
    """Retorna o diagnóstico e as versões finais do Agente 3."""
    return DEMO_REVIEWER_AND_FINAL


def get_demo_image_designer_output() -> str:
    """Retorna a direção visual e os prompts de imagem do Agente 4."""
    return DEMO_IMAGE_PROMPTS


def get_demo_campaign_data() -> dict[str, Any]:
    """Retorna o dicionario estruturado integral da campanha de demonstracao."""
    campaign_dict = {
        "form_data": dict(DEMO_FORM_DATA),
        "research_data": dict(DEMO_RESEARCH_DATA),
        "strategy": DEMO_STRATEGY,
        "preliminary_copy": DEMO_PRELIMINARY_COPY,
        "review_and_final": DEMO_REVIEWER_AND_FINAL,
        "image_prompts": DEMO_IMAGE_PROMPTS,
        "is_complete": True,
        "is_demo": True
    }

    # Validação determinística local oficial dos guardrails
    campaign_dict["guardrails_result"] = validate_campaign_guardrails(
        campaign_data=campaign_dict,
        report_markdown=DEMO_STRATEGY + "\n\n" + DEMO_REVIEWER_AND_FINAL
    )
    return campaign_dict


# ==============================================================================
# 8. GERADOR DE RELATÓRIOS OFFLINE (MARKDOWN E TXT)
# ==============================================================================

def build_demo_campaign_reports(campaign_data: Optional[dict[str, Any]] = None) -> tuple[str, str]:
    """
    Gera relatorios de demonstracao em Markdown (.md) e Texto (.txt).
    Inclui identificacao explicita no topo:
    'DEMONSTRAÇÃO — CAMPANHA FICTÍCIA — RESULTADOS PRÉ-CARREGADOS'
    """
    data = campaign_data or get_demo_campaign_data()
    form = data.get("form_data", DEMO_FORM_DATA)
    research = data.get("research_data", DEMO_RESEARCH_DATA)
    strategy = data.get("strategy", DEMO_STRATEGY)
    copy = data.get("preliminary_copy", DEMO_PRELIMINARY_COPY)
    review = data.get("review_and_final", DEMO_REVIEWER_AND_FINAL)
    images = data.get("image_prompts", DEMO_IMAGE_PROMPTS)
    guardrails = data.get("guardrails_result") or validate_campaign_guardrails(campaign_data=data)

    now_str = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M")
    product_name = form.get("product_name", "Café Aurora")

    # 1. Relatorio Markdown
    md_lines = [
        "DEMONSTRAÇÃO — CAMPANHA FICTÍCIA — RESULTADOS PRÉ-CARREGADOS",
        f"# RELATÓRIO DE CAMPANHA DE MARKETING (MODO DEMONSTRAÇÃO) — {product_name.upper()}",
        f"*Data de geração: {now_str}*",
        "",
        "> ℹ️ **AVISO DE DEMONSTRAÇÃO:** Este relatório foi gerado no **Modo Demonstração Offline** do MarketFlow AI 2.0. "
        "Todos os dados da empresa, produtos, pesquisas de tendências e textos são estritamente fictícios e pré-carregados para fins acadêmicos. "
        "Nenhuma chamada a APIs externas (OpenRouter, Tavily Search API ou n8n) foi realizada nesta simulação.",
        "",
        "---",
        "## 1. DADOS DE CONTEXTO E BRIEFING FICTÍCIO",
        f"- **Produto/Serviço:** {form.get('product_name', '')}",
        f"- **Descrição:** {form.get('product_description', '')}",
        f"- **Público-Alvo:** {form.get('target_audience', '')}",
        f"- **Objetivo da Campanha:** {form.get('objective', '')}",
        f"- **Tom de Comunicação:** {form.get('tone', '')}",
        f"- **Diferenciais Informados:** {form.get('differentials', '')}",
        f"- **Chamada para Ação (CTA):** {form.get('cta', '')}",
        f"- **Canais Selecionados:** {', '.join(form.get('channels', []))}",
        "",
        "---",
        "## 2. FONTES DE PESQUISA E TENDÊNCIAS ILUSTRATIVAS",
        "> *Pesquisa ilustrativa — Modo Demonstração. Nenhuma consulta externa foi realizada.*",
        f"- **Consulta Conceitual de Referência:** `{research.get('query', '')}`",
        f"- **Total de Exemplos Ilustrativos:** {len(research.get('results', []))}",
        ""
    ]

    for idx, item in enumerate(research.get("results", []), 1):
        md_lines.append(f"{idx}. **{item.get('title')}**")
        md_lines.append(f"   - *Descrição ilustrativa:* {item.get('content')}")
        md_lines.append("")

    md_lines.extend([
        "---",
        "## 3. ESTRATÉGIA DE MARKETING (AGENTE 1 — ESTRATEGISTA)",
        strategy,
        "",
        "---",
        "## 4. TEXTOS PRELIMINARES POR CANAL (AGENTE 2 — COPYWRITER)",
        copy,
        "",
        "---",
        "## 5. REVISÃO CRÍTICA, SEO E VERSÃO FINAL (AGENTE 3 — REVISOR)",
        review,
        "",
        "---",
        "## 6. DIREÇÃO VISUAL E PROMPTS DE IMAGEM (AGENTE 4 — DESIGNER DE PROMPTS)",
        images,
        "",
        "---",
        "## 7. RESULTADO DA VALIDAÇÃO DOS GUARDRAILS DETERMINÍSTICOS",
        f"- **Status de Conformidade:** {guardrails.get('status', 'approved').upper()}",
        f"- **Índice de Pontuação:** {guardrails.get('score', 100)}/100",
        f"- **Bloqueio de Envio:** {'Sim' if guardrails.get('is_blocked') else 'Não (Aprovado)'}",
        f"- **Origem da Validação:** Verificação determinística local de consistência, sem consumo de LLM externa.",
        "- **Itens Verificados e Aprovados:**",
    ])

    for chk in guardrails.get("passed_checks", []):
        chk_display = str(chk).replace("lucro garantido", "ganhos irreais").replace("retorno financeiro", "promessas irreais")
        md_lines.append(f"  - ✓ {chk_display}")

    md_lines.extend([
        "",
        "---",
        "## 8. AVISO ÉTICO E LEGAL",
        "> **AVISO IMPORTANTE:** Os conteúdos deste relatório pertencem a um projeto educacional e acadêmico. "
        "A empresa 'Café Aurora' e suas respectivas comunicações são obras puramente ilustrativas criadas para demonstrar "
        "a arquitetura do estúdio de campanhas com agentes generativos e guardrails.",
        ""
    ])

    report_md = "\n".join(md_lines)

    # 2. Relatorio Texto (.txt)
    txt_lines = [
        "DEMONSTRAÇÃO — CAMPANHA FICTÍCIA — RESULTADOS PRÉ-CARREGADOS",
        "=" * 70,
        f"RELATÓRIO DE CAMPANHA DE MARKETING (MODO DEMONSTRAÇÃO) — {product_name.upper()}",
        f"Data de geração: {now_str}",
        "=" * 70,
        "",
        "AVISO DE DEMONSTRAÇÃO:",
        "Este material foi gerado no Modo Demonstração Offline do MarketFlow AI 2.0.",
        "Dados fictícios pré-carregados para demonstração acadêmica sem consumo de APIs.",
        "",
        "-" * 70,
        "[1. DADOS DE CONTEXTO E BRIEFING FICTÍCIO]",
        "-" * 70,
        f"Produto/Serviço: {form.get('product_name', '')}",
        f"Descrição: {form.get('product_description', '')}",
        f"Público-Alvo: {form.get('target_audience', '')}",
        f"Objetivo da Campanha: {form.get('objective', '')}",
        f"Tom de Comunicação: {form.get('tone', '')}",
        f"Diferenciais: {form.get('differentials', '')}",
        f"CTA Desejada: {form.get('cta', '')}",
        f"Canais: {', '.join(form.get('channels', []))}",
        "",
        "-" * 70,
        "[2. PESQUISA E TENDÊNCIAS ILUSTRATIVAS (MODO DEMONSTRAÇÃO)]",
        "-" * 70,
        "Pesquisa ilustrativa — Nenhuma consulta externa foi realizada.",
        f"Consulta Conceitual: {research.get('query', '')}",
        "",
        "-" * 70,
        "[3. ESTRATÉGIA DE MARKETING (AGENTE 1 — ESTRATEGISTA)]",
        "-" * 70,
        strategy,
        "",
        "-" * 70,
        "[4. TEXTOS PRELIMINARES POR CANAL (AGENTE 2 — COPYWRITER)]",
        "-" * 70,
        copy,
        "",
        "-" * 70,
        "[5. REVISÃO CRÍTICA, SEO E VERSÃO FINAL (AGENTE 3 — REVISOR)]",
        "-" * 70,
        review,
        "",
        "-" * 70,
        "[6. DIREÇÃO VISUAL E PROMPTS DE IMAGEM (AGENTE 4 — DESIGNER DE PROMPTS)]",
        "-" * 70,
        images,
        "",
        "-" * 70,
        "[7. VALIDAÇÃO LOCAL DOS GUARDRAILS]",
        "-" * 70,
        f"Status: {guardrails.get('status', 'approved').upper()}",
        f"Índice: {guardrails.get('score', 100)}/100",
        f"Bloqueio: {'Sim' if guardrails.get('is_blocked') else 'Não (Aprovado)'}",
        "",
        "=" * 70,
        "[8. AVISO ÉTICO E LEGAL]",
        "=" * 70,
        "Conteúdo de demonstração acadêmica e educacional. Empresa puramente fictícia.",
        "=" * 70,
    ]
    report_txt = "\n".join(txt_lines)

    return report_md, report_txt


# ==============================================================================
# 9. EXECUÇÃO DA SIMULAÇÃO DIDÁTICA DO WORKFLOW
# ==============================================================================

def run_demo_workflow_simulation(
    progress_callback: Optional[Callable[[str, str, str, Any], None]] = None
) -> dict[str, Any]:
    """
    Executa a simulacao visual dos quatro agentes utilizando os dados ficticios pre-carregados.
    Nao faz requisicoes de rede e dispara callbacks didaticos para a interface Streamlit.
    """
    campaign_data = get_demo_campaign_data()

    if progress_callback:
        # Etapa 1: Briefing
        progress_callback("briefing", "completed", "Briefing fictício do Café Aurora carregado.")

        # Etapa 2: Pesquisa Ilustrativa
        progress_callback(
            "research",
            "completed",
            "Exemplo do Pesquisador carregado (pesquisa ilustrativa — nenhuma consulta externa realizada).",
            campaign_data["research_data"]
        )

        # Etapa 3: Agente 1 - Estrategista
        progress_callback(
            "strategist",
            "completed",
            "Exemplo do Agente 1 carregado (Plano Estratégico e Posicionamento).",
            campaign_data["strategy"]
        )

        # Etapa 4: Agente 2 - Copywriter
        progress_callback(
            "copywriter",
            "completed",
            "Exemplo do Agente 2 carregado (Redação preliminar para Instagram, WhatsApp e E-mail).",
            campaign_data["preliminary_copy"]
        )

        # Etapa 5: Agente 3 - Revisor
        progress_callback(
            "reviewer",
            "completed",
            "Exemplo do Agente 3 carregado (Diagnóstico crítico, SEO e Versões Finais completas).",
            campaign_data["review_and_final"]
        )

        # Etapa 6: Agente 4 - Designer de Imagem
        progress_callback(
            "image_designer",
            "completed",
            "Exemplo do Agente 4 carregado (Direção de arte e 3 prompts em inglês).",
            campaign_data["image_prompts"]
        )

        # Etapa 7: Guardrails e Campanha Pronta
        progress_callback(
            "ready",
            "completed",
            "Demonstração concluída: validação determinística de guardrails aprovada com êxito.",
            campaign_data["guardrails_result"]
        )

    return campaign_data


# ==============================================================================
# 10. BLOQUEIO DE AUTOMAÇÃO EXTERNA
# ==============================================================================

def block_demo_automation() -> dict[str, Any]:
    """
    Bloqueio seguro para impedir disparos acidentais ao n8n, Gmail ou Google Sheets
    durante o Modo Demonstracao.
    """
    return {
        "success": False,
        "uncertain": False,
        "is_blocked_by_demo": True,
        "message": (
            "Operação bloqueada com segurança: No Modo Demonstração, os envios externos ao n8n, "
            "ao Gmail e ao Google Sheets estão desativados."
        )
    }
