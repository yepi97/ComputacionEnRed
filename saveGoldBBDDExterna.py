#GroveStreams.com Python 3.2 Feed Example
#Demonstrates uploading two stream feeds using compression, JSON, and 
# a short URL (The org and api_key values are passed as cookies instead
# of as part of the URL)
#The GS API being used will automatically create a component with 
# two Random streams if they do not already exist
 
#This example uploads two stream feeds, random temperature and humidity
# samples every 10 seconds.
#A full "how to" guide for this example can be found at:
# https://www.grovestreams.com/developers/getting_started_helloworld_python.html
#It relies and the GroveStreams API which can be found here:
# https://www.grovestreams.com/developers/api.html#2

# License:
# Copyright 2014 GroveStreams LLC.
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at: http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
 
#GroveStreams Setup:
 
#* Sign Up for Free User Account - https://www.grovestreams.com
#* Create a GroveStreams organization
#* Enter the GroveStreams api key under "GroveStreams Settings" below  
#*    (Can be retrieved from a GroveStreams organization: 
#*     click the Api Keys toolbar button,
#*     select your Api Key, and click View Secret Key)
 
import time
from datetime import datetime
import json
import http.client
import io
import gzip
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.remote_connection import LOGGER, logging

if __name__ == '__main__':
    
    #GroveStreams Settings
    api_key = "82cb0f75-4fda-365b-adb7-cf11529d4166"    # Mirar en la web > API Key
    
    component_id = "valor oro"
    
	#Optionally compress the JSON feed body to decrease network bandwidth
    compress = True
    url = '/api/feed'
    
    #Connect to the server
    conn = http.client.HTTPConnection('www.grovestreams.com')
    

    op = webdriver.ChromeOptions()
    op.add_argument('headless')
    driver = webdriver.Chrome(options=op)
    url_gold = 'https://es.investing.com/commodities/gold'
    
    while True:
        driver.get(url_gold)
        valores = driver.find_elements(By.XPATH, '//div/div/div/div/div/div/div/div/div')
        val = valores[10].text
        gold_val = val[:9]
        goldNew = str(gold_val).replace(".", "").replace(",", ".")
        gold_val = float(goldNew)
        print("--------El valor del oro es: ",gold_val)
        
		
        #Assemble feed as a JSON string (Let the GS servers set the sample time)
        samples = []
        samples.append({'compId' : component_id, 'streamId' : 'gold', 'data' : gold_val })
        
        #Uncomment below to include the sample time - milliseconds since epoch
        #now = datetime.datetime.now()
        #sample_time = int(time.mktime(now.timetuple())) * 1000
        #samples = []
        #samples.append({ 'compId': component_id, 'streamId' : 'temperature', 'data' : temperature_val, 'time' : sample_time })
        #samples.append({ 'compId': component_id, 'streamId' : 'humidity', 'data' : humidity_val, 'time' : sample_time  })
        
        json_encoded = json.dumps(samples);
        
        try:      
            
            if compress:
                #Compress the JSON HTTP body
                body = gzip.compress(json_encoded.encode('utf-8'))
                print('Compressed feed ' + str(100*len(body) / len(json_encoded)) + '%')
                
                headers = {"Content-Encoding" : "gzip" , "Connection" : "close", 
                           "Content-type" : "application/json", "Cookie" : "api_key="+api_key}
                
                #GS limits feed calls to one per 10 seconds per outward facing router IP address
                #Use the ip_addr and headers assignment below to work around this 
                # limit by setting the below to this device's IP address
                #ip_addr = "192.168.1.72"
                #headers = {"Content-Encoding" : "gzip" , "Connection" : "close", "Content-type" : "application/json", "X-Forwarded-For" : ip_addr, "Cookie" : "api_key="+api_key}
                
            else:
                #No Compression
                body = json_encoded
                org = 'ComputacionEnRed'
                headers = {"Connection" : "close", "Content-type" : "application/json", "Cookie" : "org="+org+";api_key="+api_key}

                #GS limits calls to 10 per second per outward facing router IP address
                #Use the ip_addr and headers assignment below to work around this 
                # limit by setting the below to this device's IP address
                #ip_addr = "192.168.1.72"
                #headers = {"Connection" : "close", "Content-type" : "application/json", "X-Forwarded-For" : ip_addr, "Cookie" : "api_key="+api_key}
                
            print('Uploading feed to: ' + url)
            
            #Upload the feed to GroveStreams
            conn.request("PUT", url, body, headers)
              
			#Check for errors
            response = conn.getresponse()
            status = response.status
            
            if status != 200 and status != 201:
                try:
                    if (response.reason != None):
                        print('HTTP Failure Reason: ' + response.reason + ' body: ' + response.read().decode(encoding='UTF-8'))
                    else:
                        print('HTTP Failure Body: ' + response.read().decode(encoding='UTF-8'))
                except Exception as e:
                    print('HTTP Failure Status : %d' % (status) )
        
        except Exception as e:
            print('HTTP Failure: ' + str(e))
        
        finally:
            if conn != None:
                conn.close()
        
		#Pause for ten seconds
        time.sleep(120)
         
    # quit
    exit(0)