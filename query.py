#!/usr/bin/env python3
# coding=utf-8

import argparse
import sys
import time

import cmd2

from substrateinterface import SubstrateInterface

URL = "ws://127.0.0.1:9944"
#URL = "wss://rpc.polkadot.io"
URL = "wss://kusama-rpc.polkadot.io"

while True:
	try:
		print(f"Connecting to {URL}...")
		substrate = SubstrateInterface(URL)
		break
	except Exception as e:
		print(f"Failed to connect to {URL}: {e}")
		time.sleep(1)
		pass


print(f"Connected to {substrate.name}: {substrate.chain} v{substrate.version}")
storage_functions = substrate.get_metadata_storage_functions()

query_parser = cmd2.Cmd2ArgumentParser()
query_subparsers = query_parser.add_subparsers(title='subcommands', help='subcommand help')

parser_info = query_subparsers.add_parser('info', help='Print chain info')
parser_connect = query_subparsers.add_parser('url', help='Chain URL')
parser_pallet = query_subparsers.add_parser('pallet', help='Query a pallet\'s storage')

parser_pallet.add_argument('pallet', type=str, help='Pallet', choices=[pallet['module_id']  for pallet in storage_functions])
def storage_for_pallet(token, **arg_tokens):
	pallet = arg_tokens['arg_tokens']['pallet'][0]
	return [s['storage_name'] for s in storage_functions if s['module_id'] == pallet]
parser_pallet.add_argument('storage', type=str, help='Storage', choices_provider=storage_for_pallet)

class Subcommands(cmd2.Cmd):
	def __init__(self):
		super().__init__()
		# Remove builtins - WTF
		for builtin in ['alias', 'history', 'macro', 'edit', 'run_pyscript', 'run_script', 'set', 'shell', 'shortcuts']:
			delattr(cmd2.Cmd, f'do_{builtin}')

	def query_pallet(self, args):
		query = substrate.query(args.pallet, args.storage)
		self.poutput(f'Querying pallet {args.pallet}.{args.storage}…')
		self.poutput(query)

	# Set handler functions for the subcommands
	parser_pallet.set_defaults(func=query_pallet)

	@cmd2.with_argparser(query_parser)
	def do_query(self, args):
		"""Query command help"""
		func = getattr(args, 'func', None)
		if func is not None:
			# Call whatever subcommand function was selected
			func(self, args)
		else:
			# No subcommand was provided, so call help
			self.do_help('query')

	def do_info(self, args):
		"""Print chain info"""
		self.poutput(f"Chain name {substrate.name}: {substrate.chain} v{substrate.version}\nThe Unit {substrate.token_symbol} has {10**substrate.token_decimals} (10^{substrate.token_decimals}) atoms")
		runtime = substrate.get_constant('System', 'Version')
		self.poutput(f"Runtime is {runtime['spec_name']} v{runtime['spec_version']} impl {runtime['impl_version']}")

if __name__ == '__main__':
	app = Subcommands()
	sys.exit(app.cmdloop())
