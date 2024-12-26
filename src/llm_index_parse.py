from src.llm import llm_call


async def llm_parse_index(index_text):
    # Preprocess: Remove the quotation marks from the input text
    index_text = index_text.replace('"', '')

    prompt = """
    You are given a text from an index page of a document after OCR. 
    The index may have a hierarchical structure where parent terms are followed by subtopics. 
    Parent terms are identified by the presence of a colon (`:`) at the end of the line. 
    Subtopics are listed below the parent term and are associated with page numbers or ranges.

    Output the list of terms and their occurrences in JSON format. Use a **list of lists** format for occurrences instead of dictionaries. For example, an occurrence with a page range or single page should be represented as `[start, end]`. For multiple occurrences, use a single array of arrays, such as `[[start1, end1], [start2, end2]]`. Do not include unnecessary newlines or whitespace between elements in the list.

    The JSON structure should look like this:
    [
        {{"t": "parent_term1", "o": [[#start1, #end1], [#start2, #end2]]}},
        {{"t": "under parent_term1: this_term", "o": [[#start1, #end1], [#start2, #end2]]}},
        ...
    ]

    Rules:
    1. If a page range includes only one page, represent it as `[start, start]`.
    2. Subtopics should be prefixed with "under [parent term]".
    3. Each occurrence of a page or page range must remain distinct and must not be merged.
    4. Avoid writing newlines or extra whitespace between elements inside the occurrences list.
    5. Ensure there is only one parent term for each hierarchy. Avoid nested parent terms.
    6. Ignore the input if it does not resemble an index page.
    7. The text may contain misspellings or OCR errors, such as words being merged together (e.g., "wordstogetherlikethis") or spaced incorrectly (e.g., "w o r d s l i k e t h i s"). Correct these errors if appropriate.
    
    The input text is:
    {index_text}
    """
    formatted_prompt = prompt.format(index_text=index_text)
    return await llm_call(formatted_prompt)
