#import ip to kinnect
import socket
ip=[ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][0]
ip='192.168.0.100'
#create and write local ip
NomFichier = 'kinect_ip.txt'
Fichier = open(NomFichier,'w')      
Fichier.write(ip)
Fichier.close()


import os



os.startfile('C:\Users\Flowers\Dropbox\Stage M2\ESM\Windows\kinect_server.py')
os.startfile('C:\Users\Flowers\Dropbox\Stage M2\\ESM\ESM_server.py')
# os.startfile('C:\Users\Flowers\Desktop\ESM\ESM_client.py')
 
