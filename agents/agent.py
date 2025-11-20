#!/usr/bin/env python3
"""
Main agent entry point for ADK
"""

from agents.core_orchestrator import create_core_orchestrator

# This is required by ADK - must be named 'root_agent'
root_agent = create_core_orchestrator()
