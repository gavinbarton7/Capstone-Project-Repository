import { useEffect, useState } from 'react'
import { usePlaidLink } from 'react-plaid-link'

function BankAccounts() {
    const [linkToken, setLinkToken] = useState(null)
    const [accounts, setAccounts] = useState([])
    const [errorMessage, setErrorMessage] = useState('')
    const [isConnecting, setIsConnecting] = useState(false)

    useEffect(() => {
        async function createLinkToken() {
            try {
                const response = await fetch('/api/plaid/link-token', {
                    method: 'POST',
                    credentials: 'include'
                })

                const data = await response.json()

                if (!response.ok) {
                    setErrorMessage('Unable to connect to Plaid.')
                    return
                }

                setLinkToken(data.link_token)
            } catch (error) {
                console.error('Unable to create Plaid link token:', error)
                setErrorMessage('Unable to connect to Plaid.')
            }
        }

        createLinkToken()
    }, [])

    const { open, ready } = usePlaidLink({
        token: linkToken,

        onSuccess: async (publicToken) => {
            try {
                setIsConnecting(true)
                setErrorMessage('')

                const response = await fetch('/api/plaid/exchange-token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    credentials: 'include',
                    body: JSON.stringify({
                        public_token: publicToken
                    })
                })

                const data = await response.json()

                if (!response.ok) {
                    setErrorMessage('Unable to load bank accounts.')
                    return
                }

                setAccounts(data.accounts)
            } catch (error) {
                console.error('Unable to retrieve Plaid accounts:', error)
                setErrorMessage('Unable to load bank accounts.')
            } finally {
                setIsConnecting(false)
            }
        },

        onExit: (error) => {
            if (error) {
                console.error('Plaid Link error:', error)
            }
        }
    })

    return (
        <div className="dashboard-content">

            <div className="dashboard-heading">

                <div>
                    <h1>Bank Accounts</h1>
                    <p>View and manage your connected bank accounts.</p>
                </div>

                <div className="dashboard-actions">
                    <button
                        type="button"
                        className="btn new-budget-button"
                        onClick={() => open()}
                        disabled={!ready || !linkToken || isConnecting}
                    >
                        {isConnecting ? 'Connecting...' : 'Connect to Plaid'}
                    </button>
                </div>

            </div>

            {errorMessage && (
                <p>{errorMessage}</p>
            )}

            {accounts.length > 0 && (
                <div className="row g-3 mt-3">

                    {accounts.map(account => (
                        <div
                            className="col-md-4"
                            key={account.account_id}
                        >
                            <div className="card h-100">
                                <div className="card-body">

                                    <h5 className="card-title">
                                        {account.name}
                                    </h5>

                                    <p className="card-text">
                                        ••••{account.mask}
                                    </p>

                                    <p className="card-text">
                                        {account.subtype}
                                    </p>

                                    <h4>
                                        ${Number(
                                        account.current_balance || 0
                                    ).toFixed(2)}
                                    </h4>

                                </div>
                            </div>
                        </div>
                    ))}

                </div>
            )}

        </div>
    )
}

export default BankAccounts