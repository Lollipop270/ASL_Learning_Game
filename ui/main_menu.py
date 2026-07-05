import customtkinter as ctk
from ui.widgets import title_label

class MainMenu(ctk.CTkFrame):
    def __init__(self, parent, start_learn, start_test, start_word):
        super().__init__(parent)

        title_label(self, "ASL Learning Game").pack(pady=80)

        ctk.CTkButton(self, text="Learn Mode", width=300, height=60, command=start_learn).pack(pady=20)
        ctk.CTkButton(self, text="Test Mode", width=300, height=60, command=start_test).pack(pady=20)
        ctk.CTkButton(self, text="Word Mode", width=300, height=60, command=start_word).pack(pady=20)