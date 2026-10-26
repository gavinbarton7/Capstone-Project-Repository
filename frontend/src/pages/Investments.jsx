function Investments() {
    return (
        <div className="dashboard-content">

            <div className="dashboard-heading">

                <div>
                    <h1>Investments</h1>
                    <p>View and manage your connected investment accounts.</p>
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

export default Investments