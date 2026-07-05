import customtkinter as ctk

def title_label(parent, text):
    return ctk.CTkLabel(parent, text=text, font=("Arial", 40, "bold"))

def big_letter(parent, text):
    return ctk.CTkLabel(parent, text=text, font=("Arial", 180, "bold"))