-- ============================================================================
-- INVENTRA - Database Seed File
-- ============================================================================
-- 
-- This file creates the database schema and populates it with sample data
-- for the Inventra inventory management system.
--
-- TABLES:
-- -------
-- 1. suppliers        - Vendor/supplier information
-- 2. inventory        - Product and stock information  
-- 3. weather_products - Weather-sensitive product mappings
--
-- RUN WITH:
--   sqlite3 inventra.db < seed.sql
--
-- ============================================================================

PRAGMA foreign_keys = ON;

-- ============================================================================
-- TABLE: suppliers
-- ============================================================================
-- Stores vendor information including lead times and reliability scores.
-- Lead time affects when reorders should be triggered.
-- Reliability affects risk calculations.

DROP TABLE IF EXISTS suppliers;

CREATE TABLE suppliers (
    supplier_id TEXT PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    city TEXT NOT NULL,
    lead_time_days INTEGER NOT NULL CHECK (lead_time_days >= 0),
    reliability_score REAL NOT NULL CHECK (reliability_score >= 0 AND reliability_score <= 1),
    min_order_qty INTEGER NOT NULL DEFAULT 10,
    contact_email TEXT,
    notes TEXT
);

-- Sample supplier data
INSERT INTO suppliers (supplier_id, supplier_name, city, lead_time_days, reliability_score, min_order_qty, notes) VALUES
    ('SUP_001', 'MonsoonWorks', 'Mumbai', 7, 0.95, 50, 'Specializes in rain gear. Fast delivery during monsoon season.'),
    ('SUP_002', 'RainShield', 'Delhi', 10, 0.88, 100, 'Large umbrella inventory. Competitive pricing.'),
    ('SUP_003', 'SunStyle Apparel', 'Bengaluru', 12, 0.92, 30, 'Summer wear specialist. Quality cotton products.'),
    ('SUP_004', 'WarmWeave', 'Kolkata', 14, 0.85, 20, 'Winter clothing. Good for seasonal prep.'),
    ('SUP_005', 'ChargeHub', 'Chennai', 5, 0.97, 50, 'Electronics accessories. Quick turnaround.'),
    ('SUP_006', 'HomeBasics', 'Hyderabad', 8, 0.90, 75, 'Home essentials. Reliable bulk orders.');


-- ============================================================================
-- TABLE: inventory
-- ============================================================================
-- Main inventory table with product details, stock levels, and economics.
-- 
-- KEY COLUMNS:
-- - units_on_hand: Current stock level
-- - reorder_point: Threshold for triggering reorder
-- - weather_sensitive: Flag for weather-affected products
-- - category: Product category for grouping

DROP TABLE IF EXISTS inventory;

CREATE TABLE inventory (
    sku_id TEXT PRIMARY KEY,
    sku_name TEXT NOT NULL,
    category TEXT NOT NULL,
    
    -- Stock levels
    units_on_hand INTEGER NOT NULL CHECK (units_on_hand >= 0),
    units_on_order INTEGER NOT NULL DEFAULT 0,
    reorder_point INTEGER NOT NULL CHECK (reorder_point >= 0),
    target_stock INTEGER NOT NULL,
    
    -- Economics
    unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
    unit_price REAL NOT NULL CHECK (unit_price >= 0),
    holding_cost_per_day REAL NOT NULL DEFAULT 0.5,
    
    -- Supplier relationship
    supplier_id TEXT NOT NULL,
    
    -- Weather sensitivity (1 = sensitive, 0 = not)
    weather_sensitive INTEGER NOT NULL DEFAULT 0,
    
    -- Sales metrics
    avg_daily_sales REAL NOT NULL DEFAULT 0,
    sales_last_7d INTEGER NOT NULL DEFAULT 0,
    sales_last_30d INTEGER NOT NULL DEFAULT 0,
    
    -- Metadata
    last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,
    
    FOREIGN KEY (supplier_id) REFERENCES suppliers(supplier_id)
);

-- Create indexes for common queries
CREATE INDEX idx_inventory_category ON inventory(category);
CREATE INDEX idx_inventory_supplier ON inventory(supplier_id);
CREATE INDEX idx_inventory_low_stock ON inventory(units_on_hand, reorder_point);

-- ============================================================================
-- INVENTORY DATA - Weather-Sensitive Products
-- ============================================================================

-- UMBRELLAS (weather sensitive - rain increases demand)
INSERT INTO inventory (sku_id, sku_name, category, units_on_hand, units_on_order, reorder_point, target_stock, unit_cost, unit_price, supplier_id, weather_sensitive, avg_daily_sales, sales_last_7d, sales_last_30d, notes) VALUES
    ('UMB_001', 'Classic Umbrella 21in', 'Umbrellas', 45, 0, 100, 300, 120.00, 350.00, 'SUP_001', 1, 25.0, 175, 750, 'Best seller during monsoon. Stock up by May.'),
    ('UMB_002', 'Compact Fold Umbrella', 'Umbrellas', 120, 50, 80, 250, 85.00, 220.00, 'SUP_002', 1, 15.0, 105, 450, 'Popular for office commuters.'),
    ('UMB_003', 'Windproof Golf Umbrella', 'Umbrellas', 30, 0, 40, 120, 250.00, 650.00, 'SUP_001', 1, 5.0, 35, 150, 'Premium segment. Lower volume.'),
    ('UMB_004', 'Kids Cartoon Umbrella', 'Umbrellas', 15, 100, 60, 180, 95.00, 280.00, 'SUP_002', 1, 12.0, 84, 360, 'School season + monsoon peak.');

-- RAINCOATS (weather sensitive - rain increases demand)
INSERT INTO inventory (sku_id, sku_name, category, units_on_hand, units_on_order, reorder_point, target_stock, unit_cost, unit_price, supplier_id, weather_sensitive, avg_daily_sales, sales_last_7d, sales_last_30d, notes) VALUES
    ('RNC_001', 'Lightweight Raincoat', 'Raincoats', 80, 0, 75, 200, 220.00, 550.00, 'SUP_001', 1, 8.0, 56, 240, 'Quick dry material. Good reviews.'),
    ('RNC_002', 'Hooded Raincoat', 'Raincoats', 25, 50, 50, 150, 280.00, 720.00, 'SUP_001', 1, 6.0, 42, 180, 'Premium range. Hood is key feature.'),
    ('RNC_003', 'Kids Raincoat Set', 'Raincoats', 40, 0, 40, 120, 180.00, 450.00, 'SUP_002', 1, 5.0, 35, 150, 'Includes boots. Popular gift item.');

-- SUMMER WEAR (weather sensitive - heat increases demand)
INSERT INTO inventory (sku_id, sku_name, category, units_on_hand, units_on_order, reorder_point, target_stock, unit_cost, unit_price, supplier_id, weather_sensitive, avg_daily_sales, sales_last_7d, sales_last_30d, notes) VALUES
    ('SUM_001', 'Cotton T-Shirt', 'Summer Wear', 200, 0, 150, 400, 180.00, 450.00, 'SUP_003', 1, 20.0, 140, 600, 'Breathable cotton. Multiple colors.'),
    ('SUM_002', 'Linen Shorts', 'Summer Wear', 90, 100, 80, 220, 220.00, 580.00, 'SUP_003', 1, 12.0, 84, 360, 'Light and comfortable for heat.'),
    ('SUM_003', 'Summer Dress', 'Summer Wear', 60, 0, 50, 150, 350.00, 850.00, 'SUP_003', 1, 8.0, 56, 240, 'Floral patterns trending.');

-- WINTER WEAR (weather sensitive - cold increases demand)
INSERT INTO inventory (sku_id, sku_name, category, units_on_hand, units_on_order, reorder_point, target_stock, unit_cost, unit_price, supplier_id, weather_sensitive, avg_daily_sales, sales_last_7d, sales_last_30d, notes) VALUES
    ('WIN_001', 'Wool Sweater', 'Winter Wear', 150, 0, 100, 300, 450.00, 1200.00, 'SUP_004', 1, 10.0, 70, 300, 'Premium wool. Nov-Feb peak.'),
    ('WIN_002', 'Thermal Jacket', 'Winter Wear', 80, 50, 60, 180, 800.00, 2000.00, 'SUP_004', 1, 6.0, 42, 180, 'High margin item.'),
    ('WIN_003', 'Fleece Hoodie', 'Winter Wear', 110, 0, 80, 200, 350.00, 850.00, 'SUP_004', 1, 8.0, 56, 240, 'Casual winter staple.');

-- ============================================================================
-- INVENTORY DATA - Non-Weather-Sensitive Products
-- ============================================================================

-- ELECTRONICS (not weather sensitive)
INSERT INTO inventory (sku_id, sku_name, category, units_on_hand, units_on_order, reorder_point, target_stock, unit_cost, unit_price, supplier_id, weather_sensitive, avg_daily_sales, sales_last_7d, sales_last_30d, notes) VALUES
    ('ELC_001', 'USB-C Cable 1m', 'Electronics', 300, 0, 150, 500, 80.00, 250.00, 'SUP_005', 0, 25.0, 175, 750, 'High volume. Steady demand.'),
    ('ELC_002', 'Power Bank 10000mAh', 'Electronics', 120, 100, 100, 300, 450.00, 1100.00, 'SUP_005', 0, 12.0, 84, 360, 'Essential travel item.'),
    ('ELC_003', 'Wireless Earbuds', 'Electronics', 75, 50, 60, 180, 600.00, 1500.00, 'SUP_005', 0, 8.0, 56, 240, 'Trending product.');

-- HOME ESSENTIALS (not weather sensitive)
INSERT INTO inventory (sku_id, sku_name, category, units_on_hand, units_on_order, reorder_point, target_stock, unit_cost, unit_price, supplier_id, weather_sensitive, avg_daily_sales, sales_last_7d, sales_last_30d, notes) VALUES
    ('HOM_001', 'Storage Box Set', 'Home Essentials', 180, 0, 100, 300, 150.00, 400.00, 'SUP_006', 0, 10.0, 70, 300, 'Organizing essentials.'),
    ('HOM_002', 'Kitchen Towels Pack', 'Home Essentials', 250, 0, 150, 400, 80.00, 200.00, 'SUP_006', 0, 15.0, 105, 450, 'Consumable - repeat purchases.'),
    ('HOM_003', 'Water Bottle 1L', 'Home Essentials', 140, 50, 100, 250, 120.00, 320.00, 'SUP_006', 0, 12.0, 84, 360, 'BPA-free. Good margins.');


-- ============================================================================
-- TABLE: weather_products
-- ============================================================================
-- Maps weather conditions to affected product categories.
-- Used by the Weather Agent to determine impact on inventory.

DROP TABLE IF EXISTS weather_products;

CREATE TABLE weather_products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    weather_condition TEXT NOT NULL,
    affected_category TEXT NOT NULL,
    demand_multiplier REAL NOT NULL DEFAULT 1.0,
    notes TEXT
);

-- Weather condition mappings
INSERT INTO weather_products (weather_condition, affected_category, demand_multiplier, notes) VALUES
    -- Rain conditions
    ('rain', 'Umbrellas', 2.5, 'Heavy demand spike during rain'),
    ('rain', 'Raincoats', 2.0, 'Strong demand during rain'),
    ('heavy_rain', 'Umbrellas', 3.0, 'Very high demand during heavy rain'),
    ('heavy_rain', 'Raincoats', 2.5, 'High demand during heavy rain'),
    
    -- Heat conditions
    ('hot', 'Summer Wear', 1.8, 'Increased demand in hot weather'),
    ('very_hot', 'Summer Wear', 2.2, 'High demand during heat waves'),
    ('hot', 'Home Essentials', 1.2, 'Slight increase (water bottles)'),
    
    -- Cold conditions
    ('cold', 'Winter Wear', 1.8, 'Increased demand in cold weather'),
    ('very_cold', 'Winter Wear', 2.5, 'High demand during cold waves'),
    
    -- Normal conditions (baseline)
    ('clear', 'Umbrellas', 0.5, 'Low demand on clear days'),
    ('clear', 'Summer Wear', 1.2, 'Slight increase on sunny days');


-- ============================================================================
-- VERIFICATION QUERIES (for testing)
-- ============================================================================
-- Uncomment these to verify data after running the seed file:
--
-- SELECT 'Suppliers:' as table_name, COUNT(*) as count FROM suppliers;
-- SELECT 'Inventory:' as table_name, COUNT(*) as count FROM inventory;
-- SELECT 'Weather Products:' as table_name, COUNT(*) as count FROM weather_products;
--
-- SELECT category, COUNT(*) as products, SUM(units_on_hand) as total_stock 
-- FROM inventory GROUP BY category;
