from flask import Flask, render_template, request, jsonify
import os
import json
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
from beam_visualizer import visualize_beam_from_data
from ai_agent.llm_orchestrator import LLMOrchestrator

# Import LangGraph components
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "AI-Agent-Flask"))
from src.langgraphagenticai.LLMS.geminillm import GeminiLLM
from src.langgraphagenticai.graph.graph_builder import GraphBuilder
from src.langgraphagenticai.tools.return_prompt import return_prompt

# Load environment variables
load_dotenv()

# Configure logging with file output
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)

# Set up file handler with rotation
from logging.handlers import RotatingFileHandler

# Configure root logger
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        # Console handler for immediate feedback
        logging.StreamHandler(),
        # File handler for persistent logs
        RotatingFileHandler(
            os.path.join(log_dir, "gendesign.log"),
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
        ),
    ],
)

logger = logging.getLogger(__name__)
logger.info("=" * 50)
logger.info("GenDesign Application Starting")
logger.info("=" * 50)

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key")
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# Initialize LLM Orchestrator
anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
if (
    not anthropic_api_key
    or anthropic_api_key == "your_anthropic_api_key_here"
    or len(anthropic_api_key.strip()) == 0
):
    logger.warning(
        "ANTHROPIC_API_KEY not set or using placeholder. Chat functionality requires a valid API key."
    )
    llm_orchestrator = None
else:
    try:
        llm_orchestrator = LLMOrchestrator(anthropic_api_key)
        logger.info("AI chat functionality initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize AI chat: {e}")
        llm_orchestrator = None

# LangGraph session storage
langgraph_sessions = {}
langgraph_llm_configs = {}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/chat", methods=["POST"])
def chat_endpoint():
    """Main API endpoint for AI conversation with optional file upload."""
    if not llm_orchestrator:
        return jsonify(
            {
                "error": "AI functionality not available. Please configure ANTHROPIC_API_KEY.",
                "action": "error",
                "llm_response": "Sorry, the AI chat feature is not configured. Please contact the administrator.",
                "require_user_input": True,
            }
        ), 500

    try:
        # Handle both JSON and form data (with file uploads)
        json_data = None

        if request.content_type and request.content_type.startswith(
            "multipart/form-data"
        ):
            # Form data with potential file upload
            user_message = request.form.get("message", "").strip()
            model = request.form.get("model", "claude-3-5-haiku-20241022")
            session_id = request.form.get("session_id", "default_session")

            # Handle file upload if present
            if "file" in request.files:
                file = request.files["file"]
                if file and file.filename and file.filename.endswith(".json"):
                    try:
                        json_data = json.load(file.stream)
                        logger.info(
                            f"File uploaded: {file.filename} with data: {json_data}"
                        )
                    except json.JSONDecodeError:
                        return jsonify({"error": "Invalid JSON file format"}), 400
                    except Exception as e:
                        logger.error(f"Error reading uploaded file: {e}")
                        return jsonify({"error": "Error reading uploaded file"}), 400
        else:
            # Standard JSON request
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400

            user_message = data.get("message", "").strip()
            model = data.get("model", "claude-3-5-haiku-20241022")
            session_id = data.get("session_id", "default_session")

        # Validate model choice
        valid_models = ["claude-3-5-haiku-20241022", "claude-3-sonnet-20240229"]
        if model not in valid_models:
            model = "claude-3-5-haiku-20241022"

        # Process with LLM orchestrator (now with optional JSON data)
        response = asyncio.run(
            llm_orchestrator.process_user_input(
                user_message, model, session_id, json_data
            )
        )

        logger.info(
            f"Chat response for session {session_id}: {response.get('action', 'unknown')}"
        )

        return jsonify(response)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify(
            {
                "error": str(e),
                "action": "error",
                "llm_response": "I encountered an error processing your request. Please try again.",
                "require_user_input": True,
            }
        ), 500


@app.route("/api/session/<session_id>", methods=["GET"])
def get_session_state(session_id):
    """Get current session state."""
    if not llm_orchestrator:
        return jsonify({"error": "AI functionality not available"}), 500

    state = llm_orchestrator.get_session_state(session_id)
    return jsonify(state if state else {})


@app.route("/api/session/<session_id>", methods=["DELETE"])
def clear_session(session_id):
    """Clear session state."""
    if not llm_orchestrator:
        return jsonify({"error": "AI functionality not available"}), 500

    llm_orchestrator.clear_session(session_id)
    return jsonify({"message": "Session cleared"})


@app.route("/api/langgraph/chat", methods=["POST"])
def langgraph_chat_endpoint():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        user_message = data.get("message", "").strip()
        session_id = data.get("session_id", "default_session")

        if not user_message:
            return jsonify({"error": "No message provided"}), 400

        # Initialize or get existing LangGraph session
        if session_id not in langgraph_sessions:
            langgraph_sessions[session_id] = []

        # Initialize LLM config for LangGraph (using Gemini as default)
        if session_id not in langgraph_llm_configs:
            try:
                # Check if GEMINI_API_KEY is available
                gemini_api_key = os.getenv("GEMINI_API_KEY")
                if not gemini_api_key:
                    logger.error("GEMINI_API_KEY not found in environment variables")
                    return jsonify(
                        {
                            "error": "GEMINI_API_KEY not configured. Please set GEMINI_API_KEY environment variable.",
                            "action": "error",
                            "llm_response": "LangGraph system requires GEMINI_API_KEY to be configured. Please contact the administrator.",
                            "require_user_input": True,
                        }
                    ), 500

                # Use Gemini as default LLM for LangGraph
                user_controls = {
                    "selected_llm": "Gemini",
                    "selected_gemini_model": "gemini-2.5-flash",
                    "GEMINI_API_KEY": gemini_api_key,
                }
                logger.info(f"Initializing LangGraph LLM for session {session_id}")
                llm_config = GeminiLLM(user_controls_input=user_controls)
                langgraph_llm_configs[session_id] = llm_config
                logger.info("LangGraph LLM initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize LangGraph LLM: {e}")
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")
                return jsonify(
                    {
                        "error": f"Failed to initialize LangGraph system: {str(e)}",
                        "action": "error",
                        "llm_response": "I encountered an error initializing the LangGraph system. Please try again or contact the administrator.",
                        "require_user_input": True,
                    }
                ), 500

        # Get chat history
        chat_history = langgraph_sessions.get(session_id, [])

        # Prepare messages with system prompt for CSV Tasks usecase
        system_prompt = return_prompt("CSV Tasks")
        messages = [{"role": "system", "content": system_prompt}]

        # Add chat history (last 20 messages)
        last_n_messages = chat_history[-20:] if len(chat_history) > 20 else chat_history
        messages += [
            {"role": msg["role"], "content": msg["content"]} for msg in last_n_messages
        ]

        # Add current user message
        if len(messages) > 20:
            messages.pop(1)
        messages.append({"role": "user", "content": user_message})

        # Prepare initial state
        initial_state = {"messages": messages}

        # Build and run the graph
        try:
            logger.info(f"Building LangGraph for session {session_id}")
            base_llm = langgraph_llm_configs[session_id].get_base_llm()
            graph_builder = GraphBuilder(
                model=base_llm,
                user_controls_input={
                    "selected_llm": "Gemini",
                    "selected_usecase": "Sushi",
                },
                message=user_message,
            )
            graph = graph_builder.setup_graph("Sushi")
            logger.info("LangGraph built successfully")

            # Run the graph
            logger.info(f"Running LangGraph for message: {user_message}")
            result = asyncio.run(
                graph.ainvoke(
                    initial_state, config={"configurable": {"session_id": session_id}}
                )
            )
            logger.info("LangGraph execution completed successfully")

        except Exception as e:
            logger.error(f"Error in LangGraph execution: {e}")
            import traceback

            logger.error(f"Traceback: {traceback.format_exc()}")
            return jsonify(
                {
                    "error": f"LangGraph execution failed: {str(e)}",
                    "action": "error",
                    "llm_response": "I encountered an error processing your request with the LangGraph system. Please try again.",
                    "require_user_input": True,
                }
            ), 500

        # Extract assistant reply and format it properly
        assistant_reply = ""
        if isinstance(result["messages"], list):
            last_message = result["messages"][-1] if result["messages"] else ""
            if isinstance(last_message, dict):
                assistant_reply = last_message.get("content", "")
            else:
                # Handle AIMessage objects
                if hasattr(last_message, "content"):
                    assistant_reply = last_message.content
                else:
                    assistant_reply = str(last_message)
        elif isinstance(result["messages"], dict):
            assistant_reply = result["messages"].get("content", "")
        else:
            assistant_reply = str(result["messages"])

        # Clean up the response - remove any raw content formatting
        if assistant_reply.startswith("content='") and assistant_reply.endswith("'"):
            # Extract content from the raw format
            try:
                import ast

                # Try to parse as a literal
                cleaned = ast.literal_eval(assistant_reply)
                if isinstance(cleaned, str):
                    assistant_reply = cleaned
            except:
                # If parsing fails, just remove the content=' and trailing '
                assistant_reply = (
                    assistant_reply[9:-1]
                    if assistant_reply.startswith("content='")
                    else assistant_reply
                )

        # Remove any additional_kwargs and response_metadata from the response
        if "additional_kwargs=" in assistant_reply:
            assistant_reply = assistant_reply.split("additional_kwargs=")[0].strip()
        if "response_metadata=" in assistant_reply:
            assistant_reply = assistant_reply.split("response_metadata=")[0].strip()

        # Clean up any trailing quotes or formatting
        assistant_reply = assistant_reply.strip().rstrip("'").rstrip('"')

        # Format the response for better readability in chat
        if assistant_reply:
            # Replace newlines with proper line breaks for HTML display
            assistant_reply = assistant_reply.replace("\n", "<br>")
            # Add some basic formatting for lists
            if "1." in assistant_reply and "2." in assistant_reply:
                # Format numbered lists
                lines = assistant_reply.split("<br>")
                formatted_lines = []
                for line in lines:
                    if line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                        formatted_lines.append(f"<strong>{line.strip()}</strong>")
                    else:
                        formatted_lines.append(line)
                assistant_reply = "<br>".join(formatted_lines)

        # Update chat history
        langgraph_sessions[session_id].append({"role": "user", "content": user_message})
        langgraph_sessions[session_id].append(
            {"role": "assistant", "content": assistant_reply}
        )

        return jsonify(
            {
                "action": "langgraph_response",
                "llm_response": assistant_reply,
                "require_user_input": True,
                "mode": "langgraph",
            }
        )

    except Exception as e:
        logger.error(f"Error in LangGraph chat endpoint: {e}")
        return jsonify(
            {
                "error": str(e),
                "action": "error",
                "llm_response": "I encountered an error processing your request. Please try again.",
                "require_user_input": True,
            }
        ), 500


@app.route("/api/langgraph/test", methods=["GET"])
def test_langgraph():
    """Test endpoint to verify LangGraph system is working."""
    try:
        # Check if GEMINI_API_KEY is available
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        if not gemini_api_key:
            return jsonify(
                {
                    "status": "error",
                    "message": "GEMINI_API_KEY not configured",
                    "gemini_available": False,
                }
            ), 500

        # Try to initialize GeminiLLM
        user_controls = {
            "selected_llm": "Gemini",
            "selected_gemini_model": "gemini-2.5-flash",
            "GEMINI_API_KEY": gemini_api_key,
        }

        llm_config = GeminiLLM(user_controls_input=user_controls)
        base_llm = llm_config.get_base_llm()

        return jsonify(
            {
                "status": "success",
                "message": "LangGraph system is properly configured",
                "gemini_available": True,
                "llm_type": "Gemini",
            }
        )

    except Exception as e:
        logger.error(f"LangGraph test failed: {e}")
        import traceback

        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify(
            {
                "status": "error",
                "message": f"LangGraph test failed: {str(e)}",
                "gemini_available": False,
            }
        ), 500


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return jsonify({"error": "No file part"})

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"})

    if file and file.filename.endswith(".json"):
        try:
            # Read the uploaded JSON data
            json_data = json.load(file.stream)

            # Generate the figure
            fig = visualize_beam_from_data(json_data)

            # Convert the figure to a JSON object
            graph_json = fig.to_json()

            return jsonify({"graph_json": graph_json})

        except json.JSONDecodeError:
            return jsonify({"error": "Invalid JSON format."})
        except ValueError as e:
            return jsonify({"error": str(e)})
        except Exception as e:
            return jsonify({"error": f"An unexpected error occurred: {str(e)}"})

    return jsonify({"error": "Invalid file type. Please upload a JSON file."})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
