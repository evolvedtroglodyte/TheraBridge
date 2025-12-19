#!/bin/bash
# Deletion script for role-play and demonstration therapy sessions
# Generated: December 18, 2025
# Keeping only REAL therapy sessions
#
# Analysis basis: DOWNLOAD_SUMMARY.md classification + filename analysis
# Total files: 33 MP3 files
# Files to DELETE: 30 (role-plays, demonstrations, duplicates, test files)
# Files to KEEP: 3 (real sessions)

cd "$(dirname "$0")/tests/samples"

echo "Starting deletion of role-play and demonstration files..."
echo ""

# CBT Role-Play Files (17 files)
echo "Deleting CBT role-play demonstrations..."
rm "CBT Role-Play - Behavioral Activation and Depression [sDrakgSYvzc].mp3"
rm "CBT Role-Play - Behavioral Activation and Postpartum Depression [SNstOn6owcI].mp3"
rm "CBT Role-Play - Depressive Symptoms and Lack of Motivation [8aDFvvjC6XM].mp3"
rm "CBT Role-Play – Complete Session – Social Anxiety Disorder – Part 1 [gbBn8EzZx3w].mp3"
rm "CBT Role-Play – Complete Session – Social Anxiety Disorder – Part 2 [8K4HW6_MvoU].mp3"
rm "CBT Role-Play – Complete Session – Social Anxiety Disorder – Part 3 [jmwQ3SE6Uew].mp3"
rm "CBT Role-Play – Complete Session – Social Anxiety Disorder – Part 4 [LuuKIF4-F_Q].mp3"
rm "CBT Role-Play – Complete Session – Social Anxiety Disorder – Part 5 [o2Cv6Mlp3KY].mp3"
rm "CBT Role-Play – Complete Session – Social Anxiety Disorder – Part 6 [TcewFGydzPM].mp3"
rm "CBT Mock Session [92jbfcpiA9Y].mp3"
rm "CBT Role-Play - Challenging Relationship with Family Member [XbYGdo9lMsQ].mp3"
rm "CBT Role-Play - Managing Anger [W_tDRu67JnI].mp3"
rm "CBT Role-Play - Cognitive Reframing an Experience of Emotional Abuse [CdyJ0iB_k00].mp3"
rm "CBT Role-Play - Anxiety and Guilt Related to Balancing Home and Work [osROod3Hmpg].mp3"
rm "CBT Role-Play - Loss of Hope [pllei-yDO8c].mp3"
rm "CBT Role Play - Catastrophizing and Decatastrophizing [nanU4vR993I].mp3"
rm "CBT Role-Play - Downward Arrow Technique [Wx8F9uwQTnY].mp3"

# ACT Learning Series (3 files)
echo "Deleting ACT educational demonstrations..."
rm "Learning ACT ⧸⧸ Part 3： Undermining Cognitive Fusion [dNfM2ihfSSE].mp3"
rm "Learning ACT ⧸⧸ Part 6： Defining Valued Directions [-GaYArbWL1Q].mp3"
rm "ACT Therapy-Advanced Counseling [ZAOwjnqVUnM].mp3"

# Motivational Interviewing Demonstrations (3 files)
echo "Deleting Motivational Interviewing demonstrations..."
rm "Motivational Interviewing for Tobacco Cessation [1jfH055byg4].mp3"
rm "Motivation Interviewing with Survivors of Intimate Partner Violence： Session 1 of 3 [P3JUXQ4kkHs].mp3"
rm "The Effective School Counselor With a High Risk Teen： Motivational Interviewing Demonstration [_TwVa4utpII].mp3"

# Emotion Focused Therapy (2 files)
echo "Deleting EFT course demonstrations..."
rm "Emotionally Focused Therapy [XUVQ5dGB1x0].mp3"
rm "SOWK 647 - Emotionally Focused Couple Therapy (EFT) Session [qe-0fk4ZG20].mp3"

# Other Modality Demonstrations (2 files)
echo "Deleting other modality demonstrations..."
rm "Dr. Ellis & Gloria Counseling Skill Demonstration [Zkolz9qTQKU].mp3"
rm "Role Play： Person Centred Therapy [4wTVbzvBH0k].mp3"

# Duplicate/Processed/Test Files (3 files)
echo "Deleting duplicate and test files..."
rm "Person-Centred Therapy Session - Full Example [VLDDUL3HBIg].mp3"
rm "Person-Centred Therapy Session - Full Example [VLDDUL3HBIg]_processed.mp3"
rm "compressed-cbt-session_processed.mp3"

echo ""
echo "========================================"
echo "Deletion complete!"
echo "========================================"
echo "Deleted: 30 role-play/demonstration files"
echo "Kept: 3 real therapy session files"
echo ""
echo "Remaining files:"
echo "  1. Carl Rogers and Gloria - Counselling 1965 Full Session - CAPTIONED [ee1bU4XuUyg].mp3 (CONFIRMED REAL)"
echo "  2. Initial Phase and Interpersonal Inventory 1 [A1XJeciqyL8].mp3 (REAL - IPT training session)"
echo "  3. LIVE Cognitive Behavioral Therapy Session (1).mp3 (REAL - live session)"
echo ""
