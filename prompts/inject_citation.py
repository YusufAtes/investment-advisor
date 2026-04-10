import os
import glob

prompts_dir = r"c:\investment advisor\prompts"
files = glob.glob(os.path.join(prompts_dir, "*Agent.txt"))

for path in files:
    # Only process Research Prompts (1A, 2B, etc.)
    filename = os.path.basename(path)
    if "Decider" in filename or "Discussion" in filename or "Inference" in filename:
        continue
        
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Replace citation rule
    old_rule = "MUST be cited."
    new_rule = "MUST be cited using strict in-text citations (e.g., [1], [2]) immediately after the sentence."
    
    if old_rule in content:
        content = content.replace(old_rule, new_rule)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated: {filename}")
    elif new_rule in content:
        print(f"Already updated: {filename}")
    else:
        print(f"Rule not found in: {filename}")

print("Done.")
