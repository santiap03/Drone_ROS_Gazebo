# Drone_ROS_Gazebo_Parte1
Esto es un proyecto para la materia de Robótica dirigido al pregrado de ingeniería electrónica en la Universidad de Antioquia
en Medellín, Colombia. Los integrantes son Santiago Álvarez Pinzón & Ken Owashi Vallejo en supervisión del profesor Andrés
Fernando Pérez González.

Con esta guía, se podrá montar un drone en un ambiente virtual con el cual puede interactuar. El drone tiene la posibilidad
de manejarse por medio de consola a través de unos comandos que se dejan en este trabajo o si se desea un manejo más directo
igualmente se puede controlar usando un control de pc que disponga a la mano. También tiene desarrollado un controlador PID 
para que sea posible que el drone vaya solo hasta un punto deseado, sin embargo no es inteligente, así que no tiene la 
capacidad de evadir obstáculos en el camino. 

## Especificaciones
El trabajo se desarrolló en **Ubuntu 16.04.1 LTS** corriendo como sistema operativo del PC, no en máquina virtual. La versión de
ROS es **Kinetic** y el entorno virtual se ejecuta en **Gazebo7**. Los archivos de Python se corren en versión 2.7.

Ubuntu: http://old-releases.ubuntu.com/releases/16.04.4/

ROS: http://wiki.ros.org/kinetic/Installation/Ubuntu

Gazebo: http://gazebosim.org/tutorials?cat=install&tut=install_ubuntu&ver=7.0

## Pasos a seguir
1. Abrir una terminal de Ubuntu y crear el espacio de trabajo con `mkdir -p ~/<catkin_workspace>/src`
2. Ejecutar `cd ~/<catkin_workspace>` y luego `catkin_make`
3. Ejecutar `source devel/setup.bash`
4. Instalar las dependencias:`cd src`, `sudo apt-get install ros-kinetic-hector-*`, `sudo apt-get install ros-kinetic-ardrone-autonomy`
5. Este repositorio git clone https://github.com/angelsantamaria/tum_simulator.git
6. `cd ..` y `catkin_make`
