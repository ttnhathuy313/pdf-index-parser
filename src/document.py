import fitz
import re
from utils.analyze_bboxes import is_two_vertical_blocks
from src.llm_index_parse import llm_parse_index
import json
from collections import Counter
import asyncio
import time
import json_repair

# TODO: Put this in the utils file
class RateLimiter:
    def __init__(self, max_calls, period):
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    async def acquire(self):
        while len(self.calls) >= self.max_calls:
            await asyncio.sleep(self.period - (time.time() - self.calls[0]))
            self.calls = [call for call in self.calls if time.time() - call < self.period]
        self.calls.append(time.time())

class Index:
    def __init__(self, term, occurrences_list):
        self.term = term
        self.occurrences = occurrences_list  # List of tuples (start, end)


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
        self.index_page_text = ""

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
                match = re.search(r'\d+[\s|\n]*$', text)
                if match:
                    self.page_number_difference_list.append(page_number - int(match.group(0)))
                
                # An index page should have at least 10 numbers
                # Find the number of matches using a regular expression \d+
                match_count = len(re.findall(r"\d+", text))
                if match_count <= 10:
                    continue
                # Simple regex to match index entries
                pattern = r"^[^,]+,\s*\d+"
                matches = re.findall(pattern, text, re.MULTILINE)
                if ("index" in text[:100].lower()):
                    self.add_index_page(page_number)
                    continue
                if (len(matches) < 10):
                    continue
                self.add_index_page(page_number)
        if self.page_number_difference_list:
            self.page_difference = Counter(self.page_number_difference_list).most_common(1)[0][0]
        # Only keep the longest consecutive sequence of index pages
        if self.index_pages:
            longest_sequence = [self.index_pages[0]]
            current_sequence = [self.index_pages[0]]
            for i in range(1, len(self.index_pages)):
                if self.index_pages[i] == self.index_pages[i - 1] + 1:
                    current_sequence.append(self.index_pages[i])
                else:
                    if len(current_sequence) > len(longest_sequence):
                        longest_sequence = current_sequence
                    current_sequence = [self.index_pages[i]]
            if len(current_sequence) > len(longest_sequence):
                longest_sequence = current_sequence
            with fitz.open(self.path) as pdf:
                # The begin of the index sequence should contain the word
                # "index" in the first 10 lines
                while (True):
                    if (len(longest_sequence) == 0):
                        break
                    page = pdf.load_page(longest_sequence[0] - 1)
                    text = page.get_text("text")[:100]
                    if "index" in text.lower():
                        break
                    longest_sequence = longest_sequence[1:]
            self.index_pages = longest_sequence

        else:
            print("No index pages found.")

    async def extract_page_text(self, pdf, page_number):
        page = pdf.load_page(page_number - 1)
        return page.get_text("text")

    async def parse_index_pages(self):
        self.index_page_text = ""
        with fitz.open(self.path) as pdf:
            tasks = [self.extract_page_text(pdf, page_number) for page_number in self.index_pages]

            # Run all tasks concurrently
            extracted_texts = await asyncio.gather(*tasks)
            self.index_page_text = "".join(extracted_texts)

        # Call the asynchronous parse_index method
        await self.parse_index(self.index_page_text)

    async def parse_index(self, text):
        chunks = list(self.split_text_into_chunks(text))
        print("Number of chunks:", len(chunks))
        
        semaphore = asyncio.Semaphore(10)  # Limit to 10 concurrent tasks
        rate_limiter = RateLimiter(15, 60)

        async def sem_process_chunk(chunk):
            async with semaphore:
                await rate_limiter.acquire()
                return await self.process_chunk(chunk)

        tasks = [sem_process_chunk(chunk) for chunk in chunks]
        results = await asyncio.gather(*tasks)
        
        # Process results in order
        for result in results:
            for entry in result:
                self.add_index(entry.term, entry.occurrences)
    
    def split_text_into_chunks(self, text, lines_per_chunk=120):
        lines = text.splitlines()
        for i in range(0, len(lines), lines_per_chunk):
            yield "\n".join(lines[i:i + lines_per_chunk])

    async def process_chunk(self, text):
        index = await llm_parse_index(text)
        results = []
        if index.startswith("```json"):
            index = index[len("```json"):].strip()
        if index.endswith("```"):
            index = index[:-len("```")].strip()
        try:
            parsed_index = json_repair.loads(index)
            for entry in parsed_index:
                term = entry["t"]
                occurrences = entry["o"]
                occurrences_list = []
                for occurrence in occurrences:
                    try:
                        if (len(occurrence) == 1):
                            start = occurrence[0]
                            end = occurrence[0]
                        else:
                            start = occurrence[0]
                            end = occurrence[1]
                        occurrences_list.append((start, end))
                    except Exception as e:
                        print(f"Error parsing occurrence: {e}, occurrence: {occurrence}")
                results.append(Index(term, occurrences_list))
        except json.JSONDecodeError as e:
            print(index)
            print(f"JSONDecodeError: {e}")

        return results

if __name__ == "__main__":
    doc = Document("pdf", "./resource/pdf/irrational.pdf")
    doc.filter_index_pages()
    doc.parse_index_pages()
    # for index in doc.original_index:
    #     print(f"{index.term}: {index.occurrences}")

