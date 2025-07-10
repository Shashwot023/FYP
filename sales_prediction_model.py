import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from prophet import Prophet
import warnings
warnings.filterwarnings('ignore')

class SalesPredictionModel:
    def __init__(self, db_path='database.db'):
        self.db_path = db_path
        self.model = None
        self.df = None
        self.forcast = None

        # Define Nepali festivals and holidays based on the data
        self.holidays = pd.DataFrame({
            'holiday': [
                'Maha Shivaratri', 'Holi', 'Nepali New Year', 'Eid', 'Teej', 
                'Dashain', 'Tihar', 'Chhath Parva', 'Christmas'
                ],
            'ds': [
                # Approximate dates for 2024 (these would need to be updated yearly)
                '2024-03-08', '2024-03-25', '2024-04-14', '2024-04-10', '2024-09-06',
                '2024-10-15', '2024-11-01', '2024-11-07', '2024-12-25'
                ],
            'lower_window': [-1] * 9, # Holiday effect starts 1 day before
            'upper_window': [1] * 9, # Holiday effect lasts 1 day after
            })

        # Convert to datetime
        self.holidays['ds'] = pd.to_datetime(self.holidays['ds'])


    def load_sales_data(self):
        """Load and prepare sales data from the database"""
        try: 
            conn = sqlite3.connect(self.db_path)

            #Load sales data with proper date parsing
            query = """
            SELECT 
                Date,
                Year,
                Month,
                DayOfWeek,
                IsFestivalDay,
                FestivalName,
                ProductID,
                ProductName,
                Category,
                SubCategory,
                UnitPrice,
                QuantitySold,
                TotalPrice,
                StoreLocation,
                PaymentMethod
            FROM sales_table
            ORDER BY Date
            """

            df = pd.read_sql_query(query, conn)
            conn.close()

            # Convert Date column to datetime
            df['Date'] = pd.to_datetime(df['Date'])

            # Aggregate daily sales
            daily_sales = df.groupby('Date').agg({
                'TotalPrice': 'sum',
                'QuantitySold': 'sum',
                'IsFestivalDay': 'max',
                'FestivalName': 'first',
                }).reset_index()

            # Rename columns for prophet (requires 'ds' and 'y')
            daily_sales = daily_sales.rename(columns={
                'Date': 'ds',
                'TotalPrice': 'y'
                })

            # Add additional features
            daily_sales['day_of_week'] = daily_sales['ds'].dt.dayofweek
            daily_sales['month'] = daily_sales['ds'].dt.month
            daily_sales['year'] = daily_sales['ds'].dt.year
            daily_sales['is_weekend'] = daily_sales['day_of_week'].isin([5, 6]).astype(int)

            self.df = daily_sales
            return daily_sales

        except Exception as e:
            print(f"Error loading sales data: {e}")
            # Return sample data for testing
            return self._generate_sample_data()

    def _generate_sample_data(self):
        """Generate sample data based on the schema for testing"""
        print("Using sample data for testing...")
        
        # Create date range from 2022 to 2024
        start_date = datetime(2022, 1, 1)
        end_date = datetime(2024, 12, 31)
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        
        # Generate realistic sales data with trends and seasonality
        np.random.seed(42)
        base_sales = 50000
        trend = np.linspace(0, 20000, len(dates))  # Growing trend
        seasonal = 10000 * np.sin(2 * np.pi * np.arange(len(dates)) / 365.25)  # Yearly seasonality
        weekly = 5000 * np.sin(2 * np.pi * np.arange(len(dates)) / 7)  # Weekly seasonality
        noise = np.random.normal(0, 5000, len(dates))
        
        sales = base_sales + trend + seasonal + weekly + noise
        sales = np.maximum(sales, 10000)  # Ensure minimum sales
        
        # Add festival effects
        festival_boost = np.zeros(len(dates))
        for _, holiday in self.holidays.iterrows():
            holiday_date = holiday['ds']
            if start_date <= holiday_date <= end_date:
                # Find the index of the holiday date
                holiday_idx = (holiday_date - start_date).days
                if 0 <= holiday_idx < len(dates):
                    # Boost sales around festival days
                    for i in range(max(0, holiday_idx-1), min(len(dates), holiday_idx+2)):
                        festival_boost[i] += np.random.uniform(15000, 30000)
        
        sales += festival_boost
        
        df = pd.DataFrame({
            'ds': dates,
            'y': sales,
            'QuantitySold': sales / 100,  # Approximate quantity
            'IsFestivalDay': [1 if boost > 0 else 0 for boost in festival_boost],
            'day_of_week': dates.dayofweek,
            'month': dates.month,
            'year': dates.year,
            'is_weekend': dates.dayofweek.isin([5, 6]).astype(int)
        })
        
        self.df = df
        return df

    def train_model(self, df=None):
        """Train Prophet model with holiday effect and seasonality"""
        if df is None:
            df = self.df

        if df is None or df.empty:
            raise ValueError("No data available for training")

        # Initialize Prophet model with custom settings
        self.model = Prophet(
                yearly_seasonality=True,
                weekly_seasonality=True,
                daily_seasonality=False,
                holidays=self.holidays,
                seasonality_mode='multiplicative', # Better for sales data
                changepoint_prior_scale=0.05, # Flexibility for trend changes
                holidays_prior_scale=10.0, # Strong holiday effect
                seasonality_prior_scale=10.0 # String seasonal effect
                )

        # Add custom seasonalities
        self.model.add_seasonality(
                name='monthly',
                period=30.5,
                fourier_order=5
                )

        # Add refressors for additional features
        self.model.add_regressor('is_weekend')

        # Prepare data for Prophet
        train_data = df[['ds', 'y', 'is_weekend']].copy()

        # Fit the model
        print("Training Prophet Model...")
        self.model.fit(train_data)
        print("Model training completed!")

        return self.model

    def predict_future_sales(self, days_ahead=90):
        """Generate future sales prediction"""
        if self.model is None:
            raise ValueError("Model not trained. call train_model() first.")

        # Create future dataframe
        future = self.model.make_future_dataframe(periods=days_ahead)

        # Add regressor values for future dates
        future['is_weekend'] = future['ds'].dt.dayofweek.isin([5, 6]).astype(int)

        # Generate forecast
        print(f"Generateing {days_ahead}-day forecast...")
        self.forecast = self.model.predict(future)

        # Extract future prediction only
        future_forecast = self.forecast.tail(days_ahead).copy()

        # Ensure non-negative prediction only
        future_forecast['yhat'] = np.maximum(future_forecast['yhat'], 0)
        future_forecast['yhat_lower'] = np.maximum(future_forecast['yhat_lower'], 0)
        future_forecast['yhat_upper'] = np.maximum(future_forecast['yhat_upper'], 0)

        # Create result dataframe
        predictions_df = pd.DataFrame({
            'Date': future_forecast['ds'],
            'PredictedSales': future_forecast['yhat'].round(2),
            'ConfidenceLower': future_forecast['yhat_lower'].round(2),
            'ConfidenceUpper': future_forecast['yhat_upper'].round(2),
            'Trend': future_forecast['trend'].round(2),
            'Seasonal': (future_forecast['yearly'] + future_forecast['weekly']).round(2),
            'Holiday': future_forecast.get('holidays', 0).round(2)
            })

        return predictions_df

    def get_model_performance(self):
        """Calculate model performance metrics"""
        if self.forecast is None:
            return None
        
        # Get historical predictions
        historical = self.forecast[self.forecast['ds'] <= self.df['ds'].max()].copy()
        actual = self.df.merge(historical[['ds', 'yhat']], on='ds', how='inner')
        
        # Calculate metrics
        mae = np.mean(np.abs(actual['y'] - actual['yhat']))
        mape = np.mean(np.abs((actual['y'] - actual['yhat']) / actual['y'])) * 100
        rmse = np.sqrt(np.mean((actual['y'] - actual['yhat']) ** 2))
        
        return {
            'MAE': round(mae, 2),
            'MAPE': round(mape, 2),
            'RMSE': round(rmse, 2),
            'R2': round(np.corrcoef(actual['y'], actual['yhat'])[0, 1] ** 2, 3)
        }

    def get_trend_analysis(self):
        """Analyze sales trends and patterns"""
        if self.df is None:
            return None
        
        # Calculate growth rates
        monthly_sales = self.df.groupby([self.df['ds'].dt.year, self.df['ds'].dt.month])['y'].sum()
        monthly_growth = monthly_sales.pct_change().dropna()
        
        # Festival impact analysis
        festival_sales = self.df[self.df['IsFestivalDay'] == 1]['y'].mean()
        regular_sales = self.df[self.df['IsFestivalDay'] == 0]['y'].mean()
        festival_impact = ((festival_sales - regular_sales) / regular_sales) * 100
        
        # Weekend vs weekday analysis
        weekend_sales = self.df[self.df['is_weekend'] == 1]['y'].mean()
        weekday_sales = self.df[self.df['is_weekend'] == 0]['y'].mean()
        weekend_impact = ((weekend_sales - weekday_sales) / weekday_sales) * 100
        
        return {
            'average_monthly_growth': round(monthly_growth.mean() * 100, 2),
            'festival_impact_percent': round(festival_impact, 2),
            'weekend_impact_percent': round(weekend_impact, 2),
            'total_sales_period': round(self.df['y'].sum(), 2),
            'average_daily_sales': round(self.df['y'].mean(), 2),
            'peak_sales_day': self.df.loc[self.df['y'].idxmax(), 'ds'].strftime('%Y-%m-%d'),
            'peak_sales_amount': round(self.df['y'].max(), 2)
        }

    def get_category_predictions(self, days_ahead=30):
        """Generate category-wise predictions (simplified)"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get category distribution
            category_query = """
            SELECT Category, SUM(TotalPrice) as total_sales
            FROM sales_table
            GROUP BY Category
            ORDER BY total_sales DESC
            """
            
            category_data = pd.read_sql_query(category_query, conn)
            conn.close()
            
            # Calculate category percentages
            total_sales = category_data['total_sales'].sum()
            category_data['percentage'] = (category_data['total_sales'] / total_sales) * 100
            
            # Get overall predictions
            if self.forecast is None:
                return None
            
            future_predictions = self.forecast.tail(days_ahead)
            avg_daily_prediction = future_predictions['yhat'].mean()
            
            # Distribute predictions by category
            category_predictions = []
            for _, row in category_data.iterrows():
                category_predictions.append({
                    'category': row['Category'],
                    'predicted_daily_sales': round(avg_daily_prediction * row['percentage'] / 100, 2),
                    'percentage_share': round(row['percentage'], 2)
                })
            
            return category_predictions
            
        except Exception as e:
            print(f"Error generating category predictions: {e}")
            return None


def test_enhanced_model():
    """Test the enhanced prediction model"""
    print("Testing Enhanced Sales Prediction Model...")
    
    # Initialize model
    model = SalesPredictionModel()
    
    # Load data
    df = model.load_sales_data()
    print(f"Loaded {len(df)} days of sales data")
    print(f"Date range: {df['ds'].min()} to {df['ds'].max()}")
    print(f"Average daily sales: ${df['y'].mean():,.2f}")
    
    # Train model
    model.train_model(df)
    
    # Generate predictions
    predictions = model.predict_future_sales(days_ahead=90)
    print(f"\nGenerated {len(predictions)} days of predictions")
    print(f"Predicted average daily sales: ${predictions['PredictedSales'].mean():,.2f}")
    
    # Get performance metrics
    performance = model.get_model_performance()
    if performance:
        print(f"\nModel Performance:")
        for metric, value in performance.items():
            print(f"  {metric}: {value}")
    
    # Get trend analysis
    trends = model.get_trend_analysis()
    if trends:
        print(f"\nTrend Analysis:")
        for key, value in trends.items():
            print(f"  {key}: {value}")
    
    # Get category predictions
    category_preds = model.get_category_predictions()
    if category_preds:
        print(f"\nTop 5 Category Predictions:")
        for cat in category_preds[:5]:
            print(f"  {cat['category']}: ${cat['predicted_daily_sales']:,.2f}/day ({cat['percentage_share']:.1f}%)")
    
    return model, predictions

if __name__ == '__main__':
    test_enhanced_model()
