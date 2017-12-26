# -*- mode: python -*-
import os
import sys
import shutil
from PyInstaller.utils.hooks import exec_statement

sys.modules['FixTk'] = None

working_dir = os.getcwd()
app_name = "happypandax"
icon_path = "static/favicon.ico"
version_path = "deploy/win/version.txt"

block_cipher = None

thumb_path = "static/thumbnails"
if os.path.exists(thumb_path):
  shutil.rmtree(thumb_path)

added_files = [
    ('bin', 'bin'),
    ('templates/base.html', 'templates'),
    ('translations', 'translations'),
    ('static', 'static'),
  ]

if sys.platform.startswith('win'):
  added_files += [('deploy/win/vc_redist.x86.exe', '.')]

interface_files = exec_statement("""
    from happypanda.common import utils
    from happypanda import interface
    print(" ".join(utils.get_package_modules(interface, False)))""").split()

def make(py_file, exe_name, analysis_kwargs={}, pyz_args=None, exe_kwargs={}):

  a_kwargs = dict(binaries=[],
               datas=added_files,
               hiddenimports=['engineio.async_gevent']+interface_files,
               hookspath=[],
               runtime_hooks=[],
               excludes=['FixTk', 'tcl', 'tk', '_tkinter', 'tkinter', 'Tkinter'],
               win_no_prefer_redirects=False,
               win_private_assemblies=False,
               cipher=block_cipher)
  a_kwargs.update(analysis_kwargs)

  a = Analysis([py_file],
               pathex=[working_dir],
               **a_kwargs
               )

  p_args = (a.pure, a.zipped_data)
  if pyz_args is not None:
    p_args = pyz_args

  pyz = PYZ(*p_args, cipher=block_cipher)

  e_kwargs = dict(icon=icon_path,
                  version=version_path,
                  exclude_binaries=True,
                  debug=False,
                  strip=False,
                  upx=True,
                  console=True)

  e_kwargs.update(exe_kwargs)

  exe = EXE(pyz, a.scripts, name=exe_name, **e_kwargs)

  return exe, a.binaries, a.zipfiles, a.datas


coll = COLLECT(
            #*make("run.py", app_name),
            *make("gui.py", app_name+'_gui', exe_kwargs={'console':False}),
            #*make("HPtoHPX.py", "HPtoHPX"),
             strip=False,
             upx=True,
             name=app_name)
