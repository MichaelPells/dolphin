while True:
    Input = input(">>> ")

    Auto = "["+Input+"]"
    
    Terminal = open("file_terminal.txt", "w")
    Terminal.write(Auto)
    Terminal.close()
