import sys
import ast
import getpass
from gee_asset_manager.session import get_google_session


def test_interactive_session():
    username = input('Account name: ')
    password = getpass.getpass()
    session = get_google_session(url='https://code.earthengine.google.com/',
                                 account_name=username,
                                 password=password,
                                 headless=False)
    r = session.get("https://code.earthengine.google.com/assets/upload/geturl")
    if r.text.startswith('\n<!DOCTYPE html>'):
        output_filename = 'failed_session.html'
        print(f'FAILED. Returned object is an HTML document. Printing the content to {output_filename}')
        with open(output_filename, 'w') as f:
            f.writelines(r.text)
            sys.exit(1)
    else:
        d = ast.literal_eval(r.text)
        url = d['url']
        print(f'SUCCESS! Our url: {url}')