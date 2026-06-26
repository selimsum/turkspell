import os
import subprocess

def main():
    print("Checking active processes on the system...")
    # On Windows, we can use tasklist
    try:
        output = subprocess.check_output("tasklist", shell=True).decode('cp1254', errors='ignore')
        lines = output.splitlines()
        
        python_count = 0
        hunspell_count = 0
        
        print("\nRelevant processes:")
        for line in lines:
            line_lower = line.lower()
            if "python" in line_lower or "hunspell" in line_lower:
                print(f"  {line}")
                if "python" in line_lower:
                    python_count += 1
                if "hunspell" in line_lower:
                    hunspell_count += 1
                    
        print(f"\nActive python processes: {python_count}")
        print(f"Active hunspell processes: {hunspell_count}")
        
    except Exception as e:
        print(f"Error running tasklist: {e}")

if __name__ == "__main__":
    main()
