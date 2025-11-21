#!/usr/bin/env python3
"""
Run the Appliance Troubleshooting Agent System on Localhost
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import the orchestrator
from agents.core_orchestrator import create_core_orchestrator

# Import Google ADK
from google.adk.apps import App

def main():
    """Start the agent application."""

    print("=" * 60)
    print("🤖 APPLIANCE TROUBLESHOOTING AGENT SYSTEM")
    print("=" * 60)
    print("Starting agent with accuracy-driven routing...")
    print()

    # Create the agent
    try:
        agent = create_core_orchestrator()
        print("✅ Agent created successfully!")
        print(f"   - Agent: {agent.name}")
        print(f"   - Model: {agent.model}")
        print(f"   - Sub-agents: {len(agent.sub_agents)}")
        print(f"   - Tools: {len(agent.tools)}")
        print()
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        sys.exit(1)

    # Create and run the app
    try:
        print("🚀 Starting server on http://localhost:8000")
        print("=" * 60)
        print()
        print("📝 How to use:")
        print("   1. Open browser: http://localhost:8000")
        print("   2. Or use API: POST http://localhost:8000/chat")
        print("   3. Chat with the agent about appliance issues")
        print()
        print("💡 Features:")
        print("   ✓ Accuracy-driven routing (75% threshold)")
        print("   ✓ Wrong model detection")
        print("   ✓ Safety checking")
        print("   ✓ Service ticket creation")
        print()
        print("Press Ctrl+C to stop the server")
        print("=" * 60)
        print()

        # Create ADK app with correct parameters
        app = App(
            name="fridge_troubleshooting_rag",
            root_agent=agent
        )

        # Run the app
        app.run(host="0.0.0.0", port=8000, log_level="INFO")

    except KeyboardInterrupt:
        print("\n\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
