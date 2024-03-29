# Visualizing Planets Mobility with SPICE-ns under ns-3 Traces

![SPICE-ns-output](https://github.com/PandiaJason/SPICE-ns-Project/assets/100123063/a1106f63-51bf-44d0-9e3d-c6fda12e6c5d)

This Python script is designed to visualize the mobility traces of celestial bodies within the solar system using SPICE-ns integrated with ns-3. It reads mobility trace data from a file generated by ns-3, extracts the XYZ coordinates of specified celestial bodies, and plots their trajectories in a 3D space.

## Prerequisites
- Python 3.x
- Matplotlib

## Usage
1. Ensure that you have Python 3.x installed on your system.
2. Install the required dependencies using pip:
    ```
    pip install matplotlib
    ```
3. Modify the `spDict` dictionary in the script to specify the celestial bodies you want to visualize along with their corresponding colors.
4. Run the script using the following command:
    ```
    python SPICE-ns-Vis.py
    ```
## Code
```python
import matplotlib.pyplot as plt

if __name__ == "__main__":
    spDict = {
        # "node=0": {"name": "MERCURY", "color": "orange"},
        # "node=1": {"name": "VENUS", "color": "brown"},
        # "node=2": {"name": "EARTH", "color": "blue"},
        "node=0": {"name": "MARS", "color": "darkred"},
        # "node=4": {"name": "JUPITER", "color": "gold"},
        # "node=5": {"name": "PLUTO", "color": "darkmagenta"}
        # "node=6": {"name": "URANUS", "color": "red"},
        # "node=7": {"name": "NEPTUNE", "color": "black"},
        # "node=8": {"name": "PLUTO", "color": "brown"}

    }
    
    # Create a single figure and subplot outside the loop
    fig = plt.figure() 
    ax = fig.add_subplot(111, projection='3d')

    for node, attributes in spDict.items():
        # Read data directly from the file
        with open("SPICE-ns-3-Mobility-Trace.mob") as file:
            data = file.readlines()

        X = []
        Y = []
        Z = []

        # Extract XYZ coordinates from each line of data
        for line in data:
            if node in line:
                pos_start = line.index("pos=") + 4
                pos_end = line.index("vel=") - 1
                XYZ_list = line[pos_start:pos_end].split(":")
                X.append(float(XYZ_list[0]))
                Y.append(float(XYZ_list[1]))
                Z.append(float(XYZ_list[2]))

        # Plot XYZ coordinates for the current node
        ax.plot(X, Y, Z, color=attributes['color'], label=attributes['name'])

    # Move legend, title, and supertitle outside the loop to avoid duplication
    plt.legend(loc='lower left', bbox_to_anchor=(-0.4, -0.1), fontsize='small', title='PLANET')
    plt.title('''Implementing the IAU_EARTH Reference Frame for Realistic Mars Mobility, where IAU_EARTH determines the orientation of Earth's mean equator and equinox of date frame.''', fontsize=14)
    plt.suptitle('''Visualizing MARS Mobility with SPICE-ns under ns-3 Traces''', fontsize=16)

    plt.show()
```

## Description
- The script reads mobility trace data from the "SPICE-ns-3-Mobility-Trace.mob" file.
- It then extracts XYZ coordinates for the specified celestial bodies from the data.
- The extracted coordinates are plotted in a 3D space, with each celestial body represented by a different color.
- The plot includes a legend indicating the names of the celestial bodies.
- The title and supertitle provide additional information about the reference frame and duration of the data.

## Sample Output
The script generates a 3D plot showing the trajectories of the specified celestial bodies within the solar system.

![SPICE-ns-output1](https://github.com/PandiaJason/SPICE-ns-Project/assets/100123063/32d4d118-d205-46ae-bdc6-d453ee99217d)


## References
- SPICE-ns Project: https://github.com/PandiaJason/SPICE-ns-Project/tree/main
- SPICE Toolkit: https://naif.jpl.nasa.gov/naif/toolkit.html
- ns-3: https://www.nsnam.org/
