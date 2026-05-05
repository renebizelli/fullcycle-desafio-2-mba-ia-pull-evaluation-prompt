"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Le os prompts otimizados de prompts/bug_to_user_story/
2. Valida os prompts
3. Converte o YAML local em ChatPromptTemplate
4. Faz push para o LangSmith Hub com metadados
"""

import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client
from utils import check_env_vars, load_yaml, print_section_header

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROMPT_DIR = PROJECT_ROOT / "prompts/bug_to_user_story"
PROMPT_NAME = "bug_to_user_story_v2"


def build_chat_prompt(prompt_config: dict[str, Any]) -> ChatPromptTemplate:
    system_prompt = prompt_config["system_prompt"].strip()
    user_prompt = prompt_config.get("user_prompt", "{bug_report}").strip()

    messages = [("system", system_prompt)]
    if user_prompt:
        messages.append(("human", user_prompt))

    return ChatPromptTemplate.from_messages(messages)


def validate_prompt(prompt_data: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Valida a estrutura basica do prompt local.
    """
    errors = []

    if not isinstance(prompt_data, dict):
        return False, ["Conteudo do prompt deve ser um dicionario."]

    system_prompt = prompt_data.get("system_prompt", "")
    if not isinstance(system_prompt, str) or not system_prompt.strip():
        errors.append("Campo obrigatorio faltando ou vazio: system_prompt")

    user_prompt = prompt_data.get("user_prompt", "{bug_report}")
    if user_prompt is not None and not isinstance(user_prompt, str):
        errors.append("Campo user_prompt deve ser texto.")

    return len(errors) == 0, errors


def build_prompt_tags(prompt_config: dict[str, Any]) -> list[str]:
    tags = list(prompt_config.get("tags", []))
    version = prompt_config.get("version")

    if version:
        tags.append(f'{str(version)}1.0')

    return tags

def build_prompt_commit_tags(prompt_config: dict[str, Any]) -> list[str]:
    tags = list()
    version = prompt_config.get("version")

    if version:
        tags.append(f'{str(version)}')

    return tags


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict[str, Any]) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub.
    """
    try:
        prompt_config = prompt_data[prompt_name]
        is_valid, errors = validate_prompt(prompt_config)

        if not is_valid:
            raise ValueError("Prompt invalido: " + "; ".join(errors))
        
        url = Client().push_prompt(
            prompt_name,
            is_public=True,
            commit_tags=build_prompt_commit_tags(prompt_config),
            object=build_chat_prompt(prompt_config),
            tags=build_prompt_tags(prompt_config),
            description=prompt_config.get("description")
        )

        # print(f"Prompt '{prompt_name}' pushado com sucesso! URL: {url}")
        return True

    except Exception as exc:
        print(f"Erro ao fazer push do prompt: {exc}")
        return False


def main() -> int:
    print_section_header("Push Prompt para o LangSmith")

    if not check_env_vars(["LANGSMITH_API_KEY", "LANGSMITH_ENDPOINT", "LANGSMITH_PROJECT", "OPENAI_API_KEY"]):
        return 1

    prompt_path = PROMPT_DIR / f"{PROMPT_NAME}.yml"
    prompt = load_yaml(prompt_path)
    if not prompt:
        print(f"Erro ao carregar prompt: {prompt_path}")
        return 1

    result = push_prompt_to_langsmith(PROMPT_NAME, prompt)

    if not result:
        print("Erro ao realizar push do prompt")
        return 1

    print("Push realizado com sucesso")
    return 0


if __name__ == "__main__":
    sys.exit(main())
