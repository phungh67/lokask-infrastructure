# definition for different prompts, fit with desired role of llm usage

class AgentPrompts:
    """Class definition for system prompts, used in Ollama summary script
    Important notes:
    - Try to append instead of directly modifying prompts
    - Classify into categories (security, summary, data,...)
    """

    def __init__(self):
        self.prompts = {
            "security": "You are a senior security officier. Your main expertises: cloud security, architect security and programing language security.",
            "devops": "You are a senior devops officier. Your main expertises: monitoring, workload orchestration and CI/CD pipelines.",
            "backend": "You are a senior backend officier. Your main expertises: go programming language and backend logic.",
            "frontend": "You are a senior frontend officier. Your main expertises: TypeScript and Vite framework plus front end logic.",
            "architecture": "You are a senior Software Solution Architect. Main expertiese: system architect, design patterns and resilient architect."
        }

        self.verbose = 0

    def toggle_verbose(self):
        if self.verbose == 1:
            self.verbose = 0
            print("[LOG] Log is disabled.")
        else:
            self.verbose = 1
            print("[LOG] Log is enabled.")

    def append(self, target_role: str, additional_prompt: str) -> bool:
        """Appends additional context to an existing role."""
        if target_role in self.prompts:
            self.prompts[target_role] += f" {additional_prompt}"
            if self.verbose:
                print(f"[LOG] Appended new context to '{target_role}'.")
            return True
            
        if self.verbose:
            print(f"[ERROR] Failed to append: Role '{target_role}' does not exist.")
        return False

    def override(self, target_role: str, new_prompt: str) -> bool:
        """Completely replaces the prompt for a given role."""
        if target_role in self.prompts:
            self.prompts[target_role] = new_prompt
            if self.verbose:
                print(f"[LOG] Overrode prompt for '{target_role}'.")
            return True
            
        if self.verbose:
            print(f"[ERROR] Failed to override: Role '{target_role}' does not exist.")
        return False

    def reinforce(self, target_role: str, reinforcement: str) -> bool:
        """Injects non-negotiable guardrails or formatting structures."""
        if target_role in self.prompts:
            self.prompts[target_role] += f"\n\nCRITICAL CONSTRAINTS:\n{reinforcement}"
            if self.verbose:
                print(f"[LOG] Reinforced '{target_role}' with critical constraints.")
            return True
            
        if self.verbose:
            print(f"[ERROR] Failed to reinforce: Role '{target_role}' does not exist.")
        return False

    def get_prompt(self, target_role: str) -> str:
        """Safely retrieves the prompt for API payload injection."""
        if target_role not in self.prompts:
            if self.verbose:
                print(f"[WARNING] Role '{target_role}' not found. Returning empty string.")
            return ""
            
        return self.prompts[target_role]