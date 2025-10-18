from langgraph.graph import StateGraph
from src.langgraphagenticai.state.state import State
from langgraph.graph import START, END
from src.langgraphagenticai.nodes.basic_chatbot_node import (
    BasicChatbotNode,
    RestaurantRecommendationNode,
    RAGNodes,
)
from src.langgraphagenticai.nodes.csv_task_node import CSVTaskNode

from dotenv import load_dotenv

load_dotenv()


class GraphBuilder:
    def __init__(self, model, user_controls_input, message):
        self.llm = model
        self.user_controls_input = user_controls_input
        self.message = message
        self.current_llm = user_controls_input["selected_llm"]
        self.graph_builder = StateGraph(
            State
        )  # StateGraph is a class in LangGraph that is used to build the graph

    def basic_chatbot_build_graph(self):
        """
        Builds a basic chatbot graph using LangGraph.
        This method initializes a chatbot node using the `BasicChatbotNode` class
        and integrates it into the graph. The chatbot node is set as both the
        entry and exit point of the graph.
        """
        self.basic_chatbot_node = BasicChatbotNode(self.llm)

        self.graph_builder.add_node("chatbot", self.basic_chatbot_node.process)
        self.graph_builder.add_edge(START, "chatbot")
        self.graph_builder.add_edge("chatbot", END)

    def chatbot_restaurant_recommendation(self):
        """
        Builds a chatbot graph for sushi recommendations with evaluation-based routing.
        """
        self.restaurant_recommendation_node = RestaurantRecommendationNode(self.llm)

        self.graph_builder.add_node(
            "restaurant_node", self.restaurant_recommendation_node.restaurant_node_sync
        )
        self.graph_builder.add_edge(START, "restaurant_node")
        self.graph_builder.add_edge("restaurant_node", END)

    def assistant_chatbot_build_graph(self):
        """
        Builds a assistant chatbot graph using LangGraph.
        """
        self.restaurant_recommendation_node = RestaurantRecommendationNode(self.llm)

        self.graph_builder.add_node(
            "chatbot", self.restaurant_recommendation_node.process_sync
        )
        self.graph_builder.add_node(
            "evaluate_node", self.restaurant_recommendation_node.evaluate_node
        )
        self.graph_builder.add_node(
            "store_node", self.restaurant_recommendation_node.store_node
        )
        self.graph_builder.add_node(
            "search_node", self.restaurant_recommendation_node.search_node
        )

        self.graph_builder.add_edge(START, "chatbot")
        self.graph_builder.add_edge("chatbot", "evaluate_node")

        # Conditional routing based on evaluate_node's result
        def route_after_evaluate(state):
            # The evaluate_node returns {"result": True} or {"result": False}
            result = state.get("result", False)
            if result:
                return "store_node"
            else:
                return "search_node"

        self.graph_builder.add_conditional_edges(
            "evaluate_node",
            route_after_evaluate,
            {"store_node": "store_node", "search_node": "search_node"},
        )
        self.graph_builder.add_edge("search_node", "store_node")
        self.graph_builder.add_edge("store_node", END)

    def rag_build_graph(self):
        """
        Builds a RAG graph using LangGraph.
        """
        # Initialize RAG components
        from src.langgraphagenticai.tools.document_processor import DocumentProcessor
        from src.langgraphagenticai.tools.vectorstore import VectorStore
        from src.langgraphagenticai.state.rag_state import RAGState

        # Create a RAG node that uses the pre-initialized RAG system
        def rag_node(state):
            try:
                print(f"RAG node called with state keys: {list(state.keys())}")

                # Get the user message
                messages = state.get("messages", [])
                if not messages:
                    print("No messages found in state")
                    return state

                last_message = messages[-1]
                user_question = (
                    str(last_message.content)
                    if hasattr(last_message, "content")
                    else str(last_message)
                )
                print(f"Processing RAG question: {user_question}")

                # Get the pre-initialized RAG system from state
                rag_system = state.get("rag_system")
                if not rag_system:
                    print("RAG system not found in state")
                    from langchain_core.messages import AIMessage

                    error_message = AIMessage(
                        content="RAG system not initialized. Please initialize the RAG system first."
                    )
                    return {
                        **state,
                        "messages": state.get("messages", []) + [error_message],
                    }

                print("RAG system found in state")

                # Get the vector store from the RAG system
                vector_store = rag_system["vector_store"]

                # Create RAG nodes with the pre-initialized vector store
                rag_nodes = RAGNodes(vector_store.get_retriever(), self.llm)
                print("RAG nodes created")

                # Run RAG workflow
                rag_state = RAGState(question=user_question)
                print("Retrieving documents...")
                rag_state = rag_nodes.retrieve_docs(rag_state)
                print(f"Retrieved {len(rag_state.retrieved_docs)} documents")

                print("Generating answer...")
                rag_state = rag_nodes.generate_answer(rag_state)
                print(f"Generated answer: {rag_state.answer[:100]}...")

                # Create response message
                from langchain_core.messages import AIMessage

                response_message = AIMessage(content=rag_state.answer)

                # Update state with response
                updated_messages = messages + [response_message]

                return {
                    **state,
                    "messages": updated_messages,
                    "rag_answer": rag_state.answer,
                    "retrieved_docs": rag_state.retrieved_docs,
                }

            except Exception as e:
                print(f"Error in RAG node: {e}")
                import traceback

                traceback.print_exc()
                from langchain_core.messages import AIMessage

                error_message = AIMessage(
                    content=f"Error processing RAG query: {str(e)}"
                )
                return {
                    **state,
                    "messages": state.get("messages", []) + [error_message],
                }

        self.graph_builder.add_node("rag_node", rag_node)
        self.graph_builder.add_edge(START, "rag_node")
        self.graph_builder.add_edge("rag_node", END)

    def csv_task_build_graph(self):
        """
        Builds a CSV task management graph using LangGraph.
        """
        self.csv_task_node = CSVTaskNode(self.llm)

        self.graph_builder.add_node(
            "csv_task_node", self.csv_task_node.process_csv_tasks_sync
        )
        self.graph_builder.add_edge(START, "csv_task_node")
        self.graph_builder.add_edge("csv_task_node", END)

    def setup_graph(self, usecase: str):
        """
        Sets up the graph for the selected use case.
        """

        if usecase == "Sushi":
            self.chatbot_restaurant_recommendation()
        elif usecase == "Agentic AI":
            self.assistant_chatbot_build_graph()
        elif usecase == "RAG":
            self.rag_build_graph()
        elif usecase == "CSV Tasks":
            self.csv_task_build_graph()
        else:
            self.basic_chatbot_build_graph()

        return self.graph_builder.compile()
