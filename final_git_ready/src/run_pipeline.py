
import os
import argparse
import pandas as pd
from data_loader import load_data
from model_trainer import TasteModel
from visualizer import plot_radar_chart

# Main execution pipeline
def main():
    parser = argparse.ArgumentParser(description="Taste Prediction Pipeline")
    parser.add_argument("--train", help="Path to training Excel file", required=False)
    parser.add_argument("--predict", help="Path to input CSV for prediction", required=False)
    parser.add_argument("--mock", action="store_true", help="Use mock data generation for training")
    
    args = parser.parse_args()
    
    model_path = "models/taste_model.pkl"
    model = TasteModel()
    
    # TRAINING MODE
    if args.train or args.mock:
        print("--- Starting Training Pipeline ---")
        
        if args.mock:
            # Check if mock file exists or generate it
            if not os.path.exists("mock_taste_data.xlsx"):
                try:
                    from generate_mock_data import generate_mock_excel
                    generate_mock_excel()
                except ImportError:
                    print("Could not import generate_mock_data. Please run 'python generate_mock_data.py' first.")
            data_path = "mock_taste_data.xlsx"
        else:
            data_path = args.train
            
        try:
            X, y, features = load_data(data_path)
            print(f"Loaded {len(X)} samples.")
            
            acc = model.train(X, y)
            model.save()
            model.save_production_format()
            print("Training Complete.")
        except Exception as e:
            print(f"Error during training: {e}")
            return

    # PREDICTION MODE
    if args.predict:
        print("\n--- Starting Prediction Pipeline ---")
        if not os.path.exists(model_path):
            print("Model not found! Please train first.")
            return
            
        try:
            model = TasteModel.load(model_path)
            print("Model loaded.")
            
            # Load input
            # Input should be a CSV with columns matching the reagents
            # Or a simple Key-Value pair
            input_df = pd.read_csv(args.predict)
            
            print(f"Predicting for {len(input_df)} samples...")
            
            for idx, row in input_df.iterrows():
                result = model.predict(row)
                
                print(f"\nSample {idx+1}:")
                print(f"  Predicted Taste: {result['predicted_taste']}")
                print(f"  Confidence: {result['confidence']*100:.2f}%")
                
                print("  Full Breakdown:")
                for taste, prob in result['all_probabilities'].items():
                    if prob > 0.01: # Only show meaningful ones
                        print(f"    - {taste}: {prob*100:.2f}%")
                
                # Visualize
                chart_name = f"result_{idx+1}_radar.png"
                plot_radar_chart(result['all_probabilities'], save_path=chart_name)
                
        except Exception as e:
            print(f"Error during prediction: {e}")

if __name__ == "__main__":
    main()
