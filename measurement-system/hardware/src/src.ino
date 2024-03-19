#include "multimax_spi.h"

#define T1_CS_PIN  4
#define T2_CS_PIN  5
#define T3_CS_PIN  6
#define T4_CS_PIN  7
#define T5_CS_PIN  8
#define T6_CS_PIN  9

// Instantiate MMAX6675 object with the specified chip select (CS) pins and maximum queue size
MMAX6675 measure_system(T1_CS_PIN, T2_CS_PIN, T3_CS_PIN, T4_CS_PIN, T5_CS_PIN, T6_CS_PIN, 40);

// Variables for controlling the measurement process
bool start = 0; // Flag to indicate whether measurements should be started or stopped
long int _time, prev_time; // Variables to keep track of time
unsigned int sampling_time = 250; // Default sampling time (milliseconds), initially set to 1 second
unsigned int analysis_time = 10000; // Default analysis time (milliseconds), initially set to 10 second
int analysis_max_counter;
int analysis_counter;

void setup()
{
    // Initialize serial communication
    Serial.begin(115200);

    // Initialize previous time
    prev_time = millis();
    update_analysis_max_counter();
    analysis_counter = 0;
}

void loop()
{   
    // If measurement process is started
    if (start){
      // Get current time
      _time = millis();
      // Check if it's time to take a new measurement (every 1000 milliseconds)
      if (_time - prev_time > sampling_time){
          if (analysis_counter < analysis_max_counter){ // take data during the analysis time
            // Register temperatures and check if successfull
            if (!measure_system.regTemperatures()){
                // Print error message if registration fails
                Serial.println("BF"); // Error code BF (Buffer Full)
                start = 0;
            }
            prev_time = _time; // Update previous time
            analysis_counter++;
          }else{
            start = 0;
          }
      }
    }
}

// Function to handle serial events (incoming commands)
void serialEvent(){
    String command = Serial.readStringUntil('\n'); // Read incoming command from serial port
    command.trim(); // Remove leading and trailing whitespaces

  // Process incoming commands
  if (command == "START") {
    analysis_counter = 0;
    start = 1; // Start measurement process
    Serial.println("STAOK"); // started OK
  }
  else if (command == "STOP") {
    start = 0; // Stop measurement process
    Serial.println("STOOK"); // stopped OK
  }
  else if (command == "GET") {
    // Check if data queue is not empty

    if (!measure_system.dataQueue.isEmpty()) {
        Serial.println(measure_system.get_measurements()); // Get and print measurements
    } else {
        Serial.println("BE"); // Error code BE (Buffer Empty)
    }
  }

  else if (command.startsWith("SETS")) {
    // Extract sampling time from the command
    int new_sampling_time = command.substring(4).toInt(); // The format should be "SETS XXX" where XXX is the new sampling time

    // Check if the new sampling time is at least 250 ms
    if (new_sampling_time >= 250) {
      sampling_time = new_sampling_time; // Update sampling time
      Serial.println("SSOK"); // Set Sampling time OK.
    } else {
      Serial.println("SSNOK"); // Error code SSNOK (Set Sampling time no OK)
    }
  }

  else if (command.startsWith("SETA")) {
    // Extract analysis time from the command
    int new_analysis_time = command.substring(4).toInt(); // The format should be "SETA XXX" where XXX is the new analysis time

    // Check if the new analysis time is not lower than  sampling_time
    if (new_analysis_time < sampling_time) {
      Serial.println("SANOK"); // Error code SANOK (Set Analysis time no OK)
    } else {
      analysis_time = new_analysis_time; // Update analysis time
      update_analysis_max_counter(); 
      Serial.println("SAOK"); // Set Analysis time OK.
    }
  }

  else if (command == "CLEAR") {
    measure_system.clear_queue();
    Serial.println("CLROK"); // cleared OK
  }
  else if (command.startsWith("BSIZE"))
  {
    if(!start){
      int new_buffer_size = command.substring(5).toInt(); // The format should be "BSIZE XXX" where XXX is the new buffer size 
      if (measure_system.resize_queue(new_buffer_size)){
        Serial.println("BSOK"); // Buffer size OK
      }else
        Serial.println("BSNOK"); // Error code BNOK (Buffer size no OK)
    }
    else{
      Serial.println("BSNOK"); // Error code BNOK (Buffer size no OK)
    }
  }
}

void update_analysis_max_counter (){
  analysis_max_counter =  int( analysis_time / sampling_time);
}