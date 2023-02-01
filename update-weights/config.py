import argparse

def parse_args():
	parser = argparse.ArgumentParser()
	parser.add_argument('--profile', type=str, help='Rust profile', default="production")
	parser.add_argument('--project', type=str, help='Project to benchmark for', choices=["substrate", "polkadot", "cumulus"])
	parser.add_argument('--cwd', type=str, help='Substrate root directory', default=".")
	parser.add_argument('--header', type=str, help='Header file to include.', default="HEADER-APACHE2")
	parser.add_argument('--runtime', type=str, help='Runtime to use.', default='dev')
	parser.add_argument('--skip', nargs='+', help='List of pallets to skip.', default="")
	parser.add_argument('--pallets', nargs='+', help='Only run for these pallets.', default="")
	parser.add_argument('--cargo-remote', action='store_true', help='Use cargo-remote for building.')
	parser.add_argument('--no-compile', action='store_true', help='Skip compilation.')
	parser.add_argument('--weight-dir', type=str, help='Relative weight output directory', default=None)
	parser.add_argument('--json-dir', type=str, help='Relative json output directory', default=None)
	parser.add_argument('--repeat', type=int, help='Repeat the benchmark this many times.', default=20)
	parser.add_argument('--steps', type=int, help='Number of resolution steps per benchmark.', default=50)
	parser.add_argument('--template', type=str, help='Template file for the weights.', default=None)
	parser.add_argument('--debug', action='store_true', help='Debug mode.')
	args = parser.parse_args()
	if args.debug:
		args.repeat = 1
		args.steps = 2
		args.profile = 'release'
	if args.project == "substrate" and args.template is None:
		args.template = ".maintain/frame-weight-template.hbs"
	if args.project is None:
		raise Exception("--project must be specified.")
	
	if args.weight_dir is None:
		args.weight_dir = "%s/weights-%s-%s" % (args.cwd, args.runtime, args.profile)
	if args.json_dir is None:
		args.json_dir = "%s/json-%s-%s" % (args.cwd, args.runtime, args.profile)
	if args.profile is None:
		parser.error("--profile is required. Use 'production' for real benchmarking results.")
	
	return args
