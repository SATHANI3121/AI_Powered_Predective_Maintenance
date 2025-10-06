"""
Generate synthetic training data with realistic failure patterns
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_training_data(
    n_machines: int = 5,
    days: int = 30,
    interval_minutes: int = 5,
    failure_probability: float = 0.10,
    output_file: str = "seed_data/training_sensors.csv"
):
    """
    Generate synthetic sensor data with realistic failure patterns
    
    Args:
        n_machines: Number of machines to simulate
        days: Number of days of data
        interval_minutes: Sampling interval in minutes
        failure_probability: Probability of failure conditions
        output_file: Output CSV file path
    """
    
    np.random.seed(42)
    
    records = []
    # Start from 'days' ago to have recent data
    start_time = datetime.now() - timedelta(days=days)
    n_samples = int((days * 24 * 60) / interval_minutes)
    
    for machine_idx in range(n_machines):
        machine_id = f"M-{machine_idx+1:03d}"
        
        # Decide if this machine will have failure patterns
        has_failures = np.random.random() < failure_probability * n_machines
        
        for i in range(n_samples):
            timestamp = start_time + timedelta(minutes=i * interval_minutes)
            
            # Base values (normal operation)
            temp_base = 65 + np.random.normal(0, 2)
            vib_base = 0.15 + np.random.normal(0, 0.02)
            current_base = 5.0 + np.random.normal(0, 0.3)
            pressure_base = 100 + np.random.normal(0, 3)
            rpm_base = 1750 + np.random.normal(0, 25)
            
            # Add failure patterns
            if has_failures:
                # Gradual degradation over time
                degradation_factor = (i / n_samples) * 0.5
                
                # Periodic spikes (simulating stress cycles)
                cycle_factor = np.sin(2 * np.pi * i / (24 * 60 / interval_minutes)) * 0.2
                
                # Random anomalies
                if np.random.random() < 0.05:  # 5% chance of anomaly
                    temp_base += np.random.normal(15, 5)
                    vib_base += np.random.normal(0.3, 0.1)
                    current_base += np.random.normal(2, 0.5)
                
                temp_base += degradation_factor * 20 + cycle_factor * 10
                vib_base += degradation_factor * 0.4 + abs(cycle_factor) * 0.2
                current_base += degradation_factor * 3 + cycle_factor * 1.5
            
            # Ensure realistic bounds
            temp_base = max(50, min(temp_base, 95))
            vib_base = max(0.05, min(vib_base, 1.5))
            current_base = max(3, min(current_base, 12))
            pressure_base = max(80, min(pressure_base, 130))
            rpm_base = max(1500, min(rpm_base, 2000))
            
            # Add records for each sensor
            records.append({
                'timestamp': timestamp.isoformat(),
                'machine_id': machine_id,
                'sensor': 'temperature',
                'value': round(temp_base, 2)
            })
            records.append({
                'timestamp': timestamp.isoformat(),
                'machine_id': machine_id,
                'sensor': 'vibration',
                'value': round(vib_base, 3)
            })
            records.append({
                'timestamp': timestamp.isoformat(),
                'machine_id': machine_id,
                'sensor': 'current',
                'value': round(current_base, 2)
            })
            records.append({
                'timestamp': timestamp.isoformat(),
                'machine_id': machine_id,
                'sensor': 'pressure',
                'value': round(pressure_base, 1)
            })
            records.append({
                'timestamp': timestamp.isoformat(),
                'machine_id': machine_id,
                'sensor': 'rpm',
                'value': round(rpm_base, 0)
            })
    
    # Create DataFrame and save
    df = pd.DataFrame(records)
    df.to_csv(output_file, index=False)
    
    print(f"✅ Generated {len(df)} sensor readings")
    print(f"   Machines: {n_machines}")
    print(f"   Time range: {days} days")
    print(f"   Samples per machine: {n_samples}")
    print(f"   Output: {output_file}")
    
    return df

if __name__ == "__main__":
    generate_training_data(
        n_machines=5,
        days=30,
        interval_minutes=5,
        failure_probability=0.3
    )

