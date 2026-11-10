import serial
import csv
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


#opens serial port
ser = serial.Serial("COM3", 115200, timeout=1)

#creates lists
timeL = []
temp = []
hum = []
prec = []
light = []
soilM = []


#sets howmany records I want to add
max_records = 370
count = 0

csv_file = 'sensor_data.csv'
#opens csv file and writes data from serial port
with open(csv_file, 'a', newline='') as csvfile:
    writer = csv.writer(csvfile)
    header = ['Time','Light','Temperature','Humidity','Soil Moisture','Precipitation']
    writer.writerow(header)

    #reads lines from serial port until max_records is reached
    while count < max_records:
        if ser.in_waiting: #checks if there is data waiting in the serial buffer
            line = ser.readline().decode('utf-8', errors='ignore').strip() #reads a line from the serial port, decodes it to a string, and removes any whitespace
            print("got: ", line) #prints the received line for debugging purposes
            parts = [p for p in line.split(',')] #splits the line into parts based on commas and removes any empty parts
            if len(parts) >= 6: #checks if parts has 6 unique values
                try:
                    row = [float(p) for p in parts[:6]] #converts the first 6 parts to floats and stores them in a list
                except ValueError:
                    print("bad readings, skipping") #if any of the parts cant be turned into a float, it skips and moves on
                    continue
                writer.writerow(row)
                csvfile.flush() #transfers data to csv file and empties buffer
                timeL.append(row[0])
                light.append(row[1])
                temp.append(row[2])
                hum.append(row[3])
                prec.append(row[4])
                soilM.append(row[5])
                count += 1
            else:
                print("not enough fields, skipping") #prevents bad data being appended to lists
        else:
            time.sleep(0.1) #causes a delay to prevent data being 'fused together'

#tells user that data was successfully added to lists and csv
print(f"done: {count} records written")
#shows user latest piece of data, tests if data got added to corrects lists
print(f"latest data - Time: {timeL[-1]}, Light: {light[-1]}, Temperature: {temp[-1]}, Humidity: {hum[-1]}, Precipitation: {prec[-1]}, Soil Moisture: {soilM[-1]}")

#code for email adapted from "https://realpython.com/python-send-email/#option-2-setting-up-a-local-smtp-server"

#email credentials and settings
sender_email = "szymon.compsci@gmail.com"  
receiver_email = "firedepartmentabc@gmail.com"
password = "qpka bwge fnxw dqpz"  #sender_email app password

#email content
subject = "Fire Risk"
message = MIMEMultipart()
message["From"] = sender_email
message["To"] = receiver_email
message["Subject"] = subject

body = f"""There is a high risk of fire in the area. Please take necessary precautions and be prepared to respond if needed.
Current conditions:
Temperature: {temp[-1]}°C
Humidity: {hum[-1]}%
Soil Moisture: {soilM[-1]}
Light: {light[-1]} lux
Precipitation: {prec[-1]} mm"""

if light[-1] >= 135 and temp[-1] >= 25 and hum[-1] <= 35 and soilM[-1] <= 40 and prec[-1] <= 0:
    print("Threshold reached - sending email") #tells user that an email should be sent due to thresholds being reached
    message.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.send_message(message)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")