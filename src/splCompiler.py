#!/usr/bin/python3

# Author:           0x0L0RD

from sys import argv
from Lexer import Lexer
from Parser import Parser
from SemanticAnalyzer import SemanticAnalyzer
from Translator import CodeGenerator


def main():
    if len(argv) < 2:
        print(f"usage: {argv[0]} <path to source file> [optional verbosity]")
        print("\t\tVerbosity flags:\n\t\t\t-v\tVerbose\n\t\t\t-vv\tMaximum Verbosity\n\n")
        exit(1)

    try:
        lexer = Lexer(argv[1])
        parser = Parser(argv[1])
        tokens, success = lexer.Scan()

        if len(argv) > 2:
            if argv[2] == "-vv":
                print("[i] Generating tokens from:")
                lexer.printCompilerLines()
            if "-v" in argv[2]:
                print("[i] Printing tokens.")
                lexer.printTokens()

        if success:
            if parser.parse(tokens):
                outputFile = argv[1].replace(".txt", ".xml")
                if not outputFile.endswith(".xml"):
                    outputFile.replace(".", "")
                    outputFile += ".xml"
                parser.saveSyntaxTreeXML(outputFile)
                print(f"[+] Successfully parsed. See '{outputFile}'")
                semanticAnalyzer = SemanticAnalyzer(parser.Tree, argv[1])
                if semanticAnalyzer.Scan():
                    print("[+] Semantic analysis passed.")
                    cGen = CodeGenerator(semanticAnalyzer.initialTree, semanticAnalyzer.semantic_table,
                                         semanticAnalyzer.discoveredIds)
                    outputFile = argv[1].replace(".txt", ".bas")
                    if not outputFile.endswith(".bas"):
                        outputFile.replace(".", "")
                        outputFile += ".bas"
                    cGen.translate_functions(outputFile)
                    print(f"[+] Compiled successfully. See '{outputFile}'.")
                    if len(argv) > 2:
                        if argv[2] == "-vv":
                            semanticAnalyzer.print_symbol_table()
                            cGen.print_symbolic_label_table()
                            cGen.print_basic_code()
            else:
                print("[-] Error occurred while parsing.")
        else:
            print("[-] Error occurred during lexical analysis.")
    except Exception as e:
        print(f"[-] Exception: {e}")


if __name__ == "__main__":
    main()
