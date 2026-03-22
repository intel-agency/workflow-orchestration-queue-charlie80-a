"""
OS-APOW: Headless Agentic Orchestration Platform

A groundbreaking headless agentic orchestration platform that transforms
the current paradigm of "interactive" AI coding into an autonomous
background production service.

Architecture (4-Pillar Model):
- Ear (Notifier): FastAPI webhook receiver for GitHub events
- State (Queue): GitHub Issues + Labels as distributed state management
- Brain (Sentinel): Persistent polling, task claiming, worker lifecycle
- Hands (Worker): Isolated DevContainer-based AI execution environment
"""

__version__ = "0.1.0"
__author__ = "Intel Agency"
