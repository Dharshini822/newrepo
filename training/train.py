import os
import sys
import argparse

# Add parent directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.services.training_service import get_training_service

def main():
    parser = argparse.ArgumentParser(description="SignAI — Train Sign Language Recognition Model")
    parser.add_argument("--trees", type=int, default=100, help="Number of trees in RandomForest (default: 100)")
    parser.add_argument("--max-depth", type=int, default=15, help="Max depth of trees (default: 15)")
    args = parser.parse_args()

    print("===============================================================")
    print("  SignAI: Starting Model Training Pipeline")
    print("===============================================================")
    print(f"Parameters: n_estimators={args.trees}, max_depth={args.max_depth}")

    service = get_training_service()
    # Run synchronously for CLI
    service._run_training_pipeline(n_estimators=args.trees, max_depth=args.max_depth)

    status = service.get_status()
    if status.get("error"):
        print(f"\n[FAILED] Training error: {status['error']}")
        sys.exit(1)
    else:
        res = status.get("latest_result", {})
        print("\n[SUCCESS] Model training completed successfully!")
        print(f"Algorithm:           {res.get('algorithm')}")
        print(f"Supported Classes:   {', '.join(res.get('classes', []))}")
        print(f"Training Samples:    {res.get('training_samples')}")
        print(f"Validation Samples:  {res.get('validation_samples')}")
        print(f"Validation Accuracy: {res.get('accuracy', 0)*100:.2f}%")
        print(f"Weighted F1-Score:   {res.get('f1_score', 0):.4f}")
        print(f"Model saved to:      models/sign_model.joblib")
        print(f"Metadata saved to:   models/model_metadata.json")

if __name__ == "__main__":
    main()
