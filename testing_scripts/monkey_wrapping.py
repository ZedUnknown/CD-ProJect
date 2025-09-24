import os
import secrets
import json
import sys

# ================== WRAPPER ==================
user_id = "123"
chat_id = "abc"
extension = "rft"

folder = f"./mnt/data/user_files/{user_id}/{chat_id}"
os.makedirs(folder, exist_ok=True)
file_name = secrets.token_urlsafe(16) + "." + extension
final_path = os.path.join(folder, file_name)

# ---- DOCX (python-docx) ----
try:
    import docx
    original_docx_save = docx.document.Document.save
    def new_docx_save(self, path):
        return original_docx_save(self, final_path)
    docx.document.Document.save = new_docx_save
except Exception as e:
    raise RuntimeError("An error occurred in DOCX patch") from e

# ---- ODF family (odfpy: ods, odt, odp) ----
try:
    from odf.opendocument import OpenDocument
    original_odf_save = OpenDocument.save
    def new_odf_save(self, path):
        return original_odf_save(self, final_path)
    OpenDocument.save = new_odf_save
except Exception as e:
    raise RuntimeError("An error occurred in ODF patch") from e

# ---- PPTX (python-pptx) ----
try:
    import pptx
    original_pptx_save = pptx.presentation.Presentation.save
    def new_pptx_save(self, path):
        return original_pptx_save(self, final_path)
    pptx.presentation.Presentation.save = new_pptx_save
except Exception as e:
    raise RuntimeError("An error occurred in PPTX patch") from e

# ---- XLSX (openpyxl) ----
try:
    import openpyxl
    original_xlsx_save = openpyxl.workbook.workbook.Workbook.save
    def new_xlsx_save(self, path):
        return original_xlsx_save(self, final_path)
    openpyxl.workbook.workbook.Workbook.save = new_xlsx_save
except Exception as e:
    raise RuntimeError("An error occurred in XLSX patch") from e

# ---- PDF / CANVAS (reportlab, platypus) ----
try:
    from reportlab.platypus import SimpleDocTemplate
    from reportlab.pdfgen import canvas

    original_pdf_save = SimpleDocTemplate.__init__
    def new_pdf_save(self, path, *args, **kwargs):
        return original_pdf_save(self, final_path, *args, **kwargs)
    SimpleDocTemplate.__init__ = new_pdf_save

    original_canvas_save = canvas.Canvas.__init__
    def new_canvas_save(self, path, *args, **kwargs):
        return original_canvas_save(self, final_path, *args, **kwargs)
    canvas.Canvas.__init__ = new_canvas_save
except Exception as e:
    raise RuntimeError("An error occurred in PDF patch") from e

# ---- CSV (pandas) ----
try:
    import pandas as pd
    original_to_csv_save = pd.DataFrame.to_csv
    def new_to_csv_save(self, path_or_buf=None, *args, **kwargs):
        return original_to_csv_save(self, final_path, *args, **kwargs)
    pd.DataFrame.to_csv = new_to_csv_save
except Exception as e:
    raise RuntimeError("An error occurred in CSV patch") from e

# ---- RTF / TXT / MD (pypandoc) ----
# PAIN IN THE EYES, WHO MADE THIS MODULE??
try:
    import importlib, os, sys

    # Reload module to get a clean original implementation
    if "pypandoc" in sys.modules:
        importlib.reload(sys.modules["pypandoc"])
    import pypandoc

    # Ensure folder for final_path exists (defensive)
    os.makedirs(os.path.dirname(final_path), exist_ok=True)

    # Store the real original once (avoid capturing an already-patched function)
    if not hasattr(pypandoc, "_original_convert_text"):
        pypandoc._original_convert_text = pypandoc.convert_text
    original_convert_text = pypandoc._original_convert_text

    # Avoid double-patching
    if not getattr(pypandoc, "_is_patched_by_wrapper", False):

        def patched_convert_text(text, to, format="md", outputfile=None, extra_args=None):
            # Normalize extra_args to a list and ensure --standalone present
            args = list(extra_args) if extra_args else []
            if "--standalone" not in args:
                args.append("--standalone")

            # Ask the original to return the converted content (do NOT pass outputfile)
            # This avoids depending on Pandoc writing to disk itself.
            result = original_convert_text(
                text,
                to,
                format=format,
                outputfile=None,
                extra_args=args,
            )

            # If result is bytes/str, write it to final_path
            if isinstance(result, bytes):
                data = result
            elif isinstance(result, str):
                data = result.encode("utf-8")
            else:
                # fallback: coerce to string
                data = str(result).encode("utf-8")

            # Atomically write to disk (write to temp then rename) to be safer
            tmp_path = final_path + ".tmp"
            with open(tmp_path, "wb") as f:
                f.write(data)
            os.replace(tmp_path, final_path)  # atomic on most OSes

            # Verify file exists
            if not os.path.exists(final_path):
                raise RuntimeError(f"Failed to write pypandoc output to {final_path}")

            return result

        pypandoc.convert_text = patched_convert_text
        pypandoc._is_patched_by_wrapper = True

except ImportError:
    # pypandoc not available - skip patching
    pass
except Exception as e:
    raise RuntimeError(f"Pandoc patching failed: {str(e)}") from e

# ================== MODEL GENERATED CODE ==================
# (model-generated code will go here)

# ================== END MODEL GENERATED CODE ==================

if os.path.exists(final_path):
    print(json.dumps({"status": "ok", "file": final_path}))
else:
    print(json.dumps({"status": "error", "message": "file not created"}))
# ================== END WRAPPER ==================