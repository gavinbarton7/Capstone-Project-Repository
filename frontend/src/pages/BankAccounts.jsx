function BankAccounts() {
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
                    >
                        Connect to Plaid
                    </button>
                </div>

            </div>

        </div>
    )
}

export default BankAccounts