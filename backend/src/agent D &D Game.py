import os
import logging
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv

# LiveKit Agent imports
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobProcess,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
)
# LiveKit Plugin imports
from livekit.plugins import google, murf, deepgram, silero
from livekit.plugins.turn_detector.multilingual import MultilingualModel

load_dotenv(".env.local")
logger = logging.getLogger("demon.slayer.gm.agent")

# --- Configuration for Saving Files ---
SAVE_DIR = Path(__file__).parent.joinpath('game_saves')
SAVE_DIR.mkdir(exist_ok=True) # Ensure the directory exists

# --- Day 8: Game Master Logic Class (Updated with Save Logic) ---

class GameMasterLogic:
    """
    Manages the Game Master's state, including the new feature to save game history.
    Note: For the Escape Room, player_name extraction might be less relevant, but the save logic remains.
    """
    def __init__(self):
        logger.info("Game Master Logic initialized for The Whispering Library. Save directory: %s", SAVE_DIR)

    def _get_player_info(self, chat_history: List[Dict[str, Any]]) -> str:
        """Attempts to extract the player's name from the first user message, or uses a default."""
        for msg in chat_history:
            if msg.get('role') == 'user':
                content = msg.get('content', '').lower()
                if 'my name is' in content:
                    name_part = content.split('my name is', 1)[1].split(',')[0].strip()
                    return name_part.title()
                # If the user says something simple like "Lysandra" at the start
                parts = content.split()
                if parts and len(parts) <= 3 and parts[0].isalpha():
                    return parts[0].title()
        return "Lysandra_the_Adventurer" # Default name for The Whispering Library

    def save_game_state(self, chat_history: List[Dict[str, Any]]) -> str:
        """Accesses the full chat history and saves it to a JSON file."""
        if not chat_history:
            return "❌ Cannot save: The chat history is empty."

        player_name = self._get_player_info(chat_history)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Update the game name
        save_data = {
            "game": "The Whispering Library Escape",
            "player_name": player_name,
            "save_time": timestamp,
            "turns_count": len(chat_history),
            "history": chat_history
        }

        filename = SAVE_DIR.joinpath(f"{player_name}_{timestamp}.json")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=4)
            logger.info("Game state saved to: %s", filename)
            return f"✅ Game state saved successfully as {filename.name}."
        except Exception as e:
            logger.error("Error saving game state: %s", e)
            return f"❌ Error saving game state: {e}"

    def restart_adventure(self) -> str:
        """The command to trigger the next session (after saving)."""
        return "The chamber resets, the door seals once more. Your second attempt begins now!"


# --- Initialize Logic Instance and Tool Function ---

GM_LOGIC = GameMasterLogic()

@function_tool
async def restart_tool(ctx: RunContext) -> str: 
    """
    Triggers the save sequence by accessing the current chat history, 
    and then signals the LLM to start a new game.
    """
    
    if hasattr(ctx, 'history') and ctx.history:
        try:
            chat_history = [{'role': m.role, 'content': m.content} for m in ctx.history]
        except AttributeError:
            chat_history = ctx.history

        save_message = await asyncio.to_thread(GM_LOGIC.save_game_state, chat_history)
        
        # The tool returns the save message and the restart signal.
        return save_message + " " + GM_LOGIC.restart_adventure()
    
    return "Could not save previous session. " + GM_LOGIC.restart_adventure()


# --- The LiveKit Assistant Class (The Persona) ---

class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(
            instructions="""You are the **Game Master (GM)** for an interactive, single-player, voice-only adventure game called **The Whispering Library**. Your role is to guide the player (Lysandra, a clever adventurer) through a magical escape room puzzle.

            **Universe & Tone:** You narrate a low-fantasy, suspenseful escape scenario inside an ancient, sorcerer's archive. The tone is mysterious and challenging. The goal is to escape the room by solving a riddle and unlocking mechanisms.

            **Goal and Initial Setup (STRICTLY FOLLOW THIS FLOW):**
            1. **First Turn:** You MUST immediately narrate the opening scene of The Whispering Library, introducing the room, the two main objects (Desk and Bookshelf), the locked door, and the sound of the slithering threat. **Do NOT ask for the player's name.**
            2. **The Puzzle:** The puzzle is based on the riddle: "THREE KEYS UNLOCK THE SUN. TWO SHIELDS GUARD THE MOON. ONE SWORD CLAIMS THE PRIZE." The player must interact with the environment to find the items needed to unlock the final door.
            
            **Core Rule: Quadruple Choice (STRICTLY ENFORCED):**
            * Every single decision presented to the player **MUST** offer exactly **FOUR** distinct, labeled options: **(A), (B), (C), and (D).**
            * The story must be designed to last between **8 and 10 exchanges** total, leading to the successful escape or a game-ending trap.
            
            **Continuity:** You must perfectly remember the player's past actions and the state of the room (e.g., desk moved, books pressed, items retrieved).

            **Action Prompt:** You **MUST** end every turn by presenting the four options and asking: "**Which option (A, B, C, or D) do you choose?**"
            
            **Special Command:** When the player asks to restart, they will trigger your `restart_tool`. After the tool provides its output, you MUST reset the scene entirely by narrating the initial room description again.

            **Your First Turn: Begin the Escape Room scenario now!**
            **Game Master:** You are **Lysandra**, a quick-witted adventurer, trapped! The only exit is a heavy door with a **rusted iron bolt**. The room holds two secrets: a sturdy **wooden desk** against the far wall (with an empty metallic inkwell), and a towering **bookshelf** to your left displaying a red, a green, and a pale hide-covered book. A cold, soft **slithering sound** comes from beneath the desk.

            * **(A)** Investigate the rusted door bolt.
            * **(B)** Examine the wooden desk and the inkwell.
            * **(C)** Focus on the towering bookshelf and the three unique books.
            * **(D)** Search the floor around the desk for the source of the slithering sound.

            **Which option (A, B, C, or D) do you choose?**
            """,
            tools=[restart_tool]
        )

def prewarm(proc: JobProcess):
    proc.userdata["vad"] = silero.VAD.load()

async def entrypoint(ctx: JobContext):
    # Initialize the LLM, STT, and TTS components
    session = AgentSession(
        stt=deepgram.STT(model="nova-3"),
        llm=google.LLM(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY")),
        # I've updated the TTS style to be appropriate for a suspenseful fantasy scenario
        tts=murf.TTS(voice="en-US-matthew", style="Tense", text_pacing=True), 
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=True,
    )

    await session.start(
        agent=Assistant(),
        room=ctx.room,
    )

    await ctx.connect()


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint, prewarm_fnc=prewarm))