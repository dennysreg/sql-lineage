WITH detail AS (
    SELECT
        store, product, amount
    FROM
        src
    WHERE
        sold > getddate () - 13
),
agg AS (
    SELECT
    store,
    max(amount) AS _agg_measure
FROM
    detail
GROUP BY
grupo
)
SELECT
    store, amount
FROM
    agg;

