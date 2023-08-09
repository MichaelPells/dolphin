import subprocess
engine = subprocess.Popen("py engine.py", shell=True)
while True:
    Input = input(">>> ")

    Auto = "["+Input+"]"
    
    Terminal = open("file_terminal.txt", "w")
    Terminal.write(Auto)
    Terminal.close()
