import __hpx__ as hpx
import pprint
import sys

log = hpx.get_logger(__name__)

@hpx.subscribe("InitApplication.init")
def appinit():
    log.info("Application startup")

@hpx.subscribe("init")
def init():
    log.info("initiating plugin")

@hpx.subscribe("disable")
def disable():
    log.info("disabling plugin")

def main():
    log.info("hi")

if __name__ == '__main__':
    main()