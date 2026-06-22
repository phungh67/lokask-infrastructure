import requests
import json
import os
import subprocess
import ollama
import shutil
from typing import Optional

class AgentPrompts:
    """Class definition for system prompts, used in Ollama summary script"""
    def __init__(self):
        self.prompts = {
            "security": "You are a senior security officier. Your main expertises: cloud security, architect security and programing language security. Document the file analyzing vulnerable functions, objects, and return payloads.",
            "devops": "You are a senior devops officier. Your main expertises: monitoring, workload orchestration and CI/CD pipelines. Document the infrastructure logic and deployment safety.",
            "backend": "You are a senior backend officier. Your main expertises: go programming language and backend logic. Document the core logic, API surfaces, and repository patterns.",
            "frontend": "You are a senior frontend officier. Your main expertises: TypeScript and Vite framework. Document the UI logic, state management, and component architecture.",
            "architecture": "You are a senior Software Solution Architect. Main expertiese: system architect, design patterns and resilient architect. Document the overarching design patterns and boundaries."
        }
        self.verbose = 0

    def get_prompt(self, target_role: str) -> str:
        return self.prompts.get(target_role, "You are a technical writer.")

    def reinforce(self, target_role: str, reinforcement: str):
        if target_role in self.prompts:
            self.prompts[target_role] += f"\n\nCRITICAL CONSTRAINTS:\n{reinforcement}"


class OllamaConnector:
    """Handles connection between program and Ollama daemon"""
    def __init__(self, host: Optional[str] = None, model: Optional[str] = None):
        self.host = host if host is not None else os.getenv("OLLAMA_HOST_URL", "http://localhost:11434")
        self.model = model if model is not None else os.getenv("OLLAMA_PREFER_MODEL", "gemma4")
        self.verbose = 0

    def documentation_files(self, source_dir: str, output_dir: str, root_dir: str, system_prompt: str) -> list[str]:
        # 1. Read source code
        with open(source_dir, 'r', encoding='utf-8') as f:
            code_body = f.read()

        # 2. Extract technical debt & security flags (Zero-Compute)
        extracted_notes = []
        for line in code_body.split('\n'):
            line_upper = line.upper()
            if any(keyword in line_upper for keyword in ['TODO', 'FIXME', 'SECURITY', 'HACK', 'VULN']):
                clean_note = line.replace('//', '').replace('/*', '').replace('*/', '').replace('--', '').replace('#', '').strip()
                if clean_note:
                    extracted_notes.append(clean_note)
        
        # 3. Prepare output directory
        os.makedirs(os.path.dirname(output_dir), exist_ok=True)

        # 4. Calculate exact depth for Obsidian Backlink
        depth = len(os.path.relpath(output_dir, root_dir).split(os.sep)) - 1
        backlink_path = "../" * depth + "README.md"
        backlink_md = f"[⬅ Return to Main Compendium]({backlink_path})\n\n"

        # 5. Call Ollama
        stream = ollama.chat(
            model=self.model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': code_body}
            ],
            stream=True
        )

        # 6. Write mathematically perfect backlink, then stream LLM response
        with open(output_dir, 'w', encoding='utf-8') as out_file:
            out_file.write(backlink_md)
            for chunk in stream:
                out_file.write(chunk['message']['content'])
                out_file.flush()

        return extracted_notes


class FileFilter:
    """Filters unnecessary files and manages directory state"""
    def __init__(self):
        self.IGNORE_DIRS = {
            '.git', '.bun', 'node_modules', '__pycache__', '.venv', 
            'dist', 'build', 'docs', '.vscode', 'infra', 'ui',
            'hooks', 'test', 'public', 'assets', 'context'
        }
        self.IGNORE_FILES = {
            'bun.lockb', 'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml', 
            '.DS_Store', '.env', 'go.sum', 'go.mod', '.gitignore', '.dockerignore',
            'travel-platform.vuerd.json', 'package.json', 'tsconfig.json', 'postcss.config.js',
            'components.json', 'vite.config.js', 'REAME.md', 'README.md', 'tailwind.config.ts',
            'tsconfig.app.json', 'vitest.config.ts', 'eslint.config.ts', 'vite.config.ts',
            'tsconfig.node.json', 'vite-env.d.ts', 'eslint.config.js', 'App.css'
        }

    def scan(self, source_dir: str) -> list[str]: # Fixed type hint
        valid_files = []
        source_dir = os.path.abspath(source_dir)

        prune_parts = " -o -name ".join([f'"{d}"' for d in self.IGNORE_DIRS])
        prune_clause = f'\\( -type d \\( -name {prune_parts} \\) -prune \\)'

        negate_clause = " ".join([f'! -name "{f}"' for f in self.IGNORE_FILES])
        file_clause = f'\\( -type f {negate_clause} -print0 \\)'

        cmd = f'find "{source_dir}" {prune_clause} -o {file_clause}'

        try:
            result = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            output = result.stdout.decode('utf-8', errors='ignore')
            return [f for f in output.split('\x00') if f.strip()]
        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to execute find command: {e.stderr.decode()}")
            return []

    def wipe_docs_directory(self, target_dir: str):
        docs_path = os.path.join(target_dir, "docs")
        if os.path.exists(docs_path):
            print(f"[LOG] Wiping existing documentation directory: {docs_path}")
            shutil.rmtree(docs_path)
        os.makedirs(docs_path, exist_ok=True)

    def generate_compedium(self, target_dir: str, manifest_lines: list[str], connector: OllamaConnector):
        print("\nBegin creating the Master Compendium...")
        
        manifest_content = "\n".join(manifest_lines)
        readme_path = os.path.join(target_dir, "README.md") # Fixed variable name

        override_prompt = (
            "You are a Senior Technical Writer and Lead Architect. Using the provided repository manifest, "
            "generate a comprehensive root-level README.md. "
            "You MUST strictly structure the document with the following sections:\n"
            "1. **Architectural Overview**: High-level summary of the system inferred from the roles and directories.\n"
            "2. **Critical Issues (ASAP)**: Read the '| Findings:' attached to the files in the manifest. Extract, aggregate, and list ONLY the most critical vulnerabilities, HACKS, and urgent technical debt that need immediate fixing.\n"
            "3. **Role-Based Directory Map**: A structured Table of Contents using the EXACT markdown links provided.\n"
        )

        stream = ollama.chat(
            model=connector.model,
            messages=[
                {'role': 'system', 'content': override_prompt},
                {'role': 'user', 'content': manifest_content}
            ],
            stream=True
        )

        print(f"Streaming final compendium to: {readme_path}")
        with open(readme_path, 'w', encoding='utf-8') as f:
            for chunk in stream:
                f.write(chunk['message']['content'])
                f.flush()
        print("[SUCCESS] Pipeline Complete.")


if __name__ == "__main__":
    target_dir = "/home/huyhoang/lokask"
    
    # Initialization
    agent_prompts = AgentPrompts()
    file_filter = FileFilter()
    ollama_connector = OllamaConnector()
    
    # 1. Clean slate
    file_filter.wipe_docs_directory(target_dir)
    files_to_feed = file_filter.scan(target_dir)
    print(f"Found {len(files_to_feed)} valid source files.\n")

    # 2. Define the roles you want to execute for this run
    TARGET_ROLES = ["security", "backend", "frontend"] 
    
    # Base Master Manifest
    manifest_lines = [f"# Master Compendium & Critical Issues\n"]

    # 3. Main Routing Loop
    for role in TARGET_ROLES:
        print(f"\n=============================")
        print(f"🚀 INITIATING ROLE: {role.upper()}")
        print(f"=============================")
        
        manifest_lines.append(f"\n## {role.title()} Domain\n")
        
        # Enforce universal guardrails per role
        agent_prompts.reinforce(role, "Append this exact phrase at the bottom: *this content was created by AI, but the coding and underlying logic are not.*")
        role_system_prompt = agent_prompts.get_prompt(role)

        for f in files_to_feed:
            # Map output to: target_dir/docs/{role}/relative_path.md
            relative_path = os.path.relpath(f, target_dir)
            output_path = os.path.join(target_dir, "docs", role, relative_path)
            output_path = os.path.splitext(output_path)[0] + ".md"
            
            print(f"[*] {role.upper()} Processing: {os.path.basename(f)}")
            
            # Execute Generation & Debt Extraction
            extracted_notes = ollama_connector.documentation_files(
                source_dir=f, 
                output_dir=output_path, 
                root_dir=target_dir, 
                system_prompt=role_system_prompt
            )
            
            # Format Manifest Link for this specific role's output
            doc_rel_path = os.path.relpath(output_path, target_dir)
            filename = os.path.basename(doc_rel_path)
            manifest_entry = f"- [{filename}](./{doc_rel_path})"
            
            if extracted_notes:
                manifest_entry += f" | **Findings:** {'; '.join(extracted_notes)}"
                
            manifest_lines.append(manifest_entry)

    # 4. Generate the Final Aggregated Compendium
    file_filter.generate_compedium(target_dir, manifest_lines, ollama_connector)