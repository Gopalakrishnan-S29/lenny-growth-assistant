
import asyncio

from app.agents.pi_agent import PiAgent


async def main():
    agent = PiAgent()

    answer = await agent.generate(
        prompt="Reply with exactly: PI_ADAPTER_OK",
        system_prompt="Follow the user's request exactly.",
    )

    print("Pi adapter response:")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
