# DataResearchRAG



'SELECT TOP 5
    T1.Store,
    SUM(T2.Sales) AS TotalSales
FROM
    dbo.Store AS T1
INNER JOIN
    dbo.Train AS T2 ON T1.Store = T2.Store AND T2.[Open] = 1
GROUP BY
    T1.Store
ORDER BY
    TotalSales DESC;'