import argparse
import subprocess
import datetime
from config import parse_args

base_compile = "%s build --bin %s --profile=%s --locked --features=runtime-benchmarks"
bench = "./target/%s/%s benchmark pallet --chain=%s --steps=%s --repeat=%s --pallet='%s' --extrinsic='%s' --execution=wasm --wasm-execution=compiled --heap-pages=4096 --output=%s"# --template=%s --header=%s"

def build_compile_cmd(args):
	if args.cargo_remote:
		# Copy back the build artefact.
		remote = "cargo remote -H home -c %s/%s --" % (args.profile, args.project)
		return base_compile % (remote, args.project, args.profile)
	else:
		return base_compile % ("cargo", args.project, args.profile)

def build_bench_cmd(args, pallet, case, out_dir):
	if args.project == "substrate":
		#weight_path = "%s/frame/%s/src/weights.rs" % (args.weight_dir, pallet)
		weight_path = out_dir
	else:
		# TODO
		weight_path = "/tmp/weight.rs"
	# TODO Json
	return bench % (args.profile, args.project, args.runtime, args.steps, args.repeat, pallet, case, weight_path)
	#, args.template, args.header)

def main(args):
	# Compile all pallets. Otherwise `cargo run` would re-compile each pallet.
	if args.no_compile:
		log("Compiling ... SKIPPED")
	else:
		log("Compiling ...")
		compile(args)		
	
	# List all available benchmarks.	
	log("Listing ...")
	per_pallet = list_benches(args)
	pallets = per_pallet.keys()
	
	# Run all benchmarks.
	for i, pallet in enumerate(pallets):
		msg = "[%d/%d] %s: %d cases" % (i+1, len(pallets), pallet, len(per_pallet[pallet]))
		if pallet in args.skip or (len(args.pallets) != 0 and pallet not in args.pallets):
			log(msg + " ... SKIPPED")
			continue
		log(msg + " ...")
		run_pallet(pallet, args)
	
	log("🎉 Weights in '%s', json output in '%s'" % (args.weight_dir, args.json_dir))
	log("You can enact the new weights with\ncp -RT %s/frame %s/frame" % (args.weight_dir, args.cwd))

def run_pallet(pallet, args):
	# Create the weight output directory.
	name = "-".join(pallet.split("_")[1:])	# Cut off the `frame_` or `pallet_` prefix.
	out_dir = "%s/frame/%s/src/" % (args.weight_dir, name)
	subprocess.run("mkdir -p %s" % out_dir, shell=True)
	
	# Run all the cases for this pallet.
	cmd = build_bench_cmd(args, pallet, "*", out_dir)
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=args.cwd)
	# Wait for the process to finish.
	stdout, stderr = p.communicate()
	# check the exit code of the process.
	if p.returncode != 0:
		print("Rust:\n\n%s\nfrom:%s" % (stderr.decode('utf-8'), cmd))

def compile(args):
	cmd = build_compile_cmd(args)
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=args.cwd)
	stdout, stderr = p.communicate()
	# check the exit code of the process.
	if p.returncode != 0:
		raise Exception("Rust:\n\n%s" % stderr.decode('utf-8'))

def list_benches(args):
	cmd = build_bench_cmd(args, "*", "*", ".") + " --list"
	p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=args.cwd)
	stdout, stderr = p.communicate()
	# check the exit code of the process.
	if p.returncode != 0:
		raise Exception("Rust:\n\n%s" % stderr.decode('utf-8'))
	cases = stdout.decode('utf-8').splitlines()[1:] # Cut off the CSV header.
	# Find which cases are there per pallet.
	per_pallet = {}
	for case in cases:
		pallet, _, _ = case.partition(",")
		if pallet not in per_pallet:
			per_pallet[pallet] = [case]
		else:
			per_pallet[pallet].append(case)
	log("Running %d cases across %d pallets. Skipped %d pallets." % (len(cases), len(per_pallet), len(args.skip)))
	# Check that skip is a subset of the per_pallet.keys.
	for pallet in args.skip:
		if pallet not in per_pallet:
			raise Exception("Pallet %s is not found in the benchmark list." % pallet)
	return per_pallet

def help():
	print("""
Usage:
  ./run.py [--cwd <path to substrate>] [--runtime <RUNTIME>] [--debug]

Options:
  --debug: Don't really run the benchmarks. Good for debugging.
  --profile: Rust profile to use.
  --cwd: Substrate root directory.
  --runtime: Runtime to use.
  --skip: List of pallets to skip.
  --pallets: Only run for these pallets.
  --no-compile: Skip compilation.
  --weight-dir: Relative weight output directory.
  --json-dir: Relative json output directory.
  --repeat: Repeat the benchmark this many times.
  --steps: Number of resolution steps per benchmark.

Example for debugging:
  python run.py --debug --project substrate --cwd ~/substrate/

is equivalent to:
  python run.py --profile release --project substrate --cwd ~/substrate/ --steps 1 --repeat 1

Example for real results on ref hardware:
  python run.py --project substrate --cwd ~/substrate/
""")

def log(msg):
	print("%s: %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))

if __name__ == '__main__':
	main(parse_args())
