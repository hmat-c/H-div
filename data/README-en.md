# BEM Data Processing Tools

This directory contains C programs for processing and manipulating BEM (Boundary Element Method) data, along with accompanying visualization tools.

## Overview

We provide C programs for generating, converting, and processing BEM data files, along with Python tools to support data visualization. These tools streamline the handling of mesh data used in 3D boundary element method analysis.

## Main Programs (C Language)

### Program Structure

#### 1. bem_convert
A program for converting BEM data file formats.
- Mutual conversion between text, binary, VTK, and formatted display formats
- Efficient processing of large-scale data
- Compatibility with various analysis software

#### 2. bem_generate
A program that generates new BEM data files by duplicating and arranging existing BEM objects.
- **Pyramid arrangement (p command)**: Arranges 1+4+9+...+n² objects in a pyramid shape
- **Cuboid arrangement (c command)**: Arranges nx×ny×nz objects in a cuboid shape
- Distance parameter specifies center-to-center distance between adjacent objects as a ratio to object diameter
  - 1.0: Objects are in contact
  - 1.5: Gap of 0.5 times the diameter between objects
  - 2.0: Gap of 1.0 times the diameter between objects
- If output filename is omitted, it's automatically generated from command parameters

### Build Instructions

```bash
cd data/
make
```

This will generate the `bem_convert` and `bem_generate` executables.

### Usage Examples

Format conversion:
```bash
./bem_convert -i input.txt -o output.vtk -f vtk
```

Mesh generation (pyramid arrangement):
```bash
./bem_generate p 1.5 3 base_input.txt output.txt
```

Mesh generation (cuboid arrangement):
```bash
./bem_generate c 1.2 4 4 4 base_input.txt output.txt
```

### Source File Structure
- **bem_file.h/c**: Implementation of BEM file I/O functionality
  - Parsers for various formats
  - Data structure definitions
- **bem_aux.c**: Auxiliary functions
  - Time measurement functionality
  - File I/O support
- **bem_convert.c**: Main program for format conversion
- **bem_generate.c**: Main program for data generation
- **filling.h/c**: Processing related to matrix element filling

## Using as a Library

`bem_file.h/c` can be used as a library for reading BEM data files from other programs.

### Basic Usage

```c
#include <stdio.h>
#include <stdlib.h>
#include "data/bem_file.h"

int main(int argc, char **argv) {
    const char *filename = "input_data.txt";
    FILE *file;
    struct bem_input bi;
    
    // Open file
    file = fopen(filename, "r");
    if (file == NULL) {
        fprintf(stderr, "Error: Unable to open file '%s'\n", filename);
        exit(1);
    }
    
    // Read BEM data
    if (read_bem_input(file, &bi, BI_AUTO) == -1) {
        fprintf(stderr, "BEM input file read error!\n");
        fclose(file);
        exit(1);
    }
    fclose(file);
    
    // Access the loaded data
    printf("Number of nodes: %ld\n", bi.nNode);
    printf("Number of faces: %ld\n", bi.nFace);
    
    // Access vertex coordinates
    for (int i = 0; i < bi.nNode; i++) {
        printf("Node %d: (%f, %f, %f)\n", i,
               bi.coordOfNode[i][0],
               bi.coordOfNode[i][1],
               bi.coordOfNode[i][2]);
    }
    
    // Access face center coordinates
    for (int i = 0; i < bi.nFace; i++) {
        printf("Face %d center: (%f, %f, %f)\n", i,
               bi.coordOfFace[i][0],
               bi.coordOfFace[i][1],
               bi.coordOfFace[i][2]);
    }
    
    // Access vertex indices that compose each face
    for (int i = 0; i < bi.nFace; i++) {
        printf("Face %d vertices: %d, %d, %d\n", i,
               bi.face2node[i][0],
               bi.face2node[i][1],
               bi.face2node[i][2]);
    }
    
    return 0;
}
```

### Compilation

```bash
gcc -o myprogram myprogram.c data/bem_file.c data/bem_aux.c -lm
```

### Available Functions

#### read_bem_input
```c
enum bi_format read_bem_input(FILE* fp, struct bem_input* pbin, enum bi_format fmt);
```
- Reads BEM data from a file pointer
- Specify `BI_AUTO` for `fmt` to automatically detect the format
- Returns the read format on success, -1 on failure

#### open_and_read_bem_input
```c
enum bi_format open_and_read_bem_input(char *ifile, struct bem_input* pbin, enum bi_format fmt);
```
- Reads BEM data by specifying a filename (handles file opening and closing)

#### print_bem_input
```c
void print_bem_input(FILE* fp, struct bem_input* pbin, enum bi_format fmt);
```
- Outputs BEM data in the specified format

### bem_input Structure Fields

- `nNode`: Number of vertices
- `coordOfNode`: Array of vertex coordinates `[nNode][3]`
- `nFace`: Number of faces
- `coordOfFace`: Array of face center coordinates `[nFace][3]`
- `face2node`: Array of vertex indices composing each face `[nFace][3]`
- See `bem_file.h` for other fields

### Implementation Example: hmat_array_filling.c

As a practical example, `hmat_array_filling.c` uses the library as follows:

```c
#include "data/bem_file.h"

struct bem_input bi;
file = fopen(fname, "r");
if (read_bem_input(file, &bi, BI_AUTO) == -1) {
    fprintf(stderr, "Bem input file read error!\n");
    exit(99);
}
fclose(file);

// Store data in variables
countOfNode = bi.nNode;
bgmid = bi.coordOfNode;
count = bi.nFace;
zgmid = bi.coordOfFace;
f2n = bi.face2node;
```

## Data Format

### BEM Data File Format

BEM data files support two formats: **text format** and **binary format**.

#### Text Format

Data files are text files with the following structure:

```
<number of vertices>
<vertex 0 X coordinate> <vertex 0 Y coordinate> <vertex 0 Z coordinate>
<vertex 1 X coordinate> <vertex 1 Y coordinate> <vertex 1 Z coordinate>
...
<number of faces>
3
0
0
<face 0 vertex index 0> <face 0 vertex index 1> <face 0 vertex index 2>
<face 1 vertex index 0> <face 1 vertex index 1> <face 1 vertex index 2>
...
```

#### Binary Format

Binary format provides fast I/O and smaller file sizes.

**Binary Format Structure:**

```
"BI_BINARY\n"                    # Preamble (ASCII string)
int64_t: nNode                   # Number of vertices
double[nNode][3]: coordOfNode    # Vertex coordinates (x,y,z)
int64_t: nFace                   # Number of faces
int64_t: nNodePerFace            # Vertices per face (always 3)
int64_t: nIFValue                # Integer parameters per face
int64_t: nDFValue                # Double parameters per face
int64_t[nFace][3]: idOfFace      # Vertex indices composing faces
double[nFace][3]: coordOfFace    # Face center coordinates
int[nFace][3]: face2node         # Vertex indices composing faces (int32)
int64_t[nFace][nIFValue]: IFValue    # Integer parameters (if exist)
double[nFace][nDFValue]: DFValue      # Double parameters (if exist)
```

**Data Types:**
- `int64_t`: 8-byte integer (little-endian)
- `int`: 4-byte integer (little-endian)  
- `double`: 8-byte floating point (IEEE 754, little-endian)

#### Format Conversion

Use `bem_convert` to convert between text and binary formats:

```bash
# Convert text to binary
./bem_convert -o output_filename -b input.txt

# Convert binary to text
./bem_convert -o output_filename -t input.bin

# Auto-detect (determine output format by extension)
./bem_convert input.txt    # → generates input.bin
./bem_convert input.bin    # → generates input.txt
```

## Attached Tools (Python)

### 3D Polygon Data Visualization Tool

Python tools to support visual confirmation of BEM data.

#### visualize_polygon.py
An advanced 3D visualization program with comprehensive features.
- **Basic 3D display**: View manipulation with mouse
- **Transparency adjustment**: Adjust polygon transparency with slider
- **Edge width adjustment**: Adjust edge thickness with slider
- **Vertex display**: Toggle vertex display on/off with button
- **Lightweight mode**: Switch to lightweight mode displaying only triangle centroids as points (fast display for large data)
- **Adaptive point size**: Automatically adjusts size according to point density in lightweight mode (prevents overlap)
- **Image file output**: Save as image file without displaying GUI (batch processing support)
- **Vector format support**: High-quality vector image output in PDF/SVG formats
- **Automatic file size control**: Automatic PNG conversion when vector files become too large
- **Viewpoint settings**: Display from arbitrary viewpoint by specifying elevation and azimuth angles
- **High-resolution output**: Generate high-quality images by specifying DPI
- **Shading**: Shadow representation with simple light source calculation
- **Statistics display**: Display information such as surface area and centroid
- **Reset function**: Return settings to initial state
- **Automatic axis range adjustment**: Automatically adjusts axis range to fit data
- **Binary format support**: Supports binary format (.bin) for fast loading

### Python Environment Setup

```bash
pip install numpy matplotlib
```

### Visualization Tool Usage

Basic usage:
```bash
python3 visualize_polygon.py input_10ts.txt
```

Command line options:
```bash
python3 visualize_polygon.py [options] [filename]

Options:
  -h, --help            Show help message
  --alpha ALPHA, -a ALPHA
                        Polygon transparency (0.1-1.0, default: 0.8)
  --edge-width WIDTH, -e WIDTH
                        Edge width (0.0-1.0, default: 0.1)
  --show-vertices, -v   Show vertices at startup
  --lightweight, -l     Start in lightweight mode (display only triangle centroids)
  --output FILE, -o FILE
                        Save as image file (no GUI display)
                        Format determined by extension (.pdf, .svg, .png, etc.)
                        PDF format if no extension
  --dpi DPI, -d DPI     DPI for output image (default: 150)
  --elev ANGLE          Viewpoint elevation angle (default: 20)
  --azim ANGLE          Viewpoint azimuth angle (default: 30)
  --point-size SIZE, -p SIZE
                        Point size in lightweight mode (automatically adjusted by density if not specified)
  --max-vector-size SIZE
                        Maximum vector format file size (MB, default: 5)
                        Automatically switches to PNG if exceeded
```

Usage examples:
```bash
# Set transparency to 0.5, edge width to 0.2
python3 visualize_polygon.py --alpha 0.5 --edge-width 0.2 input.txt

# Start in lightweight mode with vertices displayed
python3 visualize_polygon.py -l -v input.txt

# Use all options
python3 visualize_polygon.py -a 0.6 -e 0.05 -v -l large_data.txt

# Save as image file (no GUI)
python3 visualize_polygon.py -o output.png input.txt

# Generate high-resolution image from specific viewpoint
python3 visualize_polygon.py -o visualization.png --dpi 300 --elev 30 --azim 60 input.txt

# Generate image in lightweight mode (for large data)
python3 visualize_polygon.py -l -o lightweight_view.png --dpi 200 large_data.txt

# Manually specify point size in lightweight mode
python3 visualize_polygon.py -l -p 1.5 -o small_points.png dense_data.txt

# Save in vector format (PDF)
python3 visualize_polygon.py -o output.pdf input.txt

# Save in vector format (SVG)
python3 visualize_polygon.py -o output.svg input.txt

# No extension (defaults to PDF)
python3 visualize_polygon.py -o output input.txt

# Change vector file size limit to 10MB
python3 visualize_polygon.py -o large_output.pdf --max-vector-size 10 input.txt

# Visualize binary file (auto-detected)
python3 visualize_polygon.py input_196kp26.bin

# Fast visualization of binary file in lightweight mode
python3 visualize_polygon.py -l -o binary_vis.png input_2ms.bin
```

### Controls

#### Mouse Controls
- **Left drag**: Rotate viewpoint
- **Right drag**: Zoom
- **Middle drag**: Pan (move)

#### Keyboard Controls (Matplotlib standard)
- **s**: Save current display as image
- **q**: Quit application

## Requirements

### C Programs
- GCC compiler (C99 compatible)
- Make

### Python Visualization Tools
- Python 3.6 or higher
- NumPy
- Matplotlib

## Sample Datasets

The `bem_bb_inputs` directory contains BEM data files of various scales:

### Dataset Overview
- **Total files**: 49 BEM data files
- **Scale range**: 26 to 50,000,000 faces (6 orders of magnitude)
- **Uses**: Algorithm benchmarking, scalability testing

### Classification by Scale
| Category | Face Count Range | Examples | Usage |
|----------|------------------|----------|-------|
| Small | 26-29 faces | input2.txt, input3.txt | Basic functionality testing |
| Medium | 600-338,000 faces | input_10ts.txt, input_338ts.txt | General analysis |
| Large | 648,000-1,965,600 faces | input_1ms.txt, input_196kp26.txt | High-precision analysis |
| Ultra-large | 2,000,000-50,000,000 faces | input_2ms.txt, input_50ms.txt | Large-scale parallel computing |

### Recommended Visualization Methods
- **Small/Medium scale**: Normal mode (display all triangles)
- **Large/Ultra-large scale**: Lightweight mode (centroid point display) recommended

## Output Information

The following information is displayed in the console when running the program:
- Number of coordinates
- Number of faces
- Vertex data shape
- Coordinate ranges (X, Y, Z)
- Total surface area
- Centroid coordinates

## Troubleshooting

### C Program Compilation Errors
- Check your GCC version (gcc --version)
- Must support C99 standard

### Python-related Errors

#### Error: "No module named 'numpy'"
NumPy is not installed. Install it with the following command:
```bash
pip install numpy
```

#### Error: "No module named 'matplotlib'"
Matplotlib is not installed. Install it with the following command:
```bash
pip install matplotlib
```

#### Not displaying or slow display
- Large data may take time to render
- Ensure your graphics drivers are up to date
- If running via SSH, ensure X11 forwarding is enabled

#### Points appear as solid fill in lightweight mode
- Point size may be too large. Specify a smaller value (0.1-1.0) with the `-p` option
- Point density becomes very high with ultra-large data (over 1 million faces)
- You can verify individual points by outputting in vector format (PDF/SVG) and zooming in

#### Vector format output is slow or files become huge
- Vector format file sizes become very large with large-scale data
- Setting a size limit with `--max-vector-size` option automatically switches to PNG
- Using lightweight mode can reduce vector file size

## License

This project is released under the MIT License.

## Authors

BEM Data Processing Tools and 3D Polygon Data Visualization Tool Development Team

## Update History

- 2025-08-25:
  - Added binary format support
  - visualize_polygon.py can now directly read binary files (.bin)
  - Added detailed binary format specification to documentation
- 2025-08-24:
  - Added image output functionality in vector formats (PDF/SVG)
  - Added automatic file size control (automatic PNG conversion when vector files exceed specified size)
  - Adjusted default viewpoint angles (changed azimuth from 45 to 30 degrees)
- 2025-08-23:
  - Integrated visualize_polygon_advanced.py into visualize_polygon.py, updated documentation
  - Added lightweight mode (display only triangle centroids)
  - Added command line options (transparency, edge width, vertex display, lightweight mode initial settings)
  - Added image file output functionality (image generation without GUI, DPI settings, viewpoint angle settings)
  - Added adaptive point size functionality (automatically adjusts size according to point density to prevent overlap)
- 2025-08-20: Added C program descriptions, reorganized README structure
- 2025-08-19: Initial release
  - Basic visualization functionality
  - Advanced visualization functionality (with sliders and buttons)