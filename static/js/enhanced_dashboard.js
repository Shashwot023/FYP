/**
 * Enhanced Dashboard JavaScript
 * Handles all chart rendering, data fetching, and interactions
 */

class DashboardManager {
    constructor() {
        this.charts = {};
        this.data = {};
        this.refreshInterval = 300000; // 5 minutes
        this.init();
    }

    async init() {
        console.log('Initializing Enhanced Dashboard...');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Load initial data
        await this.loadAllData();
        
        // Render all components
        this.renderAll();
        
        // Set up auto-refresh
        this.setupAutoRefresh();
        
        console.log('Dashboard initialized successfully');
    }

    setupEventListeners() {
        // Window resize handler
        window.addEventListener('resize', this.debounce(() => {
            this.resizeCharts();
        }, 250));
    }

    async loadAllData() {
        try {
            // Load data from multiple endpoints
            const [metricsData, chartsData, predictionsData, recommendationsData, inventoryData] = await Promise.all([
                this.fetchData('/api/dashboard/metrics'),
                this.fetchData('/api/dashboard/charts'),
                this.fetchData('/api/dashboard/predictions'),
                this.fetchData('/api/dashboard/recommendations'),
                this.fetchData('/api/inventory/summary')
            ]);

            this.data = {
                metrics: metricsData,
                charts: chartsData,
                predictions: predictionsData,
                recommendations: recommendationsData,
                inventory: inventoryData
            };

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showErrorState();
        }
    }

    async fetchData(endpoint) {
        try {
            const response = await fetch(endpoint);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error fetching data from ${endpoint}:`, error);
            return this.getMockData(endpoint);
        }
    }

    getMockData(endpoint) {
        const mockData = {
            '/api/dashboard/metrics': {
                totalRevenue: 298612065.81,
                revenueChange: 15.2,
                customersAcquired: 8855,
                customersChange: 12.5,
                inventoryValue: 2847500,
                inventoryChange: -2.1,
                growthRate: 18.7,
                growthChange: 5.3
            },
            '/api/dashboard/charts': {
                productPerformance: {
                    products: ['Basmati Rice 5kg', 'Smartphone', 'LED TV 32-inch'],
                    salesVolume: [15000, 8000, 3000],
                    profitMargin: [25, 35, 40]
                },
                customerSegmentation: {
                    labels: ['Mobile Wallet', 'Cash', 'Card'],
                    values: [33.6, 33.5, 32.9]
                },
                seasonalTrends: {
                    months: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
                    categories: {
                        'Electronics': [1200000, 1100000, 1300000, 1250000, 1400000, 1350000, 1500000, 1450000, 1600000, 1550000, 1700000, 1650000],
                        'Groceries': [800000, 850000, 900000, 950000, 1000000, 1050000, 1100000, 1150000, 1200000, 1250000, 1300000, 1350000]
                    }
                }
            },
            '/api/dashboard/predictions': {
                dates: this.generateDateRange(90),
                predictions: this.generateRandomData(90, 500000, 50000),
                confidenceUpper: this.generateRandomData(90, 600000, 60000),
                confidenceLower: this.generateRandomData(90, 400000, 40000)
            },
            '/api/dashboard/recommendations': [
                {
                    category: 'Sales Optimization',
                    title: 'Focus on Electronics during Festival Season',
                    description: 'Electronics show 40% higher sales during Dashain and Tihar. Increase inventory and marketing.',
                    priority: 'High',
                    impact: 'Revenue Growth'
                }
            ],
            '/api/inventory/summary': {
                total_items: 34492,
                total_value: 14131237855,
                stock_health_percentage: 90.1,
                critical_items: 3392,
                avg_days_remaining: 45
            }
        };
        
        return mockData[endpoint] || {};
    }

    generateDateRange(days) {
        const dates = [];
        const startDate = new Date();
        for (let i = 0; i < days; i++) {
            const date = new Date(startDate);
            date.setDate(startDate.getDate() + i);
            dates.push(date.toISOString().split('T')[0]);
        }
        return dates;
    }

    generateRandomData(length, base, variance) {
        return Array.from({ length }, () => 
            base + (Math.random() - 0.5) * variance * 2
        );
    }

    renderAll() {
        this.renderMetrics();
        this.renderCharts();
        this.renderBusinessIntelligence();
        this.updateLastUpdated();
    }

    renderMetrics() {
        const metrics = this.data.metrics || this.getMockData('/api/dashboard/metrics');
        const inventory = this.data.inventory || {};
        
        // Total Revenue
        this.updateMetric('total-revenue', this.formatCurrency(metrics.totalRevenue));
        this.updateMetricChange('revenue-change', metrics.revenueChange, '%');
        
        // Customers Acquired
        this.updateMetric('customers-acquired', this.formatNumber(metrics.customersAcquired));
        this.updateMetricChange('customers-change', metrics.customersChange, '%');
        
        // Inventory Value
        this.updateMetric('inventory-value', this.formatCurrency(metrics.inventoryValue));
        this.updateMetricChange('inventory-change', metrics.inventoryChange, '%');
        
        // Growth Rate
        this.updateMetric('growth-rate', `${metrics.growthRate}%`);
        this.updateMetricChange('growth-change', metrics.growthChange, 'pts');
        
        // Inventory Metrics
        if (inventory.total_items) {
            this.updateMetric('total-inventory-items', this.formatNumber(inventory.total_items));
            this.updateMetric('stock-health', `${inventory.stock_health_percentage}%`);
            this.updateMetric('critical-items', this.formatNumber(inventory.critical_items));
            this.updateMetric('avg-days-remaining', `${inventory.avg_days_remaining} days`);
            
            // Update inventory metric changes (simulated)
            this.updateMetricChange('inventory-items-change', 2.3, '%');
            this.updateMetricChange('stock-health-change', 1.5, 'pts');
            this.updateMetricChange('critical-items-change', -5.2, '%');
            this.updateMetricChange('days-remaining-change', 0.8, 'days');
        }
    }

    updateMetric(elementId, value) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = value;
        }
    }

    updateMetricChange(elementId, change, unit) {
        const element = document.getElementById(elementId);
        if (element) {
            const isPositive = change > 0;
            const isNegative = change < 0;
            
            element.className = `metric-change ${isPositive ? 'positive' : isNegative ? 'negative' : 'neutral'}`;
            
            const icon = element.querySelector('i');
            if (icon) {
                icon.className = `fas fa-arrow-${isPositive ? 'up' : isNegative ? 'down' : 'right'}`;
            }
            
            const span = element.querySelector('span');
            if (span) {
                span.textContent = `${Math.abs(change).toFixed(1)}${unit} from last month`;
            }
        }
    }

    renderCharts() {
        this.renderSalesForecastChart();
        this.renderProductPerformanceChart();
        this.renderCustomerSegmentationChart();
        this.renderSeasonalTrendsChart();
        this.renderInventoryOptimizationChart();
        
        // New inventory charts
        this.renderStockStatusChart();
        this.renderAbcClassificationChart();
        this.renderCategoryValueChart();
        this.renderStorePerformanceChart();
    }

    renderSalesForecastChart() {
        const container = document.getElementById('sales-forecast-chart');
        if (!container) return;

        const predictions = this.data.predictions || this.getMockData('/api/dashboard/predictions');
	const historicalTrace = {
            x: predictions.dates.slice(0, 30),
            y: predictions.predictions.slice(0, 30),
            type: 'scatter',
            mode: 'lines',
            name: 'Historical Sales',
            line: { color: '#2E7D32', width: 3 }
        };

        const predictedTrace = {
            x: predictions.dates.slice(30),
            y: predictions.predictions.slice(30),
            type: 'scatter',
            mode: 'lines',
            name: 'Predicted Sales',
            line: { color: '#1976D2', width: 3, dash: 'dash' }
        };

        const confidenceTrace = {
            x: [...predictions.dates.slice(30), ...predictions.dates.slice(30).reverse()],
            y: [...predictions.confidenceUpper.slice(30), ...predictions.confidenceLower.slice(30).reverse()],
            fill: 'toself',
            fillcolor: 'rgba(25, 118, 210, 0.2)',
            line: { color: 'transparent' },
            name: 'Confidence Interval',
            showlegend: false
        };

        const layout = {
            title: '',
            xaxis: {
                title: 'Date',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0'
            },
            yaxis: {
                title: 'Sales (NPR)',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0',
                tickformat: '.2s'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: { family: 'Inter, sans-serif', size: 12, color: '#212121' },
            margin: { l: 60, r: 20, t: 20, b: 60 },
            legend: {
                x: 0,
                y: 1,
                bgcolor: 'rgba(255,255,255,0.8)'
            }
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        try {
            Plotly.newPlot(container, [confidenceTrace, historicalTrace, predictedTrace], layout, config);
            this.charts.salesForecast = container;
        } catch (error) {
            console.error('Error rendering sales forecast chart:', error);
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">Error loading sales forecast</div>';
        }
    }

    renderProductPerformanceChart() {
        const container = document.getElementById('product-performance-chart');
        if (!container) return;

        const data = this.data.charts?.productPerformance || this.getMockData('/api/dashboard/charts').productPerformance;

        // Validate data
        if (!data || !data.products || !data.salesVolume || !data.profitMargin) {
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">No product performance data available</div>';
            return;
        }

        const trace = {
            x: data.salesVolume,
            y: data.profitMargin,
            mode: 'markers+text',
            type: 'scatter',
            text: data.products,
            textposition: 'top center',
            marker: {
                size: data.salesVolume.map(v => Math.max(10, v / 1000)),
                color: data.profitMargin,
                colorscale: 'Viridis',
                showscale: true,
                colorbar: {
                    title: 'Profit Margin (%)',
                    titleside: 'right'
                }
            },
            hovertemplate: '<b>%{text}</b><br>Sales Volume: %{x}<br>Profit Margin: %{y}%<extra></extra>'
        };

        const layout = {
            title: '',
            xaxis: {
                title: 'Sales Volume',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0'
            },
            yaxis: {
                title: 'Profit Margin (%)',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: { family: 'Inter, sans-serif', size: 12, color: '#212121' },
            margin: { l: 60, r: 80, t: 20, b: 60 }
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        try {
            Plotly.newPlot(container, [trace], layout, config);
            this.charts.productPerformance = container;
        } catch (error) {
            console.error('Error rendering product performance chart:', error);
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">Error loading product performance chart</div>';
        }
    }

    renderCustomerSegmentationChart() {
        const container = document.getElementById('customer-segmentation-chart');
        if (!container) return;

        const data = this.data.charts?.customerSegmentation || this.getMockData('/api/dashboard/charts').customerSegmentation;

        const trace = {
            labels: data.labels,
            values: data.values,
            type: 'pie',
            hole: 0.4,
            marker: {
                colors: ['#FF6F00', '#2E7D32', '#1976D2'],
                line: { color: 'white', width: 2 }
            },
            textinfo: 'label+percent',
            textposition: 'outside',
            hovertemplate: '<b>%{label}</b><br>Share: %{percent}<extra></extra>'
        };

        const layout = {
            title: '',
            font: { family: 'Inter, sans-serif', size: 12, color: '#212121' },
            margin: { l: 20, r: 20, t: 20, b: 20 },
            paper_bgcolor: 'white',
            showlegend: false
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        try {
            Plotly.newPlot(container, [trace], layout, config);
            this.charts.customerSegmentation = container;
        } catch (error) {
            console.error('Error rendering customer segmentation chart:', error);
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">Error loading customer segmentation chart</div>';
        }
    }

    renderSeasonalTrendsChart() {
        const container = document.getElementById('seasonal-trends-chart');
        if (!container) return;

        const data = this.data.charts?.seasonalTrends || this.getMockData('/api/dashboard/charts').seasonalTrends;

        const traces = Object.keys(data).map((category, index) => ({
            x: data[category].x,
            y: data[category].y,
            type: 'scatter',
            mode: 'lines+markers',
            name: category,
            line: { width: 3 },
            marker: { size: 8 }
        }));

        const layout = {
            title: '',
            xaxis: {
                title: 'Month',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0'
            },
            yaxis: {
                title: 'Sales (NPR)',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0',
                tickformat: '.2s'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: { family: 'Inter, sans-serif', size: 12, color: '#212121' },
            margin: { l: 80, r: 20, t: 20, b: 60 },
            legend: {
                x: 0,
                y: 1,
                bgcolor: 'rgba(255,255,255,0.8)'
            }
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        try {
            Plotly.newPlot(container, traces, layout, config);
            this.charts.seasonalTrends = container;
        } catch (error) {
            console.error('Error rendering seasonal trends chart:', error);
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">Error loading seasonal trends chart</div>';
        }
    }

    renderInventoryOptimizationChart() {
        const container = document.getElementById('inventory-optimization-chart');
        if (!container) return;

        // Mock ABC analysis data
        const data = {
            categories: ['A-Class', 'B-Class', 'C-Class'],
            values: [5, 7, 4]
        };

        const trace = {
            x: data.categories,
            y: data.values,
            type: 'bar',
            marker: {
                color: ['#2E7D32', '#FF6F00', '#F44336'],
                line: { color: 'white', width: 2 }
            },
            text: data.values,
            textposition: 'auto',
            hovertemplate: '<b>%{x}</b><br>Items: %{y}<extra></extra>'
        };

        const layout = {
            title: '',
            xaxis: {
                title: 'ABC Category',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0'
            },
            yaxis: {
                title: 'Number of Items',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: { family: 'Inter, sans-serif', size: 12, color: '#212121' },
            margin: { l: 60, r: 20, t: 20, b: 60 }
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        Plotly.newPlot(container, [trace], layout, config);
        this.charts.inventoryOptimization = container;
    }

    renderBusinessIntelligence() {
        this.renderRecommendations();
        this.renderInsights();
        this.renderAlerts();
        this.renderReorderRecommendations();
    }

    renderRecommendations() {
        const container = document.getElementById('recommendations-content');
        if (!container) return;

        const recommendations = this.data.recommendations || this.getMockData('/api/dashboard/recommendations');

        if (!recommendations || recommendations.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">No recommendations available</div>';
            return;
        }

        const html = recommendations.map(rec => `
            <div class="recommendation-item">
                <div class="recommendation-header">
                    <div class="recommendation-category">${rec.category}</div>
                    <div class="priority-badge ${rec.priority.toLowerCase()}">${rec.priority}</div>
                </div>
                <div class="recommendation-title">${rec.title}</div>
                <div class="recommendation-description">${rec.description}</div>
                <div class="recommendation-impact">Impact: ${rec.impact}</div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    renderInsights() {
        const container = document.getElementById('insights-content');
        if (!container) return;

        const insights = [
            {
                title: 'Peak Sales Period',
                description: 'October and November show 35% higher sales due to festival season',
                type: 'trend'
            },
            {
                title: 'Top Performing Category',
                description: 'Electronics contribute 42% of total revenue',
                type: 'performance'
            },
            {
                title: 'Payment Preference',
                description: 'Mobile wallet usage increased by 28% this quarter',
                type: 'behavior'
            }
        ];

        const html = insights.map(insight => `
            <div class="insight-item">
                <div class="insight-icon ${insight.type}">
                    <i class="fas fa-${insight.type === 'trend' ? 'chart-line' : insight.type === 'performance' ? 'trophy' : 'users'}"></i>
                </div>
                <div class="insight-content">
                    <div class="insight-title">${insight.title}</div>
                    <div class="insight-description">${insight.description}</div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    renderAlerts() {
        const container = document.getElementById('alerts-content');
        if (!container) return;

        const alerts = [
            {
                title: 'Low Stock Alert',
                description: '15 items are below reorder point',
                severity: 'warning',
                time: '2 hours ago'
            },
            {
                title: 'Revenue Milestone',
                description: 'Monthly target achieved 5 days early',
                severity: 'success',
                time: '1 day ago'
            },
            {
                title: 'System Update',
                description: 'Dashboard updated with new features',
                severity: 'info',
                time: '3 days ago'
            }
        ];

        const html = alerts.map(alert => `
            <div class="alert-item ${alert.severity}">
                <div class="alert-icon">
                    <i class="fas fa-${alert.severity === 'warning' ? 'exclamation-triangle' : alert.severity === 'success' ? 'check-circle' : 'info-circle'}"></i>
                </div>
                <div class="alert-content">
                    <div class="alert-title">${alert.title}</div>
                    <div class="alert-description">${alert.description}</div>
                    <div class="alert-time">${alert.time}</div>
                </div>
            </div>
        `).join('');

        container.innerHTML = html;
    }

    // Inventory Chart Methods
    
    renderStockStatusChart() {
        const container = document.getElementById('stock-status-chart');
        if (!container) return;

        const data = this.data.charts?.stock_status || {
            labels: ['Normal', 'Low Stock', 'Out of Stock', 'Overstock'],
            values: [31062, 3175, 217, 38]
        };

        const trace = {
            labels: data.labels,
            values: data.values,
            type: 'pie',
            hole: 0.4,
            marker: {
                colors: ['#2E7D32', '#FF6F00', '#F44336', '#9C27B0'],
                line: { color: 'white', width: 2 }
            },
            textinfo: 'label+percent',
            textposition: 'outside',
            hovertemplate: '<b>%{label}</b><br>Items: %{value}<br>Share: %{percent}<extra></extra>'
        };

        const layout = {
            title: '',
            font: { family: 'Inter, sans-serif', size: 12, color: '#212121' },
            margin: { l: 20, r: 20, t: 20, b: 20 },
            paper_bgcolor: 'white',
            showlegend: false
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        try {
            Plotly.newPlot(container, [trace], layout, config);
            this.charts.stockStatus = container;
        } catch (error) {
            console.error('Error rendering stock status chart:', error);
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">Error loading stock status chart</div>';
        }
    }

    renderAbcClassificationChart() {
        const container = document.getElementById('abc-classification-chart');
        if (!container) return;

        const data = this.data.charts?.abc_classification || {
            labels: ['A-Class', 'B-Class', 'C-Class'],
            values: [12, 3400, 31080]
        };

        const trace = {
            x: data.labels,
            y: data.values,
            type: 'bar',
            marker: {
                color: ['#2E7D32', '#FF6F00', '#F44336'],
                line: { color: 'white', width: 2 }
            },
            text: data.values,
            textposition: 'auto',
            hovertemplate: '<b>%{x}</b><br>Items: %{y}<extra></extra>'
        };

        const layout = {
            title: '',
            xaxis: {
                title: 'ABC Classification',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0'
            },
            yaxis: {
                title: 'Number of Items',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: { family: 'Inter, sans-serif', size: 12, color: '#212121' },
            margin: { l: 60, r: 20, t: 20, b: 60 }
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        try {
            Plotly.newPlot(container, [trace], layout, config);
            this.charts.abcClassification = container;
        } catch (error) {
            console.error('Error rendering ABC classification chart:', error);
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">Error loading ABC classification chart</div>';
        }
    }

    renderCategoryValueChart() {
        const container = document.getElementById('category-value-chart');
        if (!container) return;

        const data = this.data.charts?.category_values || {
            categories: ['Electronics', 'Groceries', 'Clothing', 'Jewelry'],
            values: [4500000000, 3200000000, 2800000000, 3600000000]
        };

        const trace = {
            x: data.categories,
            y: data.values,
            type: 'bar',
            marker: {
                color: ['#1976D2', '#2E7D32', '#FF6F00', '#9C27B0'],
                line: { color: 'white', width: 2 }
            },
            text: data.values.map(v => this.formatCurrency(v)),
            textposition: 'auto',
            hovertemplate: '<b>%{x}</b><br>Value: %{text}<extra></extra>'
        };

        const layout = {
            title: '',
            xaxis: {
                title: 'Category',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0'
            },
            yaxis: {
                title: 'Inventory Value (NPR)',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0',
                tickformat: '.2s'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: { family: 'Inter, sans-serif', size: 12, color: '#212121' },
            margin: { l: 80, r: 20, t: 20, b: 60 }
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        try {
            Plotly.newPlot(container, [trace], layout, config);
            this.charts.categoryValue = container;
        } catch (error) {
            console.error('Error rendering category value chart:', error);
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">Error loading category value chart</div>';
        }
    }

    renderStorePerformanceChart() {
        const container = document.getElementById('store-performance-chart');
        if (!container) return;

        const data = this.data.charts?.store_performance || {
            stores: ['Kathmandu', 'Pokhara', 'Biratnagar', 'Janakpur'],
            values: [3509660327, 3542065037, 3543950590, 3535561899]
        };

        const trace = {
            x: data.stores,
            y: data.values,
            type: 'bar',
            marker: {
                color: ['#1976D2', '#2E7D32', '#FF6F00', '#9C27B0'],
                line: { color: 'white', width: 2 }
            },
            text: data.values.map(v => this.formatCurrency(v)),
            textposition: 'auto',
            hovertemplate: '<b>%{x}</b><br>Value: %{text}<extra></extra>'
        };

        const layout = {
            title: '',
            xaxis: {
                title: 'Store Location',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0'
            },
            yaxis: {
                title: 'Inventory Value (NPR)',
                gridcolor: '#E0E0E0',
                linecolor: '#E0E0E0',
                tickformat: '.2s'
            },
            plot_bgcolor: 'white',
            paper_bgcolor: 'white',
            font: { family: 'Inter, sans-serif', size: 12, color: '#212121' },
            margin: { l: 80, r: 20, t: 20, b: 60 }
        };

        const config = {
            responsive: true,
            displayModeBar: false
        };

        try {
            Plotly.newPlot(container, [trace], layout, config);
            this.charts.storePerformance = container;
        } catch (error) {
            console.error('Error rendering store performance chart:', error);
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">Error loading store performance chart</div>';
        }
    }

    async renderReorderRecommendations() {
        const container = document.getElementById('reorder-recommendations');
        if (!container) return;

        try {
            const recommendations = await this.fetchData('/api/inventory/reorder-recommendations');
            
            if (!recommendations || recommendations.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">No reorder recommendations available</div>';
                return;
            }

            const html = recommendations.slice(0, 10).map((rec, index) => `
                <div class="recommendation-item" style="border-left: 4px solid ${this.getUrgencyColor(rec.UrgencyScore)};">
                    <div class="recommendation-header">
                        <div class="recommendation-title">${rec.ProductName}</div>
                        <div class="urgency-badge ${this.getUrgencyClass(rec.UrgencyScore)}">${rec.UrgencyScore.toFixed(0)}% Urgent</div>
                    </div>
                    <div class="recommendation-details">
                        <div class="detail-item">
                            <strong>Store:</strong> ${rec.StoreLocation}
                        </div>
                        <div class="detail-item">
                            <strong>Current Stock:</strong> ${rec.CurrentStock} units
                        </div>
                        <div class="detail-item">
                            <strong>Recommended Order:</strong> ${rec.RecommendedQuantity} units
                        </div>
                        <div class="detail-item">
                            <strong>Estimated Cost:</strong> NPR ${rec.EstimatedCost.toLocaleString()}
                        </div>
                        <div class="detail-item">
                            <strong>Supplier:</strong> ${rec.Supplier}
                        </div>
                    </div>
                </div>
            `).join('');

            container.innerHTML = html;

        } catch (error) {
            console.error('Error rendering reorder recommendations:', error);
            container.innerHTML = '<div style="text-align: center; padding: 50px; color: #666;">Error loading reorder recommendations</div>';
        }
    }

    getUrgencyColor(score) {
        if (score >= 80) return '#F44336';
        if (score >= 60) return '#FF6F00';
        return '#2E7D32';
    }

    getUrgencyClass(score) {
        if (score >= 80) return 'high';
        if (score >= 60) return 'medium';
        return 'low';
    }

    setupAutoRefresh() {
        setInterval(() => {
            this.loadAllData().then(() => {
                this.renderAll();
            });
        }, this.refreshInterval);
    }

    resizeCharts() {
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof Plotly !== 'undefined') {
                Plotly.Plots.resize(chart);
            }
        });
    }

    updateLastUpdated() {
        const element = document.querySelector('.last-updated span');
        if (element) {
            element.textContent = new Date().toLocaleString();
        }
    }

    showErrorState() {
        console.error('Dashboard is in error state');
        // Could implement error UI here
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    formatCurrency(value) {
        if (value >= 1e9) {
            return `$${(value / 1e9).toFixed(1)}B`;
        } else if (value >= 1e6) {
            return `$${(value / 1e6).toFixed(1)}M`;
        } else if (value >= 1e3) {
            return `$${(value / 1e3).toFixed(1)}K`;
        }
        return `$${value.toFixed(0)}`;
    }

    formatNumber(value) {
        if (value >= 1e6) {
            return `${(value / 1e6).toFixed(1)}M`;
        } else if (value >= 1e3) {
            return `${(value / 1e3).toFixed(1)}K`;
        }
        return value.toLocaleString();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardManager();
});


