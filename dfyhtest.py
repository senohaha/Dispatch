import socket
import fcntl
import struct
def get_host_ip():
    myname = socket.getfqdn(socket.gethostname())
    myaa = socket.gethostbyname(myname)
    print myname
    print myaa

def get_local_ip(ifname='enp9s0'):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))
    return socket.inet_ntoa(inet[20:24])




if __name__=='__main__':
    d = {'a':5,'zz':3,'g':4,'d':1,'b':2}
    s = sorted(d.items(), lambda x, y: cmp(x[1], y[1]))[0][0]
    print s