import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

# ============================================================
# μRISCV Project - Milestone #1
# Group 5: Program Input with Error Checking + Opcode Output
# ============================================================
# Group 5 Control Hazard Scheme: Pipeline Freeze
# ============================================================

# Group 2,5: LW, SW, AND, OR, ORI, BLT, BGE
# Supported instructions for Group 5

class RiscVGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("μRISCV Assembler Simulator")
        self.root.geometry("800x400")
        
        
        # Create notebook (tabs)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # Create tabs
        self.create_program_tab()
        self.create_register_tab()
        self.create_memory_tab()
        self.create_opcode_tab()

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Made by Sean Regindin")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief='sunken')
        status_bar.pack(side='bottom', fill='x')


    def create_program_tab(self):
        """Create the program input tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Program Input")
    
    def create_register_tab(self):
        """Create the register input tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Register Input")
    
    def create_memory_tab(self):
        """Create the memory input tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Memory Input")
    
    def create_memory_table(self, parent):
        """Create memory table for data segment."""
        # Create frame with scrollbar
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    def create_opcode_tab(self):
        """Create the opcode output tab."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Opcode Output")

def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = RiscVGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()