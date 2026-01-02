from typing import Dict
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import InMemorySaver
from langchain_openai import ChatOpenAI

from config import Config
from bash import Bash

class ExecOnConfirm:
    """
    A wrapper around the Bash tool that asks for user confirmation before executing any command.
    """

    def __init__(self, bash: Bash):
        self.bash = bash

    def _confirm_execution(self, cmd: str) -> bool:
        """Ask the user whether the suggested command should be executed."""
        return input(f"    ▶️   Execute '{cmd}'? [y/N]: ").strip().lower() == "y"

    def exec_bash_command(self, cmd: str) -> Dict[str, str]:
        """Execute a bash command after confirming with the user."""
        if self._confirm_execution(cmd):
            return self.bash.exec_bash_command(cmd)
        return {"error": "The user declined the execution of this command."}

def main(config: Config):
    # Create the client
    llm = ChatOpenAI(
        model=config.llm_model_name,
        openai_api_base=config.llm_base_url,
        openai_api_key=config.llm_api_key,
        temperature=config.llm_temperature,
        top_p=config.llm_top_p,
    )
    # Create the tool
    bash = Bash(config)
    # Create the agent
    agent = create_react_agent(
        model=llm,
        tools=[ExecOnConfirm(bash).exec_bash_command],
        prompt=config.system_prompt,
        checkpointer=InMemorySaver(),
    )
    print("[INFO] Type 'quit' at any time to exit the agent loop.\n")

    # The main loop
    while True:
        user = input(f"['{bash.cwd}' 🙂] ").strip()

        if user.lower() == "quit":
            print("\n[🤖] Shutting down. Bye!\n")
            break
        if not user:
            continue

        # Always tell the agent where the current working directory is to avoid confusions.
        user += f"\n Current working directory: `{bash.cwd}`"
        print("\n[🤖] Thinking...")

        # Run the agent's logic and get the response.
        result = agent.invoke(
            {"messages": [{"role": "user", "content": user}]},
            config={"configurable": {"thread_id": "cli"}},  # one ongoing conversation
        )
        # Show the response (without the thinking part, if any)
        response = result["messages"][-1].content.strip()

        if "</think>" in response:
            response = response.split("</think>")[-1].strip()

        if response:
            print(response)
            print("-" * 80 + "\n")

if __name__ == "__main__":
    # Load the configuration
    config = Config()
    main(config)
