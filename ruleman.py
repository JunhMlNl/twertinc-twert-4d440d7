import os
import datetime
import threading
from tracemalloc import start
import time
import psutil
import elevate
import sqlite3


# time_start = [] # ['21:29', '11:25']
# time_end = [] # ['22:22', '11:37']
# exe_list = [] # ['notepad.exe']
hosts_path = "C:\Windows\System32\drivers\etc\hosts"



# theo dang 127.0.0.1 facebook.com www.facebook.com thi moi block dc
#restart lai browser de bat dau block


redirect = "127.0.0.1"
website_list = [] # ["www.facebook.com","facebook.com",
    # "dub119.mail.live.com","www.dub119.mail.live.com",
    # "www.gmail.com","gmail.com"]

counter = 0

# def update_rules(time_start_rules,time_end_rules,process_names,domain_names):
#     #todo this should be Lock()
#     global time_start 
#     time_start.clear()
#     time_start = time_start_rules.copy()
#     global time_end
#     time_end.clear()
#     time_end = time_end_rules.copy()
#     global exe_list
#     exe_list = process_names.copy()
#     global website_list
#     website_list = domain_names.copy()
#     print("update_rules(): ",threading.get_native_id(),time_start,time_end,exe_list,website_list)

#시간 설정
def checktime(name):
    db = sqlite3.connect('nblocker.sqlite3')
    cur = db.cursor()
    time_rules = cur.execute("SELECT  strftime('%H:%M',from_time),strftime('%H:%M',to_time) FROM time_rules")
    time_rules_rows = time_rules.fetchall()
    
    time_starts = []
    time_ends = []

    for row in time_rules_rows:
      # print(type(row),type(row[0]))
      time_start = row[0]
      time_end = row[1]
      time_starts.append(time_start)
      time_ends.append(time_end)

    db.commit()
    db.close()
    print(time_starts, time_ends, sep = '\n')
    if not time_starts:
        # print(name,counter,threading.get_native_id(),"No time range means always True",len(time_start),time_start)
        return False
    else:
      # print("Checktime",counter,threading.get_native_id(),time_start,time_end)
      for i in range(len(time_starts)):
        # print(name,"Checking time between",time_start[i],time_end[i],"now is",datetime.datetime.now().hour,":",datetime.datetime.now().minute)
        datetime_time_start = datetime.datetime.strptime(time_starts[i], '%H:%M')

        datetime_time_end = datetime.datetime.strptime(time_ends[i], '%H:%M')
        if (datetime_time_start.hour * 60 + datetime_time_start.minute <= datetime.datetime.now().hour * 60 + datetime.datetime.now().minute) and (datetime.datetime.now().hour * 60 + datetime.datetime.now().minute <= datetime_time_end.hour * 60 + datetime_time_end.minute):
            return True

    return False  


def blockexe(): #block từ time_start -> time_end (2 cái này là string) vd: "18:00"
    exe_list = []
    if checktime():
        #print("exe still blocked")

        for exe in exe_list: #todo, change to using psutil please
            cmd_string = "taskkill /f /im " + exe
            os.system(cmd_string) # os.system là để chạy command trên cmd

def psutil_blockexe(): #block từ time_start -> time_end (2 cái này là string) vd: "18:00"
    db = sqlite3.connect('nblocker.sqlite3')
    cur = db.cursor()
    process_rules = cur.execute("""
        SELECT process_rules.exe_name
    FROM process_rules
    JOIN time_rules ON process_rules.time_rule_name = time_rules.name
    WHERE process_rules.is_blocked = TRUE
      AND time_rules.from_time <= strftime('%H:%M', 'now', 'localtime')
      AND time_rules.to_time >= strftime('%H:%M', 'now', 'localtime')
    """)
    process_rules_rows = process_rules.fetchall()
    
    exe_list = []

    for row in process_rules_rows:
        exe_list.append(row[0])
    db.commit()
    db.close()
    
    if checktime("exe"):
        for proc in psutil.process_iter():
            if proc.name() in exe_list:
                proc.kill()
    else:
        # print("psutil_blockexe checktime() not yet")
        pass
                

def webblock():  
    db = sqlite3.connect('nblocker.sqlite3')
    cur = db.cursor()

    # Query domain_rules and join with time_rules based on time_rule_name
    domain_rules = cur.execute("""
        SELECT domain_rules.domain 
        FROM domain_rules 
        JOIN time_rules ON domain_rules.time_rule_name = time_rules.name
        WHERE domain_rules.is_blocked = TRUE
          AND time_rules.from_time <= strftime('%H:%M', 'now', 'localtime')
          AND time_rules.to_time >= strftime('%H:%M', 'now', 'localtime')
    """)
    domain_rules_rows = domain_rules.fetchall()

    website_list = []

    for row in domain_rules_rows:
        domain_name = row[0]
        if 'www.' in domain_name:
            st = domain_name.find('www.')
            if domain_name.find('/', st + 4) != -1:
                domain_name = domain_name[:domain_name.find('/', st + 4)]
            website_list.append(domain_name[st + 4:])
            website_list.append(domain_name[st:])
        else:
            if 'http:' in domain_name:
                st = 7
                if domain_name.find('/', st) != -1:
                    domain_name = domain_name[: domain_name.find('/', st)]
                website_list.append(domain_name[st:])
                website_list.append('www.' + domain_name[st:])
            elif 'https:' in domain_name:
                st = 8
                if domain_name.find('/', st) != -1:
                    domain_name = domain_name[:domain_name.find('/', st)]
                website_list.append(domain_name[st:])
                website_list.append('www.' + domain_name[st:])
            else:
                if domain_name.find('/') != -1:
                    domain_name = domain_name[:domain_name.find('/')]
                website_list.append(domain_name)
                website_list.append('www.' + domain_name)

    db.commit()
    db.close()

    if website_list:  # Only block if there are domains to block
        with open(hosts_path, 'r+') as file:
            content = file.readlines()
            file.seek(0)
            for line in content:
                if not (redirect in line):
                    file.write(line)

            file.truncate()
            for website in website_list:
                if website in content:
                    pass
                else:
                    file.write(redirect + " " + website + "\n")
        print(website_list)
    else:
        with open(hosts_path, 'r+') as file:
            content = file.readlines()
            file.seek(0)
            for line in content:
                if not (redirect in line):
                    file.write(line)

            file.truncate()
            
        print('fun')

def thread_run(id):
    print("A thread ",threading.get_native_id()," was spawned for rule manager daemon")
    while True:
        time.sleep(1)
        try:
            psutil_blockexe()
            webblock()
        except Exception as e:
            print("RuleMan exception: ",e)    

def start_thread():
    elevate.elevate()
    print("Rule Manager is now running ",threading.get_native_id())
    rThread = threading.Thread(target=thread_run,args=(1,),daemon=True)
    rThread.start()
    pass