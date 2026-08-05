import os
import requests

def main():
    k = os.getenv('ORIX_OR_OPENROUTER_KEY')
    if not k:
        print('No ORIX_OR_OPENROUTER_KEY env var set')
        return 2
    url = 'https://openrouter.ai/v1/chat/completions'
    payload = {
      'model': 'gpt-4o-mini',
      'messages': [{'role':'user','content':'Orix health-check: say hello and return a short JSON {"ok":true}'}],
      'temperature': 0.0,
    }
    headers = {'Authorization': f'Bearer {k}', 'Content-Type': 'application/json'}
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        print('STATUS', r.status_code)
        print(r.text[:2000])
        return 0
    except Exception as e:
        print('ERROR', e)
        return 3

if __name__ == '__main__':
    raise SystemExit(main())
