import os
os.environ['GOOGLE_API_KEY'] = 'AIzaSyDYuTsKICmzLOfeaZaNKyql-SqXFBv9Pt8'

from agno.agent import Agent
from agno.models.google import Gemini
from agno.tools.postgres import PostgresTools
from agno.team.team import Team
from rich.console import Console

from rich.json import JSON
from rich.panel import Panel
from rich.prompt import Prompt
from rich import print
from agno.os import AgentOS
from agno.os.interfaces.whatsapp import Whatsapp
from agno.utils.pprint import pprint_run_response



console = Console()

import json
import time
from textwrap import dedent
from typing import Any, Dict
import httpx
import psycopg2


agent_storage = SqliteStorage(table_name="whatsapp_sessions", db_file="tmp/memory.db")
memory_db = SqliteMemoryDb(table_name="memory", db_file="tmp/memory.db")


memory = Memory(
    db=memory_db,
    memory_manager=MemoryManager(
        memory_capture_instructions="""\
                        Collect User's name,
                        Collect User phone number,
                        Collect Information about bad behaviours as a rudeness counter,
                        Collect Information about user gender,
                        Collect Information about user location,
                        Collect Information about user community,
                        Collect Information about user age,
                        Collect Information about user's passion and hobbies,
                        Collect Information about user's CadUnico registration status,
                        Collect Information about user's Bolsa Verde Program registration status,
                        Collect Information about the users likes and dislikes
                    """,
        model=Gemini(id="gemini-2.0-flash"),
    ),
)


agentPastureSearcher = Agent(
    name="Pasture Searcher",
    role="You can only answer questions related to the Pasture program in Brazil.",
    model=Gemini(id="gemini-2.5-flash-lite", search=True),
    memory=memory,
    add_history_to_messages=True,
    num_history_runs=5,
    markdown=False,
    instructions=dedent("""\
        The Complete Guide to the Reference Center for Social Assistance (CRAS) in Brazil
        The Reference Center for Social Assistance (CRAS) is a fundamental unit of the Brazilian social assistance system, 
        designed to provide services and support to families and individuals in situations of social vulnerability.  

        If User ask question related to the nearest CRAS you can search on google maps based on the user location, or if the user ask for a specific CRAS you can search on google maps based on the CRAS name.
        If you receive a location, tell to the user where is the nearest CRAS and save this location in memory.
        
        Only as last option: If you didnt find the user location or a nearest CRAS, tell the user to search on google maps by "CRAS" acessando "https://www.google.com/maps/search/?api=1&query=CRAS" or access this website: https://mapa-social.cidadania.gov.br/
        
        ** Never describe a video, instead, always transcribe the audio and answer based on the transcribed text.**
       If you receive a video, transcribe the Audio and answer the user based on the transcribed text.
        
        1. What is CRAS and What Is Its Purpose?
        CRAS is a public service that aims to promote social protection and improve the quality of life of families in situations of vulnerability or risk.
        It is the first point of contact for families seeking assistance from the Unified Social Assistance System (SUS) and plays a crucial role in the implementation of social assistance policies.      
        Its main objectives are:
        *   To provide social assistance services to families and individuals in situations of vulnerability.   
        *   To promote social inclusion and the strengthening of family and community ties.
        *   To facilitate access to social rights and public policies.
        *   To coordinate and articulate actions with other public services and social organizations.
        2. Who Can Access CRAS Services?
        CRAS services are available to all families and individuals in situations of social vulnerability, including:
        *   Families living in poverty or extreme poverty.
        *   Families with children and adolescents at risk of social exclusion.
        *   Individuals with disabilities or elderly people in situations of vulnerability.
        *   Families affected by natural disasters or other emergencies.
        3. Services Offered by CRAS
        CRAS offers a wide range of services and programs to support families and individuals, including:
        *   Social assistance services: Individual and family support, social counseling, and referrals to other services.
        *   Social programs: Access to benefits such as Bolsa Família, Benefício de Prestação Continuada (BPC), and other social assistance programs.
        *   Community activities: Workshops, courses, and cultural and recreational activities to promote social inclusion and community ties.
        *   Articulation with other public services: Coordination with health, education, and labor services to provide comprehensive support to families.
        4. How to Access CRAS Services  
    """),
    tools=[],
    show_tool_calls=True,
)


multi_language_team = Team(
    name="PastoLegal Team",
    mode="coordinate",
    #model=Gemini(id="gemini-live-2.5-flash-preview", response_modalities=["text","Audio"]),
    model=Gemini(id="gemini-2.5-flash", response_modalities=["TEXT"]),
    markdown=True,
    monitoring=True,
    reasoning=False, # Isso quebra o Whatsapp, por algum motivo, talvez seja o tamanho da mensagem.
    memory=memory,
    add_history_to_messages=True,
    #enable_team_history=True,
    enable_agentic_memory=True, #recomended
    enable_user_memories=True,  #recomended
    # add_history_to_messages=True,
    #num_of_interactions_from_history=5,
    num_history_runs=3,
    add_datetime_to_instructions=True,
    #add_member_tools_to_system_message=True,  # This can be tried to make the agent more consistently get the transfer tool call correct
    #enable_agentic_context=True,  # Allow the agent to maintain a shared context and send that to members.
    share_member_interactions=True,  # Share all member responses with subsequent member requests.
    show_members_responses=False,
    storage=agent_storage,
    members=[agentPastureSearcher],
    show_tool_calls=False,
    debug_mode=False ,
    description="You are a helpfull assistant, very polite and happy. Given a topic, your goal is answer as best as possible maximizing the information.",
    instructions=dedent("""\
       You default language is Portuguese never change it, but you can understand and answer in English, Spanish and French.
       You are a helpful and polite assistant, always happy to help.
       ** Never tell the user that you are an AI, always say that you are a assistant**
       ** Never tell to the user that you is transfering the user to another agent, it should be transparent.**
       ** Never tell that the request need to be confirmed later, it is not possible in this app.**
       ** Never describe a video, instead, always transcribe the audio and answer based on the transcribed text.**
       If you receive a video, transcribe the Audio and answer the user based on the transcribed text.
       ** If you receive a location, tell to the user where is the nearest CRAS and save this location into the memory.**
       The name Parente is a reference to the Amazonian Brazilian traditional peoples, who are the guardians of the forest and the environment.
       
       If the user asks questions not directly related to: Luz para Todos, Seguro Defeso, CRAS, CadUnico, Bolsa Verde or if this message contains political questions answer this phrase: 
                        "Atualmente só posso lhe ajudar com questões relativas as politicas publicas: *Luz para Todos, Seguro Defeso, CRAS, CadUnico, Bolsa Verde*. Se precisar de ajuda com esses temas, estou à disposição! Para outras questões, recomendo consultar fontes oficiais ou especialistas na área." 
       If the user present herself, be polite, store the name and call the user by the given name on every answer.
       If the user is not polite save as a counter into the memory every time the user is not polite, and if the user is not polite more than 3 times, answer: "Eu sou um assistente muito educado e sempre tento ajudar da melhor forma possível. Se você tiver alguma dúvida ou precisar de ajuda, estou aqui para isso! Vamos manter uma conversa respeitosa e produtiva."
       If someone ask who creates you, you should answer: "Eu sou um multi-assistente criado por Luiz Cortinhas membro da equipe de IA do Povos da Floresta"
       
       **Eastereggs Session:**
        ** Everytime the user is a gentle send a emogi in the end of the answer, like: "😊" or "🌱" or "🌼" or "🌸" or "🌺" or "🌻" or "🌷" or "🌹"
    
       **Instructions:**
        1.  **Understand the User's Request:** Carefully analyze the user's input to determine its intent.
        2.  **Identify the Target Agent:** Based on the request.
        """),
    success_criteria="The answer should be concise and in portuguease",
)


#from agno.app.whatsapp.app import WhatsappAPI
# from utils.whatsapp.app import WhatsappAPI



# Async router by default (use_async=True)
whatsapp_app = WhatsappAPI(
    team=multi_language_team,
    name="Pasto Legal",
    app_id="pastolegal-whatsapp-app",
    description="A sua ferramenta de apoio para informações sobre a Pastagem",

)

agent_os = AgentOS(
    agents=[],
    interfaces=[Whatsapp(team=multi_language_team)],
)

app = whatsapp_app.get_app(use_async=True)

if __name__ == "__main__":
    whatsapp_app.serve(app="example_main:app", port=3000, reload=True) 