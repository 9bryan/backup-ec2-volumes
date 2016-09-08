"""
This code iterates through running ec2 instances and
backs up volumes whose instances are tagged as "backup=true"
"""

import uuid
import datetime
import boto3
import pytz

ec2 = boto3.resource('ec2')

snapshot_suffix = "-automated" #Suffix appended to the end of the snapshot description
retention_days = 7             #Days to retain snapshots

now = datetime.datetime.utcnow()
now = now.replace(tzinfo=pytz.utc)

#Only work with instances tagged with backup=true
instances = ec2.instances.filter(
    Filters=[{'Name': 'tag:backup'.lower(), 'Values': ['true'.lower()]}])

for instance in instances:
    for volume in instance.volumes.all():
        instance_name = instance.tags[0]['Value']   #Name of instance we're working with for snapshot description
        date_str = str(now.strftime("%A-%Y-%m-%d")) #Date string for snapshot description
        uid = str(uuid.uuid4().fields[1])           #uid for for description so we can tell them apart
        snapshot_description = instance_name + "-" + date_str + "-" + uid + snapshot_suffix
        snapshot = ec2.create_snapshot(VolumeId=volume.id, Description=snapshot_description)
        print "Snapshotting instance: " + instance_name + "(" + instance.id + ")" + " volume: " + volume.id
        for snapshot in volume.snapshots.all():
            print snapshot.description
            snapshot_datetime = snapshot.start_time
            cutoff = now - datetime.timedelta(days=retention_days)
            if snapshot_datetime < cutoff and snapshot.description.endswith(snapshot_suffix):
                #snapshot.delete
                print "Deleted old snapshot: " + snapshot.id + " from " + instance_name + "(" + instance.id + ")" + " volume: " + volume.id
