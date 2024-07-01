import os
import re
import sys
import json

from cargo_workspace import Workspace

ZEPTER_OUTPUT = '../zepter/renames.json'
ROOT = '../polkadot-sdk'
w = Workspace.from_path(ROOT)

UNALIAS_OVERRIDE = [
    # This one is just too long and collides with other test helpers
    'polkadot-primitives-test-helpers',
    'polkadot-node-subsystem-test-helpers',
]

def main():
    if os.path.exists(ZEPTER_OUTPUT):
        with open(ZEPTER_OUTPUT, 'r') as f:
            raw = f.read()[:-2]
            raw = f"[{raw}]"
            data = json.loads(raw)

    print(f"Processing {len(data)} alias conflicts")

    for conflict in data:
        name = conflict['name']
        # The crates that did not rename it.
        unrenamed = conflict['unnrenamed']
        # The name that it was renamed to and the crates that did it.
        renamed = conflict['renames']

        max_renamed = 0
        best_alias = None
        for a in renamed:
            if len(renamed[a]) > max_renamed:
                max_renamed = len(renamed[a])
                best_alias = a
    
        print(f"{name}: {len(unrenamed)} times unrenamed and {max_renamed} times renamed to {best_alias}")
        # First check if it should be renamed at all
        if len(unrenamed) > max_renamed or name in UNALIAS_OVERRIDE:
            for a in renamed:
                for r in renamed[a]:
                    unrename(name, a, r)
        else:
            for a in renamed:
                if a != best_alias:
                    for r in renamed[a]:
                        realias(name, a, best_alias, r)
            for crate in unrenamed:
                alias(name, best_alias, crate)

def unrename(name, alias, crate):
    print(f" -> unalias {name} as {alias} in {crate}")
    crate = w.crate_by_name(crate)

    # First fix the Cargo.toml
    with open(crate.abs_path, 'r') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if re.match(rf'^{alias} =', line):
            lines[i] = re.sub(rf'^{alias}', name, line)
            lines[i] = re.sub(rf'package = ".*?"\s*?,\s?', '', lines[i])			
    with open(crate.abs_path, 'w') as f:
        f.writelines(lines)

    fix_features(crate.abs_path, alias, name)
    print(f" -> fixed Cargo.toml in {name}")

def realias(name, old_alias, new_alias, crate):
    print(f" -> realias {name} from {old_alias} to {new_alias} in {crate}")

    # First fix the Cargo.toml
    crate = w.crate_by_name(crate)
    with open(crate.abs_path, 'r') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if re.match(rf'^{old_alias} =', line):
            lines[i] = re.sub(rf'^{old_alias}', new_alias, line)
    
    with open(crate.abs_path, 'w') as f:
        f.writelines(lines)
    fix_features(crate.abs_path, old_alias, new_alias)
    print(f" -> fixed Cargo.toml in {name}")
    return

def alias(name, alias, crate):
    print(f" -> alias {name} to {alias} in {crate}")

    # First fix the Cargo.toml
    crate = w.crate_by_name(crate)
    if crate is None:
        print(f" -> {crate} not found")
        return

    with open(crate.abs_path, 'r') as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if re.match(rf'^{name} =', line):
            lines[i] = re.sub(rf'^{name}', alias, line)
            # insert the `package = "..."` into the beginning after the {
            if '{' in lines[i]:
                index = lines[i].find('{') + 1
                lines[i] = lines[i][:index] + f' package = "{name}",' + lines[i][index:]
            elif '=' in lines[i]:
                content = lines[i].split('=')[1].replace('"', '').strip()
                lines[i] = f'{alias} = {{ package = "{name}", version = "{content}" }}\n'
    with open(crate.abs_path, 'w') as f:
        f.writelines(lines)
    fix_features(crate.abs_path, name, alias)
    print(f" -> fixed Cargo.toml in {name}")
    return

def fix_features(path, old_name, new_name):
    with open(path, 'r') as f:
        lines = f.readlines()
    saw_features = False
    for i, line in enumerate(lines):
        if '[features]' in line:
            saw_features = True
        
        # Replace feature enables:
        lines[i] = lines[i].replace(f'"{old_name}/', f'"{new_name}/')
        # Replace dep feature enables:
        if saw_features:
            lines[i] = lines[i].replace(f'"{old_name}"', f'"{new_name}"')
        # Replace optional dep enables:
        lines[i] = lines[i].replace(f'"dep:{old_name}', f'"dep:{new_name}')
    with open(path, 'w') as f:
        f.writelines(lines)
    
    folder = os.path.dirname(path)
    fix_code(folder, old_name, new_name)

def fix_code(folder, old_name, new_name):
    good = []
    excluded_dirs = set()
    
    for dirpath, dirnames, filenames in os.walk(folder, topdown=True):
        if dirpath == folder:
            # If at the top level, skip the check for Cargo.toml
            good.append(dirpath)
            continue
        # Skip directories that are in the excluded_dirs set
        if dirpath in excluded_dirs:
            dirnames[:] = []  # This will prune the walk to exclude subfolders of excluded dirs
            continue
        
        # Check if current directory contains Cargo.toml
        if 'Cargo.toml' not in filenames:
            good.append(dirpath)
            # Add all subdirectories to the excluded_dirs set
            for dirname in dirnames:
                excluded_dirs.add(os.path.join(dirpath, dirname))
    
    for dirpath in good:
        for dirpath, dirnames, filenames in os.walk(dirpath):
            for filename in filenames:
                if not filename.endswith('.rs'):
                    continue
                path = os.path.join(dirpath, filename)
                with open(path, 'r') as f:
                    lines = f.readlines()
                original = lines.copy()
                old = old_name.replace('-', '_')
                new = new_name.replace('-', '_')
                
                for i, line in enumerate(lines):
                    if not old in line:
                        continue
                    if line.strip().startswith('//'):
                        continue
                    # Replace all instances where it appears as full word
                    lines[i] = re.sub(rf'\b(?<!::){old}(?=::)\b', new, lines[i])
                    # Corner cases... TODO remove identity aliases
                    lines[i] = re.sub(rf'use {old} as', f'use {new} as', lines[i])
                    lines[i] = re.sub(rf'"{old}"', f'"{new}"', lines[i])
                    lines[i] = re.sub(rf'use {old}::', f'use {new}::', lines[i])
                    lines[i] = re.sub(rf'use ::{old} as', f'use {new} as', lines[i])
                    lines[i] = re.sub(rf'^\s*{old}::', f'{new}::', lines[i])

                if lines != original:
                    with open(path, 'w') as f:
                        f.writelines(lines)

if __name__ == "__main__":
    main()
