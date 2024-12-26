import fitz
import os
from tqdm import tqdm

path = "./resource/pdf/extract_image.pdf"
workdir = "./images"

pdf_document = fitz.open(path)
page_number = 502
page = pdf_document.load_page(page_number)
image_list = page.get_images(full=True)

print(image_list)

for img in tqdm(page.get_images(full=True), desc="Extracting images"):
    xref = img[0]
    image = pdf_document.extract_image(xref)
    pix = fitz.Pixmap(pdf_document, xref)
    if pix.n < 5:  # this is GRAY or RGB
        pix.save(os.path.join(workdir, "p%s-%s.png" % (page_number, xref)))
    else:  # CMYK: convert to RGB first
        pix1 = fitz.Pixmap(fitz.csRGB, pix)
        pix1.save(os.path.join(workdir, "p%s-%s.png" % (page_number, xref)))
        pix1 = None
    pix = None