import os
import builtins
from pyfsmanager.cli import PyFSCmd


def test_touch_and_rm(tmp_path, monkeypatch):
    cwd = tmp_path
    monkeypatch.chdir(cwd)

    cli = PyFSCmd()
    # touch a file
    cli.do_touch('testfile.txt')
    assert (cwd / 'testfile.txt').exists()

    # remove the file with confirmation 's'
    monkeypatch.setattr(builtins, 'input', lambda prompt='': 's')
    cli.do_rm('testfile.txt')
    assert not (cwd / 'testfile.txt').exists()


def test_mkdir_cp_mv(tmp_path, monkeypatch):
    cwd = tmp_path
    monkeypatch.chdir(cwd)

    cli = PyFSCmd()

    # mkdir
    cli.do_mkdir('dirA')
    assert (cwd / 'dirA').is_dir()

    # create a source file
    src = cwd / 'hello.txt'
    src.write_text('hola')

    # copy
    cli.do_cp('hello.txt copia.txt')
    assert (cwd / 'copia.txt').exists()
    assert (cwd / 'copia.txt').read_text() == 'hola'

    # move
    cli.do_mv('copia.txt movida.txt')
    assert not (cwd / 'copia.txt').exists()
    assert (cwd / 'movida.txt').exists()
