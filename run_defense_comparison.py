import sys
import os
import json
from datetime import datetime
from collections import defaultdict

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("WARNING: python-dotenv not installed. Make sure .env file is loaded.")

from experiment_runner import ExperimentRunner
from llm_agent import create_agent
from results_analyzer import ResultsAnalyzer

def create_defense_comparison_report(on_results, off_results, model_name):
    """
    Create a detailed comparison report showing defense mode impact.
    """
    
    report = []
    report.append("=" * 90)
    report.append("DEFENSE MODE COMPARISON ANALYSIS")
    report.append(f"Model: {model_name}")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 90)
    report.append("")
    
    # Overall statistics
    on_attacks = [r for r in on_results if not r.get("is_baseline", False)]
    off_attacks = [r for r in off_results if not r.get("is_baseline", False)]
    
    on_vulnerable = sum(1 for r in on_attacks if r.get("vulnerable", False))
    off_vulnerable = sum(1 for r in off_attacks if r.get("vulnerable", False))
    
    on_rate = (on_vulnerable / len(on_attacks) * 100) if on_attacks else 0
    off_rate = (off_vulnerable / len(off_attacks) * 100) if off_attacks else 0
    defense_impact = off_rate - on_rate
    
    report.append("1. OVERALL DEFENSE IMPACT")
    report.append("-" * 90)
    report.append(f"Total Attacks Tested:              {len(on_attacks)}")
    report.append("")
    report.append(f"With Defense Mode ON:")
    report.append(f"  - Vulnerable: {on_vulnerable}/{len(on_attacks)}")
    report.append(f"  - Vulnerability Rate: {on_rate:.2f}%")
    report.append("")
    report.append(f"With Defense Mode OFF:")
    report.append(f"  - Vulnerable: {off_vulnerable}/{len(off_attacks)}")
    report.append(f"  - Vulnerability Rate: {off_rate:.2f}%")
    report.append("")
    report.append(f"Defense Effectiveness:")
    report.append(f"  - Impact: {defense_impact:.2f}% (Firewall reduced vulnerability by {abs(defense_impact):.2f}%)")
    if defense_impact < 0:
        report.append(f"  - Status: ✓ EFFECTIVE - Firewall helps defend against attacks")
    else:
        report.append(f"  - Status: ✗ LIMITED - Firewall has minimal impact")
    report.append("")
    
    # Category-wise comparison
    report.append("2. VULNERABILITY BY ATTACK CATEGORY")
    report.append("-" * 90)
    report.append(f"{'Category':<25} {'Defense ON':<20} {'Defense OFF':<20} {'Impact':<20}")
    report.append("-" * 90)
    
    category_on = defaultdict(lambda: {"total": 0, "vulnerable": 0})
    category_off = defaultdict(lambda: {"total": 0, "vulnerable": 0})
    
    for result in on_attacks:
        category = result.get("category", "Unknown")
        category_on[category]["total"] += 1
        if result.get("vulnerable", False):
            category_on[category]["vulnerable"] += 1
    
    for result in off_attacks:
        category = result.get("category", "Unknown")
        category_off[category]["total"] += 1
        if result.get("vulnerable", False):
            category_off[category]["vulnerable"] += 1
    
    for category in sorted(set(list(category_on.keys()) + list(category_off.keys()))):
        on_data = category_on[category]
        off_data = category_off[category]
        
        on_rate_cat = (on_data["vulnerable"] / on_data["total"] * 100) if on_data["total"] > 0 else 0
        off_rate_cat = (off_data["vulnerable"] / off_data["total"] * 100) if off_data["total"] > 0 else 0
        impact_cat = off_rate_cat - on_rate_cat
        
        on_str = f"{on_rate_cat:.1f}% ({on_data['vulnerable']}/{on_data['total']})"
        off_str = f"{off_rate_cat:.1f}% ({off_data['vulnerable']}/{off_data['total']})"
        impact_str = f"{impact_cat:+.1f}%"
        
        report.append(f"{category:<25} {on_str:<20} {off_str:<20} {impact_str:<20}")
    
    report.append("")
    
    # Task-wise comparison
    report.append("3. VULNERABILITY BY TASK TYPE")
    report.append("-" * 90)
    report.append(f"{'Task Type':<25} {'Defense ON':<20} {'Defense OFF':<20} {'Impact':<20}")
    report.append("-" * 90)
    
    task_on = defaultdict(lambda: {"total": 0, "vulnerable": 0})
    task_off = defaultdict(lambda: {"total": 0, "vulnerable": 0})
    
    for result in on_attacks:
        task = result.get("task", "Unknown")
        task_on[task]["total"] += 1
        if result.get("vulnerable", False):
            task_on[task]["vulnerable"] += 1
    
    for result in off_attacks:
        task = result.get("task", "Unknown")
        task_off[task]["total"] += 1
        if result.get("vulnerable", False):
            task_off[task]["vulnerable"] += 1
    
    for task in sorted(set(list(task_on.keys()) + list(task_off.keys()))):
        on_data = task_on[task]
        off_data = task_off[task]
        
        on_rate_task = (on_data["vulnerable"] / on_data["total"] * 100) if on_data["total"] > 0 else 0
        off_rate_task = (off_data["vulnerable"] / off_data["total"] * 100) if off_data["total"] > 0 else 0
        impact_task = off_rate_task - on_rate_task
        
        on_str = f"{on_rate_task:.1f}% ({on_data['vulnerable']}/{on_data['total']})"
        off_str = f"{off_rate_task:.1f}% ({off_data['vulnerable']}/{off_data['total']})"
        impact_str = f"{impact_task:+.1f}%"
        
        report.append(f"{task:<25} {on_str:<20} {off_str:<20} {impact_str:<20}")
    
    report.append("")
    
    # Per-attack comparison
    report.append("4. PER-ATTACK DEFENSE EFFECTIVENESS")
    report.append("-" * 90)
    report.append(f"{'Attack Name':<50} {'Defense ON':<15} {'Defense OFF':<15} {'Impact':<15}")
    report.append("-" * 90)
    
    attack_on = defaultdict(lambda: {"total": 0, "vulnerable": 0})
    attack_off = defaultdict(lambda: {"total": 0, "vulnerable": 0})
    
    for result in on_attacks:
        attack = result.get("attack", "Unknown")
        attack_on[attack]["total"] += 1
        if result.get("vulnerable", False):
            attack_on[attack]["vulnerable"] += 1
    
    for result in off_attacks:
        attack = result.get("attack", "Unknown")
        attack_off[attack]["total"] += 1
        if result.get("vulnerable", False):
            attack_off[attack]["vulnerable"] += 1
    
    for attack in sorted(set(list(attack_on.keys()) + list(attack_off.keys()))):
        on_data = attack_on[attack]
        off_data = attack_off[attack]
        
        on_rate_attack = (on_data["vulnerable"] / on_data["total"] * 100) if on_data["total"] > 0 else 0
        off_rate_attack = (off_data["vulnerable"] / off_data["total"] * 100) if off_data["total"] > 0 else 0
        impact_attack = off_rate_attack - on_rate_attack
        
        on_str = f"{on_rate_attack:.1f}%"
        off_str = f"{off_rate_attack:.1f}%"
        impact_str = f"{impact_attack:+.1f}%"
        
        report.append(f"{attack:<50} {on_str:<15} {off_str:<15} {impact_str:<15}")
    
    report.append("")
    report.append("=" * 90)
    report.append("KEY INSIGHTS")
    report.append("=" * 90)
    
    # Key findings
    if defense_impact < -20:
        report.append("• Firewall is HIGHLY EFFECTIVE at reducing injection attacks")
    elif defense_impact < 0:
        report.append("• Firewall provides MODERATE protection against injection attacks")
    else:
        report.append("• Firewall has MINIMAL impact on injection attack success rates")
    
    worst_defense_cat = min(category_on.keys(), 
                           key=lambda c: -(category_off[c]["vulnerable"]/category_off[c]["total"]*100 if category_off[c]["total"] > 0 else 0))
    worst_defense_rate = (category_off[worst_defense_cat]["vulnerable"] / category_off[worst_defense_cat]["total"] * 100) if category_off[worst_defense_cat]["total"] > 0 else 0
    report.append(f"• Most dangerous category (Defense OFF): {worst_defense_cat} ({worst_defense_rate:.1f}% vulnerability)")
    
    best_defended_cat = max(category_on.keys(),
                           key=lambda c: (category_on[c]["total"] - category_on[c]["vulnerable"]) / category_on[c]["total"] * 100 if category_on[c]["total"] > 0 else 0)
    best_defended_rate = ((category_on[best_defended_cat]["total"] - category_on[best_defended_cat]["vulnerable"]) / category_on[best_defended_cat]["total"] * 100) if category_on[best_defended_cat]["total"] > 0 else 0
    report.append(f"• Best defended category (Defense ON): {best_defended_cat} ({best_defended_rate:.1f}% blocked)")
    
    report.append("")
    report.append("=" * 90)
    
    return "\n".join(report)

def main():
    print("\n" + "="*70)
    print("DEFENSE MODE COMPARISON - IPI VULNERABILITY TESTING")
    print("Testing attacks with Defense Mode ON vs OFF")
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

    num_attacks = 19
    total_experiments = num_attacks * 2 * len(models_to_test)  # 19 attacks × 2 defense modes

    print("\n" + "="*70)
    print("EXPERIMENT DETAILS")
    print("="*70)
    print(f"Models to test:           {len(models_to_test)}")
    for model_id, model_name in models_to_test:
        print(f"   - {model_name}")
    print(f"Attacks to test:          {num_attacks}")
    print(f"Defense modes:            2 (ON and OFF)")
    print(f"Total experiments:        {total_experiments}")
    print(f"Estimated time:           {total_experiments * 30 // 60} minutes")

    print("\n   Continue? (y/n): ", end="")
    confirm = input().strip().lower()
    if confirm not in ['y', 'yes']:
        print("\nCancelled by user.")
        return

    all_on_results = []
    all_off_results = []

    for model_id, model_name in models_to_test:
        print("\n" + "="*70)
        print(f"TESTING {model_name.upper()}")
        print("="*70)

        try:
            print(f"\nInitializing {model_name} agent...")
            agent = create_agent(model_id)

            # Test with Defense Mode ON
            print("\n" + "="*70)
            print(f"DEFENSE MODE ON - {model_name}")
            print("="*70)
            runner_on = ExperimentRunner(agent)
            attacks_on = runner_on.run_attack_tests()
            runner_on.results.extend(attacks_on)
            
            model_filename_on = f"experiment_results_{model_id}_defense_on.json"
            runner_on.save_results(filename=model_filename_on)
            all_on_results.extend(runner_on.results)

            # Test with Defense Mode OFF
            print("\n" + "="*70)
            print(f"DEFENSE MODE OFF - {model_name}")
            print("="*70)
            
            # Create new agent for fresh state
            agent = create_agent(model_id)
            runner_off = ExperimentRunner(agent)
            
            # Manually run attack tests with defense_mode="OFF"
            from injection_payloads import get_bill_attacks, get_landlord_attacks
            from banking_suite import ALL_TASKS
            import time
            
            bill_attacks = get_bill_attacks()
            landlord_attacks = get_landlord_attacks()
            
            print(f"\nTesting Task 2 (Bill Payment) with {len(bill_attacks)} attacks...")
            for i, attack in enumerate(bill_attacks, 1):
                print(f"\n   Attack {i}: {attack.name}")
                print(f"   Category: {attack.category}")
                print(f"   ", end="")

                result = runner_off.run_single_experiment(1, attack=attack, is_baseline=False, network_defense_mode="OFF")
                runner_off.results.append(result)

                if result["success"]:
                    if result["vulnerable"]:
                        print(f"WARNING: VULNERABLE - Injection succeeded!")
                    else:
                        print(f"SAFE - Attack blocked")
                else:
                    print(f"ERROR: {result.get('error', 'Unknown')}")

                time.sleep(1)

            print(f"\nTesting Task 3 (Rent Update) with {len(landlord_attacks)} attacks...")
            for i, attack in enumerate(landlord_attacks, 1):
                print(f"\n   Attack {i}: {attack.name}")
                print(f"   Category: {attack.category}")
                print(f"   ", end="")

                result = runner_off.run_single_experiment(2, attack=attack, is_baseline=False, network_defense_mode="OFF")
                runner_off.results.append(result)

                if result["success"]:
                    if result["vulnerable"]:
                        print(f"WARNING: VULNERABLE - Injection succeeded!")
                    else:
                        print(f"SAFE - Attack blocked")
                else:
                    print(f"ERROR: {result.get('error', 'Unknown')}")

                time.sleep(1)

            model_filename_off = f"experiment_results_{model_id}_defense_off.json"
            runner_off.save_results(filename=model_filename_off)
            all_off_results.extend(runner_off.results)

            # Generate comparison report for this model
            comparison_report = create_defense_comparison_report(runner_on.results, runner_off.results, model_name)
            
            results_dir = "results"
            os.makedirs(results_dir, exist_ok=True)
            comparison_file = os.path.join(results_dir, f"defense_comparison_{model_id}.txt")
            with open(comparison_file, 'w') as f:
                f.write(comparison_report)
            print(f"\n✓ Comparison report saved to: {comparison_file}")

        except Exception as e:
            print(f"\nERROR testing {model_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    if len(models_to_test) > 1:
        print("\n" + "="*70)
        print("GENERATING COMBINED COMPARISON REPORT")
        print("="*70)
        
        combined_report = create_defense_comparison_report(all_on_results, all_off_results, "All Models Combined")
        
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        combined_file = os.path.join(results_dir, "defense_comparison_combined.txt")
        with open(combined_file, 'w') as f:
            f.write(combined_report)
        print(f"✓ Combined comparison report saved to: {combined_file}")

    print("\n" + "="*70)
    print("DEFENSE MODE COMPARISON COMPLETE!")
    print("="*70)

    print("\nFiles generated:")
    for model_id, model_name in models_to_test:
        print(f"   - experiment_results_{model_id}_defense_on.json")
        print(f"   - experiment_results_{model_id}_defense_off.json")
        print(f"   - defense_comparison_{model_id}.txt")
    
    if len(models_to_test) > 1:
        print(f"   - defense_comparison_combined.txt")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nWARNING: Interrupted by user. Partial results may be saved.")
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
