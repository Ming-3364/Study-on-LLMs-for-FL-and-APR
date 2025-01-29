from tree_sitter import Language, Parser
import os
class JavaParser:
    def __init__(self):
        base_path = os.path.dirname(os.path.abspath(__file__))
        repo_path = os.path.join(base_path, 'tree-sitter-java')
        lib_path = os.path.join(base_path, 'build/my-languages.so')
        Language.build_library(
            lib_path,
            [repo_path]
        )
        self.language = Language(lib_path, 'java')
        self.parser = Parser()
        self.parser.set_language(self.language)

    def parse_code(self, code):
        return self.parser.parse(bytes(code, "utf8", errors='replace'))

    def find_method_by_line(self, code, line_number):
        tree = self.parse_code(code)
        return find_method_by_line(tree, code, line_number)

    def find_return_statements_by_method(self, code, method_name, method_line):
        tree = self.parse_code(code)
        return find_return_statements_with_line(tree, code, method_name, method_line)
    
    def find_method_by_name(self, code, method_name):
        tree = self.parse_code(code)
        return find_method_by_name(tree, code, method_name)
    
    def get_line_content(self, code, line_number):
        lines = code.split("\n")
        return lines[line_number - 1]
    
    def print_tree(self, code):
        tree = self.parse_code(code)
        print_tree(tree)


def find_method_by_line(tree, source_code, line_number):
    """
    Find the method content where a specific line belongs.
    """
    def find_method(node):
        if node.type == "method_declaration":
            start_line, _ = node.start_point
            end_line, _ = node.end_point

            if start_line <= line_number <= end_line:
                method_name_node = next((child for child in node.children if child.type == "identifier"), None)
                method_name = method_name_node.text.decode('utf8') if method_name_node else ""
                return {
                    "method_name": method_name,
                    "method_body": source_code[node.start_byte:node.end_byte],
                    "start_line": start_line + 1,
                    "end_line": end_line + 1
                }

        for child in node.children:
            result = find_method(child)
            if result:
                return result
        return None

    root_node = tree.root_node
    return find_method(root_node)


def find_return_statements_with_line(tree, source_code, method_name, method_line):
    # TODO: 区分同名方法
    # DONE
    """
    Find all return statements in a given method, along with their line numbers.
    """
    def find_method(node):
        if node.type == "method_declaration":
            for child in node.children:
                if child.type == "identifier" \
                    and child.text.decode('utf8') == method_name \
                    and node.start_point[0] == method_line - 1:
                    return node
        for child in node.children:
            result = find_method(child)
            if result:
                return result
        return None

    def find_returns(node):
        results = []
        if node.type == "return_statement":
            start_line, _ = node.start_point
            content = source_code[node.start_byte:node.end_byte]
            results.append({"content": content, "line": start_line + 1})
        for child in node.children:
            results.extend(find_returns(child))
        return results

    root_node = tree.root_node
    method_node = find_method(root_node)
    if method_node:
        return find_returns(method_node)
    return []

def find_method_by_name(tree, source_code, method_name):
    def find_method(node):
        # some test is variable_declarator
        if node.type == "method_declaration":
            method_name_node = next((child for child in node.children if child.type == "identifier"), None)
            if method_name_node and method_name_node.text.decode('utf8') == method_name:
                start_line, _ = node.start_point
                end_line, _ = node.end_point
                return {
                    "method_name": method_name,
                    "method_body": source_code[node.start_byte:node.end_byte],
                    "start_line": start_line + 1,
                    "end_line": end_line + 1
                }
        for child in node.children:
            result = find_method(child)
            if result:
                return result
        return None

    root_node = tree.root_node
    return find_method(root_node)

def print_tree(tree):
    def print_node(node, indent=0):
        print(' ' * indent, node)
        for child in node.children:
            print_node(child, indent + 2)
    print_node(tree.root_node)