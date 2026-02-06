# ============================================================================
# INVENTRA - Prompts Package
# ============================================================================
# 
# This package contains prompt templates for all agents.
# Prompts are stored as markdown files for easy editing.
#
# Files:
# - supervisor.md: System prompt for the Supervisor/Router agent
# - data_agent.md: System prompt for the Data Understanding Agent
# - weather_agent.md: System prompt for the Weather Agent
# - decision_agent.md: System prompt for the Decision Agent
#
# Usage:
#   from prompts import load_prompt
#   prompt = load_prompt("supervisor")
# ============================================================================

from pathlib import Path


def load_prompt(prompt_name: str) -> str:
    """
    Load a prompt template from a markdown file.
    
    Args:
        prompt_name: Name of the prompt file (without .md extension)
        
    Returns:
        str: The prompt content
        
    Example:
        >>> prompt = load_prompt("supervisor")
    """
    prompt_path = Path(__file__).parent / f"{prompt_name}.md"
    
    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


__all__ = ["load_prompt"]
