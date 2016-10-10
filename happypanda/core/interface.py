import code, sys

def interactive():
    
    # exception trick to pick up the current frame
    try:
        raise None
    except:
        frame = sys.exc_info()[2].tb_frame.f_back

    # evaluate commands in current namespace
    namespace = frame.f_globals.copy()
    namespace.update(frame.f_locals)

    code.interact("======== Start Happypanda Debugging ========", local=namespace)
    print("======== END ========")




