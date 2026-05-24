# 📡 SPICE-ns - An Extension for ns-3 to Simulate DSN and DTN

- 🌐 Idealized the Proof of Concept for integrating CSPICE with ns3.
- 🚧 SPICE-ns is under development, an extension for ns3 that supports various aspects of deep space network simulations.
- ✅ Successfully Integrated CSPICE under ns3.
- ✅ Developed an Accurate Deep Space Mobility Model under ns3 with SPICE-ns.
- 🚀 As a first step, we have successfully implemented a mobility model for SPICE-ns.

![image](https://github.com/PandiaJason/SPICE-ns-Project/assets/100123063/3d260a63-1d33-4404-bca0-09f35a20f226)


## 📡 About SPICE-ns
SPICE-ns is a modular extension for deep space networks simulation under Network Simulator 3 (ns3). It uses NAIF/NASA's space geometrical data modular toolkit Spacecraft, Planet, Instrument, C-matrix, Events (SPICE)  for modeling astrodynamics of natural and artifical satilites and spacecrafts. In general SPICE finds applications from mission concept development to post-mission data analysis in a realisitic simulated enviornment. With SPICE-ns, it can perform various deep space networking tasks, deep space network scheduling, space packet loss tests, network path finding/planning, and network cost analysis through its simulations.

## 🔥 Motivation for SPICE-ns Contribution

SPICE, developed by NAIF/NASA, is extensively utilized in various space organizations such as ISRO and ESA. It serves diverse purposes, including spacecraft and satellite mission planning, astrodynamics analysis, and deep space network studies. SPICE have been planning a majar role in the development of SPICE enhanced Cosmosphia, widely adopted toolkit across the space organizations.

In terms of network aspects, these organizations rely on in-house software sollutions. Projects like DTNDevKit2.0's CORE(A set of Delay/Disruption-Tolerant Network emulation scenarios for use with the Common Open Research Emulator (CORE)) provide network and visualization for deep space network simulations. The limitations in simulating natural astrodynamics, particualry(For Example: Not handling Mobility in natual way) within DTNDevKit2.0 CORE. And the closed nature of other existing deep space network simulation environments serve as motivation for us to contribute to SPICE-ns under ns3. Our goal is to enhance deep space network stack and simulation aspects with the integration of SPICE, providing a more comprehensive solution.

It is possible to implement the existing as well as new algorithms almost in all the layers of the DSN communication protocol stack. It means it is possible to implement the existing protocols of DSN protocol stack under SPICE-ns framework. In addition to that, for example, it is possible to implement a new, state-of-the-art antenna model and mac layer protocol and hence can develop a few innovative, patentable ideas and protocol designs.

AI/ML/DL/YOLO based Algorithms can be developed for Autamamted Spacecraft/Rover navigation systems.

![image](https://github.com/PandiaJason/SPICE-ns-Project/assets/100123063/2393b78b-4b26-48da-98f7-aff4cca89d6d)

### 📊 Try Our ns3 Traces of SPICE-ns

- **Outputs:** This directory contains the simulation scripts used to generate mobility traces for celestial bodies within the solar system using SPICE-ns integrated with ns-3.

#### How to Use

1. Clone the repository to your local machine using the following command:
    ```
    git clone https://github.com/PandiaJason/SPICE-ns-Project.git
    ```

2. Navigate to the ["SimulationScripts"](https://github.com/PandiaJason/SPICE-ns-Project/tree/main/SimulationScripts) directory to access the simulation scripts.

3. Explore the scripts and data files to understand how the mobility traces are generated and utilized within ns-3 simulations.

#### Example Output

![SPICE-ns-output1](https://github.com/PandiaJason/SPICE-ns-Project/assets/100123063/32d4d118-d205-46ae-bdc6-d453ee99217d)

### 🚧 Note 
The code and information presented in this document are currently under development and are not ready for public distribution. This is a work in progress, and certain features may not be fully implemented or tested. Any use or distribution of the code is discouraged until an official release is made.

📊 Meantime, one can check some of the preliminary results in ["Outputs"](https://github.com/PandiaJason/SPICE-ns-Project/tree/main/Outputs) Folder.

### 📜 Declaration
We are actively processing an application for getting grant to support the future development of SPICE-ns. Consequently, the source code for SPICE-ns, inclusive of the grantor's affiliation, will soon be made accessible on this page.

### 🎯 Long-term Goal

The long-term goal of this project is to develop a complete extension called 'SPICE-ns' for ns-3 to perform DSN/DTN simulations.

In the future, we plan to incrementally implement other aspects necessary to simulate a complete DSN/DTN under SPICE-ns.

## 🌐 SPICE-ns Modules 
 
- ⌛ SPICE-ns Application Models
- ⌛ SPICE-ns DSN/DTN Bundle Data Traffic Generator
- ⌛ SPICE-ns Network Layer Modelling
- ⌛ SPICE-ns Phy Model
- ⌛ SPICE-ns MAC Model
- ⌛ SPICE-ns Spectrum Model
- ⌛ SPICE-ns Antenna Model
- ⌛ SPICE-ns Propagation Model
- ⌛ SPICE-ns Obstacle Model
- ✅ SPICE-ns Mobility Model
- ⌛ SPICE-ns Energy Model
- ✅ SPICE-ns Visualization Tools

   
### 🚀 Project Status 

As a first step, we have successfully implemented a mobility model, propagation models for SPICE-ns, and the proposal has been presented in WNS3 2024, Spain and ICNS-3 2025, Japan. This represents the PhD proposal of Jason Pandian, the maintainer of this repository and project.

