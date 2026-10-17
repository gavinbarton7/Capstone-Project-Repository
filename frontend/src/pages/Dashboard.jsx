function Dashboard() {
    return (
        <div className="dashboard-content">

            <div className="dashboard-heading">

                <div>
                    <h1>A little planning. More possibility.</h1>
                    <p>Your budget, all in one place.</p>
                </div>

                <button className="btn btn-success">
                    + New budget
                </button>

            </div>

            <div className="row g-3">

                <div className="col-lg-4">
                    <div className="dashboard-card">

                        <span>Total assets</span>

                        <h2 className="mt-3">$42,580.00</h2>

                        <hr />

                        <div className="asset-details">

                            <div>
                                <small>Card accounts</small>
                                <strong>$5,530</strong>
                            </div>

                            <div>
                                <small>Savings</small>
                                <strong>$17,050</strong>
                            </div>

                            <div>
                                <small>Investments</small>
                                <strong>$20,000</strong>
                            </div>

                        </div>

                    </div>
                </div>

                <div className="col-lg-4">
                    <div className="dashboard-card debit-card dark-card">

                        <span>Everyday debit</span>
                        <small>Available balance</small>

                        <h2>$4,280.00</h2>

                        <span>•••• 4829</span>

                    </div>
                </div>

                <div className="col-lg-4">
                    <div className="dashboard-card debit-card light-card">

                        <span>Travel debit</span>
                        <small>Available balance</small>

                        <h2>$1,250.00</h2>

                        <span>•••• 9016</span>

                    </div>
                </div>

            </div>

        </div>
    )
}

export default Dashboard