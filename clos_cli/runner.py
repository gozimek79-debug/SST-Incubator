"""CLI Runner v0.8."""

import sys, os
sys.path.insert(0, os.getcwd())

def run_academy():
    from clos_academy import run_lesson_L1_1
    run_lesson_L1_1()

def run_school():
    from clos_curriculum.academy.levels import get_level
    from clos_curriculum.laboratory.runner import run_lesson
    import json
    print("=" * 60)
    print("CLOS Cognitive Research Curriculum v0.8")
    print("SCHOOL FOR BRAIN")
    print("=" * 60)
    level0 = get_level(0)
    print(f"\n{level0.summary()}")
    results = {}
    for lesson in level0.lessons:
        result = run_lesson(lesson)
        results[lesson.lesson_id] = result
    print(f"\n--- LEVEL 0 EXAM ---")
    exam_result = run_lesson(level0.exam[0])
    results["EXAM0"] = exam_result
    passed_lessons = sum(1 for r in results.values() if r["grade"] == "PASS")
    total_lessons = len(results)
    exam_passed = exam_result["grade"] == "PASS"
    level_passed = exam_passed and passed_lessons >= total_lessons * level0.required_pass_rate
    print(f"\n{'='*60}")
    print(f"LEVEL 0 RESULT: {'PASS' if level_passed else 'FAIL'}")
    print(f"  Lessons: {passed_lessons}/{total_lessons}")
    print(f"  Exam: {'PASS' if exam_passed else 'FAIL'}")
    print(f"{'='*60}")
    os.makedirs("reports/crc", exist_ok=True)
    report_path = f"reports/crc/level0_{'PASS' if level_passed else 'FAIL'}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"level":0,"level_passed":level_passed,"exam_passed":exam_passed,"passed_lessons":passed_lessons,"total_lessons":total_lessons,"results":{k:{kk:vv for kk,vv in v.items() if kk!="runs"} for k,v in results.items()}},f,indent=2,ensure_ascii=False,default=str)
    print(f"Report saved: {report_path}")

def run_matrix(manifest_path: str):
    from clos_studio.execution.matrix_runner import MatrixRunner
    runner = MatrixRunner()
    try: runner.run(manifest_path)
    finally: runner.close()

def run_experiment(manifest_path: str):
    from clos_studio.cli.commands import run_experiment_from_manifest
    run_experiment_from_manifest(manifest_path)

def run_demo(seed: int, ticks: int, stream: bool = False, genome: str = "default", scenario: str = "shock_world", telemetry: int = 0):
    import run_demo
    return run_demo.main(seed=seed, ticks=ticks, stream=stream, genome_preset=genome, scenario=scenario, telemetry_interval=telemetry)

def run_compare(seed: int, ticks: int):
    import run_compare; run_compare.main(seed=seed, ticks=ticks)

def run_benchmark(seed: int, ticks: int):
    import run_benchmark; run_benchmark.main(seed=seed, ticks=ticks)

def run_dashboard(seed: int, ticks: int):
    import run_dashboard; run_dashboard.main(seed=seed, ticks=ticks)
