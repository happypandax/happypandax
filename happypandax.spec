# -*- mode: python -*-
import os
import sys
import shutil
from PyInstaller.utils.hooks import exec_statement

sys.modules['FixTk'] = None

working_dir = os.getcwd()
icon_path = "deploy/osx/app.icns" if sys.platform.startswith('darwin') else "static/favicon/favicon.ico"
version_path = "deploy/win/version.txt"

block_cipher = None

thumb_path = "static/thumbnails"
if os.path.exists(thumb_path):
  shutil.rmtree(thumb_path)

app_name = exec_statement("""
    from happypanda.common import constants
    print(constants.executable_name)""")

app_gui_name = exec_statement("""
    from happypanda.common import constants
    print(constants.executable_gui_name)""")

osx_bundle_name = exec_statement("""
    from happypanda.common import constants
    print(constants.osx_bundle_name)""")

added_files = [
    ('bin', 'bin'),
    ('templates/base.html', 'templates'),
    ('translations', 'translations'),
    ('static', 'static'),
    ('migrate', 'migrate'),
    ('alembic.ini', '.'),
  ]

interface_files = exec_statement("""
    from happypanda.common import utils
    from happypanda import interface
    print(" ".join(utils.get_package_modules(interface, False)))""").split()
print(interface_files)
if os.name == 'nt':
  added_files += [('deploy/win/vc_redist.x86.exe', '.')]
  interface_files.append("winreg")
  app_name = app_name[:-4]
  app_gui_name = app_gui_name[:-4]
  
version_str = exec_statement("""
    from happypanda.common import constants
    print(constants.version_str)""")

def make(py_file, exe_name, analysis_kwargs={}, pyz_args=None, exe_kwargs={}):

  a_kwargs = dict(binaries=[],
               datas=added_files,
               hiddenimports=['engineio.async_gevent',
                              'logging.config',
                              'sqlalchemy.ext.baked']+interface_files,
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

col = [
        *make("run.py", app_name),
        *make("gui.py", app_gui_name, exe_kwargs={'console':False}),
        *make("HPtoHPX.py", "HPtoHPX"),
        ]

if sys.platform.startswith('darwin'):
  app = BUNDLE(*col,
           name=osx_bundle_name,
           icon=icon_path,
           bundle_identifier=None,
           info_plist={
              'CFBundleExecutable': 'MacOS/'+app_gui_name,
              'CFBundleGetInfoString': "A manga/doujinshi manager with tagging support (https://github.com/happypandax/server)",
              'NSHighResolutionCapable': 'True',
              'CFBundleVersion': version_str,
              'NSHumanReadableCopyright': u"Copyright © 2018, Twiddly, All Rights Reserved"
              },
           )
  col = []

coll = COLLECT(
            *col,
             strip=False,
             upx=True,
             name=app_name)