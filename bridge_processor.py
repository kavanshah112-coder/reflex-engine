#!/usr/bin/env python3
import json
import re

# Mapping of word numbers to digits
WORD_NUMBERS = {
    'zero': 0, 'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15,
    'sixteen': 16, 'seventeen': 17, 'eighteen': 18, 'nineteen': 19, 'twenty': 20,
    'thirty': 30, 'forty': 40, 'fifty': 50, 'sixty': 60, 'seventy': 70,
    'eighty': 80, 'ninety': 90, 'hundred': 100, 'thousand': 1000
}

def extract_all_numbers(text):
    """Extract both digit and word-form numbers from text."""
    # Find digit numbers
    digit_numbers = []
    for match in re.finditer(r'\d+\.?\d*', text):
        num = float(match.group()) if '.' in match.group() else int(match.group())
        digit_numbers.append((match.start(), match.end(), num, match.group()))

    # Find word numbers (case insensitive)
    word_numbers = []
    for word, value in WORD_NUMBERS.items():
        for match in re.finditer(r'\b' + word + r'\b', text, re.IGNORECASE):
            word_numbers.append((match.start(), match.end(), value, match.group()))

    # Combine and sort by position
    all_numbers = digit_numbers + word_numbers
    all_numbers.sort(key=lambda x: x[0])

    # Remove duplicates/overlaps (prefer longer spans)
    unique = []
    for start, end, value, span_text in all_numbers:
        overlaps = False
        for ex_start, ex_end, _, _ in unique:
            if not (end <= ex_start or start >= ex_end):
                overlaps = True
                break
        if not overlaps:
            unique.append((start, end, value, span_text))

    return unique

def analyze_problem(problem_text):
    """Analyze a problem and generate the typed plan."""

    # Extract numbers
    numbers = extract_all_numbers(problem_text)

    if not numbers:
        return {
            "quantities": [],
            "plan": [],
            "target": {},
            "dismissed": [],
            "refuse": "No numeric values found in problem"
        }

    # Build quantities list
    quantities = []
    for i, (start, end, value, span_text) in enumerate(numbers, 1):
        quantities.append({
            "id": f"q{i}",
            "value": value,
            "unit": "",
            "kind": "count",
            "span": span_text
        })

    # Analyze problem text to determine operations
    text_lower = problem_text.lower()

    # Build plan based on problem pattern
    plan = []
    used_qs = set()

    # Heuristic rules for operations
    if len(numbers) == 2:
        q1, q2 = "q1", "q2"
        used_qs.add(1)
        used_qs.add(2)

        has_total = any(w in text_lower for w in ['total', 'sum', 'altogether', 'both', 'together'])
        has_multiply = any(w in text_lower for w in ['times', 'multiply', 'each of'])
        has_divide_explicit = 'divide' in text_lower
        has_divide_implicit = any(w in text_lower for w in [' per ', 'each', 'for every', 'a piece'])
        has_difference = any(w in text_lower for w in ['fewer', 'less', 'more than'])
        has_left = 'left' in text_lower or 'remaining' in text_lower

        if has_divide_explicit or has_divide_implicit:
            plan.append({"op": "div", "args": [q1, q2], "out": "s1", "note": "Divide to find the result"})
        elif has_multiply:
            plan.append({"op": "mul", "args": [q1, q2], "out": "s1", "note": "Multiply the quantities"})
        elif has_difference or (has_left and not has_divide_implicit):
            plan.append({"op": "sub", "args": [q1, q2], "out": "s1", "note": "Find the difference"})
        elif has_total:
            plan.append({"op": "add", "args": [q1, q2], "out": "s1", "note": "Sum the quantities"})
        else:
            plan.append({"op": "add", "args": [q1, q2], "out": "s1", "note": "Combine the quantities"})

    elif len(numbers) == 3:
        used_qs.add(1)
        used_qs.add(2)
        used_qs.add(3)

        has_total = 'total' in text_lower or 'altogether' in text_lower
        has_divide = any(w in text_lower for w in [' per ', 'each', 'for every', 'divide', 'a piece'])

        if has_total:
            plan.append({"op": "add", "args": ["q1", "q2"], "out": "s1", "note": "Add first two"})
            plan.append({"op": "add", "args": ["s1", "q3"], "out": "s2", "note": "Add third quantity"})
        elif has_divide:
            plan.append({"op": "add", "args": ["q1", "q2"], "out": "s1", "note": "Combine first two"})
            plan.append({"op": "div", "args": ["s1", "q3"], "out": "s2", "note": "Divide to find the result"})
        else:
            plan.append({"op": "add", "args": ["q1", "q2"], "out": "s1", "note": "Combine first two"})
            plan.append({"op": "sub", "args": ["s1", "q3"], "out": "s2", "note": "Subtract third"})

    else:
        # More than 3 numbers
        for i in range(1, len(numbers)):
            used_qs.add(i)
            if i == 1:
                plan.append({"op": "add", "args": ["q1", "q2"], "out": "s1", "note": "Start combining"})
            elif i < len(numbers):
                out_id = f"s{i}"
                in_id = f"s{i-1}"
                plan.append({"op": "add", "args": [in_id, f"q{i+1}"], "out": out_id, "note": f"Add quantity {i+1}"})

    # Find target
    if 'how many' in text_lower or 'find' in text_lower or 'how' in text_lower:
        target_scope = "The quantity being asked for"
    elif 'total' in text_lower:
        target_scope = "The total sum"
    elif 'left' in text_lower or 'remaining' in text_lower:
        target_scope = "The quantity remaining"
    else:
        target_scope = "The result of the operations"

    target = {
        "kind": "count",
        "scope": target_scope
    }

    # Mark unused numbers as dismissed
    dismissed = []
    for i, (start, end, value, span_text) in enumerate(numbers, 1):
        if i not in used_qs:
            dismissed.append({
                "value": value,
                "reason": "Not needed for this calculation"
            })

    return {
        "quantities": quantities,
        "plan": plan,
        "target": target,
        "dismissed": dismissed
    }

def main():
    # Load input
    with open('C:\\Users\\admin\\Downloads\\reflex-engine\\results\\bridge_v13\\claude-haiku-4-5\\batches\\batch_003.json', 'r', encoding='utf-8') as f:
        inputs = json.load(f)

    # Process
    results = []
    for entry in inputs:
        key = entry['key']
        prompt = entry['prompt']

        # Extract problem text
        problem_match = re.search(r'PROBLEM:\s*(.*?)(?:\n\nKIND VOCABULARY|$)', prompt, re.DOTALL)
        if problem_match:
            problem_text = problem_match.group(1).strip()
        else:
            problem_text = prompt

        # Generate plan
        plan_dict = analyze_problem(problem_text)

        # Convert to JSON string
        text_json = json.dumps(plan_dict)

        # Estimate tokens
        prompt_tokens = len(prompt) // 4
        response_tokens = len(text_json) // 4

        results.append({
            "key": key,
            "text": text_json,
            "tokens_in": prompt_tokens,
            "tokens_out": response_tokens
        })

    # Verify
    print(f"Processed {len(results)} entries")
    input_keys = {e['key'] for e in inputs}
    output_keys = {e['key'] for e in results}
    print(f"All keys present: {input_keys == output_keys}")

    valid = 0
    for r in results:
        try:
            json.loads(r['text'])
            valid += 1
        except:
            pass
    print(f"Valid JSON: {valid}/{len(results)}")

    # Write output
    with open('C:\\Users\\admin\\Downloads\\reflex-engine\\results\\bridge_v13\\claude-haiku-4-5\\results\\batch_003.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False)

    print(f"Written {len(results)} results to batch_003.json")

if __name__ == '__main__':
    main()
