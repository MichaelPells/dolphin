
def runEngine():
    import engine
    engine.main()
    
if __name__ == "__main__":
    
    import subprocess
    import time
    import json
    import os
    import signal
    import psutil
    from pathlib import Path
    from multiprocessing import Process

    def checkRunningSystems():
        systems = open("data/running_systems.pid").read().strip().splitlines()
        if len(systems) == 0: return
        else:
            print("Some systems are currently running. What do you want to do?")
            print("""
 1. Stop all running systems
 2. Preserve all running systems
 3. Exit Terminal
""")
            Reply = input(">>> Choose option: ")
            if Reply == "1":
            for PID in systems:
                
                exitSystem(PID)    
        
    #checkRunningSystems()
    
    def loadSystem():
        outputs_last_modified = Path("engine_outputs.txt").stat().st_mtime

        engine = Process(target=runEngine, args=())
        engine.start()
        global engine_PID
        engine_PID = engine.pid

        while Path("engine_outputs.txt").stat().st_mtime == outputs_last_modified: pass
        else:
            while len(open("engine_outputs.txt").read().splitlines()) < 1: pass
            else:
                global engine_properties
                engine_properties = list(json.loads("{"+open("engine_outputs.txt").readline().strip()+"}").values())[0]
        
    loadSystem()

    def closed_Subsystems(PID):
        outputs = open("engine_outputs.txt").read().splitlines()
        for u in range(len(outputs)-1, -1, -1):
            output = list(json.loads("{"+outputs[u]+"}").values())[0]
            if output["no"] == str(no) and output["text"] == str(PID) and os.path.exists("data/engine_outputs.txt") == False:
                if output["code"] == "CODE": return True
                else: return True
        else: return False
                
    def exitSystem(PID=None):
        if PID == None: PID = engine_PID
        else:
            try: PID = int(PID)
            except: return
        if PID in psutil.pids():
            while True:
                closed = closed_Subsystems(PID)
                if closed == True: break
            try: os.kill(PID, signal.SIGTERM)
            except Exception as e: print(str(e))
        systems = open("data/running_systems.pid").read().strip().splitlines()
        systems.remove(str(PID))
        if len(systems) > 0: open("data/running_systems.pid", "w").write("\n".join(systems)+"\n")
        else: open("data/running_systems.pid", "w").write("\n".join(systems))


    def exitAll():
        systems = open("data/running_systems.pid").read().strip().splitlines()
        for PID in systems: exitSystem(PID)

    Inputbase = {}

    no = 0

    while True:
        no += 1
        Input = input(">>> ")


        if Input == "exit": Input = "exit "+str(engine_PID)
        if Input == "reload": Input = "exit old"
            
        Auto = {"no": str(no), "message": Input}

        Inputbase[str(no)] = {"timestamp": time.time(), "message": Input}
        
        Terminal = open("file_terminal.txt", "w")
        Terminal.write(json.dumps(Auto))
        Terminal.close()

        if Input == "leave":
            exit()

        elif Input == "exit "+str(engine_PID):
            exitSystem()
            exit()

        elif Input == "exit all":
            exitAll()
            exit()

        elif Input == "exit old":
            exitAll()
            loadSystem()

        elif Input.startswith("exit "):
            exitSystem(Input.replace("exit ",""))

