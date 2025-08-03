import pandas as pd
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from tkinter import StringVar, END, Listbox, Toplevel, Label, Entry, Button
from tkinter.scrolledtext import ScrolledText
import pyperclip
import webbrowser
import tkinter as tk

class BilingualPredictiveDictionary:
    def __init__(self, root):
        self.root = root
        self.root.title("📖 മലയാളം നിഘണ്ടു ")
        self.root.geometry("1000x700")
        self.root.resizable(False, False)

        self.font_normal = ("Noto Sans Malayalam", 14)
        self.font_bold = ("Noto Sans Malayalam", 16, "bold")
        self.font_heading = ("Helvetica", 20, "bold")

        # Load data
        self.enml_data = pd.read_excel(r"C:/Users/20hsm/OneDrive/Desktop/files/en_ml.xlsx")
        self.mlml_data = pd.read_excel(r"C:/Users/20hsm/OneDrive/Desktop/datukexcel.xlsx")

        self.enml_data.dropna(inplace=True)
        self.mlml_data.dropna(inplace=True)

        self.enml_pairs = list(zip(self.enml_data['from_content'].astype(str).str.strip(),
                                   self.enml_data['to_content'].astype(str).str.strip()))

        self.mlml_pairs = list(zip(self.mlml_data['from_content'].astype(str).str.strip(),
                                   self.mlml_data['to_content'].astype(str).str.strip()))

        self.search_var = StringVar()
        self.direction = StringVar(value="en-ml")
        self.search_job = None

        self.create_widgets()

    def create_widgets(self):
        header = tk.Frame(self.root, bg="white")
        header.pack(fill="x")

        tk.Label(
            header,
            text="📖 മലയാളം നിഘണ്ടു",
            font=self.font_heading,
            foreground="#009688",
            background="white"
        ).pack(pady=15)

        frame = ttkb.Frame(self.root)
        frame.pack(pady=5, padx=20, fill=X)

        ttkb.Label(frame, text=" തിരയുക🔍:", font=self.font_normal).pack(side=LEFT, padx=10)

        self.entry = ttkb.Entry(frame, textvariable=self.search_var, font=self.font_normal, width=35, bootstyle="success")
        self.entry.pack(side=LEFT, padx=10)
        self.entry.bind("<KeyRelease>", self.delayed_search)

        dir_frame = ttkb.Frame(self.root)
        dir_frame.pack(pady=5)
        ttkb.Radiobutton(dir_frame, text="🇬🇧 English → മലയാളം", variable=self.direction, value="en-ml", command=self.perform_search, bootstyle="info").pack(side=LEFT, padx=10)
        ttkb.Radiobutton(dir_frame, text="🇮🇳 മലയാളം → English", variable=self.direction, value="ml-en", command=self.perform_search, bootstyle="info").pack(side=LEFT, padx=10)
        ttkb.Radiobutton(dir_frame, text="🗣️ മലയാളം → മലയാളം", variable=self.direction, value="ml-ml", command=self.perform_search, bootstyle="info").pack(side=LEFT, padx=10)

        ttkb.Button(self.root, text="➕ Add Word to Dictionary", bootstyle="warning", command=self.add_word).pack(pady=5)
        ttkb.Button(self.root, text="📬 Contact Me", bootstyle="secondary", command=self.open_contact_window).pack(pady=5)

        self.suggestion_box = Listbox(self.root, height=6, font=self.font_normal, bg="#f9f9f9")
        self.suggestion_box.pack(fill=X, padx=20, pady=10)
        self.suggestion_box.bind("<<ListboxSelect>>", self.on_suggestion_click)

        self.output_box = ScrolledText(self.root, wrap='word', font=self.font_normal, bg="#f0fff0", height=10)
        self.output_box.pack(fill=BOTH, expand=True, padx=20, pady=10)
        self.output_box.tag_config("bold", font=self.font_bold)
        self.output_box.tag_config("copy", foreground="black", underline=False)
        self.output_box.tag_bind("copy", "<Button-1>", self.on_copy_click)
        self.output_box.config(state="disabled")

    def delayed_search(self, event=None):
        if self.search_job:
            self.root.after_cancel(self.search_job)
        self.search_job = self.root.after(150, self.perform_search)

    def perform_search(self):
        word = self.search_var.get().strip().lower()
        self.suggestion_box.delete(0, END)
        self.output_box.config(state="normal")
        self.output_box.delete("1.0", END)

        if not word:
            return

        if self.direction.get() == "en-ml":
            matches = [(src, tgt) for src, tgt in self.enml_pairs if src.lower().startswith(word)]
            exacts = [(src, tgt) for src, tgt in self.enml_pairs if src.lower() == word]
        elif self.direction.get() == "ml-en":
            matches = [(tgt, src) for src, tgt in self.enml_pairs if tgt.lower().startswith(word)]
            exacts = [(tgt, src) for src, tgt in self.enml_pairs if tgt.lower() == word]
        else:
            matches = [(src, tgt) for src, tgt in self.mlml_pairs if src.lower().startswith(word)]
            exacts = [(src, tgt) for src, tgt in self.mlml_pairs if src.lower() == word]

        for suggestion in list(dict.fromkeys([src for src, _ in matches]))[:20]:
            self.suggestion_box.insert(END, suggestion)

        if exacts:
            src_word = exacts[0][0]
            self.output_box.insert(END, src_word + "\n", "bold")

            added_translations = set()
            for _, tgt in exacts:
                if tgt not in added_translations:
                    self.output_box.insert(END, f"→ {tgt} 🗍\n", "copy")
                    self.output_box.tag_add(tgt, "end-2l", "end-1l")
                    added_translations.add(tgt)

        self.output_box.config(state="disabled")

    def add_word(self):
        popup = Toplevel(self.root)
        popup.title("Add New Word")
        popup.geometry("400x300")
        popup.grab_set()

        Label(popup, text="From Word:", font=self.font_normal).pack(pady=5)
        from_entry = Entry(popup, font=self.font_normal)
        from_entry.pack(pady=5)
        from_entry.insert(0, self.search_var.get().strip())

        Label(popup, text="To Word:", font=self.font_normal).pack(pady=5)
        to_entry = Entry(popup, font=self.font_normal)
        to_entry.pack(pady=5)

        def save():
            from_word = from_entry.get().strip()
            to_word = to_entry.get().strip()
            if not from_word or not to_word:
                return
            self.enml_pairs.append((from_word, to_word))
            new_row = pd.DataFrame([[from_word, to_word]], columns=['from_content', 'to_content'])
            self.enml_data = pd.concat([self.enml_data, new_row], ignore_index=True)
            try:
                self.enml_data.to_excel(r"C:/Users/20hsm/OneDrive/Desktop/files/en_ml.xlsx", index=False)
            except:
                print("Warning: Could not save to Excel.")
            popup.destroy()
            self.perform_search()

        Button(popup, text="Save Word", command=save, font=self.font_normal).pack(pady=15)

    def on_suggestion_click(self, event):
        index = self.suggestion_box.curselection()
        if not index:
            return
        selected_word = self.suggestion_box.get(index)
        self.search_var.set(selected_word)
        self.entry.icursor(END)

        self.output_box.config(state="normal")
        self.output_box.delete("1.0", END)

        if self.direction.get() == "en-ml":
            results = [(src, tgt) for src, tgt in self.enml_pairs if src == selected_word]
        elif self.direction.get() == "ml-en":
            results = [(tgt, src) for src, tgt in self.enml_pairs if tgt == selected_word]
        else:
            results = [(src, tgt) for src, tgt in self.mlml_pairs if src == selected_word]

        if results:
            self.output_box.insert(END, f"{selected_word}\n", "bold")
            added = set()
            for _, tgt in results:
                if tgt not in added:
                    self.output_box.insert(END, f"→ {tgt} 🗍\n", "copy")
                    self.output_box.tag_add(tgt, "end-2l", "end-1l")
                    added.add(tgt)

        self.output_box.config(state="disabled")

    def on_copy_click(self, event):
        index = self.output_box.index(f"@{event.x},{event.y}")
        tags = self.output_box.tag_names(index)
        for tag in tags:
            if tag not in ("copy", "bold", "sel", "normal"):
                pyperclip.copy(tag)
                self.root.title("✅ Copied!")
                self.root.after(1000, lambda: self.root.title("\U0001F4D8 Fast Bilingual Dictionary"))
                break

    def open_contact_window(self):
        contact_window = Toplevel(self.root)
        contact_window.title("Contact Me")
        contact_window.geometry("400x250")
        contact_window.resizable(False, False)
        contact_window.grab_set()

        ttkb.Label(contact_window, text="📬 Let's Connect", font=self.font_heading, bootstyle="primary").pack(pady=10)

        ttkb.Button(contact_window, text="📧 Email", bootstyle="info", width=25,
                    command=lambda: webbrowser.open_new(
                        "https://mail.google.com/mail/?view=cm&fs=1&to=yaduk883@gmail.com")).pack(pady=5)

        ttkb.Button(contact_window, text="🐙 GitHub", bootstyle="dark", width=25,
                    command=lambda: webbrowser.open_new("https://github.com/yaduk883")).pack(pady=5)

        ttkb.Button(contact_window, text="📸 Instagram", bootstyle="danger", width=25,
                    command=lambda: webbrowser.open_new("https://instagram.com/ig.yadu/")).pack(pady=5)

# available themes (hidden/reference only):
# "cosmo", "flatly", "journal", "litera", "lumen", "minty",
# "pulse", "sandstone", "united", "yeti", "morph", "simplex",
# "cerculean",  # Cerulean style
# "darkly", "cyborg", "superhero", "solar"

if __name__ == "__main__":
    root = ttkb.Window(themename="flatly")
    app = BilingualPredictiveDictionary(root)
    root.mainloop()
