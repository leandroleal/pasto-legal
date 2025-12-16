from agno.playground import Playground, serve_playground_app
from teams.multi_language_team import multi_language_team
from dotenv import load_dotenv

load_dotenv()

playground_app = Playground(
    teams=[multi_language_team],
    name="Flora MapBiomas Assistant",
    description="A playground for MapBiomas data exploration",
    app_id="flora-playground",
).get_app()

if __name__ == "__main__":
    serve_playground_app("app.playground_server:playground_app", reload=True)