# Author:           0xL0RD

from Parser import Node, SyntaxTree
from SemanticTable import SemanticTable
from SymanticRuleInspector import SemanticRuleEnforcer
from TypeChecker import TypeChecker


class SemanticAnalyzer:
    initialTree: SyntaxTree
    ScopeTree: SyntaxTree
    ScopeID: int
    ProcID: int
    VarID: int
    SemanticID: int
    discoveredIds: dict = {}
    semantic_table: SemanticTable
    source_file_name: str
    rule_enforcer: SemanticRuleEnforcer
    type_checker: TypeChecker

    def __init__(self, initialSyntaxTree: SyntaxTree, sourceFile):
        self.initialTree = initialSyntaxTree
        self.semantic_table = SemanticTable()
        self.ScopeID = 0
        self.VarID = 0
        self.ProcID = 0
        self.SemanticID = 0
        self.source_file_name = sourceFile

    def __discoveredIDsContains(self, Scope: Node) -> bool:
        for Ids in self.discoveredIds.keys():
            start, end = Ids
            if Scope.ID == start and Scope.closer.ID == end:
                return True
        return False

    def __assignParent(self, newScope: Node):
        n_scope_start = newScope.ID
        n_scope_end = newScope.closer.ID
        match = False
        bestMatch = None
        bestDifference = None
        if not self.__discoveredIDsContains(newScope):
            for Ids in self.discoveredIds.keys():
                start, end = Ids
                n_scope_start = newScope.ID
                n_scope_end = newScope.closer.ID
                if int(start) < int(n_scope_start) and int(end) > int(n_scope_end):
                    difference = (int(n_scope_start) - int(start)) + (int(end) - int(n_scope_end))
                    if bestMatch is None:
                        bestMatch = Ids
                        bestDifference = difference
                        match = True
                    else:
                        if difference < bestDifference:
                            bestMatch = Ids
                            bestDifference = difference
            if not match:
                self.ScopeTree.root.children.append(newScope)
                newScope.parent = self.ScopeTree.root
                newScope.parent_scope_id = "0"
            else:
                parent = self.discoveredIds[bestMatch]
                newScope.parent_scope_id = self.discoveredIds[bestMatch].scopeID
                parent.children.append(newScope)
                newScope.parent = parent
            newScope.scopeID = str(self.ScopeID)
            self.semantic_table.add_scope(newScope.value, newScope.ID, newScope.scopeID, newScope.parent_scope_id)
            self.ScopeID += 1
            self.discoveredIds.update({(n_scope_start, n_scope_end): newScope})

    def __searchForScopeIdentifiers(self, current: Node):
        todo = [current]
        done = []
        while len(todo) > 0:
            todo.remove(current)
            done.append(current)
            for child in current.children:
                if child.value == "{" and child.parent.value == "PD":
                    prev = current.children.index(child) - 1
                    if prev > -1:
                        try:
                            newScopeNode = Node(current.children[prev].subValue, [])
                        except:
                            newScopeNode = Node(current.children[prev].value, [])
                    else:
                        newScopeNode = Node("ArbitraryScope", [])

                    newScopeNode.ID = current.children[current.children.index(child) - 1].ID
                    newStart = current.children.index(child) + 1
                    for sChild in current.children[newStart::]:
                        if sChild.value == "}":
                            closer = Node(sChild.value, [])
                            closer.ID = sChild.ID
                            newScopeNode.closer = closer
                            break
                    self.__assignParent(newScopeNode)
                    current.children[prev].scopeID = newScopeNode.scopeID
                if child not in done:
                    todo.append(child)

            if len(todo) > 0:
                current = todo[0]

    def __recursiveMainScopeSearch(self, current: Node):
        mainFound = False
        for child in current.children:
            newStart = current.children.index(child) + 1
            if child.value == "main" and current.children[newStart].value == "{":
                newRootNode = Node(child.value, [])
                for cChild in current.children[newStart + 1::]:
                    if cChild.value == "}":
                        newlyDiscoveredScope = (current.children[newStart].ID, cChild.ID)
                        newRootNode.closer = cChild
                        newRootNode.ID = child.ID
                        newRootNode.scopeID = str(self.ScopeID)
                        self.semantic_table.add_scope(newRootNode.value, newRootNode.ID, newRootNode.scopeID, "-")
                        self.ScopeID += 1
                        self.discoveredIds.update({newlyDiscoveredScope: newRootNode})
                self.ScopeTree = SyntaxTree(newRootNode, self.initialTree.terminalTokens)
                return newRootNode

        if not mainFound:
            for child in current.children:
                result = self.__recursiveMainScopeSearch(child)
                if result:
                    return result

    def __findScopes(self):
        self.__recursiveMainScopeSearch(self.initialTree.root)
        self.__searchForScopeIdentifiers(self.initialTree.root)

    @staticmethod
    def __check_parent_for_user_defined_name(c_node: Node):
        target_parent_found = False
        parent = c_node.parent
        while not target_parent_found:
            if parent is not None:
                if parent.value == "PD" and parent != c_node.parent:
                    target_parent_found = True
                else:
                    parent = parent.parent
            else:
                return False
        if parent.children[1].value == "UserDefinedName" and parent.children[1].subValue == c_node.subValue:
            return True
        return False

    def __getNodeScope(self, current: Node, is_proc=False):
        bestMatch = None
        bestDifference = None
        for Ids in self.discoveredIds.keys():
            start, end = Ids
            if int(start) < int(current.ID) < int(end):
                difference = (int(current.ID) - int(start)) + (int(end) - int(current.ID))

                if current.value != "main":
                    if not is_proc:
                        existing_entry_of_this_scope = self.semantic_table.get_variable_with(current.subValue,
                                                                                             self.discoveredIds[
                                                                                                 Ids].scopeID)
                        if current.parent.value != "Decl":
                            if existing_entry_of_this_scope is not None and current.semantic_id == "":
                                current.semantic_id = existing_entry_of_this_scope["SemanticID"]

                if bestMatch is None:
                    bestMatch = Ids
                    bestDifference = difference
                else:
                    if difference < bestDifference:
                        bestMatch = Ids
                        bestDifference = difference
        if bestMatch is None:
            if current.scopeID == "":
                current.scopeID = "0"
        else:
            if current.scopeID == "":
                current.scopeID = self.discoveredIds[bestMatch].scopeID
            if is_proc:
                # Inner scope
                existing_entry_of_this_scope = self.semantic_table.get_procedure_with(current.subValue,
                                                                                      self.discoveredIds[
                                                                                          bestMatch].scopeID)
                if existing_entry_of_this_scope is not None:
                    self.__report_semantic_error(current,
                                                 f"Redefinition of existing procedure within the same scope.\n\t\tProc: {existing_entry_of_this_scope['Token']}")

                # Parent scope.
                if self.__check_parent_for_user_defined_name(current):
                    self.__report_semantic_error(current,
                                                 f"Redefinition of parent procedure.\n\t\tProc: {current.subValue}")

        if not is_proc:
            existing_entry_of_this_scope = self.semantic_table.get_variable_with(current.subValue,
                                                                                 self.discoveredIds[bestMatch].scopeID)
            if existing_entry_of_this_scope is not None:
                self.__report_semantic_error(current,
                                             f"Redeclaration of variable '{current.subValue}' within same scope.")

        if current.semantic_id == "":
            current.semantic_id = str(self.SemanticID)
            self.SemanticID += 1

    @staticmethod
    def __is_array(current: Node):
        if current.parent.children[0].value == "arr":
            return True
        return False

    @staticmethod
    def __getType(current: Node):
        parent = current.parent

        for child in parent.children:
            if child.value == "TYP":
                return child.children[0].value

        raise "Critical error - type not found. Possible hacking detected."

    def __recursiveTableBuild(self, current: Node):
        if current.value == "UserDefinedName":
            if current.parent.value == "PD":
                self.__getNodeScope(current, True)
                self.semantic_table.add_procedure_entry(current.subValue, current.scopeID, current.ID,
                                                        current.semantic_id)
            else:
                self.__getNodeScope(current, False)
                if current.parent.value == "Dec":
                    type_ = self.__getType(current)
                    if self.__is_array(current):
                        size_node = current.parent.children[3]
                        if size_node.value == "Const":
                            size_ = size_node.children[0].subValue
                        else:
                            size_ = size_node.subValue
                        self.semantic_table.add_variable_entry(current.subValue + "[]", current.scopeID, current.ID,
                                                               current.semantic_id, type_, size_)
                    else:
                        self.semantic_table.add_variable_entry(current.subValue, current.scopeID, current.ID,
                                                               current.semantic_id, type_)
        elif current.value == "main":
            self.__getNodeScope(current, True)
            self.semantic_table.add_procedure_entry(current.value, current.scopeID, current.ID, current.semantic_id)

        for child in current.children:
            self.__recursiveTableBuild(child)

    def __report_semantic_error(self, erroneous_node: Node, message: str):
        lines: list
        with open(self.source_file_name, "r") as f:
            lines = f.readlines()

        raise Exception(
            f"{message}\n\t\tLine {erroneous_node.lineNumber}: {lines[int(erroneous_node.lineNumber) - 1].strip()}")

    def saveScopeTreeXML(self, fileName: str):
        self.ScopeTree.fileName = fileName
        self.ScopeTree.createXMLTree(None, self.ScopeTree.root)

    def Scan(self):
        self.__findScopes()
        self.__recursiveTableBuild(self.initialTree.root)
        self.rule_enforcer = SemanticRuleEnforcer(self.semantic_table, self.initialTree)
        rule_inspection = self.rule_enforcer.procedure_rule_inspection()
        if rule_inspection is not None:
            self.__report_semantic_error(rule_inspection,
                                         f"APPL-DECL Error - call made to out-of-scope or non-existing procedure '{rule_inspection.subValue}'")
        rule_inspection = self.rule_enforcer.variable_rule_inspection()
        if rule_inspection is not None:
            self.__report_semantic_error(rule_inspection,
                                         f"APPL-DECL Error - variable '{rule_inspection.subValue}' is referenced but is never declared.")

        self.type_checker = TypeChecker(self.semantic_table, self.initialTree, self.source_file_name)
        self.type_checker.check()
        return True

    def print_symbol_table(self):
        self.semantic_table.print_table()
