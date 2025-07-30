import json
import os
import re
from typing import List

from dotenv import load_dotenv
from pydantic import BaseModel, Field
# Import from swarms - note: some imports may need adjustment based on current swarms version
try:
    from swarms import Agent, tool
    # Try to import SwarmNetwork and Anthropic - these may not be available in current version
    try:
        from swarms import SwarmNetwork
    except ImportError:
        print("Warning: SwarmNetwork not available in current swarms version")
        SwarmNetwork = None
    
    try:
        from swarms import Anthropic
    except ImportError:
        print("Warning: Anthropic not available in current swarms version")
        # Try alternative import for Anthropic
        try:
            from swarms.models import Anthropic
        except ImportError:
            print("Warning: Anthropic model not found, using placeholder")
            Anthropic = None
except ImportError as e:
    print(f"Error importing from swarms: {e}")
    Agent = None
    tool = None
    SwarmNetwork = None
    Anthropic = None

from neo_sapiens.few_shot_prompts import (
    data,
    data1,
    data2,
    data3,
    orchestrator_prompt_agent,
    select_workers,
    boss_sys_prompt,
)
from loguru import logger
from neo_sapiens.tools_preset import (
    terminal,
    browser,
    file_editor,
    create_file,
)

# Load environment variables
load_dotenv()

# Initialize SwarmNetwork only if available
if SwarmNetwork and callable(SwarmNetwork):
    network = SwarmNetwork(api_enabled=True, logging_enabled=True)
else:
    network = None
    print("Warning: SwarmNetwork not available or not callable - agent pooling disabled")


# def tool_router(tool: str, *args, **kwargs):
#     if "terminal" in tool:
#         return terminal(*args, **kwargs)
#     elif "browser" in tool:
#         return browser(*args, **kwargs)


def find_agent_id_by_name(name: str):
    """
    Find an agent's ID by its name.

    Args:
        name (str): The name of the agent.

    Returns:
        str: The ID of the agent.
    """
    if network and hasattr(network, 'agent_pool'):
        for agent in network.agent_pool:
            if agent.agent_name == name:
                return agent.id
    return None


class ToolSchema(BaseModel):
    tool: str = Field(
        ...,
        title="Tool name",
        description="Either `browser` or `terminal`",
    )


class AgentSchema(BaseModel):
    name: str = Field(
        ...,
        title="Name of the agent",
        description="Name of the agent",
    )
    system_prompt: str = (
        Field(
            ...,
            title="System prompt for the agent",
            description="System prompt for the agent",
        ),
    )
    rules: str = Field(
        ...,
        title="Rules",
        description="Rules for the agent",
    )
    # tools: List[ToolSchema] = Field(
    #     ...,
    #     title="Tools available to the agent",
    #     description="Either `browser` or `terminal`",
    # )
    # task: str = Field(
    #     ...,
    #     title="Task assigned to the agent",
    #     description="Task assigned to the agent",
    # )
    # TODO: Add more fields here such as the agent's language model, tools, etc.


class HassSchema(BaseModel):
    plan: str = Field(
        ...,
        title="Plan to solve the input problem",
        description="List of steps to solve the problem",
    )
    agents: List[AgentSchema] = Field(
        ...,
        title="List of agents to use for the problem",
        description="List of agents to use for the problem",
    )

    # Rules for the agents
    # rules: str = Field(
    #     ...,
    #     title="Rules for the agents",
    #     description="Rules for the agents",
    # )


# import json
def parse_json_from_input(input_str):
    # Validate input is not None or empty
    if not input_str:
        logger.info("Error: Input string is None or empty.")
        return None, None, None

    # Attempt to extract JSON from markdown using regular expression
    json_pattern = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
    match = json_pattern.search(input_str)
    json_str = match.group(1).strip() if match else input_str.strip()

    # Attempt to parse the JSON string
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.info(f"Error: JSON decoding failed with message '{e}'")
        return None, None, None

    hass_schema = HassSchema(**data)
    return (
        hass_schema.plan,
        hass_schema.agents,
        # hass_schema.rules,
    )


# You can test the function with a markdown string similar to the one provided.


def merge_plans_into_str(
    plan: List[str] = [data, data1, data2, data3]
) -> str:
    """
    Merge a list of plans into a single string.

    Args:
        plan (List[str]): A list of plans to be merged.

    Returns:
        str: The merged plans as a single string.
    """
    return "\n".join(plan)


# parsed_schema = parse_hass_schema(data5)
# plan, number_of_agents, agents = parsed_schema


def merge_rules_into_str(prompts: List[str]):
    """
    Merge a list of prompts into a single string.

    Args:
        prompts (List[str]): A list of prompts to be merged.

    Returns:
        str: The merged prompts as a single string.
    """
    return "\n".join(prompts)


def create_worker_agents(
    agents: List[AgentSchema],
) -> List[Agent]:
    """
    Create and initialize agents based on the provided AgentSchema objects.

    Args:
        agents (List[AgentSchema]): A list of AgentSchema objects containing agent information.

    Returns:
        List[Agent]: The initialized Agent objects.

    """
    if not Agent:
        logger.error("Agent class not available - cannot create agents")
        return []
        
    agent_list = []
    for agent in agents:
        name = agent.name
        system_prompt = agent.system_prompt

        logger.info(
            f"Creating agent: {name} with system prompt:"
            f" {system_prompt}"
        )

        # Create agent with available LLM
        llm = None
        if Anthropic:
            llm = Anthropic(
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
            )
        else:
            logger.warning("Anthropic not available - using default LLM")

        out = Agent(
            agent_name=name,
            system_prompt=system_prompt,
            llm=llm,
            max_loops=1,
            autosave=True,
            dashboard=False,
            verbose=True,
            stopping_token="<DONE>",
            tools=[browser, terminal, create_file, file_editor],
        )

        if network:
            network.add_agent(out)
        agent_list.append(out)

    return agent_list


@tool
def create_agents_by_boss(team: str = None, *args, **kwargs):
    """
    Create agents by boss.

    Args:
        team (str): The name of the team. Defaults to None.
        *args: Variable length argument list.
        **kwargs: Arbitrary keyword arguments.

    Returns:
        str: The output of the agent run.

    """
    if not Agent:
        return "Error: Agent class not available"
        
    system_prompt_daddy = orchestrator_prompt_agent(team)

    # Create agent with available LLM
    llm = None
    if Anthropic:
        llm = Anthropic(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=4000,
        )
    else:
        logger.warning("Anthropic not available - using default LLM")

    # Create the agents
    agent = Agent(
        agent_name="Swarm Orchestrator",
        system_prompt=system_prompt_daddy,
        llm=llm,
        max_loops=1,
        autosave=True,
        dashboard=False,
        verbose=True,
        stopping_token="<DONE>",
        *args,
        **kwargs,
    )

    # Run the agent and parse the output
    out = agent.run(str(team))
    return out


def print_agent_names(agents: list):
    for agent in agents:
        logger.info(f"Agent Name: {agent.agent_name}")


@tool
def send_task_to_network_agent(name: str, task: str):
    """
    Send a task to a network agent.

    Args:
        name (str): The name of the agent.
        task (str): The task to be sent to the agent.

    Returns:
        str: The response from the agent.
    """
    if not network:
        return f"Error: SwarmNetwork not available - cannot send task to {name}"
        
    logger.info(f"Adding agent {name} as a tool")
    agent_id = find_agent_id_by_name(name)
    if agent_id:
            out = network.run_single_agent(agent_id, task)
            return out
    else:
        return f"Error: Agent {name} not found in network"


def build_swarm(team_task: str, task: str, *args, **kwargs):
    """
    Master function to create agents based on a task.

    Args:
        team_task (str): The team task description.
        task (str): The task to be executed.

    Returns:
        str: The output from the swarm execution.
    """
    if not Agent:
        return "Error: Agent class not available"
        
    # Create agent with available LLM
    llm = None
    if Anthropic:
        llm = Anthropic(
            anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
            max_tokens=4000,
        )
    else:
        logger.warning("Anthropic not available - using default LLM")
    
    # Call the agents [ Main Agents ]
    boss = Agent(
        agent_name="Swarm Orchestrator",
        system_prompt=boss_sys_prompt,
        llm=llm,
        max_loops="auto",
        autosave=True,
        dashboard=False,
        verbose=True,
        interactive=True,
        stopping_token="<DONE>",
        tools=[create_agents_by_boss, send_task_to_network_agent],
        *args,
        **kwargs,
    )

    # Task 1: Run the agent and parse the output
    logger.info("Creating the workers ...")
    out = create_agents_by_boss(team_task)
    json_agentic_output = out
    # logger.info(f"Output: {out}")
    out = parse_json_from_input(out)
    if out[0] is None:  # Check if parsing failed
        return "Error: Failed to parse agent creation output"
        
    plan, agents = out

    # Task 2: Print agent names and create agents
    # logger.info(agents)
    # logger.info("Creating agents...")
    agents = create_worker_agents(agents)

    # Send JSON of agents to boss
    boss.add_message_to_memory(
        select_workers(json_agentic_output, task)
    )

    # Task 3: Now add the agents as tools -- Run the agents in a loop sequentially
    # boss.add_tool(send_task_to_network_agent)

    # Run the boss:
    out = boss.run(task)

    return out


def run_swarm(
    team_task: str = None, task: str = None, *args, **kwargs
):
    """
    Run a task using the Swarm Orchestrator agent.

    Args:
        team_task (str): The team task description. 
        task (str): The task to be executed.

    Returns:
        str: The output from the swarm execution.
    """
    if not team_task or not task:
        return "Error: Both team_task and task parameters are required"
        
    out = build_swarm(team_task, task, *args, **kwargs)
    return out
