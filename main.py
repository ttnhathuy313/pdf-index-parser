import tkinter as tk
from tkinter import filedialog, ttk, messagebox, Toplevel
import threading
import fitz  # PyMuPDF
from src.document import Document
from ctypes import windll
windll.shcore.SetProcessDpiAwareness(1)

class PDFIndexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Index Processor")
        
        # File selection
        self.file_label = tk.Label(root, text="Select a PDF File:")
        self.file_label.pack(pady=5)
        
        self.file_button = tk.Button(root, text="Browse", command=self.select_file)
        self.file_button.pack(pady=5)
        
        self.file_path = tk.StringVar()
        self.file_entry = tk.Entry(root, textvariable=self.file_path, width=50, state="readonly")
        self.file_entry.pack(pady=5)
        
        # Progress bar and logs
        self.progress = ttk.Progressbar(root, orient="horizontal", mode="indeterminate")
        self.progress.pack(fill=tk.X, padx=10, pady=10)
        
        self.log_text = tk.Text(root, height=10, state="disabled")
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Results section
        self.results_frame = tk.Frame(root)
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.results_label = tk.Label(self.results_frame, text="Index Results:")
        self.results_label.pack(anchor="w")
        
        self.results_list = tk.Listbox(self.results_frame, height=15)
        self.results_list.pack(fill=tk.BOTH, expand=True)
        self.results_list.bind("<<ListboxSelect>>", self.display_index_pages)
        
        # Page number selection
        self.page_number_frame = tk.Frame(root)
        self.page_number_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.page_number_label = tk.Label(self.page_number_frame, text="Page Numbers:")
        self.page_number_label.pack(anchor="w")
        
        self.page_number_list = tk.Listbox(self.page_number_frame, height=15)
        self.page_number_list.pack(fill=tk.BOTH, expand=True)
        self.page_number_list.bind("<<ListboxSelect>>", self.display_page_text_popup)
        
        # Document instance
        self.document = None
        self.index_results = []
        self.selected_index = None
        self.page_difference = 0
        
    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if file_path:
            self.file_path.set(file_path)
            self.start_processing(file_path)
    
    def start_processing(self, file_path):
        self.log("Processing started...")
        self.progress.start()
        threading.Thread(target=self.process_pdf, args=(file_path,)).start()
    
    def process_pdf(self, file_path):
        try:
            self.document = Document(doc_type="pdf", path=file_path)
            self.document.filter_index_pages()
            self.log("Index pages found: " + ", ".join(map(str, self.document.index_pages)))
            self.log("The page difference seems to be: " + str(self.document.page_difference))
            self.log("Parsing index pages...")
            self.document.parse_index_pages()
            self.index_results = self.document.original_index
            self.update_results()
        except Exception as e:
            self.log(f"Error: {e}")
        finally:
            self.progress.stop()
            self.log("Processing complete.")
    
    def update_results(self):
        self.results_list.delete(0, tk.END)
        for idx, index in enumerate(self.index_results):
            self.results_list.insert(tk.END, f"{index.term} ({len(index.occurrences)} occurrences)")
        self.log(f"Loaded {len(self.index_results)} indices.")
    
    def display_index_pages(self, event):
        selection = self.results_list.curselection()
        if not selection:
            return
        selected_index = selection[0]
        self.selected_index = self.index_results[selected_index]
        self.update_page_numbers()
    
    def update_page_numbers(self):
        self.page_number_list.delete(0, tk.END)
        if self.selected_index:
            for start, end in self.selected_index.occurrences:
                for page_number in range(start, end + 1):
                    self.page_number_list.insert(tk.END, page_number)
    
    def display_page_text_popup(self, event):
        selection = self.page_number_list.curselection()
        if not selection:
            return
        selected_page = int(self.page_number_list.get(selection[0]))
        self.load_page_text_popup(selected_page)
    
    def load_page_text_popup(self, page_number):
        with fitz.open(self.file_path.get()) as pdf:
            page = pdf[page_number + self.document.page_difference - 1]  # Pages are 0-indexed in PyMuPDF
            text = page.get_text("text")
            self.show_text_popup(text)
    
    def show_text_popup(self, text):
        popup = Toplevel(self.root)
        popup.title(f"Page {int(self.page_number_list.get(self.page_number_list.curselection()))} Text")
        popup.geometry("2200x1500")
        
        text_label = tk.Label(popup, text="Page Text:")
        text_label.pack(anchor="w", padx=10, pady=5)
        
        text_area = tk.Text(popup, height=30, width=100, wrap=tk.WORD)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(tk.END, text)
        text_area.config(state="disabled")
        
        close_button = tk.Button(popup, text="Close", command=popup.destroy)
        close_button.pack(pady=10)
    
    def log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

# Run the application
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFIndexApp(root)
    root.mainloop()