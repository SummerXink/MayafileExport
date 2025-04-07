import time
def initialize():
    try:
        import maya.standalone
        maya.standalone.initialize(name="python")
        print("maya.standalone.initialize success!")
    except: 			
        pass

def uninitialize():
    try: 			
        import maya.standalone
        maya.standalone.uninitialize() 	
        print("maya.standalone.uninitialize success!")
    except: 			
        pass

def createModel():
    # import mayapy
    import maya.cmds as cmds

    # create sphere and move it
    sphereName = cmds.polySphere(name="mySphere")
    cmds.move( -2, 1, 0, sphereName, absolute=True )

    # create cube and move it
    cubeName = cmds.polyCube(name="myCube")
    cmds.move( 0, 0.5, 0, cubeName, absolute=True )

    # create cylinder and move it
    cylinderName = cmds.polyCylinder(name="myCylinder")
    cmds.move( 2, 1, 0, cylinderName, absolute=True )

    print("createModel success!")

def saveFile():
    # import mayapy
    import maya.cmds as cmds

    # save .ma file
    cmds.file(rename=r"D:\standalone\autoCreateMod.ma")
    cmds.file(save=True, type="mayaAscii")

    print("saveFile success!")

if __name__ == '__main__':
    tic = time.time()
    initialize()

    createModel()

    saveFile()

    uninitialize()
    toc = time.time()
    print("run time cost: {}".format(toc-tic))