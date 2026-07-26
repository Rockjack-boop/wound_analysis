import urllib.request
import hashlib
import os

url = "http://127.0.0.1:5000/static/uploads/ebc6d946e9_Avulsion.png"
local_path = r"c:\Users\jeevithgowdasr\OneDrive\Desktop\wound\static\uploads\ebc6d946e9_Avulsion.png"

try:
    with urllib.request.urlopen(url) as response:
        served_data = response.read()
    
    with open(local_path, "rb") as f:
        local_data = f.read()
        
    print("Served length:", len(served_data))
    print("Local length:", len(local_data))
    
    served_md5 = hashlib.md5(served_data).hexdigest()
    local_md5 = hashlib.md5(local_data).hexdigest()
    
    print("Served MD5:", served_md5)
    print("Local MD5:", local_md5)
    
    if served_md5 == local_md5:
        print("MATCH! The served file is identical.")
    else:
        print("MISMATCH! The served file is corrupted.")
except Exception as e:
    print("Error:", e)
