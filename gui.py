import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Button
from tkinter.constants import DISABLED, NORMAL
import re

# ============================================================
# μRISCV Project - Milestone #1
# Group 5: Program Input with Error Checking + Opcode Output
# ============================================================
# Group 5 Control Hazard Scheme: Pipeline Freeze
# ============================================================

# Group 2,5: LW, SW, AND, OR, ORI, BLT, BGE
# Supported instructions for Group 5
R_TYPE = {"AND": {"0110011": "111"}, "OR": {"0110011": "110"}}
I_TYPE = {"ORI": {"0010011": "110"}, "LW": {"0000011": "010"}}
S_TYPE = {"SW": {"0100011": "010"}}
B_TYPE = {"BLT": {"1100011": "100"}, "BGE": {"1100011": "101"}}
DIRECTIVE = {".WORD"}
SUPPORTED_INSTRUCTIONS = set(R_TYPE.keys()) | set(I_TYPE.keys()) | set(S_TYPE.keys()) | set(B_TYPE.keys()) | DIRECTIVE

# Regular expressions for validation
REGISTER_PATTERN = re.compile(r'^x([0-9]|[1-2][0-9]|3[0-1])$')
IMMEDIATE_PATTERN = re.compile(r'^-?[0-9]+$')
HEX_PATTERN = re.compile(r'^0x[0-9a-fA-F]+$')
LABEL_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*:')

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
        """Create the program input tab with a scrollable area."""
        # Main Frame for the tab content
        self.frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(self.frame, text="Program Input")
        
        # 1. Create Canvas
        self.canvas = tk.Canvas(self.frame, bg="#D3D3D3", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)

        # 2. Create Scrollbar and link it to the canvas
        self.v_scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.v_scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        
        # 3. Create a Frame inside the Canvas
        # All program entries and line numbers will go into this inner frame.
        self.inner_frame = tk.Frame(self.canvas, bg="#D3D3D3")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        
        # Configure the inner frame's column for expansion
        self.inner_frame.columnconfigure(1, weight=1)
        
        # Bind events to update the scroll region
        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.add_entry(event=None)
    
    def _on_frame_configure(self, event):
        """Update the scrollregion of the canvas when the size of the inner frame changes."""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Update the inner frame width to fill the canvas width."""
        self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())

    def _on_frame1_configure(self, event):
        """Update the scrollregion of the canvas when the size of the inner frame changes."""
        self.canvas1.configure(scrollregion=self.canvas1.bbox("all"))
    
    def create_register_tab(self):
        """Create the register input tab."""
        # Main Frame for the tab content
        self.frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(self.frame, text="Register Tab")
        
        # 1. Create Canvas
        self.canvas1 = tk.Canvas(self.frame, bg="#D3D3D3", highlightthickness=0)
        self.canvas1.pack(side="left", fill="both", expand=True)

        # 2. Create Scrollbar and link it to the canvas
        self.v_scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas1.yview)
        self.v_scrollbar.pack(side="right", fill="y")
        self.canvas1.configure(yscrollcommand=self.v_scrollbar.set)
        
        # 3. Create a Frame inside the Canvas
        # All program entries and line numbers will go into this inner frame.
        self.innerFrame = tk.Frame(self.canvas1, bg="#D3D3D3")
        self.canvas_window = self.canvas1.create_window((0, 0), window=self.innerFrame, anchor="nw")
        
        # Configure the inner frame's column for expansion
        self.innerFrame.columnconfigure(1, weight=1)
        ttk.Label(self.innerFrame, text="Reg", font=('Arial', 10, 'bold'),anchor="center").grid(row=0, column=0, padx=5, pady=5,sticky='ew')
        ttk.Label(self.innerFrame, text="Value (Hex)", font=('Arial', 10, 'bold'), anchor="center").grid(row=0, column=1, pady=5,sticky='ew')
        for i in range(32):
            reg_name = f"x{i}"

            ttk.Label(self.innerFrame, text=reg_name).grid(row=i + 1, column=0, padx=5, sticky='w')

            entry = tk.Entry(self.innerFrame, width=15)
            entry.grid(row=i + 1, column=1, padx=5, pady=1)
            entry.insert(i, "0x00000000")
            entry.config(state='readonly', bg='#D3D3D3')
        # Bind events to update the scroll region
        self.innerFrame.bind("<Configure>", self._on_frame1_configure)
    
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
        self.opcode_frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(self.opcode_frame, text="Opcode Output")
        
        # Create scrolled text widget for opcode output
        self.opcode_text = scrolledtext.ScrolledText(
            self.opcode_frame, 
            bg="white", 
            width=80, 
            height=20, 
            font=("Courier New", 10)
        )
        self.opcode_text.pack(fill='both', expand=True, padx=10, pady=10)
        self.opcode_text.config(state=tk.DISABLED)  # Make it read-only initially
        
    def create_buttons(self):
        frame = tk.Frame(self.root, bg="#D3D3D3", bd=1, relief="sunken")
        frame.pack(fill='x', side='top', padx=10, pady=(10,0))
        self.runButton = Button(frame, text="Run", width=3, command=self.run_program)
        self.runButton.pack(side="right")
        self.runButton["state"] = "disabled"
        self.checkButton = Button(frame, text="Check", width=5, command=self.check_program)
        self.checkButton.pack(side="right")

    def run_program(self):
        """Run the program and generate opcode output."""
        # Collect all instructions
        instructions = []
        for i, entry in enumerate(self.entry_widgets):
            line_text = entry.get().strip()
            if line_text:
                instructions.append((i + 1, line_text))
        
        if not instructions:
            messagebox.showwarning("No Program", "No instructions to run.")
            return
        
        # Generate opcodes
        opcodes = self.generate_opcodes(instructions)
        
        # Display in opcode tab
        self.display_opcodes(opcodes)
        
        # Switch to opcode tab
        self.notebook.select(3)  # Select opcode tab (4th tab, 0-indexed)
        
        self.status_var.set("Program executed - Opcodes generated")
        messagebox.showinfo("Run Complete", "Program executed successfully! Check Opcode Output tab.")

    def reg_to_bin(self, reg):
        """Convert register name (e.g., x5) to 5-bit binary string."""
        if not REGISTER_PATTERN.match(reg):
            raise ValueError(f"Invalid register: {reg}")
        return format(int(reg[1:]), '05b')

    def imm_to_bin(self, imm, bits=12):
        """Convert immediate to binary (2's complement for negative values)."""
        try:
            # Handle hex format
            if isinstance(imm, str) and imm.startswith('0x'):
                imm_val = int(imm, 16)
            else:
                imm_val = int(imm)
            
            if imm_val < 0:
                imm_val = (1 << bits) + imm_val
            return format(imm_val, f'0{bits}b')
        except ValueError:
            raise ValueError(f"Invalid immediate value: {imm}")

    def binary_to_hex(self, binary_str):
        """Convert binary string to hexadecimal."""
        # Pad to multiple of 4 bits if necessary
        padding = (4 - len(binary_str) % 4) % 4
        binary_str = '0' * padding + binary_str
        
        # Convert to hex
        hex_str = ''
        for i in range(0, len(binary_str), 4):
            nibble = binary_str[i:i+4]
            hex_str += format(int(nibble, 2), 'x')
        
        return hex_str.zfill(8)  # Ensure 8 hex digits

    def encode_r_type(self, instruction, operands):
        """Encode R-type instructions (AND, OR)."""
        opcode = list(R_TYPE[instruction].keys())[0]
        funct3 = R_TYPE[instruction][opcode]
        
        rd = self.reg_to_bin(operands[0])
        rs1 = self.reg_to_bin(operands[1])
        rs2 = self.reg_to_bin(operands[2])
        funct7 = "0000000"  # Default funct7 for AND/OR
        
        binary = funct7 + rs2 + rs1 + funct3 + rd + opcode
        return self.binary_to_hex(binary)

    def encode_i_type(self, instruction, operands):
        """Encode I-type instructions (ORI, LW)."""
        opcode = list(I_TYPE[instruction].keys())[0]
        funct3 = I_TYPE[instruction][opcode]
        
        if instruction == "LW":
            # LW rd, offset(rs1)
            rd = self.reg_to_bin(operands[0])
            # Parse offset(rs1) format - improved regex to handle hex
            match = re.match(r'(-?0x[0-9a-fA-F]+|-?[0-9]+)\((\w+)\)', operands[1])
            if not match:
                raise ValueError(f"Invalid LW operand format: {operands[1]}")
            imm = match.group(1)
            rs1 = self.reg_to_bin(match.group(2))
            imm_bin = self.imm_to_bin(imm, 12)
        else:  # ORI
            rd = self.reg_to_bin(operands[0])
            rs1 = self.reg_to_bin(operands[1])
            imm_bin = self.imm_to_bin(operands[2], 12)
        
        binary = imm_bin + rs1 + funct3 + rd + opcode
        return self.binary_to_hex(binary)

    def encode_s_type(self, instruction, operands):
        """Encode S-type instructions (SW)."""
        
        opcode = list(S_TYPE[instruction].keys())[0]
        funct3 = S_TYPE[instruction][opcode]
        
        # SW rs2, offset(rs1)
        rs2 = self.reg_to_bin(operands[0])
        
        # Parse offset(rs1) format
        match = re.match(r'(-?0x[0-9a-fA-F]+|-?[0-9]+)\((\w+)\)', operands[1])
        if not match:
            raise ValueError(f"Invalid SW operand format: {operands[1]}")
        
        imm = match.group(1)
        rs1 = self.reg_to_bin(match.group(2))
        
        imm_bin = self.imm_to_bin(imm, 12)
        
        # S-type immediate is split: imm[11:5] + imm[4:0]
        imm_11_5 = imm_bin[0:7]  # bits 11-5
        imm_4_0 = imm_bin[7:12]  # bits 4-0
        
        binary = imm_11_5 + rs2 + rs1 + funct3 + imm_4_0 + opcode
        
        result = self.binary_to_hex(binary)
        
        return result

    def encode_b_type(self, instruction, operands):
        """Encode B-type instructions (BLT, BGE)."""
        opcode = list(B_TYPE[instruction].keys())[0]
        funct3 = B_TYPE[instruction][opcode]
        
        rs1 = self.reg_to_bin(operands[0])
        rs2 = self.reg_to_bin(operands[1])
        
        # Handle immediate (for now, just use the value directly)
        # In a real implementation, you'd handle labels and PC-relative addressing
        imm_str = operands[2]
        try:
            if imm_str.startswith('0x'):
                imm = int(imm_str, 16)
            else:
                imm = int(imm_str)
        except ValueError:
            # If it's not a number, use 0 as placeholder
            imm = 0
        
        imm_bin = self.imm_to_bin(imm, 13)  # B-type uses 13-bit immediate
        
        # B-type immediate field is split: [12|10:5|4:1|11]
        imm_12 = imm_bin[0]
        imm_11 = imm_bin[1]  
        imm_10_5 = imm_bin[2:8]
        imm_4_1 = imm_bin[8:12]
        
        binary = imm_12 + imm_10_5 + rs2 + rs1 + funct3 + imm_4_1 + imm_11 + opcode
        return self.binary_to_hex(binary)

    def encode_directive(self, directive, operand):
        """Encode .WORD directive."""
        try:
            if operand.startswith('0x'):
                value = int(operand, 16)
            else:
                value = int(operand)
            
            # Ensure value fits in 32 bits
            if value < -2147483648 or value > 4294967295:
                raise ValueError(f"Value out of 32-bit range: {operand}")
            
            # Convert to 32-bit hexadecimal
            if value < 0:
                value = (1 << 32) + value
            return format(value, '08x')
        except ValueError:
            raise ValueError(f"Invalid value for .WORD directive: {operand}")

    def generate_opcodes(self, instructions):
        """Generate hexadecimal opcodes for the instructions."""
        opcodes = []
        program_counter = 0x0080  # Program starts at 0x0080
        
        # First pass: collect labels
        labels = {}
        current_pc = program_counter
        
        for line_num, instruction in instructions:
            clean_instruction = instruction.split('#')[0].strip()
            if not clean_instruction:
                continue
                
            # Check for label (could be at start of line or with instruction)
            if ':' in clean_instruction:
                # Handle labels - split by colon
                label_part = clean_instruction.split(':')[0].strip()
                instruction_part = clean_instruction.split(':')[1].strip() if len(clean_instruction.split(':')) > 1 else ""
                
                # Store label address
                labels[label_part] = current_pc
                
                # If there's an instruction, it will be at the current PC
                if instruction_part:
                    current_pc += 4
            else:
                current_pc += 4
        
        # Second pass: generate opcodes
        current_pc = program_counter
        
        for line_num, instruction in instructions:
            clean_instruction = instruction.split('#')[0].strip()
            if not clean_instruction:
                continue
                
            # Handle labels with instructions
            if ':' in clean_instruction:
                label_part = clean_instruction.split(':')[0].strip()
                instruction_part = clean_instruction.split(':')[1].strip() if len(clean_instruction.split(':')) > 1 else ""
                
                opcodes.append(f"0x{current_pc:04x}: [LABEL] {label_part}:")
                
                if instruction_part:
                    # Process the instruction after the label
                    if instruction_part.upper().startswith('SW'):
                        # Special handling for SW instruction
                        parts = instruction_part.split()
                        mnemonic = parts[0].upper()
                        rs2 = parts[1].rstrip(',')
                        offset_rs1 = ' '.join(parts[2:])
                        operands = [rs2, offset_rs1]
                    else:
                        parts = re.split(r'[,\s()]+', instruction_part)
                        parts = [p for p in parts if p]
                        mnemonic = parts[0].upper()
                        operands = parts[1:]
                    
                    if parts:
                        try:
                            if mnemonic in R_TYPE:
                                hex_opcode = self.encode_r_type(mnemonic, operands)
                            elif mnemonic in I_TYPE:
                                hex_opcode = self.encode_i_type(mnemonic, operands)
                            elif mnemonic in S_TYPE:
                                hex_opcode = self.encode_s_type(mnemonic, operands)
                            elif mnemonic in B_TYPE:
                                # For branch instructions, resolve labels
                                if len(operands) >= 3 and operands[2] in labels:
                                    # Calculate offset
                                    offset = labels[operands[2]] - current_pc
                                    modified_parts = operands[0:2] + [str(offset)]
                                    hex_opcode = self.encode_b_type(mnemonic, modified_parts)
                                else:
                                    # Use the original operands if no label resolution
                                    hex_opcode = self.encode_b_type(mnemonic, operands)
                            elif mnemonic in DIRECTIVE:
                                hex_opcode = self.encode_directive(mnemonic, operands[0])
                            else:
                                hex_opcode = "00000000"
                            
                            opcodes.append(f"0x{current_pc:04x}: {hex_opcode} // {instruction_part}")
                            current_pc += 4
                        except Exception as e:
                            opcodes.append(f"0x{current_pc:04x}: ERROR - {str(e)} // {instruction_part}")
                            current_pc += 4
            else:
                # Regular instruction
                if clean_instruction.upper().startswith('SW'):
                    # Special handling for SW instruction
                    parts = clean_instruction.split()
                    mnemonic = parts[0].upper()
                    rs2 = parts[1].rstrip(',')
                    offset_rs1 = ' '.join(parts[2:])
                    operands = [rs2, offset_rs1]
                else:
                    parts = re.split(r'[,\s()]+', clean_instruction)
                    parts = [p for p in parts if p]
                    mnemonic = parts[0].upper()
                    operands = parts[1:]
                
                if not parts:
                    continue
                    
                try:
                    if mnemonic in R_TYPE:
                        hex_opcode = self.encode_r_type(mnemonic, operands)
                    elif mnemonic in I_TYPE:
                        hex_opcode = self.encode_i_type(mnemonic, operands)
                    elif mnemonic in S_TYPE:
                        hex_opcode = self.encode_s_type(mnemonic, operands)
                    elif mnemonic in B_TYPE:
                        # For branch instructions, resolve labels
                        if len(operands) >= 3 and operands[2] in labels:
                            # Calculate offset
                            offset = labels[operands[2]] - current_pc
                            modified_parts = operands[0:2] + [str(offset)]
                            hex_opcode = self.encode_b_type(mnemonic, modified_parts)
                        else:
                            # Use the original operands if no label resolution
                            hex_opcode = self.encode_b_type(mnemonic, operands)
                    elif mnemonic in DIRECTIVE:
                        hex_opcode = self.encode_directive(mnemonic, operands[0])
                    else:
                        hex_opcode = "00000000"
                    
                    opcodes.append(f"0x{current_pc:04x}: {hex_opcode} // {clean_instruction}")
                    current_pc += 4
                except Exception as e:
                    opcodes.append(f"0x{current_pc:04x}: ERROR - {str(e)} // {clean_instruction}")
                    current_pc += 4
        
        return opcodes

    def display_opcodes(self, opcodes):
        """Display generated opcodes in the opcode tab."""
        self.opcode_text.config(state=tk.NORMAL)  # Enable editing
        self.opcode_text.delete(1.0, tk.END)  # Clear previous content
        
        if opcodes:
            header = "μRISCV OPCODE OUTPUT\n"
            header += "=" * 60 + "\n"
            header += "Address   Opcode      Instruction\n"
            header += "=" * 60 + "\n"
            self.opcode_text.insert(tk.END, header)
            
            for opcode_line in opcodes:
                self.opcode_text.insert(tk.END, opcode_line + "\n")
        else:
            self.opcode_text.insert(tk.END, "No opcodes generated.")
        
        self.opcode_text.config(state=tk.DISABLED)  # Make it read-only again

    # when the user hit enter

    def hit_enter(self, event):
        current_entry = event.widget
        try: 
            widget_index = self.entry_widgets.index(current_entry)
        except ValueError:
            print("Error: Widget not found during hit_enter.")
            return "break" 
            
        list_length = len(self.entry_widgets)
        last_index = list_length - 1
        
        # 1. Check if we are at the last line (add new entry)
        if widget_index == last_index:
            self.add_entry(event)
            # Ensure the canvas scrolls to the new entry
            self.canvas.yview_moveto(1.0)
            
        # 2. Otherwise, move focus to the next existing line
        elif (widget_index + 1) < list_length:
            self.entry_widgets[widget_index + 1].focus_set()
        
        # After a successful action (add or focus shift), break the event
        return "break"


    def hit_backspace(self, event):
        current_entry = event.widget
        
        # 1. Disable Run Button
        if self.runButton['state'] == 'normal':
            self.runButton["state"] = "disabled"
            
        try:
            widget_index = self.entry_widgets.index(current_entry)
        except ValueError:
            print("Error: Widget not found during hit_backspace.")
            return 
            
        current_text = current_entry.get()

        # 2. Row deletion logic: if not the first entry AND entry is empty
        if widget_index != 0 and not current_text:
            
            # 1. Set focus to the entry above it
            self.entry_widgets[widget_index - 1].focus_set()
            
            # 2. Destroy the widgets
            current_entry.destroy()
            self.line_labels[widget_index].destroy()

            # 3. Remove from tracking lists
            del self.entry_widgets[widget_index]
            del self.line_labels[widget_index]      
            
            # 4. Re-number subsequent line labels
            for i in range(len(self.entry_widgets)):
                self.line_labels[i].config(text=str(i + 1)) 
                
            # 5. Update scroll region
            self.inner_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            return "break" # Stop default character deletion
        
        return # Allow default Backspace character deletion (if not deleted a row)

    def add_entry(self, event):
        self.entry_row_count += 1 
        current_grid_row = self.entry_row_count # Use the unique counter for placement

        # 1. Determine the VISIBLE line number
        visible_line_num = len(self.entry_widgets) + 1
        
        # 2. Create and place line label (using UNIQUE grid row)
        line_label = tk.Label(self.inner_frame, text=str(visible_line_num), bg="#D3D3D3")
        line_label.grid(row=current_grid_row, column=0, sticky='w') 
        
        # 3. Create and place Entry widget (using UNIQUE grid row)
        self.new_entry = tk.Entry(self.inner_frame, bg="white", width=50)
        self.new_entry.grid(row=current_grid_row, column=1, padx=5, pady=2, sticky='ew') 
        
        # 4. Add to tracking lists
        self.entry_widgets.append(self.new_entry)
        self.line_labels.append(line_label)
        self.new_entry.focus_set()
        
        # 5. Bind events (no change)
        self.new_entry.bind("<Return>", self.hit_enter)
        self.new_entry.bind("<BackSpace>", self.hit_backspace)
        self.new_entry.bind("<Delete>", self.disable_run)
        self.new_entry.bind("<Key>", self.disable_run)
        
        # 6. Update scroll region (no change)
        self.inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))
    def disable_run(self, event):
        """Disable the Run button."""
        self.runButton["state"] = "disabled"


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
            
        # Check for label (could be at start of line or with instruction)
        if ':' in instruction:
            # Handle labels - split by colon
            label_part = instruction.split(':')[0].strip()
            instruction_part = instruction.split(':')[1].strip() if len(instruction.split(':')) > 1 else ""
            
            # Validate label format
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', label_part):
                return f"Line {line_num}: Invalid label name '{label_part}'"
                
            # If there's an instruction after the label, validate it too
            if instruction_part:
                # Recursively validate the instruction part
                error = self.validate_instruction(line_num, instruction_part)
                if error:
                    return error
            return None  # Label is valid
            
        # For SW instructions, we need special handling because of the offset(rs1) format
        if instruction.upper().startswith('SW'):
            # Manual parsing for SW instruction
            parts = instruction.split()
            if len(parts) < 3:
                return f"Line {line_num}: SW requires 2 operands (rs2, offset(rs1))"
            
            mnemonic = parts[0].upper()
            rs2 = parts[1].rstrip(',')  # Remove trailing comma if present
            
            # The rest should be the offset(rs1) part
            offset_rs1 = ' '.join(parts[2:])
            
            if not REGISTER_PATTERN.match(rs2):
                return f"Line {line_num}: Invalid source register '{rs2}' in SW"
            
            # Check offset(rs1) format
            # This is a basic check. A more robust check would parse offset and rs1.
            match = re.match(r'(-?0x[0-9a-fA-F]+|-?[0-9]+)\((\w+)\)', offset_rs1)
            if not match:
                return f"Line {line_num}: Invalid memory operand format '{offset_rs1}' in SW"
            
            # Validate the rs1 inside the parentheses
            if not REGISTER_PATTERN.match(match.group(2)):
                 return f"Line {line_num}: Invalid base register '{match.group(2)}' in SW"
            
            return None
            
        # For other instructions, use the original parsing
        parts = re.split(r'[,\s]+', instruction)
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
                # A robust check of the format, including offset and rs1 validation
                offset_rs1_part = parts[2]
                match = re.match(r'(-?0x[0-9a-fA-F]+|-?[0-9]+)\((\w+)\)', offset_rs1_part)
                if not match:
                    return f"Line {line_num}: Invalid memory operand format '{offset_rs1_part}' in LW"
                if not REGISTER_PATTERN.match(match.group(2)):
                    return f"Line {line_num}: Invalid base register '{match.group(2)}' in LW"
            else:  # ORI
                if len(parts) != 4:
                    return f"Line {line_num}: ORI requires 3 operands (rd, rs1, immediate)"
                if not REGISTER_PATTERN.match(parts[1]) or not REGISTER_PATTERN.match(parts[2]):
                    return f"Line {line_num}: Invalid register in ORI"
                if not (IMMEDIATE_PATTERN.match(parts[3]) or HEX_PATTERN.match(parts[3])):
                    return f"Line {line_num}: Invalid immediate '{parts[3]}' in ORI"
                    
        elif mnemonic in B_TYPE:  # BLT, BGE
            if len(parts) != 4:
                return f"Line {line_num}: {mnemonic} requires 3 operands (rs1, rs2, offset/label)"
            for i in range(1, 3):  # First two operands are registers
                if not REGISTER_PATTERN.match(parts[i]):
                    return f"Line {line_num}: Invalid register '{parts[i]}' in {mnemonic}"
            # Third operand can be immediate (for offset) or label
            imm_or_label = parts[3]
            is_immediate = IMMEDIATE_PATTERN.match(imm_or_label) or HEX_PATTERN.match(imm_or_label)
            is_label = re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', imm_or_label)
            if not (is_immediate or is_label):
                return f"Line {line_num}: Invalid offset or label '{imm_or_label}' in {mnemonic}"
                
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