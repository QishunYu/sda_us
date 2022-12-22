from optparse import OptionParser
import logging
from datetime import datetime
import can
import udsoncan
import isotp
from udsoncan.connections import PythonIsoTpConnection
from udsoncan.client import Client
from udsoncan.exceptions import *
from udsoncan.services import *
import platform
from time import sleep

import sys
import os
# getting the name of the directory where the this file is present.
current = os.path.dirname(os.path.realpath(__file__))
# Getting the parent directory name where the current directory is present.
parent = os.path.dirname(current)
# adding the parent directory to the sys.path.
sys.path.append(parent)

from udsoncan_setup import udsoncan_connection_User, udsoncan_setup_logging, udsoncan_connection
from udsoncan_config import Project

def calc_angle(angle_hex):
    phys_value = 0
    if angle_hex < 0x8000:
        phys_value = angle_hex * 0.01 -3
    else:
        phys_value = angle_hex * 0.01 -3
    return phys_value

def decode_SDA_result(recorddata):
    res = {}
    res['routine status'] = 0
    res['routine result'] = 0
    res['driving profile'] = 0
    res['progress'] = 0
    res['horizonal angle'] = 0
    res['Vertical angle'] = 0
    if len(recorddata) != 7:
        print('Error: invalid record data length')
    else:
        res['routine result'] = (int(recorddata[0]) & 0xF0)>>4
        res['routine status'] = (int(recorddata[0]) & 0x0F)
        res['driving profile'] = int(recorddata[1])
        res['progress'] = int(recorddata[2])
        res['horizonal angle'] = (int(recorddata[3])<<8) + int(recorddata[4])
        res['Vertical angle'] = (int(recorddata[5])<<8) + int(recorddata[6])
        print_SDA_result(res)
    return res

def print_SDA_result(res):
    print('----', res)
    status_dict = {
        0x00: 'Routine inactive',
        0x01: 'Routine active',
        0x02: 'Routine NVM write not OK',
        0x03: 'Routine timeout',
        0x04: 'Routine finished correctly',
        0x05: 'Routine aborted'}
    datavalue = res['routine status']
    desp = 'undefined'
    if datavalue in status_dict:
        desp = status_dict[datavalue] 
    print('------routine status: {0}, {1}'.format(datavalue, desp))

    result_dict = {
        0x00: 'Alignment no result available',
        0x01: 'Alignment incorrect result',
        0x02: 'Alignment correct result'}
    datavalue = res['routine result']
    desp = 'undefined'
    if datavalue in result_dict:
        desp = result_dict[datavalue]
    print('------routine result: {0}, {1}'.format(datavalue, desp))

    drive_dict = {
        0: 'Velocity too slow',
        1: 'Velocity too fast',
        2: 'Yaw rate too high',
        3: 'acceleration too high',
        4: 'location number insufficient',
        5: 'Sensor is blind'}
    datavalue = res['driving profile']
    alist = []
    for key in drive_dict:
        if ((datavalue>>key) & 0x01) > 0:
            alist.append(drive_dict[key])
    print('------drive profile: {0}, {1}'.format(hex(datavalue), alist))

    datavalue = res['progress']
    print('------progress: {0}'.format(datavalue))

    datavalue = res['horizonal angle']
    print('------horizonal angle: {0}, {1}'.format(hex(datavalue), calc_angle(datavalue)))

    datavalue = res['Vertical angle']
    print('------Vertical angle: {0}, {1}'.format(hex(datavalue), calc_angle(datavalue)))

def udsoncan_test_SideRadar_SDA_main(radarx = 'left', project = 'j7', timeout = 600, use_vcan = False):
    udsoncan_setup_logging()
    print('udsoncan test started:', datetime.now())
    logging.info('udsoncan test started')

    if radarx == 'right':
        print('-Side right radar uds test: SDA...')
        ecuname = 'side_right_radar'
        
    else:
        print('-Side left radar uds test: SDA...')
        ecuname = 'side_left_radar'

    pj = Project(project, ecuname)
    uds_client_config = pj.uds_client_config
    conn_func, conn_phys = udsoncan_connection_User(pj.isotp_params, pj.can_params, use_vcan)
    
    with Client(conn_phys, config=uds_client_config, request_timeout=20.0) as client:
        try:
            print('--enter extended session')
            client.change_session(
                DiagnosticSessionControl.Session.extendedDiagnosticSession)
            sleep(1)

            print('--security access L1')
            client.unlock_security_access(0x01)
            sleep(1)
            
            print('--start routine SDA')
            rid_sda = 0xF008
            client.start_routine(rid_sda)
            sleep(1)
            
            loops = int(timeout/4)
            radar_stop = 0
            for i in range(loops):
                # print('\n--request SDA result [{0}]...'.format(i))
                client.tester_present()
                sleep(2)

                print('\n--request SDA result [{0}]...'.format(i))
                r_resp = client.get_routine_result(rid_sda)
                # print('----resp data from radar:', list(r_resp.data))
                print('----resp data from radar:', list(r_resp.service_data.routine_status_record))
                
                result = decode_SDA_result(r_resp.service_data.routine_status_record)
                # if result['routine result'] >0 or result['routine status'] > 1:
                if result['routine status'] == 4:
                    print('\n--exit SDA progress: radar report SDA PASS')
                    radar_stop = 1
                    break
                elif result['routine status'] > 1:
                    print('\n--exit SDA progress: radar report SDA error')
                    radar_stop = 1
                    break
                sleep(2)
            if radar_stop == 0:
                print('\n--exit SDA progress: time out ({0} seconds expected)'.format(timeout))

        except NegativeResponseException as e:
            print('--Server refused our request for service %s with code "%s" (0x%02x)' % (
                e.response.service.get_name(), e.response.code_name, e.response.code))
        except InvalidResponseException as e:
            print('--Server sent an invalid payload : %s' %
                  e.response.original_payload)
        except Exception as e:
            print('--error: ', e)
        finally:
            client.close()


    print('udsoncan test end:', datetime.now())

def test():
    # data_wid = b'\x40\x22\x3f\x9b\x3e\x75\x09\x92\x07\x08\x01'
    # print(len(data_wid))
    # print(list(data_wid))
    data_sda = b'\x01\x04\x63\x01\xAD\x01\x00'
    data = decode_SDA_result(data_sda)
    print_SDA_result(data)

def main():
    usage = "usage: python3 %prog [options] arg"
    parser = OptionParser(usage)
    parser.add_option("-l", "--left_radar", dest="left_radar", help="simulate left radar", action="store_true", default=False)
    parser.add_option("-r", "--right_radar", dest="right_radar", help="simulate right radar", action="store_true", default=False)
    parser.add_option("-p", "--project", dest="project", help="project name: j7, k7 ...", default="j7")
    parser.add_option("-t", "--timeout", dest="timeout", help="timeout to exit(seconds)", type="int", default=600)
    parser.add_option("-v", "--vcan", dest="vcan", help="use vcan device", action="store_true", default=False)
    (options, args) = parser.parse_args()
    print(options)

    if not options.left_radar and not options.right_radar:
        print('Error: no valid input is given. should input "-l" or "-r" to start left or right radar test.')
    if(options.left_radar):
        udsoncan_test_SideRadar_SDA_main('left', options.project, options.timeout, options.vcan)
    
    if(options.right_radar):
        udsoncan_test_SideRadar_SDA_main('right', options.project, options.timeout, options.vcan)
    
if __name__ == "__main__":
    main()
    # test()



