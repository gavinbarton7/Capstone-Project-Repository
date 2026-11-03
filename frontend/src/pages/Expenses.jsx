import { Icon } from '@iconify/react'

const budgetCategories = [
    {
        name: 'Housing',
        amount: '$1,800 of $1,800',
        percent: 100,
        icon: 'mdi:home-outline'
    },
    {
        name: 'Groceries',
        amount: '$420 of $650',
        percent: 65,
        icon: 'mdi:basket-outline'
    },
    {
        name: 'Dining & coffee',
        amount: '$260 of $450',
        percent: 58,
        icon: 'mdi:coffee-outline'
    },
    {
        name: 'Transport',
        amount: '$180 of $350',
        percent: 51,
        icon: 'mdi:bus'
    },
    {
        name: 'Shopping',
        amount: '$310 of $600',
        percent: 52,
        icon: 'mdi:shopping-outline'
    },
    {
        name: 'Bills & subscriptions',
        amount: '$180 of $350',
        percent: 51,
        icon: 'mdi:receipt-text-outline'
    }
]

const transactions = [
    {
        name: 'Whole Foods Market',
        category: 'Groceries',
        account: 'Everyday debit',
        date: 'Sep 30',
        amount: '-$82.40',
        icon: 'mdi:basket-outline'
    },
    {
        name: 'Blue Bottle Coffee',
        category: 'Dining & coffee',
        account: 'Everyday debit',
        date: 'Sep 30',
        amount: '-$6.50',
        icon: 'mdi:coffee-outline'
    },
    {
        name: 'City Transit',
        category: 'Transport',
        account: 'Everyday debit',
        date: 'Sep 29',
        amount: '-$24.00',
        icon: 'mdi:bus'
    }
]

function Expenses() {
    return (
        <div className="dashboard-content">

            <div className="dashboard-heading">

                <div>
                    <h1>Expenses</h1>
                    <p>The month's spending against your budget plans.</p>
                </div>

                <div className="dashboard-actions">

                    <button
                        type="button"
                        className="btn new-budget-button"
                    >
                        Connect to Plaid
                    </button>

                    <button
                        type="button"
                        className="btn new-budget-button"
                    >
                        Manually Add Expense
                    </button>

                </div>

            </div>

            <section className="dashboard-card expense-budget-card">

                <div className="section-heading">

                    <h2>Expense budget plans</h2>

                    <button
                        type="button"
                        className="text-button"
                    >
                        Manage plans
                        <Icon icon="mdi:arrow-top-right" />
                    </button>

                </div>

                <div className="budget-summary">

                    <div>
                        <small>Monthly spending</small>

                        <div>
                            <strong>$3,150</strong>
                            <span> / $4,200</span>
                        </div>
                    </div>

                    <div className="left-to-spend">
                        <small>Left to spend</small>
                        <strong>$1,050</strong>
                    </div>

                </div>

                <div className="budget-category-grid">

                    {budgetCategories.map((category) => (
                        <div
                            className="budget-category"
                            key={category.name}
                        >

                            <div className="budget-category-info">

                                <div className="category-icon">
                                    <Icon icon={category.icon} />
                                </div>

                                <div>
                                    <strong>{category.name}</strong>
                                    <small>{category.amount}</small>
                                </div>

                                <span className="category-percent">
                  {category.percent}%
                </span>

                            </div>

                            <div className="progress-track">

                                <div
                                    className="progress-fill"
                                    style={{ width: `${category.percent}%` }}
                                />

                            </div>

                        </div>
                    ))}

                </div>

                <div className="budget-message">
                    <Icon icon="mdi:check-circle-outline" />
                    75% of your budget used. Every category is within its limit.
                </div>

            </section>

            <section className="dashboard-card expense-transactions-card">

                <div className="section-heading">

                    <h2>Recent transactions</h2>

                    <button
                        type="button"
                        className="text-button"
                    >
                        View all
                        <Icon icon="mdi:arrow-top-right" />
                    </button>

                </div>

                <div className="transaction-list">

                    {transactions.map((transaction) => (
                        <div
                            className="transaction-row"
                            key={transaction.name}
                        >

                            <div className="transaction-main">

                                <div className="transaction-icon">
                                    <Icon icon={transaction.icon} />
                                </div>

                                <div>
                                    <strong>{transaction.name}</strong>

                                    <small>
                                        {transaction.category} · {transaction.account}
                                    </small>
                                </div>

                            </div>

                            <span className="transaction-date">
                {transaction.date}
              </span>

                            <strong className="transaction-amount">
                                {transaction.amount}
                            </strong>

                        </div>
                    ))}

                </div>

            </section>

        </div>
    )
}

export default Expenses