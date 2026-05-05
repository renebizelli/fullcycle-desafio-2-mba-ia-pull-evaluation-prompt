"""
Testes automatizados para validacao do prompt v2.
"""

from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).parent.parent
PROMPT_PATH = PROJECT_ROOT / "prompts" / "bug_to_user_story" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: Path):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class TestPrompts:
    prompt_data = load_prompts(PROMPT_PATH)[PROMPT_KEY]

    def test_prompt_has_system_prompt(self):
        """Verifica se o campo system_prompt existe e nao esta vazio."""
        assert "system_prompt" in self.prompt_data
        assert isinstance(self.prompt_data["system_prompt"], str)
        assert self.prompt_data["system_prompt"].strip()

    def test_prompt_has_role_definition(self):
        """Verifica se o prompt define uma persona."""
        system_prompt = self.prompt_data["system_prompt"].lower()

        assert "[persona" in system_prompt
        assert "voce" in system_prompt or "você" in system_prompt
        assert "product owner" in system_prompt
        assert "tecnico" in system_prompt or "técnico" in system_prompt or "tÃ©cnico" in system_prompt

    def test_prompt_mentions_format(self):
        """Verifica se o prompt exige o formato atual de user story."""
        system_prompt = self.prompt_data["system_prompt"].lower()

        assert "saida" in system_prompt or "saída" in system_prompt or "saÃ­da" in system_prompt
        assert "markdown" in system_prompt
        assert "como um" in system_prompt
        assert "eu quero" in system_prompt
        assert "para que" in system_prompt
        assert "criterios de aceitacao" in system_prompt or "critérios de aceitação" in system_prompt or "critÃ©rios de aceitaÃ§Ã£o" in system_prompt
        assert "dado que" in system_prompt
        assert "quando" in system_prompt
        assert "entao" in system_prompt or "então" in system_prompt or "entÃ£o" in system_prompt

    def test_prompt_has_few_shot_examples(self):
        """Verifica se o prompt contem exemplo de entrada/saida."""
        system_prompt = self.prompt_data["system_prompt"].lower()
        techniques = [technique.lower() for technique in self.prompt_data.get("techniques", [])]

        assert "exemplo de saida" in system_prompt or "exemplo de saída" in system_prompt
        assert "few shot prompting" in techniques

    def test_prompt_no_todos(self):
        """Garante que nao existe nenhum TODO no prompt."""
        system_prompt = self.prompt_data["system_prompt"]

        assert "[TODO]" not in system_prompt
        assert "TODO" not in system_prompt

    def test_minimum_techniques(self):
        """Verifica se pelo menos 2 tecnicas foram listadas no YAML."""
        techniques = self.prompt_data.get("techniques", [])

        assert isinstance(techniques, list)
        assert len(techniques) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
