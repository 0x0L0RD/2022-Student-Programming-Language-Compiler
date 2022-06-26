# Author:           0xL0RD

from Parser import Node, SyntaxTree
from SemanticTable import SemanticTable


class TypeChecker:
    sem_table: SemanticTable
    error_assign_messages = {
        "S": f"Assigning non-string value to String variable",
        "U": f"Attempting to assign Unknown variable type",
        "N": f"Assigning non-numeric value to Number variable",
        "B": f"Assigning non-binary value to Boolean variable",
        "M": ["N", "S"]
    }
    source_file: str
    tree: SyntaxTree

    def __init__(self, st: SemanticTable, t: SyntaxTree, fname: str):
        self.sem_table = st
        self.source_file = fname
        self.tree = t

    @staticmethod
    def __is_array(current: Node):
        immediate_right_child_position = current.parent.children.index(current) + 1
        immediate_right_child = current.parent.children[immediate_right_child_position]
        if immediate_right_child.value == "VAR":
            if len(immediate_right_child.children) > 0:
                if immediate_right_child.children[0].value == "[":
                    return True
        return False

    def __eval_expr(self, expr_node: Node):
        resulting_type = None
        if expr_node.children[0].value == "UnOp":
            resulting_type = self.__unop(expr_node.children[0])
        elif expr_node.children[0].value == "Const":
            resulting_type = self.__const(expr_node.children[0])
        elif expr_node.children[0].value == "UserDefinedName":
            data_type, is_array = self.__get_data_type(expr_node.children[0])
            resulting_type = data_type
        elif expr_node.children[0].value == "BinOp":
            resulting_type = self.__binop(expr_node.children[0])

        expr_node.data_type = resulting_type
        return resulting_type

    def __binop(self, bin_op_node: Node):
        numerical_ops = ["add", "sub", "mult"]
        binary_ops = ["not", "and", "or", "eq", "larger"]
        operation = bin_op_node.children[0].value
        expr_1 = bin_op_node.children[2]
        expr_2 = bin_op_node.children[4]
        expr_1_type = self.__eval_expr(expr_1)
        expr_2_type = self.__eval_expr(expr_2)
        if expr_1_type == expr_2_type:
            if operation in binary_ops:
                return "B"
            else:
                if operation in numerical_ops and expr_1_type == "N":
                    return "N"
                else:
                    self.__report_type_error(f"'{operation}' operation only permits the use of numeric data.",
                                             bin_op_node)
        else:
            if operation == "eq":
                return "B"
            elif operation in binary_ops:
                if expr_1_type != "B":
                    err_node = expr_1
                else:
                    err_node = expr_2
                error_message = f"Only boolean values are permitted in '{operation}' calls."
            else:
                if expr_1_type != "N":
                    err_node = expr_1
                else:
                    err_node = expr_2
                error_message = f"Only numerical values are permitted in '{operation}' calls."
            self.__report_type_error(error_message, err_node)

    @staticmethod
    def __const(const_node: Node):
        const_node: Node = const_node.children[0]
        if const_node.value == "Number":
            return "N"
        if const_node.value == "ShortString":
            return "S"
        if const_node.value == "true" or const_node.value == "false":
            return "B"

    def __unop(self, unop_node: Node):
        operation: Node = unop_node.children[0]
        operation_name = operation.value
        parameter: Node = unop_node.children[2]
        if operation_name == "input":
            if parameter.value == "UserDefinedName":
                expected, is_arr = self.__get_data_type(parameter)
                if expected == "N":
                    return "N"
                else:
                    self.__report_type_error(f"Parameter for 'input' must be a number.", parameter)
        elif operation_name == "not":
            if parameter.value == "UserDefinedName":
                expected, is_arr = self.__get_data_type(parameter)
                if expected == "B":
                    return "B"
                else:
                    self.__report_type_error(f"Parameter for 'not' must be a bool.", parameter)
            elif parameter.value == "Expr":
                type_val = self.__eval_expr(parameter)
                if type_val == "B":
                    return "B"
                else:
                    self.__report_type_error(f"Parameter for 'not' must be a bool.", parameter)
            else:
                self.__report_type_error(f"Parameter for 'not' must be a bool.", parameter)

    def __evaluate_rhs(self, rhs: Node, expected_data_type: str):
        if rhs.value == "Expr":
            evaluated_value = self.__eval_expr(rhs)
            if evaluated_value == expected_data_type:
                return True
            self.__report_type_error(self.error_assign_messages[expected_data_type], rhs)

    def __report_type_error(self, message, er_node: Node = None):
        lines: list
        with open(self.source_file, "r") as f:
            lines = f.readlines()
        print(f"[-] Type error: {message}")
        try:
            if er_node is not None:
                if er_node.lineNumber == "":
                    trav = er_node
                    while er_node.lineNumber == "":
                        for child in trav.children:
                            er_node.lineNumber = child.lineNumber
                            if er_node.lineNumber != "":
                                break
                        trav = trav.children[0]
                if er_node.lineNumber != "":
                    print(f"\t\tLine {er_node.lineNumber}: {lines[int(er_node.lineNumber) - 1]}")
        except Exception as e:
            print(f"[-] Could not retrieve line number.\n{e}")
        exit(-1)

    def __correct_array_subscript_used(self, arr_udn: Node):
        immediate_right_child_position = arr_udn.parent.children.index(arr_udn) + 1
        immediate_right_child = arr_udn.parent.children[immediate_right_child_position]
        if immediate_right_child.value == "VAR":
            if len(immediate_right_child.children) > 1:
                if immediate_right_child.children[1].value == "VAR'":
                    subscript_expr = immediate_right_child.children[1].children[0]
                    if subscript_expr.value == "Const":
                        if subscript_expr.children[0].value == "Number" and int(
                                subscript_expr.children[0].subValue) >= 0:
                            return True
                        else:
                            self.__report_type_error("Expected Non-Negative number as subscript value", subscript_expr)
                    elif subscript_expr.value == "UserDefinedName":
                        udn_type, is_arr = self.__get_data_type(subscript_expr)
                        if udn_type == "N":
                            return True
                        else:
                            self.__report_type_error("Subscript variable must be of type number", subscript_expr)
        self.__report_type_error("Expected subscript variable or constant", arr_udn)

    def __get_data_type(self, udn_node: Node):
        # We can assume, at this point, that the variable has been declared properly.
        # That is, we can assume that the declaration will be in this scope, or one of its ancestors.
        ancestor_scopes = self.sem_table.get_ancestor_scopes(udn_node.scopeID)
        ancestor_scopes.remove("-")
        ancestor_scopes.sort()
        ancestor_scopes = list(reversed(ancestor_scopes))
        var_name = udn_node.subValue
        if self.__is_array(udn_node):
            var_name += "[]"
        decl_entry = self.sem_table.get_variable_with(var_name, udn_node.scopeID)
        is_arr: bool

        while decl_entry is None:
            decl_entry = self.sem_table.get_variable_with(var_name, ancestor_scopes.pop())

        if decl_entry["Type"] == "num":
            udn_node.data_type = "N"
        elif decl_entry["Type"] == "string":
            udn_node.data_type = "S"
        elif decl_entry["Type"] == "bool":
            udn_node.data_type = "B"

        is_arr = True if decl_entry["Token"].endswith("[]") else False
        return udn_node.data_type, is_arr

    def __var_type_check(self, lhs: Node, rhs: Node):
        expected_data_type, is_array = self.__get_data_type(lhs)
        if is_array:
            self.__correct_array_subscript_used(lhs)
        self.__evaluate_rhs(rhs, expected_data_type)
        return True

    def __stdio_type_check(self, rhs: Node):
        # RHS is always an expr.
        data_type_of_rhs = self.__eval_expr(rhs)
        if data_type_of_rhs in ["N", "S"]:
            rhs.data_type = data_type_of_rhs
            return True
        else:
            self.__report_type_error(f"Output function may only write Numbers and Strings to the screen.", rhs)

    def __branch_check(self, branch_node: Node):
        target_expr = branch_node.children[2]
        type_ = self.__eval_expr(target_expr)
        if type_ == "B":
            return True
        else:
            self.__report_type_error(f"If condition must be of type boolean", target_expr)

    def __loop_check(self, loop_node: Node):
        target_index: int
        if loop_node.children[0].value == "while":
            target_index = 2
        else:
            target_index = 6
        target_expr = loop_node.children[target_index]
        type_returned = self.__eval_expr(target_expr)
        if type_returned == "B":
            return True
        else:
            self.__report_type_error(f"Loop condition must be of type boolean", target_expr)

    def __identify_types(self, current: Node):
        if current.value == "Assign":
            LHS = current.children[0].children[0]
            RHS = current.children[2]
            if LHS.value == "UserDefinedName":
                self.__var_type_check(LHS, RHS)
            elif LHS.value == "output":
                self.__stdio_type_check(RHS)
        elif current.value == "Branch":
            self.__branch_check(current)
        elif current.value == "Loop":
            self.__loop_check(current)

        for child in current.children:
            self.__identify_types(child)

    def check(self):
        self.__identify_types(self.tree.root)
