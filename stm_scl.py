import socket
import math 
from struct import *
import time
import re
import logging
import string
import sys

def stm_ascii_only(text):
  if( sys.version_info.major < 3 ):
    return ''.join([i if i in string.printable else ' ' for i in text])
    #return ''.join([i if ord(i) < 128 else ' ' for i in text])
  else:
    if( isinstance(text, (bytes, bytearray)) ):
      ret = ''.join([chr(i) if chr(i) in string.printable else ' ' for i in text])
      return(ret.rstrip())


  return(str(text))


#FIXME use the new style of class MyObj(obj):
class STM_Motor_SCL:
  ip = ''
  port = 7775
  local_port = 15000
  sock = None
  motor_gearing = 4000
  mechanical_gearing = 1.0 # Used if there are gears attached to the motor
  default_socket_timeout = 5

  ENCODER_FUNCTION_OFF = 0
  ENCODER_STALL_DETECTION = 1
  ENCODER_STALL_PREVENTION = 2
  ENCODER_STALL_PREVENTION_WITH_TIMEOUT = 6


  def __init__(self, ip, local_port = None, logger = None):
    if( logger == None ):
      self._log = logging.getLogger()
    else:
      self._log = logger

    self.ip = ip
    if( local_port == None ):
      l = re.match('(.*)\.(.*)\.(.*)\.(.*)', ip)
      port_offset = l.group(4)
      self._log.info("port offset " + port_offset)
      self.local_port = 15000 + int(port_offset)
    else:
      self.local_port = local_port

    self._log.info("Initing Stm: IP=" + ip + " local UDP port = " + str(self.local_port))
    self.sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) 
    if self.sock == None:
      raise Exception("Unable to create new UDP socket")

    self.sock.bind(("0.0.0.0", self.local_port))

    self.sock.settimeout(self.default_socket_timeout)

    mv = self.get_model_revision()
    self._log.info("Model Revision is '" + str(mv) + "'")

    rv = self.get_revision_level()
    self._log.info("Revision Level is '" + str(rv) + "'")

    #mn = self.get_model_number()

    #if mv != '105W049K':
    #  self._log.error("ERROR Stepper motor did not responded with expected 105W049K value")

    return

  def get_ip(self):
    return(self.ip)

  def setup_motor(self, accl_decl_rate = 0.4, gearing = 4000, jog_speed = 0.4, velocity = 0.4):
     """ Sets initial motor settings, gearing, modes and velocities. """

     self._log.info("Setting up motor...")
     self.stop_jogging()
     self.set_electronic_gearing(gearing)
     self.set_encoder_function(self.ENCODER_STALL_PREVENTION)
     self.enable_input('3')
     #self.set_velocity_max(1.0)
     self.set_velocity(velocity)

     self.set_acceleration_rate(accl_decl_rate)
     self.set_decceleration_rate(accl_decl_rate)
     self.set_jog_decceleration_rate(accl_decl_rate)
     self.set_jog_acceleration_rate(accl_decl_rate)
     self.set_jog_speed(jog_speed)
     self._log.info("Done Setting up motor...")

     return self
 

  def get_model_revision(self):
    s = self.scl_send_command("MV", 'none')
    if( sys.version_info.major >= 3 ):
      fs = [x for x in s if x in string.printable]
    else:
      fs = filter(lambda x: x in string.printable, s)
      
    return(fs)
    #return(s.encode('ascii', errors='ignore'))
    #return(self.scl_send_command("MV", 'none'));

  def get_model_number(self):
    return(self.scl_send_command("MN", 'none'))

  def get_revision_level(self):
    return(self.scl_send_command("RV", 'value'))

  def get_alarm_code(self):
    return(self.scl_send_command("AL", 'value'))

  def get_request_status(self):
    return(self.scl_send_command("RS", 'value'))

  def no_operation(self):
    return(self.scl_send_command("NO"))
    
  def reset(self):
    return(self.scl_send_command("RE"))
    

  def set_velocity_max(self, rps):
    return(self.scl_send_command("VM" + str(round(rps, 4))))

  def set_jog_speed(self, rps):
    return(self.scl_send_command("JS" + str(round(rps, 4))))
    
  def set_change_speed(self, rps):
    return(self.scl_send_command("CS" + str(round(rps, 4))))
 
  def set_velocity(self, rps):
    return(self.scl_send_command("VE" + str(round(rps, 4))))

  def check_accl_range(self, rpsps):
    if( rpsps < 0.167 or rpsps > 5461.167 ):
      self._log.error("ERROR: rpsps is out of range: " + str(rpsps))
      raise Exception("rpsps is out of range: " + str(rpsps))

  def set_acceleration_rate(self, rpsps):
    """ Minimum of 0.167 per manual """
    self.check_accl_range(rpsps)
    return(self.scl_send_command("AC" + (str)(rpsps)))
    
  def set_decceleration_rate(self, rpsps):
    self.check_accl_range(rpsps)
    return(self.scl_send_command("DE" + (str)(rpsps)))
    
  def get_acceleration_rate(self):
    return(self.scl_send_command("AC", 'value'))
    
  def get_decceleration_rate(self):
    return(self.scl_send_command("DE", 'value'))
    

  def set_jog_acceleration_rate(self, rpsps):
    self.check_accl_range(rpsps)
    return(self.scl_send_command("JA" + (str)(rpsps)))
    
  def set_jog_decceleration_rate(self, rpsps):
    self.check_accl_range(rpsps)
    return(self.scl_send_command("JL" + (str)(rpsps)))
    
  def get_jog_acceleration_rate(self):
    return(self.scl_send_command("JA", 'value'))
    
  def get_jog_decceleration_rate(self):
    return(self.scl_send_command("JL", 'value'))
    
  

  def commence_jogging(self):
    return(self.scl_send_command("CJ"))
    
  def stop_jogging(self):
    return(self.scl_send_command("SJ"))
    
  def stop_and_kill(self, decel_rate=""):
    return(self.scl_send_command("SK"+decel_rate))

  def move_distance(self, encoder_counts):
    return(self.scl_send_command("DI" + (str)(encoder_counts)))
    
  def feed_to_length(self, encoder_counts):
    return(self.scl_send_command("FL" + (str)(encoder_counts)))
    
  def feed_to_position(self, encoder_counts):
    self._log.info("Feeding to " + str(encoder_counts))
    self.target_position = encoder_counts
    return(self.scl_send_command("FP" + (str)(int(encoder_counts))))
    

  def is_at_target_position(self):
    """ Returns True if the motor is at the target position that it was last instructed to move to, False otherwise. """
    p = self.get_immediate_encoder_position()
    self._log.info("Checking position: " + str(p) + ", " + str(self.target_position))

    window = 40
    if( p < (self.target_position + window) and p > (self.target_position - window) ):
      return(True)
    return(False)


  def set_position_limit(self, encoder_counts):
    return(self.scl_send_command("PL" + (str)(encoder_counts)))

  def get_position_limit(self):
    return(self.scl_send_command("PL", 'value'))


  def set_motor_enable(self):
    return(self.scl_send_command("ME"))
    
  def set_motor_disable(self):
    return(self.scl_send_command("MD"))
 
  def stop(self):
    return(self.scl_send_command("ST"))


  def seek_home(self, append):
    return(self.scl_send_command("SH" + (str)(append)))

  def enable_input(self, append):
    return(self.scl_send_command("SI" + (str)(append)))
 

   
  def set_encoder_function(self, fv):
    return(self.scl_send_command("EF" + (str)(fv)))
    
  def get_encoder_function(self):
    return(self.scl_send_command("EF", 'value'))
    
  def set_position(self, fv):
    return(self.scl_send_command("SP" + (str)(fv)))

  def get_mechanical_gearing(self):
    return(self.mechanical_gearing)

  def set_mechanical_gearing(self, mg):
    self.mechanical_gearing = mg

  def get_angle(self):
    """ Calculates the current angle of the device the motor is controlling based on the known gear ratio and the electronic gearing set on the motor. """
    ep = self.get_immediate_encoder_position()
    #self._log.info("EP = " + str(ep) + ", self.motor_gearing = " + str(self.motor_gearing) + ", self.mechanical_gearing = " + str(self.mechanical_gearing))
    ang = float((float(ep) / float(self.motor_gearing)) * 360.0) / float(self.mechanical_gearing)
    return ang

  def set_angle(self, new_angle):
    """ Move the motor shaft such that the thing being controled is at a specific angle, factoring in the mechanical and electronic gearing set. """
    position = int(round((new_angle * self.mechanical_gearing / 360.0) * self.motor_gearing))
    #print("Feeding to position " + str(position) + " for new angle " + str(new_angle))
    self.feed_to_position(position)
    return

  def set_encoder_position(self, fv):
    return(self.scl_send_command("EP" + (str)(fv)))
    
  def get_encoder_position(self):
    return(self.scl_send_command("EP", 'value'))

  def get_immediate_encoder_position(self):
    return(self.scl_send_command("IE", 'value_hex_signed'))
    
  def set_encoder_resolution(self, fv):
    return(self.scl_send_command("ER" + (str)(fv)))
    
  def get_encoder_resolution(self):
    return(self.scl_send_command("ER", 'value'))
    
  def get_last_electronic_gearing(self):
    return(self.motor_gearing)

  def set_electronic_gearing(self, pulses_per_revolution):
    #200=1.8 degrees steps
    #400=0.9 degree steps
    #800=0.045 degree steps
    self.motor_gearing = pulses_per_revolution
    return(self.scl_send_command("EG" + (str)(pulses_per_revolution)))

  def get_immediate_current(self):
    return(self.scl_send_command("IC", 'value'))
    
  def get_immediate_temperature(self):
    return(self.scl_send_command("IT", 'value'))
    
  def get_immediate_voltage(self):
    return(self.scl_send_command("IU", 'value'))
    
  def get_immediate_velocity_actual(self):
    return(self.scl_send_command("IV0", 'value_hex_signed'))
    
  def get_immediate_velocity_target(self):
    return(self.scl_send_command("IV1", 'value'))

  def get_motor_current_rated(self):
    return(self.scl_send_command("MC", 'value'))
    
    
  def teardown(self):
    """ Function to stop the motor before disconnecting. """
    self.stop_jogging()
    self.close()

  def close(self):
    """ Close the socket used to communicate with the motor. """
    if( self.sock != None ):
      self.sock.close()
      self.sock = None

  def purge_rx_socket(self):
    """ Purges old data that has come in via UDP. """
    got_percent = False

    # Note: After sending the stop and kill command there are various packets that come back from the motor that need to be purged
    self.sock.settimeout(3)

    for i in range(1, 15):
      try:
        data = ""
        data, addr = self.sock.recvfrom(1024) 
        data = data.strip()
        self._log.info("Purged a packet from the RX socket: " + self.ip + ": '" + str(data) + "'")

        if( data.find("%") != -1 ):
          self._log.info("Got a percent...")
          got_percent = True
          break

      except socket.error:
        self._log.info("Timeout while purging RX socket, good...")
        break

    self.sock.settimeout(self.default_socket_timeout)

    self._log.info("Got percent = " + str(got_percent))
    return(got_percent)

  def scl_send_command(self, cmd, cmd_type = 'executed'):
    """ Helper function to handle sending commands to the motor and receiving and parsing data that came back. """

    # Note: the STM32 is modal. If you power it up and connect via TCP, it seems to got into TCP mode and no longer handles UDP. You have to reset it to get it back into UDP mode.
    pack_data = "BB" + (str)(len(cmd)) + "sc"
    #print("pack_data:", pack_data)
    #print("cmd:", str(cmd))
    command = pack(pack_data, 0, 7, cmd.encode('utf-8'), '\r'.encode('utf-8'))
    
    send_time = time.process_time()
    self._log.info((str(send_time) + ": UDP target IP:", self.ip, "UDP target port:", self.port, " CMD:", cmd))
    #print("Command:", command, ", Len = ", (str)(len(command)))

    if not self.sock.sendto(command, (self.ip, self.port)):
      raise Exception("Unable to send UDP command to motor")


    #time.sleep(0.010)
    data, addr = self.sock.recvfrom(1024) # buffer size is 1024 bytes
    data = bytearray(data)
    rx_time = time.process_time()
    cmd_time = rx_time - send_time

    #for i in range(0,len(data)):
    #  print("data[",i,"]= '",data[i],"'")
    self._log.debug("Raw data from datagram is '" + stm_ascii_only(data.rstrip()) + "'")

    # The ack for an executed command is a % and a buffered command is a asterix *
    if((cmd_type == 'executed' and data[2] != ord('%') and data[2] != ord('*')) ):
      self._log.error("ERROR: received message: '" + str(data) + "'")
      self._log.error("ERROR: received message: '" + str(data[1]) + "', " + cmd_type)
      raise Exception("Did not get expected response from " + str(self.ip) + ", '" + cmd_type + "' command '" + str(cmd) + "', Motor: '" + str(data) + "'")

    # Ack for executed command is *
    # Ack for buffered command is *

    if data[0] == 0 and data[1] == 7:
      data[0] = ord(' ')
      data[1] = ord(' ')

    data = data.decode('utf-8')
    data = data.strip()

    if cmd_type == 'value':
      data = re.sub('.*?=', '', data)
      
    data = data.strip()
    if( cmd_type == 'value' and re.match('^[0-9\.]+$', data) ):
      data = float(data)

    if( cmd_type == 'value_hex_signed' ):
      m = re.search('^.*=([0-9A-Z\.]+)$', data)
      if( m ) :
        #self._log.debug("Group is '" + str(m.group(1)) + "'")

        data = int(m.group(1),16)

        if data > 0x7FFFFFFF:
          data -= 0x100000000

        #self._log.debug("Data parsed is " + str(data))


    self._log.info(str(time.process_time()) + ": cmd_time = " + str(cmd_time) + " Return data is '" + stm_ascii_only(str(data)) + "'")
    return(data)



