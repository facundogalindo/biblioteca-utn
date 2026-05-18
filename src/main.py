import tkinter as tk
from interfaz import InterfazBiblioteca


def main():
    root = tk.Tk()
    InterfazBiblioteca(root)
    root.mainloop()


if __name__ == "__main__":
    main()