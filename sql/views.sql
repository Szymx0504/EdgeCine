create or replace view v_model_training_triplets as
select ui.user_id, ui.film_id as item_id, sum(
	case
		when ui.interaction_type = 'like' then 5.0
		when ui.interaction_type = 'rate_5' then 5.0
		when ui.interaction_type = 'rate_4' then 4.0
		when ui.interaction_type = 'rate_3' then 3.0
		when ui.interaction_type = 'rate_2' then 2.0
		when ui.interaction_type = 'rate_1' then 1.0
		else 0.0
		end
) as interaction_score
from user_interactions ui
group by ui.user_id, ui.film_id
having count(*) > 0;