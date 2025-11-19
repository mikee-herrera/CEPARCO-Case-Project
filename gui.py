import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, Button
from tkinter.constants import DISABLED, NORMAL
import re

# ============================================================
# μRISCV Project 
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

# Architectural registers
REGISTER_FILE = {i: 0 for i in range(32)}
REGISTER_FILE[0] = 0

# Patterns
REGISTER_PATTERN = re.compile(r'^x([0-9]|[1-2][0-9]|3[0-1])$')
IMMEDIATE_PATTERN = re.compile(r'^-?[0-9]+$')
HEX_PATTERN = re.compile(r'^0x[0-9a-fA-F]+$')

class RiscVGUI:
    def __init__(self, root):
        self.reg_entries = {}
        self.entry_row_count = 0
        self.entry_widgets = []
        self.line_labels = []
        self.root = root
        self.root.title("μRISCV Assembler Simulator - Fixed")
        self.root.geometry("980x700")

        # Pipeline state - keep same fields your GUI expects
        self.pipeline_state = {
            'PC': 0x0080,
            'IF_ID': {'IR': 0, 'NPC': 0},
            'ID_EX': {'A': 0, 'B': 0, 'IMM': 0, 'IR': 0, 'NPC': 0},
            'EX_MEM': {'ALUOUTPUT': 0, 'cond': 0, 'IR': 0, 'B': 0},
            'MEM_WB': {'LMD': 0, 'IR': 0, 'ALUOUTPUT': 0}
        }

        self.cycle_count = 0
        self.is_running = False
        self.program_memory = {}
        # Expanded memory range: 0x0000 .. 0x01FF (word addresses shown 0x0000..0x01FC)
        self.memory_low = DATA_START
        self.memory_high = PROG_END
        self.memory = {addr: 0 for addr in range(self.memory_low, self.memory_high + 1)}  # byte addressed storage
        self.memory_entries = {}

        self.create_buttons()
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        self.create_program_tab()
        self.create_register_tab()
        self.create_memory_tab()
        self.create_opcode_tab()
        self.create_pipeline_tab()

        self.status_var = tk.StringVar()
        self.status_var.set("Made by Sean Regindin, Marvien Castillo, Mikaela Herrera - FIXED")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief='sunken')
        status_bar.pack(side='bottom', fill='x')

    # -------------------------
    # UI creation (unchanged besides ranges)
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

    def _on_frame1_configure(self, event):
        self.canvas1.configure(scrollregion=self.canvas1.bbox("all"))

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
        ttk.Label(self.innerFrame, text="Reg", font=('Arial', 10, 'bold'),anchor="center").grid(row=0, column=0, padx=5, pady=5,sticky='ew')
        ttk.Label(self.innerFrame, text="Value (Hex)", font=('Arial', 10, 'bold'), anchor="center").grid(row=0, column=1, pady=5,sticky='ew')
        self.reg_entries = {}
        for i in range(32):
            reg_name = f"x{i}"
            ttk.Label(self.innerFrame, text=reg_name).grid(row=i + 1, column=0, padx=5, sticky='w')
            entry = tk.Entry(self.innerFrame, width=15)
            entry.grid(row=i + 1, column=1, padx=5, pady=1)
            if i == 0:
                entry.insert(0, "0x00000000")
                entry.config(state='readonly', bg='#D3D3D3')
            else:
                entry.insert(0, f"0x{REGISTER_FILE[i]:08x}")
                self.reg_entries[i] = entry
                entry.bind('<FocusOut>', lambda e, reg=i: self.update_register_value(reg))
        self.innerFrame.bind("<Configure>", self._on_frame1_configure)

        # ---- ADD PC display ----
        ttk.Label(self.innerFrame, text="PC").grid(row=33, column=0, padx=5, sticky='w')
        self.pc_entry = tk.Entry(self.innerFrame, width=15)
        self.pc_entry.grid(row=33, column=1, padx=5, pady=1)
        self.pc_entry.insert(0, f"0x{self.pipeline_state['PC']:08x}")
        self.pc_entry.config(state='readonly')
        

    def update_register_value(self, reg):
        try:
            entry = self.reg_entries[reg]
            value_str = entry.get().strip()
            if value_str.startswith('0x'):
                value = int(value_str, 16)
            else:
                value = int(value_str)
            if value < -2147483648 or value > 4294967295:
                raise ValueError("Value out of 32-bit range")
            if value < 0:
                value = (1 << 32) + value
            REGISTER_FILE[reg] = value & 0xFFFFFFFF
            entry.delete(0, tk.END)
            entry.insert(0, f"0x{value:08x}")
        except Exception:
            entry.delete(0, tk.END)
            entry.insert(0, f"0x{REGISTER_FILE[reg]:08x}")
            messagebox.showerror("Error", f"Invalid value for register x{reg}")

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

        # Word-aligned addresses for the expanded range
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
        # read 4 bytes little-endian as a word; addresses are byte addresses
        b0 = self.memory.get(addr, 0)
        b1 = self.memory.get(addr+1, 0)
        b2 = self.memory.get(addr+2, 0)
        b3 = self.memory.get(addr+3, 0)
        return ((b3 << 24) | (b2 << 16) | (b1 << 8) | b0) & 0xFFFFFFFF

    def write_word(self, addr, value):
        # Only allow writes into data segment
        if addr < DATA_START or addr + 3 > DATA_END:
            return False

        # Must be word-aligned
        if addr % 4 != 0:
            return False

        self.memory[addr]   = value & 0xFF
        self.memory[addr+1] = (value >> 8) & 0xFF
        self.memory[addr+2] = (value >> 16) & 0xFF
        self.memory[addr+3] = (value >> 24) & 0xFF
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
                # attempt to scroll canvas so that widget is visible
                try:
                    self.mem_canvas.yview_moveto(widget.winfo_y() / max(1, self.mem_scrollable_frame.winfo_height()))
                except Exception:
                    pass
                messagebox.showinfo("GOTO", f"Navigated to address 0x{addr:04x}")
            else:
                messagebox.showerror("Error", "Address not present in memory display")
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
            # write to byte-addressed memory
            self.write_word(address, value & 0xFFFFFFFF)
            entry.delete(0, tk.END)
            entry.insert(0, f"0x{value:08x}")
        except Exception:
            entry.delete(0, tk.END)
            entry.insert(0, f"0x{self.read_word(address):08x}")
            messagebox.showerror("Error", "Invalid memory value")

    def update_memory_display(self):
        for addr, entry in self.memory_entries.items():
            entry.config(state='normal')
            entry.delete(0, tk.END)
            entry.insert(0, f"0x{self.read_word(addr):08x}")

    def reset_simulation(self):
        self.pipeline_state = {
            'PC': 0x0080,
            'IF_ID': {'IR': 0, 'NPC': 0},
            'ID_EX': {'A': 0, 'B': 0, 'IMM': 0, 'IR': 0, 'NPC': 0},
            'EX_MEM': {'ALUOUTPUT': 0, 'cond': 0, 'IR': 0, 'B': 0},
            'MEM_WB': {'LMD': 0, 'IR': 0, 'ALUOUTPUT': 0}
        }
        self.cycle_count = 0
        self.is_running = False
        for i in range(1, 32):
            self.reg_entries[i].config(state='normal')
            self.reg_entries[i].delete(0, tk.END)
            self.reg_entries[i].insert(0, f"0x{REGISTER_FILE[i]:08x}")
            self.reg_entries[i].config(state='readonly')
        self.update_memory_display()
        self.status_var.set("Simulation reset")
        messagebox.showinfo("Reset", "Simulation has been reset")

    # -------------------------
    # Pipeline: core functions
    # -------------------------
    
    def step_execution(self):
        """
        Perform ONE pipeline cycle (WB -> MEM -> EX -> ID -> IF).
        Stops when the pipeline has reached the same "final visible state" as Run (Option A):
        - no more instructions to fetch (PC not in program_memory)
        - IF/ID, ID/EX, EX/MEM are empty
        In that final state MEM/WB still contains the last committed instruction (visible).
        When this final step finishes, behave like Run: generate opcodes, update displays, disable Run/Step.
        """

        # Ensure program is loaded
        if not self.program_memory:
            self.load_program_to_memory()
        if not self.program_memory:
            messagebox.showwarning("No Program", "No valid program to execute")
            return

        # Evaluate "no more fetch" and earlier-stage emptiness BEFORE doing a step.
        no_more_fetch = (self.pipeline_state['PC'] not in self.program_memory)
        earlier_stages_empty = (
            self.pipeline_state['IF_ID'].get('IR', 0) == 0 and
            self.pipeline_state['ID_EX'].get('IR', 0) == 0 and
            self.pipeline_state['EX_MEM'].get('IR', 0) == 0
        )

        # If we are already at the final visible state, do NOT allow another step.
        # (This prevents the extra blanking step that previously emptied MEM/WB.)
        if no_more_fetch and earlier_stages_empty:
            messagebox.showinfo("Done", "Pipeline already completed. No further steps.")
            return

        # Prime pipeline the same way Run does on first cycle so Step and Run match.
        # If first cycle (cycle_count == 0) and IF_ID empty, fetch first inst.
        if self.cycle_count == 0 and self.pipeline_state['IF_ID'].get('IR', 0) == 0:
            pc0 = self.pipeline_state['PC']
            if pc0 in self.program_memory:
                self.pipeline_state['IF_ID']['IR'] = self.program_memory[pc0]
                self.pipeline_state['IF_ID']['NPC'] = (pc0 + 4) & 0xFFFFFFFF
                self.pipeline_state['PC'] = (pc0 + 4) & 0xFFFFFFFF

        # ---- perform one pipeline cycle ----
        self.cycle_count += 1

        # 1) Write-back
        self.write_back()

        # 2) Memory stage
        self.memory_access()

        # 3) Execute stage => produces EX/MEM dict
        ex_mem_new = self.execute_current_instruction()
        branch_taken = (ex_mem_new.get('cond', 0) == 1)

        # 4) Advance pipeline (handles freeze on branch)
        self.pipeline_advance(ex_mem_new=ex_mem_new, branch_taken=branch_taken)

        # 5) GUI updates
        self.update_register_display()
        self.update_memory_display()
        self.update_pipeline_display()

        # update PC widget if present
        try:
            self.pc_entry.config(state='normal')
            self.pc_entry.delete(0, tk.END)
            self.pc_entry.insert(0, f"0x{self.pipeline_state['PC']:08x}")
            self.pc_entry.config(state='readonly')
        except Exception:
            # pc_entry might not exist if you didn't add it — ignore silently
            pass

        self.status_var.set(f"Cycle: {self.cycle_count} - PC: 0x{self.pipeline_state['PC']:08x}")

        # ---- After the cycle, check if we've reached the final visible stop condition ----
        no_more_fetch = (self.pipeline_state['PC'] not in self.program_memory)
        earlier_stages_empty = (
            self.pipeline_state['IF_ID'].get('IR', 0) == 0 and
            self.pipeline_state['ID_EX'].get('IR', 0) == 0 and
            self.pipeline_state['EX_MEM'].get('IR', 0) == 0
        )

        # If we've drained IF/ID, ID/EX, EX/MEM and there's nothing left to fetch,
        # then we are in the final visible state (MEM/WB still contains last instruction).
        if no_more_fetch and earlier_stages_empty:
            # Finalize exactly like Run: generate opcodes, show opcode tab, disable buttons
            instructions = []
            for i, entry in enumerate(self.entry_widgets):
                line_text = entry.get().strip()
                if line_text:
                    instructions.append((i + 1, line_text))

            if instructions:
                opcodes = self.generate_opcodes(instructions)
                self.display_opcodes(opcodes)
                # switch to opcode output tab (index may differ — you used select(3) earlier)
                try:
                    self.notebook.select(3)
                except Exception:
                    pass

            self.status_var.set("Step finished: program complete. Opcodes generated.")
            self.is_running = False

            # Disable run/step to prevent extra blanking step
            try:
                self.runButton["state"] = "disabled"
                self.stepButton["state"] = "disabled"
            except Exception:
                pass

            messagebox.showinfo("Run Complete", "Program executed successfully by stepping. Check Opcode Output tab.")
            return

        # otherwise allow further stepping (do nothing special)
        return


    def memory_access(self):
        ex = self.pipeline_state['EX_MEM']
        instruction = ex.get('IR', 0)

        if not instruction:
            self.pipeline_state['MEM_WB'] = {'LMD': 0, 'IR': 0, 'ALUOUTPUT': 0}
            return

        inst_bin = format(instruction & 0xFFFFFFFF, '032b')
        opcode = inst_bin[25:32]
        funct3 = inst_bin[17:20]
        addr = ex.get('ALUOUTPUT', 0)

        # LW
        if opcode == "0000011" and funct3 == "010":
            if DATA_START <= addr <= DATA_END - 3 and addr % 4 == 0:
                lmd = self.read_word(addr)
            else:
                lmd = 0
            self.pipeline_state['MEM_WB'] = {
                'LMD': lmd,
                'IR': instruction,
                'ALUOUTPUT': addr
            }
            return

        # SW
        if opcode == "0100011" and funct3 == "010":
            data = ex.get('B', 0)
            if DATA_START <= addr <= DATA_END - 3 and addr % 4 == 0:
                self.write_word(addr, data)
            self.pipeline_state['MEM_WB'] = {
                'LMD': 0,
                'IR': instruction,
                'ALUOUTPUT': addr
            }
            return

        # Otherwise ALU op
        self.pipeline_state['MEM_WB'] = {
            'LMD': 0,
            'IR': instruction,
            'ALUOUTPUT': ex.get('ALUOUTPUT', 0)
        }

    def write_back(self):
        """
        WB stage: commit MEM_WB to registers if needed.
        """
        mem = self.pipeline_state['MEM_WB']
        instruction = mem.get('IR', 0)
        if not instruction:
            return

        inst = instruction & 0xFFFFFFFF
        inst_bin = format(inst, '032b')
        opcode = inst_bin[25:32]
        funct3 = inst_bin[17:20]
        rd = int(inst_bin[20:25], 2)

        if rd != 0:
            if opcode == "0110011":  # R-type
                REGISTER_FILE[rd] = mem.get('ALUOUTPUT', 0) & 0xFFFFFFFF
            elif opcode == "0010011":  # I-type (e.g., ORI)
                REGISTER_FILE[rd] = mem.get('ALUOUTPUT', 0) & 0xFFFFFFFF
            elif opcode == "0000011" and funct3 == "010":  # LW
                REGISTER_FILE[rd] = mem.get('LMD', 0) & 0xFFFFFFFF

        REGISTER_FILE[0] = 0  # keep x0 = 0

    def pipeline_advance(self, ex_mem_new=None, branch_taken=False):
        """
        Advance pipeline one cycle:
        MEM_WB <= old EX_MEM
        EX_MEM <= ex_mem_new (from EX stage)
        ID_EX  <= IF_ID
        IF_ID  <= fetched instruction OR frozen on branch
        """
        # --- 1. Capture old EX_MEM for MEM_WB update ---
        old_ex = self.pipeline_state['EX_MEM'].copy()

        # --- 2. MEM_WB should preserve whatever MEM stage wrote this cycle ---
        memwb_lmd = self.pipeline_state['MEM_WB'].get('LMD', 0)

        self.pipeline_state['MEM_WB'] = {
            'LMD': memwb_lmd,                        # from memory_access()
            'IR': old_ex.get('IR', 0),               # pass down old EX instruction
            'ALUOUTPUT': old_ex.get('ALUOUTPUT', 0)  # pass down ALU result
        }

        # --- 3. Insert new EX_MEM from EX stage ---
        if ex_mem_new is None:
            # default NOP
            self.pipeline_state['EX_MEM'] = {
                'ALUOUTPUT': 0,
                'cond': 0,
                'IR': 0,
                'B': 0
            }
        else:
            # ✔ FIX B: correctly forward all EX outputs
            self.pipeline_state['EX_MEM'] = ex_mem_new.copy()

        # --- 4. If branch taken: freeze IF_ID and insert bubble into ID_EX ---
        if branch_taken:
            # ID_EX becomes bubble
            self.pipeline_state['ID_EX'] = {'A': 0, 'B': 0, 'IMM': 0, 'IR': 0, 'NPC': 0}

            # IF_ID is FROZEN — DO NOT FETCH A NEW INSTRUCTION
            return

        # --- 5. Normal pipeline flow: ID_EX <= old IF_ID ---
        self.pipeline_state['ID_EX'] = self.pipeline_state['IF_ID'].copy()

        # --- 6. Fetch next instruction into IF_ID ---
        pc = self.pipeline_state['PC']
        if pc in self.program_memory:
            self.pipeline_state['IF_ID'] = {
                'IR': self.program_memory[pc],
                'NPC': (pc + 4) & 0xFFFFFFFF
            }
            # PC increments only after successful fetch
            self.pipeline_state['PC'] = (pc + 4) & 0xFFFFFFFF
        else:
            # No instruction to fetch → insert bubble
            self.pipeline_state['IF_ID'] = {'IR': 0, 'NPC': 0}

    def execute_current_instruction(self):
        """
        EX stage: read ID/EX, perform ALU/branch computations and return EX/MEM dict.
        (Does not modify pipeline registers except possibly PC when branch taken.)
        """
        idex = self.pipeline_state['ID_EX']
        instruction = idex.get('IR', 0)
        # Default NOP EX/MEM
        ex_mem_new = {'ALUOUTPUT': 0, 'cond': 0, 'IR': 0, 'B': 0}

        if not instruction:
            return ex_mem_new

        inst = instruction & 0xFFFFFFFF
        inst_bin = format(inst, '032b')
        opcode = inst_bin[25:32]
        funct3 = inst_bin[17:20]

        # Extract registers
        rd = int(inst_bin[20:25], 2)
        rs1 = int(inst_bin[12:17], 2)
        rs2 = int(inst_bin[7:12], 2)

        rs1_val = REGISTER_FILE.get(rs1, 0)
        rs2_val = REGISTER_FILE.get(rs2, 0)

        ex_mem_new['IR'] = instruction
        ex_mem_new['B'] = rs2_val & 0xFFFFFFFF

        # I-type immediate bits [31:20]
        imm_i = int(inst_bin[0:12], 2)
        if inst_bin[0] == '1':
            imm_i = imm_i - (1 << 12)

        npc = idex.get('NPC', 0)

        # R-type
        if opcode == "0110011":
            if funct3 == "111":  # AND
                res = (rs1_val & rs2_val) & 0xFFFFFFFF
                ex_mem_new['ALUOUTPUT'] = res
            elif funct3 == "110":  # OR
                res = (rs1_val | rs2_val) & 0xFFFFFFFF
                ex_mem_new['ALUOUTPUT'] = res

        # ORI
        elif opcode == "0010011" and funct3 == "110":
            res = (rs1_val | (imm_i & 0xFFF)) & 0xFFFFFFFF
            ex_mem_new['ALUOUTPUT'] = res

        # LW
        elif opcode == "0000011" and funct3 == "010":
            addr = (rs1_val + imm_i) & 0xFFFFFFFF
            ex_mem_new['ALUOUTPUT'] = addr

        # SW
        elif opcode == "0100011" and funct3 == "010":
            addr = (rs1_val + imm_i) & 0xFFFFFFFF
            ex_mem_new['ALUOUTPUT'] = addr
            ex_mem_new['B'] = rs2_val & 0xFFFFFFFF

        # Branches BLT/BGE
        elif opcode == "1100011":
            # reconstruct B-type immediate
            imm_b_bits = inst_bin[0] + inst_bin[24] + inst_bin[1:7] + inst_bin[20:24]
            imm_b = int(imm_b_bits, 2)
            if imm_b_bits[0] == '1':
                imm_b = imm_b - (1 << 13)
            branch_taken = False
            if funct3 == "100":  # BLT
                branch_taken = (rs1_val < rs2_val)
            elif funct3 == "101":  # BGE
                branch_taken = (rs1_val >= rs2_val)
            ex_mem_new['cond'] = 1 if branch_taken else 0
            if branch_taken:
                branch_target = (npc + imm_b - 4) & 0xFFFFFFFF
                # set PC to branch target: Note pipeline_advance will freeze IF_ID and insert bubble
                self.pipeline_state['PC'] = branch_target

        # ensure 32-bit values
        ex_mem_new['ALUOUTPUT'] = ex_mem_new.get('ALUOUTPUT', 0) & 0xFFFFFFFF
        ex_mem_new['B'] = ex_mem_new.get('B', 0) & 0xFFFFFFFF
        ex_mem_new['cond'] = ex_mem_new.get('cond', 0)

        return ex_mem_new

    # -------------------------
    # Non-pipeline (assembler) helpers
    # -------------------------
    def load_program_to_memory(self):
        """
        Properly loads validated instructions into program_memory.
        Performs:
            1. Extract non-empty lines
            2. First pass: collect labels & their addresses
            3. Second pass: encode instructions
            4. Write encoded 32-bit words into program_memory
        """
        PROG_START = 0x80
        address = PROG_START

        # Clear program memory
        self.program_memory.clear()

        # ---- COLLECT NON-EMPTY INSTRUCTIONS ----
        lines = []
        for i, entry in enumerate(self.entry_widgets):
            text = entry.get().strip()
            if text:
                lines.append((i + 1, text))  # (line#, text)

        if not lines:
            return False

        # ---- FIRST PASS: LABEL COLLECTION ----
        labels = {}
        pc = PROG_START

        for line_num, text in lines:
            clean = text.split("#")[0].strip()

            if ":" in clean:
                label = clean.split(":")[0].strip()
                labels[label] = pc

                # If instruction exists after label, it occupies one word
                inst_after = clean.split(":")[1].strip()
                if inst_after:
                    pc += 4
            else:
                pc += 4

        # ---- SECOND PASS: ENCODING ----
        pc = PROG_START
        for line_num, text in lines:
            clean = text.split("#")[0].strip()

            # Separate label from instruction (robust parsing)
            if ":" in clean:
                before, after = clean.split(":", 1)
                label = before.strip()
                inst = after.strip()

                # Skip label-only lines (e.g., "LOOP:" or "LOOP:   ")
                if inst == "" or inst.isspace():
                    continue

                # Continue with the actual instruction text
                clean = inst


            # Normalize SW format (your parser requires special handling)
            if clean.upper().startswith("SW"):
                parts = clean.split()
                mnemonic = parts[0].upper()
                rs2 = parts[1].rstrip(',')
                offset_rs1 = " ".join(parts[2:])
                operands = [rs2, offset_rs1]
            else:
                parts = re.split(r'[,\s()]+', clean)
                parts = [p for p in parts if p]
                mnemonic = parts[0].upper()
                operands = parts[1:]

            # ---- ENCODE USING EXISTING ENCODERS ----
            try:
                if mnemonic in R_TYPE:
                    hex_opcode = self.encode_r_type(mnemonic, operands)

                elif mnemonic in I_TYPE:
                    hex_opcode = self.encode_i_type(mnemonic, operands)

                elif mnemonic in S_TYPE:
                    hex_opcode = self.encode_s_type(mnemonic, operands)

                elif mnemonic in B_TYPE:
                    # Label resolution
                    if len(operands) >= 3 and operands[2] in labels:
                        offset = labels[operands[2]] - pc
                        operands = operands[0:2] + [str(offset)]
                    hex_opcode = self.encode_b_type(mnemonic, operands)

                elif mnemonic == ".WORD":
                    hex_opcode = self.encode_directive(mnemonic, operands[0])

                else:
                    raise ValueError(f"Unsupported instruction {mnemonic}")

            except Exception as e:
                messagebox.showerror("Encoding Error", f"Line {line_num}: {e}")
                return False

            # Store encoded instruction as 32-bit integer
            self.program_memory[pc] = int(hex_opcode, 16)

            pc += 4

        return True

    def create_pipeline_tab(self):
        self.pipeline_frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(self.pipeline_frame, text="Pipeline State")
        self.pipeline_text = scrolledtext.ScrolledText(self.pipeline_frame, bg="white", width=100, height=25, font=("Courier New", 10))
        self.pipeline_text.pack(fill='both', expand=True, padx=10, pady=10)
        self.pipeline_text.config(state=tk.DISABLED)

    def update_register_display(self):
        for i in range(1, 32):
            self.reg_entries[i].config(state='normal')
            self.reg_entries[i].delete(0, tk.END)
            self.reg_entries[i].insert(0, f"0x{REGISTER_FILE[i]:08x}")
            self.reg_entries[i].config(state='readonly')
        # ---- UPDATE PC display ----
        self.pc_entry.config(state='normal')
        self.pc_entry.delete(0, tk.END)
        self.pc_entry.insert(0, f"0x{self.pipeline_state['PC']:08x}")
        self.pc_entry.config(state='readonly')


    def update_pipeline_display(self):
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
            ("MEM/WB", self.pipeline_state['MEM_WB'])
        ]
        for stage_name, stage_data in stages:
            self.pipeline_text.insert(tk.END, f"\n{stage_name}:\n")
            for reg, value in stage_data.items():
                if isinstance(value, int):
                    display_value = f"0x{value:08x}"
                else:
                    display_value = str(value)
                self.pipeline_text.insert(tk.END, f"  {reg}: {display_value}\n")
        self.pipeline_text.config(state=tk.DISABLED)

    def create_opcode_tab(self):
        self.opcode_frame = tk.Frame(self.notebook, bg="#D3D3D3", bd=3)
        self.notebook.add(self.opcode_frame, text="Opcode Output")
        self.opcode_text = scrolledtext.ScrolledText(self.opcode_frame, bg="white", width=100, height=25, font=("Courier New", 10))
        self.opcode_text.pack(fill='both', expand=True, padx=10, pady=10)
        self.opcode_text.config(state=tk.DISABLED)

    def create_buttons(self):
        frame = tk.Frame(self.root, bg="#D3D3D3", bd=1, relief="sunken")
        frame.pack(fill='x', side='top', padx=10, pady=(10,0))
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
        """
        Run cycles until the pipeline and fetch are empty, but STOP early so MEM/WB
        still shows the last committed instruction (Option A behavior).
        """
        if not self.program_memory:
            self.load_program_to_memory()
        if not self.program_memory:
            messagebox.showwarning("No Program", "No valid program to execute")
            return

        # reset pipeline and PC to known starting state
        self.pipeline_state = {
            'PC': PROG_START,
            'IF_ID': {'IR': 0, 'NPC': 0},
            'ID_EX': {'A': 0, 'B': 0, 'IMM': 0, 'IR': 0, 'NPC': 0},
            'EX_MEM': {'ALUOUTPUT': 0, 'cond': 0, 'IR': 0, 'B': 0},
            'MEM_WB': {'LMD': 0, 'IR': 0, 'ALUOUTPUT': 0}
        }
        self.cycle_count = 0

        # Prime pipeline by fetching first instruction if present
        pc = self.pipeline_state['PC']
        if pc in self.program_memory:
            self.pipeline_state['IF_ID']['IR'] = self.program_memory[pc]
            self.pipeline_state['IF_ID']['NPC'] = (pc + 4) & 0xFFFFFFFF
            self.pipeline_state['PC'] = (pc + 4) & 0xFFFFFFFF

        while True:
            self.step_execution()
            self.root.update()

            # Same termination condition that step_execution() expects:
            pipeline_empty = (
                self.pipeline_state['IF_ID']['IR'] == 0 and
                self.pipeline_state['ID_EX']['IR'] == 0 and
                self.pipeline_state['EX_MEM']['IR'] == 0 and
                self.pipeline_state['MEM_WB']['IR'] == 0
            )
            pc_done = self.pipeline_state['PC'] not in self.program_memory

            if pipeline_empty and pc_done:
                break

        # generate opcodes 
        instructions = []
        for i, entry in enumerate(self.entry_widgets):
            line_text = entry.get().strip()
            if line_text:
                instructions.append((i + 1, line_text))
        if instructions:
            opcodes = self.generate_opcodes(instructions)
            self.display_opcodes(opcodes)
            self.notebook.select(3)

        self.status_var.set("Program executed - Opcodes generated")
        messagebox.showinfo("Run Complete", "Program executed successfully! Check Opcode Output tab.")
        self.is_running = False

    # -------------------------
    # Assembler/encoding & validation 
    # -------------------------
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
            return format(imm_val, f'0{bits}b')
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

    def encode_r_type(self, instruction, operands):
        opcode = list(R_TYPE[instruction].keys())[0]
        funct3 = R_TYPE[instruction][opcode]
        rd = self.reg_to_bin(operands[0])
        rs1 = self.reg_to_bin(operands[1])
        rs2 = self.reg_to_bin(operands[2])
        funct7 = "0000000"
        binary = funct7 + rs2 + rs1 + funct3 + rd + opcode
        return self.binary_to_hex(binary)

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
            return format(value, '08x')
        except ValueError:
            raise ValueError(f"Invalid value for .WORD directive: {operand}")

    def generate_opcodes(self, instructions):
        opcodes = []
        program_counter = 0x0080
        labels = {}
        current_pc = program_counter
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
        current_pc = program_counter
        for line_num, instruction in instructions:
            clean_instruction = instruction.split('#')[0].strip()
            if not clean_instruction:
                continue
            if ':' in clean_instruction:
                label_part = clean_instruction.split(':')[0].strip()
                instruction_part = clean_instruction.split(':')[1].strip() if len(clean_instruction.split(':')) > 1 else ""
                opcodes.append(f"0x{current_pc:04x}: [LABEL] {label_part}:")
                if instruction_part:
                    if instruction_part.upper().startswith('SW'):
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
                                if len(operands) >= 3 and operands[2] in labels:
                                    offset = labels[operands[2]] - current_pc
                                    modified_parts = operands[0:2] + [str(offset)]
                                    hex_opcode = self.encode_b_type(mnemonic, modified_parts)
                                else:
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
                if clean_instruction.upper().startswith('SW'):
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
                        if len(operands) >= 3 and operands[2] in labels:
                            offset = labels[operands[2]] - current_pc
                            modified_parts = operands[0:2] + [str(offset)]
                            hex_opcode = self.encode_b_type(mnemonic, modified_parts)
                        else:
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

    # Remaining UI logic for program lines (unchanged)
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
        self.new_entry = tk.Entry(self.inner_frame, bg="white", width=80)
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
            parts = instruction.split()
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

def main():
    root = tk.Tk()
    app = RiscVGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
