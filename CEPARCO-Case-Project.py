import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Button
from tkinter.constants import DISABLED, NORMAL
import re
import math
import random

# ============================================================
# μRISCV Project - Pipeline Freeze mode with full pipeline table
# ============================================================

# ===== MEMORY LAYOUT CONSTANTS (REQUIRED BY SPEC) =====
DATA_START = 0x0000
DATA_END   = 0x007F    # 128 bytes
PROG_START = 0x0080
PROG_END   = 0x00FF

# Supported instructions (Group 2,5: LW, SW, AND, OR, ORI, BLT, BGE)
R_TYPE = {"AND": {"0110011": "111"}, "OR": {"0110011": "110"}}
I_TYPE = {"ORI": {"0010011": "110"}, "LW": {"0000011": "010"}}
S_TYPE = {"SW": {"0100011": "010"}}
B_TYPE = {"BLT": {"1100011": "100"}, "BGE": {"1100011": "101"}}
DIRECTIVE = {".WORD"}
SUPPORTED_INSTRUCTIONS = set(R_TYPE.keys()) | set(I_TYPE.keys()) | set(S_TYPE.keys()) | set(B_TYPE.keys()) | DIRECTIVE

# Architectural registers - Using a list for easier management
REGISTER_FILE = [0] * 32
REGISTER_FILE[0] = 0  # x0 is always 0

# Patterns
REGISTER_PATTERN = re.compile(r'^x([0-9]|[1-2][0-9]|3[0-1])$')
IMMEDIATE_PATTERN = re.compile(r'^-?[0-9]+$')
HEX_PATTERN = re.compile(r'^0x[0-9a-fA-F]+$')

# Color palette (editable). Each unique instruction IR will be assigned a color from this palette in order.
PALETTE = [
    "#FFB3BA", "#FFDFBA", "#FFFFBA", "#BAFFC9", "#BAE1FF",
    "#D7BAFF", "#FFC2E2", "#C2FFD8", "#FCE2C6", "#BDE0FE",
    "#F7D6E0", "#DFF7E0", "#E0F7F3", "#F0E6F6", "#E6F0E6",
    "#F0E6E6", "#E6EAF0", "#FFF5BA", "#E8FFBA", "#BACBFF"
]


class RiscVGUI:
    def __init__(self, root):
        self.reg_entries = []
        self.reg_dec_labels = []
        self.entry_row_count = 0
        self.entry_widgets = []
        self.line_labels = []
        self.root = root
        self.root.title("μRISCV Assembler Simulator - Pipeline Freeze")
        self.root.geometry("1300x780")

        # pipeline registers / state
        self.pipeline_state = {
            'PC': PROG_START,
            'IF_ID': {'IR': 0, 'NPC': 0, 'PC': 0},
            'ID_EX': {'A': 0, 'B': 0, 'IMM': 0, 'IR': 0, 'NPC': 0},
            'EX_MEM': {'ALUOUTPUT': 0, 'cond': 0, 'IR': 0, 'B': 0},
            'MEM_WB': {'LMD': 0, 'IR': 0, 'ALUOUTPUT': 0},
            'WB': {'IR': 0, 'RD': 0, 'VALUE': 0}  
        }

        # Keep history per cycle for the pipeline table representation
        self.pipeline_history = []

        # map IR -> color
        self.ir_color_map = {}
        self.next_color_index = 0

        self.cycle_count = 0
        self.is_running = False
        self.program_memory = {}

        # Expanded memory range: 0x0000 .. 0x00FF
        self.memory_low = DATA_START
        self.memory_high = PROG_END
        self.memory = {addr: 0 for addr in range(self.memory_low, self.memory_high + 1)}
        self.memory_entries = {}

        self.create_buttons()
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        self.create_program_tab()
        self.create_register_tab()
        self.create_memory_tab()
        self.create_opcode_tab()
        self.create_pipeline_state_tab()
        self.create_pipeline_table_tab()

        self.status_var = tk.StringVar()
        self.status_var.set("μRISCV - Pipeline Freeze mode | Color-coded pipeline map")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief='sunken')
        status_bar.pack(side='bottom', fill='x')

    def zero_bubble(self):
        """Return a zeroed pipeline bubble state"""
        return {'A': 0, 'B': 0, 'IMM': 0, 'IR': 0, 'NPC': 0}

    # -------------------------
    # UI Creation
    # -------------------------
    def create_program_tab(self):
        self.frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(self.frame, text="Program Input")
        self.canvas = tk.Canvas(self.frame, bg="#D3D3D3", highlightthickness=0)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.v_scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas.yview)
        self.v_scrollbar.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        self.inner_frame = tk.Frame(self.canvas, bg="#D3D3D3")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor="nw")
        self.inner_frame.columnconfigure(1, weight=1)
        self.inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.add_entry(event=None)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=self.canvas.winfo_width())

    def create_register_tab(self):
        self.frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(self.frame, text="Register Tab")
        self.canvas1 = tk.Canvas(self.frame, bg="#D3D3D3", highlightthickness=0)
        self.canvas1.pack(side="left", fill="both", expand=True)
        self.v_scrollbar = ttk.Scrollbar(self.frame, orient="vertical", command=self.canvas1.yview)
        self.v_scrollbar.pack(side="right", fill="y")
        self.canvas1.configure(yscrollcommand=self.v_scrollbar.set)
        self.innerFrame = tk.Frame(self.canvas1, bg="#D3D3D3")
        self.canvas_window = self.canvas1.create_window((0, 0), window=self.innerFrame, anchor="nw")
        self.innerFrame.columnconfigure(1, weight=1)

        # Headers
        ttk.Label(self.innerFrame, text="Reg", font=('Arial', 10, 'bold'), anchor="center").grid(row=0, column=0, padx=5, pady=5, sticky='ew')
        ttk.Label(self.innerFrame, text="Value (Hex)", font=('Arial', 10, 'bold'), anchor="center").grid(row=0, column=1, pady=5, sticky='ew')
        ttk.Label(self.innerFrame, text="Value (Dec)", font=('Arial', 10, 'bold'), anchor="center").grid(row=0, column=2, pady=5, sticky='ew')

        self.reg_entries = []
        self.reg_dec_labels = []

        for i in range(32):
            reg_name = f"x{i}"
            ttk.Label(self.innerFrame, text=reg_name).grid(row=i + 1, column=0, padx=5, sticky='w')
            
            # Hex entry
            entry = tk.Entry(self.innerFrame, width=15)
            entry.grid(row=i + 1, column=1, padx=5, pady=1)
            entry.insert(0, f"0x{REGISTER_FILE[i]:08x}")
            entry.config(state='readonly', bg='#D3D3D3' if i == 0 else 'white')
            self.reg_entries.append(entry)
            
            # Decimal label
            dec_label = ttk.Label(self.innerFrame, text=str(REGISTER_FILE[i]))
            dec_label.grid(row=i + 1, column=2, padx=5, pady=1)
            self.reg_dec_labels.append(dec_label)

        # PC display
        ttk.Label(self.innerFrame, text="PC").grid(row=33, column=0, padx=5, sticky='w')
        self.pc_entry = tk.Entry(self.innerFrame, width=15)
        self.pc_entry.grid(row=33, column=1, padx=5, pady=1)
        self.pc_entry.insert(0, f"0x{self.pipeline_state['PC']:08x}")
        self.pc_entry.config(state='readonly')

        self.innerFrame.bind("<Configure>", lambda e: self.canvas1.configure(scrollregion=self.canvas1.bbox("all")))

    def create_memory_tab(self):
        self.memory_frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(self.memory_frame, text="Memory Input")
        self.create_memory_table(self.memory_frame)

        goto_frame = tk.Frame(self.memory_frame, bg="#D3D3D3")
        goto_frame.pack(fill='x', padx=10, pady=5)
        tk.Label(goto_frame, text="GOTO Address (hex):", bg="#D3D3D3").pack(side='left')
        self.goto_entry = tk.Entry(goto_frame, width=10)
        self.goto_entry.pack(side='left', padx=5)
        self.goto_entry.insert(0, "0x0000")
        goto_button = tk.Button(goto_frame, text="GOTO", command=self.goto_memory)
        goto_button.pack(side='left', padx=5)

    def create_memory_table(self, parent):
        table_frame = tk.Frame(parent, bg="#D3D3D3", bd=3)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)

        canvas = tk.Canvas(table_frame, bg="#D3D3D3")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#D3D3D3")

        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        headers = ["Address", "Value"]
        for col, header in enumerate(headers):
            label = tk.Label(scrollable_frame, text=header, font=('Arial', 10, 'bold'), bg="#D3D3D3", width=20)
            label.grid(row=0, column=col, padx=5, pady=2)

        # Word-aligned addresses
        row_idx = 1
        for addr in range(self.memory_low, self.memory_high + 1, 4):
            addr_label = tk.Label(scrollable_frame, text=f"0x{addr:04x}", bg="#D3D3D3", width=20)
            addr_label.grid(row=row_idx, column=0, padx=5, pady=1)
            entry = tk.Entry(scrollable_frame, width=20)
            entry.grid(row=row_idx, column=1, padx=5, pady=1)
            entry.insert(0, f"0x{self.read_word(addr):08x}")
            self.memory_entries[addr] = entry
            entry.bind('<FocusOut>', lambda e, addr=addr: self.update_memory_value(addr))
            row_idx += 1

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.mem_canvas = canvas
        self.mem_scrollable_frame = scrollable_frame

    def read_word(self, addr):
        """Read 4 bytes as a word (little-endian)"""
        if addr % 4 != 0:
            return 0
        b0 = self.memory.get(addr, 0)
        b1 = self.memory.get(addr + 1, 0)
        b2 = self.memory.get(addr + 2, 0)
        b3 = self.memory.get(addr + 3, 0)
        return (b3 << 24) | (b2 << 16) | (b1 << 8) | b0

    def write_word(self, addr, value):
        """Write 4 bytes as a word (little-endian)"""
        # Allow writes to both data (0x0000-0x007F) and program (0x0080-0x00FF) memory areas
        if addr < self.memory_low or addr > self.memory_high - 3 or addr % 4 != 0:
            return False

        self.memory[addr] = value & 0xFF
        self.memory[addr + 1] = (value >> 8) & 0xFF
        self.memory[addr + 2] = (value >> 16) & 0xFF
        self.memory[addr + 3] = (value >> 24) & 0xFF
        return True

    def goto_memory(self):
        try:
            addr_str = self.goto_entry.get().strip()
            addr = int(addr_str, 16)
            if addr < self.memory_low or addr > self.memory_high:
                messagebox.showerror("Error", f"Address must be in range 0x{self.memory_low:04x}-0x{self.memory_high:04x}")
                return
            if addr % 4 != 0:
                messagebox.showwarning("Warning", "Address not word-aligned; navigating to nearest word.")
                addr = addr - (addr % 4)
            if addr in self.memory_entries:
                widget = self.memory_entries[addr]
                widget.focus_set()
                try:
                    self.mem_canvas.yview_moveto(widget.winfo_y() / max(1, self.mem_scrollable_frame.winfo_height()))
                except Exception:
                    pass
        except ValueError:
            messagebox.showerror("Error", "Invalid address format")

    def update_memory_value(self, address):
        try:
            entry = self.memory_entries[address]
            value_str = entry.get().strip()
            if value_str.startswith('0x'):
                value = int(value_str, 16)
            else:
                value = int(value_str)
            if value < 0 or value > 0xFFFFFFFF:
                raise ValueError("Value out of range")
            if not self.write_word(address, value):
                raise ValueError("Invalid memory address for write")
            entry.delete(0, tk.END)
            entry.insert(0, f"0x{value:08x}")
        except Exception:
            entry.delete(0, tk.END)
            entry.insert(0, f"0x{self.read_word(address):08x}")
            messagebox.showerror("Error", "Invalid memory value or address")

    def update_memory_display(self):
        for addr, entry in self.memory_entries.items():
            entry.config(state='normal')
            entry.delete(0, tk.END)
            entry.insert(0, f"0x{self.read_word(addr):08x}")
            entry.config(state='readonly')

    def reset_simulation(self):
        """Reset the entire simulation to initial state"""
        self.pipeline_state = {
            'PC': PROG_START,
            'IF_ID': {'IR': 0, 'NPC': 0, 'PC': 0},
            'ID_EX': {'A': 0, 'B': 0, 'IMM': 0, 'IR': 0, 'NPC': 0},
            'EX_MEM': {'ALUOUTPUT': 0, 'cond': 0, 'IR': 0, 'B': 0},
            'MEM_WB': {'LMD': 0, 'IR': 0, 'ALUOUTPUT': 0},
            'WB': {'IR': 0, 'RD': 0, 'VALUE': 0}
        }
        self.pipeline_history.clear()
        self.ir_color_map.clear()
        self.next_color_index = 0
        self.cycle_count = 0
        self.is_running = False
        
        # Reset all registers to 0
        for i in range(32):
            REGISTER_FILE[i] = 0
        REGISTER_FILE[0] = 0
        
        # Reset memory
        for addr in range(self.memory_low, self.memory_high + 1):
            self.memory[addr] = 0
        
        self.update_register_display()
        self.update_memory_display()
        self.update_pipeline_display()
        self.update_pipeline_table()
        self.update_pc_display()
        self.status_var.set("Simulation reset")
        messagebox.showinfo("Reset", "Simulation has been reset")

    # -------------------------
    # Register Display Methods
    # -------------------------
    
    def update_register_display(self):
        """Update all register displays using the REGISTER_FILE"""
        for i in range(32):
            self.reg_entries[i].config(state='normal')
            self.reg_entries[i].delete(0, tk.END)
            self.reg_entries[i].insert(0, f"0x{REGISTER_FILE[i]:08x}")
            self.reg_entries[i].config(state='readonly')
            
            # Update decimal label
            self.reg_dec_labels[i].config(text=str(REGISTER_FILE[i]))
        
        # Update PC display
        self.update_pc_display()

    def update_register_display_from_file(self):
        """Update register display directly from REGISTER_FILE"""
        for i in range(32):
            # Update hex entry
            self.reg_entries[i].config(state='normal')
            self.reg_entries[i].delete(0, tk.END)
            self.reg_entries[i].insert(0, f"0x{REGISTER_FILE[i]:08x}")
            if i == 0:
                self.reg_entries[i].config(state='readonly', bg='#E0E0E0')
            else:
                self.reg_entries[i].config(state='readonly', bg='white')
            
            # Update decimal label
            self.reg_dec_labels[i].config(text=str(REGISTER_FILE[i]))

    # -------------------------
    # Pipeline: core functions
    # -------------------------
    
    def step_execution(self):
        """Execute one pipeline cycle"""
        if not self.program_memory:
            messagebox.showwarning("No Program", "No valid program loaded")
            return

        # For the very first step after loading program, prime the pipeline
        if self.cycle_count == 0 and self.pipeline_state['IF_ID']['IR'] == 0:
            print("Priming pipeline - first cycle")
            self.instruction_fetch()
            if self.pipeline_state['IF_ID']['IR']:
                self.set_register_values_for_instruction()
            self.cycle_count += 1
            self.record_pipeline_snapshot()
            self.update_pipeline_display()
            self.update_pipeline_table()
            self.update_pc_display()
            self.status_var.set(f"Cycle: {self.cycle_count} - Pipeline primed")
            return

        self.cycle_count += 1
        print(f"\n=== Cycle {self.cycle_count} ===")

        # Record pipeline snapshot before advancement
        self.record_pipeline_snapshot()

        # Pipeline stages in reverse order
        # WB stage - write results to register file
        if self.pipeline_state['WB']['VALUE'] != 0:
            self.write_back()
        
        # MEM stage - handle memory operations
        if self.pipeline_state['EX_MEM']['IR'] != 0:
            self.memory_access()
        else:
            self.pipeline_state['MEM_WB'] = {'LMD': 0, 'IR': 0, 'ALUOUTPUT': 0}
        
        # EX stage - execute instruction
        if self.pipeline_state['ID_EX']['IR'] != 0:
            ex_mem_new, branch_taken = self.execute()
        else:
            ex_mem_new = {'ALUOUTPUT': 0, 'cond': 0, 'IR': 0, 'B': 0}
            branch_taken = False
        
        # ID stage - decode and read registers
        if self.pipeline_state['IF_ID']['IR'] != 0:
            id_ex_new = self.instruction_decode()
        else:
            id_ex_new = {'A': 0, 'B': 0, 'IMM': 0, 'IR': 0, 'NPC': 0}
        
        # Advance pipeline with freeze handling
        self.pipeline_advance(ex_mem_new, id_ex_new, branch_taken)

        # Update displays
        self.update_memory_display()
        self.update_pipeline_display()
        self.update_pipeline_table()

        self.status_var.set(f"Cycle: {self.cycle_count} - PC: 0x{self.pipeline_state['PC']:04x}")

        if self.is_program_complete():
            self.finalize_execution()

    def record_pipeline_snapshot(self):
        """Store human-readable snapshot of pipeline stages"""
        def fmt(v):
            if isinstance(v, int):
                return f"0x{v:08x}" if v != 0 else ""
            return str(v)

        # Compute memory at EX/MEM ALUOUTPUT if valid
        mem_at_addr = ""
        ex_alu = self.pipeline_state['EX_MEM'].get('ALUOUTPUT', 0)
        if ex_alu and (DATA_START <= ex_alu <= DATA_END - 3) and ex_alu % 4 == 0:
            mem_at_addr = f"0x{self.read_word(ex_alu):08x}"

        # Compute writeback register name/value if available
        wb_rd_str = ""
        memwb_ir = self.pipeline_state['MEM_WB'].get('IR', 0)
        if memwb_ir:
            inst_bin = format(memwb_ir, '032b')
            rd = int(inst_bin[20:25], 2)
            if rd != 0:
                wb_rd_str = f"x{rd}=0x{REGISTER_FILE[rd]:08x}"
            else:
                wb_rd_str = "x0=0x00000000"

        snap = {
            'IF/ID.IR': fmt(self.pipeline_state['IF_ID'].get('IR', 0)),
            'IF/ID.NPC': fmt(self.pipeline_state['IF_ID'].get('NPC', 0)),
            'PC': fmt(self.pipeline_state.get('PC', 0)),
            'ID/EX.A': fmt(self.pipeline_state['ID_EX'].get('A', 0)),
            'ID/EX.B': fmt(self.pipeline_state['ID_EX'].get('B', 0)),
            'ID/EX.IMM': str(self.pipeline_state['ID_EX'].get('IMM', 0)) if self.pipeline_state['ID_EX'].get('IMM', 0) != 0 else "",
            'ID/EX.IR': fmt(self.pipeline_state['ID_EX'].get('IR', 0)),
            'ID/EX.NPC': fmt(self.pipeline_state['ID_EX'].get('NPC', 0)),
            'EX/MEM.ALUOUTPUT': fmt(self.pipeline_state['EX_MEM'].get('ALUOUTPUT', 0)),
            'EX/MEM.IR': fmt(self.pipeline_state['EX_MEM'].get('IR', 0)),
            'EX/MEM.B': fmt(self.pipeline_state['EX_MEM'].get('B', 0)),
            'EX/MEM.COND': str(self.pipeline_state['EX_MEM'].get('cond', 0)) if self.pipeline_state['EX_MEM'].get('cond', 0) else "",
            'MEM/WB.LMD': fmt(self.pipeline_state['MEM_WB'].get('LMD', 0)),
            'MEM/WB.IR': fmt(self.pipeline_state['MEM_WB'].get('IR', 0)),
            'MEM/WB.ALUOUTPUT': fmt(self.pipeline_state['MEM_WB'].get('ALUOUTPUT', 0)),
            'MEM[EX/MEM.ALUOUTPUT]': mem_at_addr,
            'WB': wb_rd_str
        }

        self.pipeline_history.append(snap)

        # Assign colors for new instruction IRs
        for key in ['IF/ID.IR', 'ID/EX.IR', 'EX/MEM.IR', 'MEM/WB.IR']:
            val = snap.get(key, "")
            if val and val not in self.ir_color_map:
                color = PALETTE[self.next_color_index % len(PALETTE)]
                self.ir_color_map[val] = color
                self.next_color_index += 1

    def is_program_complete(self):
        """Check if program execution is complete"""
        pc = self.pipeline_state['PC']
        pipeline_empty = (
            self.pipeline_state['IF_ID']['IR'] == 0 and
            self.pipeline_state['ID_EX']['IR'] == 0 and
            self.pipeline_state['EX_MEM']['IR'] == 0 and
            self.pipeline_state['MEM_WB']['IR'] == 0 and
            self.pipeline_state['WB']['IR'] == 0
        )
        return pipeline_empty and (pc not in self.program_memory)

    def finalize_execution(self):
        """Final steps after program completion"""
        instructions = []
        for i, entry in enumerate(self.entry_widgets):
            line_text = entry.get().strip()
            if line_text:
                instructions.append((i + 1, line_text))

        if instructions:
            opcodes = self.generate_opcodes(instructions)
            self.display_opcodes(opcodes)
            self.notebook.select(3)

        self.status_var.set("Execution completed - Opcodes generated")
        self.is_running = False
        self.runButton["state"] = "disabled"
        self.stepButton["state"] = "disabled"

    def memory_access(self):
        """MEM stage: Handle memory operations"""
        ex = self.pipeline_state['EX_MEM']
        instruction = ex.get('IR', 0)

        if not instruction:
            self.pipeline_state['MEM_WB'] = {'LMD': 0, 'IR': 0, 'ALUOUTPUT': 0}
            return

        inst_bin = format(instruction, '032b')
        opcode = inst_bin[25:32]
        funct3 = inst_bin[17:20]
        addr = ex.get('ALUOUTPUT', 0)

        # LW instruction
        if opcode == "0000011" and funct3 == "010":
            # Check if address is within valid memory range and word-aligned
            if self.memory_low <= addr <= self.memory_high - 3 and addr % 4 == 0:
                lmd = self.read_word(addr)
            else:
                lmd = 0
            self.pipeline_state['MEM_WB'] = {
                'LMD': lmd,
                'IR': instruction,
                'ALUOUTPUT': addr
            }
            return

        # SW instruction
        if opcode == "0100011" and funct3 == "010":
            data = ex.get('B', 0)
            # Check if address is within valid memory range and word-aligned
            if self.memory_low <= addr <= self.memory_high - 3 and addr % 4 == 0:
                self.write_word(addr, data)
            self.pipeline_state['MEM_WB'] = {
                'LMD': 0,
                'IR': instruction,
                'ALUOUTPUT': addr
            }
            return

        # Other instructions (ALU operations)
        self.pipeline_state['MEM_WB'] = {
            'LMD': 0,
            'IR': instruction,
            'ALUOUTPUT': ex.get('ALUOUTPUT', 0)
        }

    def write_back(self):
        """WB stage: Write results to register file"""
        wb = self.pipeline_state['WB']
        instruction = wb.get('IR', 0)
        rd = wb.get('RD', 0)
        value = wb.get('VALUE', 0)

        if not instruction:
            return

        print(f"WB Stage: Instruction {instruction:08x}, rd=x{rd}, value=0x{value:08x}")

        # Only write to non-zero registers
        if rd != 0:
            REGISTER_FILE[rd] = value & 0xFFFFFFFF
            print(f"  Writing: x{rd} = 0x{value:08x}")

        # Ensure x0 is always zero
        REGISTER_FILE[0] = 0
        
        # Update display after writing
        self.update_register_display_from_file()
        self.pipeline_state['WB']['VALUE'] = 0

    def pipeline_advance(self, ex_mem_new=None, id_ex_new=None, branch_taken=False):
        """Advance pipeline registers with pipeline-freeze policy for branches"""
        if ex_mem_new is None:
            ex_mem_new = {'ALUOUTPUT': 0, 'cond': 0, 'IR': 0, 'B': 0}
        if id_ex_new is None:
            id_ex_new = {'A': 0, 'B': 0, 'IMM': 0, 'IR': 0, 'NPC': 0}

        print(f"Pipeline Advance: branch_taken={branch_taken}")

        # WB <- MEM_WB
        self.pipeline_state['WB'] = {
            'IR': self.pipeline_state['MEM_WB']['IR'],
            'RD': self.get_rd_from_instruction(self.pipeline_state['MEM_WB']['IR']),
            'VALUE': self.get_writeback_value(self.pipeline_state['MEM_WB'])
        }

        # MEM_WB <- EX_MEM
        self.pipeline_state['MEM_WB'] = {
            'LMD': 0,
            'IR': self.pipeline_state['EX_MEM']['IR'],
            'ALUOUTPUT': self.pipeline_state['EX_MEM']['ALUOUTPUT']
        }

        # EX/MEM becomes ex_mem_new (computed by EX stage)
        self.pipeline_state['EX_MEM'] = ex_mem_new

        # Handle control hazards (pipeline freeze)
        if branch_taken:
            # Pipeline freeze: insert bubble into ID_EX and clear IF/ID
            self.pipeline_state['ID_EX'] = self.zero_bubble()
            self.pipeline_state['IF_ID'] = {'IR': 0, 'NPC': 0, 'PC': 0}
            # Fetch new instruction at branch target
            self.instruction_fetch()
            return

        # Normal flow: move ID/EX
        self.pipeline_state['ID_EX'] = id_ex_new

        # Fetch next instruction
        self.instruction_fetch()

    def get_rd_from_instruction(self, instruction):
        """Extract RD from instruction"""
        if not instruction:
            return 0
        inst_bin = format(instruction, '032b')
        return int(inst_bin[20:25], 2)

    def get_writeback_value(self, mem_wb):
        """Get the value to write back to register file"""
        instruction = mem_wb.get('IR', 0)
        if not instruction:
            return 0
        
        inst_bin = format(instruction, '032b')
        opcode = inst_bin[25:32]
        funct3 = inst_bin[17:20]
        
        if opcode == "0000011" and funct3 == "010":  # LW
            return mem_wb.get('LMD', 0)
        else:
            return mem_wb.get('ALUOUTPUT', 0)

    def instruction_decode(self):
        """ID stage: Decode instruction and prepare for EX stage"""
        instruction = self.pipeline_state['IF_ID']['IR']
        if not instruction:
            return {'A': 0, 'B': 0, 'IMM': 0, 'IR': 0, 'NPC': 0}

        inst_bin = format(instruction, '032b')
        
        rs1 = int(inst_bin[12:17], 2)
        rs2 = int(inst_bin[7:12], 2)

        # Set values for next ID/EX
        id_ex_new = {
            'A': REGISTER_FILE[rs1],
            'B': REGISTER_FILE[rs2],
            'IR': instruction,
            'NPC': self.pipeline_state['IF_ID']['NPC']
        }

        # Set immediate value based on instruction type
        opcode = inst_bin[25:32]
        imm_value = 0
        
        if opcode in ["0010011", "0000011"]:  # I-type (ORI, LW)
            imm_bits = inst_bin[0:12]
            imm_value = int(imm_bits, 2)
            if imm_bits[0] == '1':
                imm_value = imm_value - (1 << 12)
                
        elif opcode == "0100011":  # S-type (SW)
            imm_11_5 = inst_bin[0:7]
            imm_4_0 = inst_bin[20:25]
            imm_bits = imm_11_5 + imm_4_0
            imm_value = int(imm_bits, 2)
            if imm_bits[0] == '1':
                imm_value = imm_value - (1 << 12)
                
        elif opcode == "1100011":  # B-type (BLT, BGE)
            imm_12 = inst_bin[0]
            imm_11 = inst_bin[24]
            imm_10_5 = inst_bin[1:7]
            imm_4_1 = inst_bin[20:24]
            imm_bits = imm_12 + imm_11 + imm_10_5 + imm_4_1 + '0'
            imm_value = int(imm_bits, 2)
            if imm_bits[0] == '1':
                imm_value = imm_value - (1 << 13)

        id_ex_new['IMM'] = imm_value
        print(f"ID Stage: Set IMM = {imm_value} (0x{imm_value & 0xFFFFFFFF:08x}) for instruction 0x{instruction:08x}")

        return id_ex_new

    def set_register_values_for_instruction(self):
        """Legacy method - now using instruction_decode instead"""
        id_ex_new = self.instruction_decode()
        self.pipeline_state['ID_EX'] = id_ex_new

    def instruction_fetch(self):
        """IF stage: Fetch instruction from program memory"""
        pc = self.pipeline_state['PC']

        print(f"IF Stage: PC = 0x{pc:04x}")

        if pc in self.program_memory:
            instruction = self.program_memory[pc]
            self.pipeline_state['IF_ID'] = {
                'IR': instruction,
                'NPC': (pc + 4) & 0xFFFFFFFF,
                'PC': pc
            }
            self.pipeline_state['PC'] = (pc + 4) & 0xFFFFFFFF
            print(f"  Fetched instruction: 0x{instruction:08x} from 0x{pc:04x}")
        else:
            self.pipeline_state['IF_ID'] = {'IR': 0, 'NPC': 0, 'PC': 0}
            print("  No instruction at this PC")

    def execute(self):
        """EX stage: Execute instruction"""
        idex = self.pipeline_state['ID_EX']
        instruction = idex.get('IR', 0)

        ex_mem_new = {'ALUOUTPUT': 0, 'cond': 0, 'IR': 0, 'B': 0}
        branch_taken = False

        if not instruction:
            return ex_mem_new, branch_taken

        inst_bin = format(instruction, '032b')
        opcode = inst_bin[25:32]
        funct3 = inst_bin[17:20]

        rs1_val = idex.get('A', 0)
        rs2_val = idex.get('B', 0)
        imm_val = idex.get('IMM', 0)
        npc_val = idex.get('NPC', 0)

        ex_mem_new['IR'] = instruction
        ex_mem_new['B'] = rs2_val

        print(f"EX Stage: Instruction {instruction:08x}, opcode={opcode}, funct3={funct3}")
        print(f"  rs1_val=0x{rs1_val:08x}, rs2_val=0x{rs2_val:08x}, imm_val={imm_val}")

        # R-type instructions
        if opcode == "0110011":
            if funct3 == "111":  # AND
                result = rs1_val & rs2_val
                print(f"  AND: 0x{rs1_val:08x} & 0x{rs2_val:08x} = 0x{result:08x}")
            elif funct3 == "110":  # OR
                result = rs1_val | rs2_val
                print(f"  OR: 0x{rs1_val:08x} | 0x{rs2_val:08x} = 0x{result:08x}")
            else:
                result = 0
            ex_mem_new['ALUOUTPUT'] = result & 0xFFFFFFFF

        # I-type instructions
        elif opcode == "0010011":
            if funct3 == "110":  # ORI
                zero_extended_imm = imm_val & 0xFFF
                result = rs1_val | zero_extended_imm
                print(f"  ORI: 0x{rs1_val:08x} | 0x{zero_extended_imm:08x} = 0x{result:08x}")
                ex_mem_new['ALUOUTPUT'] = result & 0xFFFFFFFF

        # Load/Store instructions
        elif opcode == "0000011" and funct3 == "010":  # LW
            address = (rs1_val + imm_val) & 0xFFFFFFFF
            print(f"  LW: base=0x{rs1_val:08x} + offset={imm_val} = address 0x{address:08x}")
            ex_mem_new['ALUOUTPUT'] = address

        elif opcode == "0100011" and funct3 == "010":  # SW
            address = (rs1_val + imm_val) & 0xFFFFFFFF
            print(f"  SW: base=0x{rs1_val:08x} + offset={imm_val} = address 0x{address:08x}")
            ex_mem_new['ALUOUTPUT'] = address
            ex_mem_new['B'] = rs2_val

        # Branch instructions
        elif opcode == "1100011":
            branch_taken = False
            if funct3 == "100":  # BLT
                rs1_signed = rs1_val if rs1_val < 0x80000000 else rs1_val - 0x100000000
                rs2_signed = rs2_val if rs2_val < 0x80000000 else rs2_val - 0x100000000
                branch_taken = rs1_signed < rs2_signed
                print(f"  BLT: 0x{rs1_val:08x} ({rs1_signed}) < 0x{rs2_val:08x} ({rs2_signed}) = {branch_taken}")
            elif funct3 == "101":  # BGE
                rs1_signed = rs1_val if rs1_val < 0x80000000 else rs1_val - 0x100000000
                rs2_signed = rs2_val if rs2_val < 0x80000000 else rs2_val - 0x100000000
                branch_taken = rs1_signed >= rs2_signed
                print(f"  BGE: 0x{rs1_val:08x} ({rs1_signed}) >= 0x{rs2_val:08x} ({rs2_signed}) = {branch_taken}")

            ex_mem_new['cond'] = 1 if branch_taken else 0

            if branch_taken:
                branch_target = (npc_val + (imm_val << 1)) & 0xFFFFFFFF
                print(f"  Branch taken! Target: 0x{branch_target:08x}")
                self.pipeline_state['PC'] = branch_target

        return ex_mem_new, branch_taken

    def update_pc_display(self):
        """Update PC display in register tab"""
        self.pc_entry.config(state='normal')
        self.pc_entry.delete(0, tk.END)
        self.pc_entry.insert(0, f"0x{self.pipeline_state['PC']:08x}")
        self.pc_entry.config(state='readonly')

    def update_pipeline_display(self):
        """Update pipeline state display (textual)"""
        self.pipeline_text.config(state=tk.NORMAL)
        self.pipeline_text.delete(1.0, tk.END)

        header = "μRISCV PIPELINE STATE\n" + "=" * 70 + "\n"
        header += f"Cycle: {self.cycle_count} | PC: 0x{self.pipeline_state['PC']:08x}\n"
        header += "=" * 70 + "\n"
        self.pipeline_text.insert(tk.END, header)

        stages = [
            ("IF/ID", self.pipeline_state['IF_ID']),
            ("ID/EX", self.pipeline_state['ID_EX']),
            ("EX/MEM", self.pipeline_state['EX_MEM']),
            ("MEM/WB", self.pipeline_state['MEM_WB']),
            ("WB", self.pipeline_state['WB'])
        ]

        for stage_name, stage_data in stages:
            self.pipeline_text.insert(tk.END, f"\n{stage_name}:\n")
            for reg, value in stage_data.items():
                if isinstance(value, int):
                    display_value = f"0x{value:08x}" if value != 0 else "0x00000000"
                else:
                    display_value = str(value)
                self.pipeline_text.insert(tk.END, f"  {reg}: {display_value}\n")

        self.pipeline_text.config(state=tk.DISABLED)

    # -------------------------
    # Pipeline Table Tab (detailed)
    # -------------------------
    def create_pipeline_table_tab(self):
        """Create a tab that visualizes pipeline progress as a table"""
        self.pipeline_table_frame = tk.Frame(self.notebook, bg="#F8F8F8")
        self.notebook.add(self.pipeline_table_frame, text="Pipeline Map Table")

        control_frame = tk.Frame(self.pipeline_table_frame)
        control_frame.pack(fill='x', pady=5)
        tk.Button(control_frame, text="Clear Table", command=self.clear_pipeline_table).pack(side='right', padx=5)

        self.table_canvas = tk.Canvas(self.pipeline_table_frame, bg='white', height=420)
        self.table_canvas.pack(fill='both', expand=True, padx=10, pady=10)

        legend = tk.Label(self.pipeline_table_frame, text="Legend: each color = one instruction. Rows correspond to pipeline fields (IF/ID.IR, IF/ID.NPC, PC, ID/EX.*, EX/MEM.*, MEM/WB.*, MEM[..], WB).", bg="#F8F8F8", anchor='w', justify='left')
        legend.pack(fill='x')

        self.max_cycles_display = 20
        self.table_cell_w = 120
        self.table_cell_h = 26

        self.table_rows = [
            'IF/ID.IR', 'IF/ID.NPC', 'PC',
            'ID/EX.A', 'ID/EX.B', 'ID/EX.IMM', 'ID/EX.IR', 'ID/EX.NPC',
            'EX/MEM.ALUOUTPUT', 'EX/MEM.IR', 'EX/MEM.B', 'EX/MEM.COND',
            'MEM/WB.LMD', 'MEM/WB.IR', 'MEM/WB.ALUOUTPUT', 'MEM[EX/MEM.ALUOUTPUT]',
            'WB'
        ]

        self.update_pipeline_table()

    def clear_pipeline_table(self):
        self.pipeline_history.clear()
        self.ir_color_map.clear()
        self.next_color_index = 0
        self.cycle_count = 0
        self.table_canvas.delete('all')

    def update_pipeline_table(self):
        """Redraw the pipeline table from the recorded pipeline_history"""
        self.table_canvas.delete('all')

        cols = max(1, min(self.max_cycles_display, len(self.pipeline_history)))
        headers = ['Stage'] + [f'cycle {i+1}' for i in range(cols)]

        # Draw headers
        for c, h in enumerate(headers):
            x0 = c * self.table_cell_w
            y0 = 0
            x1 = x0 + self.table_cell_w
            y1 = y0 + self.table_cell_h
            self.table_canvas.create_rectangle(x0, y0, x1, y1, fill='#4E69A2', outline='black')
            self.table_canvas.create_text(x0 + 5, y0 + 3, anchor='nw', text=h, font=('Arial', 10, 'bold'), fill='white')

        # Draw rows
        for r, row in enumerate(self.table_rows):
            for c in range(cols + 1):
                x0 = c * self.table_cell_w
                y0 = (r + 1) * self.table_cell_h
                x1 = x0 + self.table_cell_w
                y1 = y0 + self.table_cell_h
                
                if c == 0:
                    self.table_canvas.create_rectangle(x0, y0, x1, y1, fill='#9BB0E3', outline='black')
                    self.table_canvas.create_text(x0 + 5, y0 + 3, anchor='nw', text=row, font=('Arial', 9, 'bold'))
                else:
                    self.table_canvas.create_rectangle(x0, y0, x1, y1, fill='white', outline='black')
                    hist_idx = c - 1
                    if hist_idx < len(self.pipeline_history):
                        snap = self.pipeline_history[hist_idx]
                        cell_value = snap.get(row, "")
                        
                        # Special handling for ID/EX.IMM - show both decimal and hex
                        if row == 'ID/EX.IMM' and cell_value:
                            try:
                                imm_val = int(cell_value)
                                if imm_val != 0:
                                    cell_value = f"{imm_val} (0x{imm_val & 0xFFFFFFFF:08x})"
                            except ValueError:
                                pass
                        
                        # Color IR-containing rows
                        if row in ('IF/ID.IR', 'ID/EX.IR', 'EX/MEM.IR', 'MEM/WB.IR') and cell_value:
                            color = self.ir_color_map.get(cell_value, None)
                            if not color:
                                color = PALETTE[self.next_color_index % len(PALETTE)]
                                self.ir_color_map[cell_value] = color
                                self.next_color_index += 1
                            self.table_canvas.create_rectangle(x0 + 2, y0 + 2, x1 - 2, y1 - 2, fill=color, outline='black')
                            self.table_canvas.create_text(x0 + 6, y0 + 4, anchor='nw', text=cell_value, font=('Courier', 9))
                        else:
                            if cell_value:
                                self.table_canvas.create_text(x0 + 6, y0 + 4, anchor='nw', text=cell_value, font=('Courier', 9))

    # -------------------------
    # Program Input and Validation Methods
    # -------------------------

    def hit_enter(self, event):
        current_entry = event.widget
        try:
            widget_index = self.entry_widgets.index(current_entry)
        except ValueError:
            return "break"
        last_index = len(self.entry_widgets) - 1
        if widget_index == last_index:
            self.add_entry(event)
            self.canvas.yview_moveto(1.0)
        elif (widget_index + 1) < len(self.entry_widgets):
            self.entry_widgets[widget_index + 1].focus_set()
        return "break"

    def hit_backspace(self, event):
        current_entry = event.widget
        if self.runButton['state'] == 'normal':
            self.runButton["state"] = "disabled"
        try:
            widget_index = self.entry_widgets.index(current_entry)
        except ValueError:
            return
        current_text = current_entry.get()
        if widget_index != 0 and not current_text:
            self.entry_widgets[widget_index - 1].focus_set()
            current_entry.destroy()
            self.line_labels[widget_index].destroy()
            del self.entry_widgets[widget_index]
            del self.line_labels[widget_index]
            for i in range(len(self.entry_widgets)):
                self.line_labels[i].config(text=str(i + 1))
            self.inner_frame.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            return "break"
        if (self.runButton['state'] == 'active'):
            self.runButton["state"] = "disabled"
        return

    def add_entry(self, event):
        self.entry_row_count += 1
        current_grid_row = self.entry_row_count
        visible_line_num = len(self.entry_widgets) + 1
        line_label = tk.Label(self.inner_frame, text=str(visible_line_num), bg="#D3D3D3")
        line_label.grid(row=current_grid_row, column=0, sticky='w')
        self.new_entry = tk.Entry(self.inner_frame, bg="white", width=100)
        self.new_entry.grid(row=current_grid_row, column=1, padx=5, pady=2, sticky='ew')
        self.entry_widgets.append(self.new_entry)
        self.line_labels.append(line_label)
        self.new_entry.focus_set()
        self.new_entry.bind("<Return>", self.hit_enter)
        self.new_entry.bind("<BackSpace>", self.hit_backspace)
        self.new_entry.bind("<Delete>", self.disable_run)
        self.new_entry.bind("<Key>", self.disable_run)
        self.inner_frame.update_idletasks()
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def disable_run(self, event):
        self.runButton["state"] = "disabled"

    def check_program(self):
        """Validate the program and enable run/step buttons if valid"""
        errors = []
        valid_instructions = 0
        instructions = []
        for i, entry in enumerate(self.entry_widgets):
            line_text = entry.get().strip()
            if line_text:
                instructions.append((i + 1, line_text))
        if not instructions:
            messagebox.showwarning("No Program", "Please enter some instructions to check.")
            return
        for line_num, instruction in instructions:
            error = self.validate_instruction(line_num, instruction)
            if error:
                errors.append(error)
            else:
                valid_instructions += 1
        if errors:
            result_message = f"VALIDATION FAILED\n\nErrors found: {len(errors)}\nValid instructions: {valid_instructions}\n\nERROR DETAILS:\n" + "\n".join(errors)
            messagebox.showerror("Program Check Results", result_message)
            self.status_var.set(f"Check failed: {len(errors)} error(s) found")
            self.runButton["state"] = "disabled"
            self.stepButton["state"] = "disabled"
        else:
            result_message = f"PROGRAM VALID\n\nValid instructions: {valid_instructions}\nAll instructions are syntactically correct!"
            messagebox.showinfo("Program Check Results", result_message)
            self.status_var.set(f"Check passed: {valid_instructions} valid instruction(s)")
            self.runButton["state"] = "active"
            self.stepButton["state"] = "active"
            self.load_program_to_memory()

    def validate_instruction(self, line_num, instruction):
        """Validate a single instruction line"""
        instruction = instruction.split('#')[0].strip()
        if not instruction:
            return None
        if ':' in instruction:
            label_part = instruction.split(':')[0].strip()
            instruction_part = instruction.split(':')[1].strip() if len(instruction.split(':')) > 1 else ""
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', label_part):
                return f"Line {line_num}: Invalid label name '{label_part}'"
            if instruction_part:
                error = self.validate_instruction(line_num, instruction_part)
                if error:
                    return error
            return None
        if instruction.upper().startswith('SW'):
            parts = re.split(r'[, \t]+', instruction)
            parts = [p for p in parts if p]
            if len(parts) < 3:
                return f"Line {line_num}: SW requires 2 operands (rs2, offset(rs1))"
            rs2 = parts[1].rstrip(',')
            offset_rs1 = ' '.join(parts[2:])
            if not REGISTER_PATTERN.match(rs2):
                return f"Line {line_num}: Invalid source register '{rs2}' in SW"
            match = re.match(r'(-?0x[0-9a-fA-F]+|-?[0-9]+)\((\w+)\)', offset_rs1)
            if not match:
                return f"Line {line_num}: Invalid memory operand format '{offset_rs1}' in SW"
            if not REGISTER_PATTERN.match(match.group(2)):
                return f"Line {line_num}: Invalid base register '{match.group(2)}' in SW"
            return None
        parts = re.split(r'[,\s]+', instruction)
        parts = [p for p in parts if p]
        if not parts:
            return None
        mnemonic = parts[0].upper()
        if mnemonic not in SUPPORTED_INSTRUCTIONS:
            return f"Line {line_num}: Unsupported instruction '{mnemonic}'"
        if mnemonic in R_TYPE:
            if len(parts) != 4:
                return f"Line {line_num}: {mnemonic} requires 3 operands (rd, rs1, rs2)"
            for reg in parts[1:4]:
                if not REGISTER_PATTERN.match(reg):
                    return f"Line {line_num}: Invalid register '{reg}' in {mnemonic}"
        elif mnemonic in I_TYPE:
            if mnemonic == "LW":
                if len(parts) != 3:
                    return f"Line {line_num}: LW requires 2 operands (rd, offset(rs1))"
                if not REGISTER_PATTERN.match(parts[1]):
                    return f"Line {line_num}: Invalid destination register '{parts[1]}' in LW"
                offset_rs1_part = parts[2]
                if IMMEDIATE_PATTERN.match(offset_rs1_part) or HEX_PATTERN.match(offset_rs1_part):
                    parts[2] = f"{offset_rs1_part}(x0)"
                    offset_rs1_part = parts[2]
                match = re.match(r'(-?0x[0-9a-fA-F]+|-?[0-9]+)\((\w+)\)', offset_rs1_part)
                if not match:
                    return f"Line {line_num}: Invalid memory operand format '{offset_rs1_part}' in LW"
                if not REGISTER_PATTERN.match(match.group(2)):
                    return f"Line {line_num}: Invalid base register '{match.group(2)}' in LW"
            else:
                if len(parts) != 4:
                    return f"Line {line_num}: ORI requires 3 operands (rd, rs1, immediate)"
                if not REGISTER_PATTERN.match(parts[1]) or not REGISTER_PATTERN.match(parts[2]):
                    return f"Line {line_num}: Invalid register in ORI"
                if not (IMMEDIATE_PATTERN.match(parts[3]) or HEX_PATTERN.match(parts[3])):
                    return f"Line {line_num}: Invalid immediate '{parts[3]}' in ORI"
        elif mnemonic in B_TYPE:
            if len(parts) != 4:
                return f"Line {line_num}: {mnemonic} requires 3 operands (rs1, rs2, offset/label)"
            for i in range(1, 3):
                if not REGISTER_PATTERN.match(parts[i]):
                    return f"Line {line_num}: Invalid register '{parts[i]}' in {mnemonic}"
            imm_or_label = parts[3]
            is_immediate = IMMEDIATE_PATTERN.match(imm_or_label) or HEX_PATTERN.match(imm_or_label)
            is_label = re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', imm_or_label)
            if not (is_immediate or is_label):
                return f"Line {line_num}: Invalid offset or label '{imm_or_label}' in {mnemonic}"
        elif mnemonic in DIRECTIVE:
            if len(parts) != 2:
                return f"Line {line_num}: .WORD requires 1 operand"
            if not (IMMEDIATE_PATTERN.match(parts[1]) or HEX_PATTERN.match(parts[1])):
                return f"Line {line_num}: Invalid value '{parts[1]}' for .WORD directive"
        return None

    # -------------------------
    # Assembler / Encoding Methods
    # -------------------------

    def load_program_to_memory(self):
        """Load validated instructions into program memory"""
        PROG_START = 0x0080
        address = PROG_START

        # Clear program memory
        self.program_memory.clear()

        # Collect non-empty instructions
        lines = []
        for i, entry in enumerate(self.entry_widgets):
            text = entry.get().strip()
            if text:
                lines.append((i + 1, text))

        if not lines:
            print("No lines to load")
            return False

        print(f"Loading {len(lines)} lines into program memory...")

        # First pass: collect labels
        labels = {}
        pc = PROG_START

        for line_num, text in lines:
            clean = text.split("#")[0].strip()

            if ":" in clean:
                label = clean.split(":")[0].strip()
                labels[label] = pc
                inst_after = clean.split(":", 1)[1].strip()
                if inst_after:
                    pc += 4
            else:
                pc += 4

        # Second pass: encode instructions
        pc = PROG_START
        for line_num, text in lines:
            clean = text.split("#")[0].strip()

            # Handle labels
            if ":" in clean:
                before, after = clean.split(":", 1)
                label = before.strip()
                inst = after.strip()
                if inst == "" or inst.isspace():
                    continue
                clean = inst

            try:
                if clean.upper().startswith("SW") or clean.upper().startswith("LW"):
                    parts = re.split(r'[, \t]+', clean)
                    parts = [p for p in parts if p]
                    mnemonic = parts[0].upper()
                    if mnemonic == "LW":
                        rd = parts[1].rstrip(',')
                        offset_rs1 = parts[2]
                        operands = [rd, offset_rs1]
                    else:  # SW
                        rs2 = parts[1].rstrip(',')
                        offset_rs1 = parts[2]
                        operands = [rs2, offset_rs1]
                else:
                    parts = re.split(r'[,\s]+', clean)
                    parts = [p for p in parts if p]
                    mnemonic = parts[0].upper()
                    operands = parts[1:]

                # Encode instruction
                hex_opcode = "00000000"  # Default NOP

                if mnemonic in R_TYPE:
                    hex_opcode = self.encode_r_type(mnemonic, operands)
                elif mnemonic in I_TYPE:
                    hex_opcode = self.encode_i_type(mnemonic, operands)
                elif mnemonic in S_TYPE:
                    hex_opcode = self.encode_s_type(mnemonic, operands)
                elif mnemonic in B_TYPE:
                    # Label resolution for branches
                    if len(operands) >= 3 and operands[2] in labels:
                        offset = labels[operands[2]] - pc
                        modified_operands = operands[0:2] + [str(offset)]
                        hex_opcode = self.encode_b_type(mnemonic, modified_operands)
                    else:
                        hex_opcode = self.encode_b_type(mnemonic, operands)
                elif mnemonic == ".WORD":
                    hex_opcode = self.encode_directive(mnemonic, operands[0])

                # Store encoded instruction as integer
                instruction_value = int(hex_opcode, 16)
                self.program_memory[pc] = instruction_value
                pc += 4

            except Exception as e:
                print(f"Error encoding line {line_num}: {e}")
                messagebox.showerror("Encoding Error", f"Line {line_num}: {e}")
                return False

        print(f"Successfully loaded {len(self.program_memory)} instructions")
        self.debug_program_memory()
        return True

    def encode_r_type(self, instruction, operands):
        opcode = list(R_TYPE[instruction].keys())[0]
        funct3 = R_TYPE[instruction][opcode]
        rd = self.reg_to_bin(operands[0])
        rs1 = self.reg_to_bin(operands[1])
        rs2 = self.reg_to_bin(operands[2])
        funct7 = "0000000"
        binary = funct7 + rs2 + rs1 + funct3 + rd + opcode
        return self.binary_to_hex(binary)

    def debug_program_memory(self):
        """Debug method to check what's in program_memory"""
        print("=== DEBUG program_memory ===")
        if not self.program_memory:
            print("program_memory is EMPTY")
            return

        for addr in sorted(self.program_memory.keys()):
            instruction = self.program_memory[addr]
            print(f"0x{addr:04x}: 0x{instruction:08x}")
        print("=== END DEBUG ===")

    def encode_i_type(self, instruction, operands):
        opcode = list(I_TYPE[instruction].keys())[0]
        funct3 = I_TYPE[instruction][opcode]
        if instruction == "LW":
            rd = self.reg_to_bin(operands[0])
            match = re.match(r'(-?0x[0-9a-fA-F]+|-?[0-9]+)\((\w+)\)', operands[1])
            if not match:
                raise ValueError(f"Invalid LW operand format: {operands[1]}")
            imm = match.group(1)
            rs1 = self.reg_to_bin(match.group(2))
            imm_bin = self.imm_to_bin(imm, 12)
        else:
            rd = self.reg_to_bin(operands[0])
            rs1 = self.reg_to_bin(operands[1])
            imm_bin = self.imm_to_bin(operands[2], 12)
        binary = imm_bin + rs1 + funct3 + rd + opcode
        return self.binary_to_hex(binary)

    def encode_s_type(self, instruction, operands):
        opcode = list(S_TYPE[instruction].keys())[0]
        funct3 = S_TYPE[instruction][opcode]
        rs2 = self.reg_to_bin(operands[0])
        match = re.match(r'(-?0x[0-9a-fA-F]+|-?[0-9]+)\((\w+)\)', operands[1])
        if not match:
            raise ValueError(f"Invalid SW operand format: {operands[1]}")
        imm = match.group(1)
        rs1 = self.reg_to_bin(match.group(2))
        imm_bin = self.imm_to_bin(imm, 12)
        imm_11_5 = imm_bin[0:7]
        imm_4_0 = imm_bin[7:12]
        binary = imm_11_5 + rs2 + rs1 + funct3 + imm_4_0 + opcode
        return self.binary_to_hex(binary)

    def encode_b_type(self, instruction, operands):
        opcode = list(B_TYPE[instruction].keys())[0]
        funct3 = B_TYPE[instruction][opcode]
        rs1 = self.reg_to_bin(operands[0])
        rs2 = self.reg_to_bin(operands[1])
        imm_str = operands[2]
        try:
            if imm_str.startswith('0x'):
                imm = int(imm_str, 16)
            else:
                imm = int(imm_str)
        except ValueError:
            imm = 0
        imm_bin = self.imm_to_bin(imm, 13)
        imm_12 = imm_bin[0]
        imm_11 = imm_bin[1]
        imm_10_5 = imm_bin[2:8]
        imm_4_1 = imm_bin[8:12]
        binary = imm_12 + imm_10_5 + rs2 + rs1 + funct3 + imm_4_1 + imm_11 + opcode
        return self.binary_to_hex(binary)

    def encode_directive(self, directive, operand):
        try:
            if operand.startswith('0x'):
                value = int(operand, 16)
            else:
                value = int(operand)
            if value < -2147483648 or value > 4294967295:
                raise ValueError(f"Value out of 32-bit range: {operand}")
            if value < 0:
                value = (1 << 32) + value
            return format(value & 0xFFFFFFFF, '08x')
        except ValueError:
            raise ValueError(f"Invalid value for .WORD directive: {operand}")

    def reg_to_bin(self, reg):
        if not REGISTER_PATTERN.match(reg):
            raise ValueError(f"Invalid register: {reg}")
        return format(int(reg[1:]), '05b')

    def imm_to_bin(self, imm, bits=12):
        try:
            if isinstance(imm, str) and imm.startswith('0x'):
                imm_val = int(imm, 16)
            else:
                imm_val = int(imm)
            if imm_val < 0:
                imm_val = (1 << bits) + imm_val
            return format(imm_val & ((1 << bits) - 1), f'0{bits}b')
        except ValueError:
            raise ValueError(f"Invalid immediate value: {imm}")

    def binary_to_hex(self, binary_str):
        padding = (4 - len(binary_str) % 4) % 4
        binary_str = '0' * padding + binary_str
        hex_str = ''
        for i in range(0, len(binary_str), 4):
            nibble = binary_str[i:i+4]
            hex_str += format(int(nibble, 2), 'x')
        return hex_str.zfill(8)

    def generate_opcodes(self, instructions):
        """Generate opcodes for display"""
        opcodes = []
        program_counter = PROG_START
        labels = {}
        current_pc = program_counter

        # First pass: collect labels
        for line_num, instruction in instructions:
            clean_instruction = instruction.split('#')[0].strip()
            if not clean_instruction:
                continue

            if ':' in clean_instruction:
                label_part = clean_instruction.split(':')[0].strip()
                instruction_part = clean_instruction.split(':')[1].strip() if len(clean_instruction.split(':')) > 1 else ""
                labels[label_part] = current_pc
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

            if ':' in clean_instruction:
                label_part = clean_instruction.split(':')[0].strip()
                instruction_part = clean_instruction.split(':')[1].strip() if len(clean_instruction.split(':')) > 1 else ""

                # Add label to output
                opcodes.append(f"0x{current_pc:04x}: [LABEL] {label_part}:")
                if instruction_part:
                    try:
                        hex_opcode = self.encode_single_instruction(instruction_part, labels, current_pc)
                        opcodes.append(f"0x{current_pc:04x}: {hex_opcode} // {instruction_part}")
                        current_pc += 4
                    except Exception as e:
                        opcodes.append(f"0x{current_pc:04x}: ERROR - {str(e)} // {instruction_part}")
                        current_pc += 4
            else:
                try:
                    hex_opcode = self.encode_single_instruction(clean_instruction, labels, current_pc)
                    opcodes.append(f"0x{current_pc:04x}: {hex_opcode} // {clean_instruction}")
                    current_pc += 4
                except Exception as e:
                    opcodes.append(f"0x{current_pc:04x}: ERROR - {str(e)} // {clean_instruction}")
                    current_pc += 4

        return opcodes

    def encode_single_instruction(self, instruction, labels, current_pc):
        """Helper method to encode a single instruction"""
        # Parse instruction
        if instruction.upper().startswith("SW") or instruction.upper().startswith("LW"):
            parts = re.split(r'[, \t]+', instruction)
            parts = [p for p in parts if p]
            mnemonic = parts[0].upper()
            if mnemonic == "LW":
                rd = parts[1].rstrip(',')
                offset_rs1 = parts[2]
                operands = [rd, offset_rs1]
            else:  # SW
                rs2 = parts[1].rstrip(',')
                offset_rs1 = parts[2]
                operands = [rs2, offset_rs1]
        else:
            parts = re.split(r'[,\s]+', instruction)
            parts = [p for p in parts if p]
            mnemonic = parts[0].upper()
            operands = parts[1:]

        # Encode instruction
        if mnemonic in R_TYPE:
            return self.encode_r_type(mnemonic, operands)
        elif mnemonic in I_TYPE:
            return self.encode_i_type(mnemonic, operands)
        elif mnemonic in S_TYPE:
            return self.encode_s_type(mnemonic, operands)
        elif mnemonic in B_TYPE:
            # Label resolution for branches
            if len(operands) >= 3 and operands[2] in labels:
                offset = labels[operands[2]] - current_pc
                modified_operands = operands[0:2] + [str(offset)]
                return self.encode_b_type(mnemonic, modified_operands)
            else:
                return self.encode_b_type(mnemonic, operands)
        elif mnemonic == ".WORD":
            return self.encode_directive(mnemonic, operands[0])
        else:
            return "00000000"

    def display_opcodes(self, opcodes):
        self.opcode_text.config(state=tk.NORMAL)
        self.opcode_text.delete(1.0, tk.END)
        if opcodes:
            header = "μRISCV OPCODE OUTPUT\n" + "=" * 60 + "\n"
            header += "Address   Opcode      Instruction\n" + "=" * 60 + "\n"
            self.opcode_text.insert(tk.END, header)
            for opcode_line in opcodes:
                self.opcode_text.insert(tk.END, opcode_line + "\n")
        else:
            self.opcode_text.insert(tk.END, "No opcodes generated.")
        self.opcode_text.config(state=tk.DISABLED)

    def create_pipeline_state_tab(self):
        self.pipeline_frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(self.pipeline_frame, text="Pipeline State")
        self.pipeline_text = scrolledtext.ScrolledText(self.pipeline_frame, bg="white", width=120, height=25, font=("Courier New", 10))
        self.pipeline_text.pack(fill='both', expand=True, padx=10, pady=10)
        self.pipeline_text.config(state=tk.DISABLED)

    def create_opcode_tab(self):
        self.opcode_frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(self.opcode_frame, text="Opcode Output")
        self.opcode_text = scrolledtext.ScrolledText(self.opcode_frame, bg="white", width=120, height=25, font=("Courier New", 10))
        self.opcode_text.pack(fill='both', expand=True, padx=10, pady=10)
        self.opcode_text.config(state=tk.DISABLED)

    def create_buttons(self):
        frame = tk.Frame(self.root, bg="#D3D3D3", bd=1, relief="sunken")
        frame.pack(fill='x', side='top', padx=10, pady=(10, 0))
        self.runButton = Button(frame, text="Run", width=6, command=self.run_program)
        self.runButton.pack(side="right", padx=2)
        self.runButton["state"] = "disabled"
        self.stepButton = Button(frame, text="Step", width=6, command=self.step_execution)
        self.stepButton.pack(side="right", padx=2)
        self.stepButton["state"] = "disabled"
        self.resetButton = Button(frame, text="Reset", width=6, command=self.reset_simulation)
        self.resetButton.pack(side="right", padx=2)
        self.checkButton = Button(frame, text="Check", width=6, command=self.check_program)
        self.checkButton.pack(side="right", padx=2)

    def run_program(self):
        """Run program to completion"""
        if not self.load_program_to_memory():
            messagebox.showwarning("No Program", "No valid program to execute")
            return

        # Reset pipeline state
        self.pipeline_state = {
            'PC': PROG_START,
            'IF_ID': {'IR': 0, 'NPC': 0, 'PC': 0},
            'ID_EX': {'A': 0, 'B': 0, 'IMM': 0, 'IR': 0, 'NPC': 0},
            'EX_MEM': {'ALUOUTPUT': 0, 'cond': 0, 'IR': 0, 'B': 0},
            'MEM_WB': {'LMD': 0, 'IR': 0, 'ALUOUTPUT': 0},
            'WB': {'IR': 0, 'RD': 0, 'VALUE': 0}
        }
        self.pipeline_history.clear()
        self.ir_color_map.clear()
        self.next_color_index = 0
        self.cycle_count = 0

        # Run cycles
        max_cycles = 1000
        while not self.is_program_complete() and self.cycle_count < max_cycles:
            self.step_execution()
            self.root.update()

        if self.cycle_count >= max_cycles:
            messagebox.showwarning("Execution Stopped", "Reached maximum cycle limit")

        self.finalize_execution()

# -------------------------
# main
# -------------------------
def main():
    root = tk.Tk()
    app = RiscVGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()