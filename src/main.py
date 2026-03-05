"""
Main entry point for recipe extraction from PDF files.

This script:
1. Reads all PDF files from the raw_pdfs directory
2. Uses an LLM (Ollama gemma3:4b) to split the text into individual recipes
3. Extracts NAME, DESCRIPTION, INGREDIENTS, and PROCEDURE for each recipe
4. Prints the formatted results

Usage:
    python -m src.main

Requirements:
    - PDF files must be placed in data/raw_pdfs/
    - Ollama must be running with gemma3:4b model installed
"""

from pathlib import Path
import os
from pypdf import PdfReader
from langchain_ollama import ChatOllama

# Import prompt from recipe_prompt module
from recipe_prompt import RECIPE_SPLIT_PROMPT

# Separator used to split recipe chunks in LLM output
RECIPE_SEPARATOR = "---SEPARATE_RECIPE---"


def read_pdfs_from_directory(directory: str) -> dict:
    """
    Read all PDF files from a directory and extract text content.

    Args:
        directory: Path to directory containing PDF files

    Returns:
        Dictionary with filename as key and extracted text as value.
        If an error occurs, the value contains the error message.
    """
    pdf_dir = Path(directory)
    results = {}
    
    # Iterate over all PDF files in the directory
    for pdf_path in pdf_dir.glob("*.pdf"):
        try:
            reader = PdfReader(str(pdf_path))
            text = ""
            
            # Extract text from each page
            for page in reader.pages:
                text += page.extract_text() + "\n"
            
            results[pdf_path.name] = text
        except Exception as e:
            results[pdf_path.name] = f"Error: {str(e)}"
    
    return results


def split_into_recipes(llm, text: str) -> list:
    """
    Use LLM to split raw PDF text into individual recipes.

    The LLM is prompted to extract:
    - NAME: Recipe name
    - DESCRIPTION: Brief description (2-3 sentences)
    - INGREDIENTS: List of required ingredients
    - PROCEDURE: Numbered preparation steps

    Args:
        llm: LangChain Ollama LLM instance
        text: Raw PDF text containing one or more recipes

    Returns:
        List of recipe strings, each formatted according to the prompt template
    """
    # Format prompt with the PDF text
    prompt = RECIPE_SPLIT_PROMPT.format(pdf_text=text)
    
    # Invoke LLM to process the text
    response = llm.invoke(prompt)
    
    # Split response by separator to get individual recipes
    recipes = response.content.split(RECIPE_SEPARATOR)
    
    # Filter out empty strings
    return [r.strip() for r in recipes if r.strip()]


def main():
    """
    Main execution function.

    Reads PDFs from data/raw_pdfs, processes each with the LLM,
    and prints the extracted recipes.
    """
    # Define path to raw_pdfs directory 
    pdf_dir = Path(__file__).resolve().parent.parent / "data" / "raw_pdfs"
    print(f"Looking in: {pdf_dir}")
    
    # Read all PDFs from the directory
    pdfs = read_pdfs_from_directory(str(pdf_dir))
    print(f"Found: {list(pdfs.keys())}")

    # Initialize Ollama LLM with gemma3:4b model
    ollama_base_url = os.getenv("OLLAMA_BASE_URL")
    llm_kwargs = {"model": "gemma3:4b"}
    if ollama_base_url:
        llm_kwargs["base_url"] = ollama_base_url
    llm = ChatOllama(**llm_kwargs)

    # Process each PDF file
    for filename, content in pdfs.items():
        print(f"Processing: {filename}\n")

        # Handle PDF reading errors
        if content.startswith("Error:"):
            print(content)
            continue

        print("Splitting into recipes...")
        
        # Extract individual recipes using LLM
        recipes = split_into_recipes(llm, content)

        print(f"Found {len(recipes)} recipes\n")

        # Print each recipe with formatting
        for i, recipe in enumerate(recipes, 1):
            print(f"{'='*60}")
            print(f"RECIPE {i}")
            print(f"{'='*60}")
            print(recipe)
            print()


if __name__ == "__main__":
    main()
