/**
 * Data Seeder Service
 * Automatically populates sample data for new users or users without data
 * Called after successful login
 */

import { supabase } from "@/lib/supabase";

interface SeedDataOptions {
  userId: string;
  phoneNumber?: string;
}

/**
 * Check if user has any data in key tables
 */
const hasUserData = async (userId: string): Promise<boolean> => {
  try {
    // Check for transactions
    const { data: transactions } = await supabase
      .from('transactions')
      .select('transaction_id')
      .eq('user_id', userId)
      .limit(1);

    // Check for risk assessments
    const { data: riskAssessments } = await supabase
      .from('risk_assessments')
      .select('id')
      .eq('user_id', userId)
      .limit(1);

    // Check for executed actions
    const { data: actions } = await supabase
      .from('executed_actions')
      .select('id')
      .eq('user_id', userId)
      .limit(1);

    // If user has any of these, consider them as having data
    return (transactions && transactions.length > 0) ||
           (riskAssessments && riskAssessments.length > 0) ||
           (actions && actions.length > 0);
  } catch (error) {
    console.error('[DataSeeder] Error checking user data:', error);
    return false;
  }
};

/**
 * Seed sample transactions for the user
 */
const seedTransactions = async (userId: string) => {
  const today = new Date();
  const transactions = [];

  // Generate transactions for the last 30 days
  for (let i = 0; i < 30; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    // Income transactions (every 2-3 days)
    if (i % 3 === 0) {
      const incomeAmounts = [500, 750, 1000, 1200, 1500];
      const sources = ['Uber', 'Swiggy', 'Zomato', 'Freelance', 'Delivery'];
      transactions.push({
        user_id: userId,
        transaction_date: dateStr,
        transaction_time: `${Math.floor(Math.random() * 12) + 8}:${String(Math.floor(Math.random() * 60)).padStart(2, '0')}:00`,
        amount: incomeAmounts[Math.floor(Math.random() * incomeAmounts.length)],
        transaction_type: 'income',
        category: 'Gig Work',
        source: sources[Math.floor(Math.random() * sources.length)],
        payment_method: 'UPI',
        description: `Earnings from ${sources[Math.floor(Math.random() * sources.length)]}`,
        verified: true,
        is_recurring: false,
      });
    }

    // Expense transactions (daily)
    const expenseCategories = [
      { category: 'Food', subcategory: 'Meals', amounts: [50, 100, 150, 200] },
      { category: 'Transport', subcategory: 'Fuel', amounts: [200, 300, 400, 500] },
      { category: 'Food', subcategory: 'Groceries', amounts: [300, 500, 700, 1000] },
      { category: 'Utilities', subcategory: 'Mobile', amounts: [199, 299, 399] },
      { category: 'Misc', subcategory: 'Other', amounts: [100, 200, 300] },
    ];

    const expense = expenseCategories[Math.floor(Math.random() * expenseCategories.length)];
    transactions.push({
      user_id: userId,
      transaction_date: dateStr,
      transaction_time: `${Math.floor(Math.random() * 12) + 8}:${String(Math.floor(Math.random() * 60)).padStart(2, '0')}:00`,
      amount: expense.amounts[Math.floor(Math.random() * expense.amounts.length)],
      transaction_type: 'expense',
      category: expense.category,
      subcategory: expense.subcategory,
      payment_method: ['UPI', 'Cash', 'Card'][Math.floor(Math.random() * 3)],
      description: `${expense.category} - ${expense.subcategory}`,
      verified: true,
      is_recurring: false,
    });
  }

  // Insert transactions in batches
  const batchSize = 10;
  for (let i = 0; i < transactions.length; i += batchSize) {
    const batch = transactions.slice(i, i + batchSize);
    const { error } = await supabase.from('transactions').insert(batch);
    if (error) {
      console.error('[DataSeeder] Error seeding transactions:', error);
    }
  }

  console.log(`[DataSeeder] Seeded ${transactions.length} transactions`);
};

/**
 * Seed risk assessment data
 */
const seedRiskAssessment = async (userId: string) => {
  const riskData = {
    user_id: userId,
    overall_risk_level: 'medium',
    risk_score: 5.5,
    risk_factors: [
      { factor: 'Low emergency fund coverage', impact: 'Only 2.5 months of expenses covered' },
      { factor: 'Variable income pattern', impact: 'Income fluctuates significantly week-to-week' },
      { factor: 'High expense variability', impact: 'Expenses can spike 1.5x during peak periods' },
    ],
    debt_to_income_ratio: 0.3,
    income_drop_percentage: 0,
    expense_spike_factor: 1.5,
    emergency_fund_coverage: 2.5,
    escalation_needed: false,
    recommended_actions: [
      { action: 'Build emergency fund to 6 months', description: 'Target: Save ₹50,000 over next 6 months' },
      { action: 'Reduce discretionary spending', description: 'Cut non-essential expenses by 20%' },
      { action: 'Diversify income sources', description: 'Consider additional gig platforms' },
    ],
    ai_risk_analysis: 'Based on your transaction history, your financial risk is moderate. Main concerns are low emergency fund coverage and income volatility. Recommended actions focus on building savings buffer and managing expenses during low-income periods.',
  };

  const { error } = await supabase.from('risk_assessments').insert(riskData);
  if (error) {
    console.error('[DataSeeder] Error seeding risk assessment:', error);
  } else {
    console.log('[DataSeeder] Seeded risk assessment');
  }
};

/**
 * Seed executed actions data
 */
const seedExecutedActions = async (userId: string) => {
  const today = new Date();
  const todayStr = today.toISOString().split('T')[0];

  const actions = [
    // Today's Action
    {
      user_id: userId,
      action_type: 'savings',
      action_description: 'Auto-save ₹500 to emergency fund',
      status: 'active',
      amount: 500.00,
      schedule: 'daily',
      next_execution: todayStr,
      user_approved: true,
      is_reversible: true,
    },
    // Upcoming Actions
    {
      user_id: userId,
      action_type: 'debt',
      action_description: 'Pay ₹2000 towards credit card debt',
      status: 'pending',
      amount: 2000.00,
      schedule: 'weekly',
      next_execution: new Date(today.getTime() + 3 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      user_approved: false,
      is_reversible: false,
    },
    {
      user_id: userId,
      action_type: 'savings',
      action_description: 'Transfer ₹1000 to savings account',
      status: 'pending',
      amount: 1000.00,
      schedule: 'weekly',
      next_execution: new Date(today.getTime() + 5 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      user_approved: false,
      is_reversible: true,
    },
    // Ongoing Actions
    {
      user_id: userId,
      action_type: 'savings',
      action_description: 'Monthly SIP of ₹3000',
      status: 'active',
      amount: 3000.00,
      schedule: 'monthly',
      next_execution: new Date(today.getTime() + 15 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      user_approved: true,
      is_reversible: true,
      recurrence_count: 3,
    },
    {
      user_id: userId,
      action_type: 'budget',
      action_description: 'Limit food delivery to ₹2000/month',
      status: 'active',
      amount: 2000.00,
      schedule: 'monthly',
      next_execution: new Date(today.getTime() + 20 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      user_approved: true,
      is_reversible: true,
      recurrence_count: 1,
    },
    // Completed Actions
    {
      user_id: userId,
      action_type: 'budget',
      action_description: 'Reduced monthly subscription costs',
      status: 'completed',
      amount: 500.00,
      execution_date: new Date(today.getTime() - 5 * 24 * 60 * 60 * 1000).toISOString(),
      schedule: 'once',
      user_approved: true,
    },
    {
      user_id: userId,
      action_type: 'savings',
      action_description: 'Emergency fund contribution of ₹5000',
      status: 'completed',
      amount: 5000.00,
      execution_date: new Date(today.getTime() - 10 * 24 * 60 * 60 * 1000).toISOString(),
      schedule: 'once',
      user_approved: true,
    },
  ];

  const { error } = await supabase.from('executed_actions').insert(actions);
  if (error) {
    console.error('[DataSeeder] Error seeding executed actions:', error);
  } else {
    console.log(`[DataSeeder] Seeded ${actions.length} executed actions`);
  }
};

/**
 * Seed recommendations
 */
const seedRecommendations = async (userId: string) => {
  const recommendations = [
    {
      user_id: userId,
      recommendation_type: 'savings',
      priority: 'high',
      title: 'Build Emergency Fund',
      description: 'Aim to save 6 months of expenses (₹50,000) for financial security',
      reasoning: 'Your current emergency fund covers only 2.5 months. Building it to 6 months will provide better protection during income fluctuations.',
      target_amount: 50000,
      target_date: new Date(Date.now() + 180 * 24 * 60 * 60 * 1000).toISOString().split('T')[0],
      confidence_score: 0.85,
      status: 'pending',
    },
    {
      user_id: userId,
      recommendation_type: 'budget',
      priority: 'medium',
      title: 'Reduce Food Delivery Expenses',
      description: 'Limit food delivery to ₹2000/month to save more',
      reasoning: 'Food delivery expenses are high. Cooking at home can save ₹3000-5000 monthly.',
      confidence_score: 0.75,
      status: 'pending',
    },
    {
      user_id: userId,
      recommendation_type: 'debt',
      priority: 'high',
      title: 'Pay Off High-Interest Debt',
      description: 'Focus on paying credit card debt to reduce interest burden',
      reasoning: 'High-interest debt reduces your ability to save. Paying it off should be a priority.',
      confidence_score: 0.9,
      status: 'pending',
    },
  ];

  const { error } = await supabase.from('recommendations').insert(recommendations);
  if (error) {
    console.error('[DataSeeder] Error seeding recommendations:', error);
  } else {
    console.log(`[DataSeeder] Seeded ${recommendations.length} recommendations`);
  }
};

/**
 * Main function to seed all data for a user
 * Only seeds if user doesn't have existing data
 */
export const seedUserData = async (options: SeedDataOptions): Promise<boolean> => {
  const { userId } = options;

  try {
    console.log('[DataSeeder] Checking if user has existing data...');
    
    // Check if user already has data
    const hasData = await hasUserData(userId);
    if (hasData) {
      console.log('[DataSeeder] User already has data, skipping seed');
      return false;
    }

    console.log('[DataSeeder] User has no data, seeding sample data...');

    // Seed data in parallel for better performance
    await Promise.all([
      seedTransactions(userId),
      seedRiskAssessment(userId),
      seedExecutedActions(userId),
      seedRecommendations(userId),
    ]);

    console.log('[DataSeeder] ✅ Data seeding completed successfully');
    return true;
  } catch (error) {
    console.error('[DataSeeder] ❌ Error seeding user data:', error);
    return false;
  }
};

/**
 * Force seed data (ignores existing data check)
 * Useful for testing or resetting user data
 */
export const forceSeedUserData = async (options: SeedDataOptions): Promise<boolean> => {
  const { userId } = options;

  try {
    console.log('[DataSeeder] Force seeding data for user...');

    await Promise.all([
      seedTransactions(userId),
      seedRiskAssessment(userId),
      seedExecutedActions(userId),
      seedRecommendations(userId),
    ]);

    console.log('[DataSeeder] ✅ Force data seeding completed');
    return true;
  } catch (error) {
    console.error('[DataSeeder] ❌ Error force seeding user data:', error);
    return false;
  }
};



