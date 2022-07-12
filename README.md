# Livy

Live TV and Replay WebAPP, enjoy watch live TV and Replay whenever and wherever you want !  

---

## Installation

- Livy require a debian server with : 
  - node
  - python


1. Clone or download this repo in debian
2. Goto Livy dir `cd Livy`
3. Install 
  - `apt update -y && apt install git nodejs npm python3 python3-pip -y`
  - `cd src/server/node && npm install express compression fs encodeurl path xmlhttprequest && cd ../../..`
  - `pip install urlquick`
  - Please be sure that python webutils is not installed
    If it is installed, run -> `pip uninstall webutils`
4. Configure Livy
  - Configure Credentials :
    - 6play : `cd src/server && python3 LivypyConfSetup.py && cd ../..` -> Then Enter Username and password
