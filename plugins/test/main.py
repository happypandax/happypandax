import __hpx__ as hpx
import pprint
import sys

print(hpx)

log = hpx.get_logger(__name__)

@hpx.subscribe("InitApplication.init")
def init():
    log.info("init")
    log.info(hpx.PluginState)
    log.info("saving config: {}".format(hpx.save_config({'name': 'test'})))

def main():
    log.info("hi")

if __name__ == '__main__':
    main()