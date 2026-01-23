## Identifying Project Industry Context (Critical Step)

### Where to Infer Industry Context From (Priority Order: High to Low)

1. **Conversation Context** (Highest Priority):
   - Current user request: "implement harmonic analysis" + recent discussion of "three-phase voltage, current"
   → Inference: Power metering
   - User question: "add ECG filtering" + previous discussion of "heart rate monitoring"
   → Inference: Medical device

2. **Current Code Context**:
   - Recently modified files: `power_quality_algorithm.c`, `metering.h`
   → Inference: Power/Energy
   - Function names: `vehicle_can_send()`, `automotive_diagnostics()`
   → Inference: Automotive electronics

3. **Project Documentation** (Last Resort):
   - Only consult CLAUDE.md / AGENTS.md / README.md when above information is insufficient
   - Many projects lack these documents

### Common Industries and Corresponding Keywords

| Industry Domain | Identifying Markers | Keywords to Add in Search |
|----------------|---------------------|--------------------------|
| Power/Energy | power, metering, voltage, current, grid | "power quality", "energy meter", "grid" |
| Industrial Automation | PLC, SCADA, industrial, automation | "industrial", "automation", "factory" |
| Medical Devices | medical, ECG, SpO2, patient, diagnosis | "medical device", "healthcare", "clinical" |
| Automotive Electronics | automotive, CAN, vehicle, OBD | "automotive", "vehicle", "car" |
| Audio Processing | audio, sound, DTMF, microphone | "audio", "sound", "speech" |
| IoT | IoT, sensor, wireless, gateway | "IoT", "sensor network", "wireless" |

### Examples

**Incorrect Example** (Missing Industry Context):
- Search: "Goertzel algorithm" → Results: Audio DTMF detection ❌
- Actual Need: Power harmonic analysis

**Correct Example** (Including Industry Context):
- Identified Industry: Power metering (from CLAUDE.md "three-phase power quality analysis")
- Search: "Goertzel harmonic power quality" → Results: Power harmonic analysis ✅

## Extracting Search Keywords

### General Principles

1. **Prioritize Core Functional Terms**: Extract core technical names of the functionality
   - ✅ Good: "FFT", "Modbus", "PID controller"
   - ❌ Poor: "calculate frequency", "communication protocol"

2. **Combine Keywords**: Core function + application scenario
   - Examples: "FFT embedded", "Modbus RTU C", "PID control motor"

3. **Avoid Overly Specific Project Terminology**
   - ✅ Good: "three-phase power metering"
   - ❌ Poor: "RN7326 DLT645 three-phase MCB"

### Keyword Strategies for Different Function Types

#### Embedded / C / C++

| Function Type | Keyword Strategy | Examples |
|--------------|------------------|----------|
| **Algorithm Implementation** | Algorithm name + "implementation" / "algorithm" | "FFT algorithm C", "Kalman filter embedded" |
| **Communication Protocol** | Protocol name + variant + language | "Modbus RTU C", "DLT645 protocol", "UART protocol parser" |
| **Hardware Driver** | Chip/peripheral name + "driver" | "SPI flash driver", "RTC driver embedded" |
| **Mathematical Operations** | Operation name + "fixed point" / "embedded" | "sine cosine fixed point", "square root integer" |
| **Data Processing** | Processing method + data type | "moving average filter", "circular buffer C" |
| **Signal Processing** | Signal processing technique + domain | "harmonic analysis power", "phase detection" |
| **State Machine/Workflow** | State machine type + application | "finite state machine C", "event driven framework" |

#### Python

| Function Type | Keyword Strategy | Examples |
|--------------|------------------|----------|
| **Web Scraping** | Target + "scraping" / "crawler" + library | "web scraping beautifulsoup", "API crawler requests" |
| **Data Analysis** | Data type + "analysis" / "processing" | "pandas dataframe processing", "numpy array operations" |
| **API Integration** | Service name + "API" + "Python" | "Stripe API Python", "OpenAI API integration" |
| **CLI Tools** | Function + "CLI" / "argparse" | "command line tool argparse", "CLI utility click" |
| **Automation** | Task + "automation" + "Python" | "file automation Python", "email automation script" |
| **Machine Learning** | Algorithm + framework | "neural network pytorch", "classification sklearn" |

#### Shell / Bash

| Function Type | Keyword Strategy | Examples |
|--------------|------------------|----------|
| **System Automation** | Task + "script" / "automation" | "backup script bash", "deployment automation shell" |
| **Log Processing** | "log" + processing method | "log parser awk", "log rotation script" |
| **Monitoring** | Resource + "monitoring" | "disk space monitoring", "process health check" |
| **Batch Operations** | Operation + "batch" / "bulk" | "batch file rename", "bulk image convert" |
| **DevOps Tasks** | Tool + "automation" | "docker deployment script", "kubernetes health check" |

#### JavaScript / TypeScript

| Function Type | Keyword Strategy | Examples |
|--------------|------------------|----------|
| **Frontend Components** | Component type + framework | "dropdown menu react", "modal component vue" |
| **State Management** | "state management" + framework | "redux toolkit", "zustand state" |
| **API Client** | Service + "client" + framework | "REST client axios", "GraphQL client" |
| **Build Tools** | Tool + "config" / "plugin" | "webpack config", "vite plugin" |
| **Node.js Backend** | Function + "express" / "fastify" | "authentication express", "API middleware" |

#### Go

| Function Type | Keyword Strategy | Examples |
|--------------|------------------|----------|
| **CLI Tools** | Function + "CLI" + "Go" | "command line tool cobra", "CLI parsing flag" |
| **Microservices** | Function + "microservice" | "gRPC microservice", "HTTP service gin" |
| **Concurrency** | Pattern + "goroutine" / "channel" | "worker pool goroutine", "pipeline channel" |
| **System Tools** | Function + "Go" | "file watcher Go", "process manager" |