# CEPARCO-Case-Project Group 5
This is a simulator for a simplified RISC-V processor, μRISCV. The μRISCV processor offers the following subset of RISC-V instructions:<br><br>
Group 5: LW, SW, AND, OR, ORI, BLT, BGE<br>
Minimum directive: .word
---
## Source Code

```
CEPARCO-Case-Project/main/
├── CEPARCO-Case-Project.py          # Final implementation (MAIN ENTRY POINT)
└── README.md                        # Project documentation
```
## GUI Components
<img width="1393" height="710" alt="image" src="https://github.com/user-attachments/assets/f53130b5-a7f9-4cf4-9ee5-9eaeed4644dc" />
1. Multi-tab Interface
   - Program Input: Assembly code editor with line numbers
   - Register Tab: Live register values (hex + decimal)
   - Memory Input: Editable memory contents
   - Pipeline State: Textual pipeline stage details
   - Pipeline Map Table: Color-coded pipeline visualization
   - Opcode Output: Generated machine code

## Design Methodology
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend GUI  │───▶│  Pipeline Engine │───▶│  Memory System │
│                 │    │                  │    │                 │
│ • Tkinter UI    │    │ • 5-stage pipe   │    │ • Data Memory   │
│ • Multi-tab     │    │ • Hazard handling│    │ • Program Memory│
│ • Visualization │    │ • State tracking │    │ • Word-aligned  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                         ┌───────────────┐
                         │ Register File │
                         │ • 32 registers│
                         │ • x0 = 0      │
                         └───────────────┘
```
**1. Frontend GUI (Tkinter-based Interface)**
   - Multi-tab interface for different simulation aspects
   - Program Input Tab: Assembly code editor with line numbers and syntax validation
   - Register Tab: Live display of all 32 registers in hexadecimal and decimal formats
   - Memory Tab: Editable memory contents with word-aligned addressing
   - Pipeline State Tab: Textual representation of pipeline register contents
   - Pipeline Map Table: Color-coded visualization of instruction flow through pipeline stages
   - Opcode Output Tab: Generated machine code display

**2. Pipeline Engine (Core Simulation Logic)**
   - 5-stage RISC-V pipeline: IF, ID, EX, MEM, WB
   - Pipeline Freeze Mechanism: Control hazard handling for branch instructions
   - State Tracking: Comprehensive pipeline register monitoring
   - Cycle Management: Step-by-step and continuous execution modes
   - Hazard Detection: Identification and resolution of pipeline conflicts

**3. Memory System (Dual Memory Architecture)**
   - Data Memory: 128 bytes (0x0000-0x007F) for program data storage
   - Program Memory: 128 bytes (0x0080-0x00FF) for instruction storage
   - Word-aligned Access: 4-byte boundary enforcement for all memory operations

Little-endian Format: Standard RISC-V byte ordering implementation
## Execution

#### EX 1 Branch Functions
<img width="1575" height="543" alt="image" src="https://github.com/user-attachments/assets/ba580bd2-4aa4-47ce-bf54-17878c7f8ae5" />
<img width="1242" height="796" alt="image" src="https://github.com/user-attachments/assets/6c696058-80c9-4534-b2c5-1f3f74893502" />

#### EX 2 ORI Function
<img width="201" height="67" alt="image" src="https://github.com/user-attachments/assets/9ff2c513-c668-4955-a580-a49fd25fc27f" />
<img width="684" height="418" alt="image" src="https://github.com/user-attachments/assets/4f49c1d7-c82f-496d-9f20-f99f0dd8edef" />
<img width="1218" height="819" alt="image" src="https://github.com/user-attachments/assets/f247724a-ca81-4e81-8217-b68fccbac132" />


## Discussion

We based our design on RARS, also known as the RISC-V Assembler, Simulator, and Runtime. We made use of a ```RiscVUI``` class which managed both the application state and the GUI components. Our interface is meant to simulate an IDE, with one input tab and separate output tabs which displayed the registers, memory, opcode outputs, pipeline states, and pipeline map. This program was tested using some of the instructions given in Problem Set 6. The outputs of the program were then compared to the outputs we obtained through manual computation in order to check if the program was working properly.

## Final Presentation Video
insert link here

## Project Updates
### Milestone #1
- [x] Program Input
- [x] Error Checking
- [x] Opcode
- [x] Basic GUI  
#### Video Demo:
#### https://drive.google.com/file/d/11MM2coCsVog75gngo4BsEMJZ_NPTL_fR/view?usp=sharing
---
### Milestone 2
- [x] GUI (registers, memory)
- [x] Initial execution draft (step and full execution added)
#### Video Demo:
#### https://drive.google.com/file/d/14tkBBiv5gQm1CpLOTHKn6AXlTAyt5T0J/view?usp=sharing
---
### Milestone 3
- [x] Updating registers and memory
- [x] Pipeline Map
- [x] Completed project


