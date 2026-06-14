IF DB_ID('Rossmann') IS NULL
    CREATE DATABASE Rossmann;
GO

USE Rossmann;
GO

IF OBJECT_ID('dbo.Store', 'U') IS NOT NULL DROP TABLE dbo.Store;
CREATE TABLE dbo.Store (
    Store INT NOT NULL PRIMARY KEY,
    StoreType VARCHAR(10) NULL,
    Assortment VARCHAR(10) NULL,
    CompetitionDistance FLOAT NULL,
    CompetitionOpenSinceMonth INT NULL,
    CompetitionOpenSinceYear INT NULL,
    Promo2 INT NULL,
    Promo2SinceWeek INT NULL,
    Promo2SinceYear INT NULL,
    PromoInterval VARCHAR(50) NULL
);
GO

IF OBJECT_ID('dbo.Train', 'U') IS NOT NULL DROP TABLE dbo.Train;
CREATE TABLE dbo.Train (
    Store INT NOT NULL,
    DayOfWeek INT NULL,
    [Date] DATE NULL,
    Sales FLOAT NULL,
    Customers FLOAT NULL,
    [Open] INT NULL,
    Promo INT NULL,
    StateHoliday VARCHAR(10) NULL,
    SchoolHoliday INT NULL
);
GO

-- Import Store CSV
BULK INSERT dbo.Store
FROM '/tmp/store.csv'
WITH (
    FIRSTROW = 2,
    FORMAT = 'CSV',
    FIELDQUOTE = '"',
    ROWTERMINATOR = '0x0a',
    TABLOCK,
    KEEPNULLS
);
GO

-- Import Train CSV
BULK INSERT dbo.Train
FROM '/tmp/train.csv'
WITH (
    FIRSTROW = 2,
    FORMAT = 'CSV',
    FIELDQUOTE = '"',
    ROWTERMINATOR = '0x0a',
    TABLOCK,
    KEEPNULLS
);
GO

SELECT COUNT(*) AS store_rows FROM dbo.Store;
SELECT COUNT(*) AS train_rows FROM dbo.Train;
GO