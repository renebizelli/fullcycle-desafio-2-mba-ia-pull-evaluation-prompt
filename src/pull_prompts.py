"""
Script para fazer pull de prompts do LangSmith Prompt Hub e salvá-los em YAML.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull de um prompt do Hub
3. Extrai os blocos system/user do prompt
4. Salva localmente na pasta prompts/
"""

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langsmith import Client
from utils import check_env_vars, print_section_header, save_yaml

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPTS_DIR = PROJECT_ROOT / "prompts/bug_to_user_story"
PROMPT_TEMPLATE  = "leonanluppi/bug_to_user_story_v1"


def extract_template_content(message_template: Any) -> str:
    prompt = getattr(message_template, "prompt", None)
    if prompt is not None and hasattr(prompt, "template"):
        return prompt.template

    if hasattr(message_template, "template"):
        return message_template.template

    if hasattr(message_template, "content"):
        content = message_template.content
        if isinstance(content, str):
            return content

    return str(message_template)


def extract_prompts(prompt_object: Any) -> tuple[str, str]:
    system_parts: list[str] = []
    user_parts: list[str] = []

    messages = getattr(prompt_object, "messages", None)
    if not messages:
        template = getattr(prompt_object, "template", None)
        if isinstance(template, str):
            return template, "{input}"
        raise ValueError("Nao foi possivel identificar mensagens no prompt retornado pelo LangSmith.")

    for message in messages:
        role = message.__class__.__name__.lower()
        content = extract_template_content(message).strip()

        if not content:
            continue

        if "system" in role:
            system_parts.append(content)
        elif "human" in role or "user" in role:
            user_parts.append(content)

    system_prompt = "\n\n".join(system_parts).strip()
    user_prompt = "\n\n".join(user_parts).strip()

    if not system_prompt and not user_prompt:
        raise ValueError("O prompt foi carregado, mas nao foi possivel extrair blocos system/user.")

    return system_prompt, user_prompt or "{input}"


def normalize_prompt_key(prompt_identifier: str) -> str:
    prompt_name = prompt_identifier.split("/")[-1]
    prompt_name = prompt_name.split(":")[0]
    return prompt_name.strip()


def build_yaml_payload(
    prompt_key: str,
    system_prompt: str,
    user_prompt: str,
    prompt_identifier: str,
) -> dict[str, Any]:
    version = "v1"
    if ":" in prompt_identifier:
        version = prompt_identifier.split(":")[-1]

    return {
        prompt_key: {
            "description": f"Prompt sincronizado do LangSmith: {prompt_identifier}",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": version,
            "created_at": str(date.today()),
            "tags": ["langsmith", "prompt-hub", "synced"],
        }
    }


def pull_prompt_from_langsmith(prompt_identifier: str, output_path: Path | None = None) -> Path:
    client = Client()
    prompt = client.pull_prompt(prompt_identifier)

    prompt_key = normalize_prompt_key(prompt_identifier)
    system_prompt, user_prompt = extract_prompts(prompt)
    payload = build_yaml_payload(
        prompt_key=prompt_key,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        prompt_identifier=prompt_identifier,
    )

    target_path = output_path or (PROMPTS_DIR / f"{prompt_key}.yml")
    saved = save_yaml(payload, str(target_path))
    if not saved:
        raise RuntimeError(f"Falha ao salvar arquivo YAML em {target_path}")

    return target_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Faz pull de um prompt do LangSmith e salva em YAML."
    )
    parser.add_argument(
        "prompt_identifier",
        nargs="?",
        default=PROMPT_TEMPLATE,
        help="Identificador do prompt no LangSmith, ex.: owner/nome_do_prompt",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Caminho opcional do arquivo YAML de saida",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not check_env_vars(["LANGSMITH_API_KEY", "LANGSMITH_ENDPOINT", "LANGSMITH_PROJECT","OPENAI_API_KEY"]):
        return 1

    print_section_header("Pull Prompt Do LangSmith")

    try:
        output_path = pull_prompt_from_langsmith(args.prompt_identifier, args.output)
    except Exception as exc:
        print(f"Erro ao fazer pull do prompt: {exc}")
        return 1

    print(f"Prompt salvo com sucesso em: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
