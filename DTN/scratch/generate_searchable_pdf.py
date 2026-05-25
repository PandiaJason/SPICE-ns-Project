import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

def main():
    img_path = '../paper/figs/P-ECGR_Deep_Space_Routing_Solution.png'
    pdf_path = '../paper/figs/P-ECGR_Deep_Space_Routing_Solution.pdf'
    
    # Load image to confirm size
    img = mpimg.imread(img_path)
    h, w, _ = img.shape
    
    # Create figure with exact dimensions and no borders
    dpi = 100
    fig, ax = plt.subplots(figsize=(w/dpi, h/dpi), dpi=dpi)
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.axis('off')
    
    # Display the image as background
    ax.imshow(img, extent=[0, w, 0, h], aspect='auto')
    
    # Define text overlays (using alpha=0 to make them invisible but fully selectable/searchable)
    # Coordinates are in pixel space: x in [0, 2752], y in [0, 1536] (0 is bottom)
    texts = [
        # --- TITLE AREA (Top Left) ---
        (80, 1420, "P-ECGR: Solving Energy Exhaustion", 36),
        (80, 1350, "in Deep Space SmallSat Networks", 36),
        (80, 1260, "P-ECGR prevents relay battery failure and maximizes data delivery", 16),
        (80, 1220, "by forecasting future energy and using reservation-based booking,", 16),
        (80, 1180, "unlike resource-blind standard routing.", 16),
        
        # --- DSN & EARTH AREA ---
        (1340, 1370, "DSN", 14),
        (1330, 890, "P-ECGR", 18),
        (1330, 770, "Traffic", 14),
        (860, 930, "SmallSat", 14),
        (1820, 930, "MRO", 14),
        
        # --- SOLUTION BOXES (Left & Right) ---
        # Solution 1: Future Orbital Energy Prediction
        (80, 1070, "THE SOLUTION: PREDICTIVE & BOOKED ROUTING (P-ECGR)", 16),
        (80, 1020, "Future Orbital Energy Prediction", 20),
        (80, 970, "Integrates solar-charging and eclipse windows to forecast", 14),
        (80, 935, "battery levels at transmission time.", 14),
        (650, 920, "Sunlight", 12),
        (760, 920, "Shadow", 12),
        (700, 850, "Forecast", 12),
        
        # Solution 2: Priority-Based Load Balancing
        (80, 750, "Priority-Based Load Balancing", 20),
        (80, 700, "Shifts low-priority traffic to high-capacity orbiters", 14),
        (80, 665, "during a SmallSat's low-energy phases.", 14),
        
        # Solution 3: Reservation-Based Energy Booking
        (1720, 750, "Reservation-Based Energy Booking", 20),
        (1720, 700, "A local registry \"books\" energy for committed bundles", 14),
        (1720, 665, "to prevent relay over-subscription.", 14),
        (1600, 700, "Registry", 14),
        
        # --- PERFORMANCE PROOF (Top Right) ---
        (1820, 1420, "PERFORMANCE PROOF: P-ECGR RESULTS", 22),
        # Card A
        (1820, 1350, "90.0% Delivery Ratio", 18),
        (1820, 1300, "P-ECGR outperforms standard and state-of-the-art", 12),
        (1820, 1275, "algorithms in total data throughput.", 12),
        (1850, 1120, "Standard CGR", 11),
        (1960, 1120, "SOTA ECGR", 11),
        (2070, 1120, "P-ECGR", 11),
        
        # Card B
        (2300, 1350, "Zero Packet Drops", 18),
        (2300, 1300, "Maintains perfect reliability while keeping SmallSat", 12),
        (2300, 1275, "batteries above the 20% critical threshold.", 12),
        (2280, 1220, "Dropped Bundles", 11),
        (2280, 1160, "Battery Charge", 11),
        (2450, 1130, "20% Critical Threshold", 11),
        
        # Table
        (1820, 1030, "P-ECGR PERFORMANCE VS. BASELINE", 14),
        (1830, 985, "Metric", 12),
        (1830, 940, "Delivery Ratio", 12),
        (1830, 895, "Dropped Bundles", 12),
        (1830, 850, "Avg. Latency", 12),
        
        (2100, 985, "Standard CGR", 12),
        (2100, 940, "83.7%", 12),
        (2100, 895, "12.9", 12),
        (2100, 850, "5483 s", 12),
        
        (2320, 985, "SOTA ECGR", 12),
        (2320, 940, "89.5%", 12),
        (2320, 895, "0.0", 12),
        (2320, 850, "5373 s", 12),
        
        (2530, 985, "P-ECGR", 12),
        (2530, 940, "90.0%", 12),
        (2530, 895, "0.0", 12),
        (2530, 850, "5073 s", 12),
        
        # --- PROBLEM AREA (Bottom) ---
        (80, 520, "THE PROBLEM: RESOURCE-BLIND ROUTING", 16),
        # Problem 1: The "Energy Overbooking" Bottleneck
        (80, 470, "The \"Energy Overbooking\" Bottleneck", 20),
        (80, 420, "Standard routing ignores cumulative energy costs, causing", 14),
        (80, 385, "SmallSat battery shutdowns and data loss.", 14),
        
        # Problem 2: The Conservatism Trap
        (80, 260, "The Conservatism Trap", 20),
        (80, 210, "Existing energy-aware systems avoid charging satellites,", 14),
        (80, 175, "reducing overall network delivery efficiency.", 14),
        
        # Problem 3: 12.9 Average Bundle Drops
        (1720, 470, "12.9 Average Bundle Drops", 20),
        (1720, 420, "Resource-blind routing frequently exhausts SmallSat", 14),
        (1720, 385, "batteries, leading to significant packet loss.", 14),
    ]
    
    # Overlay the invisible selectable text onto the canvas
    for x, y, string, size in texts:
        ax.text(x, y, string, fontsize=size, color='none', alpha=0.0,
                va='bottom', ha='left')
        
    # Save the output PDF with high quality
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight', pad_inches=0, dpi=dpi)
    plt.close()
    print("Searchable vector-text PDF generated successfully at:", pdf_path)

if __name__ == '__main__':
    main()
