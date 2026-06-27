import asyncio
import pymupdf
import pymupdf4llm

def to_markdown(doc, **kwargs):
    """
    Synchronous wrapper to convert document/file to markdown using pymupdf4llm.
    """
    return pymupdf4llm.to_markdown(doc, **kwargs)

async def extract_pdf_to_markdown(filepath: str) -> str:
    """
    Asynchronously extracts PDF content to Markdown using a thread pool.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: pymupdf4llm.to_markdown(filepath))
