#Cross-device file copier

print("Hi...", end=" ")

import requests
import time
import json

info = "Welcome to Cross-device file copier!\n\n"
for i in info:
    print(i, end="")
    time.sleep(0.02)
time.sleep(0.5)

lastUsedCoord = ""

def main(lastUsedCoord):    
    lastCoord = input("Enter last coordinate of server (Press Enter key if unknown.): 192.x.x.")
    if lastCoord != "":
        y = [int(lastCoord)]
        time.sleep(0.4)
    elif lastUsedCoord == "":
        print("Performing automatic search for server...")
        y = range(2, 256)
    else:
        print("Resolving to last found server...")
        y = [int(lastUsedCoord)]
        
    def ping(guesses, tryTimeout, trials):
        for x in y:
            try: pingURL = requests.get("http://192.168.137."+str(x)+":8000/", allow_redirects=False, timeout=(tryTimeout,None))
            except:
                if x == 255 or len(y) == 1: return (None, tryTimeout, trials)
            else: return (x, tryTimeout, trials)

    tryTimeout = 0.03
    trial = 1
    while trial <= 4:
        attempt = ping(y, tryTimeout, trial)
        if attempt[0] != None:
            lastCoord = str(attempt[0])
            if len(y) > 1: lastUsedCoord = str(attempt[0])
            break
        else:
            tryTimeout += 0.03
            trial += 1
            if trial == 4:
                print("Server not found!")
                time.sleep(2)
                quit()

    quicklinks = json.loads(open("data/quicklinks.txt").read())
    
    linkList = []
    
    saved = quicklinks["saved"]
    if len(saved) > 0:
        for quicklink in saved:
            if quicklink not in linkList and quicklink != "": linkList.append(quicklink)
    mostUsed = quicklinks["mostUsedTimes"]
    if len(mostUsed) > 0:
        toNumber = list(mostUsed.keys())
        for n in range(0, len(toNumber)): toNumber[n] = int(toNumber[n])
        compare = sorted(toNumber, reverse=True)
        temp_linkList = []
        for t in compare:
            for quicklink in mostUsed[str(t)]:
                if len(temp_linkList) < 3:
                    if quicklink not in linkList and quicklink != "": temp_linkList.append(quicklink)
                else: break
        linkList.extend(temp_linkList)

    recent = quicklinks["recent"]
    if len(recent) > 0:
        for quicklink in recent:
            if quicklink not in linkList and quicklink != "": linkList.append(quicklink)

    if len(linkList) > 0:
        print("\nQuicklinks:")
        for ln in range(0, len(linkList)):
            print("  "+str(ln+1)+"  -  "+linkList[ln])
        print("\nTry entering a Quicklink No. to preceed your file, E.g: 1 > index.html\n")
            
    files = input("File(s): ").split(", ")
    for file in files:
        if file.find(">") > 0 and file.split(">")[0].strip().isnumeric() == True:
            quickl = file.split(">")
            try: file = linkList[int(quickl[0].strip())-1]+"/"+quickl[1].strip()
            except: pass
        
        url = "http://192.168.137."+lastCoord+":8000/"+file
        
        try: source = requests.get(url, allow_redirects=True)
        except Exception as error: print(error)
        else:
            if source.status_code == 200:
                if len(file) > 0:
                    path = source.url.split("/")
                    if len(path[-1]) > 0: name = path[-1]
                    else: name = path[-2]+"_index.html"
                else: name = "index.html"

                open("Received/"+name, "wb").write(source.content)
                print(name+" copied successfully!")

                newRecent = "/".join(source.url.split("/")[3:-1])

                # Update mostUsed
                if newRecent != "":
                    if newRecent not in quicklinks["mostUsedList"]:
                        quicklinks["mostUsedList"][newRecent] = 0
                    else:
                        quicklinks["mostUsedList"][newRecent] += 1
                        if str(quicklinks["mostUsedList"][newRecent]) not in quicklinks["mostUsedTimes"]: quicklinks["mostUsedTimes"][str(quicklinks["mostUsedList"][newRecent])] = []
                        quicklinks["mostUsedTimes"][str(quicklinks["mostUsedList"][newRecent])].insert(0, newRecent)
                        try: quicklinks["mostUsedTimes"][str(quicklinks["mostUsedList"][newRecent]-1)].remove(newRecent)
                        except: pass

                # Update recent
                if newRecent != "" and newRecent != quicklinks["recent"][-1]:
                    quicklinks["recent"][-2] = quicklinks["recent"][-1]
                    quicklinks["recent"][-1] = newRecent

                open("data/quicklinks.txt","w").write(json.dumps(quicklinks))
                
            else: print("File could not be copied: "+source.reason.replace("File",file))

    time.sleep(0.5)
    def reuse():
        use = input("\nDo you have another file(s) to transfer? (Yes/No): ")

        if use.lower() == "yes": main(lastUsedCoord)
        elif use.lower() == "no": time.sleep(1)
        else:
            print("Unknown Response: Please enter Yes or No.")
            reuse()
    reuse()
main(lastUsedCoord)
