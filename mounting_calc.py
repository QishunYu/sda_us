import json
import ast

#declare constants
POS_PHY_MIN = -15
POS_PHY_MAX = 15
ANGLE_PHY_MIN = -180
ANGLE_PHY_MAX = 180

POS_NORM_FACTOR = 1000
ANGLE_NORM_FACTOR = 10
POS_PHY_OFFSET = -15
ANGLE_PHY_OFFSET = -180


def calc_param(radar_param):
    hex_output = ""
    did_output = ""
    pos_x = radar_param['Radar Position X']
    pos_y = radar_param['Radar Position Y']
    pos_z = radar_param['Radar Position Z']
    angle_azimuth = radar_param['Mounting Angle Azimuth']
    angle_elevation = radar_param['Mounting Angle Elevation']
    flipped = str(radar_param['Radar Flipped'])
    DID_value = radar_param['DID']
    hex_header = radar_param['HEX Header']

    # calculate hex values
    dec_pos_x = round((pos_x / 1000 - POS_PHY_OFFSET) * POS_NORM_FACTOR)
    byte1_pos_x = dec_pos_x // 256
    byte2_pos_x = dec_pos_x % 256
    hex_pos_x = split_append((f'{dec_pos_x:x}').upper())
    dec_pos_y = round((pos_y / 1000 - POS_PHY_OFFSET) * POS_NORM_FACTOR)
    byte1_pos_y = dec_pos_y // 256
    byte2_pos_y = dec_pos_y % 256
    hex_pos_y = split_append((f'{dec_pos_y:x}').upper())
    dec_pos_z = round((pos_z / 1000 - POS_PHY_OFFSET) * POS_NORM_FACTOR)
    byte1_pos_z = dec_pos_z // 256
    byte2_pos_z = dec_pos_z % 256
    hex_pos_z = split_append((f'{dec_pos_z:x}').upper())
    dec_angle_azimuth = round((angle_azimuth - ANGLE_PHY_OFFSET) * ANGLE_NORM_FACTOR)
    byte1_angle_azimuth = dec_angle_azimuth // 256
    byte2_angle_azimuth = dec_angle_azimuth % 256
    hex_angle_azimuth = split_append((f'{dec_angle_azimuth:x}').upper())
    dec_angle_elevation = round((angle_elevation - ANGLE_PHY_OFFSET) * ANGLE_NORM_FACTOR)
    byte1_angle_elevation = dec_angle_elevation // 256
    byte2_angle_elevation = dec_angle_elevation % 256
    hex_angle_elevation = split_append((f'{dec_angle_elevation:x}').upper())

    hex_output = hex_header + hex_output + hex_pos_x + hex_pos_y + hex_pos_z + hex_angle_azimuth + \
        hex_angle_elevation + " 0" + flipped
    did_output = DID_value + " " + str(byte1_pos_x) + " " + str(byte2_pos_x) \
        + " " + str(byte1_pos_y) + " " + str(byte2_pos_y) \
        + " " + str(byte1_pos_z) + " " + str(byte2_pos_z) \
        + " " + str(byte1_angle_azimuth) + " " + str(byte2_angle_azimuth) \
        + " " + str(byte1_angle_elevation) + " " + str(byte2_angle_elevation) \
        + " " + flipped
    return hex_output, did_output

def split_append(hex_value):
    output = " "
    if (len(hex_value) == 3):
        hex_value = "0" + hex_value
    output = output + hex_value[:2] + " " + hex_value[2:]
    return output

def uds_sec_algo(level, f_SeedArray, params):
    # logging.debug("level, seed, params:", level, list(seed), params)
    SEC_MASK = 0x0919931125
    l_Sec_Coe_a_L1 = 0x2528
    l_Sec_Coe_a_L2 = 0x2527
    l_Sec_Coe_c_L1 = 0x28
    l_Sec_Coe_c_L2 = 0x27
    l_seed = 0
    l_key = 0
    # f_SeedArray = bytearray(seed)
    f_SeedArrarySize = len(f_SeedArray)
    f_SecurityLevel = level
    f_KeyArray = [0]*5

    l_seed = ((f_SeedArray[0] << 32) & 0x000000FF00000000)
    l_seed = (l_seed | (((f_SeedArray[1]) << 24) & 0x00000000FF000000))
    l_seed = (l_seed | (((f_SeedArray[2]) << 16) & 0x0000000000FF0000))
    l_seed = (l_seed | (((f_SeedArray[3]) << 8) & 0x000000000000FF00))
    l_seed = (l_seed | (((f_SeedArray[4]) & 0x00000000000000FF)))
    if (f_SeedArrarySize == 5 and l_seed != 0 and l_seed != 0x000000FFFFFFFFFF):
        if (f_SecurityLevel == 0x01):
            l_key = (l_Sec_Coe_a_L1 * (l_seed ^ SEC_MASK) +
                     l_Sec_Coe_c_L1) % 0x0000010000000000
        elif (f_SecurityLevel == 0x03):
            l_key = (l_Sec_Coe_a_L2 * (l_seed ^ SEC_MASK) +
                     l_Sec_Coe_c_L2) % 0x0000010000000000
    f_KeyArray[0] = (l_key & 0x00000000000000FF)
    f_KeyArray[1] = ((l_key & 0x000000000000FF00) >> 8)
    f_KeyArray[2] = ((l_key & 0x0000000000FF0000) >> 16)
    f_KeyArray[3] = ((l_key & 0x00000000FF000000) >> 24)
    f_KeyArray[4] = ((l_key & 0x000000FF00000000) >> 32)
    return bytes(f_KeyArray)


def calc_key(radar_seed):
    seed_0 = int(("0x" + radar_seed[0]), 16)
    seed_1 = int(("0x" + radar_seed[1]), 16)
    seed_2 = int(("0x" + radar_seed[2]), 16)
    seed_3 = int(("0x" + radar_seed[3]), 16)
    seed_4 = int(("0x" + radar_seed[4]), 16)

    seed = [seed_0, seed_1, seed_2, seed_3, seed_4]

    keystr = ''
    print("seed(decimal):", seed, "\n")
    key1 = uds_sec_algo(1, seed, None)
    # print("key(binary):", key1)
    for i in key1:
        keystr += ('%02x ' % i)
    # print("key(hex format):", keystr)
    return keystr

print("This script is used to calculate access key and the radar mounting locations.", "\n",\
    "In json file, the position is in (mm), the angle is in (degree)", "\n")

# Opening JSON file
f = open('mounting_parameter.json',)
# extract radar data
radar_param = json.load(f)

# calculate security key to access radar
radar_seed = radar_param['Seed'].split()

radar_key_str = calc_key(radar_seed).upper()
radar_key_str = "27 02 " + radar_key_str

print("To gain security access to radar, use the code below: ", "\n")
print(radar_key_str, "\n")

# calculate mounting parameters for side radars
left_radar_param = radar_param['Left Bosch Radar'][0]
right_radar_param = radar_param['Right Bosch Radar'][0]

left_hex_output, left_did_output = calc_param(left_radar_param)
right_hex_output, right_did_output = calc_param(right_radar_param)


print("the left radar mounting parameters in CANalyzer is: ", "\n")
print(left_hex_output, "\n")
print("the right radar mounting parameters in CANalyzer is: ", "\n")
print(right_hex_output, "\n")
print("")
print("the left radar mounting parameters in DID 0x2000 is: ", "\n")
print(left_did_output, "\n")
print("the right radar mounting parameters in DID 0x2001 is: ", "\n")
print(right_did_output, "\n")
