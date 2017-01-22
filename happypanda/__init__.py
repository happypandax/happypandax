#import logging
#import sys
#import os
#import argparse

#from PyQt5 import QtCore
#from PyQt5.QtWidgets import QApplication
#from logging.handlers import RotatingFileHandler

#from .common import utils, constants

### PARSE ARGUMENTS ##
#parser = argparse.ArgumentParser(prog='Happypanda',
#                                  description='A video/manga/doujinshi manager with tagging support')
#parser.add_argument('-d', '--debug', action='store_true',
#                    help='happypanda_debug_log.log will be created in main directory')
#parser.add_argument('-v', '--version', action='version',
#                    version='Happypanda v{}'.format(constants.version))
#parser.add_argument('-e', '--exceptions', action='store_true',
#                    help='Disable custom excepthook')
#parser.add_argument('-x', '--dev', action='store_true',
#                    help='Development Switch')

#args = parser.parse_args()

### LOG SETUP ##

## create log directory
#if constants.log_dir:
#    if not os.path.isdir(constants.log_dir):
#        os.mkdir(constants.log_dir)

#log_handlers = []
#log_level = logging.INFO
#if args.dev:
#    log_handlers.append(logging.StreamHandler())
#else:
#    logging.raiseExceptions = False # Don't raise exception if in production mode

#if args.debug:
#    print("{} created at {}".format(constants.debug_log, os.getcwd()))
#    try:
#        with open(constants.debug_log, 'x') as f:
#            pass
#    except FileExistsError:
#        pass

#    lg = logging.FileHandler(constants.debug_log, 'w', 'utf-8')
#    lg.setLevel(logging.DEBUG)
#    log_handlers.append(lg)

#for log_path, lvl in ((constants.normal_log, logging.INFO), (constants.error_log, logging.ERROR)):
#    try:
#        with open(log_path, 'x') as f:
#            pass
#    except FileExistsError: pass
#    lg = RotatingFileHandler(log_path, maxBytes=100000 * 10, encoding='utf-8', backupCount=1)
#    lg.setLevel(lvl)
#    log_handlers.append(lg)

#logging.basicConfig(level=log_level,
#                format='%(asctime)-8s %(levelname)-10s %(name)-10s %(message)s',
#                datefmt='%d-%m %H:%M',
#                handlers=tuple(log_handlers))

#log = logging.getLogger(__name__)
#log_i = log.info
#log_d = log.debug
#log_w = log.warning
#log_e = log.error
#log_c = log.critical

### QAPP CONFIGURATION ##

#def qt_msg_handler(type_, ctx, msg):
#    if type_ == QtCore.QtCriticalMsg:
#        log_e(msg)
#        utils.eprint(msg)
#    elif type_ == QtCore.QtFatalMsg:
#        log_c(msg)
#        utils.eprint(msg)
#    elif type_ == QtCore.QtWarning:
#        log_w(msg)

#QtCore.qInstallMessageHandler(qt_msg_handler)

#app = QApplication(sys.argv)
#app.setOrganizationName('Pewpews')
#app.setOrganizationDomain('https://github.com/Pewpews/happypanda')
#app.setApplicationName('Happypanda')
#app.setApplicationDisplayName('Happypanda')
#app.setApplicationVersion('v{}'.format(constants.version))





