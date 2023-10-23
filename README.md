# C code generator

The file `c_code_generator.py` is designed to generate valid but dummy C code.
It randomly creates multiple function signatures and one large function body, with an arbitrary number of lines and specific characteristics.
The function body includes variable declarations, assignments, if-else conditions, while loops, function calls and return statements. 
The percentage of each of these constructs can be customized by command-line arguments (run `python c_code_generator.py -h`).

The C code generator may be useful to evaluate the performance of tools on large files. 

The scripts inside `lsa_scripts` were used to evaluate the performance of a lifetimes static analyzer on large C files, as well as generate plots with the results obtained. 

