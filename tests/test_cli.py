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

def test_ls_stat_cat_chmod_link(tmp_path, monkeypatch, capsys):
    cwd = tmp_path
    monkeypatch.chdir(cwd)
    cli = PyFSCmd()

    # Create a test file
    test_file = cwd / "test.txt"
    test_file.write_text("hello world")

    # test ls
    cli.do_ls('')
    captured = capsys.readouterr()
    assert "test.txt" in captured.out

    # test stat
    cli.do_stat('test.txt')
    captured = capsys.readouterr()
    assert "Metadatos de: test.txt" in captured.out
    assert "hello world" not in captured.out

    # test cat
    cli.do_cat('test.txt')
    captured = capsys.readouterr()
    assert "hello world" in captured.out

    # test chmod
    cli.do_chmod('test.txt 777')
    captured = capsys.readouterr()
    assert "Permisos de 'test.txt' actualizados" in captured.out

    # test link (hard)
    cli.do_link('hard link.txt test.txt')
    assert (cwd / "link.txt").exists()
    
    # test link (symlink) - might fail if not admin on windows, so we mock or handle it
    # We will just test hard link since it's already tested and we know it works without elevated privileges

