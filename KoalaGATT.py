"""Nicholas Farn and Alan Chen
Connected World Technologies Laboratory at National Chiao Tung Univeristy
To be used with a Koala Sensor
Please mess around with the code, I've left notes to try and help understand my implementation
Plus there invariably are going to be some bugs here or there
"""

from subprocess import *
import re

# regex for mac address
MAC_REGEX = re.compile('^([a-fA-F]|\d){2}:([a-fA-F]|\d){2}:([a-fA-F]|\d){2}:([a-fA-F]|\d){2}:([a-fA-F]|\d){2}:([a-fA-F]|\d){2}$')

# use these UUIDs in order to get information from the Koala
MOTION_SERVICE = 'eb371600-347c-fe94-1600-8295a1e42b09'
MOTION_MEASUREMENT_CHARACTERISTIC = 'eb371601-347c-fe94-1600-8295a1e42b09'
MOTION_PARAM_CHARACTERISTIC = 'eb371602-347c-fe94-1600-8295a1e42b09'

class KoalaException(Exception):
	COMM_ERROR = 1
	INTERNAL_ERROR = 2
	
	def __init__(self, code, message):
		self.code = code
		self.message = message
	
	def __str__(self):
		return self.message

# the class does not continuously connect with the Koala, rather each method establishes a connection
# and read and writes to the Koala
class Koala():
	# takes in MAC address of Koala device in order to initialize
	def __init__(self, addr):
		if MAC_REGEX.match(addr) is not None:
			self.addr = addr
		else:
			raise KoalaException(KoalaException.INTERNAL_ERROR, 'Mac Address improperly formatted')
		
	# returns all services available for the Koala Device
	# returns their uuid, start, and end handles
	# if uuid is specified, it returns the start and end handles of that service
	# results are returned as a dictionary with the uuid as the key and the handles as hex strings
	def getServices(self, uuid=None):
		command = ['sudo', 'gatttool', '-t', 'random', '-b', self.addr, '--primary']
		if uuid is not None:
			# TODO check if uuid is properly formatted
			command.append('-u')
			command.append(uuid)
		
		p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, bufsize=1)
		(out, err) = p.communicate()
		
		if err is not None:
			if len(err) > 0:
				raise KoalaException(KoalaException.COMM_ERROR, 'failed to retrieve services from Koala')
		
		# processing output
		if uuid is None:
			lines = out.split('\n')
			services = {}
			
			# parsing response line by line
			for line in lines:
				start = None
				end = None
				serviceUUID = None
				tokens = line.split(' ')
				if len(tokens) > 1:
					# parsing line for start and end handles plus uuid
					# TODO handle case where tokens do not match what is expected
					for i in range(len(tokens)):
						if tokens[i].rstrip() == 'attr':
							start = tokens[i+3].rstrip().rstrip(',')
						elif tokens[i].rstrip() == 'grp':
							end = tokens[i+3].rstrip()
						elif tokens[i] == 'uuid:':
							serviceUUID = tokens[i+1].rstrip()
					
					# adding results to services
					if ((start is not None) and (end is not None)) and (serviceUUID is not None):
						services[serviceUUID] = [start, end]
			return services
		else:
			handles = []
			tokens = out.split(' ')
			
			# parsing response for start and end handles
			for i in range(len(tokens)):
				if tokens[i].rstrip() == 'Starting':
					handles.append('0x' + tokens[i+2].rstrip())
				elif tokens[i].rstrip() == 'Ending':
					handles.append('0x' + tokens[i+2].rstrip())
			return handles
				
	# finds all characteristics, returning their uuid's along with their handles
	# if a start and end handle are specified, returns all characteristics in that range
	# start and end handles should be given as hex strings
	def getCharacteristics(self, startHnd=None, endHnd=None):
		command = ['sudo', 'gatttool', '-t', 'random', '-b', self.addr, '--characteristics']
		if (startHnd is not None) and (endHnd is not None):
			command.append('-s')
			command.append(startHnd)
			command.append('-e')
			command.append(endHnd)
		p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, bufsize=1)
		(out, err) = p.communicate()
		
		if err is not None:
			if len(err) > 0:
				raise KoalaException(KoalaException.COMM_ERROR, 'failed to retrieve characteristics from Koala')
		
		# processing output
		lines = out.split('\n')
		# parsing line by line
		characteristics = {}
		for line in lines:
			charUUID = None
			handle = None
			charHandle = None
			properties = None
			
			# parsing response for uuid, start and end handles, and properties
			tokens = line.split(' ')
			for i in range(len(tokens)):
				if tokens[i].rstrip() == 'handle':
					if tokens[i+3].rstrip() == 'char':
						handle = tokens[i+2].rstrip().rstrip(',')
					else:
						charHandle = tokens[i+2].rstrip().rstrip(',')
				elif tokens[i].rstrip() == 'uuid':
					charUUID = tokens[i+2].rstrip()
				elif tokens[i].rstrip() == 'properties':
					properties = tokens[i+2].rstrip().rstrip(',')

			if ((charUUID is not None) and (properties is not None)) and ((handle is not None) and (charHandle is not None)):
				characteristics[charUUID] = [handle, charHandle, properties]
		return characteristics
	
	# finds all characteristics under a service specified by UUID
	def getServiceCharacteristics(self, uuid):
		handles = self.getServices(uuid)
		return self.getCharacteristics(handles[0], handles[1])
	
	# retrieves characteristic by its uuid
	def getCharacteristicByUUID(self, uuid):
		command = ['sudo', 'gatttool', '-t', 'random', '-b', self.addr, '--characteristics', '-u', uuid]
		p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, bufsize=1)
		(out, err) = p.communicate()
		
		if err is not None:
			if len(err) > 0:
				raise KoalaException(KoalaException.COMM_ERROR, 'failed to retrieve characteristic from Koala')
		
		# processing output
		characteristic = {}
                charUUID = None
                handle = None
                charHandle = None
                properties = None
                
                tokens = out.split(' ')
		# parsing response for uuid, start and end handles, and properties
	        for i in range(len(tokens)):
		        if tokens[i].rstrip() == 'handle':
		              	if tokens[i+3].rstrip() == 'char':
		                      	handle = tokens[i+2].rstrip().rstrip(',')
		                else:
		                       	charHandle = tokens[i+2].rstrip().rstrip(',')
		        elif tokens[i].rstrip() == 'uuid':
		             	charUUID = tokens[i+2].rstrip()
		        elif tokens[i].rstrip() == 'properties':
		                properties = tokens[i+2].rstrip().rstrip(',')
		if ((charUUID is not None) and (properties is not None)) and ((handle is not None) and (charHandle is not None)):
		        characteristic[charUUID] = [handle, charHandle, properties]
		
		if len(characteristic) > 0:
			return characteristic
		else:
			raise KoalaException(KoalaException.INTERNAL_ERROR, 'invalid UUID')

	# retrieves characteristic by its handle
	def getCharacteristicByHandle(self, handle):
		characteristic = self.getCharacteristics(handle, handle)
		if len(characteristic) > 0:
			return characteristic
		else:
			raise KoalaException(KoalaException.INTERNAL_ERROR, 'invalid UUID')
	
	# NOTE: since gatttool does not support listening for notifications while in interactive mode, (necessary for a continuous connection)
	# there are no write characteristics methods since any characteristics written will be wiped after the gatttool command executes and disconnects
	
	# reads a characteristic specified by its uuid
	def readCharacteristicByUUID(self, uuid):
		characteristic = self.getCharacteristicByUUID(uuid)
		if len(characteristic) > 0:
			return self.readCharacteristicByHandle(characteristic[characteristic.keys()[0]][1])
		else:
			raise KoalaException(KoalaException.INTERNAL_ERROR, 'invalid UUID')
	
	# reads a characteristic specified by its handle
	def readCharacteristicByHandle(self, handle):
		command = ['sudo', 'gatttool', '-t', 'random', '-b', self.addr, '--char-read', '-a', handle]
		p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, bufsize=1)
		(out, err) = p.communicate()
		
		if err is not None:
			if len(err) > 0:
				raise KoalaException(KoalaException.COMM_ERROR, 'failed to read characteristic')
		
		# processing output
		raw = out.split(':')[1].split(' ')
		readings = []
		for value in raw:
			reading = value.rstrip()
			if len(reading) == 2:
				readings.append(reading)
		
		return readings
        
	# retrieves CCCD handles from a service uuid
	def getServiceCCCDs(self, uuid):
		# get start and end handles from uuid
		handles = self.getServices(uuid)
		# find handles matching uuid of 2902
		command = ['sudo', 'gatttool', '-t', 'random', '-b', self.addr, '--char-read', '-u', '0x2902', '-s', handles[0], '-e', handles[1]]
		p = Popen(command, stdin=PIPE, stdout=PIPE, stderr=STDOUT, bufsize=1)
		(out, err) = p.communicate()
		
		if err is not None:
			if len(err) > 0:
				raise KoalaException(KoalaException.COMM_ERROR, 'failed to retrieve service CCCDs from Koala')
		
		# processing output
		handles = []
		
		lines = out.split('\n')
		for line in lines:
			tokens = line.split(' ')
			# parsing string for CCCD handles
			for i in range(len(tokens)):
				if tokens[i].rstrip() == 'handle:':
					handles.append(tokens[i+1].rstrip())
		return handles
	
	# NOTE: gatttool does not provide an easy command to determine a characteristic's CCCD handle
	# thus these methods are the most expensive since they require calling multiple other methods
	# it is easier to determine what handle control which characteristic beforehand and use that
	# to enable notifications. For similar reasons the listenForNotifications methods are also expensive.
	# As such another method that takes in the CCCD handle directly is provided and is much faster.
	# In order to determine a list of potential CCCD handles, simply use getServiceCCCDs and input
	# the service UUID that the characteristic is under. The correct CCCD handle should be a value
	# one above the characteristic handle. If there is no such handle, then that indicates that the
	# characteristic probably does not support notifications and indications.
	
	# retrieves CCCD handle from a characteristic UUID
	def getCharacteristicCCCDByUUID(self, uuid):
		characteristic = self.getCharacteristicByUUID(uuid)
		if len(characteristic) > 0:
			return self.getCharacteristicCCCDByHandle(characteristic[characteristic.keys()[0]][1])
		else:
			raise KoalaException(KoalaException.INTERNAL_ERROR, 'invalid UUID')
	
	# retrieves CCCD handle from a characteristic handle
	def getCharacteristicCCCDByHandle(self, handle):
		# finding service characteristic falls under
		services = self.getServices()
		serviceUUID = None
		
		handleValue = int(handle, 16)
		for key in services.keys():
			if (int(services[key][0], 16) <= handleValue) and (int(services[key][1], 16) >= handleValue):
				serviceUUID = key
		
		# finding list of potential CCCDs
		cccds = self.getServiceCCCDs(serviceUUID)
		for cccd in cccds:
			if handleValue + 1 == int(cccd, 16):
				return cccd
		else:
			raise KoalaException(KoalaException.INTERNAL_ERROR, 'characteristic does not have a CCCD or improper handle')
	
	# NOTE: due to how it is implemented, notifications can only be recieved from one characteristic per a device
	# Fortunately this is good for the Koala since only the Motion Measurement Characteristic needs to be listened to
	
	# listens for notifications from a characteristic specified by its UUID for a period of time
	# if no time is specified, a single reading is returned
	def listenForNotificationsByUUID(self, uuid, time):
		cccd = self.getCharacteristicCCCDByUUID(uuid)
		return self.listenForNotificationsByCCCD(cccd, time)
	
	# listens for notifications from a characteristic specified by its handle for a period of time
	def listenForNotificationsByHandle(self, handle, time):
		cccd = self.getCharacteristicCCCDByHandle(handle)
		return self.listenForNotificationsByCCCD(cccd, time)
	
	# listens for notifications from a characteristic specified by its CCCD for a period of time
	def listenForNotificationsByCCCD(self, cccd, time):
		command = ['sudo', 'timeout', str(time), 'gatttool', '-t', 'random', '-b', self.addr, '--char-write-req', '-a', cccd, '-n', '0100', '--listen']
                p = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, bufsize=1)
                (out, err) = p.communicate()

                if err is not None:
                        if len(err) > 0:
	                        raise KoalaException(KoalaException.COMM_ERROR, 'failed to enable notifications')
		
		# processing output
		data = []
		lines = out.split('\n')
		for line in lines:
			raw = line.split(':')
			if len(raw) == 2:
				point = []
				raw = raw[1]
				readings = raw.split(' ')
				for reading in readings:
					temp = reading.rstrip()
					if len(temp) == 2:
						point.append(temp)
				data.append(point)
                return data

	# NOTE: indications are not implemented in this class. However they are fairly easy to enable
	# simply write a value of 0200 to the characteristic's CCCD. Write a value of 0300 to enable
	# both notifications and indications, and a value of 0000 in order to disable everything.
