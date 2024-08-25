# FactureFacile (Invoice Processing Tool)

### Description
This project is an invoice processing tool that automates the extraction of important information from scanned or digital invoices. The tool uses OCR (Optical Character Recognition) and various Python libraries to identify, extract, and validate the text within invoices. Additionally, it offers translation capabilities and provides a user-friendly interface to correct and confirm the extracted data.

This is a group project developed by Avrile Floro, Aude Hennino, and Maxime Bronny.

### Features
- **OCR Integration:** Uses Tesseract for text recognition in images.
- **Data Extraction:** Automatically extracts key information such as invoice number, date, total amount, and line items.
- **Translation Support:** Integrates with DeepL API for translating the extracted text.
- **User Interface:** Provides an interactive UI for verifying and correcting the extracted data.
- **Database Management:** Saves and retrieves invoice data from a MySQL database.
- **Pattern Matching:** Includes regex pattern matching for data validation.

### Files Overview
- **`bdd_SQL.py`:** Handles the database interactions using MySQL.
- **`config.py`:** Contains configuration settings such as API keys and database credentials (not public)
- **`openai_deepl.py`:** Implements the translation functionality using DeepL API.
- **`pattern_matcher.py`:** Manages regex pattern matching for text validation.
- **`rapidAPI.py`:** Integrates with external APIs for additional functionality.
- **`tesseract.py`:** Handles OCR processing using Tesseract.
- **`UI.py`:** Provides the graphical user interface for user interaction.

### Usage
1. **Upload an Invoice:**
    - Use the UI to upload an image or PDF of an invoice.
  
2. **Verify and Correct:**
    - The tool will automatically extract text. You can draw rectangles around areas of text if manual corrections are needed.
  
3. **Translate (Optional):**
    - Translate the extracted text if required.
  
4. **Save to Database:**
    - Once validated, save the invoice data to the MySQL database.

### Dependencies
- Python > 3.10
- Tesseract OCR
- MySQL
- PyTesseract
- Tkinter
- Pillow
- DeepL API
- OpenAI API

### Authors
- Avrile Floro
- Aude Hennino
- Maxime Bronny
