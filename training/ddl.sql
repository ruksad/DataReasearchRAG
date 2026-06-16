-- Rossmann database schema (MS SQL Server)

CREATE TABLE dbo.Store (
    Store                    INT          NOT NULL PRIMARY KEY,
    StoreType                VARCHAR(10)  NULL,  -- 'a', 'b', 'c', 'd'
    Assortment               VARCHAR(10)  NULL,  -- 'a'=basic, 'b'=extra, 'c'=extended
    CompetitionDistance      FLOAT        NULL,  -- metres to nearest competitor
    CompetitionOpenSinceMonth INT         NULL,
    CompetitionOpenSinceYear  INT         NULL,
    Promo2                   INT          NULL,  -- 0=not participating, 1=participating
    Promo2SinceWeek          INT          NULL,
    Promo2SinceYear          INT          NULL,
    PromoInterval            VARCHAR(50)  NULL   -- months Promo2 restarts e.g. 'Feb,May,Aug,Nov'
);

CREATE TABLE dbo.Train (
    Store        INT          NOT NULL,  -- FK to dbo.Store.Store
    DayOfWeek    INT          NULL,      -- 1=Monday, 2=Tuesday, ..., 7=Sunday
    [Date]       DATE         NULL,
    Sales        FLOAT        NULL,      -- daily turnover; always 0 when [Open]=0
    Customers    FLOAT        NULL,      -- number of customers that day
    [Open]       INT          NULL,      -- 0=closed, 1=open  (reserved keyword: always bracket as [Open])
    Promo        INT          NULL,      -- 1=promotion running, 0=no promotion
    StateHoliday VARCHAR(10)  NULL,      -- 'a'=public holiday, 'b'=Easter, 'c'=Christmas, '0'=none
    SchoolHoliday INT         NULL       -- 1=affected by school closure, 0=not
);

-- Join key
-- dbo.Train.Store = dbo.Store.Store
