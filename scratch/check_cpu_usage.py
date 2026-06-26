import subprocess

def main():
    try:
        # Use powershell to query CPU usage of hunspell
        cmd = ["powershell", "-Command", "Get-Process hunspell | Select-Object Id, CPU, ProcessName"]
        output = subprocess.check_output(cmd).decode('utf-8', errors='ignore')
        
        print("Active Hunspell process CPU details:")
        print(output)
    except Exception as e:
        print(f"Error querying process CPU usage: {e}")

if __name__ == "__main__":
    main()
