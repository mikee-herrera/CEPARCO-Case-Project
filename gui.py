import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Button
import re

# ============================================================
# μRISCV Project - Milestone #1
# Group 5: Program Input with Error Checking + Opcode Output
# ============================================================
# Group 5 Control Hazard Scheme: Pipeline Freeze
# ============================================================

# Group 2,5: LW, SW, AND, OR, ORI, BLT, BGE
# Supported instructions for Group 5
R_TYPE = {"AND", "OR"}
I_TYPE = {"ORI", "LW"}
S_TYPE = {"SW"}
B_TYPE = {"BLT", "BGE"}
DIRECTIVE = {".WORD"}
SUPPORTED_INSTRUCTIONS = R_TYPE | I_TYPE | S_TYPE | B_TYPE | DIRECTIVE

# Regular expressions for validation
REGISTER_PATTERN = re.compile(r'^x([0-9]|[1-2][0-9]|3[0-1])$')
IMMEDIATE_PATTERN = re.compile(r'^-?[0-9]+$')
HEX_PATTERN = re.compile(r'^0x[0-9a-fA-F]+$')
LABEL_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*:$')

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
        self.status_var.set("Made by Sean Regindin, Marvien Castillo, Mikaela Herrera")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief='sunken')
        status_bar.pack(side='bottom', fill='x')

    def create_program_tab(self):
        """Create the program input tab."""
        self.frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(self.frame, text="Program Input")
        self.frame.columnconfigure(1, weight=1)
        self.add_entry(event=None)
        
    def create_register_tab(self):
        """Create the register input tab."""
        frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(frame, text="Register Input")
    
    def create_memory_tab(self):
        """Create the memory input tab."""
        frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(frame, text="Memory Input")
    
    def create_memory_table(self, parent):
        """Create memory table for data segment."""
        # Create frame with scrollbar
        table_frame = tk.Frame(parent, bg="#D3D3D3", bd=3)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
    
    def create_opcode_tab(self):
        """Create the opcode output tab."""
        frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(frame, text="Opcode Output")
        
    def create_buttons(self):
        frame = tk.Frame(self.root, bg="#D3D3D3", bd=1, relief="sunken")
        frame.pack(fill='x', side='top', padx=10, pady=(10,0))
        self.runButton = Button(frame, text="Run", width=3, command=self.run_program)
        self.runButton.pack(side="right")
        self.runButton["state"] = "disabled"
        self.checkButton = Button(frame, text="Check", width=5, command=self.check_program)
        self.checkButton.pack(side="right")

    def run_program(self):
        """Run the program (placeholder)."""
        messagebox.showinfo("Run", "Running the program... (not implemented)")

    # when the user hit enter
    def hit_enter(self, event):
        current_entry = event.widget
        instruction = current_entry.get() 
        try: 
            widget_index = self.entry_widgets.index(current_entry)
        except ValueError:
            print("Error")
            return "break" 
        last_index = self.entry_row_count - 1
        if widget_index == last_index: # if current focus is the last entry then it will create a new entry
            self.add_entry(event)
        else: 
            # if the current entry is not the last then it will focus on the next entry
            if((widget_index + 1) < self.entry_row_count):
                self.entry_widgets[widget_index + 1].focus_set()
    
    def disable_run(self, event):
        """Disable the Run button."""
        self.runButton["state"] = "disabled"

    # Add new entry
    def add_entry(self, event):
        self.entry_row_count += 1
        current_row = self.entry_row_count
        # for row indicator 
        line_label = tk.Label(self.frame, text=str(current_row))
        line_label.grid(row=current_row, column=0, sticky='w')
        # text input field
        self.new_entry = tk.Entry(self.frame, bg="#D3D3D3", width=50)
        self.new_entry.grid(row=current_row, column=1, padx=(5,0), pady=2, sticky='ew')
        # add it to widget list so that it can be get() and will be process later
        self.entry_widgets.append(self.new_entry)
        self.line_labels.append(line_label)
        self.new_entry.focus_set()
        self.new_entry.bind("<Return>", self.hit_enter) # if enter is 
        self.new_entry.bind("<BackSpace>", self.disable_run) # if backspace is pressed
        self.new_entry.bind("<Delete>", self.disable_run) # if delete is pressed
        self.new_entry.bind("<Key>", self.disable_run) # if any key is pressed

    def check_program(self):
        """Check the program for errors and display results."""
        errors = []
        warnings = []
        valid_instructions = 0
        
        # Collect all non-empty instructions
        instructions = []
        for i, entry in enumerate(self.entry_widgets):
            line_text = entry.get().strip()
            if line_text:
                instructions.append((i + 1, line_text))
        
        if not instructions:
            messagebox.showwarning("No Program", "Please enter some instructions to check.")
            return
            
        # Validate each instruction
        for line_num, instruction in instructions:
            error = self.validate_instruction(line_num, instruction)
            if error:
                errors.append(error)
            else:
                valid_instructions += 1
                
        # Prepare result message
        if errors:
            result_message = f"VALIDATION FAILED\n\n"
            result_message += f"Errors found: {len(errors)}\n"
            result_message += f"Valid instructions: {valid_instructions}\n\n"
            result_message += "ERROR DETAILS:\n" + "\n".join(errors)
            messagebox.showerror("Program Check Results", result_message)
            self.status_var.set(f"Check failed: {len(errors)} error(s) found")
            self.runButton["state"] = "disabled"
        else:
            result_message = f"PROGRAM VALID\n\n"
            result_message += f"Valid instructions: {valid_instructions}\n"
            result_message += "All instructions are syntactically correct!"
            messagebox.showinfo("Program Check Results", result_message)
            self.status_var.set(f"Check passed: {valid_instructions} valid instruction(s)")
            self.runButton["state"] = "active"
            
    def validate_instruction(self, line_num, instruction):
        """Validate a single instruction and return error message if invalid."""
        # Remove comments
        instruction = instruction.split('#')[0].strip()
        if not instruction:
            return None
            
        # Check for label
        if LABEL_PATTERN.match(instruction):
            return None  # Labels are valid
            
        parts = re.split(r'[,\s()]+', instruction)
        parts = [p for p in parts if p]
        
        if not parts:
            return None
            
        mnemonic = parts[0].upper()
        
        # Check if instruction is supported
        if mnemonic not in SUPPORTED_INSTRUCTIONS:
            return f"Line {line_num}: Unsupported instruction '{mnemonic}'"
            
        # Validate based on instruction type
        if mnemonic in R_TYPE:  # AND, OR
            if len(parts) != 4:
                return f"Line {line_num}: {mnemonic} requires 3 operands (rd, rs1, rs2)"
            for reg in parts[1:4]:
                if not REGISTER_PATTERN.match(reg):
                    return f"Line {line_num}: Invalid register '{reg}' in {mnemonic}"
                    
        elif mnemonic in I_TYPE:  # ORI, LW
            if mnemonic == "LW":
                if len(parts) != 3:
                    return f"Line {line_num}: LW requires 2 operands (rd, offset(rs1))"
                if not REGISTER_PATTERN.match(parts[1]):
                    return f"Line {line_num}: Invalid destination register '{parts[1]}' in LW"
                # Check offset(rs1) format
                if not re.match(r'.*\(.*\)', parts[2]):
                    return f"Line {line_num}: Invalid memory operand format '{parts[2]}' in LW"
            else:  # ORI
                if len(parts) != 4:
                    return f"Line {line_num}: ORI requires 3 operands (rd, rs1, immediate)"
                if not REGISTER_PATTERN.match(parts[1]) or not REGISTER_PATTERN.match(parts[2]):
                    return f"Line {line_num}: Invalid register in ORI"
                if not (IMMEDIATE_PATTERN.match(parts[3]) or HEX_PATTERN.match(parts[3])):
                    return f"Line {line_num}: Invalid immediate '{parts[3]}' in ORI"
                    
        elif mnemonic in S_TYPE:  # SW
            if len(parts) != 3:
                return f"Line {line_num}: SW requires 2 operands (rs2, offset(rs1))"
            if not REGISTER_PATTERN.match(parts[1]):
                return f"Line {line_num}: Invalid source register '{parts[1]}' in SW"
            # Check offset(rs1) format
            if not re.match(r'.*\(.*\)', parts[2]):
                return f"Line {line_num}: Invalid memory operand format '{parts[2]}' in SW"
                
        elif mnemonic in B_TYPE:  # BLT, BGE
            if len(parts) != 4:
                return f"Line {line_num}: {mnemonic} requires 3 operands (rs1, rs2, offset)"
            for i in range(1, 3):  # First two operands are registers
                if not REGISTER_PATTERN.match(parts[i]):
                    return f"Line {line_num}: Invalid register '{parts[i]}' in {mnemonic}"
            # Third operand can be immediate or label (basic check)
            if not (IMMEDIATE_PATTERN.match(parts[3]) or HEX_PATTERN.match(parts[3])):
                # Might be a label - we'll assume it's valid for now
                pass
                
        elif mnemonic in DIRECTIVE:  # .WORD
            if len(parts) != 2:
                return f"Line {line_num}: .WORD requires 1 operand"
            if not (IMMEDIATE_PATTERN.match(parts[1]) or HEX_PATTERN.match(parts[1])):
                return f"Line {line_num}: Invalid value '{parts[1]}' for .WORD directive"
                
        return None  # No error

def main():
    """Main function to run the GUI."""
    root = tk.Tk()
    app = RiscVGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()