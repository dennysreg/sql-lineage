# How-To

```sql
--model_name = idf_entities
with scores_entities as (
    select
        score_type,
        score_id,
        score_name
    from "onefootball"."analytics"."stg_scores__entities"
),
articles as (
    select
        language_code,
        article_id,
        publish_time,
        title
    from
        "onefootball"."analytics_datasets"."train_set_tagging"
),
per_language_count as (
    select
        language_code,
        count(article_id) as per_language_count
    from articles
    group by 1
),
article_entities_counts as (
    select
        language as language_code,
        score_type,
        score_id,
        count(feed_item_id) as per_entity_count
    from "onefootball"."analytics"."stg_cms__feed_item_streams" as fis
    join articles on fis.feed_item_id = articles.article_id
    where
        score_type in ('team', 'competition', 'player')
    group by 1, 2, 3
)
select
    language_code,
    score_type,
    score_id,
    score_name,
    per_language_count,
    per_entity_count,
    --log((1 + per_language_count) / (1 + per_entity_count)) + 1 as idf
from article_entities_counts
join per_language_count using (language_code)
join scores_entities using (score_type, score_id)
```
![lienage](/column_lineage.svg.svg)