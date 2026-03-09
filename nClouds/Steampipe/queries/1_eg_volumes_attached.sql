select
  v.volume_id,
  v.state as volume_state,
  -- Check if volume is unattached (orphaned)
  case 
    when v.state = 'available' then 'YES' 
    else 'NO' 
  end as is_orphaned,
  v.size,
  v.volume_type,
  v.create_time,
  -- Extracts the instance ID from the attachments JSON array
  v.attachments -> 0 ->> 'InstanceId' as attached_instance_id,
  -- Joins with the instance table to get the 'Name' tag
  i.tags ->> 'Name' as instance_name,
  i.instance_state,
  v.region
from
  aws_ebs_volume as v
  left join aws_ec2_instance as i 
    on i.instance_id = v.attachments -> 0 ->> 'InstanceId'
where 
  v.volume_id in (
    'vol-xxxx',
    'vol-xxxx'
  );