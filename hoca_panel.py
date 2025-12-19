import customtkinter as ctk
import pandas as pd
import os
import subprocess
from datetime import datetime
import random
from tkinter import messagebox

# Configuration
EXCEL_FILE = "mail_merge_wide_3kalem.xlsx"
LOG_FILE = "student_logs.json"

class AdminPanel(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Trakya Üniversitesi - BİLGE Hoca Paneli")
        self.geometry("800x600")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        self.logo_label = ctk.CTkLabel(self.sidebar, text="BİLGE\nYönetim", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.pack(pady=20)

        self.btn_shuffle = ctk.CTkButton(self.sidebar, text="Verileri Karıştır", command=self.shuffle_data)
        self.btn_shuffle.pack(pady=10, padx=20)

        self.btn_push = ctk.CTkButton(self.sidebar, text="Canlıyı Güncelle", fg_color="green", hover_color="darkgreen", command=self.push_to_github)
        self.btn_push.pack(pady=10, padx=20)

        self.btn_logs = ctk.CTkButton(self.sidebar, text="Logları Yenile", command=self.load_logs)
        self.btn_logs.pack(pady=10, padx=20)

        # Main Content
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        self.log_display = ctk.CTkTextbox(self.main_frame, width=550, height=500)
        self.log_display.pack(expand=True, fill="both")

        self.load_logs()

    def shuffle_data(self):
        try:
            if not os.path.exists(EXCEL_FILE):
                messagebox.showerror("Hata", "Excel dosyası bulunamadı!")
                return

            xl = pd.ExcelFile(EXCEL_FILE)
            new_sheets = {}
            
            for sheet in xl.sheet_names:
                df = pd.read_excel(EXCEL_FILE, sheet_name=sheet)
                
                # Örnek Karıştırma Mantığı: Fiyatları %10-20 arası rastgele değiştir
                for i in range(1, 4):
                    col = f'Kalem_Fiyatı_{i}'
                    if col in df.columns:
                        df[col] = df[col].apply(lambda x: round(x * random.uniform(0.9, 1.1), 2) if isinstance(x, (int, float)) else x)
                
                new_sheets[sheet] = df

            with pd.ExcelWriter(EXCEL_FILE) as writer:
                for sheet, df in new_sheets.items():
                    df.to_excel(writer, sheet_name=sheet, index=False)
            
            messagebox.showinfo("Başarılı", "Excel verileri rastgele karıştırıldı ve kaydedildi.")
        except Exception as e:
            messagebox.showerror("Hata", f"Karıştırma sırasında hata oluştu: {e}")

    def push_to_github(self):
        try:
            # Git komutlarını çalıştır
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", f"Hoca Paneli Güncellemesi: {datetime.now().strftime('%Y-%m-%d %H:%M')}"], check=True)
            subprocess.run(["git", "push", "origin", "main"], check=True)
            
            messagebox.showinfo("Başarılı", "Değişiklikler GitHub'a gönderildi. Canlı sistem 1-2 dakika içinde güncellenecektir.")
        except Exception as e:
            messagebox.showerror("Hata", f"GitHub'a gönderilirken hata oluştu: {e}\nLütfen Git'in yüklü ve bağlı olduğundan emin olun.")

    def load_logs(self):
        self.log_display.delete("1.0", "end")
        if os.path.exists(LOG_FILE):
            import json
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                logs = json.load(f)
                for log in reversed(logs):
                    status = "✅ BAŞARILI" if log['success'] else "❌ HATALI"
                    text = f"[{log['timestamp']}] {log['student_name']} ({log['student_no']})\n"
                    text += f"Ödev: {log['odev_no']} | Durum: {status}\n"
                    if log['errors']:
                        text += f"Hatalar: {', '.join(log['errors'][:3])}...\n"
                    text += "-"*50 + "\n"
                    self.log_display.insert("end", text)
        else:
            self.log_display.insert("end", "Henüz log kaydı bulunmuyor.")

if __name__ == "__main__":
    app = AdminPanel()
    app.mainloop()
