# Author:           0xL0RD

from xml.etree import ElementTree as eTree


class Node:
    value: str
    children: list
    parent: any
    subValue: str
    lineNumber: str
    ID: str
    scopeID: str
    parent_scope_id: str
    semantic_id: str
    data_type: str
    closer = None

    def __init__(self, value, children=None):
        if children is None:
            children = []
        self.value = value
        self.children = children
        self.parent = None
        self.lineNumber = ""
        self.scopeID = ""
        self.closer = None
        self.semantic_id = ""
        self.data_type = "U"


class SyntaxTree:
    root: Node
    terminalTokens: list
    ID = 0
    fileName: str

    specialCases = {
        ":=": "AssignmentOperator",
        "{": "OpenBraceCurly",
        "}": "CloseBraceCurly",
        "(": "OpenBraceRound",
        ")": "CloseBraceRound",
        "[": "OpenBraceRect",
        "]": "CloseBraceRect",
        ";": "InstrEnd",
        ",": "DelimeterComma"
    }

    def __init__(self, rootNode: Node, terminals):
        self.root = rootNode
        self.terminalTokens = terminals

    def createXMLTree(self, parent, node: Node):
        if parent == None:
            nodeElement = eTree.Element(node.value)
        else:
            if node.value in self.terminalTokens:
                if node.value in self.specialCases.keys():
                    nodeElement = eTree.SubElement(parent, self.specialCases[node.value])
                else:
                    nodeElement = eTree.SubElement(parent, node.value)

                if (node.value == "Number" or node.value == "ShortString" or node.value == "UserDefinedName"):
                    nodeElement.text = f"{node.subValue}"
                else:
                    nodeElement.text = node.value

                if (node.lineNumber != ""):
                    nodeElement.set("lineNumber", node.lineNumber)
            else:
                elementName = node.value
                if elementName == "ε":
                    elementName = "EPSILON"
                elif elementName == "VAR'":
                    elementName = "FIELDPRIME"
                elif elementName == "VAR":
                    elementName = "FIELD"

                nodeElement = eTree.SubElement(parent, elementName)

        nodeElement.set("id", str(self.ID))
        node.ID = self.ID

        self.ID += 1

        for child in node.children:
            self.createXMLTree(nodeElement, child)

        if parent == None:
            data = eTree.tostring(nodeElement)

            with open(self.fileName, "wb+") as f:
                f.write(data)


class Parser:
    Table: dict = {}
    Tree: SyntaxTree
    Stack = list
    srcFile: str

    def __init__(self, sourcefile):
        self.srcFile = sourcefile
        defualtObj = {
            "SPL": "",
            "SPLProgr": "",
            "ProcDefs": "",
            "PD": "",
            "Algorithm": "",
            "Instr": "",
            "Assign": "",
            "Branch": "",
            "Alternat": "",
            "Loop": "",
            "LHS": "",
            "Expr": "",
            "VAR": "",
            "VAR'": "",
            "PCall": "",
            "Const": "",
            "UnOp": "",
            "BinOp": "",
            "VarDecl": "",
            "Dec": "",
            "TYP": "",
        }

        self.Table["main"] = defualtObj.copy()
        self.Table["main"]["SPL"] = "SPLProgr"
        self.Table["main"]["SPLProgr"] = "ProcDefs main { Algorithm halt ; VarDecl }"
        self.Table["main"]["ProcDefs"] = "ε"

        self.Table["{"] = defualtObj.copy()

        self.Table["halt"] = defualtObj.copy()
        self.Table["halt"]["Algorithm"] = "ε"

        self.Table[";"] = defualtObj.copy()
        self.Table[";"]["Alternat"] = "ε"
        self.Table[";"]["VAR"] = "ε"

        self.Table["}"] = defualtObj.copy()
        self.Table["}"]["Algorithm"] = "ε"
        self.Table["}"]["VarDecl"] = "ε"

        self.Table[","] = defualtObj.copy()
        self.Table[","]["VAR"] = "ε"
        self.Table[","]["ProcDefs"] = "ε"

        self.Table["proc"] = defualtObj.copy()
        self.Table["proc"]["SPL"] = "SPLProgr"
        self.Table["proc"]["SPLProgr"] = "ProcDefs main { Algorithm halt ; VarDecl }"
        self.Table["proc"]["ProcDefs"] = "PD , ProcDefs"
        self.Table["proc"]["PD"] = "proc UserDefinedName { ProcDefs Algorithm return ; VarDecl }"

        self.Table["UserDefinedName"] = defualtObj.copy()
        self.Table["UserDefinedName"]["ProcDefs"] = "ε"
        self.Table["UserDefinedName"]["Algorithm"] = "Instr ; Algorithm"
        self.Table["UserDefinedName"]["Instr"] = "Assign"
        self.Table["UserDefinedName"]["Assign"] = "LHS := Expr"
        self.Table["UserDefinedName"]["LHS"] = "UserDefinedName VAR"
        self.Table["UserDefinedName"]["Expr"] = "UserDefinedName VAR"
        self.Table["UserDefinedName"]["VAR'"] = "UserDefinedName ]"

        self.Table["return"] = defualtObj.copy()
        self.Table["return"]["Algorithm"] = "ε"
        self.Table["return"]["ProcDefs"] = "ε"

        self.Table[":="] = defualtObj.copy()
        self.Table[":="]["VAR"] = "ε"

        self.Table["if"] = defualtObj.copy()
        self.Table["if"]["ProcDefs"] = "ε"
        self.Table["if"]["Algorithm"] = "Instr ; Algorithm"
        self.Table["if"]["Instr"] = "Branch"
        self.Table["if"]["Branch"] = "if ( Expr ) then { Algorithm } Alternat"

        self.Table["("] = defualtObj.copy()

        self.Table[")"] = defualtObj.copy()
        self.Table[")"]["VAR"] = "ε"

        self.Table["then"] = defualtObj.copy()

        self.Table["else"] = defualtObj.copy()
        self.Table["else"]["Alternat"] = "else { Algorithm }"

        self.Table["do"] = defualtObj.copy()
        self.Table["do"]["ProcDefs"] = "ε"
        self.Table["do"]["Algorithm"] = "Instr ; Algorithm"
        self.Table["do"]["Instr"] = "Loop"
        self.Table["do"]["Loop"] = "do { Algorithm } until ( Expr )"

        self.Table["until"] = defualtObj.copy()

        self.Table["while"] = defualtObj.copy()
        self.Table["while"]["ProcDefs"] = "ε"
        self.Table["while"]["Algorithm"] = "Instr ; Algorithm"
        self.Table["while"]["Instr"] = "Loop"
        self.Table["while"]["Loop"] = "while ( Expr ) do { Algorithm }"

        self.Table["output"] = defualtObj.copy()
        self.Table["output"]["ProcDefs"] = "ε"
        self.Table["output"]["Algorithm"] = "Instr ; Algorithm"
        self.Table["output"]["Instr"] = "Assign"
        self.Table["output"]["Expr"] = "LHS := Expr"
        self.Table["output"]["Loop"] = "while ( Expr ) do { Algorithm }"
        self.Table["output"]["LHS"] = "output"
        self.Table["output"]["Assign"] = "LHS := Expr"

        self.Table["["] = defualtObj.copy()
        self.Table["["]["VAR"] = "[ VAR'"

        self.Table["]"] = defualtObj.copy()

        self.Table["call"] = defualtObj.copy()
        self.Table["call"]["ProcDefs"] = "ε"
        self.Table["call"]["Algorithm"] = "Instr ; Algorithm"
        self.Table["call"]["Instr"] = "PCall"
        self.Table["call"]["PCall"] = "call UserDefinedName"

        self.Table["ShortString"] = defualtObj.copy()
        self.Table["ShortString"]["Expr"] = "Const"
        self.Table["ShortString"]["VAR'"] = "Const ]"
        self.Table["ShortString"]["Const"] = "ShortString"

        self.Table["Number"] = defualtObj.copy()
        self.Table["Number"]["Expr"] = "Const"
        self.Table["Number"]["VAR'"] = "Const ]"
        self.Table["Number"]["Const"] = "Number"

        self.Table["true"] = defualtObj.copy()
        self.Table["true"]["Expr"] = "Const"
        self.Table["true"]["VAR'"] = "Const ]"
        self.Table["true"]["Const"] = "true"

        self.Table["false"] = defualtObj.copy()
        self.Table["false"]["Expr"] = "Const"
        self.Table["false"]["VAR'"] = "Const ]"
        self.Table["false"]["Const"] = "false"

        self.Table["input"] = defualtObj.copy()
        self.Table["input"]["Expr"] = "UnOp"
        self.Table["input"]["UnOp"] = "input ( UserDefinedName )"

        self.Table["not"] = defualtObj.copy()
        self.Table["not"]["Expr"] = "UnOp"
        self.Table["not"]["UnOp"] = "not ( Expr )"

        self.Table["and"] = defualtObj.copy()
        self.Table["and"]["Expr"] = "BinOp"
        self.Table["and"]["BinOp"] = "and ( Expr , Expr )"

        self.Table["or"] = defualtObj.copy()
        self.Table["or"]["Expr"] = "BinOp"
        self.Table["or"]["BinOp"] = "or ( Expr , Expr )"

        self.Table["eq"] = defualtObj.copy()
        self.Table["eq"]["Expr"] = "BinOp"
        self.Table["eq"]["BinOp"] = "eq ( Expr , Expr )"

        self.Table["larger"] = defualtObj.copy()
        self.Table["larger"]["Expr"] = "BinOp"
        self.Table["larger"]["BinOp"] = "larger ( Expr , Expr )"

        self.Table["add"] = defualtObj.copy()
        self.Table["add"]["Expr"] = "BinOp"
        self.Table["add"]["BinOp"] = "add ( Expr , Expr )"

        self.Table["sub"] = defualtObj.copy()
        self.Table["sub"]["Expr"] = "BinOp"
        self.Table["sub"]["BinOp"] = "sub ( Expr , Expr )"

        self.Table["mult"] = defualtObj.copy()
        self.Table["mult"]["Expr"] = "BinOp"
        self.Table["mult"]["BinOp"] = "mult ( Expr , Expr )"

        self.Table["arr"] = defualtObj.copy()
        self.Table["arr"]["VarDecl"] = "Dec ; VarDecl"
        self.Table["arr"]["Dec"] = "arr TYP [ Const ] UserDefinedName"

        self.Table["num"] = defualtObj.copy()
        self.Table["num"]["VarDecl"] = "Dec ; VarDecl"
        self.Table["num"]["Dec"] = "TYP UserDefinedName"
        self.Table["num"]["TYP"] = "num"

        self.Table["bool"] = defualtObj.copy()
        self.Table["bool"]["VarDecl"] = "Dec ; VarDecl"
        self.Table["bool"]["Dec"] = "TYP UserDefinedName"
        self.Table["bool"]["TYP"] = "bool"

        self.Table["string"] = defualtObj.copy()
        self.Table["string"]["VarDecl"] = "Dec ; VarDecl"
        self.Table["string"]["Dec"] = "TYP UserDefinedName"
        self.Table["string"]["TYP"] = "string"

    def __reportError(self, input, expected):
        print(f"\t*************[ Syntax Error ]*************")
        FOUND = input["type"]
        if FOUND == "":
            FOUND = input["value"]

        line: str

        with open(self.srcFile, "r") as f:
            lines = f.readlines()
            line = lines[int(input['line']) - 1]

        print(
            f"\t\tFound: {FOUND}\n\t\tIn sequence: \'{line.strip()}\' on line {input['line']}\n\t\tExpected: {expected.value}\n")

    def __createNodes(self, elements: list) -> list:
        nodes: list = []

        for element in elements:
            nodes.append(Node(element))

        return nodes

    def __addChildren(self, parent: Node, children: list):
        for child in children:
            child.parent = parent

        parent.children = children

    def parse(self, tokens) -> bool:
        input = []

        for token in tokens:
            Type = token.split(" -> ")[0][token.find(": ") + 2::]
            lineNumber = token.split(" -> ")[1].split("] ")[1].strip("\n")
            rToken = token.split(" -> ")[1].split("] ")[0]

            if Type == "Number" or Type == "UserDefinedName" or Type == "ShortString":
                input.append({
                    "type": Type,
                    "line": lineNumber,
                    "value": f"{rToken}"
                })

            else:
                input.append({
                    "type": rToken,
                    "line": lineNumber,
                    "value": ""
                })

        input = list(reversed(input))
        first = Node("SPL")
        self.Tree = SyntaxTree(first, self.Table.keys())
        self.Stack = [first]

        while len(self.Stack) > 0 and len(input) > 0:
            top = len(self.Stack) - 1
            iTop = len(input) - 1

            if (self.Stack[top].value in self.Table.keys()):
                if (self.Stack[top].value == input[iTop]["type"]):
                    if (input[iTop]["type"] == "Number" or input[iTop]["type"] == "ShortString" or input[iTop][
                        "type"] == "UserDefinedName"):
                        self.Stack[top].subValue = input[iTop]["value"]
                    self.Stack[top].lineNumber = input[iTop]["line"]
                    input.pop()
                    self.Stack.pop()
                else:
                    self.__reportError(input.pop(), self.Stack.pop())
                    return False
            elif (self.Table[(input[iTop]["type"])][self.Stack[top].value] == ""):
                self.__reportError(input[iTop], self.Stack[top])
                return False
            else:
                nonTerminal = self.Stack.pop()
                MatchedValueAsStackElements = list(
                    reversed(self.Table[input[iTop]["type"]][nonTerminal.value].split(" ")))
                children = self.__createNodes(MatchedValueAsStackElements)
                self.__addChildren(nonTerminal, list(reversed(children)))
                if children[0].value != "ε":
                    self.Stack.extend(children)

        if len(self.Stack) != len(input):
            with open(self.srcFile, "r") as f:
                allLines = f.readlines()
            self.__reportError({"type": "EOF", "line": str(len(allLines))}, self.Stack.pop())
            return False
        return True

    def saveSyntaxTreeXML(self, filename):
        self.Tree.fileName = filename
        self.Tree.createXMLTree(None, self.Tree.root)
