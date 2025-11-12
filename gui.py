import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox,Button

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
        self.entry_row_count = 0  # Tracks the next available grid row
        self.entry_widgets = []
        self.line_labels = []
        self.commands = []
        self.root = root
        self.root.title("μRISCV Assembler Simulator")
        self.root.geometry("800x400")
        self.create_buttons()
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
        self.status_var.set("Made by Sean Regindin,Marvien Castillo,Mikaela Herrera")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief='sunken')
        status_bar.pack(side='bottom', fill='x')


    def create_program_tab(self):
        """Create the program input tab."""
    
        self.frame = tk.Frame(self.notebook,bg="#D3D3D3",bd=3)
        self.notebook.add(self.frame, text="Program Input")
        self.frame.columnconfigure(1,weight=1)
        self.add_entry(event=None)
        
    def create_register_tab(self):
        """Create the register input tab."""
        frame = tk.Frame(self.notebook,bg="#D3D3D3",bd=3)
        self.notebook.add(frame, text="Register Input")
    
    def create_memory_tab(self):
        """Create the memory input tab."""
        frame = tk.Frame(self.notebook,bg="#D3D3D3",bd=3)
        self.notebook.add(frame, text="Memory Input")
    
    def create_memory_table(self, parent):
        """Create memory table for data segment."""
        # Create frame with scrollbar
        table_frame = tk.Frame(parent,bg="#D3D3D3",bd=3)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    def create_opcode_tab(self):
        """Create the opcode output tab."""
        frame = tk.Frame(self.notebook,bg="#D3D3D3",bd=3)
        self.notebook.add(frame, text="Opcode Output")
    def create_buttons(self):
        frame = tk.Frame(self.root,bg="#D3D3D3",bd=1,relief="sunken")
        frame.pack(fill='x', side='top',padx=10,pady=(10,0))
        self.runButton = Button(frame,text="Run",width=3)
        self.runButton.pack(side="right")
        self.runButton["state"] = "disabled"
        self.checkButton = Button(frame,text="Check",width=5)
        self.checkButton.pack(side="right")
    # when the user hit enter
    def hit_enter(self,event):
        current_entry = event.widget
        instruction = current_entry.get() 
        try: 
            widget_index = self.entry_widgets.index(current_entry)
        except ValueError:
            print("Error")
            return "break" 
        last_index = self.entry_row_count - 1
        if instruction: # if there is instruction then this will push thru
            self.evaluateCommand()
            self.add_entry(event)
        elif widget_index == last_index: # if current focus is the last entry then it will create a new entry
            self.add_entry(event)
        else:  # if there is no instruction then this will not push thru (empty string)
            # if the current entry is not the last then it will focus on the next entry
            if((widget_index+1) < self.entry_row_count):
                self.entry_widgets[widget_index+1].focus_set()
    # Add new entry
    def add_entry(self,event):
        self.entry_row_count += 1
        current_row = self.entry_row_count
        # for row indicator 
        line_label = tk.Label(self.frame,text=current_row)
        line_label.grid(row=current_row,column=0,sticky='w')
        # text input field
        self.new_entry = tk.Entry(self.frame,bg="#D3D3D3",width=50)
        self.new_entry.grid(row=current_row, column=1, padx=(5,0), pady=2, sticky='ew')
        # add it to widget list so that it can be get() and will be process later
        self.entry_widgets.append(self.new_entry)
        self.line_labels.append(line_label)
        self.new_entry.focus_set()
        self.new_entry.bind("<Return>",self.hit_enter) # if enter is typed
    def evaluateCommand(command):
        print("Hello")

def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = RiscVGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()