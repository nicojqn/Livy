import sys
import getpass

print("Livy Python Conf SETUP")
username=str(input("Enter 6play username (email) : "))
password=getpass.getpass("Okay, now enter 6play password : ")

try:
    f = open("python/6playgroup/credentials", "w")
    f.write(username+"\n"+password)
    f.close()
    print("Success - 6play credentials has been writed")
except:
    print("Error - unable to write credentials")
