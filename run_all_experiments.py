
import sys
import os
import json
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not installed. Make sure .env file is loaded.")

from experiment_runner import ExperimentRunner
from llm_agent import create_agent
from results_analyzer import analyze_results

def main():
    print("\n" + "="*70)
    print("IPI VULNERABILITY TESTING FRAMEWORK - MULTI-MODEL EDITION")
    print("Security Analysis of Model Context Protocol Systems")
    print("="*70)

    missing_packages = []
    try:
        import openai
    except ImportError:
        missing_packages.append("openai")

    try:
        import anthropic
    except ImportError:
        missing_packages.append("anthropic")

    if missing_packages:
        print("\nWARNING: Some packages are missing:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\nInstall with: pip install openai anthropic python-dotenv")
        print("You can still proceed if you have API keys in .env file")

    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    print("\n" + "="*70)
    print("API KEY STATUS")
    print("="*70)
    print(f"OpenAI API Key:    {'Found in .env' if openai_key else 'NOT FOUND'}")
    print(f"Anthropic API Key: {'Found in .env' if anthropic_key else 'NOT FOUND'}")

    if not openai_key and not anthropic_key:
        print("\nERROR: No API keys found!")
        print("\n   1. Create a .env file in this directory")
        print("   2. Add your API keys:")
        print("      OPENAI_API_KEY=your-key-here")
        print("      ANTHROPIC_API_KEY=your-key-here")
        print("   3. Run this script again")
        return

    print("\n" + "="*70)
    print("MODEL SELECTION")
    print("="*70)
    print("\nWhich model(s) would you like to test?")

    if openai_key:
        print("   1. GPT-5 Mini (gpt-5-mini-2025-08-07)")
        print("   2. GPT-4.1 (gpt-4.1-2025-04-14)")
    if anthropic_key:
        print("   3. Claude 3.5 Haiku (claude-3-5-haiku-20241022)")
        print("   4. Claude Haiku 4.5 (claude-haiku-4-5-20251001)")
    if openai_key and anthropic_key:
        print("   5. All Models (Comparison)")

    print("\nEnter choice: ", end="")
    choice = input().strip()

    models_to_test = []
    choice_map = {
        "1": ("gpt-5-mini-2025-08-07", "GPT-5 Mini"),
        "2": ("gpt-4.1-2025-04-14", "GPT-4.1"),
        "3": ("claude-3-5-haiku-20241022", "Claude 3.5 Haiku"),
        "4": ("claude-haiku-4-5-20251001", "Claude Haiku 4.5"),
    }

    if choice == "5" and openai_key and anthropic_key:
        models_to_test = [
            ("gpt-5-mini-2025-08-07", "GPT-5 Mini"),
            ("gpt-4.1-2025-04-14", "GPT-4.1"),
            ("claude-3-5-haiku-20241022", "Claude 3.5 Haiku"),
            ("claude-haiku-4-5-20251001", "Claude Haiku 4.5"),
        ]
    elif choice in choice_map:
        model_id, model_name = choice_map[choice]
        if choice in ["1", "2"] and openai_key:
            models_to_test = [(model_id, model_name)]
        elif choice in ["3", "4"] and anthropic_key:
            models_to_test = [(model_id, model_name)]
        else:
            print("\nInvalid choice or API key not available.")
            return
    else:
        print("\nInvalid choice.")
        return

    num_experiments = 16
    total_experiments = num_experiments * len(models_to_test)

    print("\n" + "="*70)
    print("EXPERIMENT DETAILS")
    print("="*70)
    print(f"Models to test:      {len(models_to_test)}")
    for model_id, model_name in models_to_test:
        print(f"   - {model_name}")
    print(f"Experiments per model: {num_experiments}")
    print(f"Total experiments:     {total_experiments}")
    print(f"Estimated time:        {total_experiments * 30 // 60} minutes")

    if len(models_to_test) > 1:
        print("\nNOTE: Running multiple models will generate comparison analysis!")

    print("\n   Continue? (y/n): ", end="")
    confirm = input().strip().lower()
    if confirm not in ['y', 'yes']:
        print("\nCancelled by user.")
        return

    all_results = []

    for model_id, model_name in models_to_test:
        print("\n" + "="*70)
        print(f"TESTING {model_name.upper()}")
        print("="*70)

        try:

            print(f"\nInitializing {model_name} agent...")
            agent = create_agent(model_id)

            runner = ExperimentRunner(agent)

            baseline_results = runner.run_baseline_tests(num_runs=3)
            runner.results.extend(baseline_results)

            attack_results = runner.run_attack_tests()
            runner.results.extend(attack_results)

            model_filename = f"experiment_results_{model_id}.json"
            runner.save_results(filename=model_filename)

            all_results.extend(runner.results)

        except Exception as e:
            print(f"\nERROR testing {model_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    if len(models_to_test) > 1:
        print("\n" + "="*70)
        print("SAVING COMBINED RESULTS")
        print("="*70)

        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        combined_filename = "experiment_results_combined.json"
        filepath = os.path.join(results_dir, combined_filename)
        with open(filepath, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"Combined results saved to: {filepath}")

    print("\n" + "="*70)
    print("ANALYZING RESULTS")
    print("="*70)

    try:
        if len(models_to_test) > 1:

            analyzer = analyze_results("experiment_results_combined.json")
        else:

            model_id, model_name = models_to_test[0]
            analyzer = analyze_results(f"experiment_results_{model_id}.json")

        print("\n" + "="*70)
        print("ALL EXPERIMENTS COMPLETE!")
        print("="*70)

        print("\nFiles generated:")
        if len(models_to_test) == 1:
            model_id, model_name = models_to_test[0]
            print(f"   - experiment_results_{model_id}.json  (raw data)")
        else:
            for model_id, model_name in models_to_test:
                print(f"   - experiment_results_{model_id}.json ({model_name} data)")
            print(f"   - experiment_results_combined.json (all models)")
        print("   - analysis_report.txt (summary report)")

    except Exception as e:
        print(f"\nERROR during analysis: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nWARNING: Interrupted by user. Partial results may be saved.")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()