import os

import plaid
from dotenv import load_dotenv
from flask import Blueprint, jsonify, request

from plaid.api import plaid_api
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products


load_dotenv()

plaid_bp = Blueprint('plaid', __name__)


configuration = plaid.Configuration(
    host=plaid.Environment.Sandbox,
    api_key={
        'clientId': os.getenv('PLAID_CLIENT_ID'),
        'secret': os.getenv('PLAID_SECRET')
    }
)

api_client = plaid.ApiClient(configuration)
plaid_client = plaid_api.PlaidApi(api_client)


@plaid_bp.route('/link-token', methods=['POST'])
def create_link_token():
    try:
        link_request = LinkTokenCreateRequest(
            products=[
                Products('transactions')
            ],
            client_name='Cache Money',
            country_codes=[
                CountryCode('US')
            ],
            language='en',
            user=LinkTokenCreateRequestUser(
                client_user_id='cache-money-sandbox-user'
            )
        )

        response = plaid_client.link_token_create(link_request)

        return jsonify({
            'link_token': response['link_token']
        })

    except Exception as error:
        print('Plaid link token error:', error)

        return jsonify({
            'error': 'Unable to create Plaid link token'
        }), 500


@plaid_bp.route('/exchange-token', methods=['POST'])
def exchange_token():
    try:
        data = request.get_json()

        if not data or not data.get('public_token'):
            return jsonify({
                'error': 'Public token is required'
            }), 400

        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=data['public_token']
        )

        exchange_response = plaid_client.item_public_token_exchange(
            exchange_request
        )

        access_token = exchange_response['access_token']
        item_id = exchange_response['item_id']

        accounts_request = AccountsGetRequest(
            access_token=access_token
        )

        accounts_response = plaid_client.accounts_get(
            accounts_request
        ).to_dict()

        accounts = []

        for account in accounts_response['accounts']:
            accounts.append({
                'account_id': account['account_id'],
                'name': account['name'],
                'official_name': account.get('official_name'),
                'mask': account.get('mask'),
                'type': str(account.get('type')),
                'subtype': str(account.get('subtype')),
                'current_balance': account['balances'].get('current'),
                'available_balance': account['balances'].get('available'),
                'currency': account['balances'].get('iso_currency_code')
            })

        return jsonify({
            'item_id': item_id,
            'accounts': accounts
        })

    except Exception as error:
        print('Plaid token exchange error:', error)

        return jsonify({
            'error': 'Unable to retrieve Plaid accounts'
        }), 500