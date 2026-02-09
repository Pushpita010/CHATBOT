import os
import mimetypes
from PyPDF2 import PdfReader
from docx import Document
import openpyxl

def extract_text_from_file(filepath):
	"""
	Extract text from PDF, Word (.docx), or Excel (.xlsx) files.
	"""
	ext = os.path.splitext(filepath)[1].lower()
	if ext == '.pdf':
		return extract_text_from_pdf(filepath)
	elif ext == '.docx':
		return extract_text_from_docx(filepath)
	elif ext == '.xlsx':
		return extract_text_from_xlsx(filepath)
	else:
		raise ValueError(f"Unsupported file type: {ext}")

def extract_text_from_pdf(filepath):
	text = []
	with open(filepath, 'rb') as f:
		reader = PdfReader(f)
		for page in reader.pages:
			text.append(page.extract_text() or '')
	return '\n'.join(text)

def extract_text_from_docx(filepath):
	doc = Document(filepath)
	text = [para.text for para in doc.paragraphs]
	return '\n'.join(text)

def extract_text_from_xlsx(filepath):
	wb = openpyxl.load_workbook(filepath, data_only=True)
	text = []
	for sheet in wb.worksheets:
		for row in sheet.iter_rows(values_only=True):
			row_text = [str(cell) if cell is not None else '' for cell in row]
			text.append('\t'.join(row_text))
	return '\n'.join(text)
