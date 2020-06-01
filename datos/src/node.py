#!/usr/bin/env python
#Developed on python 2.7

import rospy
from sensor_msgs.msg import NavSatFix
from gazebo_msgs.srv import GetModelState #library import section, including each type of message used in the program and math functions.
from geometry_msgs.msg import Twist
from simple_pid import PID
import tf
import numpy as np

class input_data(object):

    def __init__(self): #Suscription to the topic /fix to get GPS sensor data.
        self.lat = 0
        self.lon = 0
        self.alt = 0
	self.z_position=0
        rospy.Subscriber("/fix", NavSatFix, self.callback)


    def callback(self, msg): #Selfcallback function to update information each time a change is detected on the source.
        self.lat = (msg.latitude)
	self.lon=msg.longitude
	self.alt=msg.altitude
	
#----------------------------------------------------This function is used to get the information provided from Gazebo about the position from a certain model

def gms_client(model_name,relative_entity_name):#Args: model name to get data from and the specific link, in this case the link is '' since there's only one in the model.
    rospy.wait_for_service('/gazebo/get_model_state')#wait for the service to be available
    try:
        gms   = rospy.ServiceProxy('/gazebo/get_model_state', GetModelState) #Import the service definition.
        resp1 = gms(model_name,relative_entity_name)#Get model location data.
        return resp1
    except rospy.ServiceException, e: #Exception called whenever the service is unresponsive or unavailable.
        print "Service call failed: %s"%e

#---------------------------------------------------------------------------------------------
rospy.init_node("data")#incio nodo de velocidades #Data node creation.
pub   = rospy.Publisher('cmd_vel', Twist, queue_size=10) #Define the publication of the linear and rotational speed of the model.
datos = input_data()#GPS Data.
vel   = Twist() #Definition of the variable vel as a Twist message.
vel.linear.x  = 0
vel.linear.y  = 0
vel.linear.z  = 0   #Initialization of linear adnd rotational speed.
vel.angular.x = 0
vel.angular.y = 0
vel.angular.z = 0
#----------------------------------------------------------------------------------------------------------
desx  = -5
desy  = 10 #Initial desired location (desx,desy,desz) and desired yaw(d_yaw).
desz  = 3
d_yaw = 0
epsilon=1 #Tolerance for the square error.
s=0 #State variable for the routine section.
count=0 #Aux variable for time count.
#--------------------------------------------------------------------------------input options
print("Opciones: \n 1: Una posicion \n 2: rutina") 
opt=input() #Program mode option.
if opt==1: #The first mode requires a desired location (X,Y,Z) and proceeds to drive the drone to it.
    print("Posicion X")
    desx=input()
    print("Posicion Y")
    desy=input()
    print("Posicion Z")
    desz=input()
    print("Desplazandose a la posicion: ", desx,desy,desz)
if opt==2: #The second option starts a routine of positions around the map to show the program capabilities.
    print("Iniciando rutina")
#---------------------------------PID Controllers, defined with the function PID that requires Proportional, integral and derivative constants along with the setpoint.
pid  = PID(1, 0.1, 0.05, setpoint=desz)#Controller z
pid2 = PID(1, 0.1, 0.05, setpoint=desx)#Controller x
pid3 = PID(1, 0.1, 0.05, setpoint=desy)#Controller y 
pid4 = PID(1, 0.1, 0.05, setpoint=0)#Controller yaw
pid.output_limits = (-1, 1)
pid2.output_limits = (-1, 1)#Limits the max controller output, since the model control plugin receives Twist data ranged from -1 to 1.
pid3.output_limits = (-1, 1)
pid4.output_limits = (-0.5, 0.5)
def angles(): #This function reads the orientation data quaternion(x,y,z,w) and returns the corresponding euler angles  
	quaternion = ( #Quaternion definition 
	q.pose.orientation.x,
        q.pose.orientation.y,
	q.pose.orientation.z,
	q.pose.orientation.w)
	euler = tf.transformations.euler_from_quaternion(quaternion) #Transformation function included in TF library.
	roll = euler[0]
	pitch = euler[1]
	yaw = euler[2]
	return(roll, pitch, yaw)#Euler angles.
def dyaw(): #Function to calculate the yaw angle to point to the desired position.
	temp=(desy-q.pose.position.y)/(desx-q.pose.position.x)
	d_yaw=np.arctan(temp)
	if (desy-q.pose.position.y)<0 and (desx-q.pose.position.x)<0:
		d_yaw=d_yaw-np.pi
	if (desy-q.pose.position.y)>0 and (desx-q.pose.position.x)<0:
		d_yaw=d_yaw+np.pi
	if np.abs(d_yaw-y)>np.pi: #This condition is used to avoid the angle discontinuity and produce smoother and faster responce.
		if y<0:
			d_yaw=d_yaw-2*np.pi #In case the polarity change goes from negative to positive.
		if y>0:
			d_yaw=d_yaw+2*np.pi #In case the polarity change goes from positive to negative.
	#print np.abs(d_yaw-y)
	return d_yaw
def conversion(): #Rotation function for desired position (X,Y,Z) and actual position into the Drone's coordinate system depending on Yaw angle.
	dx=desx*np.cos(y)+desy*np.sin(y) #Rotation matrix
	dy=-desx*np.sin(y)+desy*np.cos(y)
	dz=desz
	ax= q.pose.position.x*np.cos(y)+q.pose.position.y*np.sin(y) #Rotation matrix
	ay= -q.pose.position.x*np.sin(y)+q.pose.position.y*np.cos(y)
	az= q.pose.position.z
	return dx,dy, dz, ax, ay, az

def pid_update(): #Each time the Yaw angle and location changes, the PID controller's setpoint is updated.
	    # PID z
	v1=(q.pose.position.z)
    	vel.linear.z = pid(v1)
#	  # PID X
	v2=(ax)
    	vel.linear.x = pid2(v2)
	  # PID Y
	v3=(ay)
    	vel.linear.y = pid3(v3)
	  # PID yaw
	v4=y
    	vel.angular.z = pid4(v4)
def one_position(): #Function to stop the one position routine with a fixed yaw angle.
	 global d_yaw
	 e=np.sqrt((dx-ax)**2+(dy-ay)**2+(dz-az)**2)
	 if e<epsilon: #Ending condition.
		d_yaw=0
	 else:
		d_yaw=dyaw()



	
def secuencia(): #Function to excecute a state machine that controls the routine for the drone to perform across the map.
	global s, count, desx, desy, desz,d_yaw
        if s==0:  
		status(5,5,6, 0)
	if s==1:
		status(2,2,2, -2.7)	
	if s==2:
		status(3,-1,5,-1.5)
	if s==3:
		status(2,-12,5,-1.5)	
	if s==4:
		status(-12,-11,5,3)
	if s==5:
		status(-12,2,8,1.5)
	if s==6:			
		status(-12,2,6.5,0)	
	if s==7:	
		status(-1.5,2,6.5,0)
	if s==8:
		status(-14,7.5,6,3)	
	if s==9:
		status(-14,7.5,4,3)
	if s==10:
		status(-14,7.5,2,0)			
def status(x,ydes,z, d): #Function used to move the Drone to a certain position (x,ydes,z) and stabilization angle d.
	#print(s)
	global s, count, desx, desy, desz,d_yaw, y
	e=np.sqrt((dx-ax)**2+(dy-ay)**2+(dz-az)**2)
	if e<epsilon: #Stabilization of yaw angle on d.
		d_yaw=d 
		#print y #np.abs(d_yaw-y)
		if np.abs(d_yaw-y)>np.pi: #Discontinuity avoid condition.
			if y<0:
				d_yaw=d_yaw-2*np.pi
			if y>0:
				d_yaw=d_yaw+2*np.pi

 	else:
		d_yaw=dyaw()	#Since the the Drone is not at the desired position, the desired yaw is the the angle of approach to destiny.
	if e<epsilon+1:		#The drone is within the required limit range for stabilization.
		print "cuenta estabilizacion: ", count
		count=count+1
		if count==5000:	 #Counts a stabilization time in the range.	
			s=s+1
			print "next" "Status update and next position set"
			desx=x
			desy=ydes
			desz=z
			count=0	 #Stabilization time reset	
	else: 
		count=0
	
#-----------------------------------------------------------------------
while not rospy.is_shutdown():
	q= gms_client('quadrotor', '')#Update of the model position q.
	r,p,y= angles() #Euler angles (Roll, pitch and yaw) calculation.
	dx, dy, dz, ax, ay, az= conversion() #Transformation of the desired and actual position to drone's coordinate system.
	if opt==1:	#Excecution mode.
		one_position()

	if opt==2:
		secuencia()

	pid_update() 	#PID controllers update.
	pid4.setpoint = d_yaw 
	pid2.setpoint = dx #Controller's setpoint update.
	pid3.setpoint = dy
	pid.setpoint = dz
	pub.publish(vel)#Publish the vel data on the topic /cmd_vel
