from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.manager import MemoryManager
from agno.models.google import Gemini
from agno.tools.csv_toolkit import CsvTools
from agno.storage.sqlite import SqliteStorage
from agno.memory.v2 import Memory
import os
import binascii



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