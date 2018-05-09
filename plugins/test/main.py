import __hpx__ as hpx
from pprint import pprint
print = pprint
log = hpx.get_logger(__name__)

def main():
    log.info("hi")
    try:
        raise ValueError
    except:
        log.exception("")

if __name__ == '__main__':
    main()