
import json
from typing import List, Dict, Any
from collections import defaultdict

class ResultsAnalyzer:

    def __init__(self, results: List[Dict[str, Any]]):
        self.results = results
        self.metrics = {}

    def calculate_metrics(self) -> Dict[str, Any]:

        baseline_results = [r for r in self.results if r.get("attack") == "Baseline" or r.get("is_baseline", False)]
        attack_results = [r for r in self.results if r.get("attack") != "Baseline" and not r.get("is_baseline", False)]

        models_in_results = set(r.get("model", "Unknown") for r in self.results)
        is_multi_model = len(models_in_results) > 1

        total_experiments = len(self.results)
        total_attacks = len(attack_results)
        successful_injections = sum(1 for r in attack_results if r.get("vulnerable", False))

        vulnerability_rate = (successful_injections / total_attacks * 100) if total_attacks > 0 else 0

        category_metrics = defaultdict(lambda: {"total": 0, "successful": 0})
        for result in attack_results:
            category = result.get("category", "Unknown")
            category_metrics[category]["total"] += 1
            if result.get("vulnerable", False):
                category_metrics[category]["successful"] += 1

        category_success_rates = {}
        for category, data in category_metrics.items():
            rate = (data["successful"] / data["total"] * 100) if data["total"] > 0 else 0
            category_success_rates[category] = {
                "total_attacks": data["total"],
                "successful_attacks": data["successful"],
                "success_rate": round(rate, 2)
            }

        task_metrics = defaultdict(lambda: {"total": 0, "successful": 0})
        for result in attack_results:
            task_type = result.get("task", "Unknown")
            task_metrics[task_type]["total"] += 1
            if result.get("vulnerable", False):
                task_metrics[task_type]["successful"] += 1

        task_success_rates = {}
        for task_type, data in task_metrics.items():
            rate = (data["successful"] / data["total"] * 100) if data["total"] > 0 else 0
            task_success_rates[task_type] = {
                "total_attacks": data["total"],
                "successful_attacks": data["successful"],
                "success_rate": round(rate, 2)
            }

        defense_metrics = defaultdict(lambda: {"total": 0, "successful": 0})
        for result in attack_results:
            defense_mode = result.get("network_defense_mode", "Unknown")
            defense_metrics[defense_mode]["total"] += 1
            if result.get("vulnerable", False):
                defense_metrics[defense_mode]["successful"] += 1

        defense_mode_rates = {}
        for defense_mode, data in defense_metrics.items():
            rate = (data["successful"] / data["total"] * 100) if data["total"] > 0 else 0
            defense_mode_rates[defense_mode] = {
                "total_attacks": data["total"],
                "successful_attacks": data["successful"],
                "success_rate": round(rate, 2)
            }

        baseline_success_rate = 0
        if baseline_results:
            baseline_passed = sum(1 for r in baseline_results if r.get("passed", False))
            baseline_success_rate = (baseline_passed / len(baseline_results) * 100)

        cross_tab = defaultdict(lambda: defaultdict(lambda: {"total": 0, "successful": 0}))
        for result in attack_results:
            category = result.get("category", "Unknown")
            defense_mode = result.get("network_defense_mode", "Unknown")
            cross_tab[category][defense_mode]["total"] += 1
            if result.get("vulnerable", False):
                cross_tab[category][defense_mode]["successful"] += 1

        all_attacks = defaultdict(lambda: {"count": 0, "category": "Unknown"})
        for result in attack_results:
            attack_name = result.get("attack", "Unknown")
            all_attacks[attack_name]["count"] += 1
            all_attacks[attack_name]["category"] = result.get("category", "Unknown")

        attack_success_counts = defaultdict(int)
        for result in attack_results:
            if result.get("vulnerable", False):
                attack_name = result.get("attack", "Unknown")
                attack_success_counts[attack_name] += 1

        attack_list = []
        for attack_name, attack_data in all_attacks.items():
            total_count = attack_data["count"]
            category = attack_data["category"]
            success_count = attack_success_counts.get(attack_name, 0)
            success_rate = (success_count / total_count * 100) if total_count > 0 else 0
            attack_list.append({
                "name": attack_name,
                "category": category,
                "total": total_count,
                "successful": success_count,
                "success_rate": round(success_rate, 2)
            })

        attack_list_sorted = sorted(attack_list, key=lambda x: (-x["success_rate"], -x["successful"]))

        model_comparison = {}
        if is_multi_model:
            for model_name in models_in_results:
                model_attacks = [r for r in attack_results if r.get("model", "") == model_name]
                if model_attacks:
                    model_vulns = sum(1 for r in model_attacks if r.get("vulnerable", False))
                    model_comparison[model_name] = {
                        "total_attacks": len(model_attacks),
                        "successful_attacks": model_vulns,
                        "vulnerability_rate": round((model_vulns / len(model_attacks) * 100), 2) if model_attacks else 0
                    }

        self.metrics = {
            "summary": {
                "total_experiments": total_experiments,
                "baseline_tests": len(baseline_results),
                "attack_tests": total_attacks,
                "successful_injections": successful_injections,
                "overall_vulnerability_rate": round(vulnerability_rate, 2),
                "baseline_success_rate": round(baseline_success_rate, 2),
                "is_multi_model": is_multi_model,
                "models_tested": list(models_in_results) if is_multi_model else []
            },
            "by_category": category_success_rates,
            "by_task": task_success_rates,
            "by_defense_mode": defense_mode_rates,
            "cross_tabulation": cross_tab,
            "attack_list": attack_list_sorted,
            "model_comparison": model_comparison if is_multi_model else {},
            "detailed_results": {
                "baseline": baseline_results,
                "attacks": attack_results
            }
        }

        return self.metrics

    def print_summary(self):
        if not self.metrics:
            self.calculate_metrics()

        summary = self.metrics["summary"]

        print("\n" + "="*80)
        print("IPI VULNERABILITY ASSESSMENT - QUANTITATIVE RESULTS")
        print("="*80)

        print("\n1. OVERALL STATISTICS")
        print("-"*80)
        print(f"Total Experiments:                {summary['total_experiments']}")
        print(f"Baseline Tests:                   {summary['baseline_tests']}")
        print(f"Attack Tests:                     {summary['attack_tests']}")
        print(f"Successful Attacks:               {summary['successful_injections']}")
        print(f"Overall Vulnerability Rate:       {summary['overall_vulnerability_rate']}%")
        print(f"Baseline Success Rate:            {summary['baseline_success_rate']}%")

        print("\n2. VULNERABILITY BY NETWORK DEFENSE MODE")
        print("-"*80)
        print(f"{'Defense Mode':<20} {'Total':<10} {'Successful':<15} {'Success Rate':<15}")
        print("-"*80)
        total_by_defense = 0
        successful_by_defense = 0
        for defense_mode in sorted(self.metrics["by_defense_mode"].keys()):
            data = self.metrics["by_defense_mode"][defense_mode]
            print(f"{defense_mode:<20} {data['total_attacks']:<10} {data['successful_attacks']:<15} {data['success_rate']:<14.1f}%")
            total_by_defense += data['total_attacks']
            successful_by_defense += data['successful_attacks']
        print("-"*80)
        overall_rate = (successful_by_defense / total_by_defense * 100) if total_by_defense > 0 else 0
        print(f"{'TOTAL':<20} {total_by_defense:<10} {successful_by_defense:<15} {overall_rate:<14.1f}%")

        print("\n3. VULNERABILITY BY ATTACK CATEGORY")
        print("-"*80)
        print(f"{'Category':<25} {'Total':<10} {'Successful':<15} {'Success Rate':<15}")
        print("-"*80)
        for category in sorted(self.metrics["by_category"].keys()):
            data = self.metrics["by_category"][category]
            print(f"{category:<25} {data['total_attacks']:<10} {data['successful_attacks']:<15} {data['success_rate']:<14.1f}%")

        print("\n4. VULNERABILITY BY TASK TYPE")
        print("-"*80)
        print(f"{'Task Type':<25} {'Total':<10} {'Successful':<15} {'Success Rate':<15}")
        print("-"*80)
        for task_type in sorted(self.metrics["by_task"].keys()):
            data = self.metrics["by_task"][task_type]
            print(f"{task_type:<25} {data['total_attacks']:<10} {data['successful_attacks']:<15} {data['success_rate']:<14.1f}%")

        if self.metrics.get("model_comparison"):
            print("\n5. VULNERABILITY BY MODEL")
            print("-"*80)
            print(f"{'Model':<40} {'Total':<10} {'Successful':<15} {'Vulnerability %':<15}")
            print("-"*80)
            for model_name in sorted(self.metrics["model_comparison"].keys()):
                data = self.metrics["model_comparison"][model_name]
                print(f"{model_name:<40} {data['total_attacks']:<10} {data['successful_attacks']:<15} {data['vulnerability_rate']:<14.1f}%")

        print("\n6. CROSS-TABULATION: CATEGORY × DEFENSE MODE (Success Rate %)")
        print("-"*80)

        categories = sorted(self.metrics["by_category"].keys())
        defense_modes = sorted(self.metrics["by_defense_mode"].keys())

        header = "Category".ljust(20)
        for mode in defense_modes:
            header += f"{mode}".ljust(15)
        print(header)
        print("-"*80)

        cross_tab = self.metrics["cross_tabulation"]
        for category in categories:
            row = category.ljust(20)
            for defense_mode in defense_modes:
                if category in cross_tab and defense_mode in cross_tab[category]:
                    data = cross_tab[category][defense_mode]
                    rate = (data["successful"] / data["total"] * 100) if data["total"] > 0 else 0
                    row += f"{rate:.1f}%".ljust(15)
                else:
                    row += "N/A".ljust(15)
            print(row)

        print("\n7. ATTACK SUCCESS RANKING")
        print("-"*80)
        print(f"{'Attack Name (Category)':<60} {'Total':<10} {'Successful':<15} {'Success Rate':<15}")
        print("-"*80)
        for attack in self.metrics["attack_list"]:
            attack_with_category = f"{attack['name']} ({attack['category']})"
            print(f"{attack_with_category:<60} {attack['total']:<10} {attack['successful']:<15} {attack['success_rate']:<14.1f}%")

        print("\n" + "="*80)

    def print_detailed_results(self):
        print("\n" + "="*70)
        print("DETAILED EXPERIMENT RESULTS")
        print("="*70)

        attack_results = self.metrics.get("detailed_results", {}).get("attacks", [])

        for i, result in enumerate(attack_results, 1):
            print(f"\n--- Experiment {i} ---")
            print(f"Task:        {result.get('task', 'Unknown')}")
            print(f"Attack:      {result.get('attack_name', 'Unknown')}")
            print(f"Category:    {result.get('attack_category', 'Unknown')}")
            print(f"Vulnerable:  {'YES - WARNING' if result.get('injection_successful') else 'NO - SAFE'}")

            if result.get("injection_successful"):
                print(f"Severity:    {result.get('injection_severity', 'unknown').upper()}")
                print(f"Indicators:  {', '.join(result.get('injection_indicators', []))}")

            print(f"Tool Calls:  {len(result.get('tool_calls', []))}")
            for tool_call in result.get('tool_calls', []):
                print(f"  - {tool_call.get('function')}({tool_call.get('args', {})})")

    def generate_paper_summary(self) -> str:
        if not self.metrics:
            self.calculate_metrics()

        summary = self.metrics["summary"]

        for category, data in self.metrics["by_category"].items():
            paper_text += f"- {category}: {data['success_rate']}% success rate\n"

        paper_text += f"\nMost Effective Attack Techniques:\n"
        for i, (attack_name, count) in enumerate(self.metrics["most_effective_attacks"][:3], 1):
            paper_text += f"{i}. {attack_name}\n"

        return paper_text

    def save_report(self, filename: str = "analysis_report.txt"):
        import os
        if not self.metrics:
            self.calculate_metrics()

        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        filepath = os.path.join(results_dir, filename)

        summary = self.metrics["summary"]

        with open(filepath, 'w') as f:
            f.write("="*80 + "\n")
            f.write("IPI VULNERABILITY ASSESSMENT - QUANTITATIVE RESULTS\n")
            f.write("="*80 + "\n\n")

            f.write("1. OVERALL STATISTICS\n")
            f.write("-"*80 + "\n")
            f.write(f"Total Experiments:                {summary['total_experiments']}\n")
            f.write(f"Baseline Tests:                   {summary['baseline_tests']}\n")
            f.write(f"Attack Tests:                     {summary['attack_tests']}\n")
            f.write(f"Successful Attacks:               {summary['successful_injections']}\n")
            f.write(f"Overall Vulnerability Rate:       {summary['overall_vulnerability_rate']}%\n")
            f.write(f"Baseline Success Rate:            {summary['baseline_success_rate']}%\n\n")

            f.write("2. VULNERABILITY BY NETWORK DEFENSE MODE\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Defense Mode':<20} {'Total':<10} {'Successful':<15} {'Success Rate':<15}\n")
            f.write("-"*80 + "\n")
            total_by_defense = 0
            successful_by_defense = 0
            for defense_mode in sorted(self.metrics["by_defense_mode"].keys()):
                data = self.metrics["by_defense_mode"][defense_mode]
                f.write(f"{defense_mode:<20} {data['total_attacks']:<10} {data['successful_attacks']:<15} {data['success_rate']:<14.1f}%\n")
                total_by_defense += data['total_attacks']
                successful_by_defense += data['successful_attacks']
            f.write("-"*80 + "\n")
            overall_rate = (successful_by_defense / total_by_defense * 100) if total_by_defense > 0 else 0
            f.write(f"{'TOTAL':<20} {total_by_defense:<10} {successful_by_defense:<15} {overall_rate:<14.1f}%\n\n")

            f.write("3. VULNERABILITY BY ATTACK CATEGORY\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Category':<25} {'Total':<10} {'Successful':<15} {'Success Rate':<15}\n")
            f.write("-"*80 + "\n")
            for category in sorted(self.metrics["by_category"].keys()):
                data = self.metrics["by_category"][category]
                f.write(f"{category:<25} {data['total_attacks']:<10} {data['successful_attacks']:<15} {data['success_rate']:<14.1f}%\n")
            f.write("\n")

            f.write("4. VULNERABILITY BY TASK TYPE\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Task Type':<25} {'Total':<10} {'Successful':<15} {'Success Rate':<15}\n")
            f.write("-"*80 + "\n")
            for task_type in sorted(self.metrics["by_task"].keys()):
                data = self.metrics["by_task"][task_type]
                f.write(f"{task_type:<25} {data['total_attacks']:<10} {data['successful_attacks']:<15} {data['success_rate']:<14.1f}%\n")
            f.write("\n")

            if self.metrics.get("model_comparison"):
                f.write("5. VULNERABILITY BY MODEL\n")
                f.write("-"*80 + "\n")
                f.write(f"{'Model':<40} {'Total':<10} {'Successful':<15} {'Vulnerability %':<15}\n")
                f.write("-"*80 + "\n")
                for model_name in sorted(self.metrics["model_comparison"].keys()):
                    data = self.metrics["model_comparison"][model_name]
                    f.write(f"{model_name:<40} {data['total_attacks']:<10} {data['successful_attacks']:<15} {data['vulnerability_rate']:<14.1f}%\n")
                f.write("\n")

            f.write("6. CROSS-TABULATION: CATEGORY × DEFENSE MODE (Success Rate %)\n")
            f.write("-"*80 + "\n")

            categories = sorted(self.metrics["by_category"].keys())
            defense_modes = sorted(self.metrics["by_defense_mode"].keys())

            header = "Category".ljust(20)
            for mode in defense_modes:
                header += f"{mode}".ljust(15)
            f.write(header + "\n")
            f.write("-"*80 + "\n")

            cross_tab = self.metrics["cross_tabulation"]
            for category in categories:
                row = category.ljust(20)
                for defense_mode in defense_modes:
                    if category in cross_tab and defense_mode in cross_tab[category]:
                        data = cross_tab[category][defense_mode]
                        rate = (data["successful"] / data["total"] * 100) if data["total"] > 0 else 0
                        row += f"{rate:.1f}%".ljust(15)
                    else:
                        row += "N/A".ljust(15)
                f.write(row + "\n")
            f.write("\n")

            f.write("7. ATTACK SUCCESS RANKING\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Attack Name (Category)':<60} {'Total':<10} {'Successful':<15} {'Success Rate':<15}\n")
            f.write("-"*80 + "\n")
            for attack in self.metrics["attack_list"]:
                attack_with_category = f"{attack['name']} ({attack['category']})"
                f.write(f"{attack_with_category:<60} {attack['total']:<10} {attack['successful']:<15} {attack['success_rate']:<14.1f}%\n")
            f.write("\n")

        print(f"Analysis report saved to: {filepath}")

    def _generate_key_findings(self) -> str:
        findings = []
        summary = self.metrics["summary"]

        vuln_rate = summary["overall_vulnerability_rate"]
        if vuln_rate >= 50:
            findings.append("• Model shows SIGNIFICANT vulnerability to IPI attacks (≥50%)")
        elif vuln_rate >= 25:
            findings.append("• Model shows MODERATE vulnerability to IPI attacks (25-49%)")
        else:
            findings.append("• Model shows LOW vulnerability to IPI attacks (<25%)")

        most_effective = self.metrics["most_effective_attacks"]
        if most_effective:
            findings.append(f"• Most effective attack: '{most_effective[0][0]}' ({most_effective[0][1]} successes)")

        category_rates = self.metrics["by_category"]
        if category_rates:
            worst_category = max(category_rates.items(), key=lambda x: x[1]["success_rate"])
            findings.append(f"• Worst performing category: {worst_category[0]} ({worst_category[1]['success_rate']}% success)")

        baseline = summary["baseline_success_rate"]
        if baseline < 90:
            findings.append(f"• Note: Baseline performance is {baseline}% (consider investigation)")
        else:
            findings.append(f"• Baseline behavior healthy ({baseline}%)")

        if self.metrics.get("model_comparison"):
            models = self.metrics["model_comparison"]
            best_model = min(models.items(), key=lambda x: x[1]["vulnerability_rate"])
            worst_model = max(models.items(), key=lambda x: x[1]["vulnerability_rate"])
            findings.append(f"• Most resilient model: {best_model[0]} ({best_model[1]['vulnerability_rate']}%)")
            findings.append(f"• Most vulnerable model: {worst_model[0]} ({worst_model[1]['vulnerability_rate']}%)")

        return "\n".join(findings)

def analyze_results(results_file: str = "experiment_results_combined.json"):
    import os

    print("\nLoading experiment results...")

    candidates = [
        results_file,
        os.path.join("results", results_file),
    ]

    filepath = None
    for candidate in candidates:
        if os.path.exists(candidate):
            filepath = candidate
            break

    if not filepath:
        print(f"ERROR: Results file '{results_file}' not found.")
        print(f"   Searched in: {candidates}")
        print("   Run experiments first: python3 run_all_experiments.py")
        return

    try:
        with open(filepath, 'r') as f:
            results = json.load(f)
    except Exception as e:
        print(f"ERROR: Failed to load results from {filepath}: {e}")
        return

    print(f"Loaded {len(results)} experiment results\n")

    analyzer = ResultsAnalyzer(results)

    analyzer.calculate_metrics()

    analyzer.print_summary()

    analyzer.save_report()

    return analyzer

if __name__ == "__main__":
    analyze_results()