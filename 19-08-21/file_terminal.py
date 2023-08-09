
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

    Inputbase = {}
    default_engine = None
    no = 0

    
    def loadSystem():
        outputs_last_modified = Path("engine_outputs.txt").stat().st_mtime

        engine = Process(target=runEngine, args=())
        engine.start()
        global engine_PID
        engine_PID = engine.pid

        global default_engine
        default_engine = engine_PID

        global latest
        latest = engine_PID

        while Path("engine_outputs.txt").stat().st_mtime == outputs_last_modified: pass
        else:
            while len(open("engine_outputs.txt").read().splitlines()) < 1: pass
            else:
                global engine_properties
                engine_properties = list(json.loads("{"+open("engine_outputs.txt").readline().strip()+"}").values())[0]

    def closed_Subsystems(PID):
        outputs = open("engine_outputs.txt").read().splitlines()
        for u in range(len(outputs)-1, -1, -1):
            output = list(json.loads("{"+outputs[u]+"}").values())[0]
            if output["no"] == str(no) and output["system"] == PID and os.path.exists("data/engine_outputs.txt") == False:
                if output["code"] == "CODE": return True
                else: return True
        else: return False
                
    def exitSystem(PID=None, created=None, systems=None):
        if systems == None:
            systems = json.loads("{"+open("data/running_systems.pid").read().strip().replace("\n",", ")+"}")
            systems = {int(PID):systems[PID] for PID in systems}
        if PID == None: PID = engine_PID
        else:
            try: PID = int(PID)
            except: return
        if created == None: created = systems[PID][1]
        if PID in psutil.pids() and psutil.Process(pid=PID).create_time() == created:
            while True:
                closed = closed_Subsystems(PID)
                if closed == True: break
            try: os.kill(PID, signal.SIGTERM)
            except Exception as e: print(str(e))
        del systems[PID]
        if len(systems) > 0:
            systems = {str(PID):systems[PID] for PID in systems}
            open("data/running_systems.pid", "w").write(str(systems)[1:-1].replace("'",'"').replace("], ","]\n")+"\n")
        else: open("data/running_systems.pid", "w")


    def exitAll():
        systems = json.loads("{"+open("data/running_systems.pid").read().strip().replace("\n",", ")+"}")
        systems = {int(PID):systems[PID] for PID in systems}
        for system in systems.values():
            exitSystem(system[0], system[1])
        

    def action():
        global Input
        global no
        global default_engine
        global Inputbase
        
        if Input == "exit": Input = "exit "+str(engine_PID)
        if Input == "reload": Input = "exit old"
        if Input.startswith("history of "): Input = "history "+Input.split("history of ")[1]

        if Input == "exit all" or Input == "exit old":
            system = "ALL"
        else: system = default_engine
        
            
        Auto = {"no": str(no), "system": system, "message": Input}

        Inputbase[str(no)] = {"timestamp": time.time(), "system": system, "message": Input}
        
        Terminal = open("file_terminal.txt", "w")
        Terminal.write(json.dumps(Auto))
        Terminal.close()

        if Input == "exit all":
            exitAll()

        elif Input.startswith("exit "):
            exitSystem(Input.replace("exit ",""))

    def checkRunningsystems():
        global Input
        systems = json.loads("{"+open("data/running_systems.pid").read().strip().replace("\n",", ")+"}")
        systems = {int(PID):systems[PID] for PID in systems}
        
        if len(systems) == 0: pass
        else:
            for system in systems.values():
                if int(system[0]) not in psutil.pids(): exitSystem(system[0], system[1], systems)
                
            systems = json.loads("{"+open("data/running_systems.pid").read().strip().replace("\n",", ")+"}")
            systems = {int(PID):systems[PID] for PID in systems}
            if len(systems) > 0:
                print("Some systems are currently running. What do you want to do?")
                print("""
1. Stop all running systems
2. Preserve all running systems
3. Exit Terminal
    """)
                Reply = input(">>> Select an option: ")
                if Reply == "1":
                    Input = "exit all"
                    action()

                elif Reply == "2": pass
                
                elif Reply == "3": exit()

                else:
                    print("\nWrong Input! Could not proceed.\n")
                    checkRunningsystems()
                
        
    checkRunningsystems()
    loadSystem()


    while True:
        no += 1
        Input = input(">>> ")

        if len(Input) > 0:
            
            if Input.startswith("switch to "):
                if Input.split("switch to ")[1] == "latest":
                    default_engine = latest
                    continue
                else:
                    New = int(Input.split("switch to ")[1])
                    systems = json.loads("{"+open("data/running_systems.pid").read().strip().replace("\n",", ")+"}")
                    systems = {int(PID):systems[PID] for PID in systems}
                    if New in systems and New in psutil.pids() and psutil.Process(pid=New).create_time() == systems[New][1]:
                        default_engine = New
                    else: print("Switch could not be made. "+New+" is not running.")
                    continue
            
            if Input == "exit": Input = "exit "+str(engine_PID)
            if Input == "reload": Input = "exit old"
            if Input.startswith("history of "): Input = "history "+Input.split("history of ")[1]

            if Input == "exit all" or Input == "exit old":
                system = "ALL"
            else: system = default_engine
            
                
            Auto = {"no": str(no), "system": system, "message": Input}

            Inputbase[str(no)] = {"timestamp": time.time(), "system": system, "message": Input}
            
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

