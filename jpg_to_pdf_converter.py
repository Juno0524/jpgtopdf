import customtkinter as ctk
import configparser
import os
import re
import threading
import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox
from tkcalendar import DateEntry
from tkinterdnd2 import DND_FILES, TkinterDnD

import pytesseract
from PIL import Image, ImageEnhance, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

# TDS (Toss Design System) 브랜드 색상
TOSS_BLUE = "#3182f6"
TOSS_BG_LIGHT = "#f2f4f6"
TOSS_WHITE = "#ffffff"
TOSS_TEXT_MAIN = "#191f28"
TOSS_TEXT_SUB = "#8b95a1"
TOSS_GRAY_BTN = "#f2f4f6"


# Detect local Tesseract path on Windows
tesseract_cmd_path = None
for p in [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]:
    if os.path.exists(p):
        tesseract_cmd_path = p
        break

if tesseract_cmd_path:
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path


# PDF font registration
try:
    font_path = "C:/Windows/Fonts/malgun.ttf"
    if os.path.exists(font_path):
        pdfmetrics.registerFont(TTFont("MalgunGothic", font_path))
        FONT_NAME = "MalgunGothic"
    else:
        FONT_NAME = "Helvetica"
except Exception:
    FONT_NAME = "Helvetica"


class JpgToPdfConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("이미지 PDF 변환기")
        
        # customtkinter 테마 설정
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("blue")

        self.tesseract_available = tesseract_cmd_path is not None
        if not self.tesseract_available:
            messagebox.showwarning(
                "OCR 제한됨",
                "Tesseract-OCR이 설치되지 않았습니다. 자동 금액/날짜 인식 기능을 사용할 수 없습니다.",
            )

        self.config_file = "config.ini"
        self.config = configparser.ConfigParser()
        self.load_config()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.image1_path = tk.StringVar()
        self.image2_path = tk.StringVar()
        self.amount1 = tk.StringVar(value="0")
        self.amount2 = tk.StringVar(value="0")
        self.total_amount = tk.StringVar(value="0")
        self.selected_campaign = tk.StringVar(value="N922")
        self.selected_usage = tk.StringVar(value="Pickup/Delivery")
        self.campaign_btns = {}  # 캠페인 버튼 객체 저장용
        self.usage_btns = {}     # 사용 내용 버튼 객체 저장용

        self.amount1.trace_add("write", self.calculate_total)
        self.amount2.trace_add("write", self.calculate_total)

        self.create_widgets()
        # 초기 활성화 상태 표시
        self.root.after(100, lambda: self.update_campaign_button_ui("N922"))
        self.root.after(100, lambda: self.update_usage_button_ui("Pickup/Delivery"))

    def load_config(self):
        default_geometry = "600x680"
        if os.path.exists(self.config_file):
            try:
                self.config.read(self.config_file, encoding="utf-8")
                self.root.geometry(self.config.get("Window", "geometry", fallback=default_geometry))
                self.root.minsize(400, 550)  # 최소 크기 대폭 하향
                return
            except Exception:
                pass
        self.root.geometry(default_geometry)
        self.root.minsize(400, 550)

    def save_config(self):
        if "Window" not in self.config:
            self.config["Window"] = {}
        self.config["Window"]["geometry"] = self.root.geometry()
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                self.config.write(f)
        except Exception as e:
            self.add_result_message(f"Config save failed: {e}")

    def on_closing(self):
        self.save_config()
        self.root.destroy()

    def add_result_message(self, message):
        stamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{stamp}] {message}")

    def update_result_text(self, event=None):
        if hasattr(self, 'result_text'):
            cc = self.selected_campaign.get()
            uc = self.selected_usage.get()
            pd = self.pickup_date.get()
            dd = self.delivery_date.get()
            
            usage_map = {
                "Pickup/Delivery": "픽업/딜리버리",
                "Pickup": "픽업",
                "Delivery": "딜리버리"
            }
            mapped_uc = usage_map.get(uc, uc)
            
            result = (
                f"1. Campaign Code: {cc}\n"
                f"2. 사용 내용: {mapped_uc}\n"
                f"3. 픽업 일자: {pd}\n"
                f"4. 딜리버리 일자: {dd}\n"
            )
            
            self.result_text.delete("1.0", "end")
            self.result_text.insert("1.0", result)

    def copy_to_clipboard(self):
        content = self.result_text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.add_result_message("Result copied to clipboard")

    def set_campaign(self, code):
        self.selected_campaign.set(code)
        self.update_campaign_button_ui(code)
        self.update_result_text()
        self.add_result_message(f"Campaign set to: {code}")

    def update_campaign_button_ui(self, active_code):
        for code, btn in self.campaign_btns.items():
            if code == active_code:
                btn.configure(fg_color=TOSS_BLUE, text_color="white")  # 토스 블루 색상
            else:
                btn.configure(fg_color=TOSS_GRAY_BTN, text_color=TOSS_TEXT_MAIN)

    def set_usage(self, usage):
        self.selected_usage.set(usage)
        self.update_usage_button_ui(usage)
        self.update_result_text()
        self.add_result_message(f"Usage set to: {usage}")

    def update_usage_button_ui(self, active_usage):
        for usage, btn in self.usage_btns.items():
            if usage == active_usage:
                btn.configure(fg_color=TOSS_BLUE, text_color="white")
            else:
                btn.configure(fg_color=TOSS_GRAY_BTN, text_color=TOSS_TEXT_MAIN)

    def calculate_total(self, *_):
        try:
            v1 = int(re.sub(r"[^0-9]", "", self.amount1.get() or "0"))
        except Exception:
            v1 = 0
        try:
            v2 = int(re.sub(r"[^0-9]", "", self.amount2.get() or "0"))
        except Exception:
            v2 = 0
        self.total_amount.set(f"{v1 + v2:,}")

    def find_date_in_text(self, text):
        pattern = r"(\d{4})[\s./-]*(\d{1,2})[\s./-]*(\d{1,2})"
        for m in re.finditer(pattern, text):
            try:
                y, mm, dd = map(int, m.groups())
                if 2000 <= y <= 2100:
                    return date(y, mm, dd)
            except Exception:
                continue
        return None

    def preprocess_image_for_ocr(self, file_path):
        img = Image.open(file_path)
        img = ImageOps.grayscale(img)
        return ImageEnhance.Contrast(img).enhance(2.0)

    def ocr_text(self, image):
        text = ""
        try:
            text = pytesseract.image_to_string(image, lang="eng+kor", config="--psm 6")
        except Exception:
            pass
        if not text.strip():
            try:
                text = pytesseract.image_to_string(image, lang="eng", config="--psm 6")
            except Exception:
                pass
        return text

    def extract_text_from_pdf(self, file_path):
        try:
            import PyPDF2
        except Exception:
            return ""

        parts = []
        try:
            with open(file_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    try:
                        parts.append(page.extract_text() or "")
                    except Exception:
                        parts.append("")
        except Exception:
            return ""

        return "\\n".join(parts).strip()

    def extract_and_set_date_from_pdf(self, file_path, target_widget):
        text = self.extract_text_from_pdf(file_path)
        if not text:
            self.add_result_message("PDF text extraction failed")
            return

        found = self.find_date_in_text(text)
        if found:
            target_widget.set_date(found)
            self.update_result_text()
            self.add_result_message(f"PDF date detected: {found}")
        else:
            self.add_result_message("No date found in PDF")

    def extract_and_set_amount(self, file_path, target_var):
        if not self.tesseract_available:
            return

        try:
            text = self.ocr_text(self.preprocess_image_for_ocr(file_path))

            scoped = text
            keyword_lines = [line for line in text.split("\\n") if "amount" in line.lower()]
            if keyword_lines:
                scoped = "\\n".join(keyword_lines)

            candidates = re.findall(r"([0-9]{1,3}(?:[,.]?[0-9]{3})*)", scoped)
            valid = []
            for token in candidates:
                clean = re.sub(r"[,.]", "", token)
                if not clean or (len(clean) > 1 and clean.startswith("0")):
                    continue
                try:
                    n = int(clean)
                    if 100 < n < 100000000:
                        valid.append(n)
                except ValueError:
                    pass

            if valid:
                best = max([n for n in valid if n % 10 == 0] or valid)
                target_var.set(f"{best:,}")
                self.add_result_message(f"Amount detected: {best:,}")
        except Exception as e:
            self.add_result_message(f"Amount OCR error: {e}")

    def extract_and_set_date(self, file_path, target_widget):
        if not self.tesseract_available:
            return

        self.add_result_message(f"Date OCR start: {os.path.basename(file_path)}")

        def run_ocr():
            try:
                text = self.ocr_text(self.preprocess_image_for_ocr(file_path))
                if not text.strip():
                    self.root.after(0, lambda: self.add_result_message("Date OCR failed: no text"))
                    return

                found = self.find_date_in_text(text)
                if found:
                    self.root.after(0, lambda: target_widget.set_date(found))
                    self.root.after(0, self.update_result_text)
                    self.root.after(0, lambda: self.add_result_message(f"Date detected: {found}"))
                else:
                    self.root.after(0, lambda: self.add_result_message("Date OCR failed: no date"))
            except Exception as e:
                self.root.after(0, lambda: self.add_result_message(f"Date OCR error: {e}"))

        threading.Thread(target=run_ocr, daemon=True).start()

    def debug_ocr(self):
        if not self.tesseract_available:
            messagebox.showwarning("OCR Unavailable", "Tesseract-OCR is not installed.")
            return

        file_path = self.image1_path.get() or self.image2_path.get()
        if not file_path:
            messagebox.showinfo("Info", "Select an image first.")
            return

        try:
            img = self.preprocess_image_for_ocr(file_path)
            text_kor = pytesseract.image_to_string(img, lang="eng+kor", config="--psm 6")
            text_eng = pytesseract.image_to_string(img, lang="eng", config="--psm 6")

            win = tk.Toplevel(self.root)
            win.title(f"OCR Debug - {os.path.basename(file_path)}")
            win.geometry("640x420")

            txt = tk.Text(win, wrap="word")
            txt.pack(expand=True, fill="both")
            txt.insert("1.0", f"--- eng+kor ---\n{text_kor}\n\n--- eng ---\n{text_eng}\n")
        except Exception as e:
            messagebox.showerror("OCR Debug Error", f"An error occurred:\n{e}")

    def handle_selected_file(self, file_path, img_num):
        lower = file_path.lower()

        if lower.endswith((".jpg", ".jpeg")):
            if img_num == 1:
                self.image1_path.set(file_path)
                self.lbl_img1.config(text=os.path.basename(file_path), bg="#d9f7d9")
                self.extract_and_set_amount(file_path, self.amount1)
                self.extract_and_set_date(file_path, self.pickup_date)
            else:
                self.image2_path.set(file_path)
                self.lbl_img2.config(text=os.path.basename(file_path), bg="#d9f7d9")
                self.extract_and_set_amount(file_path, self.amount2)
                self.extract_and_set_date(file_path, self.delivery_date)
            self.add_result_message(f"Upload: {os.path.basename(file_path)}")
            return

        if lower.endswith(".pdf"):
            if img_num == 1:
                self.lbl_img1.config(text=os.path.basename(file_path), bg="#fff6cc")
                self.extract_and_set_date_from_pdf(file_path, self.pickup_date)
            else:
                self.lbl_img2.config(text=os.path.basename(file_path), bg="#fff6cc")
                self.extract_and_set_date_from_pdf(file_path, self.delivery_date)
            self.add_result_message("PDF handled for date extraction only")
            return

        self.add_result_message("Unsupported file type")

    def on_drop(self, event, img_num):
        file_path = event.data
        if file_path.startswith("{") and file_path.endswith("}"):
            file_path = file_path[1:-1]
        self.handle_selected_file(file_path, img_num)

    def select_image(self, img_num):
        default_path = r"C:\Users\user\Documents\카카오톡 받은 파일"
        file_path = filedialog.askopenfilename(
            initialdir=default_path if os.path.exists(default_path) else None,
            filetypes=[
                ("Image/PDF files", "*.jpg;*.jpeg;*.pdf"),
                ("JPG files", "*.jpg;*.jpeg"),
                ("PDF files", "*.pdf"),
            ]
        )
        if file_path:
            self.handle_selected_file(file_path, img_num)

    def generate_pdf(self):
        cc = self.selected_campaign.get()
        uc = self.usage_content.get()
        pd = self.pickup_date.get()
        dd = self.delivery_date.get()
        total = self.total_amount.get()

        if not all([cc, uc, pd, dd]):
            messagebox.showwarning("Input Error", "Please fill all fields.")
            return

        if not self.image1_path.get() or not self.image2_path.get():
            messagebox.showwarning("File Error", "Please select both JPG images.")
            return

        output_pdf = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")]
        )
        if not output_pdf:
            return

        try:
            self.create_pdf(output_pdf, cc, uc, pd, dd, total)
            messagebox.showinfo("Success", f"PDF generated:\n{output_pdf}")
            self.add_result_message(f"PDF generated: {os.path.basename(output_pdf)}")
        except Exception as e:
            messagebox.showerror("Error", f"PDF generation failed:\n{e}")

    def create_pdf(self, output_path, cc, uc, pd, dd, total):
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4

        c.setFont(FONT_NAME, 12)
        y = height - 50
        lh = 20

        c.drawString(50, y, f"1. Campaign Code: {cc}")
        y -= lh
        c.drawString(50, y, f"2. Usage: {uc}")
        y -= lh
        c.drawString(50, y, f"3. Pickup Date: {pd}")
        y -= lh
        c.drawString(50, y, f"4. Delivery Date: {dd}")
        y -= lh
        c.drawString(50, y, f"5. Total Amount: {total}")
        y -= 30

        max_h = (y - 50) / 2 - 10
        max_w = width - 100

        for img_path in [self.image1_path.get(), self.image2_path.get()]:
            with Image.open(img_path) as img:
                iw, ih = img.size
                ratio = min(max_w / iw, max_h / ih)
                nw, nh = iw * ratio, ih * ratio
                x = (width - nw) / 2
                draw_y = y - nh
                c.drawImage(img_path, x, draw_y, width=nw, height=nh)
                y = draw_y - 20

        c.save()

    def create_widgets(self):
        self.root.columnconfigure(0, weight=1)
        self.root.configure(bg=TOSS_WHITE)  # fg_color 대신 bg 사용

        # 메인 컨테이너 (여백 최소화)
        main = ctk.CTkFrame(self.root, fg_color=TOSS_WHITE, corner_radius=0)
        main.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main.columnconfigure(1, weight=1)

        font_label = ("Apple SD Gothic Neo", 12, "bold")
        font_entry = ("Apple SD Gothic Neo", 12)
        
        row = 0
        ctk.CTkLabel(main, text="1. Campaign Code", font=font_label, text_color=TOSS_TEXT_MAIN).grid(row=row, column=0, sticky="w", pady=(0, 2))
        
        row += 1
        btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 6))
        for code in ["N922", "H521", "N634"]:
            btn = ctk.CTkButton(
                btn_frame,
                text=code,
                width=60,
                height=32,
                corner_radius=8,
                font=font_label,
                command=lambda c=code: self.set_campaign(c),
                fg_color=TOSS_GRAY_BTN,
                text_color=TOSS_TEXT_MAIN,
                hover_color="#e5e8eb"
            )
            btn.pack(side="left", padx=(0, 6))
            self.campaign_btns[code] = btn

        row += 1
        ctk.CTkLabel(main, text="2. Usage", font=font_label, text_color=TOSS_TEXT_MAIN).grid(row=row, column=0, sticky="w", pady=(0, 1))
        
        row += 1
        usage_frame = ctk.CTkFrame(main, fg_color="transparent")
        usage_frame.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 6))
        for usage in ["Pickup/Delivery", "Pickup", "Delivery"]:
            btn = ctk.CTkButton(
                usage_frame,
                text=usage,
                width=100,
                height=32,
                corner_radius=8,
                font=font_entry,
                command=lambda u=usage: self.set_usage(u),
                fg_color=TOSS_GRAY_BTN,
                text_color=TOSS_TEXT_MAIN,
                hover_color="#e5e8eb"
            )
            btn.pack(side="left", padx=(0, 6))
            self.usage_btns[usage] = btn
        row += 1

        # 날짜 영역 (가로 배치로 높이 절약)
        date_frame = ctk.CTkFrame(main, fg_color="transparent")
        date_frame.grid(row=row, column=0, columnspan=2, sticky="we", pady=(0, 6))
        date_frame.columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(date_frame, text="3. Pickup Date", font=font_label, text_color=TOSS_TEXT_MAIN).grid(row=0, column=0, sticky="w")
        self.pickup_date = DateEntry(date_frame, width=15, date_pattern="yyyy-mm-dd", font=font_entry)
        self.pickup_date.grid(row=1, column=0, sticky="w", pady=(1, 0), padx=(0, 10))

        ctk.CTkLabel(date_frame, text="4. Delivery Date", font=font_label, text_color=TOSS_TEXT_MAIN).grid(row=0, column=1, sticky="w")
        self.delivery_date = DateEntry(date_frame, width=15, date_pattern="yyyy-mm-dd", font=font_entry)
        self.delivery_date.grid(row=1, column=1, sticky="w", pady=(1, 0))
        row += 1

        ctk.CTkFrame(main, height=1, fg_color="#e5e8eb").grid(row=row, column=0, columnspan=2, sticky="we", pady=6)
        row += 1

        # 이미지 업로드 영역 (레이블 단축 및 버튼 크기 확대)
        for i, (label_text, btn_text) in enumerate([("P. Amount", "Pickup Image"), ("D. Amount", "Delivery Image")]):
            img_num = i + 1
            btn_col = ctk.CTkButton(
                main, 
                text=btn_text, 
                width=120, # 버튼 크기 확대
                height=34,
                corner_radius=6,
                font=font_label,
                fg_color=TOSS_GRAY_BTN,
                text_color=TOSS_TEXT_MAIN,
                hover_color="#e5e8eb",
                command=lambda n=img_num: self.select_image(n)
            )
            btn_col.grid(row=row, column=0, sticky="w", pady=(0, 3))
            
            lbl = tk.Label(main, text="Drop file here", bg=TOSS_BG_LIGHT, fg=TOSS_TEXT_SUB, font=("Apple SD Gothic Neo", 9), relief="flat", height=1)
            lbl.grid(row=row, column=1, sticky="we", padx=(10, 0), pady=(0, 3))
            if img_num == 1: self.lbl_img1 = lbl
            else: self.lbl_img2 = lbl
            
            row += 1
            ctk.CTkLabel(main, text=label_text, font=font_label, text_color=TOSS_TEXT_MAIN).grid(row=row, column=0, sticky="w")
            entry = ctk.CTkEntry(
                main, 
                textvariable=(self.amount1 if img_num == 1 else self.amount2),
                width=150,
                height=28,
                corner_radius=6,
                fg_color=TOSS_BG_LIGHT,
                border_width=0,
                font=font_entry
            )
            entry.grid(row=row, column=1, sticky="w", padx=(10, 0), pady=(0, 5))
            row += 1

        self.lbl_img1.drop_target_register(DND_FILES)
        self.lbl_img1.dnd_bind("<<Drop>>", lambda e: self.on_drop(e, 1))
        self.lbl_img2.drop_target_register(DND_FILES)
        self.lbl_img2.dnd_bind("<<Drop>>", lambda e: self.on_drop(e, 2))

        # 합계 및 액션
        row += 1
        summary_frame = ctk.CTkFrame(main, fg_color=TOSS_BG_LIGHT, corner_radius=12)
        summary_frame.grid(row=row, column=0, columnspan=2, sticky="we", pady=6, ipady=4)
        
        ctk.CTkLabel(summary_frame, text="Total Amount", font=font_label, text_color=TOSS_TEXT_SUB).pack(side="left", padx=15)
        ctk.CTkLabel(summary_frame, textvariable=self.total_amount, font=("Apple SD Gothic Neo", 16, "bold"), text_color=TOSS_BLUE).pack(side="right", padx=15)
        
        row += 1
        btn_generate = ctk.CTkButton(
            main, 
            text="Generate PDF", 
            fg_color=TOSS_BLUE, 
            text_color="white", 
            font=("Apple SD Gothic Neo", 14, "bold"),
            height=45,
            corner_radius=12,
            command=self.generate_pdf
        )
        btn_generate.grid(row=row, column=0, columnspan=2, sticky="we", pady=(4, 4))
        
        row += 1
        # Result 영역
        result_header = ctk.CTkFrame(main, fg_color="transparent")
        result_header.grid(row=row, column=0, columnspan=2, sticky="we", pady=(3, 0))
        ctk.CTkLabel(result_header, text="Result", font=font_label, text_color=TOSS_TEXT_MAIN).pack(side="left")
        ctk.CTkButton(
            result_header, 
            text="Copy", 
            width=50, 
            height=24, 
            corner_radius=6, 
            font=("Apple SD Gothic Neo", 10, "bold"),
            fg_color=TOSS_GRAY_BTN,
            text_color=TOSS_TEXT_MAIN,
            command=self.copy_to_clipboard
        ).pack(side="right")
        
        row += 1
        self.result_text = tk.Text(
            main, 
            height=5, 
            width=40, 
            wrap="word", 
            font=("Consolas", 10), 
            bg=TOSS_BG_LIGHT, 
            fg=TOSS_TEXT_MAIN,
            relief="flat",
            padx=10,
            pady=8
        )
        self.result_text.grid(row=row, column=0, columnspan=2, sticky="we", pady=(4, 0))

        self.pickup_date.bind("<<DateEntrySelected>>", self.update_result_text)
        self.pickup_date.bind("<KeyRelease>", self.update_result_text)
        self.delivery_date.bind("<<DateEntrySelected>>", self.update_result_text)
        self.delivery_date.bind("<KeyRelease>", self.update_result_text)
        
        self.update_result_text()


if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = JpgToPdfConverterApp(root)
    root.mainloop()
