import requests


def main():
    data = {
        'id': 3,
        'search': 'abc',
        'test': False,
        'status': 1,
        'stime': '2020-01-01',
        'etime': '2020-02-01',
        'order': {
            'order_no': 'A123456789',
            'pay_time': '2020-01-01 11:00:00',
            'status': 'success',
            'amount': 100
        },
        'user': {
            'uid': 111,
            'name': 'test',
            'roles': [1, 2],
            'remark': '...'
        },
        'ids': []
    }
    headers = {'Content-Type': 'application/json'}
    resp = requests.post('http://localhost:8888/',
                         json=data, headers=headers)
    if resp.status_code == 200:
        print(resp.content)
    else:
        print(resp.status_code)


if __name__ == "__main__":
    main()
