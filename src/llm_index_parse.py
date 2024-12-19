from src.llm import llm_call


async def llm_parse_index(index_text):
    prompt = """
    You are given a text from an index page of a document after OCR. 
    The index may have a hierarchical structure where parent terms are followed by subtopics. 
    Parent terms are identified by the presence of a colon (`:`) at the end of the line. 
    Subtopics are listed below the parent term and are associated with page numbers or ranges.

    Output the list of terms and their occurrences in JSON format. Ensure that each page occurrence is treated independently and is not merged with others. For instance, if a term appears as "Jewish, 129, 142-54, 157", this should generate separate occurrences for each page or range, such as 129, 142-154, and 157. 

    The JSON structure should look like this:
    [
        {{
            "t": "parent_term1",
            "o": [
                {{
                    "s": #some_number,
                    "e": #some_number
                }},
                {{
                    "s": #some_number,
                    "e": #some_number
                }}
            ]
        }},
        {{
            "t": "subtopic1 under parent_term1: this_term",
            "o": [
                {{
                    "s": #some_number,
                    "e": #some_number
                }},
                {{
                    "s": #some_number,
                    "e": #some_number
                }}
            ]
        }},
        ...
    ]

    Rules:
    1. If a page range includes only one page, represent it as both `start` and `end`.
    2. Subtopics should be prefixed with "subtopic under [parent term]" for clarity.
    3. Each occurrence of a page or page range must remain distinct and must not be merged.
    4. Ensure there is only one parent term for each hierarchy. Avoid nested parent terms (e.g., no parent1 -> parent2 -> child).
    5. If the input text does not resemble an index page, ignore it.

    The input text is:
    {index_text}

    """
    formatted_prompt = prompt.format(index_text=index_text)
    return await llm_call(formatted_prompt)
