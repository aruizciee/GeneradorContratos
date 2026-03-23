import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
from docxtpl import DocxTemplate
import win32com.client as win32
import os
from datetime import datetime
import threading

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Generador de Contratos y Correos")
        self.geometry("800x750")
        
        # --- Variables ---
        self.word_template_path = ""
        self.excel_data_path = ""
        self.outlook_template_path = ""
        self.output_folder = ""
        
        # --- UI Layout ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main Frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_columnconfigure(1, weight=1)
        
        # 1. Word Template Select
        ctk.CTkLabel(self.main_frame, text="1. Plantilla Word (.docx):").grid(row=0, column=0, padx=10, pady=(20, 10), sticky="w")
        self.lbl_word = ctk.CTkLabel(self.main_frame, text="Ningún archivo seleccionado", text_color="gray")
        self.lbl_word.grid(row=0, column=1, padx=10, pady=(20, 10), sticky="w")
        ctk.CTkButton(self.main_frame, text="Seleccionar", command=self.select_word).grid(row=0, column=2, padx=10, pady=(20, 10))
        
        # 2. Excel Data Select
        ctk.CTkLabel(self.main_frame, text="2. Datos Excel (.xlsx):").grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.lbl_excel = ctk.CTkLabel(self.main_frame, text="Ningún archivo seleccionado", text_color="gray")
        self.lbl_excel.grid(row=1, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkButton(self.main_frame, text="Seleccionar", command=self.select_excel).grid(row=1, column=2, padx=10, pady=10)
        
        # 3. Output Folder Select
        ctk.CTkLabel(self.main_frame, text="3. Carpeta de Salida (Contratos):").grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.lbl_output = ctk.CTkLabel(self.main_frame, text="Ninguna carpeta seleccionada", text_color="gray")
        self.lbl_output.grid(row=2, column=1, padx=10, pady=10, sticky="w")
        ctk.CTkButton(self.main_frame, text="Seleccionar", command=self.select_output).grid(row=2, column=2, padx=10, pady=10)

        # 4. Email Column configuration (from Excel)
        ctk.CTkLabel(self.main_frame, text="4. Configuración Excel:").grid(row=3, column=0, padx=10, pady=5, sticky="w")
        
        frame_excel_config = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_excel_config.grid(row=3, column=1, columnspan=2, sticky="ew")
        frame_excel_config.grid_columnconfigure(1, weight=1)
        
        ctk.CTkLabel(frame_excel_config, text="Columna de Email:").grid(row=0, column=0, padx=(0, 10), pady=0, sticky="w")
        self.entry_email_col = ctk.CTkEntry(frame_excel_config, placeholder_text="Ej: Email o Correo")
        self.entry_email_col.insert(0, "Email") # Default value
        self.entry_email_col.grid(row=0, column=1, padx=0, pady=5, sticky="ew")

        ctk.CTkLabel(frame_excel_config, text="Patrón Nombre Archivo:").grid(row=1, column=0, padx=(0, 10), pady=0, sticky="w")
        self.entry_filename_pattern = ctk.CTkEntry(frame_excel_config, placeholder_text="Ej: {{ Apellidos }}, {{ Nombre }}")
        self.entry_filename_pattern.insert(0, "{{ Apellidos }}, {{ Nombre }}") # Default value
        self.entry_filename_pattern.grid(row=1, column=1, padx=0, pady=5, sticky="ew")

        # Divider
        frame_div = ctk.CTkFrame(self.main_frame, height=2, fg_color="gray50")
        frame_div.grid(row=4, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        
        # 5. Email Configuration Toggle
        self.email_mode = ctk.StringVar(value="manual")
        
        # Email settings container
        self.email_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.email_frame.grid(row=5, column=0, columnspan=3, sticky="ew")
        self.email_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkRadioButton(self.email_frame, text="Escribir Asunto y Cuerpo", variable=self.email_mode, value="manual", command=self.toggle_email_mode).grid(row=0, column=0, padx=10, pady=10)
        ctk.CTkRadioButton(self.email_frame, text="Usar Plantilla de Outlook (.oft)", variable=self.email_mode, value="template", command=self.toggle_email_mode).grid(row=0, column=1, padx=10, pady=10, sticky="w")

        # Manual Mode Fields
        self.lbl_subj = ctk.CTkLabel(self.email_frame, text="Asunto del Correo:")
        self.lbl_subj.grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.entry_subject = ctk.CTkEntry(self.email_frame, placeholder_text="Asunto: Contrato Adjunto...")
        self.entry_subject.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        
        self.lbl_body = ctk.CTkLabel(self.email_frame, text="Cuerpo del Correo:")
        self.lbl_body.grid(row=2, column=0, padx=10, pady=5, sticky="nw")
        self.txt_body = ctk.CTkTextbox(self.email_frame, height=100)
        self.txt_body.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")

        # Template Mode Fields
        self.lbl_oft = ctk.CTkLabel(self.email_frame, text="Archivo .oft:")
        self.lbl_oft_path = ctk.CTkLabel(self.email_frame, text="Ningún archivo seleccionado", text_color="gray")
        self.btn_oft = ctk.CTkButton(self.email_frame, text="Seleccionar .oft", command=self.select_oft)
        # Initially hide template fields
        self.toggle_email_mode()

        # Output format
        self.output_format = ctk.StringVar(value="pdf")
        frame_out_format = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_out_format.grid(row=6, column=0, columnspan=3, pady=(10,0))
        ctk.CTkLabel(frame_out_format, text="Formato Archivo:").pack(side="left", padx=10)
        ctk.CTkRadioButton(frame_out_format, text="PDF", variable=self.output_format, value="pdf").pack(side="left", padx=10)
        ctk.CTkRadioButton(frame_out_format, text="Word (.docx)", variable=self.output_format, value="docx").pack(side="left", padx=10)

        # Send Mode
        self.send_mode = ctk.StringVar(value="draft")
        frame_send_mode = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        frame_send_mode.grid(row=7, column=0, columnspan=3, pady=(10,0))
        ctk.CTkRadioButton(frame_send_mode, text="Guardar en Borradores (Draft)", variable=self.send_mode, value="draft").pack(side="left", padx=10)
        ctk.CTkRadioButton(frame_send_mode, text="Enviar Directamente (Send)", variable=self.send_mode, value="send").pack(side="left", padx=10)

        # Generate Button
        self.btn_generate = ctk.CTkButton(self.main_frame, text="Generar Contratos y Correos", command=self.start_generation, height=40, font=("System", 14, "bold"))
        self.btn_generate.grid(row=8, column=0, columnspan=3, pady=20)
        
        # Log Textbox
        self.log_box = ctk.CTkTextbox(self.main_frame, height=150, state="disabled")
        self.log_box.grid(row=9, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.main_frame.grid_rowconfigure(9, weight=1)

    def log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {text}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def toggle_email_mode(self):
        mode = self.email_mode.get()
        if mode == "manual":
            self.lbl_oft.grid_forget()
            self.lbl_oft_path.grid_forget()
            self.btn_oft.grid_forget()
            
            self.lbl_subj.grid(row=1, column=0, padx=10, pady=5, sticky="w")
            self.entry_subject.grid(row=1, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
            self.lbl_body.grid(row=2, column=0, padx=10, pady=5, sticky="nw")
            self.txt_body.grid(row=2, column=1, columnspan=2, padx=10, pady=5, sticky="ew")
        else:
            self.lbl_subj.grid_forget()
            self.entry_subject.grid_forget()
            self.lbl_body.grid_forget()
            self.txt_body.grid_forget()
            
            self.lbl_oft.grid(row=1, column=0, padx=10, pady=5, sticky="w")
            self.lbl_oft_path.grid(row=1, column=1, padx=10, pady=5, sticky="w")
            self.btn_oft.grid(row=1, column=2, padx=10, pady=5)

    def select_word(self):
        filename = filedialog.askopenfilename(title="Seleccionar Plantilla Word", filetypes=[("Word Documents", "*.docx")])
        if filename:
            self.word_template_path = filename
            self.lbl_word.configure(text=os.path.basename(filename), text_color="black")

    def select_excel(self):
        filename = filedialog.askopenfilename(title="Seleccionar Datos Excel", filetypes=[("Excel Files", "*.xlsx")])
        if filename:
            self.excel_data_path = filename
            self.lbl_excel.configure(text=os.path.basename(filename), text_color="black")

    def select_output(self):
        foldername = filedialog.askdirectory(title="Seleccionar Carpeta de Salida")
        if foldername:
            self.output_folder = foldername
            self.lbl_output.configure(text=foldername, text_color="black")

    def select_oft(self):
        filename = filedialog.askopenfilename(title="Seleccionar Plantilla Outlook", filetypes=[("Outlook Template", "*.oft")])
        if filename:
            self.outlook_template_path = filename
            self.lbl_oft_path.configure(text=os.path.basename(filename), text_color="black")

    def start_generation(self):
        if not self.word_template_path:
            messagebox.showwarning("Faltan datos", "Por favor, seleccione la plantilla Word.")
            return
        if not self.excel_data_path:
            messagebox.showwarning("Faltan datos", "Por favor, seleccione el archivo Excel de datos.")
            return
        if not self.output_folder:
            messagebox.showwarning("Faltan datos", "Por favor, seleccione una carpeta de salida.")
            return
        
        email_col = self.entry_email_col.get().strip()
        if not email_col:
            messagebox.showwarning("Faltan datos", "Por favor, especifique el nombre de la columna de Email.")
            return

        filename_pattern = self.entry_filename_pattern.get().strip()
        if not filename_pattern:
            messagebox.showwarning("Faltan datos", "Por favor, especifique un patrón para el nombre de archivo.")
            return

        mode = self.email_mode.get()
        if mode == "manual":
            subject = self.entry_subject.get()
            body = self.txt_body.get("1.0", "end-1c")
            if not subject:
                if not messagebox.askyesno("Confirmar", "El asunto está vacío. ¿Continuar de todos modos?"): return
        else:
            if not self.outlook_template_path:
                messagebox.showwarning("Faltan datos", "Por favor, seleccione la plantilla .oft de Outlook.")
                return

        self.btn_generate.configure(state="disabled")
        self.log("=== INICIANDO PROCESO ===")
        
        # Run in a separate thread so UI doesn't freeze
        threading.Thread(target=self.process_data, daemon=True).start()

    def process_data(self):
        try:
            email_col = self.entry_email_col.get().strip()
            mode = self.email_mode.get()
            s_mode = self.send_mode.get()
            
            self.log("Leyendo Excel...")
            df = pd.read_excel(self.excel_data_path)
            
            if email_col not in df.columns:
                self.log(f"ERROR: La columna '{email_col}' no se encuentra en el Excel.")
                self.log(f"Columnas disponibles: {', '.join(df.columns)}")
                self.btn_generate.configure(state="normal")
                return

            try:
                import pythoncom
                pythoncom.CoInitialize()
                outlook = win32.Dispatch("Outlook.Application")
                
                # Only init Word if PDF is selected to speed up DOCX-only runs
                word_app = None
                if self.output_format.get() == "pdf":
                    word_app = win32.Dispatch("Word.Application")
                    word_app.Visible = False
            except Exception as e:
                self.log(f"ERROR al iniciar Outlook o Word: {e}")
                self.btn_generate.configure(state="normal")
                return

            rows_total = len(df)
            self.log(f"Se encontraron {rows_total} registros a procesar.")

            for index, row in df.iterrows():
                try:
                    # Context for DocxTemplate and Email
                    context = {}
                    for col in df.columns:
                        val = row[col]
                        # Handling NaNs
                        if pd.isna(val):
                            val = ""
                        context[str(col)] = str(val)

                    # 1. Generate Word Document
                    doc = DocxTemplate(self.word_template_path)
                    doc.render(context)
                    
                    # Create a friendly filename based on the pattern
                    pattern = self.entry_filename_pattern.get().strip()
                    name_for_file = pattern
                    for k, v in context.items():
                        name_for_file = name_for_file.replace("{"+k+"}", str(v))
                        name_for_file = name_for_file.replace("{{ "+k+" }}", str(v))
                        name_for_file = name_for_file.replace("{{"+k+"}}", str(v))
                    
                    # Clean up remaining tags if not found
                    import re
                    name_for_file = re.sub(r'\{\{.*?\}\}', '', name_for_file)
                    name_for_file = re.sub(r'\{.*?\}', '', name_for_file)
                    
                    if not name_for_file.strip():
                        name_for_file = f"Contrato_{index+1}"
                        
                    # Remove invalid characters for windows file paths but let sensible chars be part of the name
                    safe_name = "".join([c for c in name_for_file if c.isalpha() or c.isdigit() or c in [' ', ',', '-', '_']]).strip()
                    
                    output_docx_path = os.path.join(self.output_folder, f"{safe_name}.docx")
                    output_pdf_path = os.path.join(self.output_folder, f"{safe_name}.pdf")
                    
                    doc.save(output_docx_path)
                    
                    # Convert to PDF
                    if self.output_format.get() == "pdf":
                        try:
                            self.log(f"Convirtiendo {safe_name} a PDF...")
                            word_doc = word_app.Documents.Open(os.path.abspath(output_docx_path))
                            word_doc.SaveAs(os.path.abspath(output_pdf_path), FileFormat=17) # 17 is wdFormatPDF
                            word_doc.Close()
                            
                            # Optionally remove the DOCX file if you only want the PDF
                            try:
                                os.remove(output_docx_path)
                            except:
                                pass
                            
                            final_attachment_path = output_pdf_path
                        except Exception as pdf_err:
                            self.log(f"Error convirtiendo a PDF para {safe_name}: {pdf_err}. Se usará el Word.")
                            final_attachment_path = output_docx_path
                    else:
                        final_attachment_path = output_docx_path
                    
                    # 2. Prepare Email
                    dest_email = context.get(email_col, "").strip()
                    if not dest_email:
                        self.log(f"Fila {index+1}: Saltado (sin email válido). Archivo generado: {os.path.basename(final_attachment_path)}")
                        continue

                    if mode == "manual":
                        mail = outlook.CreateItem(0)
                        
                        subject_f = self.entry_subject.get()
                        body_f = self.txt_body.get("1.0", "end-1c")
                        
                        # Simple replacement for subject/body variables if they used bracket notation like {Nombre}
                        for k, v in context.items():
                            subject_f = subject_f.replace("{"+k+"}", str(v))
                            body_f = body_f.replace("{"+k+"}", str(v))
                            
                        mail.Subject = subject_f
                        import html
                        body_esc = html.escape(body_f).replace("\n", "<br>")
                        mail.HTMLBody = f"<html><body>{body_esc}</body></html>"
                        
                    else: # Template mode
                        mail = outlook.CreateItemFromTemplate(self.outlook_template_path)
                        
                        try: body_orig = mail.HTMLBody 
                        except: body_orig = mail.Body
                        
                        # Replace variables in .oft body
                        for k, v in context.items(): 
                            body_orig = body_orig.replace("{"+k+"}", str(v))
                        
                        try: mail.HTMLBody = body_orig
                        except: mail.Body = body_orig
                        
                        sub_orig = mail.Subject or ""
                        for k, v in context.items(): 
                            sub_orig = sub_orig.replace("{"+k+"}", str(v))
                        mail.Subject = sub_orig

                    mail.To = dest_email
                    mail.Attachments.Add(os.path.abspath(final_attachment_path))
                    
                    if s_mode == "send":
                        mail.Send()
                        action_str = "Enviado a"
                    else:
                        mail.Save()
                        action_str = "Guardado borrador para"
                        
                    self.log(f"Fila {index+1}: OK - Doc: {os.path.basename(output_file_path)} | Correo: {action_str} {dest_email}")

                except Exception as e:
                    self.log(f"Error procesando fila {index+1}: {e}")

            self.log("=== PROCESO COMPLETADO ===")
            messagebox.showinfo("Completado", "El proceso de generación ha finalizado.")

        except Exception as e:
            self.log(f"Error general: {e}")
        finally:
            self.btn_generate.configure(state="normal")
            try:
                if word_app is not None:
                    word_app.Quit()
            except:
                pass

if __name__ == "__main__":
    app = App()
    app.mainloop()
