# definition for different prompts, fit with desired role of llm usage

class AgentPrompts:
    """Class definition for system prompts, used in Ollama summary script
    Important notes:
    - Try to appened instead of directly modifying prompts
    - Classify into categories (security, summary, data,...)
    """

    def __init__(self):
        self.security_role_default_prompt = (
            "You are a senior security engineer from an enterprise environment."
            "You main task: focus on review the security issue of any codebase."
            "Classify threats and risks into: High, Medium and Low."
            "Specialized in: cloud security, system security, infrastructure hardening."
        )

        self.devops_role_default_prompt = (
            
        )