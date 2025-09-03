"""
Scoring system for AI Code Benchmark
"""

from typing import Any


class BenchmarkScorer:
    """Handles scoring and grading for the benchmark."""

    def __init__(self) -> None:
        self.grade_thresholds = {
            "A+": 95,
            "A": 90,
            "A-": 85,
            "B+": 80,
            "B": 75,
            "B-": 70,
            "C+": 65,
            "C": 60,
            "F": 0,
        }

        self.prompt_weights = {
            "prompt_1": 1.0,  # All prompts weighted equally
            "prompt_2": 1.0,
            "prompt_3": 1.0,
            "prompt_4": 1.0,
        }

    def calculate_grade(self, percentage: float) -> str:
        """Convert percentage score to letter grade."""
        for grade, threshold in self.grade_thresholds.items():
            if percentage >= threshold:
                return grade
        return "F"

    def generate_feedback_summary(self, results: dict[str, Any]) -> list[str]:
        """Generate high-level feedback based on results."""
        feedback = []

        if "prompts" not in results:
            return ["No test results available"]

        prompts = results["prompts"]

        # Overall performance
        percentage = results.get("percentage", 0)
        grade = self.calculate_grade(percentage)

        if percentage >= 90:
            feedback.append(f"🌟 Excellent performance! Grade: {grade}")
        elif percentage >= 75:
            feedback.append(f"👍 Good performance! Grade: {grade}")
        elif percentage >= 60:
            feedback.append(f"✓ Satisfactory performance. Grade: {grade}")
        else:
            feedback.append(f"⚠️ Needs improvement. Grade: {grade}")

        # Prompt-specific feedback
        strengths = []
        weaknesses = []

        prompt_names = {
            "prompt_1": "Code Refactoring",
            "prompt_2": "YAML/JSON Handling",
            "prompt_3": "Data Transformation",
            "prompt_4": "API Integration",
        }

        for prompt_id, prompt_result in prompts.items():
            if "error" in prompt_result:
                weaknesses.append(f"{prompt_names.get(prompt_id, prompt_id)} (Error)")
                continue

            score = prompt_result.get("score", 0)
            max_score = prompt_result.get("max_score", 25)
            percentage = (score / max_score * 100) if max_score > 0 else 0

            if percentage >= 80:
                strengths.append(prompt_names.get(prompt_id, prompt_id))
            elif percentage < 60:
                weaknesses.append(prompt_names.get(prompt_id, prompt_id))

        if strengths:
            feedback.append(f"💪 Strengths: {', '.join(strengths)}")

        if weaknesses:
            feedback.append(f"📚 Areas for improvement: {', '.join(weaknesses)}")

        return feedback

    def generate_improvement_suggestions(self, results: dict[str, Any]) -> list[str]:
        """Generate specific improvement suggestions based on test results."""
        suggestions = []

        if "prompts" not in results:
            return suggestions

        prompts = results["prompts"]

        # Prompt 1 suggestions
        if "prompt_1" in prompts:
            p1 = prompts["prompt_1"]
            tests = p1.get("tests_passed", {})

            if not tests.get("valid_python"):
                suggestions.append("📌 Fix Python syntax errors in your refactored code")
            elif not tests.get("runs_successfully"):
                suggestions.append("📌 Ensure your refactored script runs without runtime errors")
            elif not tests.get("good_structure"):
                suggestions.append(
                    "📌 Add error handling, logging, and type hints to improve code structure"
                )

        # Prompt 2 suggestions
        if "prompt_2" in prompts:
            p2 = prompts["prompt_2"]
            tests = p2.get("tests_passed", {})

            if not tests.get("valid_yaml"):
                suggestions.append("📌 Fix YAML indentation and syntax issues")
            elif not tests.get("correct_types"):
                suggestions.append(
                    "📌 Ensure proper data type conversion (strings to numbers/booleans)"
                )

        # Prompt 3 suggestions
        if "prompt_3" in prompts:
            p3 = prompts["prompt_3"]
            tests = p3.get("tests_passed", {})

            if not tests.get("no_crash"):
                suggestions.append(
                    "📌 Add error handling to prevent crashes in data transformation"
                )
            elif not tests.get("email_provider"):
                suggestions.append("📌 Handle edge cases like null emails in transformation")
            elif not tests.get("account_tiers"):
                suggestions.append("📌 Review account tier calculation logic")

        # Prompt 4 suggestions
        if "prompt_4" in prompts:
            p4 = prompts["prompt_4"]
            tests = p4.get("tests_passed", {})

            if not tests.get("uses_requests"):
                suggestions.append("📌 Use the requests library for API calls")
            elif not tests.get("error_handling"):
                suggestions.append(
                    "📌 Add comprehensive error handling for network and HTTP errors"
                )

        return suggestions

    def compare_models(self, all_results: dict[str, Any]) -> dict[str, Any]:
        """Generate detailed model comparison analysis."""
        if "models" not in all_results:
            return {}

        models = all_results["models"]
        comparison = {
            "best_overall": None,
            "best_by_prompt": {},
            "consistency_analysis": {},
            "detailed_comparison": [],
        }

        # Find best overall
        best_score = 0
        for model_name, model_result in models.items():
            if "error" not in model_result:
                score = model_result.get("overall_score", 0)
                if score > best_score:
                    best_score = score
                    comparison["best_overall"] = {
                        "model": model_name,
                        "score": score,
                        "percentage": model_result.get("percentage", 0),
                    }

        # Find best by prompt
        for prompt_id in ["prompt_1", "prompt_2", "prompt_3", "prompt_4"]:
            best_prompt_score = 0
            best_prompt_model = None

            for model_name, model_result in models.items():
                if "error" not in model_result and "prompts" in model_result:
                    prompt_result = model_result["prompts"].get(prompt_id, {})
                    score = prompt_result.get("score", 0)

                    if score > best_prompt_score:
                        best_prompt_score = score
                        best_prompt_model = model_name

            if best_prompt_model:
                comparison["best_by_prompt"][prompt_id] = {
                    "model": best_prompt_model,
                    "score": best_prompt_score,
                }

        # Consistency analysis
        for model_name, model_result in models.items():
            if "error" not in model_result and "prompts" in model_result:
                scores = []
                for _prompt_id, prompt_result in model_result["prompts"].items():
                    if "score" in prompt_result:
                        max_score = prompt_result.get("max_score", 25)
                        percentage = (
                            (prompt_result["score"] / max_score * 100) if max_score > 0 else 0
                        )
                        scores.append(percentage)

                if scores:
                    avg_score = sum(scores) / len(scores)
                    variance = sum((s - avg_score) ** 2 for s in scores) / len(scores)
                    std_dev = variance**0.5

                    comparison["consistency_analysis"][model_name] = {
                        "average_percentage": round(avg_score, 1),
                        "standard_deviation": round(std_dev, 1),
                        "consistency_rating": "High"
                        if std_dev < 10
                        else "Medium"
                        if std_dev < 20
                        else "Low",
                    }

        return comparison

    def generate_badge(self, percentage: float) -> str:
        """Generate a badge/achievement based on performance."""
        if percentage >= 95:
            return "🏆 AI Code Master"
        elif percentage >= 90:
            return "🥇 Expert Coder"
        elif percentage >= 80:
            return "🥈 Proficient Developer"
        elif percentage >= 70:
            return "🥉 Competent Programmer"
        elif percentage >= 60:
            return "✅ Certified Pass"
        else:
            return "📚 Keep Learning"
