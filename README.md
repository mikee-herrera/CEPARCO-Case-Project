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


## Execution
insert screenshots here

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


