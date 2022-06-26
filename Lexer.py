# Author:           0xL0RD

class Lexer:
    Tokens = {
        "main": "Main",
        "proc": "Proc",
        "halt": "Halt",
        "return": "Return",
        "if": "If",
        "then": "Then",
        "else": "Else",
        "do": "Do",
        "while": "While",
        "until": "Until",
        "output": "Output",
        "call": "Call",
        "true": "TRUE",
        "false": "FALSE",
        "input": "Input",
        "not": "Not",
        "and": "And",
        "or": "Or",
        "eq": "Eq",
        "larger": "Larger",
        "add": "Add",
        "sub": "Sub",
        "mult": "Mult",
        "arr": "Arr",
        "num": "Num",
        "bool": "Bool",
        "string": "String",
        ":=": "AssignmentToken",
        "{": "CurlyOpen",
        "}": "CurlyClose",
        "(": "RoundOpen",
        ")": "RoundClose",
        "[": "SquareOpen",
        "]": "SquareClose",
        ";": "InstrEnd",
        ",": "OpDelimeter",
        "#SHORTSTRING" : "ShortString",
        "#NUMBER": "Number",
        "#USERDEFINEDNAME" : "UserDefinedName"
    }

    lexerLines = []
    shortStrings:list = []
    userDefinedNames:list = []
    numbers:list = []
    processedTokens:list = []
    delimeters:list = ["{","}","[","]","(",")",";",",",":="]
    targetFileName:str = ""

    def __init__(self, sourceFile):
        self.targetFileName = sourceFile

    def __enforceStructure(self, fileData):
        lineIndex = 0
        temp : str
        for line in fileData:
            temp = line
            for i in range(len(temp)):
                temp = temp.replace(" "*(i+2), "")
            temp = temp.replace("\t", "")
            for terminal in self.delimeters:
                if terminal in temp:
                    temp = temp.replace(terminal, f" {terminal} ")
            temp = temp.replace("  ", " ")
            temp = temp.strip()
            fileData[lineIndex] = temp
            lineIndex += 1
        return fileData

    def __reportLexicalError(self, lineNbr, line, correctionalMessage):
        print(f"[-] Lexical Error\n")
        print(f"\tLine number: {lineNbr}\n\tIn: {line}\n\tError: {correctionalMessage}")

    def __isValidShortString(self, line:str) -> bool:
        validChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "
        if len( line ) > 17:
            return False
        for char in line[1:len(line)-1:]:
            if char not in validChars:
                return False
        return True

    def __getShortStrings(self, sourceFileData:list):
        lineNumber = 1
        for line in sourceFileData:
            temp = line 
            while "\"" in temp:
                open = sourceFileData[lineNumber-1].find("\"")

                close = open + sourceFileData[lineNumber-1][open+1::].find("\"") + 1

                if open == close:
                    self.__reportLexicalError(lineNumber, line, "Short strings must be enclosed by \"")
                    return []

                shortString = sourceFileData[lineNumber-1][open:close+1]

                if not self.__isValidShortString(shortString):
                    self.__reportLexicalError(lineNumber, line, "Short strings may only feature chars in range A-Z0-9 "
                                                                "and spaces (MAX-LENGTH=15)")
                    return []

                self.shortStrings.append(shortString)
                sourceFileData[lineNumber-1] = sourceFileData[lineNumber-1][:open:]+"#SHORTSTRING"+sourceFileData[lineNumber-1][close+1::]     
                temp = sourceFileData[lineNumber-1][close+1::]
                
            lineNumber += 1
        return sourceFileData

    def __isvalidUserDefinedName(self, line:str) -> bool:
        validChars = "abcdefghijklmnopqrstuvwxyz1234567890"
        if line[0] not in validChars[:26]:
            return False
        
        if len(line) > 1:
            for char in line[1::]:
                if char not in validChars:
                    return False
        return True

    def __getUserDefinedNames(self, sourceFileData:list):
        numbers = "-1234567890"
        lineNumber = 1
        for line in sourceFileData:
            elements:list = line.split(" ")
            for element in elements:
                if len(element) > 0:
                    if element not in self.Tokens.keys():
                        if element[0] not in numbers:
                            if not self.__isvalidUserDefinedName(element):
                                self.__reportLexicalError(lineNumber, line, f"User defined name \"{element}\" does "
                                                                            f"not conform to regex [a-z].([a-z0-9])*")
                                return []
                            else:
                                elements[elements.index(element)] = "#USERDEFINEDNAME"
                                self.userDefinedNames.append(element)

                                sourceFileData[lineNumber-1] = " ".join(elements)

            lineNumber += 1
        return sourceFileData

    def __isValidNumber(self, element:str):
        numbers = "1234567890"

        if len(element) > 1:
            if element[0] == "-":
                if element[1] not in numbers[:9:]:
                    return False
                else:
                    if len(element) > 2:
                        for char in element[1::]:
                            if char not in numbers:
                                return False      
                    return True
            elif element[0] in numbers[:9:]:
                for char in element[1::]:
                    if char not in numbers:
                        return False
                return True
            else:
                return False
        else:
            if element not in numbers:
                return False
        return True        

    def __getNumbers(self, sourceFileData:list):
        lineNumber = 1
        for line in sourceFileData:
            elements = line.split(" ")
            for element in elements:
                if len(element) > 0:
                    if element not in self.Tokens.keys():
                        if not self.__isValidNumber(element):
                            self.__reportLexicalError(lineNumber, line, f"\"{element}\" is not a valid number in SPL.")
                            return []
                        else:
                            elements[elements.index(element)] = "#NUMBER"
                            self.numbers.append(element)
                            sourceFileData[lineNumber-1] = " ".join(elements)

            lineNumber += 1
        return sourceFileData

    def __generateTokens(self, sourceFileData):
        lineNumber = 1
        TokenId = 0
        for line in sourceFileData:
            elements = line.split(" ")
            for element in elements:
                if element != "\n":
                    if element in self.Tokens.keys():
                        if element == "#SHORTSTRING":
                            shortString = self.shortStrings[0]
                            if len(self.shortStrings) > 1:
                                self.shortStrings = self.shortStrings[1::]
                            self.processedTokens.append(f"[{TokenId}: {self.Tokens[element]} -> {shortString}] {lineNumber}")
                        elif element == "#USERDEFINEDNAME":
                            userDefinedName = self.userDefinedNames[0]
                            if len(self.userDefinedNames) > 1:
                                self.userDefinedNames = self.userDefinedNames[1::]
                            self.processedTokens.append(f"[{TokenId}: {self.Tokens[element]} -> {userDefinedName}] {lineNumber}")
                        elif element == "#NUMBER":
                            number = self.numbers[0]
                            if len(self.numbers) > 1:
                                self.numbers = self.numbers[1::] 
                            self.processedTokens.append(f"[{TokenId}: {self.Tokens[element]} -> {number}] {lineNumber}")
                        else:
                            self.processedTokens.append(f"[{TokenId}: {self.Tokens[element]} -> {element}] {lineNumber}")

                        TokenId += 1
            lineNumber += 1

    def Scan(self):
        with open(self.targetFileName, "r") as f:
            self.lexerLines = f.readlines()
        
        self.lexerLines = self.__getShortStrings(self.lexerLines)
        self.lexerLines = self.__enforceStructure(self.lexerLines)
        self.lexerLines = self.__getUserDefinedNames(self.lexerLines)
        self.lexerLines = self.__getNumbers(self.lexerLines)
        
        if self.lexerLines == []:
            return [], False

        self.__generateTokens(self.lexerLines)

        return self.processedTokens, True
    
    def printTokens(self):
        print("Tokens:")
        for token in self.processedTokens:
            print(token)
        print("="*50)

    def printCompilerLines(self):
        print("Compiler lines: ")
        for line in self.lexerLines:
            print(line)
        print("="*50)
