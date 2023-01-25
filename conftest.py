import os
import requests
import stat

# Lets use the pytest cache directory to store the polkadot binary.
DIR = '.pytest_cache'

def pytest_configure(config):
	os.makedirs(DIR, exist_ok=True)

def pytest_sessionstart(session):
	os.chdir(DIR)
    # Check if the polkadot binary is present
	if os.path.exists('polkadot'):
		print('Found a Polkadot binary')
		return

	# Download the polkadot binary
	print('Downloading polkadot binary')
	url = 'https://github.com/paritytech/polkadot/releases/download/v0.9.37/polkadot'
	r = requests.get(url, allow_redirects=True)
	open('polkadot', 'wb').write(r.content)
	# chmod +x
	st = os.stat('polkadot')
	os.chmod('polkadot', st.st_mode | stat.S_IEXEC)
	os.chdir('..')
