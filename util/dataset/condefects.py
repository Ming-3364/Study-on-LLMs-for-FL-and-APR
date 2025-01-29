import subprocess
import os
import shutil

def check_checkout_dir(checkout_dir):
    if not os.path.exists(checkout_dir) \
       or len(os.listdir(checkout_dir)) == 0:
        return True
    return False

def checkout_condefects(condefects_home, checkout_dir, time_from, time_to, language):
    if not check_checkout_dir(checkout_dir):
        assert False, "Checkout directory already exists and is not empty."
    command = f"(cd {condefects_home} &&" \
            + f" python3 ConDefects.py checkout -w {checkout_dir} -t {time_from} {time_to} -l {language})"
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    returncode = process.returncode
    stdout, stderr = process.communicate()
    assert(stdout.startswith("Checkout command called with") and "ConDefects checkout failed")
    return returncode, stdout, stderr

def checkout_condefects_task_program(condefects_home, checkout_dir, task_id, program_id):
    src_dir = os.path.join(condefects_home, "Code", task_id, "Java", program_id)
    dest_dir = checkout_dir
    assert os.path.exists(src_dir), f"Source directory {src_dir} does not exist."
    assert not os.path.exists(dest_dir), f"Destination directory {dest_dir} already exist."
    shutil.copytree(src_dir,dest_dir)
    return 0

def compile_condefects_task_program(condefects_home, checkout_dir, version):
    command = f"timeout 300 bash -c \"cd {checkout_dir} && cp {version}.java Main.java && javac Main.java\""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    returncode = process.returncode
    stdout, stderr = process.communicate()
    return returncode, stdout, stderr

def test_condefects_task_program(condefects_home, checkout_dir, task_id):
    class_file = os.path.join(checkout_dir, f"Main.class")
    assert os.path.exists(class_file), f"{class_file} don't exist."
    test_home = os.path.join(condefects_home, "Test")
    id1, id2 = task_id.split("_")
    task_test_home = os.path.join(test_home, id1, id2.upper())
    in_path = os.path.join(task_test_home, "in")
    out_path = os.path.join(task_test_home, "out")
    in_case_set = os.listdir(in_path)
    out_case_set = os.listdir(out_path)
    assert in_case_set == out_case_set, "Input and output case set should be the same."
    failed_tests = set()
    test_res_info_list = []
    for case in in_case_set:
        case_name = case.split('.')[0]
        in_case_file = os.path.join(in_path, case)
        out_case_file = os.path.join(out_path, case)
        with open(out_case_file, "r", encoding="utf-8") as file:
            output = file.read()

        command = f"timeout 300 bash -c \"cd {checkout_dir} && java -cp . Main < {in_case_file}\""
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        returncode = process.returncode
        stdout, stderr = process.communicate()
        test_res_info_list.append({
            'case_name': case_name,
            'returncode': returncode,
            'stdout': stdout,
            'stderr': stderr
        })
        if stdout != output:
            failed_tests.add(case_name)
    return failed_tests, test_res_info_list



def get_condefects_tasks(checkout_dir):
    return os.listdir(checkout_dir)

def get_java_programs_in_task(checkout_dir, task_id):
    task_java_dir = os.path.join(checkout_dir, task_id, "Java")
    program_list = os.listdir(task_java_dir)
    return program_list

def get_condefects_task_program_id(task_id, program_id):
    return f"{task_id}-{program_id}"

def get_java_program_path(checkout_dir, task_id, program_id):
    java_program_path = os.path.join(checkout_dir, task_id, "Java", program_id)
    return java_program_path

def get_program_content(file_path):
    with open(file_path, "r", encoding="utf-8", errors='replace') as file:
        code = file.read()
        return code

def get_program_correct_version(program_path):
    file_path = os.path.join(program_path, "correctVersion.java")
    return get_program_content(file_path)

def get_program_faulty_version(program_path):
    file_path = os.path.join(program_path, "faultyVersion.java")
    return get_program_content(file_path)

def get_program_fault_location(program_path):
    file_path = os.path.join(program_path, "faultLocation.txt")
    with open(file_path, "r", encoding="utf-8") as file:
        lines = file.readlines()
        assert len(lines) == 1, "Fault location file should contain only one line."
        location = int(lines[0].strip())
        return location

test_in_out = \
"""

"""
def get_test_method(name, input, output):
    test_method = "\n   @Test\n" \
         + f"   public void test_{name}() {{ \n" \
         + f"       String simulatedInput = \"{input}\";\n"\
         +  "       ByteArrayInputStream inputStream = new ByteArrayInputStream(simulatedInput.getBytes());\n" \
         +  "       System.setIn(inputStream);\n" \
         +  "       ByteArrayOutputStream outputStream = new ByteArrayOutputStream();\n" \
         +  "       System.setOut(new PrintStream(outputStream));\n" \
         +  "       Main.main(null);\n" \
         + f"       String expectedOutput = \"{output}\";\n" \
         +  "       assertEquals(expectedOutput, outputStream.toString());\n" \
         +  "   }\n"
    return test_method

def get_test_class(test_methods):
    test_class =  "import org.junit.Test;\n" \
               +  "import static org.junit.Assert.assertEquals;\n" \
               +  "import java.io.ByteArrayInputStream;\n" \
               +  "import java.io.ByteArrayOutputStream;\n" \
               +  "import java.io.PrintStream;\n" \
               +  "public class MainTest {\n" \
               + f"{test_methods}" \
               +  "}\n"
    return test_class

def generate_test_class(condefects_home, task_id, java_program_path):
    test_home = os.path.join(condefects_home, "Test")
    id1, id2 = task_id.split("_")
    task_test_home = os.path.join(test_home, id1, id2.upper())
    in_path = os.path.join(task_test_home, "in")
    out_path = os.path.join(task_test_home, "out")
    in_case_set = os.listdir(in_path)
    out_case_set = os.listdir(out_path)
    assert in_case_set == out_case_set, "Input and output case set should be the same."
    test_methods = ""
    for case in in_case_set:
        case_name = case.split('.')[0]
        in_case_file = os.path.join(in_path, case)
        out_case_file = os.path.join(out_path, case)
        with open(in_case_file, "r", encoding="utf-8") as file:
            # input = repr(file.read())
            input = file.read().replace('\n', '\\n')
        with open(out_case_file, "r", encoding="utf-8") as file:
            # output = repr(file.read())
            output = file.read().replace('\n', '\\n')
        test_methods += get_test_method(case_name, input, output)
    test_class = get_test_class(test_methods)
    test_class_path = os.path.join(java_program_path, "MainTest.java")
    with open(test_class_path, 'w') as file:
        file.write(test_class)
    return test_class_path

def compile_condefects_main_and_maintest(program_dir, classpath):
    command = f"timeout 300 bash -c \"cd {program_dir} && javac -cp {classpath} Main.java MainTest.java)\""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    returncode = process.returncode
    stdout, stderr = process.communicate()
    return returncode, stdout, stderr

def run_condefects_maintest(program_dir, classpath):
    command = f"timeout 300 bash -c \"cd {program_dir} && java -cp {classpath} org.junit.runner.JUnitCore MainTest\""
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    returncode = process.returncode
    stdout, stderr = process.communicate()
    return returncode, stdout, stderr

# condefects_home = "/data/cmd/Ming/LLM_Based-Mutation/tools/mutant/ConDefects"
# condefects_checkout_dir = "/data/cmd/Ming/LLM_Based-Mutation/tools/mutant/tmp-condefects"
# time_from = "2024-03-01"
# time_to = "2024-06-30"
def test_condefects_checkout():
    returncode, stdout, stderr = checkout_condefects(condefects_home, condefects_checkout_dir, time_from, time_to, "Java")

# test_condefects_checkout()

# tasks = get_condefects_tasks(condefects_checkout_dir)
# print(tasks)
# program_list = get_java_programs_in_task(condefects_checkout_dir, tasks[0])
# print(program_list)
# task_id = tasks[0]
# program_id = program_list[0]
# code = get_program_correct_version(os.path.join(condefects_checkout_dir, task_id, "Java", program_id))
# print(code)
# java_program_path = os.path.join(condefects_checkout_dir, task_id, "Java", program_id)

def test_all_fault_location():
    tasks = get_condefects_tasks(condefects_checkout_dir)
    for task_id in tasks:
        program_list = get_java_programs_in_task(condefects_checkout_dir, task_id)
        for program_id in program_list:
            java_program_path = os.path.join(condefects_checkout_dir, task_id, "Java", program_id)
            fault_location = get_program_fault_location(java_program_path)
            print(task_id, program_id, fault_location, java_program_path)
# test_all_fault_location()

# print(generate_test_class(condefects_home, task_id, java_program_path))