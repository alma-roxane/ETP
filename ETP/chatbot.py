from datetime import datetime, timedelta
from database import get_transactions, get_summary

def get_chatbot_response(user_input, transactions, currency_symbol="$"):
    """
    Generate chatbot response based on user input and financial data.
    
    Args:
        user_input: User's question/prompt
        transactions: List of transaction dictionaries
        currency_symbol: Symbol to use for currency display (default: "$")
    """
    user_input_lower = user_input.lower()

    # Spending this month
    if "spend" in user_input_lower and "month" in user_input_lower:
        return get_monthly_spending(transactions, currency_symbol)

    # Total expenses
    elif "total expense" in user_input_lower or "how much did i spend" in user_input_lower:
        summary = get_summary()
        return f"Your total expenses are {currency_symbol}{summary['total_expenses']:.2f}"

    # Total income
    elif "total income" in user_input_lower or "how much did i earn" in user_input_lower:
        summary = get_summary()
        return f"Your total income is {currency_symbol}{summary['total_income']:.2f}"

    # Balance
    elif "balance" in user_input_lower or "how much do i have" in user_input_lower:
        summary = get_summary()
        return f"Your current balance is {currency_symbol}{summary['balance']:.2f}"

    # Budget recommendation
    elif "budget" in user_input_lower or "suggest" in user_input_lower:
        return get_budget_recommendation(transactions, currency_symbol)

    # Expense breakdown
    elif "breakdown" in user_input_lower or "category" in user_input_lower:
        return get_expense_breakdown(transactions, currency_symbol)

    # Spending trends
    elif "trend" in user_input_lower or "pattern" in user_input_lower:
        return get_spending_trends(transactions, currency_symbol)

    # Savings tips
    elif "save" in user_input_lower or "tip" in user_input_lower:
        return get_savings_tips(transactions, currency_symbol)

    # Default response
    else:
        return get_financial_insights(transactions, currency_symbol)


def get_monthly_spending(transactions, currency_symbol="$"):
    """Get spending for the current month."""
    current_month = datetime.now().strftime("%Y-%m")
    
    monthly_expenses = sum(
        t['amount'] for t in transactions
        if t['type'] == 'expense' and t['date'].startswith(current_month)
    )
    
    return f"You spent {currency_symbol}{monthly_expenses:.2f} this month ({datetime.now().strftime('%B %Y')})."


def get_budget_recommendation(transactions, currency_symbol="$"):
    """Provide budget recommendations based on spending patterns."""
    summary = get_summary()
    total_income = summary['total_income']
    
    if total_income == 0:
        return "💡 Add some income transactions to get personalized budget recommendations."
    
    # 50/30/20 rule inspired budgeting
    recommended_budget = {
        "Food": total_income * 0.15,
        "Transport": total_income * 0.10,
        "Entertainment": total_income * 0.10,
        "Utilities": total_income * 0.10,
        "Healthcare": total_income * 0.05,
        "Shopping": total_income * 0.10,
        "Savings": total_income * 0.40
    }
    
    response = f"📊 **Recommended Monthly Budget** (based on your total income of {currency_symbol}{total_income:.2f}):\n\n"
    for category, amount in recommended_budget.items():
        response += f"• **{category}**: {currency_symbol}{amount:.2f}\n"
    
    response += f"\n💡 *Tip: Try to save at least 40% of your income for financial security.*"
    
    return response


def get_expense_breakdown(transactions, currency_symbol="$"):
    """Get expense breakdown by category."""
    category_totals = {}
    
    for t in transactions:
        if t['type'] == 'expense':
            category = t['category']
            category_totals[category] = category_totals.get(category, 0) + t['amount']
    
    if not category_totals:
        return "📝 No expenses recorded yet. Start adding expenses to see your breakdown!"
    
    total_expenses = sum(category_totals.values())
    
    response = "💰 **Your Expense Breakdown by Category**:\n\n"
    for category, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        percentage = (amount / total_expenses * 100) if total_expenses > 0 else 0
        response += f"• **{category}**: {currency_symbol}{amount:.2f} ({percentage:.1f}%)\n"
    
    response += f"\n**Total**: {currency_symbol}{total_expenses:.2f}"
    
    return response


def get_spending_trends(transactions, currency_symbol="$"):
    """Analyze spending trends."""
    if not transactions:
        return "📊 No transactions to analyze yet. Start tracking to see your spending trends!"
    
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    recent_transactions = [t for t in transactions if t['date'] >= thirty_days_ago]
    
    if not recent_transactions:
        return "📅 No transactions in the last 30 days."
    
    total_recent = sum(t['amount'] for t in recent_transactions if t['type'] == 'expense')
    avg_daily = total_recent / 30
    
    # Calculate trend (compare to previous 30 days if data exists)
    sixty_days_ago = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    previous_period = [
        t for t in transactions 
        if sixty_days_ago <= t['date'] < thirty_days_ago and t['type'] == 'expense'
    ]
    
    response = f"📈 **Spending Trends (Last 30 Days)**:\n\n"
    response += f"• **Total spending**: {currency_symbol}{total_recent:.2f}\n"
    response += f"• **Average daily spending**: {currency_symbol}{avg_daily:.2f}\n"
    
    if previous_period:
        prev_total = sum(t['amount'] for t in previous_period)
        change = ((total_recent - prev_total) / prev_total * 100) if prev_total > 0 else 0
        trend_emoji = "📈" if change > 0 else "📉" if change < 0 else "➡️"
        response += f"• **Trend**: {trend_emoji} {abs(change):.1f}% {'increase' if change > 0 else 'decrease' if change < 0 else 'no change'} from previous month\n"
    
    return response


def get_savings_tips(transactions, currency_symbol="$"):
    """Provide personalized savings tips."""
    category_totals = {}
    
    for t in transactions:
        if t['type'] == 'expense':
            category = t['category']
            category_totals[category] = category_totals.get(category, 0) + t['amount']
    
    if not category_totals:
        return "💡 Start tracking expenses to get personalized savings tips!"
    
    highest_category = max(category_totals, key=category_totals.get)
    highest_amount = category_totals[highest_category]
    
    tips = {
        "Food": "🍳 Consider meal planning and cooking at home to reduce food expenses.",
        "Transport": "🚌 Use public transportation or carpool to save on transport costs.",
        "Entertainment": "🎭 Look for free or low-cost entertainment options in your area.",
        "Shopping": "🛍️ Set a budget for shopping and avoid impulse purchases.",
        "Utilities": "💡 Reduce energy consumption by using LED bulbs and unplugging devices.",
        "Healthcare": "🏥 Maintain preventive care to avoid expensive medical bills."
    }
    
    response = f"💡 **Personalized Savings Tips**:\n\n"
    response += f"Your highest spending is on **{highest_category}** ({currency_symbol}{highest_amount:.2f}). "
    response += f"{tips.get(highest_category, 'Consider reducing this expense.')}\n\n"
    response += "**General Money-Saving Tips**:\n"
    response += "✓ Track all your expenses daily\n"
    response += "✓ Set monthly budget goals for each category\n"
    response += "✓ Build an emergency fund (3-6 months of expenses)\n"
    response += "✓ Review and adjust your budget regularly\n"
    response += "✓ Automate savings transfers\n"
    
    return response


def get_financial_insights(transactions, currency_symbol="$"):
    """Provide general financial insights."""
    summary = get_summary()
    
    response = "📊 **Your Financial Overview**:\n\n"
    response += f"• **Total Income**: {currency_symbol}{summary['total_income']:.2f}\n"
    response += f"• **Total Expenses**: {currency_symbol}{summary['total_expenses']:.2f}\n"
    response += f"• **Current Balance**: {currency_symbol}{summary['balance']:.2f}\n\n"
    
    if summary['balance'] > 0:
        savings_rate = (summary['balance'] / summary['total_income'] * 100) if summary['total_income'] > 0 else 0
        response += f"✅ Great job! You're saving {savings_rate:.1f}% of your income. Keep it up!\n"
        
        if savings_rate < 20:
            response += "💡 Try to increase your savings rate to at least 20% for better financial security."
        elif savings_rate >= 40:
            response += "🌟 Excellent savings rate! You're building a strong financial foundation."
            
    elif summary['balance'] < 0:
        response += "⚠️ You're spending more than you earn. Consider:\n"
        response += "• Reviewing your expenses and cutting unnecessary costs\n"
        response += "• Finding ways to increase your income\n"
        response += "• Creating a strict budget to get back on track"
    else:
        response += "➡️ Your income and expenses are balanced. Consider saving more for emergencies."
    
    return response