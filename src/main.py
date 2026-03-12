from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path

from langchain_ollama import ChatOllama
from pypdf import PdfReader

try:
    from .prompt import RECIPE_SPLIT_PROMPT, SQL_RECIPE_BLOCK_PROMPT
except ImportError:
    from prompt import RECIPE_SPLIT_PROMPT, SQL_RECIPE_BLOCK_PROMPT


RECIPE_SEPARATOR = "---SEPARATE_RECIPE---"
SQL_HEADER = "USE ricettario;"
DEFAULT_MODEL_NAME = "gemma3:4b"
DEFAULT_OUTPUT_FILENAME = "insert_recipes.sql"


@dataclass(frozen=True)
class AppConfig:
    """Runtime configuration for the PDF-to-SQL pipeline."""

    project_root: Path
    pdf_dir: Path
    schema_path: Path
    output_path: Path
    model_name: str
    ollama_base_url: str | None


def load_config() -> AppConfig:
    """Build runtime configuration from project paths and environment."""
    project_root = Path(__file__).resolve().parent.parent
    return AppConfig(
        project_root=project_root,
        pdf_dir=project_root / "data" / "raw_pdfs",
        schema_path=project_root / "db" / "schema" / "create.sql",
        output_path=project_root / "db" / "seed" / DEFAULT_OUTPUT_FILENAME,
        model_name=os.getenv("OLLAMA_MODEL", DEFAULT_MODEL_NAME),
        ollama_base_url=os.getenv("OLLAMA_BASE_URL"),
    )


def ensure_required_paths(config: AppConfig) -> None:
    """Fail fast when required input paths are missing."""
    if not config.pdf_dir.exists():
        raise FileNotFoundError(f"PDF directory not found: {config.pdf_dir}")
    if not config.schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {config.schema_path}")


def read_pdfs_from_directory(directory: Path) -> dict[str, str]:
    """Read all PDFs in a directory and return extracted text by filename."""
    results: dict[str, str] = {}

    for pdf_path in sorted(directory.glob("*.pdf")):
        try:
            reader = PdfReader(str(pdf_path))
            pages = [page.extract_text() or "" for page in reader.pages]
            results[pdf_path.name] = "\n".join(pages).strip()
        except Exception as exc:
            results[pdf_path.name] = f"Error: {exc}"

    return results


def create_llm(config: AppConfig) -> ChatOllama:
    """Create the Ollama chat client used by the pipeline."""
    llm_kwargs = {
        "model": config.model_name,
        "temperature": 0,
    }
    if config.ollama_base_url:
        llm_kwargs["base_url"] = config.ollama_base_url
    return ChatOllama(**llm_kwargs)


def split_into_recipes(llm: ChatOllama, text: str) -> list[str]:
    """Use the LLM to split raw PDF text into structured recipes."""
    prompt = RECIPE_SPLIT_PROMPT.format(pdf_text=text)
    response = llm.invoke(prompt)
    content = getattr(response, "content", "")
    return [chunk.strip() for chunk in content.split(RECIPE_SEPARATOR) if chunk.strip()]


def sanitize_sql_output(sql_text: str) -> str:
    """Remove wrappers the model may add and normalize the SQL block."""
    cleaned = sql_text.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    lines: list[str] = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue
        if stripped.lower() == SQL_HEADER.lower():
            continue
        lines.append(line.rstrip())

    return "\n".join(lines).strip()


def generate_recipe_sql_block(llm: ChatOllama, recipe_text: str, schema_sql: str) -> str:
    """Generate the SQL block for a single structured recipe."""
    prompt = SQL_RECIPE_BLOCK_PROMPT.format(
        schema_sql=schema_sql,
        recipe_text=recipe_text,
    )
    response = llm.invoke(prompt)
    content = getattr(response, "content", "")
    return sanitize_sql_output(content)


def collect_structured_recipes(llm: ChatOllama, pdf_texts: dict[str, str]) -> list[tuple[str, str]]:
    """Extract structured recipes from all PDFs."""
    structured_recipes: list[tuple[str, str]] = []

    for filename, content in pdf_texts.items():
        print(f"Processing PDF: {filename}")

        if content.startswith("Error:"):
            print(f"  {content}")
            continue

        recipes = split_into_recipes(llm, content)
        print(f"  Extracted recipes: {len(recipes)}")

        for index, recipe in enumerate(recipes, start=1):
            structured_recipes.append((f"{filename}#{index}", recipe))

    return structured_recipes


def summarize_pdf_results(pdf_texts: dict[str, str]) -> tuple[int, int]:
    """Return counts for readable PDFs and read failures."""
    successful = sum(1 for content in pdf_texts.values() if not content.startswith("Error:"))
    failed = len(pdf_texts) - successful
    return successful, failed


def build_seed_sql(
    llm: ChatOllama,
    structured_recipes: list[tuple[str, str]],
    schema_sql: str,
) -> str:
    """Generate the final SQL seed file content."""
    sql_blocks = [SQL_HEADER, ""]

    for source_label, recipe_text in structured_recipes:
        print(f"Generating SQL block: {source_label}")
        sql_block = generate_recipe_sql_block(llm, recipe_text, schema_sql)

        if not sql_block:
            raise ValueError(f"Empty SQL block generated for {source_label}")

        sql_blocks.append(sql_block)
        sql_blocks.append("")

    return "\n".join(sql_blocks).strip() + "\n"


def write_seed_file(output_path: Path, sql_content: str) -> None:
    """Write the generated SQL seed file to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(sql_content, encoding="utf-8")


def main() -> None:
    """Read recipe PDFs, extract recipes, and generate the SQL seed file."""
    config = load_config()
    ensure_required_paths(config)

    print(f"Reading PDFs from: {config.pdf_dir}")
    pdfs = read_pdfs_from_directory(config.pdf_dir)
    print(f"PDF files found: {len(pdfs)}")

    if not pdfs:
        raise RuntimeError(f"No PDF files found in {config.pdf_dir}")

    readable_pdfs, failed_pdfs = summarize_pdf_results(pdfs)
    print(f"Readable PDFs: {readable_pdfs} | Failed PDFs: {failed_pdfs}")

    llm = create_llm(config)
    print(f"Using model: {config.model_name}")

    schema_sql = config.schema_path.read_text(encoding="utf-8")
    structured_recipes = collect_structured_recipes(llm, pdfs)
    print(f"Total structured recipes: {len(structured_recipes)}")

    if not structured_recipes:
        raise RuntimeError("No recipes extracted from the PDFs.")

    seed_sql = build_seed_sql(llm, structured_recipes, schema_sql)
    write_seed_file(config.output_path, seed_sql)

    print(f"SQL seed file created: {config.output_path}")


if __name__ == "__main__":
    main()
