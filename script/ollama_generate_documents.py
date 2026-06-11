import requests
import json
import os
import subprocess
import ollama
import shutil
from typing import Optional

class OllamaConnector:
    """Class definition for Ollama Connector - handle connection between program
    and Ollama daemon
    
    Keyword arguments:
    argument -- description
    Documentations: https://docs.ollama.com/api/
    At least 2 environment variables need setting
    OLLAMA_HOST_URL = address where OLLAMA is running
    OLLAMA_PREFER_MODEL = model that is currently being used
    """

    def __init__(self, host: Optional[str] = None, model: Optional[str] = None, embedding_model: Optional[str] = None):
        """Constructor
        
        Keyword arguments:
        argument -- description
        host(string) -- ollama host url
        model(string) -- ollama model 
        embedding_model(string) -- ollama embedding model
        Return: OllamaConnector object
        """

        self.host = host if host is not None else os.getenv("OLLAMA_HOST_URL", "http://localhost:11434")
        self.model = model if model is not None else os.getenv("OLLAMA_PREFER_MODEL", "gemma4")
        self.embedding_model = embedding_model if embedding_model is not None else os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")

        self.api_url = f"{self.host}/api/chat"

        self.verbose = 0

        self.system_prompt = (
            "You are a documentation-engineer in a coporate."
            "You read each input file, try to create a comprehesive summary from that file."
            "Each file should have overview, detail, note and warning(thing that are left unfinished, most important, tech debt)."
            "Knowledge base: system design, infrastructure, cloud components, security engineer."
            "Not use emoji if unnecessary."
            "Generate structural README file in markdown format. Include generated figured if possible."
            "You MUST start the markdown file with a structural navigation link back to the main compendium exactly like this:\n"
            "`[⬅ Return to Main Compendium](../../README.md)`\n\n"
        )

    def toggle_log(self):
        """Flip the status of verbose indicator
        """
        self.verbose = not self.verbose
        if self.verbose:
            print("[LOG] Toogled on}\n")
        else:
            print("[LOG] Toogled off\n")

    def documentation_files(self, source_dir: str, output_dir: str):
        with open(source_dir, 'r', encoding='utf-8') as f:
            code_body = f.read()

        extracted_notes = []
        for line in code_body.split('\n'):
            line_upper = line.upper()
            if any(keyword in line_upper for keyword in ['TODO', 'FIXME', 'SECURITY', 'HACK', 'VULN']):
                clean_note = line.replace('//', '').replace('/*', '').replace('*/', '').replace('--', '').replace('#', '').strip()
                if clean_note:
                    extracted_notes.append(clean_note)
        
        os.makedirs(os.path.dirname(output_dir), exist_ok=True)

        stream = ollama.chat(
            model = self.model,
            messages = [
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': code_body}
            ],
            stream = True
        )

        with open(output_dir, 'w', encoding='utf-8') as out_file:
            for chunk in stream:
                out_file.write(chunk['message']['content'])
                out_file.flush()

class FileFilter:
    """Class for a file filter object, take an input directory, filter all unnecessary files
    and feeds these filess to the Ollama
    """
    def __init__(self):
        self.IGNORE_DIRS = {
            '.git', '.bun', 'node_modules', '__pycache__', '.venv', 
            'dist', 'build', 'docs', '.vscode', '.github', 'infra', 'components',
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
        self.IGNORE_EXTS = {
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', 
            '.pdf', '.zip', '.tar', '.gz', '.json', '.vuerd'
        }

    def scan(self, source_dir: str) -> out_list[str]:
        valid_files = []
        source_dir = os.path.abspath(source_dir)

        prune_parts = " -o -name ".join([f'"{d}"' for d in self.IGNORE_DIRS])
        prune_clause = f'\\( -type d \\( -name {prune_parts} \\) -prune \\)'

        negate_clause = " ".join([f'! -name "{f}"' for f in self.IGNORE_FILES])
        file_clause = f'\\( -type f {negate_clause} -print0 \\)'

        cmd = f'find "{source_dir}" {prune_clause} -o {file_clause}'

        try:
            result = subprocess.run(
                cmd, 
                shell=True, 
                check=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE
            )
            
            output = result.stdout.decode('utf-8', errors='ignore')
            valid_files = [f for f in output.split('\x00') if f.strip()]
            
            return valid_files

        except subprocess.CalledProcessError as e:
            print(f"[ERROR] Failed to execute find command: {e.stderr.decode()}")
            return []

    def wipe_docs_directory(self, target_dir: str):
        """Wipes the docs directory to ensure a fresh compendium build."""
        docs_path = os.path.join(target_dir, "docs")
        if os.path.exists(docs_path):
            print(f"[LOG] Wiping existing documentation directory: {docs_path}")
        shutil.rmtree(docs_path)
    
        os.makedirs(docs_path, exist_ok=True)

    def generate_compedium(self, target_dir: str, files: list[str]):
        print("Begin to create the compedium.\n")

        tree_lines = [f"# Directory Map for {os.path.basename(target_dir)}\n"]

        for file_path in files:
            relative_path = os.path.relpath(file_path, target_dir)
            doc_path = os.path.splitext(relative_path)[0] + ".md"

            filename = os.path.basename(doc_path)
            tree_lines.append(f"- [{filename}](./docs/{doc_path})")
        
        manifest_content = "\n".join(tree_lines)

        override_prompt = (
            "You are a Senior Technical Writer. Using the provided repository file manifest, "
            "generate a comprehensive root-level README.md. "
            "It must include a high-level architectural overview (inferred from the directory/file names) "
            "and a structured, categorized Table of Contents using the exact markdown links provided. "
            "At the very end of your response, you MUST append this exact markdown disclaimer phrase: "
            "\n\n*this content was created by AI, but the coding and underlying logic are not.*"
        )

        readme_path = os.path.join(target_directory, "README.md")

        stream = ollama.chat(
            model=self.model,
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


if __name__ == "__main__":
    target_dir = "/home/huyhoang/lokask"
    file_filter = FileFilter()
    ollama_connector = OllamaConnector()
    files_to_feed = file_filter.scan(target_dir)

    file_filter.wipe_docs_directory(target_dir)

    print(f"Found {len(files_to_feed)} valid source files.\n")
    
    manifest_lines = [f"# Directory Map for {os.path.basename(target_dir)}\n"]

    for f in files_to_feed:
        print(f"[*] Now processing file {f}...")
        relative_path = os.path.relpath(f, target_dir)
        output_path = os.path.join(target_dir, "docs", relative_path)
        output_path = os.path.splitext(output_path)[0] + ".md"
        
        extracted_notes = ollama_connector.documentation_files(f, output_path)
        
        doc_rel_path = os.path.relpath(output_path, target_dir)
        filename = os.path.basename(doc_rel_path)
        manifest_entry = f"- [{filename}](./{doc_rel_path})"
        
        if extracted_notes:
            manifest_entry += f" | **Findings:** {'; '.join(extracted_notes)}"
            
        manifest_lines.append(manifest_entry)

    file_filter.generate_compedium(manifest_lines)
    
    
    
        

    