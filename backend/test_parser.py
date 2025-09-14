from parser import save_clean_text

# Test with your sample docs
pdf_clean = save_clean_text("../data/raw/loan1.pdf")
print(f"✅ Clean text saved at: {pdf_clean}")

docx_clean = save_clean_text("../data/raw/lease1.docx")
print(f"✅ Clean text saved at: {docx_clean}")
