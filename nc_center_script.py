#!/usr/bin/python3

import sys
import xlrd
import pprint
import time
import json
import re, uuid
from datetime import datetime
import telnetlib
import os

#setting date
now = datetime.now()
today = now.strftime("%Y-%m-%d")

# CITY #
print(f"\n\nEnter the City Name. Ex... chicago ")
city = input("City Name: ").strip().lower()

# POD COUNT #
print (f"\n\nEnter the Pod count. Ex... B ")
pod_count = input("Pod: ").strip().upper()

# PROMPTING FOR S_Number #
print (f"\n\nEnter the S Number. Ex... S589876")
s_numb = input("S Number: ").strip()

# ENTER THE SITE PMATT NUMBER #
print (f"\n\nEnter the PMATT Number")
pmatt = input("PMATT: ").strip()

city_pmatt = f"{city}_{pod_count}_{s_numb}_PMATT-{pmatt}"
#print (city_pmatt)

# LOCATION OF FILES TO BE USED
carton_label = "center_script_carton_label.xlsx"
carton_label_path = "/home/jamespone/dell-scripts/carton_labels/nc_carton_labels/"
carton_label_full = f"{carton_label_path}{carton_label}"
book = xlrd.open_workbook(carton_label_full)
sheet = book.sheet_by_name('Carton Label')

data = {}

for i in range(1, sheet.nrows):
    row = sheet.row_values(i)
    device = row[19]
    default_gw = [row[22]]

    data[device] = {
            'ipv4 address': [row[20]],
            'ipv4 subnet mask': '255.255.255.192',
            'ipv4 gateway': [row[22]],
            'idrac mac': [row[8]],
            'rack name': [row[15]],
            'device name': [row[19]],
            'domain name': [row[23]],
            'burnin location': [row[14]],
            'serial_num':[row[6]],
            'kgp_asset':[row[12]],
     }

# CREATING SITE SPECIFIC DIRECTORY PATH.
main_dir = f"/home/jamespone/dell-scripts/pmatts/nc_pmatts/{city_pmatt}/"
sub_dir_1 = "dhcp_info"
sub_dir_2 = "logs"
sub_dir_3 = "scripts"
sub_dir_4 = "firmware"

dhcp_dir = f"{main_dir}{sub_dir_1}"
logs_dir = f"{main_dir}{sub_dir_2}"
scripts_dir = f"{main_dir}{sub_dir_3}"

integration_logs = f"{logs_dir}/integration_logs"
post_logs_dir = f"{logs_dir}/post_logs"
lc_logs = f"{logs_dir}/lc_logs"
diagnostic_log_dir = f"{logs_dir}/diagnostics"

firmware_dir = f"{main_dir}{sub_dir_4}"
firm_bios_dir = f"{firmware_dir}/bios_upgrade"
firm_idrac_dir = f"{firmware_dir}/idrac_upgrade"

site_cisco_dir = f"{main_dir}cisco_3650"
site_cisco_gmop = f"{site_cisco_dir}/gmop_configs"
site_ansible_directory = f"{site_cisco_dir}/ansible"
site_ansible_upgrades = f"{site_ansible_directory}/ansi_upgrade"
site_ansible_postlogs = f"{site_ansible_directory}/ansi_postlogs"

os.makedirs(dhcp_dir, exist_ok=True)
os.makedirs(logs_dir, exist_ok=True)
os.makedirs(scripts_dir, exist_ok=True)
os.makedirs(integration_logs, exist_ok=True)

os.makedirs(post_logs_dir, exist_ok=True)
os.makedirs(lc_logs, exist_ok=True)
os.makedirs(diagnostic_log_dir, exist_ok=True)

os.makedirs(firmware_dir, exist_ok=True)
os.makedirs(firm_bios_dir, exist_ok=True)
os.makedirs(firm_idrac_dir, exist_ok=True)

os.makedirs(site_ansible_directory, exist_ok=True)
os.makedirs(site_cisco_gmop, exist_ok=True)
os.makedirs(site_ansible_upgrades, exist_ok=True)
os.makedirs(site_ansible_postlogs, exist_ok=True)


# DEFINING FILE PATHS TO BE USED.
temp = "/home/jamespone/dell-scripts/temp/nc_temp/"

main_log_path = f"/home/jamespone/dell-scripts/pmatts/nc_pmatts/{city_pmatt}/"

dhcp_info_add = "dhcp_info/add_dhcp.txt"
dhcp_info_rm = "dhcp_info/remove_dhcp.txt"

dhcp_scripts_add = f"{main_log_path}{dhcp_info_add}"      #Use to Add DHCP Addressing
dhcp_scripts_remove = f"{main_log_path}{dhcp_info_rm}"    #Use to Remove DHCP Addressing

script_path = "scripts/"
config_script_path = f"{main_log_path}{script_path}"

temp_ansible_file = f"{temp}ansible_hosts.txt"

#CREATING DHCP SCRIPT AND ROUTING TO BE USED ON ROUTER 3.
ospf_proc = "router ospf 1"
network_1 = f"{default_gw}".replace("['", "").replace("']", "")
network = f"{network_1}".replace(".1", ".0")
net_wildcard = f"network {network} 0.0.0.63 area 1"
add_net = f"{ospf_proc}\n\t{net_wildcard}\n\texit\n"
rem_net = f"{ospf_proc}\n\tno {net_wildcard}\n\texit\n"

interface = "interface fa0/1.100"
inter_ip_add = f"ip address {default_gw} 255.255.255.192".replace("['", "").replace("']", "")
int_config = f"{interface}\n\t{inter_ip_add}\n\texit"

ospf_int_conf = f"{int_config}" #REMOVED '{add_net}' THAT WAS BEFORE 'int_config' BECAUSE ROUTES ENTER THE OSPF PROCESS BY BEING ADDED TO THE INTERFACE.

with open(dhcp_scripts_add, 'w')as f:
    print (ospf_int_conf, file = f)

with open(dhcp_scripts_remove, 'w') as f:
    print(rem_net, file = f)

with open(dhcp_scripts_add, 'a')as f:
    for device, dhcp_info in data.items():
        dhcp = f"{dhcp_info['ipv4 address']} 255.255.255.192\n\tdefault-router {dhcp_info['ipv4 gateway']}".replace("['", "").replace("']", "")
        mac = f"{dhcp_info['idrac mac']}".replace("['", "").replace("']", "")
        mac = f"01{mac}"
        n =  (f"\nip dhcp pool {device}\n\thost {dhcp} \n\tclient-identifier {mac}")
        print (n,  file=f)

with open(dhcp_scripts_remove, 'a') as f:
    for device, dhcp_info in data.items():
        n = f"\nno  ip dhcp pool {device}"
        print (n, file=f)

#CREATING FILEPATH TO REACH 'ADD DHCP FILE' THAT WILL LATER BE READ BY THE 'router3_config.py' SCRIPT. 
temp_dhcp_path = f"{temp}dhcp_temp.txt"

with open(temp_dhcp_path, 'w') as dh:
    print (dhcp_scripts_add, file=dh)



#CREATING DCHP ASSIGNMENTS IN WINDOWS SERVER.
dhcp_2_dir = "/home/jamespone/dell-scripts/pmatts/dhcp_files/"
dhcp_2_file =f"{dhcp_2_dir}network_cloud_dhcp.conf"

with open (dhcp_2_file, 'w') as dhcpmasq:
    
    #CREATING THE NETOWRK ADDRESS TO BE USED.
    network_address_1 = f'{default_gw}'.replace("['", "").replace("']", "") 
    network_address_2 = network_address_1[:-1]
    network_address_3 = f'{network_address_2}0'
    #print (network_address_3)

    #THE FIRST LINE OF THE UBUNTU DNSMASQ FILE
    dhcp_range = f"dhcp-range={network_address_3},static"
    network_dnsmasq = f"dhcp-option=1,255.255.255.192"
    gateway_dnsmasq = f"dhcp-option=3,{network_address_1}"
    network_header = f"{dhcp_range}\n{network_dnsmasq}\n{gateway_dnsmasq}"

    print(network_header,file=dhcpmasq)
    
    for device, dhcp_info in data.items():
        
        #dhcp = f"{network_address_3},{dhcp_info['ipv4 address']} 255.255.255.192\n\tdefault-router {dhcp_info['ipv4 gateway']}".replace("['", "").replace("']", "")
        
        #print (dhcp)
        dnsmasq_ip = f"{dhcp_info['ipv4 address']}".replace("['", "").replace("']", "")
        mac_2 = f"{dhcp_info['idrac mac']}".replace("['", "").replace("']", "")
        mac_2_1 = (mac_2[:2])
        mac_2_2 = (mac_2[2:4])
        mac_2_3 = (mac_2[4:6])
        mac_2_4 = (mac_2[6:8])
        mac_2_5 = (mac_2[8:10])
        mac_2_6 = (mac_2[10:12])
        final_mac = f"{mac_2_1}:{mac_2_2}:{mac_2_3}:{mac_2_4}:{mac_2_5}:{mac_2_6}"
        static_mac_line = f"dhcp-host={final_mac}"
        
        static_assignment = f"{static_mac_line},{dnsmasq_ip}"
        print (static_assignment,file=dhcpmasq)
        #n =  (f"\nip dhcp pool {device}\n\thost {dhcp} \n\tclient-identifier {mac}")
        #print (n,  file=f)







#CREATING  'host_ips.txt' FILE THAT WILL BE USED BY 'ping_test.py' TO VERIFY CONNECTIVITY TO ALL OF THE SERVERS.
host_ip_file = f"{main_dir}host_ips.txt"
with open (host_ip_file, 'w') as f:
    for ip, ip_hosts in data.items():
        x = f"{ip_hosts['ipv4 address']}".replace("['", "").replace("']", "")
        print (x, file=f)

#CREATING 'execute_script_path.txt' FILES THAT WILL BE USED BY 'execute_script.py' TO EXECUTE ALL SCRIPTS.
execute_config_file = f"{temp}execute_config_path.txt"
with open (execute_config_file, 'w')as f9:
    print (scripts_dir + '/', file=f9)

execute_log_file = f"{temp}execute_log_path.txt"
with open (execute_log_file, 'w') as f8:
    print (logs_dir + '/', file=f8)

#CREATING THE LINES THAT WILL BE EXECUTED FOR CONFIGURING THE DEVICES AND POSTCHECKS.
script_init_path = f"{config_script_path}all_script_init.txt"
with open(script_init_path, 'w') as f1:
    for device, script in data.items():
        device = f"{script['device name']}".replace("['", "").replace("']", "")
        print (f"nohup ./{device}_script.py &", file=f1)

post_init_path = f"{post_logs_dir}/all_log_init.txt"
with open(post_init_path, 'w') as f1:
    for device, script in data.items():
        device = f"{script['device name']}".replace("['", "").replace("']", "")
        host_ip = f"{script['ipv4 address']}".replace("['", "").replace("']", "")
        device_data = f"{script['serial_num']}_{script['kgp_asset']}".replace("['", "").replace("']", "")

        first_section = f"nohup full_post-checks.py {host_ip} root calvin {device} "
        second_section = f">{post_logs_dir}/{device}_{device_data}_post_logs.txt &"
        print (first_section + second_section, file=f1)

lc_log_path = f"{lc_logs}/lc_logs_init.txt"
with open(lc_log_path, 'w') as f1:
    for device, script in data.items():
        device = f"{script['device name']}".replace("['", "").replace("']", "")
        host_ip = f"{script['ipv4 address']}".replace("['", "").replace("']", "")

        first_section = f"nohup lc_logs.py {host_ip} root calvin {device} "
        second_section = f">{lc_logs}/{device}_lc_post_logs.txt &"
        lc_commands = (f'{first_section} {second_section}')
        print (lc_commands, file=f1)

diagnostic_log_path = f"{diagnostic_log_dir}/diagnostic_lines.txt"
with open (diagnostic_log_path, 'w') as f3:
    for device, script in data.items():
        device = f"{script['device name']}".replace("['", "").replace("']", "")
        host_ip = f"{script['ipv4 address']}".replace("['", "").replace("']", "")

        first_section = f"nohup redfish_diag.py -ip {host_ip} -u root -p calvin"
        reboot_extended_test = "-r 2 -m 0"
        diag_init_output = f">{diagnostic_log_dir}/{device}diag_init_output.txt"
        diagnostic_lines = f"{first_section} {reboot_extended_test} {diag_init_output} &"
        print(diagnostic_lines, file=f3)

diagnostic_nfs_transfer = f"{diagnostic_log_dir}/transfer_diagLogs_to_WinServer.txt"
with open (diagnostic_nfs_transfer, 'w') as f4:
    for device, script in data.items():
        device = f"{script['device name']}".replace("['", "").replace("']", "")
        host_ip = f"{script['ipv4 address']}".replace("['", "").replace("']", "")
        
        first_section = f'nohup redfish_diag.py -ip {host_ip} -u root -p calvin -e 2'
        file_share = f'--ipaddress 172.26.125.81 --sharename /dellupgrades/la_diag_logs --filename {device}_diagnostic_log.txt &'
        nfs_transfer_lines = f'{first_section} {file_share}'
        print (nfs_transfer_lines, file=f4)




#CREATING A LINEBREAK IN THE LOGS.
with open ("/home/jamespone/postlog_errors.txt", 'a') as f5:
    print (f"\n\n--------------------\n{today}\n{main_dir}", file = f5)

###### FOR SCRIPTS TO FIX CONFIG ISSUES REPLACE "static_dell.py" WITH THE SCRIPT THAT WILL FIX YOUR ISSUE ################
#CREATING SCRIPT THAT WILL BE PUSHED TO SERVERS.

#nc_static_dell = "/home/jamespone/dell-scripts/static_dell_scripts/nc_static_dell_NO_VARIABLE_DATA.py"
nc_static_dell = "/home/jamespone/dell-scripts/static_dell_scripts/nc_static_dell.py"

with open(nc_static_dell, 'r') as static_config:
    sconfig = static_config.read()
## Function to create BIOS target config job
    for device, script_info in data.items():
        device_script_path = f"{config_script_path}{device}_script.py"
        with open(device_script_path, 'w')as f2:

            #SETTING THE VARIABLES THAT WILL APPEAR AT THE BEGINNING OF EACH DEVICE'S PYTHON SCRIPT. 
            shabang = "#!/usr/bin/python3"
            import_modules = "import sys, paramiko, time, sys"
            file_creation = (f"{shabang}\n\n{import_modules}")

            #DELL r740 LOGIN INFORMATION.
            set_ip = (f"ip_address = {script_info['ipv4 address']}").replace("[", "").replace("]", "")
            username = """username = 'root'"""
            password = """password = 'calvin'"""
            login_info = (f"#Login Info\n{set_ip}\n{username}\n{password}")
            
            #OPENING INTEGRATION LOG FILE
            server_name = (f"{script_info['device name']}").replace("['", "").replace("']", "")
            log_path = (f"""int_log_path = (f"{integration_logs}/{server_name}_integration_logs.txt")""".replace("['", "").replace("']", ""))
            open_file = (f"{log_path}\nwith open (int_log_path, 'w') as file1:")
                    
            #SSH CONFIG FOR PARAMIKO.
            ssh_client = "ssh_client = paramiko.SSHClient()"
            ssh_client2 = "ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())"
            ssh_client3 = "ssh_client.connect(hostname=ip_address,username=username,password=password,look_for_keys=False,allow_agent=False)"
            xx="""transport = ssh_client.get_transport()\nif not transport.is_authenticated():\n\ttransport.auth_interactive_dumb(username,handler=None,submethods="")"""
            ssh_print = """print ("SUCCESSFUL CONNECTION TO " + ip_address)"""
            ssh_remote = "remote_connection = ssh_client.invoke_shell()"
            ssh_info = (f"{ssh_client}\n{ssh_client2}\n{ssh_client3}\n{xx}\n\n{open_file}\n\t{ssh_print}\n\t{ssh_remote}\n\t")

            #BINDING 3 PREVIOUS SECTIONS TOGETHER.
            script_config = (f"{file_creation}\n\n{login_info}\n\n{ssh_info}\n")
            print (script_config, file=f2)
  
            #SETTING THE VARIABLES FOR THE DEVICE'S CONFIG.
            dns_rn = (f"{script_info['device name']}").replace("[", "").replace("]", "")
            dns_dn = (f"{script_info['domain name']}").replace("[", "").replace("]", "")
            ip_addr = (f"{script_info['ipv4 address']}").replace("[", "").replace("]", "")
            ip_gtw = (f"{script_info['ipv4 gateway']}").replace("[", "").replace("]", "")
            ip_msk = (f"{script_info['ipv4 subnet mask']}").replace("[", "").replace("]", "")
            
            #PUTTING VARIABLE DATA INSIDE CONFIG SCRIPTS
            enter = (f"""remote_connection.send("\\n")\n\ttime.sleep(2)\n""")
            racadm = (f"""remote_connection.send("racadm\\n")\n\ttime.sleep(2)\n""")
            set_rn = (f"""remote_connection.send("racadm set iDRAC.Nic.DNSRacName {dns_rn}\\n")\n\ttime.sleep(2)\n""").replace("'", "").replace("'", "")
            set_dn = (f"""remote_connection.send("racadm set iDRAC.Nic.DNSDomainName {dns_dn}\\n")\n\ttime.sleep(2)\n""").replace("'", "").replace("'", "")
            set_ip = (f"""remote_connection.send("racadm set iDRAC.IPv4Static.Address {ip_addr}\\n")\n\ttime.sleep(2)\n""").replace("'", "").replace("'", "")
            set_gw = (f"""remote_connection.send("racadm set iDRAC.IPv4Static.Gateway {ip_gtw}\\n")\n\ttime.sleep(2)\n""").replace("'", "").replace("'", "")
            set_msk =(f"""remote_connection.send("racadm set iDRAC.IPv4Static.Netmask {ip_msk}\\n")\n\ttime.sleep(2)\n""").replace("'", "").replace("'", "")
            set_variable_data = (f"{enter}\t{racadm}\t{set_rn}\t{set_dn}\t{set_ip}\t{set_gw}\t{set_msk}")

            #PRINTING LOG FILES TO FILE
            log_file = "\tprint (output, file=file1)"
            
            #BRINGING THE FULL CONFIG TOGETHER AND PRINTING TO THEIR INDIVIDUAL FILES.
            var_data_header = ("\t#CONNECTING TO DEVICE AND SENDING VARIABLD DATA")
            #full_config = (f"{var_data_header}{sconfig}") ## NEEDS TO ONLY BE USED WHEN VARIABLE DATA ISN'T AVAILABLE.
            full_config = (f"{var_data_header}{set_variable_data}{sconfig}")
            #full_config = (f"{var_data_header}{set_variable_data}") ## ONLY USE WHEN STATIC CONFIG ISN'T REQUIRED.
            print (full_config, file=f2)

            #CREATING A CONFIG THAT DOESN'T CONFIGURE VARIABLE INFO HOSTNAME AND IP.




#MAKING THE SCRIPTS EXECUTABLE.
#x = f"{config_script_path}*"
#os.chmod(x,0o664)a


# DEFINING BIOS AND IDRAC VERSIONS THAT NEED TO BE USED. 
bios_ver = "BIOS_HC85T_WN64_2.8.2_02.EXE"
idrac_ver = "iDRAC-with-Lifecycle-Controller_Firmware_FP2XW_WN64_4.22.00.53_A00.EXE"

# CREATING BIOS UPGRADE LINES.
bios_file = f"{firm_bios_dir}/bios_lines.py"
with open(bios_file, 'w')as bios_1:
    for device, dhcp_info in data.items():
        ipv4_line = f"{dhcp_info['ipv4 address']}".replace("['", "").replace("']", "")
        bios_line_1 = f"nohup redfish_firmware_update.py -ip"
        bios_line_2 = f"-u root -p calvin -t HTTP --uri http://172.26.125.81/dellupgrades_web/{bios_ver} -r y &"
        bios_line_3 = f"{bios_line_1} {ipv4_line} {bios_line_2}"
        print (bios_line_3, file=bios_1)

# CREATING IDRAC UPGRADE LINES.
idrac_file = f"{firm_idrac_dir}/idrac_lines.txt"
with open(idrac_file, 'w')as idrac_1:
    for device, dhcp_info in data.items():
        ipv4_line = f"{dhcp_info['ipv4 address']}".replace("['", "").replace("']", "")
        idrac_line_1 = f"nohup redfish_firmware_update.py -ip"
        idrac_line_2 = f"-u root -p calvin -t HTTP --uri http://172.26.125.81/dellupgrades_web/{idrac_ver} -r y &"
        idrac_line_3 = f"{idrac_line_1} {ipv4_line} {idrac_line_2}"
        print (idrac_line_3, file=idrac_1)

# INITIATE INTEGRACTION SCRIPT.
integrate_variable_data = f"{main_dir}variables.py"

with open (integrate_variable_data, 'w')as integrate_vd:

    # SHABANG THAT IS USED TO AT THE BEGINNING OF HTE PYTHON FILE. 
    shabang_var = "#!/usr/bin/python3"
    print(f"{shabang_var}", file=integrate_vd)
    # CREATING LINES THAT WILL BE READ TO INITIATE THE BIOS UPGRADES.
    bios_lines = f"""bios_lines = "{bios_file}" """
    print (f"{bios_lines}", file=integrate_vd)

    # CREATING LINES THAT WILL BE READ TO INITIATE THE IDRAC UPGRADES.
    idrac_lines = f"""idrac_lines = "{idrac_file}" """
    print (f"{idrac_lines}", file=integrate_vd)

    # SCRIPT FILE PATH USED BY ./integrate.py TO 'cd' AND 'chmod + x' DEVICE SCRIPTS.
    script_fp = f"""scripts_filepath = "{config_script_path}" """
    print (f"{script_fp}", file=integrate_vd)
    
    # CREATING LINES THAT WILL BE READ TO INITIATE THE DEVICE SPECIFIC INTEGRATION.
    script_exe_lines = f"""script_lines = "{config_script_path}all_script_init.txt" """
    print (f"{script_exe_lines}", file=integrate_vd)
    
    # CREATING LINES THAT WILL BE READ TO INITIATE THE POSTLOGS. 
    log_init_fp = f"""postlog_lines = "{post_logs_dir}/all_log_init.txt" """
    print (f"{log_init_fp}", file=integrate_vd)

    # CREATING LINE STHAT WILL BE READ TO INITIATE THE LC LOGS.
    lc_init_fp = f"""lc_log_lines = "{lc_logs}/lc_logs_init.txt" """   
    print (f"{lc_init_fp}", file=integrate_vd)
    
    # CREATING LINES THAT WILL BE READ TO INITIATE THE TRANSFER OF THE DIAGNOSTIC LOGS TO FTP SERVER.
    diag_init_fp =  f"""diagnostic_log_lines = "{diagnostic_log_dir}/diagnostic_lines.txt" """
    print (f"{diag_init_fp}", file=integrate_vd)
    
    #CREATING THE CITY VARIABLE
    city = f"""city = "{city_pmatt}" """
    print (f"{city}", file=integrate_vd)




# MOVING A COPY OF THE INTEGRATION SCRIPT TO THE PROJECT FILEPATH #
integrate_static_script = "/home/jamespone/dell-scripts/temp/nc_temp/integrate.py" 
new_integrate_static_script = f"{main_dir}"

#print (f"{integrate_static_script}\n{new_integrate_static_script}")
os.system(f"cp {integrate_static_script} {new_integrate_static_script}")

# MOVING A COPY OF THE BIOS UPGRADE SCRIPT TO THE PROJECT'S FILEPATH #
bios_static_script = "/home/jamespone/dell-scripts/temp/nc_temp/bios_upgrade.py"
os.system(f"cp {bios_static_script} {new_integrate_static_script}")

# MOVING A COPY OF THE iDRAC  UPGRADE SCRIPT TO THE PROJECT'S FILEPATH #
idrac_static_script = "/home/jamespone/dell-scripts/temp/nc_temp/idrac_upgrade.py"
os.system(f"cp {idrac_static_script} {new_integrate_static_script}")

# MOVING A COPY OF THE iDRAC DIAG_INIT  SCRIPT TO THE PROJECT'S FILEPATH #
diag_static_init = "/home/jamespone/dell-scripts/temp/nc_temp/diag_init.py"
os.system(f"cp {diag_static_init} {new_integrate_static_script}")

# MAKING DEVICE SPECIFIC SCRIPTS EXECUTABLE #
os.system(f"chmod +x {main_dir}scripts/*.py")

# MAKING MAIN INTEGRATE SCRIPT EXECUTABLE #
os.system(f"chmod +x {main_dir}*.py")

# COPYING 'CENTER_SCRIPT_CARTON_LABEL' EXCEL FILE TO THE SITE DIRECTORY SO IT CAN BE USED ON THE RASPBERRY PI DURING PORT TESTING.
os.system(f"cp {carton_label_full} {main_dir}")

# EXECUTE THE DHCP SERVER RESTART #
os.system(f"sudo service dnsmasq restart")

# MOVING THE ANSIBLE FILES TO THE CURRENT PMATT DIRECTORY #
os.system(f"cp {temp_ansible_file} {site_ansible_directory}")

# MOVING THE GMOP CONFIGS TO THE SITE FOLDER #
os.system(f"mv /home/jamespone/dell-scripts/temp/nc_temp/gmop_configs/* {site_cisco_gmop}/")

# COPYING UPGRADE FILES TO SITE DIRECTORY #
os.system(f"cp /home/jamespone/dell-scripts/static_dell_scripts/nc_static_ansible/ansi_3650_upgrade/* {site_ansible_upgrades}/")

# COPYING POSTLOG FILES TO SITE DIRECTORY #
os.system(f"cp /home/jamespone/dell-scripts/static_dell_scripts/nc_static_ansible/ansi_3650_postlogs/* {site_ansible_postlogs}/")

print("\n\t\tNetwork Cloud Center Script executed successfully\n")
#print("\t\tBE SURE TO SWAP THE HAS SIGN ON LINES 252&253, THEN 313&314\n\n")
