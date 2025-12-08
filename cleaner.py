from bs4 import BeautifulSoup, Comment

def clean_html(html_content: str, max_length: int = 100000) -> str:
    """
    Cleans the HTML by removing scripts, styles, and other non-content elements.
    Truncates the result to max_length to save tokens.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove unwanted tags
    for tag in soup(["script", "style", "svg", "noscript", "iframe", "object", "embed", "meta", "link"]):
        tag.decompose()

    # Remove comments
    for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
        comment.extract()

    # Get the cleaned HTML string
    # prettify() might add too much whitespace, but it helps with structure. 
    # However, for LLM token efficiency, we might just want the structure without excessive whitespace.
    # Let's use str(soup) but maybe try to minimize it? 
    # Actually, keeping structure is good for the LLM to understand the DOM.
    cleaned_html = str(soup)

    # Simple truncation
    if len(cleaned_html) > max_length:
        cleaned_html = cleaned_html[:max_length] + "... (truncated)"

    return cleaned_html
