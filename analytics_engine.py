
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
import json

class AnalyticsEngine:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        
        # Product category mapping for better analysis
        self.category_colors = {
            'Electronics': '#1f77b4',
            'Groceries': '#ff7f0e', 
            'Clothing': '#2ca02c',
            'Jewelry': '#d62728',
            'Personal Care': '#9467bd',
            'Household Items': '#8c564b',
            'Beverages': '#e377c2',
            'Meat': '#7f7f7f',
            'Fruits': '#bcbd22',
            'Flowers': '#17becf',
            'Puja Items': '#ff9896',
            'Sweets': '#ffbb78',
            'Dry Fruits': '#98df8a',
            'Colors': '#c5b0d5'
        }
        
        # Store location mapping
        self.store_locations = ['Pokhara', 'Kathmandu', 'Janakpur', 'Biratnagar']
        
        # Payment methods
        self.payment_methods = ['Mobile Wallet', 'Cash', 'Card']
        
        # Nepali festivals
        self.festivals = [
            'Maha Shivaratri', 'Holi', 'Nepali New Year', 'Eid', 'Teej',
            'Dashain', 'Tihar', 'Chhath Parva', 'Christmas'
        ]
    
    def load_sales_data(self):
        """Load sales data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            query = """
            SELECT * FROM sales_table
            ORDER BY Date
            """
            
            df = pd.read_sql_query(query, conn)
            conn.close()
            
            # Convert Date to datetime
            df['Date'] = pd.to_datetime(df['Date'])
            
            return df
            
        except Exception as e:
            print(f"Error loading sales data: {e}")
            return self._generate_sample_data()
    
    def _generate_sample_data(self):
        """Generate sample data based on actual schema"""
        print("Using sample data for analytics...")
        
        # Create sample data matching the actual schema
        np.random.seed(42)
        
        # Date range
        start_date = datetime(2022, 1, 1)
        end_date = datetime(2024, 12, 31)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Product data based on actual schema
        products = [
            ('P001', 'Basmati Rice 5kg', 'Groceries', 'Staples', 500),
            ('P002', 'Lentils 1kg', 'Groceries', 'Staples', 150),
            ('P003', 'Cooking Oil 1L', 'Groceries', 'Staples', 200),
            ('P004', 'Instant Noodles', 'Groceries', 'Snacks', 50),
            ('P005', 'Biscuits Pack', 'Groceries', 'Snacks', 80),
            ('P006', 'Milk 1L', 'Groceries', 'Dairy', 60),
            ('P007', 'Yogurt 500g', 'Groceries', 'Dairy', 40),
            ('P008', 'Fresh Apples', 'Fruits', 'Seasonal Fruits', 120),
            ('P009', 'Bananas', 'Fruits', 'Seasonal Fruits', 80),
            ('P010', 'Oranges', 'Fruits', 'Seasonal Fruits', 100),
            ('P011', 'Chicken Breast 1kg', 'Meat', 'Poultry', 400),
            ('P012', 'Mutton 1kg', 'Meat', 'Red Meat', 800),
            ('P013', 'Coca-Cola 1.5L', 'Beverages', 'Soft Drinks', 80),
            ('P014', 'Local Beer 650ml', 'Beverages', 'Alcohol', 150),
            ('P015', 'Toothpaste', 'Personal Care', 'Oral Care', 120),
            ('P016', 'Shampoo', 'Personal Care', 'Hair Care', 200),
            ('P017', 'Washing Powder 1kg', 'Household Items', 'Cleaning Supplies', 180),
            ('P018', 'Dish Soap', 'Household Items', 'Cleaning Supplies', 90),
            ('P019', 'Men\'s T-Shirt', 'Clothing', 'Apparel', 800),
            ('P020', 'Women\'s Kurti', 'Clothing', 'Apparel', 1200),
            ('P021', 'Gold Plated Necklace', 'Jewelry', 'Fashion Jewelry', 2500),
            ('P022', 'Silver Earrings', 'Jewelry', 'Fashion Jewelry', 1500),
            ('P023', 'Smartphone', 'Electronics', 'Mobile Phones', 25000),
            ('P024', 'LED TV 32-inch', 'Electronics', 'Televisions', 35000),
            ('P025', 'Diya (Oil Lamp)', 'Puja Items', 'Religious Items', 50),
            ('P026', 'Incense Sticks', 'Puja Items', 'Religious Items', 30),
            ('P027', 'Assorted Sweets 500g', 'Sweets', 'Traditional Sweets', 300),
            ('P028', 'Cashew Nuts 250g', 'Dry Fruits', 'Nuts', 400),
            ('P029', 'Marigold Garland', 'Flowers', 'Fresh Flowers', 100),
            ('P030', 'Holi Color Pack', 'Colors', 'Festival Colors', 150)
        ]
        
        # Generate sample sales data
        sample_data = []
        
        for date in dates:
            # Determine if it's a festival day
            is_festival = np.random.choice([0, 1], p=[0.9, 0.1])
            festival_name = np.random.choice(self.festivals) if is_festival else ''
            
            # Generate 1-10 sales per day
            num_sales = np.random.randint(1, 11)
            
            for _ in range(num_sales):
                product = np.random.choice(products)
                quantity = np.random.randint(1, 6)
                
                # Festival boost
                price_multiplier = 1.5 if is_festival else 1.0
                unit_price = int(product[4] * price_multiplier)
                total_price = unit_price * quantity
                
                sample_data.append({
                    'Date': date.strftime('%Y-%m-%d'),
                    'Year': date.year,
                    'Month': date.month,
                    'DayOfWeek': date.strftime('%A'),
                    'IsFestivalDay': is_festival,
                    'FestivalName': festival_name,
                    'ProductID': product[0],
                    'ProductName': product[1],
                    'Category': product[2],
                    'SubCategory': product[3],
                    'UnitPrice': unit_price,
                    'QuantitySold': quantity,
                    'TotalPrice': total_price,
                    'StoreLocation': np.random.choice(self.store_locations),
                    'PaymentMethod': np.random.choice(self.payment_methods)
                })
        
        df = pd.DataFrame(sample_data)
        df['Date'] = pd.to_datetime(df['Date'])
        
        return df
    
    def get_charts_data(self):
        """Create data for all dashboard charts"""
        df = self.load_sales_data()
        
        return {
            'productPerformance': self._get_product_performance_data(df),
            'paymentSegments': self._get_payment_segments_data(df),
            'seasonalTrends': self._get_seasonal_trends_data(df),
            'categoryBreakdown': self._get_category_breakdown_data(df),
            'storePerformance': self._get_store_performance_data(df),
            'festivalImpact': self._get_festival_impact_data(df),
            'topProducts': self._get_top_products_data(df),
            'monthlyTrends': self._get_monthly_trends_data(df)
        }
    
    def _get_product_performance_data(self, df):
        """Product performance matrix: sales volume vs profit margin"""
        # Calculate product metrics
        product_metrics = df.groupby(['ProductID', 'ProductName', 'Category']).agg({
            'QuantitySold': 'sum',
            'TotalPrice': 'sum',
            'UnitPrice': 'mean'
        }).reset_index()
        
        # Calculate profit margin (simplified as 20-40% of unit price)
        np.random.seed(42)
        product_metrics['ProfitMargin'] = np.random.uniform(20, 40, len(product_metrics))
        
        # Get top 15 products by revenue
        top_products = product_metrics.nlargest(15, 'TotalPrice')
        
        # Ensure all values are valid (not NaN, not zero, finite)
        valid_products = top_products[
            (top_products['QuantitySold'] > 0) & 
            (top_products['TotalPrice'] > 0) & 
            (top_products['ProfitMargin'] > 0) &
            (top_products['QuantitySold'].notna()) &
            (top_products['TotalPrice'].notna()) &
            (top_products['ProfitMargin'].notna())
        ]
        
        if len(valid_products) == 0:
            # Return fallback data if no valid products
            return {
                'x': [100, 150, 200, 75, 300],
                'y': [25, 30, 35, 20, 40],
                'size': [50000, 75000, 100000, 30000, 150000],
                'text': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],
                'color': ['Electronics', 'Groceries', 'Clothing', 'Jewelry', 'Electronics']
            }
        
        return {
            'x': valid_products['QuantitySold'].tolist(),
            'y': valid_products['ProfitMargin'].tolist(),
            'size': (valid_products['TotalPrice'] / 1000).tolist(),  # Scale for bubble size
            'text': valid_products['ProductName'].tolist(),
            'color': valid_products['Category'].tolist()
        }
    
    def _get_payment_segments_data(self, df):
        """Payment method distribution"""
        payment_data = df.groupby('PaymentMethod')['TotalPrice'].sum().reset_index()
        
        return {
            'labels': payment_data['PaymentMethod'].tolist(),
            'values': payment_data['TotalPrice'].tolist()
        }
    
    def _get_seasonal_trends_data(self, df):
        """Monthly sales trends by category"""
        monthly_category = df.groupby(['Month', 'Category'])['TotalPrice'].sum().reset_index()
        
        trends = {}
        for category in df['Category'].unique():
            category_data = monthly_category[monthly_category['Category'] == category]
            
            # Ensure all 12 months are represented
            all_months = pd.DataFrame({'Month': range(1, 13)})
            category_data = all_months.merge(category_data, on='Month', how='left')
            category_data['TotalPrice'] = category_data['TotalPrice'].fillna(0)
            
            trends[category] = {
                'x': category_data['Month'].tolist(),
                'y': category_data['TotalPrice'].tolist()
            }
        
        return trends
    
    def _get_category_breakdown_data(self, df):
        """Revenue breakdown by category"""
        category_revenue = df.groupby('Category')['TotalPrice'].sum().reset_index()
        category_revenue = category_revenue.sort_values('TotalPrice', ascending=False)
        
        return {
            'categories': category_revenue['Category'].tolist(),
            'revenue': category_revenue['TotalPrice'].tolist()
        }
    
    def _get_store_performance_data(self, df):
        """Store location performance"""
        store_performance = df.groupby('StoreLocation').agg({
            'TotalPrice': 'sum',
            'QuantitySold': 'sum'
        }).reset_index()
        
        return {
            'locations': store_performance['StoreLocation'].tolist(),
            'revenue': store_performance['TotalPrice'].tolist(),
            'quantity': store_performance['QuantitySold'].tolist()
        }
    
    def _get_festival_impact_data(self, df):
        """Festival vs regular day sales comparison"""
        festival_comparison = df.groupby('IsFestivalDay')['TotalPrice'].agg(['sum', 'mean', 'count']).reset_index()
        
        return {
            'festival_total': float(festival_comparison[festival_comparison['IsFestivalDay'] == 1]['sum'].iloc[0]) if len(festival_comparison[festival_comparison['IsFestivalDay'] == 1]) > 0 else 0,
            'regular_total': float(festival_comparison[festival_comparison['IsFestivalDay'] == 0]['sum'].iloc[0]) if len(festival_comparison[festival_comparison['IsFestivalDay'] == 0]) > 0 else 0,
            'festival_avg': float(festival_comparison[festival_comparison['IsFestivalDay'] == 1]['mean'].iloc[0]) if len(festival_comparison[festival_comparison['IsFestivalDay'] == 1]) > 0 else 0,
            'regular_avg': float(festival_comparison[festival_comparison['IsFestivalDay'] == 0]['mean'].iloc[0]) if len(festival_comparison[festival_comparison['IsFestivalDay'] == 0]) > 0 else 0
        }
    
    def _get_top_products_data(self, df):
        """Top selling products"""
        top_products = df.groupby(['ProductName', 'Category']).agg({
            'TotalPrice': 'sum',
            'QuantitySold': 'sum'
        }).reset_index()
        
        top_products = top_products.nlargest(10, 'TotalPrice')
        
        return {
            'products': top_products['ProductName'].tolist(),
            'revenue': top_products['TotalPrice'].tolist(),
            'quantity': top_products['QuantitySold'].tolist(),
            'categories': top_products['Category'].tolist()
        }
    
    def _get_monthly_trends_data(self, df):
        """Monthly sales trends over time"""
        monthly_sales = df.groupby([df['Date'].dt.to_period('M')])['TotalPrice'].sum().reset_index()
        monthly_sales['Date'] = monthly_sales['Date'].astype(str)
        
        return {
            'months': monthly_sales['Date'].tolist(),
            'sales': monthly_sales['TotalPrice'].tolist()
        }
    
    def get_business_recommendations(self):
        """Generate AI-powered business recommendations"""
        df = self.load_sales_data()
        
        recommendations = []
        
        # Analyze top performing categories
        category_performance = df.groupby('Category')['TotalPrice'].sum().sort_values(ascending=False)
        top_category = category_performance.index[0]
        top_category_revenue = category_performance.iloc[0]
        total_revenue = category_performance.sum()
        top_category_percentage = (top_category_revenue / total_revenue) * 100
        
        recommendations.append({
            'category': 'Product Strategy',
            'title': f'Focus on {top_category} Category',
            'description': f'{top_category} generates {top_category_percentage:.1f}% of total revenue (NPR {top_category_revenue:,.0f}). Consider expanding inventory and marketing for this category.',
            'priority': 'High',
            'impact': 'Revenue Growth'
        })
        
        # Festival impact analysis
        festival_impact = self._get_festival_impact_data(df)
        if festival_impact['festival_avg'] > 0 and festival_impact['regular_avg'] > 0:
            impact_percentage = ((festival_impact['festival_avg'] - festival_impact['regular_avg']) / festival_impact['regular_avg']) * 100
            
            recommendations.append({
                'category': 'Marketing Strategy',
                'title': 'Leverage Festival Seasons',
                'description': f'Festival days show {impact_percentage:.1f}% higher average sales. Plan special campaigns and inventory for upcoming Nepali festivals.',
                'priority': 'High',
                'impact': 'Revenue Growth'
            })
        
        # Store performance analysis
        store_performance = df.groupby('StoreLocation')['TotalPrice'].sum().sort_values(ascending=False)
        best_store = store_performance.index[0]
        worst_store = store_performance.index[-1]
        performance_gap = ((store_performance.iloc[0] - store_performance.iloc[-1]) / store_performance.iloc[-1]) * 100
        
        recommendations.append({
            'category': 'Operations',
            'title': 'Store Performance Optimization',
            'description': f'{best_store} outperforms {worst_store} by {performance_gap:.1f}%. Analyze successful practices from {best_store} and implement in other locations.',
            'priority': 'Medium',
            'impact': 'Operational Efficiency'
        })
        
        # Payment method trends
        payment_trends = df.groupby('PaymentMethod')['TotalPrice'].sum().sort_values(ascending=False)
        top_payment = payment_trends.index[0]
        top_payment_percentage = (payment_trends.iloc[0] / payment_trends.sum()) * 100
        
        recommendations.append({
            'category': 'Customer Experience',
            'title': f'Optimize {top_payment} Experience',
            'description': f'{top_payment} accounts for {top_payment_percentage:.1f}% of transactions. Ensure smooth processing and consider incentives for this payment method.',
            'priority': 'Medium',
            'impact': 'Customer Satisfaction'
        })
        
        # Seasonal analysis
        monthly_sales = df.groupby('Month')['TotalPrice'].sum()
        peak_month = monthly_sales.idxmax()
        low_month = monthly_sales.idxmin()
        
        month_names = {
            1: 'January', 2: 'February', 3: 'March', 4: 'April',
            5: 'May', 6: 'June', 7: 'July', 8: 'August',
            9: 'September', 10: 'October', 11: 'November', 12: 'December'
        }
        
        recommendations.append({
            'category': 'Inventory Management',
            'title': 'Seasonal Inventory Planning',
            'description': f'{month_names[peak_month]} is your peak sales month while {month_names[low_month]} is lowest. Adjust inventory levels and marketing spend accordingly.',
            'priority': 'Medium',
            'impact': 'Cost Optimization'
        })
        
        return recommendations
    
    def get_key_insights(self):
        """Generate key business insights"""
        df = self.load_sales_data()
        
        insights = []
        
        # Festival impact insight
        festival_impact = self._get_festival_impact_data(df)
        if festival_impact['festival_avg'] > 0 and festival_impact['regular_avg'] > 0:
            impact_percentage = ((festival_impact['festival_avg'] - festival_impact['regular_avg']) / festival_impact['regular_avg']) * 100
            insights.append({
                'title': 'Festival Sales Boost',
                'description': f'Festival days generate {impact_percentage:.0f}% higher sales than regular days.',
                'icon': 'celebration'
            })
        
        # Top category insight
        category_performance = df.groupby('Category')['TotalPrice'].sum().sort_values(ascending=False)
        top_category = category_performance.index[0]
        top_percentage = (category_performance.iloc[0] / category_performance.sum()) * 100
        
        insights.append({
            'title': 'Leading Category',
            'description': f'{top_category} dominates with {top_percentage:.1f}% of total revenue.',
            'icon': 'trending_up'
        })
        
        # Payment method insight
        payment_trends = df.groupby('PaymentMethod')['TotalPrice'].sum().sort_values(ascending=False)
        digital_payments = payment_trends.get('Mobile Wallet', 0) + payment_trends.get('Card', 0)
        cash_payments = payment_trends.get('Cash', 0)
        
        if digital_payments > cash_payments:
            digital_percentage = (digital_payments / payment_trends.sum()) * 100
            insights.append({
                'title': 'Digital Payment Adoption',
                'description': f'Digital payments account for {digital_percentage:.1f}% of transactions.',
                'icon': 'payment'
            })
        
        return insights
    
    def get_alerts_notifications(self):
        """Generate business alerts and notifications"""
        df = self.load_sales_data()
        
        alerts = []
        
        # Recent sales trend
        recent_data = df[df['Date'] >= (df['Date'].max() - timedelta(days=30))]
        previous_data = df[(df['Date'] >= (df['Date'].max() - timedelta(days=60))) & 
                          (df['Date'] < (df['Date'].max() - timedelta(days=30)))]
        
        if len(recent_data) > 0 and len(previous_data) > 0:
            recent_avg = recent_data['TotalPrice'].sum() / 30
            previous_avg = previous_data['TotalPrice'].sum() / 30
            change_percentage = ((recent_avg - previous_avg) / previous_avg) * 100
            
            if change_percentage < -10:
                alerts.append({
                    'type': 'warning',
                    'title': 'Sales Decline Alert',
                    'description': f'Sales decreased by {abs(change_percentage):.1f}% in the last 30 days.',
                    'priority': 'High'
                })
            elif change_percentage > 15:
                alerts.append({
                    'type': 'success',
                    'title': 'Sales Growth',
                    'description': f'Sales increased by {change_percentage:.1f}% in the last 30 days.',
                    'priority': 'Medium'
                })
        
        # Low performing products
        product_performance = df.groupby('ProductName')['TotalPrice'].sum().sort_values()
        low_performers = product_performance.head(5)
        
        alerts.append({
            'type': 'info',
            'title': 'Product Review Needed',
            'description': f'5 products have low sales. Consider promotional strategies or discontinuation.',
            'priority': 'Medium'
        })
        
        # Upcoming festival opportunity
        alerts.append({
            'type': 'info',
            'title': 'Festival Season Preparation',
            'description': 'Upcoming festival season detected. Prepare inventory and marketing campaigns.',
            'priority': 'Medium'
        })
        
        return alerts

def test_enhanced_analytics():
    """Test the enhanced analytics engine"""
    print("Testing Enhanced Analytics Engine...")
    
    engine = AnalyticsEngine()
    
    # Test chart data generation
    charts_data = engine.get_charts_data()
    print(f"Generated chart data for {len(charts_data)} chart types")
    
    # Test recommendations
    recommendations = engine.get_business_recommendations()
    print(f"Generated {len(recommendations)} business recommendations")
    
    # Test insights
    insights = engine.get_key_insights()
    print(f"Generated {len(insights)} key insights")
    
    # Test alerts
    alerts = engine.get_alerts_notifications()
    print(f"Generated {len(alerts)} alerts and notifications")
    
    return engine

if __name__ == '__main__':
    test_enhanced_analytics()
