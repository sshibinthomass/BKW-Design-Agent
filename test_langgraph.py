#!/usr/bin/env python3
"""
Test script to diagnose LangGraph integration issues.
Run this script to check if all dependencies and configurations are working.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_environment():
    """Test environment variables and basic setup."""
    print("🔍 Testing Environment Setup...")

    # Check GROQ_API_KEY
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print(f"✅ GROQ_API_KEY found: {groq_key[:10]}...")
    else:
        print("❌ GROQ_API_KEY not found")
        return False

    return True


def test_imports():
    """Test if all required modules can be imported."""
    print("\n🔍 Testing Module Imports...")

    try:
        # Test basic imports
        import asyncio

        print("✅ asyncio imported")

        # Test LangChain imports
        from langchain_core.messages import HumanMessage, AIMessage

        print("✅ langchain_core imported")

        # Test LangGraph imports
        from langgraph.graph import StateGraph

        print("✅ langgraph imported")

        # Test Groq import
        from langchain_groq import ChatGroq

        print("✅ langchain_groq imported")

        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_langgraph_components():
    """Test LangGraph specific components."""
    print("\n🔍 Testing LangGraph Components...")

    try:
        # Add AI-Agent-Flask to path
        sys.path.append(os.path.join(os.path.dirname(__file__), "AI-Agent-Flask"))

        # Test GroqLLM
        from src.langgraphagenticai.LLMS.groqllm import GroqLLM

        print("✅ GroqLLM imported")

        # Test GraphBuilder
        from src.langgraphagenticai.graph.graph_builder import GraphBuilder

        print("✅ GraphBuilder imported")

        # Test return_prompt
        from src.langgraphagenticai.tools.return_prompt import return_prompt

        print("✅ return_prompt imported")

        return True

    except ImportError as e:
        print(f"❌ LangGraph component import error: {e}")
        return False


def test_groq_connection():
    """Test Groq API connection."""
    print("\n🔍 Testing Groq API Connection...")

    try:
        from langchain_groq import ChatGroq

        groq_key = os.getenv("GROQ_API_KEY")
        if not groq_key:
            print("❌ GROQ_API_KEY not available")
            return False

        # Test basic Groq connection
        llm = ChatGroq(
            groq_api_key=groq_key, model_name="llama-3.3-70b-versatile", temperature=0.1
        )

        # Test a simple completion
        response = llm.invoke("Hello, this is a test message.")
        print(f"✅ Groq API working: {response.content[:50]}...")

        return True

    except Exception as e:
        print(f"❌ Groq API error: {e}")
        return False


def test_langgraph_simple():
    """Test a simple LangGraph setup."""
    print("\n🔍 Testing Simple LangGraph Setup...")

    try:
        import asyncio
        from langchain_core.messages import HumanMessage
        from langchain_groq import ChatGroq

        # Add AI-Agent-Flask to path
        sys.path.append(os.path.join(os.path.dirname(__file__), "AI-Agent-Flask"))
        from src.langgraphagenticai.graph.graph_builder import GraphBuilder

        groq_key = os.getenv("GROQ_API_KEY")
        llm = ChatGroq(
            groq_api_key=groq_key, model_name="llama-3.3-70b-versatile", temperature=0.1
        )

        # Test simple graph creation
        graph_builder = GraphBuilder(
            model=llm,
            user_controls_input={"selected_llm": "Groq", "selected_usecase": "Sushi"},
            message="test",
        )

        graph = graph_builder.setup_graph("Sushi")
        print("✅ LangGraph setup successful")

        # Test simple execution
        initial_state = {
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"},
            ]
        }

        result = asyncio.run(
            graph.ainvoke(
                initial_state, config={"configurable": {"session_id": "test_session"}}
            )
        )

        print(f"✅ LangGraph execution successful: {str(result)[:100]}...")
        return True

    except Exception as e:
        print(f"❌ LangGraph execution error: {e}")
        import traceback

        print(f"Traceback: {traceback.format_exc()}")
        return False


def main():
    """Run all tests."""
    print("🚀 LangGraph Diagnostic Test")
    print("=" * 50)

    tests = [
        test_environment,
        test_imports,
        test_langgraph_components,
        test_groq_connection,
        test_langgraph_simple,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)

    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")

    passed = sum(results)
    total = len(results)

    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")

    if passed == total:
        print("🎉 All tests passed! LangGraph should work.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("\n💡 Common fixes:")
        print("1. Install missing dependencies: pip install -r requirements.txt")
        print("2. Set GROQ_API_KEY in your .env file")
        print("3. Check if all LangGraph modules are properly installed")


if __name__ == "__main__":
    main()
