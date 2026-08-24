
import matplotlib.pyplot as plt
import numpy as np

def plot_radar_chart(probabilities_dict, save_path="radar_chart.png"):
    """
    Plots a radar chart for the given probabilities.
    probabilities_dict: { 'Sour': 0.1, 'Sweet': 0.8, ... }
    """
    # Categories
    categories = list(probabilities_dict.keys())
    values = list(probabilities_dict.values())
    
    # Number of variables
    N = len(categories)
    
    # What will be the angle of each axis in the plot?
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    
    # Close the plot
    values += values[:1]
    angles += angles[:1]
    
    # Output path
    if not save_path:
        save_path = "radar_chart.png"
        
    print(f"Generating Radar Chart for: {probabilities_dict}")
    
    # Start plot
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    
    # Draw one axe per variable + add labels
    # Offset labels slightly to avoid overlap with grid
    plt.xticks(angles[:-1], categories, color='#333333', size=12, weight='bold')
    
    # Draw ylabels
    ax.set_rlabel_position(30)
    plt.yticks([0.2, 0.4, 0.6, 0.8], ["0.2", "0.4", "0.6", "0.8"], color="#999999", size=9)
    plt.ylim(0, 1)
    
    # Custom Color
    # Use a dynamic color based on max value? Or just a nice fixed one.
    # Let's use a nice teal/blue.
    main_color = '#1E88E5' 
    
    # Plot data
    ax.plot(angles, values, linewidth=2.5, linestyle='solid', color=main_color, marker='o', markersize=6)
    
    # Fill area
    ax.fill(angles, values, color=main_color, alpha=0.25)
    
    # Grid customization
    ax.grid(True, color='#E0E0E0', linestyle='--')
    ax.spines['polar'].set_visible(False) # Remove outer circle border for cleaner look
    
    # Title
    max_cat = categories[np.argmax(values[:-1])]
    max_val = max(values[:-1])
    plt.title(f"Taste Profile: {max_cat} ({max_val:.0%})", size=18, y=1.1, color='#333333', weight='bold')
    
    # Add Breakdown Subtitle
    # Sort categories by value
    sorted_probs = sorted(zip(categories, values[:-1]), key=lambda x: x[1], reverse=True)
    
    # Take top 3-4 that are non-zero
    breakdown_text = "Content: " + " | ".join([f"{cat}: {val:.0%}" for cat, val in sorted_probs if val > 0.01][:4])
    
    plt.figtext(0.5, 0.02, breakdown_text, ha='center', fontsize=10, 
                bbox={"facecolor":"white", "alpha":0.8, "pad":5}, color="#555555")
    
    plt.savefig(save_path)
    plt.close()
    print(f"Chart saved to {save_path}")

if __name__ == "__main__":
    # Test
    mock_data = {'Sour': 0.1, 'Sweet': 0.4, 'Bitter': 0.3, 'Salty': 0.1, 'Umami': 0.1}
    try:
        plot_radar_chart(mock_data)
    except Exception as e:
        print(f"Visualization Error: {e}")
