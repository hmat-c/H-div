# hmat-assign.pl Usage Guide

## Overview
`hmat-assign.pl` is a Perl script that visualizes how leaf matrices in an H-matrix (hierarchical matrix) are assigned to MPI processes and worker threads. It reads input files and generates a PDF file using gnuplot.

## Generating H-matrix Information (hmat_array_filling.c)

### Compilation and Execution
```bash
# Compile (requires MKL library)
gcc -o hmat_array_filling hmat_array_filling.c data/bem_file.c -lmkl_intel_lp64 -lmkl_sequential -lmkl_core -lpthread -lm

# Execute (use -t option to generate visualization data)
./hmat_array_filling -t [input_file]
```

### Usage Examples
```bash
# Use default input file
./hmat_array_filling -t

# Specify a particular input file
./hmat_array_filling -t data/input_100ts.txt
```

### Generated Files
The program generates a file with `_hmat` appended to the input filename:
- Example: `input_10ts.txt` → `input_10ts.txt_hmat`
- Directory paths are automatically removed from the output filename

## Basic Usage of hmat-assign.pl

### Single File Processing
```bash
perl hmat-assign.pl <inputfile>
```

### Multiple Process Files Processing
```bash
perl hmat-assign.pl --mproc <prefix>
```

## Options

- `--keep, -k`: Keep plot files and gnuplot script after execution
- `--help, -h`: Show help message
- `--mproc=<prefix>, -m <prefix>`: Process multiple process files with the specified prefix
  - Reads all files named `<prefix>0000`, `<prefix>0001`, etc.
  - The postfix number in each filename is treated as the process number

## Input File Format

Each line describes leaf matrix information in the following format:
```
<thr>, <x0>, <y0>, <x1>, <y1>, <mattype>
```

- `<thr>`: Thread number (integer ≥ 0)
- `<x0>, <y0>`: Index of the upper-left element
- `<x1>, <y1>`: Index of the lower-right element
- `<mattype>`: Matrix type (1: Rk-matrix, 2: Full-matrix)

## Complete Usage Examples

### 1. Visualizing H-matrix Structure
```bash
# Generate H-matrix information file
./hmat_array_filling -t data/input_10ts.txt

# Verify generated file
ls input_10ts.txt_hmat

# Generate visualization PDF
perl hmat-assign.pl input_10ts.txt_hmat

# Verify generated PDF
ls input_10ts.txt_hmat.pdf
```

### 2. Keeping Intermediate Files
```bash
perl hmat-assign.pl -k input_10ts.txt_hmat
# Intermediate files are saved in input_10ts.txt_hmat-dir/ directory
```

### 3. Multi-process Visualization
```bash
# When process-specific files exist (e.g., hmat_0000, hmat_0001, ...)
perl hmat-assign.pl -m hmat_
```

## Output

- **PDF File**: File with `.pdf` appended to the input filename (e.g., `input_10ts.txt_hmat.pdf`)
  - Rk-matrices: Light fill (opacity 0.1)
  - Full-matrices: Dark fill (opacity 0.5)
  - Different colors for each thread
  - Process boundaries displayed (for multiple processes)

- **Temporary Files** (kept only with `-k` option):
  - Plot files: `<inputfile>-dir/thread-<n>-<mattype>.plt`
  - Gnuplot script: `<inputfile>-dir/plot.gnuplot`
  - Process boundaries file: `<inputfile>-dir/boundaries.plt`

## Requirements

- Perl
- gnuplot (with PDFCairo terminal support)
- MKL library (for compiling hmat_array_filling)

## Notes

- Output PDF is generated in the same directory as the input file
- Confirmation is requested when overwriting existing directories
- An error occurs if gnuplot is not installed
- Without the `-t` option in hmat_array_filling execution, no visualization file will be generated