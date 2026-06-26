import sys

def main():
    print("Checking tr_v2.aff for flag length anomalies...")
    invalid_sfx_flags = []
    invalid_continuation_flags = []
    
    with open('tr_v2.aff', 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, start=1):
            line_clean = line.strip()
            if not line_clean or line_clean.startswith('#'):
                continue
                
            parts = line_clean.split()
            if parts[0] == 'SFX':
                flag_name = parts[1]
                if len(flag_name) != 2:
                    invalid_sfx_flags.append((line_num, line_clean, flag_name))
                    
                # Check continuation flags
                if len(parts) >= 4 and '/' in parts[3]:
                    # Format: SFX flag strip add/flags condition
                    add_flags = parts[3].split('/')
                    if len(add_flags) > 1:
                        flags = add_flags[1]
                        if len(flags) % 2 != 0:
                            invalid_continuation_flags.append((line_num, line_clean, flags))

    print(f"Total invalid SFX flag declarations (not 2 chars): {len(invalid_sfx_flags)}")
    for item in invalid_sfx_flags[:5]:
        print(f"  Line {item[0]}: {item[1]}")
        
    print(f"Total invalid continuation flag strings (not multiple of 2 chars): {len(invalid_continuation_flags)}")
    for item in invalid_continuation_flags[:20]:
        print(f"  Line {item[0]}: {item[1]} (flags: '{item[2]}')")

if __name__ == '__main__':
    main()
