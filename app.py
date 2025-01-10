import tkinter as tk
from tkinter import ttk, messagebox

class StartPage(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Compteur")
        self.geometry("400x200")
        self.resizable(False, False)

        self.counter = 0  # Initialisation du compteur

        self.label = tk.Label(self, text=f"Compteur : {self.counter}", font=('Times', '20'))
        self.label.pack(pady=20)

        increment_button = tk.Button(self, text="Augmenter", command=self.increment_counter)
        increment_button.pack(pady=10)

        decrement_button = tk.Button(self, text="Réduire", command=self.decrement_counter)
        decrement_button.pack(pady=10)

    def increment_counter(self):
        self.counter += 1
        self.label.config(text=f"Compteur : {self.counter}")

    def decrement_counter(self):
        self.counter -= 1
        self.label.config(text=f"Compteur : {self.counter}")

if __name__ == "__main__":
    app = StartPage()
    app.mainloop()
