
def runEngine():
    import engine
    engine.main()
    
if __name__ == "__main__":
    
    import subprocess
    import time
    import json
    import os
    import signal
    from pathlib import Path
    from multiprocessing import Process

    def loadSystem():
        outputs_last_modified = Path("engine_outputs.txt").stat().st_mtime

        engine = Process(target=runEngine, args=())
        engine.start()
        global engine_PID
        engine_PID = engine.pid
        print(engine_PID)

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
            if output["no"] == str(no) and output["text"] == str(PID):
                if output["code"] == "CODE": return True
                else: return True
        else: return False
                
    def exitSystem(PID=None):
        if PID == None: PID = engine_PID
        else:
            try: PID = int(PID)
            except: return
        while True:
            closed = closed_Subsystems(PID)
            if closed == True: break
        try: os.kill(PID, signal.SIGTERM)
        except: pass
        systems = open("running_engines.pid").read().strip().splitlines()
        systems.remove(str(PID))
        if len(systems) > 0: open("running_engines.pid", "w").write("\n".join(systems)+"\n")
        else: open("running_engines.pid", "w").write("\n".join(systems))


    def exitAll():
        systems = open("running_engines.pid").read().strip().splitlines()
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

