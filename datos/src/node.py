#!/usr/bin/env python

import rospy
from sensor_msgs.msg import NavSatFix
from gazebo_msgs.srv import GetModelState
from geometry_msgs.msg import Twist
from simple_pid import PID
import copy
import tf
import numpy as np
import time


#Instalar el controlador pid https://pypi.org/project/simple-pid/

#
class input_data(object):

    def __init__(self): #suscripcion al topic fix para datos gps
        self.lat = 0
        self.lon = 0
        self.alt = 0
	self.z_position=0
        rospy.Subscriber("/fix", NavSatFix, self.callback)


    def callback(self, msg):
        self.lat = (msg.latitude)
	self.lon=msg.longitude
	self.alt=msg.altitude
	
#--------------------------------------------------------lectura model position

def gms_client(model_name,relative_entity_name):
    rospy.wait_for_service('/gazebo/get_model_state')
    try:
        gms = rospy.ServiceProxy('/gazebo/get_model_state', GetModelState)
        resp1 = gms(model_name,relative_entity_name)
        return resp1
    except rospy.ServiceException, e:
        print "Service call failed: %s"%e

#---------------------------------------------------------------------------------------------
rospy.init_node("data")#incio nodo de velocidades 
pub = rospy.Publisher('cmd_vel', Twist, queue_size=10)
datos=input_data()#creacion estructura de datos
vel=Twist()
vel.linear.x = 0
vel.linear.y = 0
vel.linear.z = 0
vel.angular.x = 0
vel.angular.y = 0
vel.angular.z = 0
#-------------------------------------------------------Controladores pid---------------------------------------------------
desx=-5
desy=10 #valores deseados y tolerancia
desz=3
d_yaw=0
epsilon=1
s=0
count=0
#---------------------------------
pid = PID(1, 0.1, 0.05, setpoint=desz)#controlador z
pid2 = PID(1, 0.1, 0.05, setpoint=desx)#controlador x
pid3 = PID(1, 0.1, 0.05, setpoint=desy)#controlador y 
pid4 = PID(1, 0.1, 0.05, setpoint=0)#controlador yaw
pid.output_limits = (-1, 1)
pid2.output_limits = (-1, 1)
pid3.output_limits = (-1, 1)
pid4.output_limits = (-0.5, 0.5)
def angles(): #funcion para obtener angulos de euler a partir del cuaternion de orientacion
	quaternion = (
	q.pose.orientation.x,
        q.pose.orientation.y,
	q.pose.orientation.z,
	q.pose.orientation.w)
	euler = tf.transformations.euler_from_quaternion(quaternion)
	roll = euler[0]
	pitch = euler[1]
	yaw = euler[2]
	return(roll, pitch, yaw)
def dyaw(): #Funcion para obtener el angulo de yaw necesario para que el dron apunte constantemente al destino
	temp=(desy-q.pose.position.y)/(desx-q.pose.position.x)
	d_yaw=np.arctan(temp)
	if (desy-q.pose.position.y)<0 and (desx-q.pose.position.x)<0:
		d_yaw=d_yaw-np.pi
	if (desy-q.pose.position.y)>0 and (desx-q.pose.position.x)<0:
		d_yaw=d_yaw+np.pi
	if np.abs(d_yaw-y)>np.pi:
		if y<0:
			d_yaw=d_yaw-2*np.pi
		if y>0:
			d_yaw=d_yaw+2*np.pi
	#print np.abs(d_yaw-y)
	return d_yaw
def conversion(): #Funcion de conversion de las coordenadas actuales y de destino al sistema de referencia del drone segun el yaw 
	dx=desx*np.cos(y)+desy*np.sin(y)
	dy=-desx*np.sin(y)+desy*np.cos(y)
	dz=desz
	ax= q.pose.position.x*np.cos(y)+q.pose.position.y*np.sin(y)
	ay= -q.pose.position.x*np.sin(y)+q.pose.position.y*np.cos(y)
	az= q.pose.position.z
	return dx,dy, dz, ax, ay, az

def pid_update():
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
def one_position():
	 if np.sqrt((dx-ax)**2+(dy-ay)**2+(dz-az)**2)<epsilon: #condicion de terminacion para estabilizar el yaw
		d_yaw=0
	 else:
		d_yaw=dyaw()

	
def secuencia():
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
def status(x,ydes,z, d):
	print(s)
	global s, count, desx, desy, desz,d_yaw, y
	e=np.sqrt((dx-ax)**2+(dy-ay)**2+(dz-az)**2)
	if e<epsilon:
		d_yaw=d
		print y#np.abs(d_yaw-y)
		if np.abs(d_yaw-y)>np.pi:
			if y<0:
				d_yaw=d_yaw-2*np.pi
			if y>0:
				d_yaw=d_yaw+2*np.pi

 	else:
		d_yaw=dyaw()	
			
	#print e
	if e<epsilon+1:		
		print "cuenta estabilizacion: ", count
		count=count+1
		if count==5000:		
			s=s+1
			print "next"
			desx=x
			desy=ydes
			desz=z
			count=0			
	else: 
		count=0
	
#-----------------------------------------------------------------------
while not rospy.is_shutdown():
	q= gms_client('quadrotor', '')#obtencion de datos de posicion en q
	r,p,y= angles() #obtencion de angulos de euler roll pitch yaw
	dx, dy, dz, ax, ay, az= conversion() #conversion por matrices de rotacion en funcion del yaw para posicion actual y deseada
	#one_position()
	secuencia()
	pid_update() 	
	pid4.setpoint = d_yaw #actualizacion del setpoint del yaw en funcion de las coordenadas actuales
	pid2.setpoint = dx #actualizacion del setpoint del destino en funcion del yaw
	pid3.setpoint = dy
	pid.setpoint = dz
	pub.publish(vel)#publicador del topic que contiene las velocidades
	#print s
	#print np.sqrt(((dx-ax)**2+(dy-ay)**2))
	#print q.pose.position.x
	#print q.pose.position.y
	#print 'cx: ', dx
	#print 'cy', dy
	#print d_yaw 
	#print 'yaw: ', y
	#print (q.pose)
	#print 'header'
	#print 'lat:', datos.lat
	#print 'lon:', datos.lon
	#print 'alt:', datos.alt





