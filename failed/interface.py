import main as app

def main():
    print("""
Create:
 1. Client
 2. Server
    """)
    mode = input("Run as (1/2): ")

    if mode == "1":
        feedback = app.run_client2()
        print(feedback)
    elif mode == "2": app.run_server2()
    else:
        print("Unknown Response: Please enter 1 or 2.")
        main()

    #feedback = app.feedback
    
    if feedback[0] == "client":
        feedback[3] = input("Test: ")
        feedback[2] = "send"
        app.interface(feedback)
        
main()
