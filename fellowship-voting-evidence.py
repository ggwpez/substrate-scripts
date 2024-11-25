import requests
import json
import argparse
from typing import Dict, List

def parse_arguments() -> argparse.Namespace:
	"""
	Parse command line arguments.
	
	Returns:
		Namespace containing the parsed arguments
	"""
	parser = argparse.ArgumentParser(
		description='Analyze GraphQL voting records where rankAtTime >= track for NoVote votes'
	)
	
	parser.add_argument(
		'--account',
		'-a',
		required=True,
		help='Account ID to query'
	)
	
	parser.add_argument(
		'--endpoint',
		'-e',
		required=True,
		help='GraphQL endpoint URL'
	)
	
	parser.add_argument(
		'--filter-rank',
		'-r',
		help='Only check voting records where the rank of the member was a specific value',
		default=None
	)
	
	return parser.parse_args()

def query_voting_records(account_id: str, endpoint_url: str, filter_rank: str) -> Dict:
	"""
	Query the GraphQL endpoint for voting records.
	
	Args:
		account_id: The account ID to query
		endpoint_url: The GraphQL endpoint URL
	
	Returns:
		Dict containing the query response
	"""

	filter_rank = f'rankAtTime_eq: {filter_rank}' if filter_rank else ''

	query = """
	query MyQuery {
		accounts(where: {votingRecord_some: {}, id_eq: "%s"}) {
			id
			votingRecord(where: {%s}) {
				rankAtTime
				vote
				referendum {
					track
					id
				}
			}
		}
	}
	""" % (account_id, filter_rank)

	headers = {
		'Content-Type': 'application/json',
	}
	
	response = requests.post(
		endpoint_url,
		headers=headers,
		json={'query': query}
	)
	
	if response.status_code != 200:
		raise Exception(f"Query failed with status code: {response.status_code}")
		
	return response.json()

def analyze_voting_records(data: Dict) -> List[Dict]:
	"""
	Analyze voting records to find cases where rankAtTime >= track.
	
	Args:
		data: GraphQL query response data
	
	Returns:
		List of records where rankAtTime >= track
	"""
	records = []
	
	if not data.get('data', {}).get('accounts'):
		return []
	
	for account in data['data']['accounts']:
		voting_records = account.get('votingRecord', [])
		
		for record in voting_records:
			rank = int(record['rankAtTime'])
			track = int(record['referendum']['track'])
			bad = False
			
			if record['vote'] == 'NoVote':				
				if eligible_to_vote(rank, track):
					bad = True

			records.append({
				'account_id': account['id'],
				'referendum_id': record['referendum']['id'],
				'rankAtTime': rank,
				'track': track,
				'bad': bad,
				'vote': record['vote']
			})
	
	return records

# Track that a rank can vote on
def eligible_to_vote(rank, track):
	return track in votable_tracks(rank)

def votable_tracks(rank):
	if rank == 0:
		return []
	elif rank == 1:
		return [1]
	elif rank == 2:
		return [1, 2]
	elif rank == 3:
		return [1, 2, 3, 11, 21, 31]
	else:
		raise Exception("Dont know what this rank can vote on, please extend the function")

def main():
	# Parse command line arguments
	args = parse_arguments()
	
	try:		
		response_data = query_voting_records(args.account, args.endpoint, args.filter_rank)
		
		# Analyze the results
		records = analyze_voting_records(response_data)
		n_bad = 0
		n_voted = 0
		n_inelegible = 0
		
		records.sort(key=lambda x: (x['bad'], x['vote']))
		
		# Output results
		for record in records:
			not_eligible = ""
			prefix = "❌" if record['bad'] else "✅"
			if record['bad']:
				n_bad += 1
			elif record['vote'] == 'NoVote':
				n_inelegible += 1
				not_eligible = " (ineligible)"
			else:
				n_voted += 1							

			print(f"{prefix} Ref {record['referendum_id']} track {record['track']:>2}, rank: {record['rankAtTime']}, vote: {record['vote']}{not_eligible}")

		ratio_good = n_voted / (len(records) - n_inelegible) * 100
		print(f"Out of all {len(records)} referenda that occurred while the fellow was rank {args.filter_rank}, they voted on {n_voted} out of the {len(records) - n_inelegible} referenda that they were eligible to vote on. They failed to vote on {n_bad} eligible referenda. The voting participation is therefore {ratio_good:.2f}%")
			
	except Exception as e:
		print(f"Error: {str(e)}")
		return 1
	
	return 0

if __name__ == "__main__":
	exit(main())
