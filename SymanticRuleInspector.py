# Author:           0xL0RD

from SemanticTable import SemanticTable
from Parser import SyntaxTree, Node


class SemanticRuleEnforcer:
    sem_table: SemanticTable
    initial_tree: SyntaxTree

    def __init__(self, st: SemanticTable, it: SyntaxTree):
        self.sem_table = st
        self.initial_tree = it

    def __is_array(self, current: Node):
        immediate_right_child_position = current.parent.children.index(current) + 1
        immediate_right_child = current.parent.children[immediate_right_child_position]
        if immediate_right_child.value == "VAR":
            if len(immediate_right_child.children) > 0:
                if immediate_right_child.children[0].value == "[":
                    return True
        return False

    def __appl_decl_var_check(self, n: Node):
        if n.value == "UserDefinedName":
            if n.parent.value != "PD" and n.parent.value != "Dec" and n.parent.value != "PCall":
                target_var = n.subValue
                if self.__is_array(n):
                    target_var += "[]"
                var_entry = self.sem_table.get_variable_by_name(target_var)
                if var_entry is None:
                    return n
                else:
                    if var_entry["ScopeID"] not in self.sem_table.get_ancestor_scopes(var_entry["ScopeID"]):
                        return n

        for child in n.children:
            lower_check = self.__appl_decl_var_check(child)
            if lower_check is not None:
                return lower_check

        return None

    def __appl_decl_proc_check(self, n: Node):
        if n.value == "PCall":
            target_node = n.children[1]
            target_procedure = n.children[1].subValue

            if target_procedure == "main":
                raise Exception("Critical Error - 'main' is not callable from within the program.")

            callable_funcs = self.sem_table.get_callable_procs_from(target_node.scopeID)

            if target_procedure not in callable_funcs:
                return target_node

        for child in n.children:
            lower_check = self.__appl_decl_proc_check(child)
            if not lower_check is None:
                return lower_check

        return None

    def __matching_proc_call_exists(self, n: Node, proc: str, scope_ids: str):
        if n.value == "PCall":
            target_proc = n.children[1].subValue
            if target_proc == proc and n.children[1].scopeID in scope_ids:
                return True
        for child in n.children:
            lower_check = self.__matching_proc_call_exists(child, proc, scope_ids)
            if lower_check:
                return lower_check
        return False

    def __variable_is_used(self, current: Node, udn: str, scope_id: str):
        if current.value == "UserDefinedName":
            if current.parent.value != "PD" and current.parent.value != "Dec" and current.parent.value != "PCall":
                var_name = current.subValue
                if self.__is_array(current):
                    var_name += "[]"
                if scope_id in self.sem_table.get_ancestor_scopes(current.scopeID) and var_name == udn:
                    return True

        for child in current.children:
            lower_check = self.__variable_is_used(child, udn, scope_id)
            if lower_check:
                return lower_check
        return False

    def __decl_appl_var_check(self):
        all_declared_variables = self.sem_table.Table["Variables"]
        for variable in all_declared_variables:
            var_is_used = self.__variable_is_used(self.initial_tree.root, variable["Token"], variable["ScopeID"])
            if not var_is_used:
                raise Exception(
                    f"DECL-APPL Error - variable \'{variable['Token']}\' declared but never used.\n")

    def __decl_appl_proc_check(self):
        all_declared_procedures = self.sem_table.Table["Procedures"]
        for procedure in all_declared_procedures:
            valid_scopes = self.sem_table.get_valid_call_scopes(procedure["ScopeID"])
            call_made = self.__matching_proc_call_exists(self.initial_tree.root, procedure["Token"], valid_scopes)
            if not call_made and procedure["Token"] != "main":
                raise Exception(
                    f"DECL-APPL Error - procedure \'{procedure['Token']}\' declared but never called.\n")

    def procedure_rule_inspection(self):
        appl_decl = self.__appl_decl_proc_check(self.initial_tree.root)
        if not appl_decl is None:
            return appl_decl
        self.__decl_appl_proc_check()

    def variable_rule_inspection(self):
        appl_decl = self.__appl_decl_var_check(self.initial_tree.root)
        if appl_decl is not None:
            return appl_decl
        self.__decl_appl_var_check()
