from java_parser import JavaParser

file_path = "Test.java"
with open(file_path, "r", encoding="utf-8") as file:
    java_code = file.read()

analyzer = JavaParser()

line_number = 8
method_content = analyzer.find_method_by_line(java_code, line_number)
if method_content:
    print(f"Method content at line {line_number}:\n{method_content}")
else:
    print(f"No method found at line {line_number}.")

method_name = "add"

return_statements = analyzer.find_return_statements_by_method(java_code, method_name, 14)
print(f"Return Statements in '{method_name}':")
for ret in return_statements:
    print(f"Line {ret['line']}: {ret['content']}")