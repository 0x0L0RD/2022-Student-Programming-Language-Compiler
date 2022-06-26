# Author:           0xL0RD

class SemanticTable:
    Table = {
        "Variables": [],
        "Procedures": [],
        "Scopes": [],
    }

    def add_variable_entry(self, user_defined_name: str, scope_id: str, variable_id: str, semantic_id: str,
                           var_type: str, size="TBA"):
        if not self.__variable_contains(user_defined_name, scope_id):
            self.Table["Variables"].append({
                "Token": user_defined_name,
                "VariableID": variable_id,
                "Type": var_type,
                "ScopeID": scope_id,
                "SemanticID": semantic_id,
                "Size": size
            })

    def add_procedure_entry(self, user_defined_name: str, scope_id: str, proc_id: str, semantic_id: str):
        if not self.__procedure_contains(user_defined_name, scope_id):
            self.Table["Procedures"].append({
                "Token": user_defined_name,
                "ProcID": proc_id,
                "ScopeID": scope_id,
                "SemanticID": semantic_id
            })

    def add_scope(self, token: str, token_id: str, scope_id: str, parent_s: str):
        self.Table["Scopes"].append({
            "Token": token,
            "TokenID": token_id,
            "ScopeID": scope_id,
            "ParentScopeID": parent_s
        })

    def get_ancestor_scopes(self, scope_id: str):
        target_scope_id = scope_id
        ancestor_scopes = [target_scope_id]
        while target_scope_id != "-":
            for scope in self.Table["Scopes"]:
                if scope["ScopeID"] == target_scope_id:
                    target_scope_id = scope["ParentScopeID"]
                    ancestor_scopes.append(target_scope_id)
                    break
        return ancestor_scopes

    def get_nearest_ancestor_scope(self, scope_id: str):
        scopes = self.get_ancestor_scopes(scope_id)
        scopes.remove("-")
        int_scopes = [int(scope) for scope in scopes]
        int_scopes.sort()
        return str(int_scopes.pop())

    def get_successor_scopes(self, scope_id: str):
        target_scope_id = scope_id
        successor_scopes = [target_scope_id]
        child_scopes = []
        target_scope = scope_id
        while target_scope is not None:
            for scope in self.Table["Scopes"]:
                if scope["ParentScopeID"] == target_scope_id and scope["ScopeID"] not in successor_scopes:
                    successor_scopes.append(scope["ScopeID"])
                    child_scopes.append(scope["ScopeID"])
                    target_scope_id = scope["ParentScopeID"]
            if len(child_scopes) < 1:
                target_scope = None
            else:
                target_scope = child_scopes[0]
                child_scopes = child_scopes[1::]
        return successor_scopes

    def get_callable_procs_from(self, scope_id: str):
        callable_funcs = []
        parent_scope_id = None

        for scope in self.Table["Scopes"]:
            if scope["Token"] not in callable_funcs:
                if scope["ParentScopeID"] == scope_id or scope["ScopeID"] == scope_id:
                    callable_funcs.append(scope["Token"])
                elif scope["ScopeID"] == scope_id:
                    callable_funcs.append(scope["Token"])
                    parent_scope_id = scope["ParentScopeID"]

        if parent_scope_id != "0":
            for scope in self.Table["Scopes"]:
                if scope["ScopeID"] == parent_scope_id:
                    callable_funcs.append(scope["Token"])

        return callable_funcs

    def __procedure_contains(self, user_defined_name: str, scope_id: str):
        for proc in self.Table["Procedures"]:
            if proc["Token"] == user_defined_name and proc["ScopeID"] == scope_id:
                return True
        return False

    def __variable_contains(self, user_defined_name: str, scope_id: str):
        for var in self.Table["Variables"]:
            if var["Token"] == user_defined_name and var["ScopeID"] == scope_id:
                return True
        return False

    def get_variable_with(self, user_defined_name: str, scope_id: str) -> dict:
        if not self.__variable_contains(user_defined_name, scope_id):
            return None
        else:
            for entry in self.Table["Variables"]:
                if entry["Token"] == user_defined_name and entry["ScopeID"] == scope_id:
                    return entry

    def get_variable_by_name(self, udn: str):
        for entry in self.Table["Variables"]:
            if entry["Token"] == udn:
                return entry
        return None

    def get_nearest_variable(self, udn: str, scope_id: str):
        lowest_difference = None
        nearest = None
        for entry in self.Table["Variables"]:
            difference = abs(int(entry["ScopeID"]) - int(scope_id))
            if entry["Token"] == udn:
                if lowest_difference is not None:
                    if lowest_difference > difference:
                        lowest_difference = difference
                        nearest = entry
                else:
                    lowest_difference = difference
                    nearest = entry
        return nearest

    def get_procedure_by_name(self, udn: str):
        for entry in self.Table["Procedures"]:
            if entry["Token"] == udn:
                return entry
        return None

    def get_nearest_procedure(self, udn: str, scope_id: str):
        lowest_difference = None
        nearest = None
        for entry in self.Table["Procedures"]:
            difference = abs(int(entry["ScopeID"]) - int(scope_id))
            if entry["Token"] == udn:
                if lowest_difference is not None:
                    if lowest_difference > difference:
                        lowest_difference = difference
                        nearest = entry
                else:
                    lowest_difference = difference
                    nearest = entry
        return nearest

    def get_procedure_with(self, user_defined_name: str, scope_id: str) -> dict:
        if not self.__procedure_contains(user_defined_name, scope_id):
            return None
        else:
            for entry in self.Table["Procedures"]:
                if entry["Token"] == user_defined_name and entry["ScopeID"] == scope_id:
                    return entry

    def get_valid_call_scopes(self, proc_scope_id: str):
        valid_call_scopes = [proc_scope_id]
        for scope in self.Table["Scopes"]:
            if scope["ScopeID"] not in valid_call_scopes and scope["ParentScopeID"] == proc_scope_id:
                valid_call_scopes.append(scope["ScopeID"])
            elif scope["ScopeID"] == proc_scope_id and scope["ParentScopeID"] not in valid_call_scopes:
                valid_call_scopes.append(scope["ParentScopeID"])

        return valid_call_scopes

    def print_table(self):
        print("Procedures:")
        print(f"Token\t\t\tProcedure ID\t\tScope ID\tSemantic ID")
        print("_" * 100)
        for proc in self.Table["Procedures"]:
            padding = ""
            if len(proc["Token"]) < 8:
                padding = " " * (8 - len(proc['Token']))
            print(f"{proc['Token'] + padding}\t\t{proc['ProcID']}\t\t\t\t\t{proc['ScopeID']}\t\t\t{proc['SemanticID']}")
        print("_" * 100)
        print("\nVariables:")
        print(f"Token\t\t\t\tVariable ID\t\t\tType\t\t\tScope ID\tSemantic ID")
        print("_" * 100)
        for var in self.Table["Variables"]:
            padding = ""
            typ_padding = ""
            if len(var["Token"]) < 10:
                padding = " " * (10 - len(var['Token']))
            if len(var["Type"]) < 8:
                typ_padding = " " * (8 - len(var["Type"]))
            print(
                f"{var['Token'] + padding}\t\t\t{var['VariableID']}\t\t\t\t\t{var['Type'] + typ_padding}\t\t{var['ScopeID']}\t\t\t{var['SemanticID']}")
        print("_" * 100)
        print("\nScopes:")
        print(f"Token\t\t\t\t\tToken ID\t\t\tScope ID\tParent Scope ID")
        print("_" * 100)
        for sco in self.Table["Scopes"]:
            padding = ""
            if len(sco["Token"]) < 12:
                padding = " " * (12 - len(sco['Token']))
            print(
                f"{sco['Token'] + padding}\t\t\t{sco['TokenID']}\t\t\t\t\t{sco['ScopeID']}\t\t\t{sco['ParentScopeID']}")
        print("_" * 100)
        print("=" * 100)
