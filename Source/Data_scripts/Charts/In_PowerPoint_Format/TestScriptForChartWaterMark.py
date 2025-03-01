import matplotlib.pyplot as plt
import numpy as np

# Sample data similar to your MTA ridership
hours = [f"{h % 12 if h % 12 != 0 else 12} {'AM' if h < 12 else 'PM'}" for h in range(24)]
sample_data = [8, 3, 3, 3, 6, 16, 32, 57, 57, 32, 28, 26, 28, 33, 42, 58, 75, 61, 37, 27, 19, 16, 15, 13]

# Your watermark text
WATERMARK_TEXT = "Created By Mantie Reid II"

# Create a function to test different watermark positions
def test_watermark(x_pos=0.45, y_pos=0.00):
    plt.figure(figsize=(10, 6))
    plt.plot(hours, sample_data, marker='o', linestyle='-', 
             label=f"Avg Riders: {np.mean(sample_data):.2f}")
    plt.title(f"Avg Ridership for 149 St-Grand Concourse (2-4-5) - 1/2023", fontsize=16)
    plt.xlabel("Time (EST)", fontsize=14)
    plt.ylabel("Avg Riders", fontsize=14)
    plt.xticks(rotation=45)
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend()
    
    # Add watermark with your name
    plt.figtext(x_pos, y_pos, WATERMARK_TEXT, ha='center', color='gray', alpha=0.7, fontsize=10)
    
    plt.tight_layout()
    plt.show()
    
    print(f"Watermark position: x={x_pos}, y={y_pos}")

# Test a specific position
test_watermark(x_pos=0.65, y_pos=0.01)

# Uncomment and modify these to try other positions
# test_watermark(x_pos=0.7, y_pos=0.01)  # More to the right
# test_watermark(x_pos=0.6, y_pos=0.005) # Lower position
# test_watermark(x_pos=0.75, y_pos=0.02) # Higher and more right