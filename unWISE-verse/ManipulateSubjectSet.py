import csv

from Spout import Spout
from Login import Login
from Discriminator import SubjectDiscriminator

# Login
login = Login(username='', password='')

# IDs
project_id =
subject_set_id =

# Spout
display_printouts = True
spout = Spout(project_identifier=project_id, login=login, display_printouts=display_printouts)

subject_set = spout.get_subject_set(subject_set_id)

print(f"Subject Set: {subject_set}")
discriminator = SubjectDiscriminator(subject_set)
print("Discriminator created.")

def in_targets_file(TARGET_ID):
    TARGET_ID = int(TARGET_ID)
    target_filename = ""
    with open(target_filename, newline='') as targets_file:
        reader = csv.DictReader(targets_file)
        for row in reader:
            if(TARGET_ID == int(row["TARGET ID"])):
                return True
    return False

def not_in_targets_file(TARGET_ID):
    TARGET_ID = int(TARGET_ID)
    target_filename = ""
    with open(target_filename, newline='') as targets_file:
        reader = csv.DictReader(targets_file)
        for row in reader:
            if(TARGET_ID == int(row["TARGET ID"])):
                return False
    return True

def all_subjects():
    return True

valid_subject_list = discriminator.findValidSubjects(in_targets_file, "TARGET ID")
print(f"Valid Subject List: {valid_subject_list}")
print(f"Number of valid subjects: {len(valid_subject_list)}")


#The following lines are examples of how to modify subject metadata.

# This line will change the field name "TARGET ID" to "Target ID" for all subjects in the list, valid_subject_list.
#spout.modify_subject_metadata_field_name(valid_subject_list, "TARGET ID", "Target ID")

# This line will change the field value for the metadata "FOV" to "~120.0 x ~120.0 arcseconds" for all subjects in the list, valid_subject_list.
#spout.modify_subject_metadata_field_value(valid_subject_list, "FOV", "~120.0 x ~120.0 arcseconds")

# Please note that the following line will delete the subjects from the subject set. This is irreversible.
# Please verify that your functional condition is absolutely correct before uncommenting the following line.
# This line will delete all subjects in the list, valid_subject_list, from the subject set.
#spout.delete_subjects(subject_set, valid_subject_list)

