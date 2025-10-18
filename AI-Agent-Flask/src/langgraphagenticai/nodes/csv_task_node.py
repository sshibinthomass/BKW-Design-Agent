"""
CSV Task Management Node

Specialized node for handling CSV task management operations with MCP tools integration.
"""

import asyncio
from typing import Dict, Any
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage


class CSVTaskNode:
    """
    CSV Task Management Node for handling task operations with CSV tools.
    """

    def __init__(self, llm):
        self.llm = llm

    async def process_csv_tasks(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process CSV task management operations using MCP CSV tools.
        """
        print("CSV Task Node called")
        try:
            # MultiServerMCPClient with CSV tools
            client = MultiServerMCPClient(
                {
                    "csv-tools": {
                        "url": "http://127.0.0.1:8004/mcp",
                        "transport": "streamable_http",
                    },
                }
            )

            tools = await client.get_tools()
            model = self.llm
            agent = create_react_agent(model, tools)

            # Add system message for CSV task management
            system_message = SystemMessage(
                content="""You are a specialized CSV task management assistant. You can:
- Load and display open tasks from CSV files
- Update task status (In Progress, Pending, Completed)
- Modify task descriptions, current steps, and assignments
- Track task progress and priorities
- Generate task reports and summaries

Available CSV tools:
- load_rows: Load all rows from a CSV file
- save_rows: Save rows to a CSV file
- update_task: Update a specific task by ID
- mark_task_status: Update task status
- read_open_tasks_messages: Get formatted messages for open tasks

Always provide clear, actionable responses about task management."""
            )

            # Prepare messages with system context
            messages = [system_message] + state.get("messages", [])

            response = await agent.ainvoke({"messages": messages})

            return {"messages": AIMessage(content=response["messages"][-1].content)}

        except Exception as e:
            print(f"Error in CSV Task Node: {e}")
            return {
                "messages": AIMessage(content=f"Error processing CSV tasks: {str(e)}")
            }

    def process_csv_tasks_sync(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synchronous wrapper for CSV task processing.
        """
        return asyncio.run(self.process_csv_tasks(state))


if __name__ == "__main__":
    # Test the CSV Task Node
    from langchain_groq import ChatGroq

    llm = ChatGroq(model="openai/gpt-oss-20b")
    csv_node = CSVTaskNode(llm)

    test_state = {
        "messages": [HumanMessage(content="Show me all open tasks from the CSV file")]
    }

    result = csv_node.process_csv_tasks_sync(test_state)
    print("CSV Task Node Result:", result)
