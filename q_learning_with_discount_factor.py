#!/usr/bin/python
#
#    license-generator
#    Copyright (C) 2015-16  Sibi Sankar <http://sibisankar.me>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
#
#

# Libraries Imports

import numpy as np,pylab
import itertools
import random,sys


# Global variables declaration
# Actions sequences Charge | Discharge
# Discretising Solar Power, Battery Level and Discharge rate into states (Larger the number of states larger the lookup table)
# PWT -- 4 states
# Battery Level -- 6 states
# Discharge Rate -- 4 states
# 96 possible scenarios based on Pwt,Dt,Batterylevel of the form eg 1|3|2, 1|1|6, 2|2|4 with combination value of 4*4*6


# HyperParameters
# Prediction belief
discount_factor = 0.8

#Learning/exploring ratio
exploration_ratio = 0.6

# Battery Parameters
# Battery is modeled as follows:
# It can charge a maximum of 1000 units per unit time
# It can charge a maximum of 1000 units per unit time
# It can only charge or discharge per unit time


Bmax = 6000
Blevel = 0

# Data initialised for plotting
histogram_data=[]
Solar_power_utilised=[]
Load_delivered=[]



# QvalTable Object
# Function approx using Lookup Table


class QvalTable(object):

    def __init__(self,alpha,gamma):
		self.Q_val_table=np.zeros((2,96))
		'Tuning Learning Rate'
		self.alpha=0.6
		'Tuning Discount Rate'
		self.gamma=0.4

    def get_max_index(self,col):
		return np.argmax(self.Q_val_table[:,col])

    def update_qtable(self,reward,row,col,u_b_level):
		next_max=self.get_next_max_val(u_b_level)
		self.Q_val_table[row,col]= self.Q_val_table[row,col] +self.alpha*(reward + self.gamma*(next_max)- self.Q_val_table[row,col])

	def get_next_max_val(self,level):
		temp=[]
		code=Sortb_level(level,6000)
		states=map_action(int(code))
		for i in scenario_dict:
			if i[-1] in states:
				temp.append(max(self.Q_val_table[:,scenario_dict[i]]))
		return max(temp)
        
	def __str__(self):
		print self.Q_val_table

# State Mapping

def map_action(code):
    map_action={0:'1',1:'02',2:'13',3:'24',4:'35',5:'4'}
        return map_action[code]

# Load Data

def Load_Data(filedir):
	temp=[]
	tempfile=open(filedir,'r')
	chunk=tempfile.readlines()
	for i in range(len(chunk)):
		temp.append(float(chunk[i]))
	return temp


# Scenario Creation

def scenario_creation(plevels,blevels):
	dic={}
	p_level_list=[str(i) for i in range(plevels)]
	b_level_list=[str(i) for i in range(blevels)]
	lst = [p_level_list,p_level_list,b_level_list]
	temp=["|".join([p, q, r]) for p, q, r in itertools.product(*lst)]
	for i in range(len(temp)):
		dic[temp[i].replace("|","")]=i
	return dic

# Mapping PD: Value to Index'

def Sortpd_level(level,levelmax):
	temp=''
	if 0<=level<=(levelmax/4.):
		temp='0'
	elif (levelmax/4.)<level<=(levelmax/2.):
		temp='1'
	elif (levelmax/2.)<level<=((levelmax*3)/4.):
		temp='2'
	else:
		temp='3'
	return temp

# Mapping Battery Level: Value to Index

def Sortb_level(level,levelmax):
	temp=''
	if 0.<=level<=(levelmax/6.):
		temp='0'
	elif (levelmax/6.)<level<=(2*levelmax/6.):
		temp='1'
	elif (2*levelmax/6.)<level<=(3*levelmax/6.):
		temp='2'
	elif (3*levelmax/6.)<level<=(4*levelmax/6.):
		temp='3'
	elif (4*levelmax/6.)<level<=(5*levelmax/6.):
		temp='4'
	else:

		temp='5'
	return temp


def Getc_Code(pwt,dwt,blevel):
	tempP=Sortpd_level(pwt,7000)
	tempD=Sortpd_level(dwt,4000)
	tempB=Sortb_level(blevel,6000)
	return tempP+tempD+tempB


def Getr_Code(lrat,code):
	if random.random() > lrat:
		return action_dict.keys()[action_dict.values().index(random.randint(0,1))]
	else:
		colnum=scenario_dict[code]
		temp=Qvalobj.get_max_index(colnum)
		return action_dict.keys()[action_dict.values().index(temp)]

def Plot_Hist(data):
	pylab.hist(data, bins=96)
	pylab.show()



# Loading data from file
# Setting seed for reproduceablity of results
# Normal distribution with mean 600 and standard deviation of size 8760
# 1 - charging 0- discharging
# Dictionary containing the number of scenarios
# Dictionary conataining action
# Creation of the QvalTableObject

# Uncomment to Test Behavior with constant seed
#random.seed(1)
#np.random.seed(1)

# Data Initialisation
Pwt=Load_Data('PWT.mat')
Dt =Load_Data('Dtlist.mat')
scenario_dict = scenario_creation(4,6)
action_dict = {'1':1,'0':0}
Qvalobj=QvalTable(0.8,0.8)
solarlist=[]
loadlist=[]
powerutil=[]
qlist=[]

for k in range(100):
	for j in range(1):
		for i in range(len(Pwt)):
			Ccode=Getc_Code(Pwt[i],Dt[i],Blevel)
			Rcode=Getr_Code(0,Ccode)
			histogram_data.append(scenario_dict[Ccode])
			action=int(Rcode)

			tekkai=(action*(min(Bmax-Blevel,Pwt[i])))+((1-action)*(min(Dt[i],Blevel)))
			reward=((action*(min(Bmax-Blevel,Pwt[i])))+((1-action)*(min(Dt[i],Blevel))))
			flow  =action*(tekkai) + (1-action)*(-tekkai)
			Blevel+=flow
			Qvalobj.update_qtable(reward,action_dict[Rcode],scenario_dict[Ccode],Blevel)

			if flow<0:
				Load_delivered.append(flow)
			else:
	 		  Solar_power_utilised.append(flow)
	temp=np.copy(Qvalobj.Q_val_table)
	qlist.append(temp)
	temp=0
	solarlist.append(round(sum(Solar_power_utilised)/(sum(Pwt)*(j+1)),2))
	loadlist.append(round(-1*sum(Load_delivered)/((j+1)*sum(Dt)),2))
	powerutil.append(round((sum(Dt))-(sum(Solar_power_utilised)/(j+1)),2))
	Solar_power_utilised=[]
	Load_delivered=[]

print 'Learning Period Over with following statistics:'
print solarlist
print loadlist
print powerutil

# Plot Data using Pylab
#pylab.ylim(0,1.0,'k')
pylab.plot(range(len(solarlist)),solarlist)
pylab.show()
#pylab.ylim(0,1.0)
pylab.plot(range(len(loadlist)),loadlist,'k')
pylab.show()
#pylab.ylim(0,1.0)
pylab.plot(range(len(powerutil)),powerutil,'k')
pylab.show()
Plot_Hist(histogram_data)


# Validation of Learnt Knowledge Depending only on Q-val table for descision making'
histogram_data=[]
Load_delivered=[]
Solar_power_utilised=[]

for k in range(1):
	for j in range(1):
		for i in range(len(Pwt)):
			Ccode=Getc_Code(Pwt[i],Dt[i],Blevel)
			Rcode=Getr_Code(1.0,Ccode)
			histogram_data.append(scenario_dict[Ccode])
			action=int(Rcode)
			reward=(action*(min(Bmax-Blevel,Pwt[i])))+((1-action)*(min(Dt[i],Blevel)))
			flow  =action*(reward) + (1-action)*(-reward)
			Blevel+=flow
			if flow<0:
				Load_delivered.append(flow)
			else:
				Solar_power_utilised.append(flow)
	solarlist.append(round(sum(Solar_power_utilised)/((j+1)*sum(Pwt)),2))
	loadlist.append(round(-1*sum(Load_delivered)/((j+1)*sum(Dt)),2))
	powerutil.append(round(sum(Dt)-(sum(Solar_power_utilised)/(j+1)),2))
	Solar_power_utilised=[]
	Load_delivered=[]
print 'Execution Period Over with following statistics:'
print (solarlist)
print (loadlist)
print powerutil
#pylab.ylim(0,1.0)
pylab.plot(range(len(solarlist)),solarlist,'k')
pylab.show()
#pylab.ylim(0,1.0)
pylab.plot(range(len(loadlist)),loadlist,'k')
pylab.show()
#pylab.ylim(0,1.0)
pylab.plot(range(len(powerutil)),powerutil,'k')
pylab.show()
Plot_Hist(histogram_data)


print len(qlist)

for i in range(len(qlist)):
	#np.savetxt('test.txt', qlist[i])
	#print np.sum(np.sum((qlist[0]-qlist[1])))/(2*96.0)

	if 0<= i < len(qlist)-2:
		print np.sum(np.sum((qlist[i]-qlist[i+1]))/(2*96.0))

'''
for i in range(24):
	print Pwt[i],Dt[i],Blevel
	Ccode=Getc_Code(Pwt[i],Dt[i],Blevel)
	print Ccode
	Rcode=Getr_Code(1.0,Ccode)
	action= int(Rcode)
	reward=(action*(min(Bmax-Blevel,Pwt[i])))+((1-action)*(min(Dt[i],Blevel)))
	flow  =action*(reward) + (1-action)*(-reward)
	Blevel+=flow
'''
