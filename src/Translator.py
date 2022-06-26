# Author:           0xL0RD

from Parser import SyntaxTree, Node
from SemanticTable import SemanticTable


class CodeGenerator:
    s_tree: SyntaxTree
    s_table: SemanticTable
    id_table: dict
    final_output: list
    main_entry: str
    symbolic_label_table: dict = {
        "Procedures": [],
        "Variables": []
    }
    var_naming_cipher_one = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    var_naming_cipher_two = "0123456789"
    first_char_pos = 0
    second_char_pos = 0
    num_char_pos = 0

    FALSE = "0"
    TRUE = "-1"

    def __init__(self, syn_tree: SyntaxTree, sem_table: SemanticTable, id_dict: dict):
        self.s_tree = syn_tree
        self.s_table = sem_table
        self.id_table = id_dict
        self.__create_symbolic_label_table()

    def __output_file(self, file_n: str):
        with open(file_n, "w+") as f:
            for lines in self.final_output:
                f.write(lines + "\n")

    def __get_label(self):
        var_name = self.var_naming_cipher_one[self.first_char_pos] + self.var_naming_cipher_one[self.second_char_pos]
        var_name += self.var_naming_cipher_two[self.num_char_pos]
        self.num_char_pos += 1

        if self.num_char_pos == 9:
            self.second_char_pos += 1
            if self.second_char_pos == 25:
                self.first_char_pos += 1
                self.second_char_pos = 0
            self.num_char_pos = 0

        if var_name in ["ZZ98", "ZZ99"]:
            raise Exception("Too many variables to compile.")

        return var_name

    def __create_symbolic_label_table(self):
        # Functions.
        for proc in self.s_table.Table["Procedures"]:
            self.symbolic_label_table["Procedures"].append({
                "Label": self.__get_label(),
                "Line": "",
                "Name": proc["Token"],
                "ScopeID": proc["ScopeID"],  # Remember, this scopeID represents the scope in which it is defined.
                "ProcID": proc["ProcID"]
            })

        # Variables.
        for var in self.s_table.Table["Variables"]:
            self.symbolic_label_table["Variables"].append({
                "Label": self.__get_label() if var["Type"] != "string" else self.__get_label() + "$",
                "Type": var["Type"],
                "Name": var["Token"],
                "ScopeID": var["ScopeID"],
                "Size": var["Size"]
            })

    def __user_defined_name(self, n: Node, scope_id):
        label = self.__get_var_by_name_and_scope_id(n.subValue, scope_id)
        if not label:
            label = self.__get_var_by_name_and_scope_id(n.subValue + "[]", scope_id)
            parent = n.parent
            next = parent.children.index(n) + 1
            var_sibling = parent.children[next]
            if len(var_sibling.children) > 1:
                subscript = self.__subscript(var_sibling.children[1], scope_id)
                label += f"({subscript})"
        return label

    def __const(self, n: Node):
        value = n.children[0].value
        if value == "true":
            value = self.TRUE
        elif value == "false":
            value = self.FALSE
        else:
            value = n.children[0].subValue

        return value

    def __un_op(self, n: Node, scope_id: str, instr_list: list, is_assignment: bool = False, var_label=""):
        op = n.children[0].value
        expr_node = n.children[2]

        if op == "input":
            containing_var = self.__user_defined_name(expr_node, scope_id)
            instr_list.append(f"INPUT {containing_var}")
            if is_assignment:
                instr_list.append(f"LET {var_label} = {containing_var}")
            return containing_var

        expr_one_label = self.__expr(expr_node, scope_id, instr_list)

        if not is_assignment:
            var_label = self.__get_label()

        if op == "not":
            instr_list.append(f"IF {expr_one_label} THEN GOTO +3")

            if var_label == "PRINT":
                instr_list.append(f"{var_label} {self.TRUE}")
            else:
                instr_list.append(f"LET {var_label} = {self.TRUE}")

            instr_list.append(f"GOTO +2")

            if var_label == "PRINT":
                instr_list.append(f"{var_label} {self.FALSE}")
            else:
                instr_list.append(f"LET {var_label} = {self.FALSE}")

        if not is_assignment:
            return var_label

    def __bin_op(self, n: Node, scope_id: str, instr_list: list, is_assignment: bool = False, var_label=""):
        op = n.children[0].value
        expr_one = n.children[2]
        expr_two = n.children[4]

        expr_one_label = self.__expr(expr_one, scope_id, instr_list)
        expr_two_label = self.__expr(expr_two, scope_id, instr_list)

        if not is_assignment and var_label == "":
            var_label = self.__get_label()

        if op == "and":
            instr_list.append(f"IF {expr_one_label} THEN GOTO +2")

            instr_list.append(f"GOTO +2")

            if var_label == "PRINT":
                instr_list.append(f"{var_label} {self.TRUE}")
            else:
                instr_list.append(f"IF {expr_two_label} THEN GOTO +3")

            if var_label == "PRINT":
                instr_list.append(f"{var_label} {self.FALSE}")
            else:
                instr_list.append(f"LET {var_label} = {self.FALSE}")

            instr_list.append(f"GOTO +2")

            instr_list.append(f"LET {var_label} = {self.TRUE}")

        elif op == "or":
            instr_list.append(f"IF {expr_one_label} THEN GOTO +4")
            instr_list.append(f"IF {expr_two_label} THEN GOTO +3")

            if var_label == "PRINT":
                instr_list.append(f"{var_label} {self.FALSE}")
            else:
                instr_list.append(f"LET {var_label} = {self.FALSE}")

            instr_list.append(f"GOTO +2")

            if var_label == "PRINT":
                instr_list.append(f"{var_label} {self.TRUE}")
            else:
                instr_list.append(f"LET {var_label} = {self.TRUE}")

        elif op == "larger":
            instr_list.append(f"IF {expr_one_label} > {expr_two_label} THEN GOTO +3")

            if var_label == "PRINT":
                instr_list.append(f"{var_label} {self.FALSE}")
            else:
                instr_list.append(f"LET {var_label} = {self.FALSE}")

            instr_list.append(f"GOTO +2")

            if var_label == "PRINT":
                instr_list.append(f"{var_label} {self.TRUE}")
            else:
                instr_list.append(f"LET {var_label} = {self.TRUE}")

        elif op == "eq":
            instr_list.append(f"IF {expr_one_label} = {expr_two_label} THEN GOTO +3")

            if var_label == "PRINT":
                instr_list.append(f"{var_label} {self.FALSE}")
            else:
                instr_list.append(f"LET {var_label} = {self.FALSE}")

            instr_list.append(f"GOTO +2")

            if var_label == "PRINT":
                instr_list.append(f"{var_label} {self.TRUE}")
            else:
                instr_list.append(f"LET {var_label} = {self.TRUE}")

        elif op == "mult":
            if var_label == "PRINT":
                instr_list.append(f"{var_label} {expr_one_label} * {expr_two_label}")
            else:
                instr_list.append(f"LET {var_label} = {expr_one_label} * {expr_two_label}")


        elif op == "sub":
            if var_label == "PRINT":
                instr_list.append(f"{var_label} {expr_one_label} - {expr_two_label}")
            else:
                instr_list.append(f"LET {var_label} = {expr_one_label} - {expr_two_label}")


        elif op == "add":
            if var_label == "PRINT":
                instr_list.append(f"{var_label} {expr_one_label} + {expr_two_label}")
            else:
                instr_list.append(f"LET {var_label} = {expr_one_label} + {expr_two_label}")

        if not is_assignment:
            return var_label

    def __subscript(self, n: Node, scope_id: str):
        target_node = n.children[0]
        if target_node.value == "Const":
            return self.__const(target_node)
        elif target_node.value == "UserDefinedName":
            return self.__user_defined_name(target_node, scope_id)

    def __expr(self, n: Node, scope_id: str, instr_list: list, var_label: str = "", is_assign: bool = False):
        body = n.children[0]
        if body.value == "Const":
            return self.__const(body)
        elif body.value == "UserDefinedName":
            return self.__user_defined_name(body, scope_id)
        elif body.value == "BinOp":
            return self.__bin_op(body, scope_id, instr_list, is_assign, var_label)
        elif body.value == "UnOp":
            return self.__un_op(body, scope_id, instr_list, is_assign, var_label)

    def __lhs(self, n: Node, scope_id: str):
        return_value = ""

        if n.children[0].value == "UserDefinedName":
            target_var = n.children[0].subValue
        else:
            target_var = n.children[0].value

        if target_var != "output":
            label = self.__get_var_by_name_and_scope_id(n.children[0].subValue, scope_id)
            if not label:
                label = self.__get_var_by_name_and_scope_id(n.children[0].subValue + "[]", scope_id)
        else:
            return "PRINT"

        return_value += f"{label}"

        # We're dealing with an array.
        if len(n.children[1].children) > 1 and label:
            index = self.__subscript(n.children[1].children[1], scope_id)
            return_value += f"({index})"

        return return_value

    def __get_proc_by_label(self, proc_label: str):
        for proc in self.symbolic_label_table["Procedures"]:
            if proc["Label"] == proc_label:
                return proc["Line"]

    def __update_proc_line_by_label(self, proc_name: str, line_num: str):
        for proc in self.symbolic_label_table["Procedures"]:
            if proc["Label"] == proc_name:
                proc["Line"] = line_num

    def __get_proc_by_name_and_scope_id(self, proc_name: str, scope_id: str):
        for proc in self.symbolic_label_table["Procedures"]:
            # At this point, scope analysis would have caught out any errors.
            if proc["Name"] == proc_name and proc["ScopeID"] == \
                    scope_id or proc["Name"] == proc_name and proc["ScopeID"] in self.s_table.get_successor_scopes(
                scope_id):
                return proc["Label"]

    def __get_var_by_name_and_scope_id(self, var_name: str, scope_id: str):
        for var in self.symbolic_label_table["Variables"]:
            # At this point, scope analysis would have caught out any errors.
            if var["Name"] == var_name and var["ScopeID"] == \
                    scope_id or var["Name"] == var_name and var["ScopeID"] in self.s_table.get_ancestor_scopes(
                scope_id):
                return var["Label"]

    def __assign(self, n: Node, scope_id, inst_list: list):
        lhs_node = n.children[0]
        rhs_node = n.children[2]
        lhs = self.__lhs(lhs_node, scope_id)
        rhs = self.__expr(rhs_node, scope_id, inst_list, lhs, True)

        if rhs:
            if lhs == "PRINT":
                inst_list.append(f"{lhs} {rhs}")
            else:
                inst_list.append(f"LET {lhs} = {rhs}")

    def __pcall(self, n: Node, scope_id, instr_list: list):
        target_func = n.children[1].subValue
        instruction = f"GO SUB {self.__get_proc_by_name_and_scope_id(target_func, scope_id)}"
        instr_list.append(instruction)

    def __loop(self, n: Node, scope_id, instr_list: list):
        is_while_loop = True if n.children[0].value == "while" else False
        if is_while_loop:
            evaluation_node = n.children[2]
            algorithm_node = n.children[6]
            beginning_of_loop = len(instr_list)
            eval_expr = self.__expr(evaluation_node, scope_id, instr_list)
            instr_list.append(f"IF {eval_expr} THEN GOTO +2")
            instr_list.append(f"GOTO PENDING...")
            post_while_loop_indicator_line = len(instr_list) - 1
            self.__algorithm(algorithm_node, scope_id, instr_list)
            instr_list.append(f"GOTO -{((len(instr_list)) - beginning_of_loop)}")
            instr_list[post_while_loop_indicator_line] = f"GOTO +{(len(instr_list)) - post_while_loop_indicator_line}"
        else:
            algorithm_node = n.children[2]
            evaluation_node = n.children[6]
            loop_beginning = len(instr_list)
            self.__algorithm(algorithm_node, scope_id, instr_list)
            eval_expr = self.__expr(evaluation_node, scope_id, instr_list)
            instr_list.append(f"IF {eval_expr} THEN GOTO +2")
            instr_list.append(f"GOTO -{(len(instr_list)) - loop_beginning}")

    def __branch(self, n: Node, scope_id, instr_list: list):
        eval_exp_node = n.children[2]
        algorithm_node = n.children[6]
        alternate_node = n.children[8]
        eval_exp_symbol = self.__expr(eval_exp_node, scope_id, instr_list)
        instr_list.append(f"IF {eval_exp_symbol} THEN GOTO +2")
        instr_list.append(f"GOTO PENDING...")
        else_or_untruthy_branch_position = len(instr_list) - 1
        self.__algorithm(algorithm_node, scope_id, instr_list)

        instr_list[else_or_untruthy_branch_position] = \
            f"GOTO +{(len(instr_list)) - else_or_untruthy_branch_position}"

        if len(alternate_node.children) > 1:
            instr_list.append("GOTO PENDING...")
            instr_list[else_or_untruthy_branch_position] = \
                f"GOTO +{(len(instr_list)) - else_or_untruthy_branch_position}"
            escape_else_pos = len(instr_list) - 1
            self.__algorithm(alternate_node.children[2], scope_id, instr_list)
            instr_list[escape_else_pos] = \
                f"GOTO +{(len(instr_list)) - escape_else_pos}"

    def __initialize_arrays(self, arr: list):
        lines_taken = 0
        for entry in self.symbolic_label_table["Variables"]:
            if "[]" in entry["Name"]:
                arr.append(f"{lines_taken} DIM {entry['Label']}({entry['Size']})")
                lines_taken += 1

        return lines_taken

    def __instr(self, n: Node, scope_id, inst_list: list):
        focus = n.children[0]
        if focus.value == "PCall":
            self.__pcall(focus, scope_id, inst_list)
        elif focus.value == "Loop":
            self.__loop(focus, scope_id, inst_list)
        elif focus.value == "Branch":
            self.__branch(focus, scope_id, inst_list)
        elif focus.value == "Assign":
            self.__assign(focus, scope_id, inst_list)

    def __algorithm(self, n: Node, scope_id, inst_list: list):
        for child in n.children:
            if child.value == "Instr":
                self.__instr(child, scope_id, inst_list)
            elif child.value == "Algorithm":
                self.__algorithm(child, scope_id, inst_list)

    def __recursive_func_build(self, current: Node, scope_id, proc_id, inst_list: list):
        if current.ID == proc_id:
            parent = current.parent
            index_of_this_node = parent.children.index(current)
            for child in parent.children:
                if parent.children.index(child) > index_of_this_node:
                    if child.value == "Algorithm":
                        self.__algorithm(child, scope_id, inst_list)
                    elif child.value == "halt":
                        inst_list.append("STOP")
                    elif child.value == "CloseBraceCurly":
                        return
        else:
            for child in current.children:
                self.__recursive_func_build(child, scope_id, proc_id, inst_list)

    def __bake_absolute_addresses(self, all_procs: dict):
        final_list = []
        line = self.__initialize_arrays(final_list)
        start = line
        final_list.append("GOTO START")
        line += 1
        self.final_output = []
        for proc_name in all_procs.keys():
            self.__update_proc_line_by_label(proc_name, str(line))
            for code in all_procs[proc_name]:
                if "GOTO +" in code or "GOTO -":
                    split_inst = code.split(" ")
                    for op in split_inst:
                        if "+" in op and split_inst[split_inst.index(op) - 1] == "GOTO":
                            replacement = line + int(op[op.find("+") + 1::].strip())
                            split_inst[split_inst.index(op)] = str(replacement)
                        if "-" in op and split_inst[split_inst.index(op) - 1] == "GOTO":
                            replacement = line - int(op[op.find("-") + 1::].strip())
                            split_inst[split_inst.index(op)] = str(replacement)

                    code = " ".join(split_inst)

                self.final_output.append(f"{line} {code}")
                line += 1

        for line in self.final_output:
            if "GO SUB" in line:
                split_line = line.split(" ")
                for element in split_line:
                    if element in all_procs.keys():
                        replacement = self.__get_proc_by_label(element)
                        split_line[split_line.index(element)] = replacement
                        new_line = " ".join(split_line)
                        self.final_output[self.final_output.index(line)] = new_line

        final_list[start] = f"{start} GOTO {self.__get_proc_by_label(self.main_entry)}"
        final_list.extend(self.final_output)
        self.final_output = final_list

    def translate_functions(self, file_name: str):
        functions = {}
        instruction_list = []
        for entry in self.symbolic_label_table["Procedures"]:
            self.__recursive_func_build(self.s_tree.root, entry["ScopeID"], entry["ProcID"], instruction_list)
            if instruction_list[-1] != "STOP":
                instruction_list.append("RETURN")

            if entry["Name"] == "main":
                self.main_entry = entry["Label"]

            functions[entry["Label"]] = instruction_list.copy()
            instruction_list = []
        self.__bake_absolute_addresses(functions)
        self.__output_file(file_name)

    def print_symbolic_label_table(self):
        # Functions.
        print(f"Procedures\n{'_' * 50}\nLabel\t\tLine\t\tScope ID\tProcID")
        for proc in self.symbolic_label_table["Procedures"]:
            print(f"{proc['Label']}\t\t{proc['Line']}\t\t\t\t{proc['ScopeID']}\t\t\t{proc['ProcID']}")

        # Variables.
        print(f"\nVariables\n{'_' * 50}\nLabel\t\tScope ID")
        for var in self.symbolic_label_table["Variables"]:
            print(f"{var['Label']}\t\t\t\t{var['ScopeID']}")

    def print_basic_code(self):
        for code in self.final_output:
            print(code)
