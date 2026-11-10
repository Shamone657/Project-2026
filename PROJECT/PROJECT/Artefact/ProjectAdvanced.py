import csv
import matplotlib.pyplot as plt
import numpy as np

#menu to choose precipitation type (analogue from SimData.csv or digital from sensor_data.csv)
prec_choice = False
while prec_choice != True:
    choice = input("Choose precipitation type:\n1. Analogue (0-100%)\n2. Digital (0-1)\nEnter 1 or 2: ").strip()
    if choice == '1':
        is_digital = False
        prec_choice = True
    elif choice == '2':
        is_digital = True
        prec_choice = True
    else:
        print("Invalid choice")
        continue

#always reads from SimData.csv for temp, hum, light, soilM
with open("SimData.csv", mode="r", newline="") as file:
    reader = csv.reader(file)
    #skips header lines until data is reached
    for row in reader:
        if row[0] == 'YEAR':
            break
    temp = []
    hum = []
    prec_temp = []  #temporary for analogue prec
    light = []
    soilM = []

    for row in reader:
        if not row or row[0] == '': #skips empty rows
            continue  
        temp.append(float(row[2]))
        hum.append(float(row[3]))
        prec_temp.append(float(row[4]))
        light.append(float(row[5]))
        soilM.append(float(row[8]))

#if digital, reads precipitation from sensor_data.csv
if is_digital:
    with open("sensor_data.csv", mode="r", newline="") as file:
        reader = csv.reader(file)
        heading = next(reader)
        prec = []
        for row in reader:
            prec.append(float(row[5]))  #only reads precipitation
else:
    prec = prec_temp

def ignition_probability(t, h, p, l, m, is_digital=False):
    #normalises inputs to their expected ranges
    h = min(max(h, 0), 100) #ensures humidity is between 0 and 100
    p = max(p, 0) #ensures precipitation is not negative 
    m = min(max(m, 0), 1) #ensures soil moisture is between 0 and 1
    l = max(l, 0) #ensures light intensity is not negative
   
    if is_digital == True:
        if p == 0:  #raining, takes away 8% of fire risk
            prec_factor = 0.92
        elif p == 1:  #not raining, adds 15% of fire risk
            prec_factor = 1.15
        else:
            prec_factor = 1.0  #no change in fire risk if bad data is present
    else:
        prec_factor = max(0, 1 - (p / 100))
    
    dryness = (1 - m) * (1 - (h / 100)) * prec_factor
    heat = min(max((t - 15) / 25, 0), 1)
    solar = min(max(l / 8, 0), 1)

    probability = dryness * heat * solar
    #final cap ensures probability is between 0 and 1
    return min(max(probability, 0), 1)

probability = []

for i in range(len(temp)):
    #clamps individual values for display
    t0, h0, p0, l0, m0 = temp[i], hum[i], prec[i], light[i], soilM[i]
    h0 = min(max(h0, 0), 100)
    p0 = max(p0, 0)
    m0 = min(max(m0, 0), 1)
    prob = ignition_probability(t0, h0, p0, l0, m0, is_digital)
    if is_digital:
        prec_unit = ""
    else:
        prec_unit = "mm"
    print(f"Day: {i+1}, Temperature: {t0}°C, Humidity: {h0}%, Precipitation: {p0}{prec_unit}, Light: {l0} lux, Soil Moisture: {m0}, Ignition Probability: {prob:.2%}")
    probability.append(prob)


#function to adjust data values for what-if scenarios
def adjust_values(name, data, is_digital=False):
    #asks the user how they want to change the dataset (won't affect the csv file).
    while True:
        print(f"\nAdjusting {name} (current first few values: {data[:5]})") 
        #tells the user the expected range for some values
        if 'humidity' in name.lower():
            print(" (enter values between 0 and 100)")
        elif 'soil' in name.lower():
            print("(enter values between 0 and 1)")
        elif 'precipitation' in name.lower() and is_digital:
            print("enter only 0 or 1 (0 = raining, 1 = not raining)")
        print("a) Add a constant to every value") #adds a constant to every value 
        print("m) Multiply every value") #multiplies every value by a constant 
        print("s) Set every value to a constant") #sets every value to a constant 
        print("x) Cancel adjustment") #cancels adjustment and keeps original values
        choice = input("Choose adjustment type [a/m/s/x]: ").strip().lower() 
        if choice == 'a':
            val = input("Enter value to add (can be negative): ") #tells the user to add/subtract a constant value from every value in the dataset
            try:
                val = float(val) #converts input to a float
                result = [] #creates new list for modified data
                for x in data:
                    result.append(x + val) #adds the constant to every value in the dataset and stores it in result
                print(f"\nData successfully modified") #tells user data was successfully modified
            except: #if input cannot be converted to a float, it catches the error and tells the user to try again
                print("Invalid number, try again.")
                continue
        elif choice == 'm':
            val = input("Enter multiplier: ") #tells the user to multiply every value in the dataset by a constant value
            try:
                val = float(val) 
                result = []
                for x in data:
                    result.append(x * val) #multiplies every value in the dataset by the constant and stores it in result
                print(f"\nData successfully modified")
            except:
                print("Invalid number, try again.")
                continue
        elif choice == 's':
            val = input("Enter constant value: ") #tells the user to set every value in the dataset to a constant value
            try:
                val = float(val)
                result = []
                for i in range(len(data)):
                    result.append(val)
                print(f"\nData successfully modified")
            except:
                print("Invalid number, try again.")
                continue
        elif choice == 'x':
            return data
        else:
            print("Invalid choice. Please choose a, m, s or x.")
            continue
        #makes sure there is no invalid data after adjustment (e.g. negative humidity or soil moisture above 1)
        clamped = []
        if 'humidity' in name.lower():
            for x in result:
                clamped.append(min(max(x, 0), 100))
        elif 'soil' in name.lower():
            for x in result:
                clamped.append(min(max(x, 0), 1))
        elif 'precipitation' in name.lower() and is_digital:
            #for digital precipitation, rounds to nearest 0 or 1
            for x in result:
                clamped.append(round(min(max(x, 0), 1)))
        elif 'precipitation' in name.lower() and not is_digital:
            for x in result:
                clamped.append(max(x, 0)) #analogue precipitation cant be negative
        else:
            #temperature/light not clamped here
            clamped = result[:]

        #tells user if any values were adjusted due to it being out of range
        if result != clamped:
            if 'precipitation' in name.lower() and is_digital:
                print(f"Warning: Digital precipitation values have been rounded to 0 or 1.")
            else:
                print(f"Warning: Some values in {name} were outside the allowed range and have been adjusted.")
        return clamped



#menu that allows the user to create what-if scenarios by adjusting the datasets and recalculating ignition probabilities without modifying the original data or CSV file
def what_if_menu(original, is_digital):
    temp_s, hum_s, prec_s, light_s, soil_s = (original['temp'][:], original['hum'][:], original['prec'][:], original['light'][:], original['soilM'][:]) #creates copies of original data to modify

    #creates menu
    while True:
        print("\n--- WHAT-IF SCENARIO MENU ---")
        print("1. Change temperature")
        print("2. Change humidity")
        print("3. Change precipitation")
        print("4. Change light intensity")
        print("5. Change soil moisture")
        print("6. Calculate & plot with current scenario")
        print("7. Reset to original data")
        print("8. Close programme")
        choice = input("Select an option: ").strip()

        if choice == '1': #adjusts temperature
            temp_s = adjust_values('temperature', temp_s, is_digital)
        elif choice == '2': #adjusts hummidty
            hum_s = adjust_values('humidity', hum_s, is_digital)
        elif choice == '3': #adjusts precipitation
            prec_s = adjust_values('precipitation', prec_s, is_digital)
        elif choice == '4': #adjusts light level
            light_s = adjust_values('light', light_s, is_digital)
        elif choice == '5': #adjusts soil moisture
            soil_s = adjust_values('soil moisture', soil_s, is_digital)
        elif choice == '6': #recalculates probabilities with modified data and plots the new probabilities
            recalc_and_plot(temp_s, hum_s, prec_s, light_s, soil_s, is_digital)
        elif choice == '7': #resets modified data to original values
            temp_s, hum_s, prec_s, light_s, soil_s = (
                original['temp'][:],
                original['hum'][:],
                original['prec'][:],
                original['light'][:],
                original['soilM'][:]
            )
            print("Data reset to original values.")
        elif choice == '8':
            break
        else:
            print("Please enter a number from 1 to 8.")


#recalculates ignition probabilities with modified data and plots the new probabilities
def recalc_and_plot(t_data, h_data, p_data, l_data, m_data, is_digital):
    probs = []
    for i in range(len(t_data)):
        #clamps for display
        t0, h0, p0, l0, m0 = t_data[i], h_data[i], p_data[i], l_data[i], m_data[i]
        h0 = min(max(h0, 0), 100) #ensures humidity is between 0 and 100
        p0 = max(p0, 0) #ensures precipitation is not negative
        l0 = max(l0, 0) #ensures light intensity is not negative
        m0 = min(max(m0, 0), 1) #ensures soil moisture is between 0 and 1
        prob = ignition_probability(t0, h0, p0, l0, m0, is_digital)
        if is_digital:
            prec_unit = ""
        else:
            prec_unit = "mm"
        print(f"Day: {i+1}, Temperature: {t0}°C, Humidity: {h0}%, "
              f"Precipitation: {p0}{prec_unit}, Light: {l0} lux, "
              f"Soil Moisture: {m0}, Ignition Probability: {prob:.2%}")
        probs.append(prob)

    days = np.arange(1, len(t_data) + 1)
    plt.figure(figsize=(10, 5))
    plt.plot(days, [p * 100 for p in probs], marker='o', linestyle='-', color='red', label='Days 1-31 = Jan \nDays 32-60 = Feb \nDays 61 – 91 = Mar \nDays 92 – 121 = Apr \nDays 122 – 152 = May \nDays 153 – 182 = Jun \nDays 183 – 213 = Jul \nDays 214 – 244 = Aug \nDays 245 – 274 = Sep \nDays 275 – 305 = Oct \nDays 306 – 335 = Nov \nDays 336 – 366 = Dec')
    plt.xlabel('Days')
    plt.ylabel('Ignition Probability (%)')
    plt.title('Ignition Probability Over Time (What-if scenario)')
    plt.legend()
    plt.grid(True)
    plt.show()

#original calculation and plot
probability = []
for i in range(len(temp)):
    prob = ignition_probability(temp[i], hum[i], prec[i], light[i], soilM[i], is_digital)
    if is_digital:
        prec_unit = ""
    else:
        prec_unit = "mm"
    print(f"Day: {i+1}, Temperature: {temp[i]}°C, Humidity: {hum[i]}%, "
          f"Precipitation: {prec[i]}{prec_unit}, Light: {light[i]} lux, "
          f"Soil Moisture: {soilM[i]}, Ignition Probability: {prob:.2%}")
    probability.append(prob)

print("*"*100)
print("Original scenario calculated and plotted. Close current plot to open what-if scenario menu.")

#plots the original data
days = np.arange(1, len(temp) + 1)
plt.figure(figsize=(10, 5))
plt.plot(days, [p * 100 for p in probability], marker='o', linestyle='-', color='red', label='Days 1-31 = Jan \nDays 32-60 = Feb \nDays 61 – 91 = Mar \nDays 92 – 121 = Apr \nDays 122 – 152 = May \nDays 153 – 182 = Jun \nDays 183 – 213 = Jul \nDays 214 – 244 = Aug \nDays 245 – 274 = Sep \nDays 275 – 305 = Oct \nDays 306 – 335 = Nov \nDays 336 – 366 = Dec')
plt.xlabel('Days')
plt.ylabel('Ignition Probability (%)')
plt.title('Ignition Probability Over Time')
plt.legend()
plt.grid(True)
plt.show()

#launches what-if menu
what_if_menu({'temp': temp, 'hum': hum, 'prec': prec, 'light': light, 'soilM': soilM}, is_digital)