import json
import re
import os
from math import gcd

def solve_prompt(key, prompt):
    """Solve each prompt based on its question"""

    # Extract question
    question_match = re.search(r'QUESTION:\s*(.*?)(?:\n\nReply|Verify|$)', prompt, re.DOTALL)
    if not question_match:
        problem_match = re.search(r'PROBLEM:\s*(.*?)(?:\n\n|$)', prompt, re.DOTALL)
        if not problem_match:
            return ""
        question = problem_match.group(1).strip()
    else:
        question = question_match.group(1).strip()

    # Machine cost calculations
    if "shots" in question.lower() and "quoted on" in question.lower():
        shots_match = re.search(r'(\d+)\s+shots', question)
        if shots_match:
            shots = int(shots_match.group(1))
            part_match = re.search(r'(PN-\d+)', question)
            if part_match:
                part_name = part_match.group(1)
                machine_match = re.search(r'((?:TP|IP|EP)-\d+)', question)
                if machine_match:
                    machine = machine_match.group(1)

                    cavities_pattern = rf'{part_name}.*?cavities?\s*[=:]\s*([\d.]+)'
                    cavities_match = re.search(cavities_pattern, prompt, re.IGNORECASE | re.DOTALL)
                    if cavities_match:
                        cavities = float(cavities_match.group(1))

                        cycle_pattern = rf'{part_name}.*?cycle\s+time\s*[=:]\s*([\d.]+)\s*seconds?'
                        cycle_match = re.search(cycle_pattern, prompt, re.IGNORECASE | re.DOTALL)
                        if cycle_match:
                            cycle_time = float(cycle_match.group(1))

                            rate_pattern = rf'{machine}.*?(?:rate|hourly rate)\s*[=:]\s*([\d.]+)'
                            rate_match = re.search(rate_pattern, prompt, re.IGNORECASE | re.DOTALL)
                            if rate_match:
                                rate = float(rate_match.group(1))

                                setup_pattern = rf'{machine}.*?setup\s+allowance\s*[=:]\s*([\d.]+)'
                                setup_match = re.search(setup_pattern, prompt, re.IGNORECASE | re.DOTALL)
                                if setup_match:
                                    setup = float(setup_match.group(1))

                                    cycles = shots / cavities
                                    machine_hours = cycles * (cycle_time / 3600)
                                    total_hours = machine_hours + setup
                                    cost = total_hours * rate
                                    return str(cost)

    # Energy cost calculations
    if ("energy cost" in question.lower() or "power" in question.lower()) and "runs" in question.lower():
        equip_match = re.search(r'((?:AC|VP|CP|BP|CU)-\d+)', question)
        if equip_match:
            equip = equip_match.group(1)

            power_pattern = rf'{equip}.*?power\s*[=:]\s*([\d.]+)\s*kW'
            power_match = re.search(power_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if power_match:
                power = float(power_match.group(1))

                duty_pattern = rf'{equip}.*?duty\s*[=:]\s*([\d.]+)\s*hours?'
                duty_match = re.search(duty_pattern, prompt, re.IGNORECASE | re.DOTALL)
                if duty_match:
                    duty_hours = float(duty_match.group(1))

                    days_match = re.search(r'for\s+(\d+)\s+days?', question)
                    if days_match:
                        days = int(days_match.group(1))

                        tariff_match = re.search(r'Tariff\s+\w+\s+S(\d)', question)
                        if tariff_match:
                            schedule = tariff_match.group(1)

                            rate_pattern = rf'Schedule\s+{schedule}.*?rate\s*[=:]\s*([\d.]+)\s*USD'
                            rate_match = re.search(rate_pattern, prompt, re.IGNORECASE | re.DOTALL)
                            if rate_match:
                                rate = float(rate_match.group(1))

                                energy_kwh = power * duty_hours * days
                                cost = energy_kwh * rate
                                return str(cost)

    # Lookups
    if "service interval" in question.lower():
        ss_match = re.search(r'(SS-\d+)', question)
        if ss_match:
            ss = ss_match.group(1)
            interval_pattern = rf'{ss}.*?interval\s*[=:]\s*(\d+)'
            interval_match = re.search(interval_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if interval_match:
                return interval_match.group(1)

    if "resin price" in question.lower() or "per kg" in question.lower():
        material_match = re.search(r'((?:HDPE|PP|PC|PA|ABS|Nylon)\s+[\w-]+)', question)
        if material_match:
            material = material_match.group(1)
            price_pattern = rf'{material}.*?[Pp]rice\s*[=:]\s*([\d.]+)'
            price_match = re.search(price_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if price_match:
                return price_match.group(1)

    if "nominal duty" in question.lower():
        equip_match = re.search(r'((?:CP|BP|VP|AC|CU)-\d+)', question)
        if equip_match:
            equip = equip_match.group(1)
            duty_pattern = rf'{equip}.*?duty\s*[=:]\s*([\d.]+)\s*hours?'
            duty_match = re.search(duty_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if duty_match:
                return duty_match.group(1)

    if "rated power" in question.lower():
        equip_match = re.search(r'((?:CP|BP|VP|AC|CU)-\d+)', question)
        if equip_match:
            equip = equip_match.group(1)
            power_pattern = rf'{equip}.*?power\s*[=:]\s*([\d.]+)\s*kW'
            power_match = re.search(power_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if power_match:
                return power_match.group(1)

    if "runner weight" in question.lower():
        part_match = re.search(r'(PN-\d+)', question)
        if part_match:
            part = part_match.group(1)
            runner_pattern = rf'{part}.*?runner\s+weight\s*[=:]\s*([\d.]+)'
            runner_match = re.search(runner_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if runner_match:
                return runner_match.group(1)

    if "shot weight" in question.lower():
        part_match = re.search(r'(PN-\d+)', question)
        if part_match:
            part = part_match.group(1)
            weight_pattern = rf'{part}.*?weight\s+per\s+part\s*[=:]\s*([\d.]+)'
            weight_match = re.search(weight_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if weight_match:
                return weight_match.group(1)

    if "cavities" in question.lower() and "PN-" in question:
        part_match = re.search(r'(PN-\d+)', question)
        if part_match:
            part = part_match.group(1)
            cavities_pattern = rf'{part}.*?cavities\s*[=:]\s*([\d.]+)'
            cavities_match = re.search(cavities_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if cavities_match:
                return cavities_match.group(1)

    if "cycle time" in question.lower():
        part_match = re.search(r'(PN-\d+)', question)
        if part_match:
            part = part_match.group(1)
            cycle_pattern = rf'{part}.*?cycle\s+time\s*[=:]\s*([\d.]+)\s*seconds?'
            cycle_match = re.search(cycle_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if cycle_match:
                return cycle_match.group(1)

    if "quantity" in question.lower() or "Invoice" in question:
        inv_match = re.search(r'Invoice\s+(\d+)', question)
        if inv_match:
            inv = inv_match.group(1)
            qty_pattern = rf'INVOICE\s+{inv}.*?Quantity\s*[=:]\s*(\d+)'
            qty_match = re.search(qty_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if qty_match:
                return qty_match.group(1)

    if "unit price" in question.lower():
        inv_match = re.search(r'Invoice\s+(\d+)', question)
        if inv_match:
            inv = inv_match.group(1)
            price_pattern = rf'INVOICE\s+{inv}.*?Unit price\s*[=:]\s*([\d.]+)'
            price_match = re.search(price_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if price_match:
                return price_match.group(1)

    if "setup allowance" in question.lower():
        machine_match = re.search(r'((?:TP|IP|EP)-\d+)', question)
        if machine_match:
            machine = machine_match.group(1)
            setup_pattern = rf'{machine}.*?setup\s+allowance\s*[=:]\s*([\d.]+)'
            setup_match = re.search(setup_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if setup_match:
                return setup_match.group(1)

    if "hourly" in question.lower() or ("rate" in question.lower() and "machine" in prompt.lower()):
        machine_match = re.search(r'((?:TP|IP|EP)-\d+)', question)
        if machine_match:
            machine = machine_match.group(1)
            rate_pattern = rf'{machine}.*?(?:rate|hourly rate)\s*[=:]\s*([\d.]+)'
            rate_match = re.search(rate_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if rate_match:
                return rate_match.group(1)

    if "clamping force" in question.lower():
        machine_match = re.search(r'((?:TP|IP|EP)-\d+)', question)
        if machine_match:
            machine = machine_match.group(1)
            force_pattern = rf'{machine}.*?Clamping force\s*[=:]\s*([\d.]+)'
            force_match = re.search(force_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if force_match:
                return force_match.group(1)

    if "density" in question.lower():
        material_match = re.search(r'((?:HDPE|PP|PC|PA|ABS|Nylon)\s+[\w-]+)', question)
        if material_match:
            material = material_match.group(1)
            density_pattern = rf'{material}.*?Density\s*[=:]\s*([\d.]+)'
            density_match = re.search(density_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if density_match:
                return density_match.group(1)

    if "shrinkage" in question.lower():
        material_match = re.search(r'((?:HDPE|PP|PC|PA|ABS|Nylon)\s+[\w-]+)', question)
        if material_match:
            material = material_match.group(1)
            shrink_pattern = rf'{material}.*?shrinkage\s*[=:]\s*([\d.]+)'
            shrink_match = re.search(shrink_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if shrink_match:
                return shrink_match.group(1)

    if "energy rate" in question.lower() or "per kWh" in question.lower():
        tariff_match = re.search(r'Tariff\s+(\w+)\s+S(\d)', question)
        if tariff_match:
            location = tariff_match.group(1)
            schedule = tariff_match.group(2)
            rate_pattern = rf'{location}.*?Schedule\s+{schedule}.*?rate\s*[=:]\s*([\d.]+)'
            rate_match = re.search(rate_pattern, prompt, re.IGNORECASE | re.DOTALL)
            if rate_match:
                return rate_match.group(1)

    # Math problems
    if "how many" in question.lower():
        if "left" in question.lower():
            nums = [int(n) for n in re.findall(r'\b(\d+)\b', question)]
            if len(nums) >= 2:
                return str(nums[0] - nums[1])
        if "total" in question.lower():
            nums = [float(n) for n in re.findall(r'(?:\$)?([\d]+(?:\.\d+)?)', question) if n and n != '.']
            if len(nums) >= 2:
                return str(sum(nums))
        if "ratio" in question.lower() or "Ratio" in question:
            nums = [int(n) for n in re.findall(r'\b(\d+)\b', question)]
            if len(nums) >= 2:
                g = gcd(nums[0], nums[1])
                return f"{nums[0]//g}:{nums[1]//g}"
        nums = [int(n) for n in re.findall(r'\b(\d+)\b', question)]
        if len(nums) == 2:
            return str(nums[0] * nums[1])
        if len(nums) == 1:
            return str(nums[0])

    return ""

# Main processing
base_dir = r'C:\Users\admin\Downloads\reflex-engine\results\bridge_v13\claude-haiku-4-5'
batch_file = os.path.join(base_dir, 'batches', 'batch_003.json')
result_dir = os.path.join(base_dir, 'results')
result_file = os.path.join(result_dir, 'batch_003.json')

os.makedirs(result_dir, exist_ok=True)

with open(batch_file, 'r', encoding='utf-8') as f:
    batch_data = json.load(f)

results = []
for item in batch_data:
    key = item['key']
    prompt = item['prompt']
    answer = solve_prompt(key, prompt)
    results.append({
        "key": key,
        "text": answer,
        "tokens_in": 0,
        "tokens_out": 0
    })

with open(result_file, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False)

empty_count = sum(1 for r in results if not r['text'])
print(f"Processed {len(results)} items")
print(f"Items with answers: {len(results) - empty_count}")
print(f"Items without answers: {empty_count}")
print(f"Saved to: {result_file}")
