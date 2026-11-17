# Dispatch after answer

An outbound LiveKit call where the agent is dispatched only after the callee picks up.

The usual outbound pattern dispatches the agent first and has it dial. If the agent connects to the room before dialing, LiveKit Cloud meters agent minutes for the whole ring time ([billing](https://docs.livekit.io/deploy/admin/billing/): "Metering starts after the agent connects to the room"). If it dials first and connects only after the answer, the job sits in the room without an agent while the phone rings.

This repo flips the order:

1. `dispatch_call.py` creates a fresh room and dials the number with `CreateSIPParticipant` and `wait_until_answered=True`. The call returns once the callee answers, or raises `SipCallError` if they don't.
2. Only then does it call `CreateAgentDispatch` for that room ([dispatch via API](https://docs.livekit.io/agents/server/agent-dispatch/#via-api)), passing the callee's identity as job metadata.
3. `agent.py` connects first thing in its entrypoint, finds the callee, starts the session and speaks a short opening line.

No agent minutes are metered while the phone rings. The trade-off is a short pause after the callee answers while the agent joins, so keep the opening line brief.

## Setup

```bash
uv sync
cp .env.example .env.local
```

Fill in `.env.local` with your LiveKit project credentials and an outbound trunk ID (`lk sip outbound list`).

## Run

Start the agent:

```bash
uv run agent.py dev
```

In another terminal, place a call:

```bash
uv run dispatch_call.py +15105550100
```

## Notes

- `AGENT_NAME` must match in both files.
- Unanswered calls never dispatch an agent, so they cost no agent minutes.
- Answering machines count as answered (`wait_until_answered` returns for voicemail too). Add [answering machine detection](https://docs.livekit.io/telephony/features/answering-machine-detection/) if that matters.
