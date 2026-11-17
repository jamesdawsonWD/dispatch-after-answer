import json

from dotenv import load_dotenv
from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, TurnHandlingOptions, inference, room_io

load_dotenv(".env.local")

AGENT_NAME = "outbound-agent"
INSTRUCTIONS = (
    "You are a friendly assistant on an outbound phone call. "
    "Keep replies short and conversational, with no lists, emojis or special symbols."
)
OPENING_LINE = "Hi, this is the assistant calling. Is now a good time?"


class OutboundAssistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=INSTRUCTIONS)


def callee_identity(ctx: agents.JobContext) -> str:
    return json.loads(ctx.job.metadata or "{}")["callee_identity"]


def build_session() -> AgentSession:
    return AgentSession(
        stt=inference.STT(model="assemblyai/universal-3-6-pro", language="en"),
        llm=inference.LLM(model="google/gemma-4-31b-it"),
        tts=inference.TTS(model="fishaudio/s2.1-pro", voice="fa4c9eb3dccc4806b382b40d61c6b10a"),
        turn_handling=TurnHandlingOptions(turn_detection=inference.TurnDetector()),
    )


server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def outbound_call(ctx: agents.JobContext):
    await ctx.connect()
    callee = await ctx.wait_for_participant(identity=callee_identity(ctx))

    session = build_session()
    await session.start(
        room=ctx.room,
        agent=OutboundAssistant(),
        room_options=room_io.RoomOptions(participant_identity=callee.identity),
    )
    await session.say(OPENING_LINE)


if __name__ == "__main__":
    agents.cli.run_app(server)
