import fitz
import re
from utils.analyze_bboxes import is_two_vertical_blocks

class Index:
    def __init__(self, term, occurrences_list):
        self.term = term
        self.occurrences = self.parse_occurrences(occurrences_list)  # List of tuples (start, end)
    
    def parse_occurrences(self, occurrences_list):
        occurrences = []
        for occ in occurrences_list:
            # Use regex to split by non-numeric characters
            parts = re.split(r'\D+', occ)  # Split on any non-digit character
            parts = list(filter(None, parts))  # Remove empty strings from the list

            if len(parts) == 2:  # If we have a range (e.g., 44-45, 12~14, 98—107)
                start, end = map(int, parts)
                occurrences.append((start, end))
            elif len(parts) == 1:  # Single page number
                occurrences.append((int(parts[0]), int(parts[0])))

        return occurrences

class Document:
    def __init__(self, doc_type, path):
        if doc_type not in ["pdf", "epub"]:
            raise ValueError("Document type must be either 'pdf' or 'epub'")
        self.doc_type = doc_type
        self.path = path
        self.original_index = []  # List of Index instances
        self.potential_index_pages = []  # List of page numbers
        self.index_pages = []  # List of page numbers
        self.page_number_difference_list = []
        self.page_difference = 0

    def add_index(self, term, occurrences):
        self.original_index.append(Index(term, occurrences))

    def add_index_page(self, page_number):
        self.index_pages.append(page_number)

    def add_potential_index_page(self, page_number):
        self.potential_index_pages.append(page_number)
    
    def filter_index_pages(self):
        if (len(self.index_pages) > 0):
            return
        with fitz.open(self.path) as pdf:
            for page_number, page in enumerate(pdf, start=1):
                text = page.get_text("text")

                # If the text starts with a number or ends with a number, it's likely the page number
                if (re.match(r'^\d', text)):
                    current_internal_page_number = re.match(r'\d+', text).group(0)
                    self.page_number_difference_list.append(page_number - int(current_internal_page_number))
                if (re.search(r'\d$', text)):
                    self.page_number_difference_list.append(page_number - int(re.search(r'\d+$', text).group(0)))
                
                # An index page should have at least 10 numbers
                # Find the number of matches using a regular expression \d+
                match_count = len(re.findall(r"\d+", text))
                if match_count <= 10:
                    continue
                if (not is_two_vertical_blocks(page)):
                    continue
                self.add_index_page(page_number)
        # Use median to get the page difference
        self.page_difference = sorted(self.page_number_difference_list)[len(self.page_number_difference_list) // 2]
    
    def parse_index_pages(self):
        with fitz.open(self.path) as pdf:
            for page_number in self.index_pages:
                page = pdf[page_number - 1]
                text = page.get_text("text")
                self.parse_index(text)
    
    def parse_index(self, text):
        # Step 1: Preprocess text to handle multi-line entries
        # Merge lines if the next line starts with a number or hyphen (continuing occurrences)
        lines = text.split('\n')
        merged_lines = []
        buffer = ""

        for line in lines:
            line = line.strip()
            if not line:  # Skip empty lines
                continue
            if re.match(r'^\d', line) or re.match(r'^\s*\d', line):  # Line starts with a number (continuation)
                buffer += " " + line  # Append to the previous buffer
            else:
                if buffer:  # Save the previous buffer if it exists
                    merged_lines.append(buffer)
                buffer = line  # Start a new entry
        if buffer:  # Add the last buffer
            merged_lines.append(buffer)
        # Step 2: Extract terms and their occurrences
        entries = []
        pattern = r'^(.*?),\s([\d,\-\s—~]+(?:,\s?\d+)?)$'

        for line in merged_lines:
            match = re.match(pattern, line)
            if match:
                term = match.group(1).strip()  # Capture the term
                occurrences = match.group(2).strip()  # Capture the occurrences
                # Convert occurrences into a list, splitting by commas and spaces
                occurrences_list = [occ.strip() for occ in re.split(r',\s*', occurrences)]
                entries.append((term, occurrences_list))
                self.add_index(term, occurrences_list)

        return entries


