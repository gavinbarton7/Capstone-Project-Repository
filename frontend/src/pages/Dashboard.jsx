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
        date: 'Sep 30',
        amount: '-$82.40',
        icon: 'mdi:basket-outline'
    },
    {
        name: 'Blue Bottle Coffee',
        category: 'Dining & coffee',
        date: 'Sep 30',
        amount: '-$6.50',
        icon: 'mdi:coffee-outline'
    },
    {
        name: 'City Transit',
        category: 'Transport',
        date: 'Sep 29',
        amount: '-$24.00',
        icon: 'mdi:bus'
    }
]

const spendingMonths = [
    { month: 'Apr', height: 70 },
    { month: 'May', height: 76 },
    { month: 'Jun', height: 68 },
    { month: 'Jul', height: 80 },
    { month: 'Aug', height: 73 },
    { month: 'Sep', height: 64, current: true }
]

function Dashboard() {
    return (
        <div className="dashboard-content">

            <div className="dashboard-heading">

                <div>
                    <h1>A little planning. More possibility.</h1>
                    <p>
                        Your September budget, all in one place. You're right on track, Alex.
                    </p>
                </div>

                <div className="dashboard-actions">

                    <button
                        type="button"
                        className="month-button"
                    >
                        <Icon icon="mdi:calendar-month-outline" />
                        September 2026
                    </button>

                    <button
                        type="button"
                        className="btn new-budget-button"
                    >
                        <Icon icon="mdi:plus" />
                        New budget
                    </button>

                </div>

            </div>

            <div className="dashboard-top-row">

                <div className="dashboard-card total-assets-card">

                    <div className="card-top-line">
                        <span>Total assets</span>
                        <span>USD</span>
                    </div>

                    <div className="total-assets-value">
                        <h2>$42,580.00</h2>
                        <span className="positive-change">
              ↗ 4.2%
            </span>
                    </div>

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

            <div className="dashboard-grid">

                <section className="dashboard-card budget-plan-card">

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

                <section className="dashboard-card spending-card">

                    <div className="section-heading">
                        <h2>Monthly spending</h2>

                        <button
                            type="button"
                            className="text-button"
                        >
                            Last 6 months
                            <Icon icon="mdi:arrow-top-right" />
                        </button>
                    </div>

                    <div className="spending-summary">

                        <div>
                            <strong>$3,150.00</strong>
                            <small>September 2026</small>
                        </div>

                        <div className="spending-change">
                            <strong>↘ 11.0%</strong>
                            <small>vs. last month</small>
                        </div>

                    </div>

                    <div className="spending-chart">

                        {spendingMonths.map((item) => (
                            <div
                                className="chart-column"
                                key={item.month}
                            >

                                <div className="chart-bar-area">
                                    <div
                                        className={
                                            item.current
                                                ? 'chart-bar current'
                                                : 'chart-bar'
                                        }
                                        style={{ height: `${item.height}%` }}
                                    />
                                </div>

                                <span className={item.current ? 'current-month' : ''}>
                  {item.month}
                </span>

                            </div>
                        ))}

                    </div>

                    <div className="spending-note">
                        <Icon icon="mdi:auto-awesome" />
                        $390 less spent than August. Small changes add up.
                    </div>

                </section>

                <section className="dashboard-card transactions-card">

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
                                        <small>{transaction.category}</small>
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

                <section className="dashboard-card savings-card">

                    <div className="section-heading">
                        <h2>A cushion for what's next</h2>

                        <button
                            type="button"
                            className="text-button"
                        >
                            View goals
                            <Icon icon="mdi:arrow-top-right" />
                        </button>
                    </div>

                    <div className="savings-title">

                        <div className="savings-icon">
                            <Icon icon="mdi:shield-check-outline" />
                        </div>

                        <div>
                            <strong>General Savings</strong>
                            <small>Peace of mind, one deposit at a time.</small>
                        </div>

                    </div>

                    <div className="savings-progress-heading">

                        <div>
                            <strong>$8,050</strong>
                            <span> / $10,000</span>
                        </div>

                        <span>80.5%</span>

                    </div>

                    <div className="savings-progress">
                        <div className="savings-progress-fill" />
                    </div>

                    <p className="savings-note">
                        Just $1,950 to go. Included in your $17,050 savings balance.
                    </p>

                </section>

            </div>

            <div className="dashboard-footer">

        <span>
          Last synced Sep 30, 2026 at 9:41 AM · All amounts in USD
        </span>

                <span>
          <Icon icon="mdi:lock-outline" />
          Your money. Your peace of mind.
        </span>

            </div>

        </div>
    )
}

export default Dashboard