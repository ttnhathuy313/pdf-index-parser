import fitz  # PyMuPDF
import re
from utils.multi_column import column_boxes

def extract_first_lines(text, num_lines=5):
    """Extract the first few lines from the text."""
    lines = text.split('\n')
    return '\n'.join(lines[:num_lines])

def parse_page_numbers(page_numbers_str):
    """Parse page numbers, including ranges like '182-4'."""
    page_numbers = []
    parts = page_numbers_str.split(',')
    for part in parts:
        part = part.strip()
        if part:
            if '-' in part:
                start, end = part.split('-')
                start = int(start.strip())
                end = int(end.strip()) + start if len(end.strip()) < 3 else int(end.strip())
                page_numbers.extend(range(start, end + 1))
            else:
                try:
                    page_numbers.append(int(part.strip()))
                except ValueError:
                    print(f"Warning: Invalid page number '{part.strip()}' found.")
    return page_numbers

def is_two_column(page):
    # Get the text blocks
    text_instances = page.get_text("dict")["blocks"]
    
    # Filter out text blocks
    text_blocks = [block for block in text_instances if block['type'] == 0]
    
    if not text_blocks:
        return False
    
    # Extract x-coordinates of the first and last lines of each block
    x_coords = []
    for block in text_blocks:
        lines = block['lines']
        if lines:
            first_line = lines[0]
            last_line = lines[-1]
            x_coords.append(first_line['bbox'][0])  # x0 of the first line
            x_coords.append(last_line['bbox'][2])   # x2 of the last line
    
    # Sort the x-coordinates
    x_coords.sort()
    
    # Find the median x-coordinate
    median_x = x_coords[len(x_coords) // 2]
    
    # Count how many lines are on the left and right of the median
    left_count = sum(1 for x in x_coords if x < median_x)
    right_count = sum(1 for x in x_coords if x > median_x)
    
    # If the difference is significant, it's likely two columns
    return abs(left_count - right_count) > len(x_coords) * 0.2

def extract_index(pdf_path):
    with fitz.open(pdf_path) as pdf:
        index_pages = []
        index_text = ""
        
        # Search for the index page(s)
        for page_number, page in enumerate(pdf, start=1):
            text = page.get_text("text")
            if (page_number==254):
                print(text)
            if text:
                first_lines = extract_first_lines(text)
                if "Index" in first_lines or "Indexes" in first_lines:
                    bboxes = column_boxes(page, no_image_text=False)
                    # print(bboxes)
                    # for rect in bboxes:
                    #     print(page.get_text(clip=rect, sort=True))
                    # print("-" * 80)
                    index_pages.append(page_number)
                    index_text += page.get_text("text", sort=True)
        
        # Extract terms and page numbers from the index pages
        terms = {}
        lines = index_text.split('\n')
        
        current_term = None
        for i, line in enumerate(lines):
            line = line.strip()
            if line:
                # Check if the line contains a term and page numbers
                if re.search(r'\d+$', line) or re.search(r'\d+-\d+', line):
                    # Handle multi-column layout: combine lines
                    if current_term:
                        parts = line.rsplit(maxsplit=1)
                        if len(parts) == 2:
                            term_part, page_numbers_str = parts
                            term_part = term_part.strip()
                            if term_part:
                                current_term += " " + term_part
                            page_numbers = parse_page_numbers(page_numbers_str)
                            terms[current_term.strip()] = page_numbers
                            current_term = None
                    else:
                        parts = line.rsplit(maxsplit=1)
                        if len(parts) == 2:
                            term, page_numbers_str = parts
                            page_numbers = parse_page_numbers(page_numbers_str)
                            terms[term.strip()] = page_numbers
                else:
                    # Handle multi-column layout: continue term
                    if current_term:
                        current_term += " " + line
                    else:
                        current_term = line
        
        return terms
# Example usage
pdf_path = './resource/pdf/test.pdf'
index_terms = extract_index(pdf_path)
# for term, pages in index_terms.items():
#     print(f"{term}: {pages}")