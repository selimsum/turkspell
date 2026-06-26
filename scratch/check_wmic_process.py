import subprocess

def main():
    try:
        # Use powershell to fetch process command line arguments
        cmd = ["powershell", "-Command", "Get-CimInstance Win32_Process -Filter \"name = 'hunspell.exe'\" | Select-Object -ExpandProperty CommandLine"]
        output = subprocess.check_output(cmd).decode('utf-8', errors='ignore')
        
        print("Active Hunspell process command lines:")
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        for line in lines:
            print(f"  {line}")
    except Exception as e:
        print(f"Error querying process details: {e}")

if __name__ == "__main__":
    main()
