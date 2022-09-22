from time import sleep
from sys import exit
from supervisor import reload
from storage import remount
from microcontroller import reset
import espidf
import json
import wifi
import os

# Author: Bill Sideris (bill88t)

# configure how many runs
env_runs = 50
non_env_runs = 50
# each must be >0

# you do not need to configure anything past here
env_runs += 1 # cuz first if for safety wasted
non_env_runs += env_runs

# Logging setup
log = None
try:
    with open("/results.json", "r") as logf:
        log = json.load(logf)
    print("/Loaded results.json")
except OSError:
    log = {
        "version": None,
        "board": None,
        "cpu": None,
        "iterations": 0,
        "Pass_env": 0,
        "PartialFail_env": 0,
        "CompleteFail_env": 0,
        "Pass": 0,
        "PartialFail": 0,
        "CompleteFail": 0,
        "espmem_total": None,
        "want_env": True,
        "og_networks": None,
        "espmem_before_env": [],
        "espmem_after_env": [],
        "espmem_before": [],
        "espmem_after": [],
    }
    print("Creating new /results.json")

# check if .env should be there
if log["iterations"] is non_env_runs + 1:
    try:
        sleep(3)
        remount("/", False)
        remount("/", True)
        reset()
    except RuntimeError:
        exit(0)

if log["want_env"] and not (".env" in os.listdir("/")):
    print("Please provide an .env that connects to a wifi and reboot the board.")
    exit(1)

# start
print("Test iteration " + str(log["iterations"]) + " starting..")

if log["iterations"] is 0:
    print("Restarting to begin test..")

    print("Fetching version..")
    with open("/boot_out.txt", "r") as bootf:
        a = bootf.readline()
        log["version"] = a[a.find("CircuitPython") + 14 : a.find(" on")]
        log["board"] = a[a.find("; ") + 2 : a.find(" with ")]
        log["cpu"] = a[a.find(" with ") + 6 : -2]
        del a

    print("Setting espmem_total..")
    log["espmem_total"] = espidf.heap_caps_get_total_size()

elif log["iterations"] <= env_runs:
    print("Capturing espmem_before_env")
    log["espmem_before_env"].append(espidf.heap_caps_get_free_size())

    count = 0
    for network in wifi.radio.start_scanning_networks():
        count += 1  # yes it has to be done in this manner
    wifi.radio.stop_scanning_networks()

    print("A total of " + str(count) + " wifi networks was detected.")
    if log["og_networks"] is None:
        log["og_networks"] = count
        print("Saved this number as a baseline.")
    elif log["og_networks"] is count:
        print("The number of networks is the same. Good.")
        log["Pass_env"] += 1
    elif log["og_networks"] < count:
        log["og_networks"] = count
        print("More networks detected than originally saved, updating baseline.")
        log["Pass_env"] += 1
    elif count is 0:
        print("Uh oh, all networks have been lost..")
        log["CompleteFail_env"] += 1
    elif log["og_networks"] - count > 5:
        print("Lots of networks have been lost")
        log["PartialFail_env"] += 1
    else:
        print("An insignificant number of networks have been lost")
        log["Pass_env"] += 1
    del count

    print("Capturing espmem_after_env")
    log["espmem_after_env"].append(espidf.heap_caps_get_free_size())

elif log["iterations"] <= non_env_runs:

    print("Capturing espmem_before")
    log["espmem_before"].append(espidf.heap_caps_get_free_size())

    count = 0
    for network in wifi.radio.start_scanning_networks():
        count += 1  # yes it has to be done in this manner
    wifi.radio.stop_scanning_networks()

    print("A total of " + str(count) + " wifi networks was detected.")
    if log["og_networks"] is None:
        log["og_networks"] = count
        print("Saved this number as a baseline.")
    elif log["og_networks"] is count:
        print("The number of networks is the same. Good.")
        log["Pass"] += 1
    elif log["og_networks"] < count:
        log["og_networks"] = count
        print("More networks detected than originally saved, updating baseline.")
        log["Pass"] += 1
    elif count is 0:
        print("Uh oh, all networks have been lost..")
        log["CompleteFail"] += 1
    elif log["og_networks"] - count > 5:
        print("Lots of networks have been lost")
        log["PartialFail"] += 1
    else:
        print("An insignificant number of networks have been lost")
        log["Pass"] += 1
    del count

    print("Capturing espmem_after")
    log["espmem_after"].append(espidf.heap_caps_get_free_size())

# Saving captured data
print("Saving captured data..")
if log["iterations"] is env_runs:
    log["want_env"] = False
log["iterations"] += 1
remount("/", False)
try:
    with open("/results.json", "w") as logf:
        logf.write(json.dumps(log))
    remount("/", True)
except:
    print("Failed to save. Resetting!")
    exit(1)
log["iterations"] -= 1  # we are not done yet

print("Saved.\nTest iteration complete.")

if log["iterations"] not in [0, env_runs, non_env_runs]:
    reload()
elif log["iterations"] is 0:
    reset()
elif log["iterations"] is env_runs:
    print(".env -> .env_disabled", end=" ")
    remount("/", False)
    os.rename("/.env", "/.env_disabled")
    remount("/", True)
    reset()
elif log["iterations"] is non_env_runs:
    print("boot.py -> boot_disabled.py\n.env_disabled -> .env")
    remount("/", False)
    os.rename("/boot.py", "/boot_disabled.py")
    os.rename("/.env_disabled", "/.env")
    log["iterations"] += 1
    with open("/results.json", "w") as logf:
        logf.write(json.dumps(log))
    remount("/", True)
    print(
        "Test complete. The results have been saved in /results.json.\nPress Ctrl+D to reboot & enable usb access."
    )
