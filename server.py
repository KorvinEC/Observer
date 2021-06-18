import socket
import os
import threading
import configparser
import sys
import json

config = configparser.ConfigParser()
if not config.read('server_config.ini'):
    config = configparser.RawConfigParser() 
    config.add_section('SERVER')
    config.set('SERVER', 'JSON_FILE_SAVE_DEST' , 'server_json//')
    config.set('SERVER', 'SCREENSHOT_DEST' , 'server_screenshot//')
    with open('config.ini', 'w') as configfile:
        config.write(configfile)
    configfile.close()

DEFAULTS = config['SERVER']

JSON_FILE_SAVE_DEST = DEFAULTS['JSON_FILE_SAVE_DEST']
SCREENSHOT_DEST = DEFAULTS['SCREENSHOT_DEST']

def wait_for_json_file():
    try:
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(('', 9090))
        serversocket.listen(10)
        while True:
            (connection, address) = serversocket.accept()
            print('\nСonnected client\nip: ' + str(address[0]))
            if not os.path.exists(JSON_FILE_SAVE_DEST + address[0]):
                os.makedirs(JSON_FILE_SAVE_DEST + address[0])
            file_size = connection.recv(32)
            connection.send(b'1')
            file_name = connection.recv(64)
            connection.send(b'1')
            file_data = connection.recv(int(file_size))
            file = open( JSON_FILE_SAVE_DEST + address[0] + '//' + file_name.decode("utf-8")  + '.json', 'wb')
            file.write(file_data)
            file.close()
            connection.close()
    except Exception as error:
        print('Error: ' + str(error))
        connection.close()
    else:
        print('JSON exchange success\n')

def get_user_screenshot(input_ip):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((input_ip, 9091))
        file_size = sock.recv(32)
        sock.send(b'1')
        file_name = sock.recv(64)
        sock.send(b'1')
        file_data = sock.recv(int(file_size))
        if not os.path.exists(SCREENSHOT_DEST + input_ip):
            os.makedirs(SCREENSHOT_DEST + input_ip)
        file = open( SCREENSHOT_DEST + input_ip + '//' + file_name.decode("utf-8")  + '.png', 'wb', 0)
        file.write(file_data)
        file.close()
        sock.close()         
    except Exception as error:
        print('Error: ' + str(error))
        sock.close()
    else:
        print('Screenshot exchange success\n')      


def send_script(input_ip, script_name):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((input_ip, 9092))
        if not os.path.exists(script_name):
            raise Exception('No such file')
        size = os.path.getsize(script_name)
        sock.send(str(size).encode())
        sock.recv(1)
        sock.send(open( script_name,'rb' ).read(size))
        sock.close()
    except Exception as error:
        print('Error: ' + str(error))
        sock.close()
    else:
        print('Script exchange success\n')


def get_json(input_ip):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((input_ip, 9093))
        if not os.path.exists(JSON_FILE_SAVE_DEST + input_ip):
            os.makedirs(JSON_FILE_SAVE_DEST + input_ip)
        file_size = sock.recv(32)
        sock.send(b'1')
        file_name = sock.recv(64)
        sock.send(b'1')
        file_data = sock.recv(int(file_size))
        if not os.path.exists(JSON_FILE_SAVE_DEST + input_ip):
            os.makedirs(JSON_FILE_SAVE_DEST + input_ip)
        file = open( JSON_FILE_SAVE_DEST + input_ip + '//' + file_name.decode("utf-8")  + '.json', 'wb', 0)
        file.write(file_data)
        file.close()
        sock.close()
    except Exception as error:
        print('Error: %s\n' % str(error))
        sock.close()
    else:
        print('JSON exchange success\n')

# def open_json(file_path):
    # try:
        # json_dict = json.load(open(file_path))
        # if json_dict['Cpu percent usage']
    # except Exception as error:
        # print('Error: %s\n' % str(error))

def menu():
    while True:
        choice = input('>> ').split()
        if choice[0] == 'screenshot':
            try:
                get_user_screenshot(choice[1])
            except IndexError:
                print('No such ip adress')
        elif choice[0] == 'script':
            try:
                send_script(choice[1], choice[2])
            except IndexError:
                print('No such ip address or script')
        elif choice[0] == 'get_json':
            try:
                get_json(choice[1])
            except IndexError:
                print('No such ip address')
        # elif choice[0] == 'open_json':
            # open_json(choice[1])
        elif choice[0] == 'exit':
            raise SystemExit
        elif choice[0] == 'cls':
            os.system('cls')
        elif choice[0] == 'help':
            print('screenshot [ip_address] \
                   \nscript [ip_address] [script_name] \
                   \nget_json [ip_address] \
                   \nexit \
                   \ncls\n')
        else:
            print('Invalid operation\n')

def main():
    if not os.path.exists(JSON_FILE_SAVE_DEST):
        os.makedirs(JSON_FILE_SAVE_DEST)
    if not os.path.exists(SCREENSHOT_DEST):
        os.makedirs(SCREENSHOT_DEST)

    thread_1 = threading.Thread(name='wait_for_json_file', target = wait_for_json_file)
    thread_1.daemon = True
    thread_2 = threading.Thread(name='menu', target = menu)

    try:
        thread_1.start()
        thread_2.start()
    except (KeyboardInterrupt, SystemExit):
            sys.exit()

if __name__ == "__main__":
    main()


















