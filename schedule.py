Teams = ["India", "Australia", "New Zealand", "England", "Bangladesh"]

schedule = []

for i in range(len(Teams)):
    for j in range(i + 1, len(Teams)):
        schedule.append((Teams[i], Teams[j]))

print("Match Schedule\n")

for match_no, match in enumerate(schedule, start=1):
    print(f"Match {match_no}: {match[0]} vs {match[1]}")



