import __hpx__ as hpx
log = hpx.get_logger(__name__)

def main():
    log.info("hi")
    raise ValueError

if __name__ == '__main__':
    main()