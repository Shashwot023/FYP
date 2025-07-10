"""
Simplified Inventory Analysis Model for SME Dashboard
Provides inventory insights and basic predictions without complex ML models
"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import json

class InventoryModel:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        
    def load_data(self):
        """Load inventory and sales data"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Load inventory data
            inventory_query = "SELECT * FROM inventory_table"
            inventory_df = pd.read_sql_query(inventory_query, conn)
            
            # Load sales data
            sales_query = "SELECT * FROM sales_table ORDER BY Date"
            sales_df = pd.read_sql_query(sales_query, conn)
            
            conn.close()
            
            # Convert date columns
            sales_df['Date'] = pd.to_datetime(sales_df['Date'])
            inventory_df['LastRestockDate'] = pd.to_datetime(inventory_df['LastRestockDate'])
            
            return inventory_df, sales_df
            
        except Exception as e:
            print(f"Error loading data: {e}")
            return None, None
    
    def analyze_inventory_status(self, inventory_df):
        """Analyze current inventory status"""
        analysis = {}
        
        # Overall stock status
        stock_status = inventory_df['StockStatus'].value_counts()
        analysis['stock_status'] = {
            'normal': stock_status.get('Normal', 0),
            'low_stock': stock_status.get('Low Stock', 0),
            'out_of_stock': stock_status.get('Out of Stock', 0),
            'overstock': stock_status.get('Overstock', 0)
        }
        
        # ABC classification distribution
        abc_distribution = inventory_df['ABCClassification'].value_counts()
        analysis['abc_distribution'] = {
            'A': abc_distribution.get('A', 0),
            'B': abc_distribution.get('B', 0),
            'C': abc_distribution.get('C', 0)
        }
        
        # Category analysis
        category_stats = inventory_df.groupby('Category').agg({
            'CurrentStock': ['sum', 'mean'],
            'UnitCost': 'mean',
            'MonthlyConsumption': 'sum'
        }).round(2)
        
        category_analysis = {}
        for category in category_stats.index:
            category_analysis[category] = {
                'total_stock': category_stats.loc[category, ('CurrentStock', 'sum')],
                'avg_stock': category_stats.loc[category, ('CurrentStock', 'mean')],
                'avg_cost': category_stats.loc[category, ('UnitCost', 'mean')],
                'monthly_consumption': category_stats.loc[category, ('MonthlyConsumption', 'sum')]
            }
        
        analysis['category_analysis'] = category_analysis
        
        # Store performance
        store_stats = inventory_df.groupby('StoreLocation').agg({
            'CurrentStock': 'sum',
            'UnitCost': 'mean'
        }).round(2)
        
        store_analysis = {}
        for store in store_stats.index:
            total_value = inventory_df[inventory_df['StoreLocation'] == store].apply(
                lambda row: row['CurrentStock'] * row['UnitCost'], axis=1
            ).sum()
            
            store_analysis[store] = {
                'total_stock': store_stats.loc[store, 'CurrentStock'],
                'avg_cost': store_stats.loc[store, 'UnitCost'],
                'total_value': round(total_value, 2)
            }
        
        analysis['store_analysis'] = store_analysis
        
        return analysis
    
    def get_reorder_recommendations(self, inventory_df, top_n=20):
        """Get items that need reordering"""
        # Filter items that need reordering
        reorder_items = inventory_df[
            inventory_df['StockStatus'].isin(['Low Stock', 'Out of Stock'])
        ].copy()
        
        # Calculate urgency score
        def calculate_urgency(row):
            score = 0
            
            # Base score on stock status
            if row['StockStatus'] == 'Out of Stock':
                score = 100
            elif row['StockStatus'] == 'Low Stock':
                if row['ReorderPoint'] > 0:
                    score = 70 + (30 * (1 - row['CurrentStock'] / row['ReorderPoint']))
                else:
                    score = 70
            
            # Adjust for ABC classification
            if row['ABCClassification'] == 'A':
                score *= 1.5
            elif row['ABCClassification'] == 'B':
                score *= 1.2
            
            # Adjust for perishable items
            if row['IsPerishable']:
                score *= 1.3
            
            return min(100, score)
        
        reorder_items['UrgencyScore'] = reorder_items.apply(calculate_urgency, axis=1)
        
        # Calculate recommended order quantity (simple heuristic)
        reorder_items['RecommendedQuantity'] = reorder_items.apply(
            lambda row: max(10, int(row['MonthlyConsumption'] * 2)), axis=1
        )
        
        # Calculate estimated cost
        reorder_items['EstimatedCost'] = reorder_items['RecommendedQuantity'] * reorder_items['UnitCost']
        
        # Sort by urgency and return top N
        recommendations = reorder_items.nlargest(top_n, 'UrgencyScore')[
            ['ProductID', 'ProductName', 'Category', 'StoreLocation', 'CurrentStock', 
             'ReorderPoint', 'UrgencyScore', 'RecommendedQuantity', 'EstimatedCost', 
             'Supplier', 'ABCClassification']
        ].to_dict('records')
        
        return recommendations
    
    def predict_stock_levels(self, inventory_df, days_ahead=30):
        """Simple stock level prediction based on consumption rate"""
        predictions = []
        
        # Sample top 20 products for performance
        sample_products = inventory_df.nlargest(20, 'MonthlyConsumption')
        
        for _, product in sample_products.iterrows():
            daily_consumption = product['MonthlyConsumption'] / 30
            
            # Predict stock levels for next N days
            future_stock = []
            current_stock = product['CurrentStock']
            
            for day in range(days_ahead + 1):
                stock_level = max(0, current_stock - (daily_consumption * day))
                future_stock.append(stock_level)
            
            # Determine when stock will run out
            stockout_day = None
            for day, stock in enumerate(future_stock):
                if stock <= 0:
                    stockout_day = day
                    break
            
            prediction = {
                'ProductID': product['ProductID'],
                'ProductName': product['ProductName'],
                'Category': product['Category'],
                'StoreLocation': product['StoreLocation'],
                'CurrentStock': product['CurrentStock'],
                'DailyConsumption': round(daily_consumption, 2),
                'StockoutRisk': 'High' if stockout_day and stockout_day <= days_ahead else 'Low',
                'DaysUntilStockout': stockout_day if stockout_day else 'No risk',
                'PredictedStock30Days': round(future_stock[30], 2) if len(future_stock) > 30 else 0
            }
            
            predictions.append(prediction)
        
        return predictions
    
    def generate_inventory_insights(self, inventory_df):
        """Generate actionable inventory insights"""
        insights = []
        
        # Critical stock alerts
        out_of_stock = len(inventory_df[inventory_df['StockStatus'] == 'Out of Stock'])
        low_stock = len(inventory_df[inventory_df['StockStatus'] == 'Low Stock'])
        
        if out_of_stock > 0:
            insights.append({
                'type': 'critical',
                'title': 'Stock-out Alert',
                'description': f'{out_of_stock} items are completely out of stock',
                'icon': 'warning',
                'priority': 'High'
            })
        
        if low_stock > 50:
            insights.append({
                'type': 'warning',
                'title': 'Low Stock Warning',
                'description': f'{low_stock} items are below reorder point',
                'icon': 'alert-triangle',
                'priority': 'Medium'
            })
        
        # ABC analysis insight
        a_class_items = len(inventory_df[inventory_df['ABCClassification'] == 'A'])
        total_items = len(inventory_df)
        a_class_percentage = (a_class_items / total_items) * 100 if total_items > 0 else 0
        
        insights.append({
            'type': 'info',
            'title': 'High-Value Items',
            'description': f'{a_class_percentage:.1f}% of items are A-class (high value)',
            'icon': 'star',
            'priority': 'Low'
        })
        
        # Perishable items insight
        perishable_count = len(inventory_df[inventory_df['IsPerishable'] == 1])
        if perishable_count > 0:
            insights.append({
                'type': 'info',
                'title': 'Perishable Inventory',
                'description': f'{perishable_count} perishable items require careful monitoring',
                'icon': 'clock',
                'priority': 'Medium'
            })
        
        # Inventory value insight
        total_value = (inventory_df['CurrentStock'] * inventory_df['UnitCost']).sum()
        insights.append({
            'type': 'success',
            'title': 'Total Inventory Value',
            'description': f'Current inventory worth NPR {total_value:,.0f}',
            'icon': 'dollar-sign',
            'priority': 'Low'
        })
        
        return insights
    
    def get_inventory_charts_data(self, inventory_df):
        """Generate data for inventory charts"""
        charts_data = {}
        
        # ABC Classification Chart
        abc_counts = inventory_df['ABCClassification'].value_counts()
        charts_data['abc_classification'] = {
            'labels': abc_counts.index.tolist(),
            'values': abc_counts.values.tolist()
        }
        
        # Stock Status Chart
        status_counts = inventory_df['StockStatus'].value_counts()
        charts_data['stock_status'] = {
            'labels': status_counts.index.tolist(),
            'values': status_counts.values.tolist()
        }
        
        # Category Value Distribution
        category_values = inventory_df.groupby('Category').apply(
            lambda x: (x['CurrentStock'] * x['UnitCost']).sum()
        ).sort_values(ascending=False)
        
        charts_data['category_values'] = {
            'categories': category_values.index.tolist(),
            'values': category_values.values.tolist()
        }
        
        # Store Performance
        store_values = inventory_df.groupby('StoreLocation').apply(
            lambda x: (x['CurrentStock'] * x['UnitCost']).sum()
        )
        
        charts_data['store_performance'] = {
            'stores': store_values.index.tolist(),
            'values': store_values.values.tolist()
        }
        
        # Top Products by Value
        product_values = inventory_df.groupby(['ProductName', 'Category']).apply(
            lambda x: (x['CurrentStock'] * x['UnitCost']).sum()
        ).sort_values(ascending=False).head(10)
        
        charts_data['top_products'] = {
            'products': [name for name, _ in product_values.index],
            'categories': [category for _, category in product_values.index],
            'values': product_values.values.tolist()
        }
        
        # Monthly Consumption Trends (simulated)
        top_categories = inventory_df.groupby('Category')['MonthlyConsumption'].sum().nlargest(5)
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        consumption_trends = {}
        for category in top_categories.index:
            base_consumption = top_categories[category]
            # Add some seasonal variation
            monthly_data = []
            for i in range(12):
                seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * i / 12)  # Seasonal variation
                monthly_data.append(base_consumption * seasonal_factor / 12)
            
            consumption_trends[category] = {
                'months': months,
                'consumption': monthly_data
            }
        
        charts_data['consumption_trends'] = consumption_trends
        
        return charts_data
    
    def get_dashboard_summary(self, inventory_df):
        """Get summary metrics for dashboard"""
        total_items = len(inventory_df)
        total_value = (inventory_df['CurrentStock'] * inventory_df['UnitCost']).sum()
        low_stock_items = len(inventory_df[inventory_df['StockStatus'] == 'Low Stock'])
        out_of_stock_items = len(inventory_df[inventory_df['StockStatus'] == 'Out of Stock'])
        
        # Calculate stock health percentage
        healthy_items = len(inventory_df[inventory_df['StockStatus'] == 'Normal'])
        stock_health = (healthy_items / total_items) * 100 if total_items > 0 else 0
        
        # Calculate average days of stock remaining
        avg_days_remaining = inventory_df.apply(
            lambda row: row['CurrentStock'] / (row['MonthlyConsumption'] / 30) 
            if row['MonthlyConsumption'] > 0 else 999, axis=1
        ).mean()
        
        summary = {
            'total_items': total_items,
            'total_value': round(total_value, 2),
            'low_stock_items': low_stock_items,
            'out_of_stock_items': out_of_stock_items,
            'stock_health_percentage': round(stock_health, 1),
            'avg_days_remaining': round(avg_days_remaining, 1),
            'critical_items': low_stock_items + out_of_stock_items
        }
        
        return summary

def test_simplified_model():
    """Test the simplified inventory model"""
    print("Testing Simplified Inventory Model...")
    
    model = InventoryModel('database.db')
    
    # Load data
    inventory_df, sales_df = model.load_data()
    
    if inventory_df is None:
        print("Failed to load inventory data")
        return None
    
    print(f"Loaded {len(inventory_df)} inventory records")
    
    # Get dashboard summary
    summary = model.get_dashboard_summary(inventory_df)
    print(f"\nDashboard Summary:")
    print(f"Total Items: {summary['total_items']}")
    print(f"Total Value: NPR {summary['total_value']:,.2f}")
    print(f"Stock Health: {summary['stock_health_percentage']}%")
    print(f"Critical Items: {summary['critical_items']}")
    
    # Get reorder recommendations
    recommendations = model.get_reorder_recommendations(inventory_df, top_n=5)
    print(f"\nTop 5 Reorder Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec['ProductName']} ({rec['StoreLocation']}) - Urgency: {rec['UrgencyScore']:.1f}")
    
    # Generate insights
    insights = model.generate_inventory_insights(inventory_df)
    print(f"\nInventory Insights:")
    for insight in insights:
        print(f"- {insight['title']}: {insight['description']}")
    
    # Get chart data
    charts_data = model.get_inventory_charts_data(inventory_df)
    print(f"\nChart Data Generated:")
    print(f"- ABC Classification: {len(charts_data['abc_classification']['labels'])} categories")
    print(f"- Stock Status: {len(charts_data['stock_status']['labels'])} statuses")
    print(f"- Category Values: {len(charts_data['category_values']['categories'])} categories")
    
    return model

if __name__ == '__main__':
    test_simplified_model()


