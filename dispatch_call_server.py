import argparse
import asyncio
import json
import logging
import os
import uuid

from dotenv import load_dotenv
from livekit import api

load_dotenv(".env.local")

logger = logging.getLogger("dispatch-call-server")

AGENT_NAME = "outbound-agent"
CALLEE_IDENTITY = "callee"


def new_room_name() -> str:
    return f"outbound-{uuid.uuid4().hex[:12]}"


async def dial_and_wait_for_answer(lkapi: api.LiveKitAPI, room_name: str, phone_number: str) -> None:
    await lkapi.sip.create_sip_participant(
        api.CreateSIPParticipantRequest(
            room_name=room_name,
            sip_trunk_id=os.environ["SIP_OUTBOUND_TRUNK_ID"],
            sip_call_to=phone_number,
            participant_identity=CALLEE_IDENTITY,
            wait_until_answered=True,
        )
    )


async def dispatch_agent(lkapi: api.LiveKitAPI, room_name: str) -> api.AgentDispatch:
    return await lkapi.agent_dispatch.create_dispatch(
        api.CreateAgentDispatchRequest(
            agent_name=AGENT_NAME,
            room=room_name,
            metadata=json.dumps({"callee_identity": CALLEE_IDENTITY}),
        )
    )


async def call(phone_number: str) -> None:
    room_name = new_room_name()
    async with api.LiveKitAPI() as lkapi:
        logger.info("dialing %s into room %s", phone_number, room_name)
        try:
            await dial_and_wait_for_answer(lkapi, room_name, phone_number)
        except api.SipCallError as error:
            logger.warning("call not answered: %s %s", error.sip_status_code, error.sip_status)
            return

        dispatch = await dispatch_agent(lkapi, room_name)
        logger.info("callee answered, dispatched agent %s (%s)", AGENT_NAME, dispatch.id)


def parse_phone_number() -> str:
    parser = argparse.ArgumentParser(description="Dial a number, then dispatch the agent once the callee answers.")
    parser.add_argument("phone_number", help="E.164 number to call, for example +15105550100")
    return parser.parse_args().phone_number


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(call(parse_phone_number()))
