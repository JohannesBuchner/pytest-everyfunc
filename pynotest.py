import ast
import io
import os
import subprocess
import sys
import tomllib
from typing import List, Tuple


def parse_missed_lines(missing_str: str) -> List[int]:
    """Parse lines missing in coverage.

    Parameters
    ----------
    missing_str: str
        '<num>-<num>' or '<num>'

    Returns
    -------
    lines: list
        integers in the range
    """
    lines = []
    for part in missing_str.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))
            lines.extend(range(start, end + 1))
        else:
            lines.append(int(part))
    return lines


def parse_coverage_report(file) -> dict:
    """Parse output of "coverage report -m"

    Parameters
    ----------
    file: object
        input stream

    Returns
    -------
    missed_by_file: dict
        list of lines for each file
    """
    missed_by_file = {}
    file.readline()
    sepline = file.readline()
    assert sepline.startswith("----")
    for line in file:
        if line.startswith("----") or line.strip() == "":
            break
        parts = line.strip().split(maxsplit=4)
        if len(parts) > 4:
            filename = parts[0]
            missing = parts[4].strip()
            missed_by_file[filename] = set(parse_missed_lines(missing))
    return missed_by_file


def get_functions_from_file(filepath: str) -> List[Tuple[str, int, int]]:
    """Get list of python functions.

    Parameters
    ----------
    filepath: str
        path to python script

    Returns
    -------
    functions: list
        list of functions and their lines.s
    """
    with open(filepath, "r") as f:
        source = f.read()

    tree = ast.parse(source)
    functions = []

    class FuncVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            """Visit a function node.

            Parameters
            ----------
            node: object
                ast node.
            """
            funcloc = node.lineno
            code_lines = []
            for child in node.body:
                # Skip docstring (which is always the first expr if present)
                if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant):
                    continue
                start = child.lineno
                end = getattr(child, 'end_lineno', start)
                code_lines.extend(range(start, end + 1))
            functions.append((node.name, funcloc, code_lines))
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node):
            """Visit a async function.

            Parameters
            ----------
            node: object
                ast node.
            """
            self.visit_FunctionDef(node)

    FuncVisitor().visit(tree)
    return functions


def find_never_called_functions(file = sys.stdin, source_root: str = "."):
    """Find functions not covered by tests.

    Parameters
    ----------
    file: object
        input stream
    source_root: str
        path where files are.

    Returns
    -------
    never_called: list
        list of filename, function name and location tuples.
    """
    missed_by_file = parse_coverage_report(file)
    never_called = []

    for rel_path, missed_lines in missed_by_file.items():
        filepath = os.path.join(source_root, rel_path)
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue

        functions = get_functions_from_file(filepath)
        for func_name, funcloc, func_lines in functions:
            if all(line in missed_lines for line in func_lines):
                never_called.append((rel_path, func_name, funcloc))

    return never_called

def read_package_name_from_pyproject() -> str:
    """Get the python package name.

    Returns
    -------
    package_name: str
        name of the python package
    """
    with open("pyproject.toml", "rb") as f:
        data = tomllib.load(f)
    return data["project"]["name"].replace("-", "_")

def run_coverage_and_capture(package: str) -> str:
    """Run coverage and pytest programmatically, return coverage report output.

    Parameters
    ----------
    package: str
        name of the python package

    Returns
    -------
    stream: object
        input stream
    """
    subprocess.run(["python3", "-m", "coverage", "run", "-m", "pytest"], check=True)
    result = subprocess.run(
        ["python3", "-m", "coverage", "report", f"--include={package}/*", "-m"],
        check=True,
        stdout=subprocess.PIPE,
        text=True
    )
    return result.stdout

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] != "-":
        package = read_package_name_from_pyproject()
        report = run_coverage_and_capture(package)
        from io import StringIO
        results = find_never_called_functions(StringIO(report))
    else:
        results = find_never_called_functions(sys.stdin)
    for filename, name, funcloc in results:
        sys.stderr.write(f"{filename}:{funcloc}: untested: {name}\n")
    if len(results) > 0:
        sys.stderr.write(f"Error: untested functions found!\n")
        sys.exit(1)
