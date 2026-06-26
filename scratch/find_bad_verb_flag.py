import subprocess
import re

def test_aff_content(aff_content):
    with open('test_s.aff', 'w', encoding='utf-8', newline='\n') as f:
        f.write(aff_content)
        
    r = subprocess.run(
        ['hunspell', '-d', 'test_s'],
        input='evler\n', capture_output=True, text=True, encoding='utf-8'
    )
    return '+ ev' in r.stdout

def main():
    print("Loading tr_v2.aff...")
    with open('tr_v2.aff', 'r', encoding='utf-8') as f:
        content = f.read()
        
    parts = content.split('# VERB PARADIGM FLAGS\n')
    noun_content = parts[0]
    verb_content = parts[1]
    
    # Split verb content into individual SFX blocks
    # A SFX block starts with SFX flag_name Y count
    blocks = []
    current_block = []
    
    # We match the SFX headers to split blocks
    lines = verb_content.split('\n')
    for line in lines:
        if line.startswith('SFX '):
            tokens = line.split()
            if len(tokens) == 4 and tokens[2] == 'Y':
                # Start of a new block!
                if current_block:
                    blocks.append('\n'.join(current_block))
                current_block = [line]
                continue
        current_block.append(line)
        
    if current_block:
        blocks.append('\n'.join(current_block))
        
    print(f"Found {len(blocks)} verb flags blocks.")
    
    # Set up test dictionary
    with open('test_s.dic', 'w', encoding='utf-8', newline='\n') as f:
        f.write('1\nev/PF\n')
        
    # Baseline check (noun content only)
    if not test_aff_content(noun_content):
        print("ERROR: Noun content baseline itself failed!")
        return
    print("Baseline (nouns only): PASS")
    
    # Test each block one by one
    for i, block in enumerate(blocks):
        # Extract flag name from first line of block
        first_line = block.split('\n')[0]
        flag_name = first_line.split()[1]
        
        # Test content = noun_content + "# VERB PARADIGM FLAGS\n" + block
        test_content = noun_content + "# VERB PARADIGM FLAGS\n" + block + "\n"
        passed = test_aff_content(test_content)
        
        status = "PASS" if passed else "FAIL"
        print(f"Block {i+1:2d} ({flag_name}): {status} (size: {len(block.splitlines())} lines)")

if __name__ == '__main__':
    main()
