"""
title: CD ProJect
author: Zed Unknown
author_url: https://github.com/ZedUnknown
description: Create Documents from Python + Jupyter
requirements:
version: 1.0.0
licence: MIT
"""

"""
Critical Error codes:
18854: user_id is missing or chat_id is missing
"""

from pydantic import BaseModel, Field
from datetime import datetime
import websocket
import requests
import textwrap
import asyncio
import logging
import uuid
import json
import time
import sys


class Tools:
    def __init__(self):
        """
        initialize the document generator tool
        """
        self.valves = self.Valves()

    class Valves(BaseModel):
        """
        configurable settings
        """
        JUPYTER_URL: str = Field(
            default="http://localhost:8888",
            description="URL of the Jupyter backend",
        )
        JUPYTER_TOKEN: str = Field(
            default="JUPYTER_TOKEN",
            description="Token for Jupyter authentication",
        )
        BASE_DOWNLOAD_URL: str = Field(
            default="https://your.domain.com/backend-api/files/download",
            description="Base URL for file downloads",
        )
        ENABLE_DEBUG: bool = Field(
            default=False,
            description="Enable debug mode",
        )

    async def create_document(
        self,
        document_extension: str,
        document_name: str,
        code: str = """""",
        # contains chat context metadata (critical: includes chat_id, message_id)
        __metadata__: dict = None,
        # open WebUI injects a callback function to send real-time updates to the UI
        # when available, use this to emit status, message, or citation events
        # when None, the tool should work without UI updates (safe fallback)
        __event_emitter__=None,
    ) -> str:
        """
        :param code: The Python code to execute for document generation.
        :param document_extension: Type of document being generated (e.g., "docx", "pdf", "excel", etc.)
        :param document_name: Meaningful name for the document
        """
        
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        # emit status that when starting document generation
        if __event_emitter__:
            await __event_emitter__(
                {
                    "type": "status",
                    "data": {
                        "description": f"Generating {document_extension} document...",
                        "done": False,
                    },
                }
            ) 
            await asyncio.sleep(1)

        # UUIDs from metadata
        chat_id = None
        user_id = None
        
        try:
            if (
                __metadata__
                and ("user_id" in __metadata__)
                and ("chat_id" in __metadata__)
            ):
                user_id = __metadata__["user_id"]
                chat_id = __metadata__["chat_id"]

            else:
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": "Something went wrong! Please contact the administrator and provide them with the error code 18854",
                                "done": True,
                                "hidden": False if self.valves.ENABLE_DEBUG else True,
                            },
                        }
                    )
                    await asyncio.sleep(1)
                raise ValueError("User ID or Chat ID is not available.")

            # map document types to file extensions
            # sometimes ai generates wrong file extensions
            extension_map = {
                "word": "docx",
                "doc": "docx",
                "docx": "docx",
                "pdf": "pdf",
                "excel": "xlsx",
                "xlsx": "xlsx",
                "powerpoint": "pptx",
                "pptx": "pptx",
                "csv": "csv",
                "text": "txt",
                "txt": "txt",
                "rtf": "rtf",
                "odt": "odt",
                "ods": "ods",
                "odp": "odp",
                "html": "html",
                "htm": "html",
                "xml": "xml",
                "json": "json",
                "md": "md",
                "markdown": "md",
                "log": "log",
                "ipynb": "ipynb",
                "py": "py",
                "js": "js",
                "css": "css",
                "ts": "ts",
                "c": "c",
                "cpp": "cpp",
                "java": "java",
                "go": "go",
                "sh": "sh",
                "bash": "sh",
                "yml": "yml",
                "yaml": "yml",
                "ini": "ini",
                "cfg": "cfg",
                "conf": "conf",
                "sql": "sql",
                "ps1": "ps1",
                "bat": "bat"
            }

            # get the appropriate extension
            extension = extension_map.get(document_extension.lower(), "txt")
            
            # ========================================================
            # ================== 🙉 MONKEY WRAPPERS 🐒 ==============
            # ========================================================
            
            # de-indent the model-generated code
            normalized_code = textwrap.dedent(code)

            WRAPPER_CODE = f"""
import os
import sys
import time
import json
import secrets

# ================== WRAPPER ==================

folder = f"/mnt/data/user_files/{user_id}/{chat_id}"
os.makedirs(folder, exist_ok=True)
file_name = secrets.token_urlsafe(16) + "." + "{extension}"
final_path = os.path.join(folder, file_name)

time.sleep(3)

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
                outputfile=None,   # request returned string/bytes
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
                raise RuntimeError(f"Failed to write pypandoc output to {{final_path}}")

            return result

        pypandoc.convert_text = patched_convert_text
        pypandoc._is_patched_by_wrapper = True

except ImportError:
    # pypandoc not available - skip patching
    pass
except Exception as e:
    raise RuntimeError(f"Pandoc patching failed: {{str(e)}}") from e

# ================== MODEL GENERATED CODE ==================
{normalized_code}
# ================== END MODEL GENERATED CODE ==================

if os.path.exists(final_path):
    print(json.dumps({{"status": "ok", "file_name": file_name}}))
else:
    print(json.dumps({{"status": "error", "message": "file not created"}}))
# ================== END WRAPPER ==================
"""

            # emit status when sending code to Jupyter
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": "Sending code to Jupyter backend...",
                            "done": False,
                        },
                    }
                )
                await asyncio.sleep(1)

            # ===================
            #  Configure Jupyter
            # ===================
            kernel_id = None

            headers = {
                "Authorization": f"token {self.valves.JUPYTER_TOKEN}",
                "Content-Type": "application/json",
            }

            kernel_url = f"{self.valves.JUPYTER_URL}/api/kernels"
            kernels_response = requests.get(kernel_url, headers=headers)
            kernels = kernels_response.json()

            if kernels_response.status_code == 200:
                logger.info("kernels_response.status_code == 200")

                if kernels == []:
                    logger.info("Kernels list is empty, creating a new kernel...")
                    kernels_response = requests.post(
                        kernel_url, headers=headers, json={"name": "python3"}
                    )
                    if kernels_response.status_code == 201:
                        kernel_id = kernels_response.json()["id"]
                        logger.info(f"Created kernel with id {kernel_id}")
                    else:
                        logger.info(f"Failed to create kernel: {kernels_response.text}")
                        raise Exception("Failed to create kernel")
                else:
                    kernel_id = kernels[0]["id"]

            else:
                logger.info(f"Failed to get kernels: {kernels_response.text}")
                raise Exception("Failed to get kernels")

            # =================================================
            #  Configure WebSocket to Communicate with Jupyter
            # =================================================

            # webSocket URL for the kernel channel
            ws_url = f"ws://{(self.valves.JUPYTER_URL).replace('https://', '').replace('http://', '')}/api/kernels/{kernel_id}/channels?token={self.valves.JUPYTER_TOKEN}"

            # create a WebSocket connection
            ws = websocket.create_connection(ws_url)

            # unique ID for the request (required by Jupyter)
            msg_id = uuid.uuid4().hex

            # jupyter payload
            msg = {
                "header": {
                    "msg_id": msg_id,
                    "msg_type": "execute_request",
                    "version": "5.2",
                    "session": uuid.uuid4().hex,
                    "username": user_id,
                    "date": time.strftime("%Y-%m-%d-%H:%M:%S"),
                },
                "metadata": {},
                "content": {
                    "code": WRAPPER_CODE,
                    "silent": False,  # fixed: was using undefined 'silent' variable
                    "store_history": False,
                    "user_expressions": {},
                    "allow_stdin": False,
                },
                "parent_header": {},
                "buffers": {},
            }

            # ======================
            #  Send code to Jupyter
            # ======================

            ws.send(json.dumps(msg))
            logger.info("Execution started. Waiting for output...")

            # initialize result variable to capture Jupyter response
            jupyter_result = None

            while True:
                try:
                    raw_msg = ws.recv()
                    if not raw_msg:
                        continue

                    response_msg = json.loads(raw_msg)
                    msg_type = response_msg.get("msg_type")
                    parent_msg_id = response_msg.get("parent_header", {}).get("msg_id")

                    # only process messages related to request sent with msg_id (line: 396)
                    if parent_msg_id != msg_id:
                        continue

                    # capture stream output (stdout from print, etc.)
                    if msg_type == "stream":
                        content = response_msg.get("content", {})
                        text = content.get("text", "")
                        for line in text.strip().split('\n'):
                            if line:
                                try:
                                    jupyter_result = json.loads(line)
                                except Exception as e:
                                    jupyter_result = line
                                logger.info(f"OUTPUT: {jupyter_result} | type: {type(jupyter_result)}")
                        break

                    # capture errors
                    elif msg_type == "error":
                        content = response_msg.get("content", {})
                        logger.info(f"ERROR: {content.get('ename')} - {content.get('evalue')}")
                        traceback = content.get("traceback", [])
                        for line in traceback:
                            logger.info(f"TRACEBACK: {line}")
                        break

                    # detect when execution is complete (this is a part of jupyter, not open webui)
                    elif msg_type == "status":
                        if (response_msg.get("content", {}).get("execution_state") == "idle"):
                            logger.info("Execution completed.")
                            break

                except Exception as e:
                    logger.info(f"Error while receiving from WebSocket: {e}", file=sys.stderr)
                    break

            # =========================
            #  Shutdown Jupyter Kernel
            # =========================
            logger.info(f"Shutting down kernel with ID: {kernel_id}")
            shutdown_url = f"http://localhost:8888/api/kernels/{kernel_id}"
            try:
                response = requests.delete(shutdown_url, headers=headers)
                response.raise_for_status()
                logger.info("Kernel shut down successfully.")
            except requests.exceptions.RequestException as e:
                logger.info(f"Failed to shut down kernel: {e}", file=sys.stderr)

            ws.close()
            logger.info("WebSocket connection closed.")

            # ============================
            #  Construct the download URL
            # ============================

            # check if we got a valid result from Jupyter
            if jupyter_result and jupyter_result["status"] == "ok":
                file_name = jupyter_result["file_name"]
                download_url = f"{self.valves.BASE_DOWNLOAD_URL}?user_id={user_id}&chat_id={chat_id}&file_name={file_name}"

                # emit success status
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": f"{document_name} generated successfully!",
                                "done": True
                            },
                        }
                    )

                # emit citation to download the document
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "citation",
                            "data": {
                                "document": [
                                    "Download the document from the above url."
                                ],
                                "metadata": [
                                    {
                                        "date_accessed": datetime.now().isoformat(),
                                        "source": f"{document_name}",
                                    }
                                ],
                                "source": {
                                    "name": f"Download '{document_name}' here",
                                    "url": f"{download_url}",
                                },
                            },
                        }
                    )
                
                return f"[{document_name}]({download_url})"
            
            else:
                error_msg = f"Document generation failed: {jupyter_result.get('message', 'Unknown error') if jupyter_result else 'No valid response from Jupyter'}"
                if __event_emitter__:
                    await __event_emitter__(
                        {
                            "type": "status",
                            "data": {
                                "description": error_msg, 
                                "done": True,
                                "hidden": False if self.valves.ENABLE_DEBUG else True,
                            },
                        }
                    )
                return f"Error: {error_msg}"

        except json.JSONDecodeError:
            error_msg = "Invalid response from Jupyter backend"
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status",
                        "data": {
                            "description": error_msg, 
                            "done": True,
                            "hidden": False if self.valves.ENABLE_DEBUG else True,
                        },
                    }
                )
            return f"Error: {error_msg}"

        except Exception as e:
            error_msg = f"Error in document generation: {str(e)}"
            if __event_emitter__:
                await __event_emitter__(
                    {
                        "type": "status", 
                        "data": {
                            "description": error_msg, 
                            "done": True,
                            "hidden": False if self.valves.ENABLE_DEBUG else True,
                        },
                    }
                )
            return f"Error: {error_msg}"