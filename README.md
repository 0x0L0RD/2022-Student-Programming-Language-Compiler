# 2022-Student-Programming-Language-Compiler
A compiler for a programming language that prof. Gruner had us implement for Compiler Design (COS 341) in 2022.

## Before you start...
Basically, this "compiler" was our practical project for the compiler module. Since it was to serve as an introduction to compiler design,
there were some liberties that were taken. Firstly, as you'll soon notice, there was hardly any optimization that was required from us students.
Secondly, we only needed to generate the "intermediate code" (which, you may notice, is vintage BASIC code). That is to say, we didn't have to write any 
machine code translation components. 

Futhermore, yes, I know. There are some parts of the specification that I did not implement. More specifically, dead code elimination. 
The short explanation for that is simply becuase I didn't have time to do it :)

Finally, I think it's worth stating that I am not one for compiler design. I've always been more interested in reversing (reverse-engineering) software, 
but I decided to share this because I found it interesting how multi-layered and complicated the process of software compilation really is.
Though I was not necessarily passionate about this project in particular, it did make me appreciate the amount of work that goes into compilation software such 
as g++, gcc, MinGW, Javac, etc. 

## Usage 
To run the compiler:
```./splCompiler <input file name> [verbosity]```

The input file must exist on disk. If it is in the current working directory, then the file name
will suffice, otherwise, specify the full path to the file. Verbosity is an optional flag.
Verbosity is specified with a ```-v``` for standard verbosity and ```-vv``` for maximum verbosoty.
The verbosity flag outputs more information about what is happening in the compilation process.

Example usage:<br/>
    ```./splCompiler.py input.txt```<br/>
    ```./splCompiler.py input.txt -v```<br/>
    ```./splCompiler.py ../../programs/fizzbuzz.spl -vv```<br/>


### Note
  - This application is intended for use on Linux machines with Python3 installed. 
  - If you would like to run this application on a Windows machine, python must be 
    invoked from the command line before ./splCompiler.py. 
  - I used .txt and .spl as input file extensions in the example usage, but, really, any text file with valid code will compile :) .
    
