import os
import re
import sys
import subprocess
from cargo_workspace.parsing import Workspace, Version

workspace_root = sys.argv[1]
os.chdir(workspace_root)
workspace = Workspace.from_path("Cargo.toml")

# Run a cargo build command and search its output for "external crate `$` unused in `$`"
proc = subprocess.Popen(
	["cargo", "remote", "--no-copy-lock", "--", "check", "--workspace", "--all-features", "--all"],
	stdout=subprocess.PIPE)

unused_in = {}

while True:
	line = proc.stdout.readline()
	if not line:
		break
  
	line = line.decode("utf-8")
	m = re.match(r".*external crate `(.*)` unused in `([^`]+)`.*", line)
	print(line)
	if m is None:
		continue

	dep = m.group(1).replace("_", "-")
	crate_name = m.group(2).replace("_", "-")
	crate = workspace.package_by_name(crate_name)
	if crate is None:
		print(f"Could not find crate {crate_name}")
		continue

	print(f"{dep} is unused in {crate.name()}")
	if not crate in unused_in:
		unused_in[crate] = []
	unused_in[crate].append(dep)

print(f"There are {len(unused_in)} crates with unused dependencies")
for crate, deps in unused_in.items():
	print(f"Removing {deps} from {crate.name()}")
	
	with open(crate.path(), "r") as f:
		data = f.read()
	
	for dep in deps:
		# Remove the line that contains the dependency
		data = re.sub(rf"^{dep} = .*$\n", "", data, flags=re.MULTILINE)
		# Remove all lines with the feature of it
		data = re.sub(rf'^\s*"{dep}.*$\n', "", data, flags=re.MULTILINE)
	
	with open(crate.path(), "w") as f:
		f.write(data)
