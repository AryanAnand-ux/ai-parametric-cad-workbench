"""
Unit tests for the AST Security Sandbox (Week 4 deliverable & security upgrade).
Verifies that:
  - Whitelisted imports (build123d, math, typing) are allowed
  - Unwhitelisted imports (os, sys, subprocess) are rejected
  - Dangerous builtins (open, eval, exec, compile, input, __import__) are rejected
  - Dunder introspection (__subclasses__, __globals__) is rejected
"""
import pytest
from services.cad_runner import is_safe_script_id, validate_script_safety


def test_script_id_rejects_path_traversal():
    assert is_safe_script_id("part_1234abcd") is True
    assert is_safe_script_id("part_1234abcd_v1") is True
    assert is_safe_script_id("../outside") is False
    assert is_safe_script_id("part/../../outside") is False
    assert is_safe_script_id("part.name") is False

def test_ast_sandbox_safe_script():
    safe_code = """
PARAMS = {"length": 50.0}
from build123d import *
import math

with BuildPart() as p:
    Box(PARAMS["length"], 20, 10)
"""
    is_safe, msg = validate_script_safety(safe_code)
    assert is_safe is True
    assert msg == "OK"

def test_ast_sandbox_blocks_os_import():
    code = """
import os
os.system("echo compromised")
"""
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "Blocked import: 'os'" in msg

def test_ast_sandbox_blocks_subprocess_import_from():
    code = """
from subprocess import Popen
"""
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "Blocked import: 'from subprocess'" in msg

def test_ast_sandbox_blocks_open_builtin():
    code = """
PARAMS = {}
f = open("/etc/passwd", "r")
"""
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "Blocked builtin call: 'open()'" in msg

def test_ast_sandbox_blocks_eval_builtin():
    code = """
eval("__import__('os').system('ls')")
"""
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "eval()" in msg or "__import__" in msg

def test_ast_sandbox_blocks_input_builtin():
    # input() causes indefinite subprocess hang
    code = """
user_input = input("Enter value: ")
"""
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "Blocked builtin call: 'input()'" in msg

def test_ast_sandbox_blocks_dunder_globals_access():
    code = """
def hack(): pass
g = hack.__globals__
"""
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "Blocked sensitive attribute access: '__globals__'" in msg


def test_ast_sandbox_blocks_indirect_builtins_access():
    code = '''
sys.modules["builtins"].__dict__["__import__"]("os")
'''
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "Blocked" in msg


def test_ast_sandbox_blocks_getattr_alias_bypass():
    code = """
g = getattr
x = g(obj, "secret")
"""
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "Blocked" in msg


def test_ast_sandbox_blocks_string_concat_dunder_via_getattr():
    code = '''
x = getattr(obj, "__cla" + "ss__")
'''
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "Blocked" in msg


def test_ast_sandbox_blocks_dunder_class_chain():
    code = """
x = ().__class__.__base__
"""
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "Blocked" in msg


def test_ast_sandbox_blocks_vars_dir_hasattr():
    for snippet in ("x = vars(obj)", "x = dir(obj)", "x = hasattr(obj, 'a')"):
        is_safe, msg = validate_script_safety(snippet)
        assert is_safe is False, snippet
        assert "Blocked" in msg


def test_ast_sandbox_blocks_lambda_exfil():
    code = """
f = lambda x: x
"""
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "Blocked" in msg


def test_ast_sandbox_blocks_dunder_attr_on_innocent_object():
    code = """
x = box.__dict__
"""
    is_safe, msg = validate_script_safety(code)
    assert is_safe is False
    assert "Blocked" in msg
