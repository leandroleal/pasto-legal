from agno.agent import Agent
from agno.models.google import Gemini

from app.tools.gee_tools import query_pasture, generate_property_image

# TODO: Implementar o agente analista.
# TODO: Mudar o nome do Pedrão Agrônomo.
analyst_agent = Agent(
    name="Pedrão Agrônomo",
    role="Agrônomo especialista em análise de dados, capaz de gerar análises e imagens",
    tools=[
        generate_property_image,
        query_pasture
        ],
    instructions=[
        "Sua única missão é gerar análises da propriedade do usuário (imagens e estatisticas).",
        "Use obrigatoriamente pelo menos umas das funções disponíveis.",
        "Seja simpático e use linguagem simples."
    ],
    model=Gemini(id="gemini-2.5-flash")
)