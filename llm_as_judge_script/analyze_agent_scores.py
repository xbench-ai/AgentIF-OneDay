#!/usr/bin/env python3
"""
Agent Score Analysis Script

Reads score_result JSONL files and calculates score statistics for each Agent under the same scoring method.
Implements the "Agent Scores" functionality in the frontend statistics panel.

Usage:
    1. Modify the parameters in the ===== Configuration Section ===== below
    2. Run: python analyze_agent_scores.py

Calculation Method:
  - Percentage Score = Actual Score / Maximum Score × 100%
  - Maximum Score only includes positive scoring items (criterion_score > 0)
  - Actual Score = Σ(scores of criteria where satisfied=true)
  - Negative scoring items (score < 0) will deduct points when satisfied=true
  - Minimum score is 0
  - Average Percentage Score = Average of percentage scores across all different question_ids
  - Number of Different Questions = Count of distinct question_ids
"""

import json
import sys
from collections import defaultdict
from typing import Dict, List, Optional, Any


# ============================================================================
# ===== Configuration Section - Modify parameters here =====
# ============================================================================

# Path to the scoring results JSONL file
INPUT_FILE = "sample/sample_results_10.jsonl"

# Path to the complete question list JSONL file (leave empty to only check questions in result file)
# Used to identify which questions have no data in the result file
QUESTION_FILE = "sample/sample_questions_10.jsonl"

# Filter specific scoring method (leave empty to analyze all scoring methods)
# Example: "HUMAN", "OpenRouter-Gemini-3.0-Pro"
METHOD_FILTER = None

# Whether to show detailed scores for each question
SHOW_DETAILS = False

# Whether to only list all scoring methods (without analysis)
LIST_METHODS_ONLY = False

# Export to CSV file (leave empty to skip export)
EXPORT_CSV_FILE = ""

# Export to JSON file (leave empty to skip export)
EXPORT_JSON_FILE = ""

# ============================================================================
# ===== End of Configuration Section =====
# ============================================================================


def load_score_results(file_path: str) -> List[Dict[str, Any]]:
    """Load scoring results from JSONL format file"""
    results = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                results.append(data)
            except json.JSONDecodeError as e:
                print(f"Warning: JSON parsing failed at line {line_no}: {e}", file=sys.stderr)
    return results


def load_question_ids(file_path: str) -> set:
    """
    Load all question_ids from a JSONL format question file
    
    Args:
        file_path: Path to the JSONL format question file
        
    Returns:
        Set of question_ids
    """
    question_ids = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                question_id = data.get('question_id', '')
                if question_id:
                    question_ids.add(question_id)
            except json.JSONDecodeError as e:
                print(f"Warning: JSON parsing failed at line {line_no}: {e}", file=sys.stderr)
    return question_ids


def calculate_question_score(criteria: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Calculate the score for a single question
    
    Args:
        criteria: List of all scoring criterion results for this question
        
    Returns:
        Dictionary containing total_score, max_score, percentage
    """
    # Calculate maximum score (only positive scoring items)
    max_score = sum(c['criterion_score'] for c in criteria if c['criterion_score'] > 0)
    
    # Calculate actual score
    total_score = 0
    for c in criteria:
        if c.get('satisfied') is True:
            # When satisfied=True, add the score (positive adds, negative deducts)
            total_score += c['criterion_score']
    
    # Ensure minimum score is 0
    total_score = max(0, total_score)
    
    # Calculate percentage
    percentage = (total_score / max_score * 100) if max_score > 0 else 0.0
    
    return {
        'total_score': total_score,
        'max_score': max_score,
        'percentage': round(percentage, 2)
    }


def analyze_agent_scores(
    results: List[Dict[str, Any]],
    method_filter: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Analyze scores for each Agent
    
    Args:
        results: List of scoring results
        method_filter: Optional, filter specific scoring method
        
    Returns:
        Agent score statistics grouped by scoring method
    """
    # Group by method -> agent_name -> question_id -> [criteria]
    grouped: Dict[str, Dict[str, Dict[str, List]]] = defaultdict(
        lambda: defaultdict(lambda: defaultdict(list))
    )
    
    for r in results:
        method = r.get('method', '')
        agent_name = r.get('agent_name', '')
        question_id = r.get('question_id', '')
        
        if method_filter and method != method_filter:
            continue
        
        grouped[method][agent_name][question_id].append({
            'criterion_content': r.get('criterion_content', ''),
            'criterion_score': r.get('criterion_score', 0),
            'satisfied': r.get('satisfied'),
            'reasoning': r.get('reasoning', '')
        })
    
    # Calculate statistics for each Agent
    result_by_method: Dict[str, Dict[str, Any]] = {}
    
    for method, agents in grouped.items():
        agent_stats = []
        
        for agent_name, questions in agents.items():
            question_scores = []
            
            for question_id, criteria in questions.items():
                score_info = calculate_question_score(criteria)
                score_info['question_id'] = question_id
                score_info['criteria_count'] = len(criteria)
                question_scores.append(score_info)
            
            # Calculate average percentage score for this Agent
            if question_scores:
                avg_percentage = sum(q['percentage'] for q in question_scores) / len(question_scores)
                total_score_sum = sum(q['total_score'] for q in question_scores)
                max_score_sum = sum(q['max_score'] for q in question_scores)
            else:
                avg_percentage = 0.0
                total_score_sum = 0
                max_score_sum = 0
            
            agent_stats.append({
                'agent_name': agent_name,
                'average_percentage_score': round(avg_percentage, 2),
                'scored_questions': len(question_scores),
                'total_score': total_score_sum,
                'max_score': max_score_sum,
                'question_details': sorted(question_scores, key=lambda x: x['question_id'])
            })
        
        # Sort by average percentage score (highest to lowest)
        agent_stats.sort(key=lambda x: x['average_percentage_score'], reverse=True)
        
        result_by_method[method] = {
            'method': method,
            'agents': agent_stats,
            'total_agents': len(agent_stats)
        }
    
    return result_by_method


def print_results(results_by_method: Dict[str, Dict[str, Any]], show_details: bool = False):
    """Print analysis results"""
    for method, data in results_by_method.items():
        print("=" * 80)
        print(f"Scoring Method: {method}")
        print(f"Number of Agents: {data['total_agents']}")
        print("=" * 80)
        print()
        
        # Print table header
        print(f"{'Rank':<6}{'Agent Name':<30}{'Avg Score%':<12}{'Questions':<12}{'Total Score':<12}{'Max Score':<10}")
        print("-" * 82)
        
        for rank, agent in enumerate(data['agents'], 1):
            print(f"{rank:<6}{agent['agent_name']:<30}{agent['average_percentage_score']:<12.2f}"
                  f"{agent['scored_questions']:<12}{agent['total_score']:<12}{agent['max_score']:<10}")
        
        print()
        
        # Print bar chart (simple ASCII bar chart)
        print("Score Bar Chart (by Average Percentage Score)")
        print("-" * 82)
        
        max_bar_length = 50
        for agent in data['agents']:
            bar_length = int(agent['average_percentage_score'] / 100 * max_bar_length)
            bar = "█" * bar_length
            
            score = agent['average_percentage_score']
            print(f"{agent['agent_name'][:20]:<22} {bar} {score:.2f}%")
        
        print()
        
        # If details are requested
        if show_details:
            print("Question Details for Each Agent:")
            print("-" * 82)
            
            for agent in data['agents']:
                print(f"\n【{agent['agent_name']}】")
                print(f"  Average Score: {agent['average_percentage_score']:.2f}%")
                print(f"  Number of Questions: {agent['scored_questions']}")
                print()
                
                for q in agent['question_details']:
                    print(f"    {q['question_id']:<20} "
                          f"Score: {q['total_score']}/{q['max_score']} "
                          f"({q['percentage']:.2f}%) "
                          f"[{q['criteria_count']} criteria]")
            
            print()


def export_to_csv(results_by_method: Dict[str, Dict[str, Any]], output_file: str):
    """Export to CSV file"""
    import csv
    
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        
        # Write table header
        writer.writerow([
            'Scoring Method', 'Agent Name', 'Average Percentage Score', 'Number of Questions', 
            'Total Score', 'Max Score', 'Rank'
        ])
        
        for method, data in results_by_method.items():
            for rank, agent in enumerate(data['agents'], 1):
                writer.writerow([
                    method,
                    agent['agent_name'],
                    agent['average_percentage_score'],
                    agent['scored_questions'],
                    agent['total_score'],
                    agent['max_score'],
                    rank
                ])
    
    print(f"Results exported to: {output_file}")


def export_to_json(results_by_method: Dict[str, Dict[str, Any]], output_file: str):
    """Export to JSON file"""
    # Remove question_details to reduce file size (optional)
    export_data = {}
    for method, data in results_by_method.items():
        export_data[method] = {
            'method': data['method'],
            'total_agents': data['total_agents'],
            'agents': [
                {
                    'agent_name': a['agent_name'],
                    'average_percentage_score': a['average_percentage_score'],
                    'scored_questions': a['scored_questions'],
                    'total_score': a['total_score'],
                    'max_score': a['max_score']
                }
                for a in data['agents']
            ]
        }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, ensure_ascii=False, indent=2)
    
    print(f"Results exported to: {output_file}")


def check_missing_answers(
    results: List[Dict[str, Any]], 
    question_file: Optional[str] = None
) -> Dict[str, Any]:
    """
    Check for missing answers
    
    Args:
        results: List of scoring results (ignores METHOD_FILTER, checks all scoring methods)
        question_file: Optional, path to JSONL file containing complete question list
        
    Returns:
        Dictionary containing all agent_names, question_ids and missing information
    """
    # Collect all unique agent_names and question_ids
    all_agent_names = set()
    result_question_ids = set()
    
    # Group by question_id -> agent_name, record which agents have answers
    question_agents: Dict[str, set] = defaultdict(set)
    
    for r in results:
        agent_name = r.get('agent_name', '')
        question_id = r.get('question_id', '')
        
        if agent_name:
            all_agent_names.add(agent_name)
        if question_id:
            result_question_ids.add(question_id)
            if agent_name:
                question_agents[question_id].add(agent_name)
    
    # If question_file is provided, use question_id list from that file as baseline
    if question_file:
        try:
            expected_question_ids = load_question_ids(question_file)
            all_question_ids = expected_question_ids
            # Find questions in baseline list but not in result file
            missing_questions = sorted(expected_question_ids - result_question_ids)
        except FileNotFoundError:
            print(f"Warning: Question file '{question_file}' not found, will use question list from result file", file=sys.stderr)
            all_question_ids = result_question_ids
            missing_questions = []
    else:
        all_question_ids = result_question_ids
        missing_questions = []
    
    # Calculate missing agent_names for each question_id
    missing_info: Dict[str, List[str]] = {}
    for question_id in sorted(all_question_ids):
        missing_agents = sorted(all_agent_names - question_agents[question_id])
        if missing_agents:
            missing_info[question_id] = missing_agents
    
    return {
        'all_agent_names': sorted(all_agent_names),
        'all_question_ids': sorted(all_question_ids),
        'result_question_ids': sorted(result_question_ids),
        'missing_questions': missing_questions,
        'question_agents': {q: sorted(agents) for q, agents in question_agents.items()},
        'missing_info': missing_info,
        'total_agents': len(all_agent_names),
        'total_questions': len(all_question_ids),
        'has_question_file': question_file is not None
    }


def print_missing_answers(missing_data: Dict[str, Any]):
    """
    Print missing answer information
    
    Args:
        missing_data: Dictionary returned by check_missing_answers()
    """
    print("=" * 80)
    print("Missing Answer Check Results")
    print("=" * 80)
    print()
    
    # Print all agent_names
    print(f"All Agent Names (Total: {missing_data['total_agents']}):")
    print("-" * 80)
    agent_names = missing_data['all_agent_names']
    for i, agent_name in enumerate(agent_names, 1):
        print(f"  {i:2d}. {agent_name}")
    print()
    
    # Print statistics
    if missing_data.get('has_question_file', False):
        print(f"Baseline Total Questions (from question file): {missing_data['total_questions']}")
        print(f"Questions in Result File: {len(missing_data['result_question_ids'])}")
        print(f"Missing Questions Count: {len(missing_data['missing_questions'])}")
        if missing_data['missing_questions']:
            print(f"Missing Question IDs:")
            for qid in missing_data['missing_questions']:
                print(f"  - {qid}")
        print()
    else:
        print(f"Total Questions: {missing_data['total_questions']}")
        print(f"Questions with Missing Answers: {len(missing_data['missing_info'])}")
        print()
    
    # Print missing agent_names for each question
    if missing_data['missing_info']:
        print("=" * 80)
        print("Missing Answer Details for Each Question")
        print("=" * 80)
        print()
        
        for question_id, missing_agents in sorted(missing_data['missing_info'].items()):
            print(f"Question ID: {question_id}")
            print(f"  Missing Agent Count: {len(missing_agents)}")
            print(f"  Missing Agent List:")
            for agent_name in missing_agents:
                print(f"    - {agent_name}")
            
            # Show number of agents with answers for this question
            answered_count = len(missing_data['question_agents'].get(question_id, []))
            print(f"  Agents with Answers: {answered_count}/{missing_data['total_agents']}")
            print()
    else:
        print("=" * 80)
        print("All questions have complete answers, no missing cases")
        print("=" * 80)
        print()
    
    # Print summary statistics
    print("=" * 80)
    print("Summary Statistics")
    print("=" * 80)
    
    # Count missing questions for each agent
    agent_missing_count: Dict[str, int] = defaultdict(int)
    for question_id, missing_agents in missing_data['missing_info'].items():
        for agent_name in missing_agents:
            agent_missing_count[agent_name] += 1
    
    if agent_missing_count:
        print("\nMissing Question Count for Each Agent:")
        print("-" * 80)
        sorted_agents = sorted(agent_missing_count.items(), key=lambda x: x[1], reverse=True)
        for agent_name, count in sorted_agents:
            print(f"  {agent_name:<30} Missing {count} questions")
    else:
        print("\nAll Agents have completed answers for all questions")
    
    print()


def main():
    # Read configuration
    input_file = INPUT_FILE
    question_file = QUESTION_FILE if QUESTION_FILE else None
    method_filter = METHOD_FILTER if METHOD_FILTER else None
    show_details = SHOW_DETAILS
    list_methods_only = LIST_METHODS_ONLY
    export_csv = EXPORT_CSV_FILE if EXPORT_CSV_FILE else None
    export_json = EXPORT_JSON_FILE if EXPORT_JSON_FILE else None
    
    # Load data
    print(f"Reading file: {input_file}")
    try:
        results = load_score_results(input_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found", file=sys.stderr)
        print("Please modify the INPUT_FILE configuration in the script", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loaded {len(results)} scoring records")
    print()
    
    if not results:
        print("Error: No scoring records read", file=sys.stderr)
        sys.exit(1)
    
    # List all scoring methods
    if list_methods_only:
        methods = sorted(set(r.get('method', '') for r in results))
        print("Available scoring methods:")
        for m in methods:
            count = sum(1 for r in results if r.get('method') == m)
            print(f"  - {m} ({count} records)")
        sys.exit(0)
    
    # Check missing answers (ignore METHOD_FILTER, check all scoring methods)
    print("Checking for missing answers...")
    if question_file:
        print(f"Using question file as baseline: {question_file}")
    print()
    missing_data = check_missing_answers(results, question_file)
    print_missing_answers(missing_data)
    print()
    
    # Analyze data
    analysis = analyze_agent_scores(results, method_filter)
    
    if not analysis:
        if method_filter:
            print(f"Error: No records found for scoring method '{method_filter}'", file=sys.stderr)
        else:
            print("Error: No data to analyze", file=sys.stderr)
        sys.exit(1)
    
    # Print results
    print_results(analysis, show_details)
    
    # Export
    if export_csv:
        export_to_csv(analysis, export_csv)
    
    if export_json:
        export_to_json(analysis, export_json)


if __name__ == '__main__':
    main()
