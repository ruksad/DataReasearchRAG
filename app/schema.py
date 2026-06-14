SCHEMA_CONTEXT = """
Database: Rossmann (MS SQL Server)

Table: dbo.Store (1,115 rows — one row per store)
  Store                    INT  PRIMARY KEY
  StoreType                VARCHAR  -- 'a', 'b', 'c', 'd'
  Assortment               VARCHAR  -- 'a'=basic, 'b'=extra, 'c'=extended
  CompetitionDistance      FLOAT    -- metres to nearest competitor
  CompetitionOpenSinceMonth INT
  CompetitionOpenSinceYear  INT
  Promo2                   INT      -- 0=not participating, 1=participating
  Promo2SinceWeek          INT
  Promo2SinceYear          INT
  PromoInterval            VARCHAR  -- months when Promo2 restarts, e.g. 'Feb,May,Aug,Nov'

Table: dbo.Train (~1M rows — daily sales Jan 2013 to Jul 2015)
  Store        INT   -- FK to dbo.Store.Store
  DayOfWeek    INT   -- 1=Monday, 2=Tuesday, ..., 7=Sunday
  Date         DATE
  Sales        FLOAT -- daily turnover; always 0 when Open=0
  Customers    FLOAT -- number of customers that day
  [Open]       INT   -- 0=closed, 1=open  (reserved keyword: always quote as [Open])
  Promo        INT   -- 1=promotion running that day, 0=no promotion
  StateHoliday VARCHAR -- 'a'=public holiday, 'b'=Easter, 'c'=Christmas, '0'=none
  SchoolHoliday INT  -- 1=affected by school closure, 0=not

Join key: dbo.Train.Store = dbo.Store.Store
"""
