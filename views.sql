create or replace view v_model_training_triplets as
select ui.user_id, ui.film_id as item_id, sum(
	case
		when ui.interaction_type = 'view' and ui.duration_watched_sec is not null
			then 1.0 + (ui.duration_watched_sec/600)
		when ui.interaction_type = 'like' then 5.0
		when ui.interaction_type = 'add_to_list' then 1.0
		else 0.0
		end
) as interaction_score
from user_interactions ui
group by ui.user_id, ui.film_id
having sum(
	case when ui.interaction_type <> 'skip' then 1 else 0 end
) > 0;